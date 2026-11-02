from pathlib import Path
from html import escape as E
import re,json,base64
r=Path.cwd();out=r/'docs/design-preview/command-mqtt-v2'
header=(r/'dashboard/templates/partials/global-header.html').read_text(encoding='utf-8');brand=re.search(r'<svg class="aerospace-wordmark".*?</svg>',header,re.S).group();brand=re.sub(r'<svg[^>]*>','<svg x="54" y="39" width="194" height="22" viewBox="40 245 1900 190" color="white">',brand,count=1)
C={'navy':'#07305B','red':'#FF0000','blue':'#0066FF','muted':'#4D647D','border':'#B8CAE0','bg':'#E8EFF7','green':'#008764'}
icons={'menu':'M4 6h16M4 12h16M4 18h16','search':'M20 20l-5-5M17 10a7 7 0 1 1-14 0 7 7 0 0 1 14 0','terminal':'M5 7l4 4-4 4M12 16h6M3 3h18v18H3z','chip':'M6 6h12v12H6zM9 2v4m6-4v4M9 18v4m6-4v4M2 9h4m-4 6h4m12-6h4m-4 6h4','wifi':'M3 8a14 14 0 0 1 18 0M6 12a9 9 0 0 1 12 0M9 16a4 4 0 0 1 6 0M12 20h.01','sliders':'M3 6h18M3 12h18M3 18h18M8 3v6m8 0v6m-6 0v6','send':'M3 3l18 9-18 9 4-9-4-9M7 12h14','chevron':'M9 5l7 7-7 7','check':'M4 12l5 5L20 6','refresh':'M20 8V3l-3 3a8 8 0 1 0 3 9M20 3h-5','copy':'M9 9h12v12H9zM15 9V3H3v12h6','shield':'M12 2l8 4v6c0 5-8 10-8 10S4 17 4 12V6l8-4M8 12l3 3 5-6','moon':'M20 15A9 9 0 0 1 9 3a9 9 0 1 0 11 12','folder':'M3 5h7l2 3h9v12H3z','message':'M3 3h18v14H8l-5 4V3z','arrow':'M15 5l-7 7 7 7','more':'M12 5h.01M12 12h.01M12 19h.01'}
def rect(x,y,w,h,fill='white',stroke=None,rad=0):return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rad}" fill="{fill}"'+(f' stroke="{stroke}"' if stroke else '')+'/>'
def text(x,y,s,size=14,fill=None,weight=400):return f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill or C["navy"]}" font-weight="{weight}">{E(str(s))}</text>'
def line(x,y,xx,yy,color=None):return f'<path d="M{x} {y}H{xx}" stroke="{color or C["border"]}"/>' if yy==y else f'<path d="M{x} {y}L{xx} {yy}" stroke="{color or C["border"]}"/>'
def icon(x,y,name,color=None,size=20):return f'<svg x="{x}" y="{y}" width="{size}" height="{size}" viewBox="0 0 24 24"><path d="{icons[name]}" fill="none" stroke="{color or C["navy"]}" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>'
def pill(x,y,s,fill='#E9F3FF',color=None,w=None):
 w=w or len(s)*6.2+18
 return rect(x,y,w,24,fill,rad=12)+text(x+9,y+16,s,11,color or C['blue'],600)
def button(x,y,w,s,primary=False,disabled=False):return rect(x,y,w,34,'#E9EEF5' if disabled else C['blue'] if primary else 'white',None if primary else C['border'],7)+text(x+12,y+22,s,12,'#8C9CAF' if disabled else 'white' if primary else C['navy'],600)
def field(x,y,w,label,value):return text(x,y,label,11,C['muted'],600)+rect(x,y+9,w,34,'white',C['border'],6)+text(x+10,y+31,value,12)
def start(w=1366,h=768):return [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><g font-family="Segoe UI, Arial, sans-serif">',rect(0,0,w,h,C['bg'])]
def apphead(page,subtitle,mobile=False):
 w=390 if mobile else 1366;s=rect(0,0,w,22,C['navy'])+text(12,15,'DESIGN PREVIEW · NOT A LIVE CONNECTION',10,'white',600)+rect(0,22,w,56,C['red'])+icon(15,40,'menu','white',21)
 if mobile:
  b=re.sub(r'x="54" y="39" width="194" height="22"','x="48" y="41" width="148" height="18"',brand)
  return s+b+icon(278,40,'search','white')+icon(316,40,'moon','white')+icon(354,40,'more','white')
 return s+brand+line(270,36,270,65,'#FF7777')+icon(288,40,'terminal' if page=='Command Center' else 'wifi','white')+text(320,46,page,15,'white',700)+text(320,63,subtitle,11,'#FFF0F0')+icon(1030,40,'search','white')+icon(1072,40,'moon','white')+text(1120,45,'27 OCT',11,'white',600)+text(1120,61,'21:36:19',10,'white')+pill(1230,39,'PREVIEW','#C40000','white',104)
def end(s,name):
 s.append('</g></svg>');(out/name).write_text(''.join(s),encoding='utf-8')
def command(expanded=False):
 s=start();s.append(apphead('Command Center','Commands, acknowledgements & execution responses'))
 s += [rect(16,94,1334,658,'white',C['border'],12),line(300,94,300,752),text(34,125,'Devices',18,weight=700),text(231,125,'2 shown',11,C['muted']),field(32,149,250,'FIND A DEVICE','Search name, ID or MAC'),icon(252,170,'search',C['muted'],17)]
 for x,label,w in [(28,'All',34),(66,'Master',52),(122,'Slave',47),(173,'Online',53),(230,'Offline',54)]:s.append(pill(x,201,label,'#EAF2FF' if label=='All' else '#F5F8FC',C['blue'] if label=='All' else C['muted'],w).replace('font-size="11"','font-size="10"'))
 s += [text(32,248,'RECORDED / ILLUSTRATIVE DEVICES',9,C['muted'],600),rect(17,261,282,100,'#EAF2FF'),rect(17,261,3,100,C['blue']),rect(32,279,36,36,'white',rad=10),icon(40,287,'chip'),text(80,283,'Master ESP32',14,weight=700),pill(80,292,'MASTER',w=66),text(80,335,'ESP32-10777D842178',11,C['muted']),text(32,352,'Recorded command test · EMQX',10,C['muted']),line(32,371,282,371),rect(32,389,36,36,C['bg'],rad=10),icon(40,397,'chip',C['muted']),text(80,394,'Slave ESP32',14,weight=600),text(80,416,'Not available for this preview',11,C['muted']),pill(80,429,'OFFLINE','#FFF0F0','#B52B39',77),text(32,692,'Selecting a node changes the target',11,C['muted']),text(32,710,'and keeps its saved conversation.',11,C['muted']),text(32,735,'No commands can be sent in this preview.',10,C['muted'])]
 s += [rect(301,95,1048,65,'white'),rect(322,108,38,38,C['bg'],rad=10),icon(331,117,'chip'),text(373,122,'Master ESP32',16,weight=700),text(373,142,'MASTER  ·  ESP32-10777D842178',11,C['muted']),pill(1090,112,'Recorded EMQX test','#E8F7F1',C['green'],157),icon(1272,116,'refresh'),icon(1310,116,'more'),line(301,160,1349,160),rect(301,161,1048,44,'#FAFCFF'),text(324,188,'History',12,C['muted']),pill(380,171,'All states'),text(976,188,'ACK ≠ execution complete',12,C['muted']),text(1207,188,'Latest ↓',12,C['blue'],600),rect(301,205,1048,457,C['bg'])]
 s += [pill(690,220,'27 October · recorded example','#E9EEF5',C['muted'],229),rect(903,268,415,83,'#E7F0FF',rad=11),text(922,291,'PING',14,C['blue'],700),text(922,312,'Check Master response',13),text(922,334,'CMD-30FEAD0494DC',10,C['muted']),text(1195,334,'21:36 · Sent',10,C['muted']),rect(330,367,505,50,'white',C['border'],11),icon(345,383,'check',C['green'],17),text(371,389,'ACK · ACCEPTED',12,C['green'],700),text(569,389,'Device accepted the command',12,C['muted']),rect(330,430,612,151,'white',C['border'],11),text(348,456,'Master ESP32',13,weight=700),pill(805,439,'COMPLETED','#E8F7F1',C['green'],119),text(348,483,'Execution response',14,weight=600),text(348,511,'{ "ok": true }',14,C['navy'],600),line(348,527,923,527),text(348,550,'▸ Technical details',12,C['blue']),icon(784,539,'copy',C['muted'],16),text(807,552,'Copy response',11,C['muted']),text(348,570,'Matched to CMD-30FEAD0494DC · 21:36:19',10,C['muted'])]
 s += [rect(301,663,1048,88,'white'),line(301,663,1349,663),text(324,684,'PING → Master ESP32',11,C['muted']),text(1102,684,'Configuration open' if expanded else 'Configuration collapsed',11,C['muted']),rect(320,697,742,38,'#F5F8FC',C['border'],8),text(334,722,'PING — Test round-trip connectivity',13),icon(1030,706,'chevron',C['muted'],18),button(1074,699,128,'Configure').replace('x="1086"','x="1110"'),icon(1084,707,'sliders',C['navy'],17),button(1214,699,115,'Send →',True)]
 if expanded:
  s += [rect(301,205,1048,229,C['bg']),pill(690,215,'27 October · recorded example','#E9EEF5',C['muted'],229),rect(1010,256,308,43,'#E7F0FF',rad=9),text(1027,282,'PING · 21:36:18 · Sent',12,C['blue'],600),rect(330,313,614,104,'white',C['border'],10),text(347,339,'Master ESP32 · RESPONSE',13,weight=700),pill(809,324,'COMPLETED','#E8F7F1',C['green'],119),text(347,368,'{ "ok": true }',14),text(347,396,'ACK accepted · execution response received · ▸ Details',11,C['muted'])]
  s += [rect(317,434,1016,226,'white',C['border'],12),text(335,461,'Command configuration',15,weight=700),text(1163,460,'Close ×',12,C['blue'])]
  for x,w,label,value in [(335,210,'Target device','Master ESP32'),(558,178,'ACK timeout (s)','5'),(749,178,'Response timeout (s)','30'),(940,171,'Max retries','3'),(1124,188,'Expiry (s)','300')]:s.append(field(x,484,w,label,value))
  s += [field(335,551,687,'Arguments · JSON','{ "message": "Connectivity check" }'),button(1036,562,83,'Reset'),button(1129,562,83,'Cancel'),button(1222,562,90,'Apply',True),text(335,633,'Draft changes stay here until applied. No credentials or unsupported delay fields.',11,C['muted'])]
 end(s,'command-expanded.svg' if expanded else 'command-desktop.svg')
def mqtt():
 s=start();s.append(apphead('MQTT','Profiles, verified TLS & broker diagnostics'))
 s += [text(20,109,'MQTT workspace',18,weight=700),text(20,132,'Same canonical profile. Candidate → test → confirm / rollback.',12,C['muted']),pill(1006,98,'DESIGN · NO BROKER CONNECTION','#E9EEF5',C['muted'],336)]
 s += [rect(16,152,320,600,'white',C['border'],12),text(34,183,'Connection profiles',16,weight=700),rect(30,200,292,65,'#EAF2FF',rad=8),icon(42,218,'wifi',C['blue']),text(73,223,'ESP32_LORA_GATEWAY001',13,weight=700),text(73,245,'EMQX · existing deployment',11,C['muted']),text(34,291,'Connection',12,weight=700),field(34,314,282,'Broker host','n1161c10.ala.eu-central-1.emqxsl.com'),field(34,377,130,'Port','8883'),field(179,377,137,'Protocol','MQTT 3.1.1'),icon(35,443,'shield',C['green'],18),text(62,457,'TLS + hostname verification required',11,C['green'],600),field(34,487,282,'Client ID','CL_ID_ESP32GATEWAY'),text(34,553,'▸ Security & protected credentials',12,C['blue']),text(34,579,'▸ Topics, identity & advanced settings',12,C['blue']),text(34,607,'Password stays write-only; provision locally.',10,C['muted']),button(34,630,134,'Connect'),button(182,630,134,'Pause'),button(34,675,282,'Save candidate'),text(34,735,'Active profile is never overwritten directly.',10,C['muted'])]
 s += [rect(350,152,300,600,'white',C['border'],12),text(369,183,'Topic registry',16,weight=700),text(369,207,'Configured topics · not a live traffic tree',11,C['muted']),field(368,233,264,'FILTER TOPICS','Search canonical topics'),text(370,309,'⌄  selvarithik',13,weight=600),text(388,342,'⌄  gateway',13,weight=600),text(408,375,'⌄  GW001',13,weight=600)]
 for y,name,selected in [(413,'telemetry',False),(453,'status',False),(493,'command',False),(533,'command_ack',True),(573,'config',False)]:
  if selected:s.append(rect(360,y-22,280,35,'#EAF2FF',rad=6))
  s += [icon(432,y-17,'message',C['blue'] if selected else C['muted'],16),text(459,y,name,12,C['blue'] if selected else C['navy'],600 if selected else 400)]
 s += [line(368,612,632,612),text(370,637,'Only contract-approved topics.',11,C['muted']),text(370,660,'No wildcard subscriptions added.',11,C['muted']),button(368,687,127,'Subscribe',disabled=True),button(505,687,127,'Unsubscribe',disabled=True),text(370,740,'General subscription API not implemented.',10,C['muted'])]
 s += [rect(666,152,684,600,'white',C['border'],12),text(686,183,'Messages & diagnostics',16,weight=700),button(1167,166,163,'Test connection'),pill(686,205,'QoS 1 only',w=101),pill(798,205,'Retain off','#F0F4FA',C['muted'],96),text(686,258,'selvarithik/gateway/GW001/command_ack',13,weight=600),text(686,281,'ACK and RESPONSE belong to the same command ID.',11,C['muted']),line(686,300,1330,300),rect(686,316,644,34,'#F5F8FC',rad=5),text(698,338,'Time',11,C['muted'],600),text(790,338,'Topic',11,C['muted'],600),text(1070,338,'QoS',11,C['muted'],600),text(1140,338,'Payload',11,C['muted'],600),icon(981,382,'message',C['muted'],30),text(849,445,'Live topic feed needs backend support',15,weight=600),text(823,471,'The current API exposes diagnostics, not arbitrary message browsing.',11,C['muted']),text(837,498,'No invented counts, retained flags or broker messages.',11,C['muted']),line(686,534,1330,534),text(686,562,'Publish message',14,weight=700),pill(1112,544,'Backend groundwork required','#FFF4E7','#946229',218),field(686,591,644,'Topic · canonical registry only','Select an authorized topic'),rect(686,647,489,73,'#F5F8FC',C['border'],7),text(699,671,'{ }',13,C['muted']),text(699,698,'Custom publish is unavailable in the current API.',10,C['muted']),button(1190,659,140,'Publish',disabled=True),text(686,739,'Available now: TLS test · authentication test · bounded QoS 1 PROBE',10,C['muted'])]
 end(s,'mqtt-desktop.svg')
def mobile(mqtt_page=False,expanded=False):
 s=start(390,844);s.append(apphead('MQTT' if mqtt_page else 'Command Center','',True))
 if mqtt_page:
  s += [text(16,108,'MQTT',20,weight=700),text(16,130,'Profiles & verified diagnostics',12,C['muted']),rect(16,150,358,42,'white',C['border'],8),pill(22,158,'Profiles',w=98),text(146,176,'Topics',12,C['muted']),text(264,176,'Messages',12,C['muted']),rect(16,206,358,570,'white',C['border'],12),text(32,236,'EMQX · existing profile',16,weight=700),pill(32,253,'Preview · not connected','#E9EEF5',C['muted'],181),field(32,304,326,'profile_name','ESP32_LORA_GATEWAY001'),field(32,369,326,'host','n1161c10.ala.eu-central-1.emqxsl.com'),field(32,435,150,'port','8883'),field(196,435,162,'mqtt_version','3.1.1'),icon(32,501,'shield',C['green']),text(61,517,'TLS verification stays enabled',12,C['green'],600),text(32,558,'▸ Credentials & CA certificate',13,C['blue']),text(32,595,'▸ Topics & advanced options',13,C['blue']),text(32,641,'Passwords are never read back.',11,C['muted']),button(32,669,156,'Connect'),button(202,669,156,'Pause'),button(32,716,326,'Save candidate',True),text(25,815,'Tabs replace narrow desktop columns.',12,C['muted'])]
 else:
  s += [rect(0,78,390,68,'white'),icon(14,100,'arrow'),text(41,105,'Nodes',11,C['blue']),text(104,103,'Master ESP32',15,weight=700),text(104,125,'MASTER · recorded test',11,C['muted']),icon(346,99,'more'),line(0,146,390,146),pill(84,165,'27 October · recorded example','#E9EEF5',C['muted'],224),rect(134,219,240,81,'#E7F0FF',rad=12),text(150,243,'PING',14,C['blue'],700),text(150,265,'Check Master response',12),text(150,285,'21:36 · Sent',10,C['muted']),rect(16,319,287,53,'white',C['border'],12),icon(30,335,'check',C['green'],18),text(58,341,'ACK · ACCEPTED',12,C['green'],600),text(58,358,'Accepted ≠ completed',11,C['muted']),rect(16,388,326,169,'white',C['border'],12),text(32,415,'Master ESP32',13,weight=700),pill(204,395,'COMPLETED','#E8F7F1',C['green'],122),text(32,446,'Execution response',14,weight=600),text(32,475,'{ "ok": true }',14),line(32,490,325,490),text(32,516,'▸ Technical details',12,C['blue']),icon(292,502,'copy',C['muted'],18),text(32,539,'CMD-30FEAD0494DC · 21:36:19',10,C['muted']),text(24,699,'Configuration opens as a bottom sheet.',11,C['muted']),rect(0,732,390,112,'white'),line(0,732,390,732),text(16,755,'PING → Master ESP32',11,C['muted']),rect(16,770,245,46,'#F5F8FC',C['border'],8),text(29,799,'PING',14),icon(226,784,'chevron',C['muted'],17),rect(271,770,46,46,'white',C['border'],8),icon(284,783,'sliders'),rect(327,770,47,46,C['blue'],rad=8),icon(341,783,'send','white'),text(16,835,'Preview only · sending is disabled',10,C['muted'])]
 if expanded and not mqtt_page:
  s += [rect(0,298,390,434,'white',C['border'],16),rect(167,309,56,4,'#D3E3FD',rad=2),text(20,341,'Command configuration',16,weight=700),text(344,340,'×',22,C['muted']),field(20,369,350,'Target device','Master ESP32'),field(20,435,350,'Response timeout (seconds)','30'),field(20,501,350,'Maximum retries','3'),field(20,567,350,'Arguments · JSON','{ "message": "Connectivity check" }'),text(20,635,'Advanced · ACK 5 s · Expiry 300 s',11,C['muted']),button(20,677,102,'Reset'),button(132,677,102,'Cancel'),button(244,677,126,'Apply',True)]
 end(s,'mqtt-mobile.svg' if mqtt_page else 'command-mobile-expanded.svg' if expanded else 'command-mobile.svg')

# V2: preserve the approved layout, replace only the conversation design.
base_command=command
base_mobile=mobile
MASTER='ESP32-10777D842178'
CID='CMD-30FEAD0494DC'

def route_card(x,y,w,sender,target,status,outcome,mobile=False):
    h=106 if mobile else 58
    s=rect(x,y,w,h,'#F1F4F8','#BCC9D8',7)
    fields=[('From Device',sender,None),('To',target,None),('Status',status,'status'),('Execution outcome',outcome,'outcome')]
    cols=2 if mobile else 4;cw=w/cols
    if mobile:
        s+=line(x,y+53,x+w,y+53,'#C6D1DF')
        s+=line(x+cw,y+8,x+cw,y+h-8,'#C6D1DF')
    else:
        for i in range(1,4):s+=line(x+i*cw,y+9,x+i*cw,y+h-9,'#C6D1DF')
    for i,(label,value,kind) in enumerate(fields):
        xx=x+(i%cols)*cw+11;yy=y+(i//cols)*53
        s+=text(xx,yy+18,label,11.5,'#4A5F76',600)
        if kind:
            colors={'SENT':('#E0EBFF','#004BAE'),'ACCEPTED':('#D9F2E7','#006D4F'),'COMPLETED':('#D9F2E7','#006D4F'),'Pending':('#FFF0CE','#835307'),'Not reported':('#E5EAF0','#475B70'),'Executed':('#D9F2E7','#006D4F'),'FAILED':('#FCE0E4','#AC2338')}
            fill,ink=colors[value];bw=min(cw-20,len(value)*6.2+16)
            s+=pill(xx,yy+25,value,fill,ink,bw)
        else:
            # Full device ID remains available as a tooltip; shorten only if needed.
            shown=value if cw>=145 or len(value)<17 else value[:11]+'…'+value[-4:]
            s+='<g><title>'+E(value)+'</title>'+text(xx,yy+39,shown,12,'#07305B',600)+'</g>'
    return s

def footer(x,y,cid,stamp,details=False,w=650):
    s=text(x,y,cid,10.5,'#435C77',500)+text(x+w-105,y,stamp,10.5,'#435C77',500)
    if details:s+=text(x+w-265,y,'Details · Copy response',10.5,'#0055C9',600)
    return s

def bubble(x,y,w,kind,status,outcome,sender,target,stamp,body='',mobile=False):
    if mobile:
        h=170 if kind!='RESPONSE' else 177
        s=rect(x,y,w,h,'#DBEAFE' if kind=='COMMAND' else 'white','#9EB9D8' if kind=='COMMAND' else '#AABED5',10)
        title='PING · command request' if kind=='COMMAND' else 'ACK · device acceptance' if kind=='ACK' else 'RESPONSE · { "ok": true }'
        s+=text(x+12,y+23,title,13,'#004BAE' if kind=='COMMAND' else '#07305B',700)
        s+=route_card(x+12,y+33,w-24,sender,target,status,outcome,True)
        s+=text(x+12,y+h-13,CID,10,'#435C77')+text(x+w-67,y+h-13,stamp,10,'#435C77')
        return s
    h=120 if kind=='COMMAND' else 118 if kind=='ACK' else 145
    fill='#DBEAFE' if kind=='COMMAND' else 'white'
    s=rect(x,y,w,h,fill,'#9EB9D8' if kind=='COMMAND' else '#AABED5',10)
    label='PING · command request' if kind=='COMMAND' else 'ACK · device acceptance' if kind=='ACK' else 'RESPONSE · execution result'
    s+=text(x+16,y+24,label,13,'#004BAE' if kind=='COMMAND' else '#07305B',700)
    card_y=y+34
    if kind=='RESPONSE':
        s+=text(x+16,y+48,'{ "ok": true }',13,'#07305B',600);card_y=y+58
    s+=route_card(x+16,card_y,w-32,sender,target,status,outcome)
    s+=footer(x+16,y+h-12,CID,stamp,kind=='RESPONSE',w-32)
    return s

def command(expanded=False):
    base_command(expanded)
    name='command-expanded.svg' if expanded else 'command-desktop.svg'
    p=out/name;s=p.read_text(encoding='utf-8').removesuffix('</g></svg>')
    # This overlay represents the conversation area resizing, not a floating card.
    height=229 if expanded else 458
    s+=rect(301,205,1048,height,'#E8EFF7')
    s+='<defs><pattern id="route-dots" width="24" height="24" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="0.7" fill="#9EB4CC" opacity="0.25"/></pattern></defs>'
    s+=rect(301,205,1048,height,'url(#route-dots)')
    s+=pill(681,214,'27 October · recorded command history','#D9E4F1','#294968',277)
    if expanded:
        s+=bubble(330,261,780,'RESPONSE','COMPLETED','Executed',MASTER,'GATEWAY','21:36:19')
    else:
        s+=bubble(623,250,695,'COMMAND','SENT','Pending','GATEWAY',MASTER,'21:36:18')
        s+=bubble(330,378,745,'ACK','ACCEPTED','Not reported',MASTER,'GATEWAY','21:36:18')
        s+=bubble(330,504,780,'RESPONSE','COMPLETED','Executed',MASTER,'GATEWAY','21:36:19')
    # A restrained status key explains semantics without relying on color alone.
    s+=rect(570,161,625,44,'#FAFCFF')
    for x,label,fill,ink,w in [(645,'Info','#E0EBFF','#004BAE',51),(703,'Pending','#FFF0CE','#835307',78),(788,'Confirmed','#D9F2E7','#006D4F',93),(888,'Failed','#FCE0E4','#AC2338',65)]:s+=pill(x,171,label,fill,ink,w)
    s+=text(976,188,'ACK ≠ execution',12,'#435C77',600)
    p.write_text(s+'</g></svg>',encoding='utf-8')

def mobile(mqtt_page=False,expanded=False):
    if mqtt_page:return base_mobile(True,expanded)
    s=start(390,844);s.append(apphead('Command Center','',True))
    s += [rect(0,78,390,68,'white'),icon(14,100,'arrow'),text(41,105,'Nodes',12,C['blue']),text(104,103,'Master ESP32',15,weight=700),text(104,125,'MASTER · recorded test',12,C['muted']),icon(346,99,'more'),line(0,146,390,146),rect(0,146,390,586,'#E8EFF7'),pill(72,153,'Recorded command · 27 October','#D9E4F1','#294968',245)]
    s += [bubble(70,184,304,'COMMAND','SENT','Pending','GATEWAY',MASTER,'21:36:18',mobile=True),bubble(16,365,328,'ACK','ACCEPTED','Not reported',MASTER,'GATEWAY','21:36:18',mobile=True),bubble(16,546,358,'RESPONSE','COMPLETED','Executed',MASTER,'GATEWAY','21:36:19',mobile=True)]
    s += [rect(0,732,390,112,'white'),line(0,732,390,732),text(16,754,'PING → Master ESP32',12,C['muted']),rect(16,770,245,46,'#EEF3FA',C['border'],8),text(29,799,'PING',14),icon(226,784,'chevron',C['muted'],17),rect(271,770,46,46,'white',C['border'],8),icon(284,783,'sliders'),rect(327,770,47,46,C['blue'],rad=8),icon(341,783,'send','white'),text(16,835,'Design preview · sending disabled',11,C['muted'])]
    if expanded:
        s += [rect(0,298,390,434,'white',C['border'],16),rect(167,309,56,4,'#A6BAD1',rad=2),text(20,341,'Command configuration',16,weight=700),text(344,340,'×',22,C['muted']),field(20,369,350,'Target device','Master ESP32'),field(20,435,350,'Response timeout (seconds)','30'),field(20,501,350,'Maximum retries','3'),field(20,567,350,'Arguments · JSON','{ "message": "Connectivity check" }'),text(20,635,'Advanced · ACK 5 s · Expiry 300 s',12,C['muted']),button(20,677,102,'Reset'),button(132,677,102,'Cancel'),button(244,677,126,'Apply',True)]
    end(s,'command-mobile-expanded.svg' if expanded else 'command-mobile.svg')

command();command(True);mqtt();mobile();mobile(True);mobile(False,True)
html='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>SELVARITHIK A&D · Design review</title><style>*{box-sizing:border-box}body{margin:0;background:#eaf0f7;color:#07305b;font-family:Segoe UI,Arial,sans-serif}.review{background:#07305b;color:white;padding:18px 24px;display:flex;gap:24px;align-items:center;justify-content:space-between}.review h1{font-size:18px;margin:0}.review p{font-size:12px;color:#c7daed;margin:5px 0 0}.tools{display:flex;gap:8px;flex-wrap:wrap}button,a{font:inherit}button{border:1px solid #bed0e6;padding:10px 14px;border-radius:7px;background:white;color:#07305b;cursor:pointer}button[aria-pressed=true]{background:#0066ff;color:white;border-color:#0066ff}button:focus-visible,a:focus-visible{outline:3px solid #00c98d;outline-offset:3px}main{max-width:1440px;margin:18px auto;padding:0 18px}.frame{background:white;border:1px solid #d3e3fd;border-radius:12px;overflow:hidden}.frame img{width:100%;height:auto;display:block}.mobile{display:none}.notes{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;font-size:13px;line-height:1.65;margin:18px 0 26px}.notes article{background:white;border:1px solid #d3e3fd;padding:16px;border-radius:9px}.notes h2{font-size:14px;margin:0 0 6px}.notes p{margin:0}.caption{font-size:12px;margin:12px 0;color:#607995}@media(max-width:760px){.review{align-items:start;flex-direction:column;gap:14px;padding:16px}.tools{gap:6px}button{font-size:12px;padding:9px}.desktop{display:none!important}.mobile{display:block!important;max-width:390px;margin:auto}.notes{grid-template-columns:1fr}main{padding:0 10px;margin-top:10px}}@media(prefers-reduced-motion:no-preference){button{transition:background .15s}} </style><header class="review"><div><h1>SELVARITHIK A&D · Design V2</h1><p>Design review only. No live routes, settings, firmware or backend connections changed.</p></div><nav class="tools" aria-label="Preview pages"><button data-page="command" aria-pressed="true">Command Center</button><button data-page="mqtt" aria-pressed="false">MQTT workspace</button><button id="expand" aria-pressed="false">Show configuration</button></nav></header><main><div class="frame"><img class="desktop" id="desktop" src="command-desktop.svg" alt="Proposed compact Command Center desktop layout"><img class="mobile" id="mobile" src="command-mobile.svg" alt="Proposed mobile Command Center"></div><p class="caption">Desktop reference: 1366 × 768. Narrow windows switch to the mobile design. Commands shown are recorded examples, never live status.</p><section class="notes"><article><h2>Compact shared header</h2><p>Stronger navy text, clearer borders and contrasting conversation backgrounds. Existing red branding, logo and compact header are retained.</p></article><article><h2>Inline route cards</h2><p>Four fields inside every message: From Device, To, Status and Execution outcome. Desktop uses four columns; mobile uses two. Command IDs and timestamps stay in the footer.</p></article><article><h2>MQTT stays truthful</h2><p>Canonical profiles and staged switching stay intact. Verified TLS and QoS 1 remain required. Generic topic capture and custom publish/subscription controls need backend support and are disabled.</p></article></section></main><script>let page='command',expanded=false;const d=document.getElementById('desktop'),m=document.getElementById('mobile'),expand=document.getElementById('expand');function render(){d.src=page==='mqtt'?'mqtt-desktop.svg':expanded?'command-expanded.svg':'command-desktop.svg';m.src=page==='mqtt'?'mqtt-mobile.svg':expanded?'command-mobile-expanded.svg':'command-mobile.svg';expand.hidden=page==='mqtt';expand.setAttribute('aria-pressed',String(expanded));expand.textContent=expanded?'Hide configuration':'Show configuration';document.querySelectorAll('[data-page]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.page===page)))}document.querySelectorAll('[data-page]').forEach(b=>b.addEventListener('click',()=>{page=b.dataset.page;render()}));expand.addEventListener('click',()=>{expanded=!expanded;render()});</script></html>'''
(out/'index.html').write_text(html,encoding='utf-8',newline='\n')
print('Created 5 SVG design screens and isolated offline preview HTML')
