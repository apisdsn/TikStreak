const { launch, server, SH } = require('./lib');
let B;
(async()=>{const srv=await server('seeded');B=srv.base;const b=await launch();
const fails=[],errs=[];const ck=(c,m)=>{console.log((c?'ok   ':'FAIL ')+m);if(!c)fails.push(m)};
const combos=[];for(const [w,h] of [[390,844],[1280,900]]) for(const scheme of ['light','dark']) for(const lang of ['id','en']) combos.push([w,h,scheme,lang]);
for(const [w,h,scheme,lang] of combos){
 const tag=`${w}-${scheme}-${lang}`;
 const c=await b.newContext({viewport:{width:w,height:h},colorScheme:scheme});
 await c.addInitScript(([l,t])=>{try{localStorage.setItem('bara_lang',l);localStorage.setItem('bara_theme',t);localStorage.setItem('bara_account','main')}catch(e){}},[lang,scheme]);
 const p=await c.newPage();p.on('pageerror',e=>errs.push(tag+' '+e.message));p.on('console',m=>{if(m.type()==='error'&&!/status of 400/.test(m.text()))errs.push(tag+' '+m.text())});
 await p.goto(B+'/login');await p.fill('#loginUser','admin');await p.fill('#loginPass','password1');await p.click('#loginSubmit');
 await p.waitForSelector('#app:not(.hidden)');await p.click('#tabs [data-tab=accounts]');await p.waitForSelector('#variationsGroup');
 ck(await p.locator('#variationList textarea').count()===0,tag+' starts with no variations');
 {
  await p.click('#btnAddVariation');await p.fill('#variationList textarea >> nth=0','Halo {nama}, hari ke-{hari}!');
  const pv=await p.textContent('#variationPreview');
  ck(pv.includes('Halo Rina, hari ke-128!'),tag+' preview fills placeholders: '+pv);
  await p.check('#randomEmoji');ck((await p.textContent('#variationPreview')).includes('✨'),tag+' preview shows sample emoji');
  await p.uncheck('#randomEmoji');
  ck((await p.textContent('#variationsCount')).includes('1/20'),tag+' counter');
  // batas 20
  for(let i=0;i<25;i++){await p.click('#btnAddVariation').catch(()=>{});}
  ck(await p.locator('#variationList textarea').count()===20,tag+' capped at 20 rows');
  await p.screenshot({path:SH+`variations-${tag}.png`,fullPage:true});
  // hapus semua selain satu
  while(await p.locator('#variationList .var-row').count()>1) await p.locator('#variationList .var-row >> nth=1').locator('button').click();
  ck(await p.locator('#variationList .var-row').count()===1,tag+' delete rows');
  // pesan default tampil sebagai pratinjau saat kosong
  await p.fill('#variationList textarea','');ck(/Default|default/.test(await p.textContent('#variationPreview')),tag+' empty -> fallback hint');
 }
 await c.close();}
// persistensi: simpan lewat UI, muat ulang
{const c=await b.newContext({viewport:{width:1280,height:900}});const p=await c.newPage();
 await p.goto(B+'/login');await p.fill('#loginUser','admin');await p.fill('#loginPass','password1');await p.click('#loginSubmit');await p.waitForSelector('#app:not(.hidden)');
 await p.click('#tabs [data-tab=accounts]');
 await p.click('#btnAddVariation');await p.fill('#variationList textarea >> nth=0','Pertama {nama}');await p.click('#btnAddVariation');await p.fill('#variationList textarea >> nth=1','Kedua {hari}');await p.check('#randomEmoji');
 await p.click('#btnSaveVariations');await p.waitForTimeout(600);
 await p.reload();await p.waitForSelector('#app:not(.hidden)');await p.click('#tabs [data-tab=accounts]');await p.waitForTimeout(300);
 const vals=await p.locator('#variationList textarea').evaluateAll(els=>els.map(e=>e.value));
 ck(JSON.stringify(vals)==='["Pertama {nama}","Kedua {hari}"]'&&await p.isChecked('#randomEmoji'),'saved variations + emoji persist after reload: '+JSON.stringify(vals));
 await c.close();}
console.log(errs.length?'ERRS '+errs.slice(0,5).join(' | '):'ERRS none');console.log(fails.length?'FAILS '+fails.length:'ALL OK');await b.close();await srv.cleanup();})().catch((e)=>{console.log('FAIL exception '+(e&&e.stack||e));process.exit(1)});
