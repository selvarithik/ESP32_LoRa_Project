"""Archive only unreferenced generated images; source assets/data are excluded."""
from pathlib import Path
import argparse,hashlib,io,json,os,sys,zipfile,uuid
from datetime import datetime,timezone
from urllib.parse import unquote
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from backup_manager import codec
SKIP={'.git','.venv','.pio','data','build','dist','node_modules','__pycache__','_legacy_ui','_rejected_ui_rebuild'}
TEXT={'.md','.html','.py','.js','.cjs','.json','.css','.txt'}
KEEP=('local-dashboard-mock-','local-page-mock-','access-page-mock-','mqtt-page-mock-','APPROVED_','SENSOR_ICON_')
def files(root):
 for current,dirs,names in os.walk(root):
  dirs[:]=[d for d in dirs if d not in SKIP and not (Path(current)/d).is_symlink()]
  for name in names:
   p=Path(current)/name
   if not p.is_symlink():yield p

def clean(roots,apply=False):
 roots=[Path(r).resolve() for r in roots]
 if any(not (r/"backend/server.py").is_file() and not (r/"src/web").is_dir() for r in roots):raise ValueError("NOT_A_GATEWAY_OR_FIRMWARE_ROOT")
 all_files=[p for r in roots for p in files(r)]
 refs=unquote('\n'.join(p.read_text(encoding='utf-8',errors='ignore') for p in all_files if p.suffix.lower() in TEXT and p.stat().st_size<4*1024*1024)).casefold()
 candidates=[]
 for root in roots:
  for p in all_files:
   if not p.is_relative_to(root):continue
   relative=p.relative_to(root)
   if p.suffix.lower() in ('.png','.jpg','.jpeg','.webp','.gif') and relative.parts[0]=='docs' and not any(x in relative.parts for x in ('esp32-sidebar-v2','command-mqtt-v5')) and p.name!='sensor-icon-preview.png' and not p.name.startswith(KEEP) and p.name.casefold() not in refs:candidates.append((root,p))
 result={'apply':apply,'image_count':len(candidates),'image_bytes':sum(p.stat().st_size for _,p in candidates),'files':[str(p.relative_to(r)) for r,p in candidates],'source_assets_preserved':True,'runtime_data_preserved':True}
 if not apply:return result
 if candidates:
  home=roots[0]/'data/cleanup';home.mkdir(parents=True,exist_ok=True);memory=io.BytesIO();manifest={}
  with zipfile.ZipFile(memory,'w',zipfile.ZIP_DEFLATED) as archive:
   for index,(root,p) in enumerate(candidates):
    if not p.resolve().is_relative_to(root) or p.is_symlink():raise RuntimeError('UNSAFE_CLEANUP_PATH')
    key=str(index)+'/'+p.name;raw=p.read_bytes();archive.writestr(key,raw);manifest[key]={'root':str(root),'relative':str(p.relative_to(root)),'sha256':hashlib.sha256(raw).hexdigest()}
   archive.writestr('manifest.json',json.dumps(manifest))
  target=home/('generated-images-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]+'.cleanup')
  target.write_bytes(codec(memory.getvalue()))
  with zipfile.ZipFile(io.BytesIO(codec(target.read_bytes(),True))) as archive:
   for key,meta in manifest.items():
    if hashlib.sha256(archive.read(key)).hexdigest()!=meta['sha256']:raise RuntimeError('CLEANUP_ARCHIVE_VERIFY_FAILED')
  for root,p in candidates:
   key=next(k for k,m in manifest.items() if m['root']==str(root) and m['relative']==str(p.relative_to(root)))
   if p.resolve().is_relative_to(root) and hashlib.sha256(p.read_bytes()).hexdigest()==manifest[key]['sha256']:p.unlink()
  result['encrypted_recovery_archive']=str(target)
 # Remove only generated Python bytecode in source/test/tool folders, never environments or runtime data.
 removed=0
 for root in roots:
  for area in ('backend','tests','tools'):
   for p in (root/area).rglob('*.pyc'):
    if p.is_file() and not p.is_symlink() and p.resolve().is_relative_to(root/area):p.unlink();removed+=1
 result['bytecode_files_removed']=removed
 (roots[0]/'data/cleanup').mkdir(parents=True,exist_ok=True)
 (roots[0]/'data/cleanup/latest.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
 return result
def restore_archive(path,roots,apply=False):
 roots={Path(r).resolve() for r in roots};plan=[]
 with zipfile.ZipFile(io.BytesIO(codec(Path(path).read_bytes(),True))) as archive:
  if sum(i.file_size for i in archive.infolist())>256*1024*1024:raise ValueError('ARCHIVE_SIZE_LIMIT')
  manifest=json.loads(archive.read('manifest.json'))
  for key,meta in manifest.items():
   root=Path(meta['root']).resolve();relative=Path(meta['relative']);target=(root/relative).resolve()
   if root not in roots or not relative.parts or relative.parts[0]!='docs' or not target.is_relative_to(root) or target.is_symlink():raise ValueError('UNSAFE_RESTORE_TARGET')
   raw=archive.read(key)
   if hashlib.sha256(raw).hexdigest()!=meta['sha256']:raise ValueError('RESTORE_HASH_MISMATCH')
   if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest()!=meta['sha256']:raise ValueError('EXISTING_FILE_PRESERVED')
   plan.append((target,raw))
 if apply:
  for target,raw in plan:
   if not target.exists():target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
 return {'applied':apply,'files':len(plan)}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',action='append',required=True);p.add_argument('--apply',action='store_true');p.add_argument('--restore',type=Path);a=p.parse_args();print(json.dumps(restore_archive(a.restore,a.root,a.apply) if a.restore else clean(a.root,a.apply),indent=2))
