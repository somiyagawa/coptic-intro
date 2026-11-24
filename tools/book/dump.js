/* 本（PDF）用：ページを開いて全部の課を組み直し（tools/rs.js）、組み直した後の本文を JSON に書き出す。
   使い方: node dump.js <sahidic.html|bohairic.html のパス> <出力.json> */
const {chromium}=require('playwright');
const fs=require('fs');
const [,, page_, out]=process.argv;
(async()=>{
  const b=await chromium.launch(); const p=await b.newPage({viewport:{width:1280,height:900}});
  const errs=[]; p.on('pageerror',e=>errs.push(e.message));
  await p.goto('file://'+require('path').resolve(page_)); await p.waitForTimeout(800);
  // 本では転写・カナ・区切り・両グロスをすべて出す（設定に左右されないように既定に戻す）
  await p.evaluate(()=>{const R=window.__rs; Object.assign(R.S,{latin:true,kana:true,seg:true,gl:true,gp:true,gloss:'all',prose:'kana'}); R.apply()});
  const data=await p.evaluate(()=>{
    const out={title:document.title, parts:[], sections:[]};
    // 目次の構成（編と課）
    let cur=null;
    document.querySelectorAll('nav.side > *').forEach(function walk(e){
      if(e.matches('h3')){ cur={name:e.childNodes[0].textContent.trim(), ids:[]}; out.parts.push(cur) }
      else if(e.matches('[data-go]')){ if(!cur){cur={name:'',ids:[]}; out.parts.push(cur)} cur.ids.push(e.getAttribute('data-go')) }
      else [...e.children].forEach(walk);
    });
    const ids=[...document.querySelectorAll('section.view')].map(s=>s.id);
    ids.forEach(id=>{ const g=document.querySelector('[data-go="'+id+'"]'); if(g) g.click() });
    ids.forEach(id=>{
      const s=document.getElementById(id); const body=s.querySelector('.lesson-body');
      const h2=s.querySelector('h2'), eb=s.querySelector('.eyebrow'), meta=s.querySelector('.lmeta');
      const nav=document.querySelector('[data-go="'+id+'"]');
      out.sections.push({id:id, eyebrow:eb?eb.textContent.trim():'', title:h2?h2.innerHTML:'', meta:meta?meta.textContent.trim():'',
        nav:nav?nav.textContent.replace(/\s+/g,' ').trim():'', html:body?body.innerHTML:s.innerHTML, hasBody:!!body});
    });
    return out});
  data.errors=errs;
  fs.writeFileSync(out,JSON.stringify(data));
  console.log(page_,'sections',data.sections.length,'parts',data.parts.map(x=>x.name+':'+x.ids.length).join(' '),'errors',errs.length);
  await b.close();
})();
