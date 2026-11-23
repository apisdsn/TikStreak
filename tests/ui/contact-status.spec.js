const { launch, server, SH } = require('./lib');
let B;
(async()=>{const srv=await server('seeded');B=srv.base;srv.py('seed_status.py');const b=await launch();
const fails=[],errs=[];const ck=(c,m)=>{console.log((c?'ok   ':'FAIL ')+m);if(!c)fails.push(m)};
for(const [w,h] of [[1280,900],[390,844]]) for(const scheme of ['light','dark']) for(const lang of ['id','en']){
 const tag=`${w}-${scheme}-${lang}`;
 const c=await b.newContext({viewport:{width:w,height:h},colorScheme:scheme});
 await c.addInitScript(([l,t])=>{try{localStorage.setItem('bara_lang',l);localStorage.setItem('bara_theme',t);localStorage.setItem('bara_account','main')}catch(e){}},[lang,scheme]);
 const p=await c.newPage();p.on('pageerror',e=>errs.push(tag+' '+e.message));p.on('console',m=>{if(m.type()==='error'&&!/status of (400|409)/.test(m.text()))errs.push(tag+' '+m.text())});
 const posts=[];await p.route('**/api/run',(r)=>{if(r.request().method()==='POST'){posts.push(r.request().postDataJSON());return r.fulfill({status:200,contentType:'application/json',body:'{"job":{}}'})}return r.continue()});
 await p.goto(B+'/login');await p.fill('#loginUser','admin');await p.fill('#loginPass','password1');await p.click('#loginSubmit');
 await p.waitForSelector('#app:not(.hidden)');await p.waitForSelector('#needsCheck:not(.hidden)');
 const nc=await p.textContent('#needsCheck');
 ck(/Dimas/.test(nc)&&/Pesan Tidak Terverifikasi/.test(nc)&&/Perlu Dicek|Needs Attention/.test(nc),tag+' needs-check card lists failed contact + reason');
 ck(await p.locator('#needsCheckList .nc-row').count()===1,tag+' only failed contacts listed');
 await p.screenshot({path:SH+`status-dash-${tag}.png`});
 await p.click('#needsCheckList button');await p.waitForTimeout(300);
 ck(posts.length===1&&JSON.stringify(posts[0].contacts)==='["Dimas"]'&&posts[0].mode==='send',tag+' resend posts just that contact '+JSON.stringify(posts[0]));
 await p.click('#tabs [data-tab=contacts]');await p.waitForSelector('#contactsList .streak-chip');
 const rina=p.locator('#contactsList li',{hasText:'Rina'}).first(),dimas=p.locator('#contactsList li',{hasText:'Dimas'}).first(),sari=p.locator('#contactsList li',{hasText:'Sari Putri'}).first();
 ck(/3 (Hari|Days)/.test(await rina.locator('.streak-chip').textContent()),tag+' Rina streak 3: '+await rina.locator('.streak-chip').textContent());
 ck(/Terkirim|Sent/.test(await rina.locator('.badge').first().textContent())&&/Terakhir Terkirim|Last Sent/.test(await rina.textContent()),tag+' Rina sent + last sent');
 ck(/Gagal|Failed/.test(await dimas.locator('.badge').first().textContent()),tag+' Dimas failed badge');
 ck(/Menunggu|Pending/.test(await sari.locator('.badge').first().textContent())&&/Belum Pernah|Never/.test(await sari.textContent()),tag+' Sari pending + never sent');
 ck(await p.evaluate(()=>document.documentElement.scrollWidth<=document.documentElement.clientWidth),tag+' no horizontal overflow');
 await p.screenshot({path:SH+`status-contacts-${tag}.png`,fullPage:true});
 await c.close();}
console.log(errs.length?'ERRS '+errs.slice(0,5).join(' | '):'ERRS none');console.log(fails.length?'FAILS '+fails.length:'ALL OK');await b.close();await srv.cleanup();})().catch((e)=>{console.log('FAIL exception '+(e&&e.stack||e));process.exit(1)});
