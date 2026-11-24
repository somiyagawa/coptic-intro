# -*- coding: utf-8 -*-
"""ビルド済みのページ（コミット 2003160 の sahidic.html / bohairic.html）に、表示の改良を重ねる。

    python3 tools/restyle.py BASE_DIR OUT_DIR

BASE_DIR には改良前のページを置く（git show 2003160:sahidic.html > BASE_DIR/sahidic.html など）。
同じ入力からは同じ出力ができる。重ねる内容：
  - tools/rs.css   読みやすさの層（文字の大きさ、例文・講読本文・クイズの体裁）
  - tools/rs.js    課を開いたときの DOM の組み直し（例文ブロック、節ごとの訳、語の分析）
  - tools/kana_s.py サイード方言のカタカナ（重ね書きの母音、ⲃ、ⲟⲟⲩ）
"""
import re, json, sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kana_s, ang, add2

UNIT = re.compile(r'(<span class="rt" aria-hidden="true"><span class="rl">.*?</span><span class="rk">)(.*?)(</span></span><span class="rw">)(.*?)(</span></span>)', re.S)

def one(t, a, b, n=1):
    assert t.count(a) == n, (t.count(a), a[:70])
    return t.replace(a, b)

def word_of(rw):
    m = re.search(r'<span class="w0">(.*?)</span>', rw)
    return re.sub(r'<[^>]+>', '', m.group(1) if m else rw)

RK = re.compile(r'(<span class="rk">)(.*?)(</span></span><span class="rw">)', re.S)
COPT = re.compile('[\u2c80-\u2cff\u03e2-\u03ef][\u2c80-\u2cff\u03e2-\u03ef\u0300-\u036f\ufe24-\ufe26⸗]*')

W1 = re.compile(r'<span class="w0">[^<]*</span><span class="w1">([^<]*)</span>')

def regloss(t, w0, old_w1, new_w1, gl, gp=None, nodot=False, after=None, count=None):
    """グロスの付いた語（w0）のうち、区切りが old_w1 のものの区切りとグロスを付け直す。after は直後に続く文字列の条件"""
    unit = re.compile(r'(<span class="rb g[^"]*"><span class="rbi"><span class="rt" aria-hidden="true"><span class="rl">[^<]*</span><span class="rk">)((?:[^<]|<i class="kc">[^<]*</i>)*)'
                      r'(</span></span><span class="rw"><span class="w0">' + re.escape(w0) + r'</span><span class="w1">)' + re.escape(old_w1) +
                      r'(</span></span></span>)<span class="gl">(?:[^<]|<i class="sc">[^<]*</i>)*</span>(?:<span class="gp">[^<]*</span>)?(</span>)' + (r'(?=' + after + ')' if after else ''))
    def f(m):
        k = m.group(2).replace('・', '') if nodot else m.group(2)   # 一語になるならカナの中黒も外す
        return m.group(1) + k + m.group(3) + new_w1 + m.group(4) + '<span class="gl">' + gl + '</span>' + ('<span class="gp">' + gp + '</span>' if gp else '') + m.group(5)
    t, k = unit.subn(f, t)
    assert count is None or k == count, (w0, k)
    return t
def kana_sahidic(t):
    stat = {'units': 0, 'changed': 0, 'problems': []}
    def f(m):
        w = COPT.search(t, m.end(), m.end() + 1500); stat['units'] += 1
        if not w: stat['problems'].append(('noword', m.group(2))); return m.group(0)
        w = w.group(0); sg = W1.match(t, m.end())
        k2, st = kana_s.patch(w, m.group(2), sg.group(1) if sg else None)
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
    seg = seg[:k2] + '「オウ」' + seg[k2 + len('「オーウ」'):]
    seg += ' ' + C('ⲟⲟⲩ') + ' は ' + C('ⲟ') + ' と ' + C('ⲟⲩ') + '（w）の組み合わせなので、重ね書きの母音とは扱わず「オウ」と書きます（' + C('ⲙⲟⲟⲩ') + ' モウ「水」、' + C('ϩⲟⲟⲩ') + ' ホウ「日」）。'
    t = t[:i] + seg + t[j:]
    # 縮約した不定冠詞 ⲩ-（ⲉ-ⲩ-ⲣⲱⲙⲉ エ-ウ-ローメ）と、ⲉ の後で ⲩ と書く ⲟⲩ の読み（ウ）
    RB = lambda lat, kana, w: '<span class="rb"><span class="rt" aria-hidden="true"><span class="rl">%s</span><span class="rk">%s</span></span><span class="rw">%s</span></span>' % (lat, kana, w)
    t = one(t, RB('urôme', 'イローメ', 'ⲩⲣⲱⲙⲉ'), RB('u', 'ウ', 'ⲩ') + '-' + RB('rôme', 'ローメ', 'ⲣⲱⲙⲉ'))
    t = one(t, RB('unoute', 'イヌーテ', 'ⲩⲛⲟⲩⲧⲉ'), RB('u', 'ウ', 'ⲩ') + '-' + RB('noute', 'ヌーテ', 'ⲛⲟⲩⲧⲉ'))
    t = one(t, RB('ušê', 'イシェー', 'ⲩϣⲏ'), RB('ušê', 'ウシェー', 'ⲩϣⲏ'))
    t = one(t, RB('uən', 'イエン', 'ⲩⲛ̄'), RB('uən', 'ウエン', 'ⲩⲛ̄'), 16)
    # 解答の中の ϫⲟⲟⲩ（ϫⲟⲟ⸗ⲩ「それらを言う」）は語幹の重ね書き＋⸗ⲩ。ϫⲟⲟⲩ「送る」（ジョウ）と区別する
    # 一語の ⲟⲩⲇⲉ が ⲟⲩ-ⲇⲉ と区切られていた／ⲛ̄ϩⲏⲧ「私の中に」が「の-心」と分析されていた
    t = regloss(t, 'ⲟⲩⲇⲉ', 'ⲟⲩ-ⲇⲉ', 'ⲟⲩⲇⲉ', '〜もない', nodot=True, count=5)
    t = regloss(t, 'ⲛ̄ϩⲏⲧ', 'ⲛ̄-ϩⲏⲧ', 'ⲛ̄ϩⲏⲧ', '中に=1<i class="sc">sg</i>', '中に・私', nodot=True, after='</span>「私の中に」', count=1)
    # ⲛⲁⲩ「見る」が ⲛⲁ⸗ⲩ「彼らに」と分析されていた箇所（語彙の提示・練習・図・命令形の表・解答）を直す
    bad = ('<span class="rw"><span class="w0">ⲛⲁⲩ</span><span class="w1">ⲛⲁ⸗ⲩ</span></span></span>'
           '<span class="gl"><i class="sc">dat</i>=3<i class="sc">pl</i></span><span class="gp">に・彼ら</span></span>')
    good = '<span class="rw"><span class="w0">ⲛⲁⲩ</span><span class="w1">ⲛⲁⲩ</span></span></span><span class="gl">見る</span></span>'
    see = re.compile(re.escape(bad) + r'(?=</span>「見る」|</span></td>\n<td>nau</td>|</span> を完了形で全人称に活用せよ|</span></span><small>見る</small>'
                     r'|</span></span><span class="w1"><span class="copt"|</span></span></span></span><span class="gl">見る</span>'
                     r'|</span></td>\n<td>(?:(?!</tr>).){0,900}見なさい)', re.S)
    t, k = see.subn(good, t); assert k == 9, k
    pat = re.compile(r'((?:<span class="rl">čoou</span><span class="rk">ジョウ</span>.{0,160}?){1,2})(?=ϫⲟⲟⲩ</span>(?:</span>)+ の ⸗)', re.S)
    t, k = pat.subn(lambda m: m.group(1).replace('ジョウ', 'ジョオウ'), t); assert k == 2, k
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
            '<li>説明文の中のコプト語には、上にカナの読みだけを小さく添えています。点線の下線つきの語は、押すと分析（区切り・転写・グロス・略号の意味）が出ます。</li>'
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
    # 説明文の中のルビ（既定はカナだけ）／文字の大きさの既定と上限
    a = '<div class="setrow"><label for="st-seg">'
    t = one(t, a, '<div class="setrow"><label for="st-prose">説明文の中のルビ</label><select id="st-prose"><option value="kana">カナだけ</option><option value="both">転写とカナ</option></select></div>\n      ' + a)
    t = one(t, '<input type="range" id="st-fs" min="14" max="22" step="1">', '<input type="range" id="st-fs" min="14" max="24" step="1">')
    t = one(t, "best:{},last:null,fs:17};", "best:{},last:null,fs:18};")
    t = one(t, "var DEF={skin:'parch',gl:true,gp:true,seg:true,kana:true,latin:true,gloss:'all',tr:'show',fs:17,cs:'1',rs:'1'};",
            "var DEF={skin:'papyrus',gl:true,gp:true,seg:true,kana:true,latin:true,gloss:'all',tr:'show',fs:18,cs:'1',rs:'1',prose:'kana'};")
    t = one(t, "if(S.fs===16) S.fs=17;", "if(S.fs===16) S.fs=17;\nif(S.rsv!==3){ if(S.fs===17) S.fs=18; S.rsv=3 }")
    # 本体スクリプトへの差し込み
    t = one(t, "function save(){try{localStorage.setItem(KEY,JSON.stringify(S))}catch(e){}}",
            "function save(){try{localStorage.setItem(KEY,JSON.stringify(S))}catch(e){}}\nwindow.__rs={S:S,apply:function(){applySet()}};")
    t = one(t, "if(byId[id]){dress($(id));", "if(byId[id]){dress($(id)); if(window.__rsEnh) window.__rsEnh($(id));")
    t = one(t, "R.setAttribute('data-gloss',S.gloss);", "R.setAttribute('data-gloss',S.gloss==='all'?'ex':S.gloss==='every'?'all':S.gloss);")
    t = one(t, "$('st-rs').value=S.rs; save();", "$('st-rs').value=S.rs; save(); if(window.__rsSync) window.__rsSync();")
    t = one(t, "het.textContent=q.h; fb.textContent='';", "het.textContent=q.h; fb.textContent=''; fb.className='q-fb';")
    t = one(t, "if(r===q.r){score++; fb.textContent=", "if(r===q.r){score++; fb.className='q-fb ok'; fb.textContent=")
    t = one(t, "else{b.classList.add('wrong'); fb.textContent=", "else{b.classList.add('wrong'); fb.className='q-fb ng'; fb.textContent=")
    # 上の帯の題：狭い画面で折り返す位置を決めておく
    for old, new in (('基礎コプト語サイード方言文法入門', '基礎コプト語<wbr>サイード方言<wbr>文法入門'), ('コプト語教会ボハイラ方言入門', 'コプト語教会<wbr>ボハイラ方言<wbr>入門')):
        b = 'id="home-btn" type="button">%s</button>' % old
        if b in t: t = one(t, b, 'id="home-btn" type="button">%s</button>' % new)
    k = t.index('<script>\n(function(){\nvar D=JSON.parse')
    t = t[:k] + '<script>\n' + js + '</script>\n' + t[k:]
    return t

# 活用形の名前：ローマ数字（現在I・完了II・未来III）をやめ、第一現在・第二完了・第三未来と書く
NUM = {'I': '第一', 'II': '第二', 'III': '第三'}
TENSE = re.compile(r'(現在|未来|完了)(III|II|I)(?![A-Za-z])')
def terms(t):
    i = t.index('<header class="top"'); head, t = t[:i], t[i:]
    t = one(t, '「現在I」「完了I」の I は、転換詞の付かない基本の形を指します。II は第二時制（下の「転換」）を指します。未来III だけは別の活用で、I・II とは形の上のつながりがありません。',
            '「第一現在」「第一完了」の「第一」は、転換詞の付かない基本の形を指します。「第二」は第二時制（下の「転換」）を指します。第三未来だけは別の活用で、第一・第二とは形の上のつながりがありません。文法書によっては「現在I」「完了II」「未来III」のようにローマ数字で書きます。')
    t = one(t, 'I と II の番号を付けました。II の形の働きは長くわかりませんでした。ポロツキーが1944年の研究で、II の形は、',
            '第一・第二（I・II）の番号を付けました。第二の形の働きは長くわかりませんでした。ポロツキーが1944年の研究で、第二の形は、')
    keep = '「現在I」「完了II」「未来III」のようにローマ数字で書きます。'
    a, b = t.split(keep)
    n = len(TENSE.findall(a)) + len(TENSE.findall(b))
    f = lambda m: NUM[m.group(2)] + m.group(1)
    t = TENSE.sub(f, a) + keep + TENSE.sub(f, b)
    assert not re.search(r'(現在|未来|完了)\s?[ⅠⅡⅢ]', t)
    return head + t, n

def main(base, out):
    for name in ('sahidic', 'bohairic'):
        t = open(os.path.join(base, name + '.html'), encoding='utf-8').read()
        if name == 'sahidic':
            t, st = kana_sahidic(t); print(name, 'kana units', st['units'], 'changed', st['changed'], 'data', st['data'], 'problems', st['problems'])
        else:
            t, n = kana_bohairic(t); print(name, 'kana fixes', n)
            # 一語の ⲟⲩⲇⲉ が ⲟⲩ-ⲇⲉ と区切られていた／名詞の ϯ-ⲥ̀ⲃⲱ「知恵」が「与える-教え」と分析されていた
            t = regloss(t, 'ⲟⲩⲇⲉ', 'ⲟⲩ-ⲇⲉ', 'ⲟⲩⲇⲉ', '〜もない', nodot=True, count=3)
            t = regloss(t, 'ϯⲥ̀ⲃⲱ', 'ϯ-ⲥ̀ⲃⲱ', 'ϯ-ⲥ̀ⲃⲱ', '<i class="sc">def</i>.<i class="sc">f</i>-教え', 'その-教え', after='</span>「知恵」', count=1)
        t, n = terms(t); print(name, 'tense names', n)
        # 「コースの構成」の表：文法編は28章ある（14章だったころの記述が残っていた）。付録の行も足す
        a = ('<td>文法1〜14</td>\n<td>項目別にまとめた参照用の文法（音と文字、名詞、冠詞、代名詞、数詞、前置詞、修飾、動詞の形、活用、'
             '文の型、否定と疑問、従属節、小辞、語形成）</td>\n</tr>')
        b = ('<td>文法1〜28</td>\n<td>項目別にまとめた参照用の文法。1〜14 は品詞と文の骨組み（音と文字、名詞、冠詞、代名詞、数詞、前置詞、修飾、'
             '動詞の形、活用、文の型、否定と疑問、従属節、小辞、語形成）、15〜28 は個別の主題（名詞文、分裂文と焦点、提示の文、引用、'
             '受け身と使役、比較、借用語、用語の解説、時・場所・数量の表現、呼びかけ、条件文、転移など）</td>\n</tr>\n'
             '<tr>\n<td>付録</td>\n<td>A〜F</td>\n<td>活用の早見表、練習問題解答、グロスの略号、例文の出典、統語論・意味論・語用論のまとめ、'
             '他の文法書との対応、参考文献</td>\n</tr>')
        assert t.count(a) == 1, (name, t.count(a)); t = t.replace(a, b)
        # 独立代名詞の短い形（ⲁⲛⲅ̄- の類）の説明を書き直す（tools/ang.py）
        t = ang.sahidic(t, regloss) if name == 'sahidic' else ang.bohairic(t)
        # Layton の文法書と照らして抜けていた項目を書き足す（tools/add2.py）
        t, ms, mb = add2.apply(t, 's' if name == 'sahidic' else 'b')
        if os.environ.get('RB_SHOW'):
            for lab, m in (('S', ms), ('B', mb)):
                print(name, lab, 'new readings', len(m)); print('  ' + ' / '.join('%s=%s=%s' % (k, v[0], v[1]) for k, v in m.items()))
        t = layer(t)
        open(os.path.join(out, name + '.html'), 'w', encoding='utf-8').write(t)
        print(name, len(t))

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
