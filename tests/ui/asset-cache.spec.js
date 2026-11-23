const { launch, server, fixtureServer, SH, ROOT } = require('./lib');
let B;
const fs=require('fs');
const APP=require('path').join(ROOT,'app','static','app.js');
(async()=>{const srv=await server('legacy',{});B=srv.base;const b=await launch();
const fails=[];const ck=(c,m)=>{console.log((c?'ok   ':'FAIL ')+m);if(!c)fails.push(m)};
const orig=fs.readFileSync(APP,'utf8');
try{
 // 1. stale cache -> new version in the same context
 fs.writeFileSync(APP,orig+'\nwindow.__MARK="one";');await srv.restart({},{fresh:true});
 const c=await b.newContext();const p=await c.newPage();const urls=[];p.on('request',r=>{if(/\/static\//.test(r.url()))urls.push(r.url())});
 await p.goto((B+'/login'));await p.waitForSelector('#login:not(.hidden)');
 ck(urls.some(u=>/app\.js\?v=[0-9a-f]{10}$/.test(u))&&urls.some(u=>/style\.css\?v=/.test(u)),'assets use ?v= '+urls.join(' '));
 ck(await p.evaluate(()=>window.__MARK)==='one','v1 running');
 fs.writeFileSync(APP,orig+'\nwindow.__MARK="two";');await srv.restart({},{fresh:true});
 urls.length=0;await p.goto((B+'/login'));await p.waitForSelector('#login:not(.hidden)');
 ck(await p.evaluate(()=>window.__MARK)==='two','new version served in same context after deploy');
 ck(urls.some(u=>/app\.js\?v=/.test(u)),'new ?v= url fetched '+urls.join(' '));
 await c.close();
 fs.writeFileSync(APP,orig);await srv.restart({},{fresh:true});
 // 2. app.js 404
 let c2=await b.newContext();let p2=await c2.newPage();await p2.route('**/static/app.js*',r=>r.fulfill({status:404,body:'nf'}));
 await p2.goto((B+'/login'));await p2.waitForSelector('#bootFail:not([hidden])',{timeout:5000}).then(()=>ck(true,'fallback on app.js 404'),()=>ck(false,'fallback on app.js 404'));
 ck((await p2.textContent('#bootFailMsg')).includes('Gagal Memuat Panel'),'fallback text');await p2.screenshot({path:SH+'bootfail.png'});await c2.close();
 // 3. app.js throws
 c2=await b.newContext();p2=await c2.newPage();await p2.route('**/static/app.js*',r=>r.fulfill({status:200,contentType:'application/javascript',body:'throw new Error("boom")'}));
 await p2.goto((B+'/login'));await p2.waitForSelector('#bootFail:not([hidden])',{timeout:6000}).then(()=>ck(true,'fallback on throw'),()=>ck(false,'fallback on throw'));await c2.close();
 // 4. 502 twice then 200
 c2=await b.newContext();p2=await c2.newPage();let n=0;await p2.route('**/api/auth/state',r=>{n++;if(n<=2)r.fulfill({status:502,body:'bad gateway'});else r.continue()});
 await p2.goto((B+'/login'));await p2.waitForSelector('#login:not(.hidden)',{timeout:8000}).then(()=>ck(n===3&&true,'boots after two 502s (calls '+n+')'),()=>ck(false,'boot after 502s'));
 ck(await p2.locator('#bootFail').isHidden(),'no fallback when booted');await c2.close();
 // 5. permanent 502 -> fallback
 c2=await b.newContext();p2=await c2.newPage();await p2.route('**/api/auth/state',r=>r.fulfill({status:502,body:'x'}));
 await p2.goto((B+'/login'));await p2.waitForSelector('#bootFail:not([hidden])',{timeout:12000}).then(()=>ck(true,'fallback on permanent 502'),()=>ck(false,'fallback on permanent 502'));await c2.close();
}finally{fs.writeFileSync(APP,orig);}
console.log(fails.length?'FAILS '+fails.length:'ALL OK');await b.close();await srv.cleanup();})().catch(async(e)=>{console.log('FAIL exception '+(e&&e.stack||e));process.exit(1)});
