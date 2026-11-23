const { launch, server, fixtureServer, SH, ROOT } = require('./lib');
let B;
(async()=>{const srv=await server('setup',{});B=srv.base;srv.py('seed_history.py');const b=await launch();
const errs=[],fails=[];const ck=(c,m)=>{console.log((c?'ok   ':'FAIL ')+m);if(!c)fails.push(m)};
for(const [w,h] of [[1280,900],[390,844]]) for(const scheme of ['light','dark']) for(const lang of ['id','en']){
 const tag=`${w}-${scheme}-${lang}`;
 const c=await b.newContext({viewport:{width:w,height:h},colorScheme:scheme});
 await c.addInitScript(([l,th])=>{try{localStorage.setItem('bara_lang',l);localStorage.setItem('bara_theme',th)}catch(e){}},[lang,scheme]);
 const p=await c.newPage();
 p.on('pageerror',e=>errs.push(tag+' pageerror '+e.message));p.on('console',m=>{if(['error','warning'].includes(m.type()))errs.push(tag+' console '+m.text())});
 await p.goto((B+'/login'));await p.waitForSelector('#login:not(.hidden)');
 await p.fill('#loginUser','admin');await p.fill('#loginPass','password1');await p.click('#loginSubmit');
 await p.waitForSelector('#app:not(.hidden)');await p.waitForSelector('#historyBody tr');await p.waitForTimeout(500);
 const info=await p.textContent('#pagerInfo');
 const exp=lang==='id'?'Menampilkan 1–20 dari 134':'Showing 1–20 of 134';
 ck(info===exp,tag+' info "'+info+'"');
 ck(await p.locator('#historyBody tr').count()===20,tag+' 20 rows');
 ck(await p.isDisabled('#pgPrev')&&!await p.isDisabled('#pgNext'),tag+' prev disabled at p1');
 let nums=(await p.locator('#pgNums').innerText()).replace(/\s+/g,' ').trim();
 ck(nums==='1 2 … 7',tag+' nums p1 "'+nums+'"');
 // go to page 5 -> 1 … 4 5 6 … 7? pages=7 -> 1 … 4 5 6 7? check ellipsis at size 10
 await p.selectOption('#pgSize','10');await p.waitForTimeout(500);
 ck((await p.textContent('#pagerInfo')).includes('1–10')&&await p.locator('#historyBody tr').count()===10,tag+' size 10');
 for(let i=0;i<4;i++){await p.click('#pgNext');await p.waitForTimeout(350);}
 // 14 pages
 nums=(await p.locator('#pgNums').innerText()).replace(/\s+/g,' ').trim();
 ck(nums==='1 … 4 5 6 … 14',tag+' ellipsis "'+nums+'"');
 ck((await p.textContent('#pagerInfo')).includes('41–50'),tag+' range 41–50: '+await p.textContent('#pagerInfo'));
 // persistence
 await p.reload();await p.waitForSelector('#historyBody tr');await p.waitForTimeout(600);
 ck((await p.textContent('#pagerInfo')).includes('41–50')&&await p.inputValue('#pgSize')==='10',tag+' persisted page+size');
 // filter chips: Kirim
 await p.click('#fMode button:nth-child(3)');await p.waitForTimeout(500);
 const t2=await p.textContent('#pagerInfo');ck(/ (\d+)$/.test(t2)&&+t2.match(/(\d+)$/)[1]<134&&t2.includes('1–10'),tag+' check filter resets to p1: '+t2);
 const rowsTxt=await p.locator('#historyBody tr .h-type').allTextContents();
 ck(rowsTxt.length>0&&rowsTxt.every(x=>/^(Cek Cookie|Cookie Check)/.test(x)),tag+' only check rows');
 await p.selectOption('#fStatus','failed');await p.waitForTimeout(500);
 const badges=await p.locator('#historyBody .badge').allTextContents();ck(badges.every(x=>/Gagal|Failed/.test(x)),tag+' status failed '+badges.length);
 // reset filters
 await p.click('#fMode button:nth-child(1)');await p.selectOption('#fStatus','');await p.waitForTimeout(500);
 if(w===390){
  const card=await p.evaluate(()=>{const tr=document.querySelector('#historyBody tr');const cs=getComputedStyle(tr);return {disp:cs.display,thead:getComputedStyle(document.querySelector('.hist-table thead')).display,sw:document.documentElement.scrollWidth,cw:document.documentElement.clientWidth}});
  ck(card.disp==='grid'&&card.thead==='none'&&card.sw<=card.cw,tag+' mobile cards '+JSON.stringify(card));
 } else {
  ck(await p.evaluate(()=>getComputedStyle(document.querySelector('.hist-table thead')).display!=='none'),tag+' table at desktop');
 }
 await p.locator('#pager').scrollIntoViewIfNeeded();
 await p.locator('#historyGroup, .group:has(#pager)').first().screenshot({path:SH+`hist-${tag}.png`});
 // last page
 await p.selectOption('#pgSize','50');await p.waitForTimeout(500);
 await p.click('#pgNext');await p.waitForTimeout(400);await p.click('#pgNext');await p.waitForTimeout(400);
 ck((await p.textContent('#pagerInfo')).includes('101–134')&&await p.isDisabled('#pgNext'),tag+' last page '+await p.textContent('#pagerInfo'));
 // dashboard stats independent of page
 ck(await p.evaluate(()=>document.getElementById('streakNum').textContent!==''),tag+' streak present');
 await c.close();
}
console.log('ERRS',errs.length?errs.slice(0,10):'none');console.log(fails.length?'FAILS '+fails.length:'ALL OK');await b.close();await srv.cleanup();})().catch(async(e)=>{console.log('FAIL exception '+(e&&e.stack||e));process.exit(1)});
