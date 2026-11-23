const { launch, server, SH } = require('./lib');
let B;
(async()=>{const srv=await server('seeded');B=srv.base;const b=await launch();
const fails=[],errs=[];const ck=(c,m)=>{console.log((c?'ok   ':'FAIL ')+m);if(!c)fails.push(m)};
const login=async(p,user='admin',pw='password1')=>{await p.goto(B+'/login');await p.fill('#loginUser',user);await p.fill('#loginPass',pw);await p.click('#loginSubmit');await p.waitForSelector('#app:not(.hidden)');};
const combos=[];for(const [w,h] of [[390,844],[1280,900]]) for(const scheme of ['light','dark']) for(const lang of ['id','en']) combos.push([w,h,scheme,lang]);
for(const [w,h,scheme,lang] of combos){
 const tag=`${w}-${scheme}-${lang}`;
 const c=await b.newContext({viewport:{width:w,height:h},colorScheme:scheme});
 await c.addInitScript(([l,t])=>{try{localStorage.setItem('bara_lang',l);localStorage.setItem('bara_theme',t);localStorage.setItem('bara_account','main')}catch(e){}},[lang,scheme]);
 const p=await c.newPage();p.on('pageerror',e=>errs.push(tag+' '+e.message));p.on('console',m=>{if(m.type()==='error')errs.push(tag+' '+m.text())});
 await login(p);await p.waitForSelector('#onboarding:not(.hidden)');
 ck(/3\/5/.test(await p.textContent('#onbRingText')),tag+' progress ring 3/5: '+await p.textContent('#onbRingText'));
 ck((await p.getAttribute('#onbRing','aria-label')).includes('3'),tag+' ring aria label');
 const steps=await p.locator('#onbList li').count();const doneN=await p.locator('#onbList li.done').count();
 ck(steps===5&&doneN===3,tag+` 5 steps, 3 done (${steps}/${doneN})`);
 ck(await p.locator('#onbList li.done button').count()===0&&await p.locator('#onbList li:not(.done) button').count()===2,tag+' buttons only on open steps');
 ck(await p.evaluate(()=>document.documentElement.scrollWidth<=document.documentElement.clientWidth),tag+' no horizontal overflow');
 await p.screenshot({path:SH+`onboarding-${tag}.png`});
 await c.close();}
// tombol menuju tab yang tepat + uji sekarang + tutup (tersimpan per pengguna dan akun)
{const c=await b.newContext({viewport:{width:1280,height:900}});await c.addInitScript(()=>{try{localStorage.setItem('bara_lang','id');localStorage.setItem('bara_account','main')}catch(e){}});
 const p=await c.newPage();const posts=[];await p.route('**/api/run',(r)=>{if(r.request().method()==='POST'){posts.push(r.request().postDataJSON());return r.fulfill({status:200,contentType:'application/json',body:'{"job":{}}'})}return r.continue()});
 await login(p);await p.waitForSelector('#onboarding:not(.hidden)');
 const open=p.locator('#onbList li:not(.done)');
 // langkah terbuka: Atur Notifikasi (settings), Coba Uji (run test)
 await open.nth(0).locator('button').click();await p.waitForTimeout(300);
 ck(await p.isVisible('#tab-settings')&&await p.evaluate(()=>document.activeElement.id==='myDcEnabled'),'notify step goes to personal notification settings');
 await p.click('#tabs [data-tab=dashboard]');await p.waitForSelector('#onboarding:not(.hidden)');
 await p.locator('#onbList li:not(.done)').nth(1).locator('button').click();await p.waitForTimeout(300);
 ck(posts.length===1&&posts[0].mode==='test'&&posts[0].account==='main','dry-run step posts a test run: '+JSON.stringify(posts[0]));
 await p.click('#onbDismiss');await p.waitForTimeout(500);
 ck(await p.locator('#onboarding').isHidden(),'dismiss hides the card');
 await p.reload();await p.waitForSelector('#app:not(.hidden)');await p.waitForTimeout(800);
 ck(await p.locator('#onboarding').isHidden(),'dismissal persists after reload');
 // akun lain tidak terpengaruh
 const other=await p.evaluate(async()=>(await (await fetch('/api/dashboard?account=second')).json()).onboarding.visible);
 ck(other===true,'other account of the same user still shows its checklist');
 await c.close();}
// pengguna lain (budi) tidak terpengaruh oleh penutupan admin
{const c=await b.newContext({viewport:{width:1280,height:900}});const p=await c.newPage();p.on('pageerror',e=>errs.push('budi '+e.message));
 await login(p,'budi','budipass1');await p.waitForSelector('#onboarding:not(.hidden)');ck(/\d\/5/.test(await p.textContent('#onbRingText')),'another user has their own checklist');await c.close();}
console.log(errs.length?'ERRS '+errs.slice(0,5).join(' | '):'ERRS none');console.log(fails.length?'FAILS '+fails.length:'ALL OK');await b.close();await srv.cleanup();})().catch((e)=>{console.log('FAIL exception '+(e&&e.stack||e));process.exit(1)});
