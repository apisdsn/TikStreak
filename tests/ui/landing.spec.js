const { launch, server, fixtureServer, SH, ROOT } = require('./lib');
let B;

const F=async(u,o)=>{for(let i=0;i<3;i++){try{return await fetch(u,o)}catch(e){await new Promise(r=>setTimeout(r,500))}}return fetch(u,o)};
(async()=>{const srv=await server('legacy',{});B=srv.base;const b=await launch();
const fails=[],errs=[];const ck=(c,m)=>{console.log((c?'ok   ':'FAIL ')+m);if(!c)fails.push(m)};
const hook=(p,tag)=>{p.on('pageerror',e=>errs.push(tag+' '+e.message));p.on('console',m=>{if(['error','warning'].includes(m.type())&&!/status of (401|403|429|400)/.test(m.text()))errs.push(tag+' '+m.text())})};
const fetchNoRedirect=async(path,cookie)=>{const r=await F(B+path,{redirect:'manual',headers:cookie?{cookie}:{}});return r};
await srv.restart({},{fresh:true});
// ---- setup required
let r=await fetchNoRedirect('/');ck(r.status===302&&r.headers.get('location')==='/login','setup required: / -> 302 /login');
ck(r.headers.get('cache-control')==='private, no-cache'&&/cookie/i.test(r.headers.get('vary')||''),'redirect headers');
r=await fetchNoRedirect('/login');ck(r.status===200&&(await r.text()).includes('id="loginForm"'),'/login serves app');
ck(r.headers.get('cache-control')==='private, no-cache'&&r.headers.get('vary')==='Cookie','/login headers');
let c=await b.newContext();let p=await c.newPage();hook(p,'setup');
await p.goto(B+'/');await p.waitForSelector('#login:not(.hidden)');ck(new URL(p.url()).pathname==='/login'&&await p.isVisible('#fieldSetupKey'),'setup form at /login');
await p.fill('#setupKey','testkey123');await p.fill('#loginUser','admin');await p.fill('#loginPass','password1');await p.fill('#loginPass2','password1');await p.click('#loginSubmit');
await p.waitForSelector('#app:not(.hidden)');ck(new URL(p.url()).pathname==='/','after setup lands at /');
const cookies=await c.cookies();const ck0=cookies.find(x=>x.name==='bara_session');
// ---- logged in
r=await fetchNoRedirect('/login','bara_session='+ck0.value);ck(r.status===302&&r.headers.get('location')==='/','logged-in /login -> 302 /');
r=await fetchNoRedirect('/','bara_session='+ck0.value);let t=await r.text();ck(r.status===200&&t.includes('id="app"')&&!t.includes('landing.js'),'logged-in / serves app');
ck(r.headers.get('cache-control')==='private, no-cache'&&r.headers.get('vary')==='Cookie','app / headers');
await p.goto(B+'/');await p.waitForSelector('#app:not(.hidden)');ck(true,'logged-in / goes straight to app');
await p.goto(B+'/login');await p.waitForSelector('#app:not(.hidden)');ck(new URL(p.url()).pathname==='/','logged-in /login ends at /');
// logout
await p.click('#userBtn');await p.click('.menu >> text=/Keluar|Log Out/');await p.waitForSelector('h1.hl');ck(new URL(p.url()).pathname==='/','logout ends on landing at /');
await c.close();
// ---- logged out
r=await fetchNoRedirect('/');t=await r.text();ck(r.status===200&&t.includes('landing.js')&&/landing\.css\?v=[0-9a-f]{10}/.test(t)&&/landing\.js\?v=[0-9a-f]{10}/.test(t),'logged-out / is landing with ?v=');
ck(r.headers.get('cache-control')==='private, no-cache'&&r.headers.get('vary')==='Cookie','landing / headers');
r=await F(B+'/static/landing.js?v=x');ck(/immutable/.test(r.headers.get('cache-control')),'landing asset immutable with ?v');
r=await fetchNoRedirect('/','bara_session=bogus');ck((await r.text()).includes('landing.js'),'bogus cookie -> landing');
// legacy cookie
const lg=await F(B+'/api/auth/login',{method:'POST',headers:{'Content-Type':'application/json','X-Requested-With':'bara'},body:JSON.stringify({username:'admin',password:'password1'})});
const tok=(lg.headers.getSetCookie().find(x=>x.startsWith('bara_session='))||'').split(';')[0].split('=')[1];
r=await fetchNoRedirect('/','sp_session='+tok);
const sc=r.headers.getSetCookie?r.headers.getSetCookie():[];
ck(r.status===200&&(await r.text()).includes('id="app"'),'legacy sp_session / serves app');
ck(sc.some(x=>x.startsWith('bara_session='))&&sc.some(x=>/^sp_session=;|sp_session=""/.test(x)||x.startsWith('sp_session=')),'legacy cookie upgraded '+JSON.stringify(sc.map(x=>x.slice(0,30))));
// ---- landing UI
c=await b.newContext({viewport:{width:1440,height:900},locale:'en-US'});p=await c.newPage();hook(p,'land');
await p.goto(B+'/');await p.waitForSelector('h1.hl');
ck((await p.textContent('h1.hl')).includes('Keep the Streak Alive'),'navigator en -> EN default: '+await p.textContent('h1.hl'));
ck(await p.evaluate(()=>document.documentElement.lang)==='en'&&(await p.title())==='Bara · TikTok Streak Keeper','html lang + title EN');
await p.click('#langId');ck((await p.textContent('h1.hl')).includes('Streak Tetap Menyala')&&(await p.title())==='Bara · Penjaga Streak TikTok'&&await p.evaluate(()=>document.documentElement.lang)==='id','switch to ID: h1, title, lang');
ck(await p.getAttribute('#langId','aria-pressed')==='true'&&await p.getAttribute('#langEn','aria-pressed')==='false','aria-pressed');
ck(await p.evaluate(()=>localStorage.getItem('bara_lang'))==='id','bara_lang stored');
ck(await p.evaluate(()=>document.querySelector('meta[name=description]').content.startsWith('Bara mengirim')),'meta description ID');
ck(await p.evaluate(()=>!!document.querySelector('a.skip')&&!!document.querySelector('main#main')),'skip link + main');
ck(await p.locator('#docsBtn').isHidden(),'docs button hidden by default');
ck(await p.getAttribute('.stack','role')==='img'&&!!(await p.getAttribute('.stack','aria-label')),'preview role=img + label');
// FAQ
const d=p.locator('#faqList details');ck(await d.count()===5&&await d.nth(0).evaluate(e=>e.open)&&!await d.nth(1).evaluate(e=>e.open),'FAQ first open');
await d.nth(1).locator('summary').click();ck(await d.nth(1).evaluate(e=>e.open),'FAQ toggles open');
await d.nth(1).locator('summary').click();ck(!await d.nth(1).evaluate(e=>e.open),'FAQ toggles closed');
await d.nth(2).locator('summary').click();await p.click('#langEn');ck(await p.locator('#faqList details').nth(2).evaluate(e=>e.open),'FAQ state kept across language switch');await p.click('#langId');
// anchors
for(const [href,id] of [['#features','features'],['#how-it-works','how-it-works'],['#security','security'],['#faq','faq']]){
 await p.evaluate(()=>window.scrollTo(0,0));await p.click(`.links a[href="${href}"]`);await p.waitForTimeout(1200);
 const top=await p.evaluate((i)=>Math.abs(document.getElementById(i).getBoundingClientRect().top),id);ck(top<30,`anchor ${href} scrolls (top=${Math.round(top)})`);}
// anchors are language neutral
await p.click('#langEn');ck(await p.evaluate(()=>['features','how-it-works','security','faq'].every(i=>!!document.getElementById(i))&&!document.getElementById('fitur')),'english ids present in EN, old ids gone');
ck(await p.evaluate(()=>[...document.querySelectorAll('a[href^="#"]')].every(a=>a.getAttribute('href')==='#'||!!document.getElementById(a.getAttribute('href').slice(1)))),'all in-page links resolve');
await p.click('#langId');
// old hashes mapped
for(const [old,nw] of [['fitur','features'],['cara','how-it-works'],['aman','security']]){
 const q=await c.newPage();await q.goto(B+'/#'+old);await q.waitForSelector('h1.hl');await q.waitForTimeout(500);
 ck(new URL(q.url()).hash==='#'+nw,`load #${old} -> URL #${nw}`);
 ck(await q.evaluate((i)=>{const r=document.getElementById(i).getBoundingClientRect();return r.top<200&&r.bottom>0},nw),`load #${old} scrolled to section`);
 await q.evaluate(()=>window.scrollTo(0,0));await q.evaluate((o)=>{location.hash=o},old);await q.waitForTimeout(1200);
 ck(new URL(q.url()).hash==='#'+nw&&await q.evaluate((i)=>Math.abs(document.getElementById(i).getBoundingClientRect().top)<40,nw),`hashchange #${old} -> #${nw} and scrolled`);
 await q.close();}
// reduced motion
const c3=await b.newContext({reducedMotion:'reduce',viewport:{width:1440,height:900}});const p3=await c3.newPage();await p3.goto(B+'/');await p3.waitForSelector('h1.hl');await p3.click('.links a[href="#faq"]');await p3.waitForTimeout(100);
ck(await p3.evaluate(()=>Math.abs(document.getElementById('faq').getBoundingClientRect().top)<30),'reduced motion: instant scroll');await c3.close();
// theme persists to login and app
await p.evaluate(()=>window.scrollTo(0,0));
await p.click('#themeBtn');const th=await p.evaluate(()=>document.documentElement.dataset.theme);
ck(await p.evaluate(()=>localStorage.getItem('bara_theme'))===th,'theme stored '+th);
await p.click('.nav >> text=/Masuk|Log In/');await p.waitForSelector('#login:not(.hidden)');
ck(new URL(p.url()).pathname==='/login','Masuk -> /login');
ck(await p.evaluate(()=>document.documentElement.dataset.theme)===th&&await p.evaluate(()=>document.documentElement.lang)==='id','theme+lang carry into login');
await p.fill('#loginUser','admin');await p.fill('#loginPass','password1');await p.click('#loginSubmit');await p.waitForSelector('#app:not(.hidden)');
ck(new URL(p.url()).pathname==='/'&&await p.evaluate(()=>document.documentElement.dataset.theme)===th,'login lands at / with same theme');
await c.close();
// footer + CTA links
c=await b.newContext();p=await c.newPage();await p.goto(B+'/');await p.waitForSelector('h1.hl');
ck(await p.evaluate(()=>[...document.querySelectorAll('a[data-login]')].every(a=>a.getAttribute('href')==='/login')&&document.querySelectorAll('a[data-login]').length===4),'4 login links');
await c.close();
// ---- docs url + landing disabled
await srv.restart({LANDING_DOCS_URL:'https://example.org/guide?a=1&b=2'},{fresh:true});
await F(B+'/api/auth/setup',{method:'POST',headers:{'Content-Type':'application/json','X-Requested-With':'bara'},body:JSON.stringify({api_key:'testkey123',username:'admin',password:'password1'})});
c=await b.newContext({viewport:{width:1440,height:900}});p=await c.newPage();await p.goto(B+'/');await p.waitForSelector('h1.hl');
ck(await p.isVisible('#docsBtn')&&await p.getAttribute('#docsBtn','href')==='https://example.org/guide?a=1&b=2','docs button shown with env url');await c.close();
await srv.restart({LANDING_ENABLED:'0'},{fresh:true});
await F(B+'/api/auth/setup',{method:'POST',headers:{'Content-Type':'application/json','X-Requested-With':'bara'},body:JSON.stringify({api_key:'testkey123',username:'admin',password:'password1'})});
r=await fetchNoRedirect('/');t=await r.text();ck(r.status===200&&t.includes('id="loginForm"')&&!t.includes('landing.js'),'LANDING_ENABLED=0: / serves app/login');
c=await b.newContext();p=await c.newPage();await p.goto(B+'/');await p.waitForSelector('#login:not(.hidden)');ck(new URL(p.url()).pathname==='/','old behaviour: login view at /');
r=await fetchNoRedirect('/login');ck(r.status===200,'/login still works when disabled');
await p.fill('#loginUser','admin');await p.fill('#loginPass','password1');await p.click('#loginSubmit');await p.waitForSelector('#app:not(.hidden)');
await p.click('#userBtn');await p.click('.menu >> text=/Keluar|Log Out/');await p.waitForSelector('#login:not(.hidden)');ck(new URL(p.url()).pathname==='/','disabled: logout shows login at /');await c.close();

console.log(errs.length?'ERRS '+errs.slice(0,5):'ERRS none');console.log(fails.length?'FAILS '+fails.length:'ALL OK');await b.close();await srv.cleanup();})().catch(async(e)=>{console.log('FAIL exception '+(e&&e.stack||e));process.exit(1)});
