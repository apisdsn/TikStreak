const { launch, server, fixtureServer, SH, ROOT } = require('./lib');
let B;
(async()=>{const srv=await server('seeded',{});B=srv.base;const b=await launch();
const errs=[],fails=[];const ck=(c,m)=>{console.log((c?'ok   ':'FAIL ')+m);if(!c)fails.push(m)};
for(const [w,h,tag] of [[1280,900,'d'],[390,844,'m']]){
 const ctx=await b.newContext({viewport:{width:w,height:h}});const p=await ctx.newPage();
 p.on('pageerror',e=>errs.push(e.message));p.on('console',m=>{if(['error','warning'].includes(m.type())&&!/status of 40/.test(m.text()))errs.push(m.text())});p.on('dialog',d=>d.accept());
 await p.goto((B+'/login'));await p.fill('#loginUser','budi');await p.fill('#loginPass','budipass1');await p.click('#loginSubmit');await p.waitForSelector('#app:not(.hidden)');await p.waitForTimeout(800);
 await p.click('#tabs [data-tab=cookies]');await p.waitForTimeout(400);
 if(await p.evaluate(()=>document.getElementById('cookieBanner').classList.contains('ok'))){await p.evaluate(()=>{const d=document.getElementById('manualCookie');d.open=true});await p.click('#btnClearCookies');await p.evaluate(()=>{document.getElementById('manualCookie').open=false});await p.waitForTimeout(2500);}
 ck(await p.evaluate(()=>document.getElementById('manualCookie').open),tag+' details auto-open when cookie missing');
 ck(await p.isDisabled('#btnSaveCookies'),tag+' save disabled initially');
 const hrefs=await p.evaluate(()=>[...document.querySelectorAll('.gstep a')].map(a=>[a.href,a.target,a.rel]));
 ck(JSON.stringify(hrefs).includes('tiktok.com')&&JSON.stringify(hrefs).includes('cookie-editor.com')&&hrefs.every(x=>x[1]==='_blank'&&/noopener/.test(x[2])),tag+' guide links');
 const check=async(txt)=>{await p.fill('#cookieInput',txt);await p.waitForTimeout(100);return [await p.textContent('#cookieCheck'),await p.getAttribute('#cookieCheck','class'),await p.isDisabled('#btnSaveCookies')]};
 const withS=JSON.stringify([{name:'sessionid',value:'SECRETVALUE1',domain:'.tiktok.com'},{name:'tt_csrf',value:'x'}]);
 let r=await check(withS);ck(r[0]==='2 Cookie Terbaca · sessionid Ditemukan'&&/ok/.test(r[1])&&!r[2],tag+' JSON+sessionid: '+r[0]);ck(!(await p.textContent('#cookieCheck')).includes('SECRETVALUE'),tag+' value never shown');
 r=await check(JSON.stringify([{name:'tt_csrf',value:'x'}]));ck(/sessionid Tidak Ada/.test(r[0])&&/warn/.test(r[1])&&!r[2],tag+' no sessionid warn: '+r[0]);
 r=await check('sessionid=abc; foo=bar; baz=1');ck(/^3 Cookie/.test(r[0])&&/ok/.test(r[1]),tag+' header: '+r[0]);
 r=await check('{"cookies":[{"name":"sessionid","value":"v"}]}');ck(/^1 Cookie/.test(r[0])&&/ok/.test(r[1]),tag+' {cookies:[]}: '+r[0]);
 r=await check('{"name":"sessionid","value":"v"}');ck(/^1 Cookie/.test(r[0]),tag+' single object: '+r[0]);
 r=await check('this is garbage');ck(r[0].startsWith('Format Tidak Dikenali')&&/bad/.test(r[1])&&r[2],tag+' garbage: '+r[0]);
 r=await check('[{"x":1}]');ck(r[0].startsWith('Format Tidak Dikenali')&&r[2],tag+' json without names bad');
 r=await check('[ broken json');ck(r[2],tag+' broken json disabled');
 r=await check('');ck(r[0]===''&&r[2],tag+' empty idle');
 await p.fill('#cookieInput',withS);await p.waitForTimeout(100);
 await p.locator('#manualCookie').scrollIntoViewIfNeeded();await p.screenshot({path:SH+`g-${tag}-guide.png`,fullPage:true});
 await p.click('#btnSaveCookies');await p.waitForTimeout(800);
 ck(await p.evaluate(()=>document.getElementById('cookieBanner').classList.contains('ok')),tag+' saved -> banner ok');
 ck((await p.textContent('#cookieCheck'))===''&&await p.isDisabled('#btnSaveCookies'),tag+' check cleared after save');
 // EN
 await p.click('[data-lang=en]');await p.fill('#cookieInput','[{"name":"a","value":"b"}]');await p.waitForTimeout(100);
 ck((await p.textContent('#cookieCheck')).includes('sessionid Is Missing'),tag+' EN warn: '+await p.textContent('#cookieCheck'));
 await p.screenshot({path:SH+`g-${tag}-guide-en.png`,fullPage:true});
 await ctx.close();}
// login page logo
const c=await b.newContext({viewport:{width:390,height:700}});const q=await c.newPage();await q.goto((B+'/login'));await q.waitForSelector('#login:not(.hidden)');await q.screenshot({path:SH+'g-login-m.png'});
console.log('FAILS',JSON.stringify(fails));console.log('ERR',JSON.stringify(errs));await b.close();await srv.cleanup();})().catch(async(e)=>{console.log('FAIL exception '+(e&&e.stack||e));process.exit(1)});
