const { launch, server, fixtureServer, SH, ROOT } = require('./lib');
let B;

(async()=>{const srv=await server('setup',{});B=srv.base;const b=await launch();
const errs=[],fails=[];const ck=(c,m)=>{console.log((c?'ok   ':'FAIL ')+m);if(!c)fails.push(m)};
srv.py('seed_jobs.py');
for(const [w,h] of [[1280,900],[390,844]]) for(const lang of ['id','en']){
 const tag=`${w}-${lang}`;
 const c=await b.newContext({viewport:{width:w,height:h}});
 await c.addInitScript(([l])=>{try{localStorage.setItem('bara_lang',l);localStorage.setItem('bara_account','main')}catch(e){}},[lang]);
 const p=await c.newPage();
 p.on('pageerror',e=>errs.push(tag+' pageerror '+e.message));p.on('console',m=>{if(['error','warning'].includes(m.type()))errs.push(tag+' console '+m.text())});
 await p.goto((B+'/login'));await p.waitForSelector('#login:not(.hidden)');
 await p.fill('#loginUser','admin');await p.fill('#loginPass','password1');await p.click('#loginSubmit');
 await p.waitForSelector('#app:not(.hidden)');await p.waitForSelector('#queueBox .qrow');await p.waitForTimeout(400);
 const q=await p.textContent('#queueBox');
 ck(/Posisi 1|Position 1/.test(q)&&/(Dalam Antrean|Queued)/.test(q)&&/(Perkiraan|Estimated) \d\d:\d\d/.test(q),tag+' queue text: '+q);
 ck(await p.isDisabled('#btnSend'),tag+' send disabled while queued');
 ck((await p.textContent('#queuePill')).match(/Antrean|Queued/)!==null,tag+' pill '+await p.textContent('#queuePill'));
 await p.screenshot({path:SH+`queue-${tag}.png`});
 await p.click('[data-tab=cookies]').catch(()=>p.click('#tabs [data-tab=cookies]'));await p.waitForTimeout(300);
 const q2=await p.textContent('#cookieQueue');ck(/Posisi|Position/.test(q2),tag+' cookie queue: '+q2);
 ck(await p.isDisabled('#btnCheckCookies'),tag+' check disabled');
 // cancel check job
 await p.click('#cookieQueue button');await p.waitForTimeout(700);
 ck(await p.isHidden('#cookieQueue')&&!await p.isDisabled('#btnCheckCookies'),tag+' cancelled -> hidden+enabled');
 // schedules hint
 await p.evaluate(async()=>{const sch=[];for(let i=0;i<8;i++)sch.push({id:null,enabled:true,time:'08:'+String(i*3).padStart(2,'0'),message:'',contacts:null});
   const H={'X-Requested-With':'bara','Content-Type':'application/json'};
   await fetch('/api/accounts/main',{method:'PUT',headers:H,body:JSON.stringify({schedules:sch})});
   await fetch('/api/accounts/second',{method:'PUT',headers:H,body:JSON.stringify({schedules:[{id:null,enabled:true,time:'08:05',message:'',contacts:null},{id:null,enabled:true,time:'14:00',message:'',contacts:null}]})});});
 await p.reload();await p.waitForSelector('#app:not(.hidden)');await p.waitForTimeout(800);
 await p.click('#tabs [data-tab=accounts]').catch(()=>{});await p.waitForTimeout(300);
 const vis=await p.locator('.sched .busy-hint:not(.hidden)').count();
 ck(vis===8,tag+' busy hints on 8 rows (got '+vis+')');
 const ht=await p.locator('.sched .busy-hint:not(.hidden)').first().textContent();
 ck(/Jam Ini Ramai, Pilih Jam Lain agar Lebih Cepat|This Time Is Busy, Pick Another Time for Faster Delivery/.test(ht),tag+' hint text '+ht);
 // change a row to quiet hour -> hint hides
 await p.locator('.sched').first().locator('select').first().selectOption('03');await p.waitForTimeout(150);
 ck(await p.locator('.sched').first().locator('.busy-hint').isHidden(),tag+' hint hides at 03:xx');
 await p.screenshot({path:SH+`hint-${tag}.png`});
 // admin stats
 await p.click('#tabs [data-tab=settings]').catch(()=>{});await p.waitForTimeout(500);
 const qa=await p.textContent('#queueAdminList');ck(/(Pekerja Browser|Browser Workers)/.test(qa)&&/1/.test(qa),tag+' admin queue: '+qa.replace(/\s+/g,' ').slice(0,120));
 await p.locator('#queueAdminList').scrollIntoViewIfNeeded();await p.screenshot({path:SH+`qadmin-${tag}.png`});
 // reset schedules for next iteration
 await p.evaluate(async()=>{const H={'X-Requested-With':'bara','Content-Type':'application/json'};for(const a of ['main','second'])await fetch('/api/accounts/'+a,{method:'PUT',headers:H,body:JSON.stringify({schedules:[]})});});
 srv.py('seed_jobs.py');
 await c.close();
}
console.log('ERRS',errs.length?errs.slice(0,10):'none');console.log(fails.length?'FAILS '+fails.length:'ALL OK');await b.close();await srv.cleanup();})().catch(async(e)=>{console.log('FAIL exception '+(e&&e.stack||e));process.exit(1)});
