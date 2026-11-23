const { launch, server, fixtureServer, SH, ROOT } = require('./lib');
let B;
(async()=>{const srv=await server('seeded',{});B=srv.base;const b=await launch();
const errs=[],bad=[];
for(const scheme of ['light','dark'])for(const [w,h] of [[1440,900],[1280,900],[1024,800],[820,800],[390,844]]){
 const ctx=await b.newContext({viewport:{width:w,height:h},colorScheme:scheme});const p=await ctx.newPage();
 p.on('pageerror',e=>errs.push(`${scheme}${w} pageerror `+e.message));p.on('console',m=>{if(['error','warning'].includes(m.type()))errs.push(`${scheme}${w} console `+m.text())});p.on('dialog',d=>d.accept());
 await p.goto((B+'/login'));await p.waitForSelector('#login:not(.hidden)');
 if(w===1280&&scheme==='light')await p.screenshot({path:SH+'z-login.png'});
 await p.fill('#loginUser','admin');await p.fill('#loginPass','password1');await p.click('#loginSubmit');await p.waitForSelector('#app:not(.hidden)');await p.waitForTimeout(1000);
 for(const lang of ['id','en']){await p.click(`[data-lang=${lang}]`);
  for(const tab of ['dashboard','accounts','contacts','cookies','settings']){
   await p.click(`#tabs [data-tab=${tab}]`);await p.waitForTimeout(150);
   const r=await p.evaluate(()=>{const t=document.getElementById('tabs');const tr=t.getBoundingClientRect();const bs=[...t.querySelectorAll('button')].map(x=>x.getBoundingClientRect());
     const tb=document.querySelector('.topbar').getBoundingClientRect();
     return {clip:t.scrollWidth>t.clientWidth+1,h:Math.round(tb.height),inview:bs.every(r=>r.right<=innerWidth+1&&r.left>=-1),ov:document.documentElement.scrollWidth>innerWidth,
       errs:[...document.querySelectorAll('.error')].filter(e=>e.textContent===''&&getComputedStyle(e).display!=='none').length}});
   if(w>720&&(r.clip||r.h>72||!r.inview))bad.push([scheme,w,lang,tab,'topbar',r]);
   if(r.ov||r.errs)bad.push([scheme,w,lang,tab,'overflow/empty-error',r]);
   if(lang==='id'&&scheme==='light'||lang==='en'&&scheme==='dark'){await p.screenshot({path:`${SH}z-${scheme}-${w}-${lang}-${tab}.png`,fullPage:w===390||w===1280});}
  }}
 await ctx.close();}
console.log('BAD',JSON.stringify(bad,null,1));console.log('ERR',JSON.stringify(errs));await b.close();await srv.cleanup();})().catch(async(e)=>{console.log('FAIL exception '+(e&&e.stack||e));process.exit(1)});
