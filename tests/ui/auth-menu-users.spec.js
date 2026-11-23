const { launch, server, fixtureServer, SH, ROOT } = require('./lib');
let B;
(async()=>{const srv=await server('legacy',{});B=srv.base;const b=await launch();
const errs=[],fails=[];const ck=(c,m)=>{console.log((c?'ok   ':'FAIL ')+m);if(!c)fails.push(m)};
const hook=(p,tag)=>{p.on('pageerror',e=>errs.push(tag+' pageerror '+e.message));p.on('console',m=>{if(['error','warning'].includes(m.type())&&!/status of (401|403|429|400)/.test(m.text()))errs.push(tag+' console '+m.text())});};
const c1=await b.newContext({viewport:{width:1280,height:900},colorScheme:'light'});const p=await c1.newPage();hook(p,'admin');
await p.goto((B+'/login'));await p.waitForSelector('#login:not(.hidden)');
// setup screen toggles
ck(await p.isVisible('#fieldSetupKey')&&await p.isVisible('#loginLang')&&await p.isVisible('#loginTheme'),'setup shows key field + toggles');
ck(await p.evaluate(()=>[...document.querySelectorAll('#loginForm label')].filter(l=>l.offsetParent).every(l=>l.textContent.trim().length>0)),'visible labels');
await p.screenshot({path:SH+'m-setup-light-id.png'});
await p.click('#loginLang');ck((await p.textContent('#loginTitle'))==='Create First Admin'&&(await p.textContent('#loginLangCode'))==='EN','setup EN: '+await p.textContent('#loginTitle'));
ck((await p.textContent('#loginForm label[for=loginUser]'))==='Username'&&(await p.textContent('#loginSubmit'))==='Create Admin','labels/button EN');
await p.click('#loginTheme');ck(await p.evaluate(()=>document.documentElement.dataset.theme)==='dark','theme dark');
await p.screenshot({path:SH+'m-setup-dark-en.png'});
// card centered
const cen=await p.evaluate(()=>{const r=document.getElementById('loginForm').getBoundingClientRect();return [Math.abs((r.left+r.right)/2-innerWidth/2),Math.abs((r.top+r.bottom)/2-innerHeight/2)]});ck(cen[0]<2&&cen[1]<2,'card centered '+cen);
await p.fill('#setupKey','testkey123');await p.fill('#loginUser','admin');await p.fill('#loginPass','password1');await p.fill('#loginPass2','password1');await p.click('#loginSubmit');
await p.waitForSelector('#app:not(.hidden)');await p.waitForTimeout(1000);
ck(await p.evaluate(()=>document.documentElement.lang==='en'&&document.documentElement.dataset.theme==='dark'),'lang+theme carry over after login');
ck(await p.evaluate(()=>[...document.querySelectorAll('.segmented [data-lang]')].find(b=>b.dataset.lang==='en').getAttribute('aria-pressed')==='true'),'EN pressed in app');
// menu
await p.click('#userBtn');await p.waitForSelector('.menu.user-menu');
ck(await p.getAttribute('#userBtn','aria-expanded')==='true'&&await p.getAttribute('#userBtn','aria-haspopup')==='menu','aria attrs');
ck((await p.textContent('.menu-head')).includes('admin')&&(await p.textContent('.menu-head')).includes('Admin ·'),'header: '+await p.textContent('.menu-head'));
const items=await p.locator('.user-menu [role=menuitem]').allTextContents();ck(JSON.stringify(items)===JSON.stringify(['Reload','Change Password','Manage Users','Log Out']),'items '+JSON.stringify(items));
await p.screenshot({path:SH+'m-menu-dark-en.png'});
ck(await p.evaluate(()=>document.activeElement.textContent.trim()==='Reload'),'first item focused');
await p.keyboard.press('ArrowDown');await p.keyboard.press('End');ck(await p.evaluate(()=>document.activeElement.textContent.trim()==='Log Out'),'End -> Log Out');
await p.keyboard.press('Home');ck(await p.evaluate(()=>document.activeElement.textContent.trim()==='Reload'),'Home -> Reload');
await p.keyboard.press('Escape');ck(await p.evaluate(()=>!document.querySelector('.menu')&&document.activeElement.id==='userBtn'),'Esc closes + focus returns');
await p.click('#userBtn');await p.mouse.click(300,400);await p.waitForTimeout(100);ck(await p.evaluate(()=>!document.querySelector('.menu')),'outside click closes');
await p.click('#userBtn');await p.keyboard.press('Tab');ck(await p.evaluate(()=>!document.querySelector('.menu')),'Tab closes');
// reload item
await p.click('#userBtn');await p.click('.menu >> text=Reload');await p.waitForTimeout(500);ck(await p.isVisible('#app'),'Reload keeps app');
// manage users
await p.click('#userBtn');await p.click('.menu >> text=Manage Users');await p.waitForTimeout(500);
ck(await p.isVisible('#tab-settings')&&await p.evaluate(()=>document.activeElement.id==='usersHeading'),'Manage Users -> settings users heading focused');
// add a user for later
await p.fill('#newUserName','budi');await p.fill('#newUserPass','budipass1');await p.click('#btnAddUser');await p.waitForTimeout(600);
// change password modal
await p.click('#userBtn');await p.click('.menu >> text=Change Password');await p.waitForSelector('#pwModal:not(.hidden)');
ck(await p.evaluate(()=>document.activeElement.id==='pwCur'),'modal focus on first field');
ck(await p.evaluate(()=>document.getElementById('pwForm').getAttribute('aria-modal')==='true'&&document.getElementById('pwForm').getAttribute('aria-labelledby')==='pwTitle'),'modal aria');
await p.screenshot({path:SH+'m-pw-dark-en.png'});
await p.click('#pwSave');ck((await p.textContent('#pwErr')).includes('Required'),'empty -> required: '+await p.textContent('#pwErr'));
await p.fill('#pwCur','password1');await p.fill('#pwNew','short');await p.fill('#pwConf','short');await p.click('#pwSave');ck((await p.textContent('#pwErr')).includes('8'),'short: '+await p.textContent('#pwErr'));
await p.fill('#pwNew','newpass123');await p.fill('#pwConf','different1');await p.click('#pwSave');ck((await p.textContent('#pwErr')).includes('Do Not Match'),'mismatch: '+await p.textContent('#pwErr'));
await p.fill('#pwConf','newpass123');await p.fill('#pwCur','wrongcurrent');await p.click('#pwSave');await p.waitForTimeout(500);ck((await p.textContent('#pwErr')).length>3&&await p.isVisible('#pwModal')&&!(await p.isDisabled('#pwSave')),'wrong current -> server error: '+await p.textContent('#pwErr'));
await p.click('[data-eye=pwNew]');ck(await p.getAttribute('#pwNew','type')==='text'&&await p.getAttribute('[data-eye=pwNew]','aria-pressed')==='true','eye toggles');
for(let i=0;i<12;i++)await p.keyboard.press('Tab');ck(await p.evaluate(()=>document.getElementById('pwModal').contains(document.activeElement)),'focus trapped');
await p.keyboard.press('Escape');ck(await p.evaluate(()=>document.getElementById('pwModal').classList.contains('hidden')&&document.activeElement.id==='userBtn'),'Esc closes, focus -> user button');
await p.click('#userBtn');await p.click('.menu >> text=Change Password');await p.waitForSelector('#pwModal:not(.hidden)');await p.mouse.click(5,5);await p.waitForTimeout(100);ck(await p.evaluate(()=>document.getElementById('pwModal').classList.contains('hidden')),'backdrop closes');
await p.click('#userBtn');await p.click('.menu >> text=Change Password');await p.waitForSelector('#pwModal:not(.hidden)');await p.click('#pwCancel');ck(await p.evaluate(()=>document.getElementById('pwModal').classList.contains('hidden')),'cancel closes');
await p.click('#userBtn');await p.click('.menu >> text=Change Password');await p.waitForSelector('#pwModal:not(.hidden)');
await p.fill('#pwCur','password1');await p.fill('#pwNew','newpass123');await p.fill('#pwConf','newpass123');await p.click('#pwSave');await p.waitForTimeout(700);
ck(await p.evaluate(()=>document.getElementById('pwModal').classList.contains('hidden')),'success closes modal');
ck(await p.isVisible('#app')&&(await p.evaluate(async()=>(await fetch('/api/status',{credentials:'same-origin'})).status))===200,'still logged in after change');
ck((await p.textContent('#toast')).includes('Password Changed'),'toast: '+await p.textContent('#toast'));
// logout via menu
await p.click('#userBtn');await p.click('.menu >> text=Log Out');await p.waitForSelector('h1.hl');await p.goto((B+'/login'));await p.waitForSelector('#login:not(.hidden)');ck(true,'logout from menu (landing, then login)');
ck(await p.evaluate(()=>document.documentElement.dataset.theme==='dark'&&document.documentElement.lang==='en'),'prefs persist on login screen');
await p.click('#loginLang');ck((await p.textContent('#loginTitle'))==='Bara'&&(await p.textContent('#loginForm label[for=loginUser]'))==='Nama Pengguna'&&(await p.textContent('#loginSubmit'))==='Masuk','login EN->ID toggle');
await p.click('#loginLang');ck((await p.textContent('#loginSubmit'))==='Login','back to EN: '+await p.textContent('#loginSubmit'));
await p.screenshot({path:SH+'m-login-dark-id.png'});await p.click('#loginTheme');await p.screenshot({path:SH+'m-login-light-id.png'});
// non-admin
const c2=await b.newContext({viewport:{width:1280,height:900}});const q=await c2.newPage();hook(q,'budi');
await q.goto((B+'/login'));await q.fill('#loginUser','budi');await q.fill('#loginPass','budipass1');await q.click('#loginSubmit');await q.waitForSelector('#app:not(.hidden)');await q.waitForTimeout(800);
await q.click('#userBtn');const qi=await q.locator('.user-menu [role=menuitem]').allTextContents();ck(!qi.some(x=>/Kelola Pengguna|Manage Users/.test(x))&&qi.length===3,'non-admin menu: '+JSON.stringify(qi));
await q.screenshot({path:SH+'m-menu-user-id.png'});await q.keyboard.press('Escape');
// mobile
for(const scheme of ['light','dark']){const c3=await b.newContext({viewport:{width:390,height:844},colorScheme:scheme});const m=await c3.newPage();hook(m,'mob'+scheme);
 await m.goto((B+'/login'));await m.waitForSelector('#login:not(.hidden)');await m.screenshot({path:SH+`m-mob-login-${scheme}.png`});
 await m.fill('#loginUser','budi');await m.fill('#loginPass','budipass1');await m.click('#loginSubmit');await m.waitForSelector('#app:not(.hidden)');await m.waitForTimeout(800);
 await m.click('#userBtn');await m.waitForSelector('.menu');await m.screenshot({path:SH+`m-mob-menu-${scheme}.png`});
 await m.click('.menu >> text=Ganti Kata Sandi');await m.waitForSelector('#pwModal:not(.hidden)');await m.screenshot({path:SH+`m-mob-pw-${scheme}.png`});
 await c3.close();}
console.log('FAILS',JSON.stringify(fails));console.log('ERR',JSON.stringify(errs));await b.close();await srv.cleanup();})().catch(async(e)=>{console.log('FAIL exception '+(e&&e.stack||e));process.exit(1)});
