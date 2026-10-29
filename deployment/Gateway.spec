# One-folder Windows bundle. Runtime data/credentials are deliberately excluded.
from pathlib import Path
ROOT=Path(SPECPATH).parent
analysis=Analysis([str(ROOT/'tools/gateway.py')],pathex=[str(ROOT/'backend')],binaries=[],datas=[(str(ROOT/'dashboard/templates'),'dashboard/templates'),(str(ROOT/'dashboard/static'),'dashboard/static'),(str(ROOT/'deployment/profile.example.json'),'deployment')],hiddenimports=['engineio.async_drivers.threading','socketio','waitress'],hookspath=[],hooksconfig={},runtime_hooks=[],excludes=['amqtt','pytest','tkinter'],noarchive=False)
pyz=PYZ(analysis.pure)
exe=EXE(pyz,analysis.scripts,[],exclude_binaries=True,name='Gateway',debug=False,bootloader_ignore_signals=False,strip=False,upx=False,console=True)
collection=COLLECT(exe,analysis.binaries,analysis.datas,strip=False,upx=False,name='Gateway')
