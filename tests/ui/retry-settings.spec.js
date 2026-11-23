const { launch, server, SH } = require('./lib');
let B;
(async()=>{const srv=await server('seeded');B=srv.base;srv.py('seed_retry.py');const b=await launch();
const fails=[],errs=[];const ck=(c,m)=>{console.log((c?'ok   ':'FAIL ')+m);if(!c)fails.push(m)};
const combos=[];for(const [w,h] of [[390,844],[1280,900]]) for(const scheme of ['light','dark']) for(const lang of ['id','en']) combos.push([w,h,scheme,lang]);
for(const [w,h,scheme,lang] of combos){
 const tag=`${w}-${scheme}-${lang}`;
 const c=await b.newContext({viewport:{width:w,height:h},colorScheme:scheme});
 await c.addInitScript(([l,t])=>{try{localStorage.setItem('bara_lang',l);localStorage.setItem('bara_theme',t)}catch(e){}},[lang,scheme]);
 const p=await c.newPage();p.on('pageerror',e=>errs.push(tag+' '+e.message));p.on('console',m=>{if(m.type()==='error'&&!/status of 400/.test(m.text()))errs.push(tag+' '+m.text())});
 await p.goto(B+'/login');await p.fill('#loginUser','admin');await p.fill('#loginPass','password1');await p.click('#loginSubmit');
 await p.waitForSelector('#app:not(.hidden)');
 // riwayat menampilkan percobaan ulang
 await p.waitForFunction(()=>document.querySelectorAll('#historyBody tr .h-type').length>=3);
 const rows=await p.locator('#historyBody tr .h-type').allTextContents();
 ck(rows.some(x=>/\bUlang\b|\bRetry\b/.test(x)),tag+' history row shows retry label: '+rows.join(' | '));
 await p.click('#tabs [data-tab=settings]');await p.waitForTimeout(300);
 const nr=await p.textContent('#nrRetry');ck(/30/.test(nr)&&/2/.test(nr),tag+' retry row summary: '+nr);
 await p.click('.nav-row[data-panel=retry]');await p.waitForSelector('#setSheet:not(.hidden)');
 ck(await p.isVisible('#setRetryDelay')&&await p.inputValue('#setRetryDelay')==='30'&&await p.inputValue('#setRetryMax')==='2'&&await p.isChecked('#setRetryEnabled'),tag+' sheet shows current values');
 await p.screenshot({path:SH+`retry-${tag}.png`});
 if(w===1280&&scheme==='dark'&&lang==='en'){
  await p.fill('#setRetryDelay','45');await p.fill('#setRetryMax','3');await p.click('#settingsForm button[type=submit]');await p.waitForTimeout(600);
  ck(/45/.test(await p.textContent('#nrRetry'))&&/3/.test(await p.textContent('#nrRetry')),tag+' saved summary: '+await p.textContent('#nrRetry'));
  await p.click('.nav-row[data-panel=retry]');await p.fill('#setRetryDelay','0');await p.click('#settingsForm button[type=submit]');await p.waitForTimeout(400);
  ck((await p.textContent('#settingsMsg')).length>0,tag+' invalid delay rejected: '+await p.textContent('#settingsMsg'));
 }
 await c.close();}
console.log(errs.length?'ERRS '+errs.slice(0,5).join(' | '):'ERRS none');console.log(fails.length?'FAILS '+fails.length:'ALL OK');await b.close();await srv.cleanup();})().catch((e)=>{console.log('FAIL exception '+(e&&e.stack||e));process.exit(1)});
