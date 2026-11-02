/* Read-only display of the existing operations feed. Never sends a device command. */
(function () {
 'use strict';
 function reportedFacts(data) {
  const masters=(Array.isArray(data?.devices)?data.devices:[]).filter(n=>n.device_role==='MASTER');
  if(masters.length!==1)return {gateway:masters.length?masters.length+' Masters':'Not reported',frequency:'Unverified',uptime:'Not reported',evidence:masters.length?'Select a Master in Device Management':'No Master report available'};
  const n=masters[0],r=n.reported||{},radio=n.diagnostics?.GET_RADIO_STATUS,channel=radio?.data?.observed?.channel;
  // E220-900 register mapping: channel 0 is 850.125 MHz, increments are 1 MHz.
  // A completed register read is historical evidence, not a verified RF link.
  const frequency=radio?.data?.public_settings_read===true&&Number.isInteger(channel)&&channel>=0&&channel<=83?(850.125+channel).toFixed(3)+' MHz':'Unverified';
  const seconds=r.uptime_s,valid=typeof seconds==='number'&&Number.isFinite(seconds)&&seconds>=0;
  const uptime=valid?(Math.floor(seconds/86400)?Math.floor(seconds/86400)+'d ':'')+Math.floor(seconds%86400/3600)+'h '+Math.floor(seconds%3600/60)+'m':'Not reported';
  return {gateway:n.node_id||'Not reported',frequency,uptime,evidence:n.health==='ONLINE'?'Last Master report':'Historical Master report',lastSeen:n.last_seen||'Unknown',radioTime:radio?.received_at||'Not queried'};
 }
 if(typeof module==='object'&&module.exports)module.exports={reportedFacts};
 if(typeof document==='undefined')return;
 document.addEventListener('gateway:operations',event=>{
  if(!document.getElementById('banner-gateway'))return;
  const facts=reportedFacts(event.detail);
  for(const key of ['gateway','frequency','uptime','evidence']){
   const element=document.getElementById('banner-'+key);element.textContent=facts[key];
   element.title=key==='frequency'?'E220 register query: '+(facts.radioTime||'Unavailable')+'. RF link not inferred.':key==='uptime'?'Last reported device uptime; last seen '+(facts.lastSeen||'Unknown'):facts[key];
  }
 });
})();
