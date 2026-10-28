(() => {
 'use strict';
 const root=document.querySelector('.operations-overview');if(!root)return;
 let busy=false;
 const esc=value=>String(value??'Unknown').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const card=(name,value,detail)=>'<article><small>'+esc(name)+'</small><strong>'+esc(value)+'</strong><small>'+esc(detail)+'</small></article>';
 function deviceCard(n){
  const x=n.reported,network=n.diagnostics.GET_NETWORK,radio=n.diagnostics.GET_RADIO_STATUS,fresh=n.health==='ONLINE';
  const wifi=!fresh?'Unknown now; historical '+(x.wifi_connected===true?'connected report':x.wifi_connected===false?'disconnected report':'report unavailable'):x.wifi_connected===true?'Connected · '+x.wifi_rssi+' dBm':x.wifi_connected===false?'Disconnected':'Unknown';
  const fields=[['Device ID',n.node_id],['Role / parent',n.device_role+(n.device_role==='NODE'?' / '+n.master_id:'')],['Hardware MAC',x.hardware_mac||n.hardware_mac],['Firmware name',x.device_name],['Firmware',x.firmware_version||n.firmware_version],['Last seen',n.last_seen],['Transport (last report)',x.transport],['Wi-Fi',wifi],['Last queried IP',network?.data.station_ip||network?.data.ip||'Use GET_NETWORK to query'],['Network query time',network?.received_at||'Unavailable'],['Gateway receipt',!fresh?'Historical report; current state unknown':x.gateway_reachable===true?'Direct receipt confirmed':x.gateway_reachable===false?'No direct receipt; relay may be used':'Unknown'],['Last queried radio',radio?.data.state||'Not queried; RF unverified'],['Radio query time',radio?.received_at||'Unavailable']];
  return '<article class="operations-device"><header><h3>'+esc(n.name||x.device_name||n.node_id)+'</h3><span class="operations-state '+esc((n.health||'UNKNOWN').toLowerCase())+'">'+esc(n.health)+'</span></header><dl>'+fields.map(([k,v])=>'<dt>'+esc(k)+'</dt><dd>'+esc(v)+'</dd>').join('')+'</dl></article>';
 }
 function radioEvidence(devices){
  if(root.dataset.operationsView!=='mesh')return;
  let section=root.querySelector('.operations-radio-data');if(!section){section=document.createElement('section');section.className='operations-radio-data';root.append(section);}
  let rows='',routes='';
  for(const n of devices){
   const radio=n.diagnostics.GET_RADIO_STATUS,route=n.diagnostics.GET_ROUTE_INFO;
   if(radio){const d=radio.data;rows+='<tr>'+[n.node_id,d.state,d.tx_uart_fragments,d.rx_messages,d.auth_failures,d.timeouts,radio.received_at].map(x=>'<td>'+esc(x)+'</td>').join('')+'</tr>';}
   for(const path of route?.data.routes||[])routes+='<tr>'+[n.node_id,path.destination,path.next_hop,path.hop_count,path.age_ms,route.received_at].map(x=>'<td>'+esc(x)+'</td>').join('')+'</tr>';
  }
  section.innerHTML='<h3>Firmware command observations</h3><p>Read-only GET_RADIO_STATUS and GET_ROUTE_INFO responses. UART writes are not RF acknowledgements. RF RSSI/SNR and packet-loss percentages are unavailable unless measured.</p><div class="table-wrap"><table class="table"><thead><tr><th>Device</th><th>Radio state</th><th>TX UART fragments</th><th>RX messages</th><th>Auth failures</th><th>Timeouts</th><th>Query time</th></tr></thead><tbody>'+(rows||'<tr><td colspan="7">No completed radio query. Use Command Center to request GET_RADIO_STATUS.</td></tr>')+'</tbody></table></div><h3>Reported next-hop routes</h3><p>A reported route is not proof of end-to-end RF delivery. No links are inferred from saved parent assignments.</p><div class="table-wrap"><table class="table"><thead><tr><th>Reporter</th><th>Destination</th><th>Next hop</th><th>Hops</th><th>Age at query (ms)</th><th>Query time</th></tr></thead><tbody>'+(routes||'<tr><td colspan="6">No firmware-reported radio routes.</td></tr>')+'</tbody></table></div>';
 }
 async function refresh(){
  if(busy||document.hidden)return;busy=true;
  try{
   const response=await fetch('/api/operations/overview',{cache:'no-store',signal:AbortSignal.timeout(9000)});
   if(!response.ok)throw Error(response.status===401?'Sign in required':'Overview unavailable');
   const data=await response.json();
   root.querySelector('.operations-feedback').textContent='Updated '+new Date(data.observed_at).toLocaleTimeString()+'. Parent assignment is configured; it does not prove an RF link.';
   root.querySelector('.operations-health').innerHTML=card('Fleet',data.online+' online',data.master_count+' Master · '+data.registered_nodes+' registered Node')+card('Local IP',data.local_ip.state,data.local_ip.accepted+' persisted exchanges')+card('MQTT',data.mqtt.state,data.mqtt.last_error||data.mqtt.acl_status)+card('Ethernet',data.ethernet,'LoRa RF delivery not verified');
   const devices=root.querySelector('.operations-devices');
   if(devices)devices.innerHTML=data.devices.map(deviceCard).join('')||'<p>No enrolled devices. Register an actual device in Device Management.</p>';
   radioEvidence(data.devices);
  }catch(error){root.querySelector('.operations-feedback').textContent=error.message+'; previous snapshot retained.';}
  finally{busy=false;}
 }
 root.querySelector('.operations-refresh').addEventListener('click',refresh);
 document.addEventListener('visibilitychange',()=>{if(!document.hidden)refresh();});
 refresh();setInterval(refresh,10000);
})();
