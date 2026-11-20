# -*- coding: utf-8 -*-
"""ビルド済みのページ（コミット 2003160 の sahidic.html / bohairic.html）に、表示の改良を重ねる。

    python3 tools/restyle.py BASE_DIR OUT_DIR

BASE_DIR には改良前のページを置く（git show 2003160:sahidic.html > BASE_DIR/sahidic.html など）。
同じ入力からは同じ出力ができる。重ねる内容：
  - tools/rs.css   読みやすさの層（文字の大きさ、例文・講読本文・クイズの体裁）
  - tools/rs.js    課を開いたときの DOM の組み直し（例文ブロック、節ごとの訳、語の分析）
  - tools/kana_s.py サイード方言のカタカナ（重ね書きの母音、ⲃ）
"""
import re, json, sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kana_s

UNIT = re.compile(r'(<span class="rt" aria-hidden="true"><span class="rl">.*?</span><span class="rk">)(.*?)(</span></span><span class="rw">)(.*?)(</span></span>)', re.S)

def one(t, a, b, n=1):
    assert t.count(a) == n, (t.count(a), a[:70])
    return t.replace(a, b)

def word_of(rw):
    m = re.search(r'<span class="w0">(.*?)</span>', rw)
    return re.sub(r'<[^>]+>', '', m.group(1) if m else rw)

RK = re.compile(r'(<span class="rk">)(.*?)(</span></span><span class="rw">)', re.S)
COPT = re.compile('[\u2c80-\u2cff\u03e2-\u03ef][\u2c80-\u2cff\u03e2-\u03ef\u0300-\u036f\ufe24-\ufe26⸗]*')

def kana_sahidic(t):
    stat = {'units': 0, 'changed': 0, 'problems': []}
    def f(m):
        w = COPT.search(t, m.end(), m.end() + 1500); stat['units'] += 1
        if not w: stat['problems'].append(('noword', m.group(2))); return m.group(0)
        w = w.group(0); k2, st = kana_s.patch(w, m.group(2))
        if st[0] in ('ambiguous', 'nomatch') or st[1].startswith('count'): stat['problems'].append((w, m.group(2), st))
        if k2 != m.group(2): stat['changed'] += 1
        return m.group(1) + k2 + m.group(3)
    t = RK.sub(f, t)
    # 語彙データ（クイズ・フラッシュカード）
    m = re.search(r'(<script id="data" type="application/json">)(.*?)(</script>)', t, re.S)
    D = json.loads(m.group(2)); n = 0
    def fix(item):
        nonlocal n
        if '　' in item.get('m', ''):
            lat, kana = item['m'].split('　', 1); k2, st = kana_s.patch(item['h'], kana)
            if st[0] in ('ambiguous', 'nomatch') or st[1].startswith('count'): stat['problems'].append((item['h'], kana, st))
            if k2 != kana: item['m'] = lat + '　' + k2; n += 1
    for it in D['deck']: fix(it)
    for me in D['meta']:
        for it in me.get('quiz', []): fix(it)
    t = t[:m.start(2)] + json.dumps(D, ensure_ascii=False) + t[m.end(2):]
    stat['data'] = n
    # 説明文の中のカタカナ
    C = lambda s: '<span class="copt" lang="cop"><span class="rb"><span class="rw">%s</span></span></span>' % s
    t = one(t, 'サイード方言の特徴です。授業では長く伸ばして読みます：',
            'サイード方言の特徴です。音価には、長い母音を示すとする説と、母音の後の声門の閉鎖を示すとする説があります（文法1）。この教材のカタカナは、どちらの説でも読めるように、二つ目の母音字もそのまま書きます：')
    t = one(t, '「マーウ」、', '「マアウ」、')
    t = one(t, '「ショープ」、', '「ショオプ」、')
    t = one(t, '「ワーブ」。音価には、母音の後の声門の閉鎖を示すとする説と、長い母音を示すとする説があります（文法1）。',
            '「ワアヴ」、' + C('ⲟⲩⲏⲏⲃ') + '「ウェーエヴ」。長音説では母音を伸ばして読み、声門閉鎖音説では二つの母音字の間を切って読みます。')
    i = t.index('<strong>二重母音</strong>'); j = t.index('</li>', i)
    seg = t[i:j]; k = seg.index('ⲟⲟⲩ'); k2 = seg.index('「オーウ」', k)
    seg = seg[:k2] + '「オオウ」' + seg[k2 + len('「オーウ」'):]
    t = t[:i] + seg + t[j:]
    t = one(t, 'ジョイス、マーウ、ヘン', 'ジョイス、マアウ、ヘン', 2)
    t = one(t, 'カタカナは現在の教会発音（ギリシア式ボハイラ）です。カタカナでは、ⲏ・ⲱ・重ね書きの母音・強勢のある ⲟⲩ を長音符で、母音を伴わない子音を小さい字で、形態素の境界を中黒で示します。再建音・古式発音との違いは第1課の補説にまとめています。',
            'カタカナは大学の授業で使われる読み方です。カタカナでは、ⲏ・ⲱ・強勢のある ⲟⲩ を長音符で示します。重ね書きの母音は、長音説でも声門閉鎖音説でも読めるように、二つ目の母音字もそのまま書きます（ⲙⲁⲁⲩ マアウ）。母音を伴わない子音は小さい字で、形態素の境界は中黒で示します。')
    if kana_s.B2V:
        t = one(t, '授業では「ブ」。実際には摩擦音 [β] に近かったと考えられる', 'カタカナでは「ヴ」行で書く。摩擦音 [β] に近かったと考えられる。[b] と読む流儀もある')
    t = one(t, '後者を採ります。授業では長く伸ばして読みます。',
            '後者を採ります。この教材のカタカナは、どちらの説でも読めるように、二つ目の母音字もそのまま書きます（' + C('ⲙⲁⲁⲩ') + ' マアウ、' + C('ϣⲟⲟⲡ') + ' ショオプ）。')
    return t, stat

def kana_bohairic(t):
    """ボハイラ方言版に引用されているサイード方言の語形を、サイード方言版の読みにそろえる。"""
    fixes = {('ⲗⲁⲁⲩ', 'ラア<i class="kc">ヴ</i>'): 'ラアウ', ('ⲧⲁⲁ⸗ⲩ', 'タア<i class="kc">ヴ</i>'): 'タアウ', ('ⲏⲏ', 'エエー'): 'エーエ'}
    n = [0]
    def f(m):
        key = (word_of(m.group(4)), m.group(2))
        if key in fixes: n[0] += 1; return m.group(1) + fixes[key] + m.group(3) + m.group(4) + m.group(5)
        return m.group(0)
    return UNIT.sub(f, t), n[0]

GLOSS_OLD = '<select id="st-gloss"><option value="all">例文と講読本文</option><option value="text">講読本文のみ</option><option value="off">なし</option></select></div>'
GLOSS_NEW = ('<select id="st-gloss"><option value="all">例文と講読本文</option><option value="every">説明文や表の中にも</option><option value="text">講読本文のみ</option><option value="off">並べない</option></select></div>\n'
             '      <p class="sethint">グロスを並べていない語は、押すと分析（区切り・読み・グロス・略号の意味）が出ます。</p>')

def span_end(t, i):
    """t[i] から始まる <span ...> の閉じタグの直後の位置"""
    d = 0
    for m in re.finditer(r'<(/?)span\b[^>]*>', t[i:]):
        d += -1 if m.group(1) else 1
        if d == 0: return i + m.end()
    raise ValueError

LAB = ('<span class="rb g lab"><span class="rbi"><span class="rt" aria-hidden="true"><span class="rl">転写</span><span class="rk">カナ</span></span>'
       '<span class="rw"><span class="w0"><small>本文</small></span><span class="w1"><small>本文（区切り）</small></span></span></span>'
       '<span class="gl">略号グロス</span><span class="gp">やさしいグロス</span></span> ')
VBAR = ('<div class="vbar" role="group" aria-label="行の表示"><span class="vb-t">表示</span>'
        + ''.join('<button type="button" class="vb" data-k="%s">%s</button>' % kv for kv in
                  [('latin', '転写'), ('kana', 'カナ'), ('seg', '区切り'), ('gl', '略号グロス'), ('gp', 'やさしいグロス')])
        + '<button type="button" class="linkbtn vb-h" data-go="apxC">略号一覧</button></div>')

def guide(t):
    """ホームに「画面の見方」を置く。見本は第5課の最初の例文。"""
    i = t.index('id="l5"'); i = t.index('<h3>例文で確認</h3>', i); i = t.index('<li><span class="copt"', i) + 4
    j = span_end(t, i); copt = t[i:j]; k = t.index('」', j); tr = t[j:k + 1]
    assert tr.startswith('「') and 'class="rb g' in copt
    head = '<span class="copt" lang="cop">'; assert copt.startswith(head)
    sample = head + LAB + copt[len(head):]
    html = ('<h3 class="h-sec">画面の見方</h3>\n<div class="guide">' + VBAR
            + '<div class="guide-ex"><div class="igt-l">' + sample + '</div><div class="igt-t"><b>訳</b>' + tr + '</div></div>'
            '<ul><li>例文と講読本文では、語ごとに「読み・本文・グロス」を縦に並べ、その下に訳を置いています。</li>'
            '<li>上の「表示」のボタンで、行を一つずつ出したり消したりできます。同じボタンが各課の上にもあります。</li>'
            '<li>説明文や表の中のコプト語（点線の下線つき）は、押すと分析が出ます。略号の意味もそこに出ます。</li>'
            '<li>講読本文は節ごとに区切り、その節の訳をすぐ下に置いています。訳を隠して読む練習は「表示設定」でできます。</li>'
            '<li>クイズは 1〜4 の数字キーでも答えられます。</li></ul></div>\n      ')
    a = '<h3 class="h-sec">復習ツール</h3>'
    return one(t, a, html + a)

def layer(t):
    css = open(os.path.join(HERE, 'rs.css'), encoding='utf-8').read()
    js = open(os.path.join(HERE, 'rs.js'), encoding='utf-8').read()
    i = t.index('<header class="top">'); j = t.rindex('</style>', 0, i)
    t = t[:j] + css + t[j:]
    t = guide(t)
    t = one(t, GLOSS_OLD, GLOSS_NEW)
    t = one(t, '<label for="st-gloss">グロスを付ける範囲</label>', '<label for="st-gloss">グロスを並べる範囲</label>')
    # 本体スクリプトへの差し込み
    t = one(t, "function save(){try{localStorage.setItem(KEY,JSON.stringify(S))}catch(e){}}",
            "function save(){try{localStorage.setItem(KEY,JSON.stringify(S))}catch(e){}}\nwindow.__rs={S:S,apply:function(){applySet()}};")
    t = one(t, "if(byId[id]){dress($(id));", "if(byId[id]){dress($(id)); if(window.__rsEnh) window.__rsEnh($(id));")
    t = one(t, "R.setAttribute('data-gloss',S.gloss);", "R.setAttribute('data-gloss',S.gloss==='all'?'ex':S.gloss==='every'?'all':S.gloss);")
    t = one(t, "$('st-rs').value=S.rs; save();", "$('st-rs').value=S.rs; save(); if(window.__rsSync) window.__rsSync();")
    t = one(t, "het.textContent=q.h; fb.textContent='';", "het.textContent=q.h; fb.textContent=''; fb.className='q-fb';")
    t = one(t, "if(r===q.r){score++; fb.textContent=", "if(r===q.r){score++; fb.className='q-fb ok'; fb.textContent=")
    t = one(t, "else{b.classList.add('wrong'); fb.textContent=", "else{b.classList.add('wrong'); fb.className='q-fb ng'; fb.textContent=")
    k = t.index('<script>\n(function(){\nvar D=JSON.parse')
    t = t[:k] + '<script>\n' + js + '</script>\n' + t[k:]
    return t

def main(base, out):
    for name in ('sahidic', 'bohairic'):
        t = open(os.path.join(base, name + '.html'), encoding='utf-8').read()
        if name == 'sahidic':
            t, st = kana_sahidic(t); print(name, 'kana units', st['units'], 'changed', st['changed'], 'data', st['data'], 'problems', st['problems'])
        else:
            t, n = kana_bohairic(t); print(name, 'kana fixes', n)
        t = layer(t)
        open(os.path.join(out, name + '.html'), 'w', encoding='utf-8').write(t)
        print(name, len(t))

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
