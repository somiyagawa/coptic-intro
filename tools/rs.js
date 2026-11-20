/* RS v2：表示の組み直し（tools/restyle.py が本体スクリプトの前に差し込む）。
   課を開いたときに一度だけ、その課の DOM を次のように組み直す。
   - 太字の見出しで始まる項目 → 見出し＋説明のカード
   - 「コプト語＋「訳」」で始まる項目 → 番号つきの行間グロス例文
   - 説明文の中の「例文「訳」（出典）」→ 独立した例文ブロック
   - 講読本文 → 節ごとの行間グロス＋その節の訳
   - グロスを並べない場所の語 → 押すと分析が出る */
(function(){
'use strict';
function el(tag,cls,txt){var e=document.createElement(tag); if(cls) e.className=cls; if(txt!=null) e.textContent=txt; return e}
function isCopt(n){return !!n&&n.nodeType===1&&n.classList.contains('copt')}
function firstReal(p){var f=p.firstChild; while(f&&f.nodeType===3&&!f.data.trim()) f=f.nextSibling; return f}
function quoteEnd(s){ if(s.charAt(0)!=='「') return -1; var d=0,i,c; for(i=0;i<s.length;i++){c=s.charAt(i); if(c==='「') d++; else if(c==='」'){d--; if(d===0) return i+1}} return -1}
function restBlank(n){ for(n=n.nextSibling;n;n=n.nextSibling){ if(n.nodeType===3){ if(n.data.trim()) return false } else return false } return true }

/* 0. ルビが二重に付いている箇所（解答欄など）を一重に戻す */
function flatten(root){
  for(var pass=0;pass<3;pass++){
    var outers=[];
    root.querySelectorAll('.rw .copt').forEach(function(c){ var o=c.parentNode.closest('.rb'); if(o&&!(o.parentNode.closest&&o.parentNode.closest('.rb'))&&outers.indexOf(o)<0) outers.push(o) });
    if(!outers.length) return;
    outers.forEach(function(o){
      var inner=o.querySelector('.w0 .copt')||o.querySelector('.rw .copt'); if(!inner||!o.parentNode) return;
      while(inner.firstChild) o.parentNode.insertBefore(inner.firstChild,o);
      o.remove();
    });
  }
}

/* 1. 見出しつきの項目 */
function points(root){
  root.querySelectorAll('li').forEach(function(li){
    if(li.dataset.rs||li.closest('.fig,table')) return;
    var f=firstReal(li); if(!f||f.nodeType!==1||f.tagName!=='STRONG') return;
    var nx=f.nextSibling; if(!nx||nx.nodeType!==3||!/^\s*[：:]/.test(nx.data)) return;
    li.dataset.rs='pt'; li.classList.add('pt');
    var h=el('div','pt-h'), b=el('div','pt-b'); while(f.firstChild) h.appendChild(f.firstChild);
    nx.data=nx.data.replace(/^\s*[：:]\s*/,''); f.remove();
    while(li.firstChild) b.appendChild(li.firstChild);
    li.appendChild(h); li.appendChild(b); li.parentNode.classList.add('pts');
  });
  root.querySelectorAll('p').forEach(function(p){
    var f=firstReal(p); if(f&&f.nodeType===1&&f.tagName==='STRONG'&&/^(他の文法書|出典)/.test(f.textContent)) p.classList.add('refp');
  });
}

/* 2. 番号つきの例文 */
function igtItems(root){
  var lists=[];
  root.querySelectorAll('li').forEach(function(li){
    if(li.dataset.rs||li.closest('.fig,table')) return;
    var f=firstReal(li); if(!isCopt(f)) return;
    var nx=f.nextSibling; if(!nx||nx.nodeType!==3) return;
    var s=nx.data.replace(/^\s+/,''), k=quoteEnd(s); if(k<0) return;
    li.dataset.rs='igt'; li.classList.add('igt');
    var body=el('div','igt-b'), line=el('div','igt-l'), tr=el('div','igt-t',s.slice(0,k)), note=el('div','igt-s');
    line.appendChild(f); nx.data=s.slice(k).replace(/^[\s　]+/,'');
    while(li.firstChild) note.appendChild(li.firstChild);
    note.querySelectorAll('small').forEach(function(sm){ var t=sm.textContent; if(/^〔[\s\S]*〕$/.test(t)&&!sm.children.length) sm.textContent=t.slice(1,-1) });
    body.appendChild(line); body.appendChild(tr); if(note.textContent.trim()) body.appendChild(note);
    li.appendChild(body); if(lists.indexOf(li.parentNode)<0) lists.push(li.parentNode);
  });
  lists.forEach(function(ul){
    var all=Array.prototype.every.call(ul.children,function(c){return c.classList.contains('igt')});
    if(all) ul.classList.add('igts'); else Array.prototype.forEach.call(ul.children,function(c){ if(c.classList.contains('igt')) c.classList.add('lone') });
  });
}

/* 3. 説明文の中の例文を取り出す */
function tryBlock(E,c){
  var t=c.nextSibling; if(!t||t.nodeType!==3) return null;
  var s=t.data.replace(/^\s+/,''), k=quoteEnd(s); if(k<0) return null;
  var rest=s.slice(k), refText=null, refNodes=null, tail=rest, tailNode=t, mid=[];
  if(rest.charAt(0)==='（'){
    var d=0,j=-1,i,ch;
    for(i=0;i<rest.length;i++){ch=rest.charAt(i); if(ch==='（') d++; else if(ch==='）'){d--; if(d===0){j=i;break}}}
    if(j>=0){refText=rest.slice(1,j); tail=rest.slice(j+1)}
    else{
      var m=t.nextSibling, found=false, n=0; refNodes=[document.createTextNode(rest.slice(1))];
      while(m&&n<14){ n++;
        if(m.nodeType===3){ var x=m.data, q=-1;
          for(i=0;i<x.length;i++){ch=x.charAt(i); if(ch==='（') d++; else if(ch==='）'){d--; if(d===0){q=i;break}}}
          if(q>=0){refNodes.push(document.createTextNode(x.slice(0,q))); tail=x.slice(q+1); tailNode=m; found=true; break}
          refNodes.push(m); mid.push(m);
        } else {refNodes.push(m); mid.push(m)}
        m=m.nextSibling;
      }
      if(!found) return null;
    }
  }
  var tl=tail.replace(/^[\s　]+/,''), c0=tl.charAt(0);
  if(!(c0==='、'||c0==='。'||(!tl&&restBlank(tailNode)))) return null;
  var g=el('span','igx'), l=el('span','igx-l'), tr=el('span','igx-t',s.slice(0,k));
  E.insertBefore(g,c); l.appendChild(c); g.appendChild(l); g.appendChild(tr);
  if(refText!=null){g.appendChild(el('span','igx-s',refText))}
  else if(refNodes){var r=el('span','igx-s'); refNodes.forEach(function(x){r.appendChild(x)}); g.appendChild(r)}
  if(tailNode!==t) t.remove();
  tailNode.data=tl.replace(/^[、。]/,'');
  return g;
}
function blockify(E){
  var n=E.firstChild, depth=0, prev='', after=false, next, d, i, ch, tt, g;
  while(n){
    next=n.nextSibling;
    if(n.nodeType===3){
      d=n.data; for(i=0;i<d.length;i++){ch=d.charAt(i); if(ch==='（'||ch==='(') depth++; else if(ch==='）'||ch===')') depth=Math.max(0,depth-1)}
      tt=d.replace(/[\s　]+$/,''); if(tt){prev=tt.slice(-1); after=false}
    } else if(n.nodeType===1){
      if(isCopt(n)&&depth===0&&(prev===''||prev==='：'||prev===':'||prev==='。'||after)&&n.querySelectorAll('.rb.g').length>=2){
        g=tryBlock(E,n); if(g){n=g.nextSibling; after=true; prev='。'; continue}
      }
      prev='x'; after=false;
    }
    n=next;
  }
}
function prose(root){
  root.querySelectorAll('li').forEach(function(li){
    if(li.dataset.rs==='igt'||li.closest('.fig,table,blockquote')) return;
    blockify(li.dataset.rs==='pt'?li.lastChild:li);
  });
  root.querySelectorAll('p').forEach(function(p){ if(!p.closest('.fig,table,blockquote,li,.ex,.ans')) blockify(p) });
}

/* 4. 講読本文 */
function attach(node,p){
  var rws=node.nodeType===1?node.querySelectorAll('.rw'):[];
  if(rws.length) rws[rws.length-1].appendChild(el('span','pc',p)); else if(node.parentNode) node.parentNode.insertBefore(document.createTextNode(p),node.nextSibling);
}
function innerPunct(c,brk){
  Array.prototype.slice.call(c.childNodes).forEach(function(n){
    if(n.nodeType!==3) return; var m=n.data.match(/^\s*([·.,;:!?])\s*$/); if(!m) return;
    var p=n.previousSibling; if(!p||p.nodeType!==1||!p.classList.contains('rb')) return;
    var rw=p.querySelector('.rw'); if(!rw) return; rw.appendChild(el('span','pc',m[1]));
    if(brk){c.insertBefore(el('span','lb'),n); n.data=''} else n.data=' ';
  });
}
function readings(root){
  root.querySelectorAll('blockquote').forEach(function(bq){
    if(bq.dataset.rs) return; bq.dataset.rs='rd'; if(!bq.querySelector('.copt')) return;
    var segs=[], ok=true;
    Array.prototype.forEach.call(bq.children,function(p){
      if(p.tagName!=='P'){ok=false; return}
      var cur=null;
      Array.prototype.slice.call(p.childNodes).forEach(function(n){
        if(n.nodeType===3){
          var m=n.data.match(/^\s*([.,;:·!?—]*)\s*(\d{1,3}|\([a-z]\))?\s*$/);
          if(m){
            if(m[1]&&cur&&cur.nodes.length) cur.punct.push([cur.nodes[cur.nodes.length-1],m[1]]);
            if(m[2]){cur={label:m[2],nodes:[],punct:[]}; segs.push(cur)} else if(cur&&cur.nodes.length) cur.nodes.push(document.createTextNode(' '));
            return;
          }
        }
        if(!cur){cur={label:'',nodes:[],punct:[]}; segs.push(cur)}
        cur.nodes.push(n);
      });
    });
    if(!ok||!segs.length) return;
    var labelled=segs.every(function(s){return s.label});
    bq.classList.add('rd'); bq.textContent='';
    segs.forEach(function(s){
      var v=el('div','vs'+(s.label?'':' nolab')), b=el('div','vbody'), l=el('div','vl');
      if(s.label) v.appendChild(el('span','vn',s.label.replace(/[()]/g,'')));
      s.nodes.forEach(function(n){l.appendChild(n)}); s.punct.forEach(function(x){attach(x[0],x[1])});
      l.querySelectorAll('.copt').forEach(function(c){innerPunct(c,!labelled)});
      if(!labelled) l.querySelectorAll('.copt').forEach(function(c){ var rws=c.querySelectorAll('.rw'), lw=rws[rws.length-1]; if(lw&&lw.querySelector('.pc')&&c.nextSibling) c.parentNode.insertBefore(el('span','lb'),c.nextSibling) });
      b.appendChild(l); v.appendChild(b); bq.appendChild(v); s.box=b;
    });
    var tp=bq.nextElementSibling; if(!tp||tp.tagName!=='P'||!/^訳[：:]/.test(tp.textContent)) return;
    var text=tp.textContent.replace(/^訳[：:]\s*/,''), pos=[], from=0, good=labelled;
    if(good) segs.forEach(function(s){
      if(!good) return; var ix,len;
      if(/^\d/.test(s.label)){var re=new RegExp('(^|[「『\\s。、」』])'+s.label+'[\\s　]'), sub=text.slice(from), m=sub.match(re); if(!m){good=false; return} ix=from+m.index+m[1].length; len=s.label.length}
      else{ix=text.indexOf(s.label,from); if(ix<0){good=false; return} len=s.label.length}
      pos.push([ix,len]); from=ix+len;
    });
    if(!good){ tp.classList.add('trp'); if(tp.firstChild&&tp.firstChild.nodeType===3) tp.firstChild.data=tp.firstChild.data.replace(/^訳[：:]\s*/,''); return }
    segs.forEach(function(s,i){
      var piece=text.slice(pos[i][0]+pos[i][1], i+1<pos.length?pos[i+1][0]:text.length).replace(/^[\s　]+|[\s　]+$/g,'');
      var op=(piece.match(/「/g)||[]).length, cl=(piece.match(/」/g)||[]).length;
      if(cl>op&&/」$/.test(piece)) piece=piece.slice(0,-1); else if(op===cl&&/^「[\s\S]*」$/.test(piece)&&quoteEnd(piece)===piece.length) piece=piece.slice(1,-1);
      if(op>cl&&/^「/.test(piece)) piece=piece.slice(1);
      var p=el('p','vt tr',piece); p.addEventListener('click',function(){ if(document.documentElement.getAttribute('data-tr')==='hide') p.classList.toggle('show') });
      s.box.appendChild(p);
    });
    tp.remove();
  });
}

/* 5. ハイフンでつないだ語形を行の途中で切らない */
function bound(root){
  root.querySelectorAll('.copt').forEach(function(c){
    if(c.dataset.bg||c.closest('blockquote,.fig')) return; c.dataset.bg='1';
    var need=false, kids=Array.prototype.slice.call(c.childNodes);
    kids.forEach(function(k){ if(k.nodeType===3&&/[-⸗]/.test(k.data)) need=true }); if(!need) return;
    var frag=document.createDocumentFragment(), grp=null;
    function open(){ if(!grp){grp=el('span','bg'); frag.appendChild(grp)} return grp }
    kids.forEach(function(k){
      if(k.nodeType===3&&/\s/.test(k.data)){
        k.data.split(/(\s+)/).forEach(function(part){ if(!part) return; if(/^\s+$/.test(part)){grp=null; frag.appendChild(document.createTextNode(part))} else open().appendChild(document.createTextNode(part)) });
      } else open().appendChild(k);
    });
    c.textContent=''; c.appendChild(frag);
  });
}

/* 5b. 表：語彙表の見出し語にはグロスを付けない／短い見出しの列は折り返さない */
function tables(root){
  root.querySelectorAll('table').forEach(function(tb){
    var heads=Array.prototype.map.call(tb.querySelectorAll('thead th'),function(h){return h.textContent.trim()});
    if(heads.indexOf('意味')>=0&&heads.indexOf('転写')>=0) tb.querySelectorAll('tbody td:first-child .rb.g').forEach(function(w){
      w.classList.remove('g'); w.querySelectorAll('.gl,.gp,.w1').forEach(function(x){x.remove()});
    });
    tb.querySelectorAll('tbody td:first-child').forEach(function(td){ if(!td.querySelector('.copt')&&td.textContent.trim().length<=9) td.classList.add('nw') });
  });
}

/* 6. 表示の切り替え */
var KEYS=[['latin','転写'],['kana','カナ'],['seg','区切り'],['gl','略号グロス'],['gp','やさしいグロス']];
function vbar(sec){
  var body=sec.querySelector('.lesson-body'); if(!body||sec.querySelector('.vbar')||!body.querySelector('.rb')) return;
  var bar=el('div','vbar'); bar.setAttribute('role','group'); bar.setAttribute('aria-label','行の表示'); bar.appendChild(el('span','vb-t','表示'));
  KEYS.forEach(function(k){var b=el('button','vb',k[1]); b.type='button'; b.dataset.k=k[0]; bar.appendChild(b)});
  var h=el('button','linkbtn vb-h','略号一覧'); h.type='button'; h.dataset.go='apxC'; bar.appendChild(h);
  sec.insertBefore(bar,body); sync();
}
function sync(){
  var R=window.__rs; if(!R) return;
  document.querySelectorAll('.vbar .vb').forEach(function(b){b.setAttribute('aria-pressed',String(!!R.S[b.dataset.k]))});
}
window.__rsSync=sync;
document.addEventListener('click',function(e){
  var b=e.target.closest&&e.target.closest('.vbar .vb'); if(!b||!window.__rs) return;
  var R=window.__rs; R.S[b.dataset.k]=!R.S[b.dataset.k]; R.apply();
});

/* 7. 語の分析 */
var ABBR=null, pop=null, cur=null, pinned=false, timer=null;
function abbr(){
  if(ABBR) return ABBR; ABBR={'1':'1人称','2':'2人称','3':'3人称','SG':'単数','PL':'複数','M':'男性','F':'女性'};
  document.querySelectorAll('#apxC table tbody tr').forEach(function(tr){
    var a=tr.cells[0]&&tr.cells[0].textContent.trim(), b=tr.cells[1]&&tr.cells[1].textContent.trim();
    if(a&&b&&/^[A-Z0-9.]+$/.test(a)) ABBR[a]=b;
  });
  return ABBR;
}
function hidePop(){ if(pop) pop.hidden=true; if(cur) cur.classList.remove('on'); cur=null; pinned=false }
function showPop(w,pin){
  var A=abbr(); if(!pop){pop=el('div','gpop'); pop.setAttribute('role','tooltip'); document.body.appendChild(pop)}
  if(cur) cur.classList.remove('on'); cur=w; pinned=!!pin; w.classList.add('on'); pop.textContent='';
  var w1=w.querySelector('.w1'), rl=w.querySelector('.rl'), rk=w.querySelector('.rk'), gl=w.querySelector('.gl'), gp=w.querySelector('.gp');
  var pw=el('div','pw'); pw.lang='cop'; if(w1) pw.innerHTML=w1.innerHTML; pop.appendChild(pw);
  if(rk||rl){var pr=el('div','pr'); if(rk){var kb=el('b'); kb.innerHTML=rk.innerHTML; pr.appendChild(kb)} if(rl) pr.appendChild(el('i',null,rl.textContent)); pop.appendChild(pr)}
  if(gl){var pg=el('div','pg'); pg.innerHTML=gl.innerHTML; pop.appendChild(pg)}
  if(gp) pop.appendChild(el('div','pp',gp.textContent));
  if(gl){
    var seen={}, list=[], t=gl.textContent;
    gl.querySelectorAll('.sc').forEach(function(s){var k=s.textContent.toUpperCase(); if(!seen[k]&&A[k]){seen[k]=1; list.push(k)}});
    ['1','2','3'].forEach(function(k){ if(new RegExp('(^|[^0-9])'+k+'(?=[A-Za-z])').test(t)&&!seen[k]){seen[k]=1; list.unshift(k)} });
    if(list.length){var dl=el('dl','pa'); list.forEach(function(k){dl.appendChild(el('dt',null,k)); dl.appendChild(el('dd',null,A[k]))}); pop.appendChild(dl)}
  }
  pop.hidden=false; pop.style.left='0px'; pop.style.top='0px';
  var r=w.getBoundingClientRect(), pw2=pop.offsetWidth, ph=pop.offsetHeight, vw=document.documentElement.clientWidth;
  var x=Math.max(8,Math.min(r.left,vw-pw2-8)), y=r.bottom+8;
  if(y+ph>window.innerHeight-8&&r.top-ph-8>8) y=r.top-ph-8;
  pop.style.left=(x+window.scrollX)+'px'; pop.style.top=(y+window.scrollY)+'px';
}
function word(t){ var w=t&&t.closest&&t.closest('.rb.g'); return w&&!w.closest('.fig')&&!w.classList.contains('lab')?w:null }
document.addEventListener('click',function(e){
  if(e.target.closest&&e.target.closest('.gpop')) return;
  var w=word(e.target); if(!w){ if(cur) hidePop(); return }
  if(cur===w&&pinned){hidePop(); return}
  showPop(w,true);
});
if(window.matchMedia&&window.matchMedia('(hover:hover)').matches){
  document.addEventListener('mouseover',function(e){ var w=word(e.target); if(!w||pinned) return; var g=w.querySelector('.gl'); if(g&&getComputedStyle(g).display!=='none') return; clearTimeout(timer); timer=setTimeout(function(){ if(!pinned) showPop(w,false) },260) });
  document.addEventListener('mouseout',function(e){ if(!word(e.target)) return; clearTimeout(timer); if(!pinned) timer=setTimeout(function(){ if(!pinned) hidePop() },140) });
}
document.addEventListener('keydown',function(e){ if(e.key==='Escape') hidePop() });
document.addEventListener('stepchange',function(){
  hidePop();
  var t=document.querySelector('.view:not([hidden]) .stab[aria-current="step"]'), box=t&&t.parentNode;
  if(box&&box.scrollWidth>box.clientWidth+4) box.scrollLeft=Math.max(0,t.offsetLeft-box.offsetLeft-(box.clientWidth-t.offsetWidth)/2);
});
window.addEventListener('resize',hidePop);

/* 8. クイズを数字キーで答える */
document.addEventListener('keydown',function(e){
  if(e.metaKey||e.ctrlKey||e.altKey||(e.target.closest&&e.target.closest('input,textarea,select'))) return;
  var v=document.querySelector('.view:not([hidden])'); if(!v) return;
  var box=null; v.querySelectorAll('.opts').forEach(function(o){ if(o.offsetParent!==null) box=o }); if(!box) return;
  if(/^[1-4]$/.test(e.key)){var o=box.querySelectorAll('.opt')[+e.key-1]; if(o&&!o.disabled){o.click(); e.preventDefault()}}
});

/* 入口：本体の show() から呼ばれる */
window.__rsEnh=function(sec){
  if(!sec||sec.dataset.rsDone) return; sec.dataset.rsDone='1';
  var body=sec.querySelector('.lesson-body'); if(!body) return;
  try{
    body.querySelectorAll('.step').forEach(function(st){var h=st.querySelector('h3'); if(h&&/この課の要点/.test(h.textContent)) st.classList.add('kp')});
    flatten(body); points(body); igtItems(body); readings(body); prose(body); tables(body); bound(body); vbar(sec);
  }catch(err){ if(window.console) console.error('rs',err) }
};
})();
