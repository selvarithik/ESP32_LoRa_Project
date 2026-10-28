'use strict';
const form=document.getElementById('login-form'),feedback=document.getElementById('feedback'),button=document.getElementById('signin'),password=document.getElementById('password');
document.getElementById('visibility').onclick=function(){const visible=password.type==='password';password.type=visible?'text':'password';this.textContent=visible?'Hide password':'Show password';this.setAttribute('aria-pressed',String(visible));};
form.onsubmit=async event=>{event.preventDefault();button.disabled=true;feedback.textContent='Signing in…';try{const r=await fetch('/api/auth/login',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':form.dataset.csrf},body:JSON.stringify({username:form.elements.username.value,password:password.value})});const d=await r.json();if(!r.ok)throw Error(d.error||'Sign-in failed');password.value='';location.assign(d.redirect==='/accounts'?'/accounts':'/');}catch(error){feedback.textContent=error.message;}finally{button.disabled=false;}};

const localTest=document.getElementById('local-test-session');
if(localTest)localTest.onclick=async()=>{localTest.disabled=true;feedback.textContent='Starting local test session…';try{const r=await fetch('/api/auth/local-test-session',{method:'POST',headers:{'Content-Type':'application/json','X-Local-Test':'1'},body:'{}'});const d=await r.json();if(!r.ok)throw Error(d.error||'Local test session unavailable');location.assign('/');}catch(error){feedback.textContent=error.message;}finally{localTest.disabled=false;}};

// Remember only the username when the user explicitly selects it; never persist a password/session.
const remember=document.getElementById('remember-username'),username=document.getElementById('username');
try{const saved=localStorage.getItem('gateway_remembered_username');if(saved&&remember&&username){username.value=saved;remember.checked=true;}}catch(_){}
form.addEventListener('submit',()=>{try{if(remember?.checked)localStorage.setItem('gateway_remembered_username',username.value);else localStorage.removeItem('gateway_remembered_username');}catch(_){}});
document.getElementById('forgot-password')?.addEventListener('click',()=>document.getElementById('recovery-help').showModal());
