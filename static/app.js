let current=null, busy=false;
const $=id=>document.getElementById(id);
async function login(){try{let r=await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({password:$('pass').value})});let d=await r.json();if(!r.ok)throw Error(d.detail||'Login failed');$('login').classList.add('hidden');$('app').classList.remove('hidden');await loadChats();if(!current)await newChat();}catch(e){$('loginerr').textContent=e.message}}
$('pass').addEventListener('keydown',e=>{if(e.key==='Enter')login()});
async function logout(){await fetch('/api/logout',{method:'POST'});location.reload()}
async function loadChats(){let r=await fetch('/api/chats');if(r.status===401)return;let list=await r.json();$('history').innerHTML='';list.forEach(c=>{let b=document.createElement('button');b.className='history-item';b.textContent=c.title||'Chat';b.onclick=()=>openChat(c.id);$('history').append(b)})}
async function newChat(){let r=await fetch('/api/chats',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({title:'New chat'})});let d=await r.json();current=d.id;$('messages').innerHTML='';showWelcome();await loadChats()}
function showWelcome(){ $('messages').innerHTML='<div class="welcome"><div class="orb">✦</div><h1>What can I help you with?</h1><p>Ideas, code, research or creative work. Start anywhere.</p></div>'}
async function openChat(id){current=id;let r=await fetch('/api/chats/'+id);let msgs=await r.json();$('messages').innerHTML='';msgs.forEach(m=>addMessage(m.role,m.content));$('messages').scrollTop=$('messages').scrollHeight}
function addMessage(role,text){let div=document.createElement('div');div.className='message '+role;div.textContent=text;$('messages').append(div);$('messages').scrollTop=$('messages').scrollHeight}
function suggest(text){$('input').value=text;$('input').focus()}
async function send(){if(busy)return;let input=$('input');let text=input.value.trim();if(!text||!current)return;busy=true;input.value='';$('messages').querySelector('.welcome')?.remove();addMessage('user',text);let loading=document.createElement('div');loading.className='message assistant';loading.textContent='Thinking…';$('messages').append(loading);try{let r=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({chat_id:current,message:text,model:$('model').value})});let d=await r.json();if(!r.ok)throw Error(d.detail||'Request failed');loading.textContent=d.answer}catch(e){loading.textContent='Error: '+e.message}busy=false;await loadChats()}
function keySend(e){if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send()}}
function toggleSide(){$('.sidebar').classList.toggle('open')}
                                                                                                                                                       
