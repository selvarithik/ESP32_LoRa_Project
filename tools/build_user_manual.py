"""Create an offline HTML manual and printable PDF from reviewed local content."""
from pathlib import Path
import html,json,hashlib,sys,re
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak,Image,Table,TableStyle,KeepTogether
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image as PILImage
from manual_content import SECTIONS

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/user-manual';OUT.mkdir(parents=True,exist_ok=True)
CAPTURES=json.loads((OUT/'captures.json').read_text(encoding='utf-8'))
CAP={c['name']:c for c in CAPTURES}
for name,file in [('Arial','arial.ttf'),('ArialBold','arialbd.ttf'),('Code','consola.ttf')]:pdfmetrics.registerFont(TTFont(name,'C:/Windows/Fonts/'+file))
styles=getSampleStyleSheet()
for name in ['Normal','Title','Heading1','Heading2']:
 styles[name].fontName='ArialBold' if name!='Normal' else 'Arial';styles[name].textColor=colors.black
styles['Title'].fontSize=28;styles['Title'].leading=34
styles['Heading1'].fontSize=18;styles['Heading1'].leading=23;styles['Heading1'].spaceAfter=12
styles['Normal'].fontSize=10;styles['Normal'].leading=14;styles['Normal'].spaceAfter=7
styles.add(ParagraphStyle('Step',parent=styles['Normal'],leftIndent=17,firstLineIndent=-17,spaceAfter=8))
styles.add(ParagraphStyle('Note',parent=styles['Normal'],fontSize=9.4,leading=13,spaceAfter=7))
styles.add(ParagraphStyle('CaptionManual',parent=styles['Normal'],fontSize=8.3,leading=11,textColor=colors.HexColor('#43546b'),spaceAfter=9))
styles.add(ParagraphStyle('CellManual',parent=styles['Normal'],fontSize=9,leading=12,spaceAfter=0))
styles.add(ParagraphStyle('CodeManual',parent=styles['Normal'],fontName='Code',fontSize=8,leading=11,spaceBefore=6,spaceAfter=10,splitLongWords=True))

def esc(t):return html.escape(str(t),quote=False)
def para(t,style='Normal'):return Paragraph(esc(t),styles[style])
WIDTH=A4[0]-88

class Manual(SimpleDocTemplate):
 def afterFlowable(self,flow):
  if isinstance(flow,Paragraph) and flow.style.name=='Heading1':
   text=flow.getPlainText();key='section-'+str(getattr(flow,'section_index',self.page));self.canv.bookmarkPage(key);self.canv.addOutlineEntry(text,key,0,False);self.notify('TOCEntry',(0,text,self.page,key))

def footer(c,d):
 c.setFont('Arial',8);c.setFillColor(colors.HexColor('#536276'));c.drawString(44,26,'SELVARITHIK A&D  |  Operator manual  |  29 October 2026');c.drawRightString(A4[0]-44,26,str(d.page))
def figure(name,maxheight=245):
 path=OUT/'images'/f'{name}.png';im=PILImage.open(path);w,h=im.size;scale=min(WIDTH/w,maxheight/h);result=[Image(str(path),width=w*scale,height=h*scale,hAlign='LEFT')]
 # The legend identifies requested callouts; missing off-screen targets are not described as visible.
 marks=CAP[name].get('visible_marks',CAP[name]['marks'])
 legend='  '.join(f'{i+1} {label}' for i,(_,label) in enumerate(marks))
 result.append(para('Figure '+name.replace('-',' ')+'  Demonstration data. '+legend,'CaptionManual'));return result

story=[Spacer(1,30),para('SELVARITHIK A&D Gateway and ESP32 user manual','Title'),Spacer(1,12),para('Step by step setup operation configuration and testing','Heading2'),Spacer(1,18),para('Version 1.0  |  29 October 2026'),para('For the project owner and authorized local operators'),Spacer(1,16),para('Use this guide to start the local Gateway, sign in, configure supported communication paths, map real sensor fields, send commands and verify actual results. Read the first chapters before changing an existing deployment.'),para('The instructions follow the current source. All page illustrations are explicitly labelled demonstrations. No passwords, protected tokens or live configuration exports are included.'),Spacer(1,20)]
story+=figure('gateway-command',220)
story+=[para('Preservation rule','Heading2'),para('Keep the existing Wi-Fi, MQTT profile and sensor settings unless you deliberately authorize a change. The safe first checks are status, freshness and PING. A queued command or green connection badge is not proof of physical execution.'),PageBreak(),para('Contents','Heading2')]
toc=TableOfContents();toc.levelStyles=[ParagraphStyle('ContentsEntry',fontName='Arial',fontSize=9.5,leading=14,leftIndent=0,firstLineIndent=0,spaceBefore=3,textColor=colors.black)];story.append(toc)

for index,s in enumerate(SECTIONS,1):
 story.append(PageBreak());heading=para(f'{index}  {s["title"]}','Heading1');heading.section_index=index;story.append(heading)
 if s['image']:story+=figure(s['image'])
 for i,step in enumerate(s['steps'],1):story.append(para(f'{i}.  {step}','Step'))
 for note in s['notes']:story.append(para(note,'Note'))
 if s['table']:
  rows=[[para(x,'CellManual') for x in row] for row in s['table']];cols=len(rows[0]);widths=[WIDTH*.28,WIDTH*.72] if cols==2 else [WIDTH*.18,WIDTH*.32,WIDTH*.50]
  table=Table(rows,colWidths=widths,repeatRows=1,hAlign='LEFT');table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e5edf6')),('GRID',(0,0),(-1,-1),.5,colors.HexColor('#d9d9d9')),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f6f8fb')])]))
  story.append(table);story.append(Spacer(1,9))
 if s['code']:story.append(Paragraph('<br/>'.join(esc(line).replace(' ','&#160;') for line in s['code'].splitlines()),styles['CodeManual']))

# Include every captured main page, even where the main instructions share a chapter.
used={s['image'] for s in SECTIONS if s['image']}|{'gateway-command'}
extras=[name for name in CAP if name not in used]
for j in range(0,len(extras),2):
 story.append(PageBreak());h=para('Page image reference '+str(j//2+1),'Heading1');h.section_index=100+j;story.append(h)
 story.append(para('These additional source-based page views complement the numbered procedures. Blue circles mark controls where visible. All values are demonstration data.','Note'))
 for name in extras[j:j+2]:story+=figure(name,270)

story.append(PageBreak());h=para('Source and verification notes','Heading1');h.section_index=200;story.append(h)
for t in [
 'Authority: current CONFIG_CONTRACT.md in both repositories; backend/device_control_contract.py, workspace_views.py, MQTT/Local IP handlers, sensor mapping code, deployment runtime and embedded ESP32 page source. Historical implementation reports can describe older source snapshots.',
 'This manual was authored from local source and isolated demonstrations. No external design reference was treated as a live feature specification. No hardware test, broker probe, credential rotation, firmware upload or production configuration mutation was run to create it.',
 'Gateway illustrations ran in an isolated temporary SQLite fixture at loopback port 5063 with no permanent worker. ESP32 screenshots used intercepted replies at esp32.test and the actual embedded HTML. Names DEMO and TEST are not production enrollment instructions.',
 'Full Gateway deployment tests from the previous implementation: 187 passed; deployment regressions 10 passed; source/frozen HTTP lifecycle smoke tests passed. Those results are not new hardware acceptance results.',
 'To regenerate: run tools/manual_fixture.py using the Gateway virtual environment; run tools/capture_manual.cjs with bundled Node/Playwright; run tools/build_user_manual.py with the bundled document Python. Stop the isolated fixture afterwards. Never point these fixture tools at production data.',
 'The companion HTML is searchable, responsive and offline-capable. Keep its images directory beside it. PDF contains the illustrations directly and is suitable for printing or sharing.'
]:story.append(para(t))
pdf=OUT/'SELVARITHIK_Gateway_ESP32_User_Manual.pdf';doc=Manual(str(pdf),pagesize=A4,rightMargin=44,leftMargin=44,topMargin=42,bottomMargin=43,title='SELVARITHIK A&D Gateway and ESP32 user manual',author='SELVARITHIK A&D');doc.multiBuild(story,onFirstPage=footer,onLaterPages=footer)

parts=['<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>SELVARITHIK A&amp;D User Manual</title><style>body{margin:0;background:#f5f7fb;color:#152b43;font:16px/1.6 Arial,sans-serif}main{max-width:1020px;margin:auto;padding:36px 24px}header,section{background:white;border:1px solid #dce3eb;border-radius:10px;padding:26px;margin:0 0 22px}h1,h2{color:#000;line-height:1.25}h1{font-size:32px}h2{font-size:25px}a{color:#164d94}img{width:auto;max-width:100%;max-height:720px;display:block;margin:12px auto}figure{margin:10px 0}figcaption{font-size:13px;color:#526174}li{margin-bottom:10px}table{width:100%;border-collapse:collapse;font-size:14px}td,th{padding:10px;border:1px solid #d9d9d9;text-align:left;vertical-align:top;overflow-wrap:anywhere}th{background:#e5edf6}tr:nth-child(even){background:#f6f8fb}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f4f6f9;padding:18px;font-size:13px}.table-wrap{overflow:auto}.meta{color:#526174}@media(max-width:600px){main{padding:12px}header,section{padding:18px}h1{font-size:26px}h2{font-size:22px}td,th{padding:7px}}@media print{body{background:white}section{break-before:page;border:0}nav{break-after:page}a{color:black}}</style><main><header><h1>SELVARITHIK A&amp;D Gateway and ESP32 user manual</h1><p>Step by step setup operation configuration and testing</p><p class="meta">Version 1.0 · 29 October 2026 · Annotated demonstration images</p><p>Use the printable PDF or follow this offline guide. Preserve existing Wi-Fi, MQTT profiles and sensor settings unless making an intentional change.</p></header><nav><h2>Contents</h2><ol>']
for i,s in enumerate(SECTIONS,1):parts.append(f'<li><a href="#section-{i}">{esc(s["title"])}</a></li>')
parts.append('<li><a href="#images">All annotated page images</a></li></ol></nav>')
def htmlfigure(name):
 marks=CAP[name].get('visible_marks',CAP[name]['marks']);legend='; '.join(f'{i+1}. {label}' for i,(_,label) in enumerate(marks))
 return f'<figure><a href="images/{name}.png"><img src="images/{name}.png" alt="Annotated {name.replace("-"," ")} demonstration"></a><figcaption>{esc(legend)}. Demonstration only; click image to enlarge.</figcaption></figure>'
for i,s in enumerate(SECTIONS,1):
 parts.append(f'<section id="section-{i}"><h2>{i} {esc(s["title"])}</h2>')
 if s['image']:parts.append(htmlfigure(s['image']))
 if s['steps']:parts.append('<ol>'+''.join('<li>'+esc(x)+'</li>' for x in s['steps'])+'</ol>')
 parts.extend('<p>'+esc(x)+'</p>' for x in s['notes'])
 if s['table']:parts.append('<div class="table-wrap"><table>'+''.join('<tr>'+''.join(f'<{"th" if n==0 else "td"}>{esc(x)}</{"th" if n==0 else "td"}>' for x in row)+'</tr>' for n,row in enumerate(s['table']))+'</table></div>')
 if s['code']:parts.append('<pre>'+esc(s['code'])+'</pre>')
 parts.append('<a href="#">Back to contents</a></section>')
parts.append('<section id="images"><h2>All annotated page images</h2>')
parts.extend('<h3>'+esc(name.replace('-',' ').title())+'</h3>'+htmlfigure(name) for name in CAP)
parts.append('</section></main></html>');(OUT/'index.html').write_text('\n'.join(parts),encoding='utf-8')
(OUT/'manual-content.json').write_text(json.dumps(SECTIONS,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps({'pdf':str(pdf),'chapters':len(SECTIONS),'images':len(CAP),'sha256':hashlib.sha256(pdf.read_bytes()).hexdigest()}))
