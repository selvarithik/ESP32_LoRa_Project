"use strict";
document.addEventListener("DOMContentLoaded", () => {
 const root = document.getElementById("accounts-app");
 let csrf = root.dataset.csrf, actor, records = [], editing;
 const message = document.getElementById("account-message");
 const editor = document.getElementById("account-editor");
 const signIn = document.getElementById("account-sign-in");
 async function api(url, method = "GET", body) {
   const response = await fetch(url, {method, headers: {"Content-Type":"application/json", "X-CSRF-Token":csrf}, body: body ? JSON.stringify(body) : undefined});
   const data = await response.json();
   if(response.status===401){location.assign('/login');throw new Error('Sign in again.');}
   if (!response.ok) throw new Error(data.error || "Account request failed.");
   if(data.reauthenticate){location.assign('/login');return data;}
   if (data.csrf) csrf = data.csrf;
   return data;
 }
 function openEditor(record) {
   editing = record;
   editor.reset(); editor.hidden = false;
   editor.elements.name.value = record?.name || "";
   editor.elements.username.value = record?.username || "";
   editor.elements.role.value = record?.role || "user";
   editor.elements.role.disabled = actor.role !== "creator";
   editor.elements.password.required = !record || !!actor.must_change;
   editor.elements.confirm_password.required = !record || !!actor.must_change;
   document.getElementById("account-current-label").hidden = !record || record.id !== actor.id;
   document.getElementById("account-editor-title").textContent = record ? "Edit account" : "Create account";
   editor.elements.name.focus();
 }
 async function load() {
   const data = await api("/api/accounts"); actor = data.user; records = data.accounts;
   signIn.hidden = true; document.getElementById("account-workspace").hidden = false;
   document.getElementById("account-identity").textContent = actor.name + " · " + actor.username;
   document.getElementById('account-role').textContent='Account type: '+actor.role+(actor.must_change?' · Temporary password: replace it now.':' · Password configured');
   document.getElementById("account-new").hidden = actor.role === "user";
   const rows = document.getElementById("account-rows"); rows.replaceChildren();
   for (const record of records) {
     const row = document.createElement("tr");
     for (const field of ["name","username","role"]) { const cell = document.createElement("td"); cell.textContent = record[field]; row.append(cell); }
     const actions = document.createElement("td"); row.append(actions);
     const allowed = actor.id === record.id || actor.role === "creator" || (actor.role === "administrator" && record.role === "user");
     if (allowed) {
       const edit = document.createElement("button"); edit.className = "btn"; edit.textContent = "Edit"; edit.onclick = () => openEditor(record); actions.append(edit);
       if (actor.id !== record.id) {
         const remove = document.createElement("button"); remove.className = "btn"; remove.textContent = "Delete";
         remove.onclick = async () => { if (!confirm("Delete account " + record.username + "?")) return; try { await api("/api/accounts/" + record.id,"DELETE"); await load(); message.textContent = "Account deleted."; } catch(e) {message.textContent=e.message;} };
         actions.append(remove);
       }
     }
     rows.append(row);
   }
   if(actor.must_change){document.getElementById('account-new').hidden=true;openEditor(actor);}
 }
 signIn.onsubmit = async event => {event.preventDefault(); try {await api("/api/accounts/sign-in","POST",Object.fromEntries(new FormData(signIn))); signIn.reset(); await load(); message.textContent="Signed in.";} catch(e) {message.textContent=e.message;}};
 editor.onsubmit = async event => {event.preventDefault(); const data = Object.fromEntries(new FormData(editor)); if(data.password!==data.confirm_password){message.textContent='Password confirmation differs.';return;}delete data.confirm_password;if (editor.elements.role.disabled) data.role = editing?.role || "user"; const submit=editor.querySelector('[type=submit]')||editor.querySelector('button');submit.disabled=true;try {const result=await api(editing ? "/api/accounts/"+editing.id : "/api/accounts",editing ? "PATCH" : "POST",data);if(result.reauthenticate)return;editor.reset(); editor.hidden=true; await load(); message.textContent="Account saved.";} catch(e) {message.textContent=e.message;}finally{submit.disabled=false;}};
 document.getElementById('account-show-password').onclick=function(){const show=this.getAttribute('aria-pressed')!=='true';for(const name of ['password','confirm_password','current_password'])editor.elements[name].type=show?'text':'password';this.setAttribute('aria-pressed',String(show));this.textContent=show?'Hide passwords':'Show passwords';};
 document.getElementById("account-new").onclick = () => openEditor(null);
 document.getElementById("account-cancel").onclick = () => {editor.reset();editor.hidden=true;};
 load().catch(e => {message.textContent=e.message;});
});
