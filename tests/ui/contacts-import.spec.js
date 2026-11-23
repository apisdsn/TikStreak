const { launch, server, SH } = require('./lib');
let B;
(async()=>{const srv=await server('seeded');B=srv.base;srv.py('seed_scan.py');const b=await launch();
const fails=[],errs=[];const ck=(c,m)=>{console.log((c?'ok   ':'FAIL ')+m);if(!c)fails.push(m)};
const combos=[];for(const [w,h] of [[390,844],[1280,900]]) for(const scheme of ['light','dark']) for(const lang of ['id','en']) combos.push([w,h,scheme,lang]);
for(const [w,h,scheme,lang] of combos){
 const tag=`${w}-${scheme}-${lang}`;
 const c=await b.newContext({viewport:{width:w,height:h},colorScheme:scheme});
 await c.addInitScript(([l,t])=>{try{localStorage.setItem('bara_lang',l);localStorage.setItem('bara_theme',t);localStorage.setItem('bara_account','main')}catch(e){}},[lang,scheme]);
 const p=await c.newPage();p.on('pageerror',e=>errs.push(tag+' '+e.message));p.on('console',m=>{if(m.type()==='error'&&!/status of (400|409)/.test(m.text()))errs.push(tag+' '+m.text())});
 // pindai sebenarnya butuh browser TikTok; POST dipalsukan, hasil disiapkan lewat db dan dibaca server sungguhan
 await p.route('**/api/contacts/scan?*',(r)=>r.request().method()==='POST'?r.fulfill({status:200,contentType:'application/json',body:'{"state":"queued"}'}):r.continue());
 await p.goto(B+'/login');await p.fill('#loginUser','admin');await p.fill('#loginPass','password1');await p.click('#loginSubmit');
 await p.waitForSelector('#app:not(.hidden)');await p.click('#tabs [data-tab=contacts]');await p.waitForTimeout(300);
 await p.click('#btnImport');await p.waitForSelector('#importSheet:not(.hidden)');await p.waitForTimeout(300);
 ck(await p.locator('#importList li').count()===10,tag+' 10 chats listed');
 const rina=p.locator('#importList li',{hasText:'Rina'}).first();
 ck(await rina.locator('input').isDisabled()&&/Sudah Ada|Already Added/.test(await rina.textContent()),tag+' existing contact disabled + badge');
 ck(/\d\d:\d\d/.test(await p.locator('#importList li').nth(1).textContent()),tag+' last-message time shown');
 await p.fill('#importSearch','a');await p.waitForTimeout(100);
 const n1=await p.locator('#importList li').count();ck(n1>0&&n1<10,tag+' search filters ('+n1+')');
 await p.fill('#importSearch','');
 await p.check('#importAll');const sel=await p.locator('#importList input:checked:not(:disabled)').count();
 const dis=await p.locator('#importList li.dis').count();ck(dis>=1&&sel===10-dis&&(await p.textContent('#importAdd')).includes(String(sel)),tag+' select all picks only selectable ('+sel+'): '+await p.textContent('#importAdd'));
 await p.uncheck('#importAll');ck(await p.isDisabled('#importAdd'),tag+' add disabled with nothing selected');
 await p.locator('#importList li',{hasText:'Fajar'}).first().click();await p.locator('#importList li',{hasText:'Maya'}).first().click();
 ck((await p.textContent('#importAdd')).includes('2'),tag+' count follows selection');
 await p.screenshot({path:SH+`import-${tag}.png`});
 if(w===1280&&scheme==='dark'&&lang==='en'){
  await p.click('#importAdd');await p.waitForSelector('#importSheet.hidden',{state:'attached'});await p.waitForTimeout(500);
  const names=await p.locator('#contactsList .title').allTextContents();
  ck(names.includes('Fajar')&&names.includes('Maya'),tag+' imported contacts appear: '+names.join(','));
 }
 await c.close();}
console.log(errs.length?'ERRS '+errs.slice(0,5).join(' | '):'ERRS none');console.log(fails.length?'FAILS '+fails.length:'ALL OK');await b.close();await srv.cleanup();})().catch((e)=>{console.log('FAIL exception '+(e&&e.stack||e));process.exit(1)});
