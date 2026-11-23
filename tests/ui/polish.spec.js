const { launch, server, fixtureServer, SH, ROOT } = require('./lib');
let B;
(async()=>{const srv=await server('setup',{});B=srv.base;srv.py('seed_meta.py');const b=await launch();
const fails=[],errs=[];const ck=(c,m)=>{console.log((c?'ok   ':'FAIL ')+m);if(!c)fails.push(m)};for(const [w,h] of [[1100,800],[390,844],[1280,900]]){
 const c=await b.newContext({viewport:{width:w,height:h}});await c.addInitScript(()=>{try{localStorage.setItem('bara_account','main')}catch(e){}});
 const p=await c.newPage();p.on('pageerror',e=>errs.push(e.message));p.on('console',m=>{if(m.type()==='error')errs.push(m.text())});p.on('dialog',d=>d.accept());
 await p.goto((B+'/login'));await p.waitForSelector('#login:not(.hidden)');await p.fill('#loginUser','admin');await p.fill('#loginPass','password1');await p.click('#loginSubmit');
 await p.waitForSelector('#app:not(.hidden)');await p.waitForTimeout(800);
 const m=await p.evaluate(()=>{const t=document.querySelector('.topbar-in');const s=document.querySelector('.brand strong');return {brand:s&&getComputedStyle(s).display!=='none'&&s.offsetWidth>0,over:t.scrollWidth>t.clientWidth+1,sw:document.documentElement.scrollWidth<=document.documentElement.clientWidth,txt:document.getElementById('cookieSub').textContent,title:[...document.querySelectorAll('.w-head h2')].map(h=>[h.textContent,h.scrollHeight>h.clientHeight+1])}});
 console.log(w,JSON.stringify(m));
 if(w>=1100)ck(m.brand,w+' brand visible');else ck(!m.brand,'brand hidden on mobile (unchanged)');
 ck(!m.over&&m.sw,w+' no topbar/page overflow');
 ck(m.txt==='Cookie TikTok Belum Diatur',w+' cookieSub "'+m.txt+'"');
 ck(m.title.every(x=>!x[1]),w+' tile titles not clipped');
 await p.screenshot({path:SH+`polish-${w}.png`});
 if(w!==1100){await p.click('#tabs [data-tab=settings]');await p.waitForTimeout(500);
  ck(await p.isVisible('#btnDelBackups'),w+' delete-backups button visible');await p.locator('#btnDelBackups').scrollIntoViewIfNeeded();await p.screenshot({path:SH+`polish-set-${w}.png`});
  if(w===1280){await p.click('#btnDelBackups');await p.waitForTimeout(800);ck(await p.locator('#btnDelBackups').count()===0,'button gone after delete');}
 }
 await c.close();}
console.log('ERRS',errs.length?errs.slice(0,5):'none');console.log(fails.length?'FAILS '+fails.length:'ALL OK');await b.close();await srv.cleanup();})().catch(async(e)=>{console.log('FAIL exception '+(e&&e.stack||e));process.exit(1)});
