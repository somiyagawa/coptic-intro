#!/usr/bin/env python3
"""書籍版（PDF）の本文を作る。

  node tools/book/dump.js sahidic.html s.json     ページを開いて組み直した後の本文を取り出す
  python3 tools/book/tex.py s.json sahidic out/   LuaLaTeX の原稿 out/sahidic.tex を書く
  （out/ に Antinoou.ttf を置いて lualatex を2〜3回）

ウェブ版と同じ決まりで組む：
  - 例文・講読本文は、転写・カナ・語形・略号のグロス・やさしいグロスを左そろえで積み、下に訳を置く
  - 説明文の中の語は、上にカナだけを置く（行送りは一定）
  - 表の中の語は、転写とカナを左そろえで積む（転写の列がある語彙表ではカナだけ）
"""
import math, json, os, re, sys, unicodedata
from bs4 import BeautifulSoup, NavigableString, Tag
from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- 文字の幅（表の列幅を決めるため）
class Metrics:
    def __init__(self, path):
        f = TTFont(path); self.cmap = f.getBestCmap(); self.hmtx = f['hmtx']; self.upm = f['head'].unitsPerEm
    def w(self, s, size):
        t = 0
        for ch in s:
            if unicodedata.combining(ch): continue
            g = self.cmap.get(ord(ch))
            t += (self.hmtx[g][0] if g else self.upm * .6)
        return t * size / self.upm
FONT_COPT = None; FONT_LAT = None
def load_fonts(antinoou):
    global FONT_COPT, FONT_LAT
    FONT_COPT = Metrics(antinoou)
    for p in ('/usr/share/fonts/truetype/gentiumplus/GentiumPlus-Regular.ttf',):
        if os.path.exists(p): FONT_LAT = Metrics(p)
    if FONT_LAT is None: FONT_LAT = FONT_COPT

def is_copt(ch):
    o = ord(ch); return 0x2c80 <= o <= 0x2cff or 0x3e2 <= o <= 0x3ef
def is_wide(ch):
    o = ord(ch)
    return (0x3000 <= o <= 0x9fff or 0xff00 <= o <= 0xffef or 0x2190 <= o <= 0x21ff or o in (0x2026, 0x2014, 0x2192, 0x25cb, 0x25cf, 0x00d7, 0x2260, 0x2205))

def text_w(s, fs, copt=False):
    """文字列の幅（pt）。fs は欧文の大きさ。和文は 0.96fs、コプト文字は 1.12fs の字として数える"""
    t = 0.0; prev = None
    for ch in s:
        if unicodedata.combining(ch): continue
        if is_copt(ch) or (copt and ch in '-⸗·.†'): t += FONT_COPT.w(ch, fs * 1.12); kind = 'c'
        elif is_wide(ch): t += fs * .96; kind = 'w'
        elif ch == ' ': t += fs * .3; kind = None
        else: t += FONT_LAT.w(ch, fs); kind = 'l'
        # 和文と欧文・コプト文字の間には四分アキが入る
        if prev and kind and prev != kind and 'w' in (prev, kind) and ch not in '（）「」、。・〜' : t += fs * .24
        prev = kind
    return t

# ---------------------------------------------------------------- LaTeX の文字
SPECIAL = {'\\': r'\textbackslash{}', '{': r'\{', '}': r'\}', '#': r'\#', '$': r'\$', '%': r'\%', '&': r'\&', '_': r'\_',
           '~': r'\textasciitilde{}', '^': r'\textasciicircum{}'}
COPT_RUN = re.compile('[\u2c80-\u2cff\u03e2-\u03ef][\u2c80-\u2cff\u03e2-\u03ef\u0300-\u036f\ufe24-\ufe26\u0483-\u0489⸗]*')
def esc(s):
    return ''.join(SPECIAL.get(c, c) for c in s)
def ws(s):
    return re.sub(r'\s+', ' ', s)
def plain(s):
    """ふつうの文字列。コプト文字の続きはコプト文字のフォントで組む"""
    s = ws(s); out = []; i = 0
    for m in COPT_RUN.finditer(s):
        out.append(plain_nc(s[i:m.start()])); out.append('{\\copfont ' + ctext(m.group(0)) + '}'); i = m.end()
    out.append(plain_nc(s[i:]))
    return ''.join(out)
def plain_nc(s):
    s = esc(s)
    s = s.replace('⸗', '{\\copfont\\cps{}}').replace('†', '{\\copfont\\dg{}}')
    s = re.sub(r'-(?=-)', '-{}', s)
    return s
def ctext(s):
    """コプト文字のフォントの中の文字列"""
    out = []
    for ch in ws(s):
        if ch == '⸗': out.append('\\cps{}')
        elif ch == '†': out.append('\\dg{}')
        elif is_wide(ch) and not is_copt(ch): out.append('\\jx{' + esc(ch) + '}')
        else: out.append(SPECIAL.get(ch, ch))
    return re.sub(r'-(?=-)', '-{}', ''.join(out))

def cls(e):
    return e.get('class') or [] if isinstance(e, Tag) else []
def has(e, c):
    return c in cls(e)

# ---------------------------------------------------------------- 語（ルビとグロス）
def kana_tex(rk):
    out = []
    for c in rk.children:
        if isinstance(c, NavigableString): out.append(esc(str(c)))
        elif has(c, 'kc'): out.append('\\kc{' + esc(c.get_text()) + '}')
        else: out.append(esc(c.get_text()))
    return ''.join(out)
def kana_w(rk, fs):
    t = 0.0
    for c in rk.children:
        if isinstance(c, NavigableString): t += len(str(c)) * fs
        else: t += len(c.get_text()) * fs * (.74 if has(c, 'kc') else 1)
    return t
def gloss_tex(g):
    if g is None: return ''
    out = []
    for c in g.children:
        if isinstance(c, NavigableString): out.append(plain(str(c)))
        elif has(c, 'sc'): out.append('\\gsc{' + esc(c.get_text().lower()) + '}')
        else: out.append(plain(c.get_text()))
    return ''.join(out)
def base_tex(rw):
    """語形（区切りを入れた形）。.w0（区切りなし）は読み飛ばす"""
    out = []; seg = rw.find(class_='w1') is not None
    def walk(n):
        for c in n.children:
            if isinstance(c, NavigableString): out.append(ctext(str(c)))
            elif has(c, 'w0') and seg: continue
            elif has(c, 'dg'): out.append('\\dg{}')
            elif c.name == 'small': out.append('\\jx{\\scriptsize ' + plain(c.get_text()) + '}')
            else: walk(c)
    walk(rw)
    return ''.join(out)
def base_str(rw):
    out = []; seg = rw.find(class_='w1') is not None
    def walk(n):
        for c in n.children:
            if isinstance(c, NavigableString): out.append(str(c))
            elif has(c, 'w0') and seg: continue
            else: walk(c)
    walk(rw)
    return ''.join(out)
def word(rb):
    """(語形, 転写, カナ, 略号グロス, やさしいグロス, 幅用の値)"""
    rt = rb.find(class_='rt'); rw = rb.find(class_='rw')
    rl = rt.find(class_='rl') if rt else None; rk = rt.find(class_='rk') if rt else None
    gl = rb.find(class_='gl'); gp = rb.find(class_='gp')
    return dict(base=base_tex(rw), lat=esc(rl.get_text()) if rl else '', kana=kana_tex(rk) if rk else '',
                gl=gloss_tex(gl), gp=gloss_tex(gp), rw=rw, rl=rl, rk=rk, glraw=gl.get_text() if gl else '', gpraw=gp.get_text() if gp else '')

class Ctx:
    def __init__(self, mode='prose', fs=10.0, kana_only=False, group=False):
        self.mode = mode; self.fs = fs; self.kana_only = kana_only; self.group = group
    def but(self, **k):
        c = Ctx(self.mode, self.fs, self.kana_only, self.group)
        for a, b in k.items(): setattr(c, a, b)
        return c

def word_tex(rb, ctx):
    w = word(rb)
    if ctx.mode == 'prose' or has(rb, 'ip'):
        if not w['kana']: return w['base']
        return ('\\prg' if ctx.group else '\\pr') + '{%s}{%s}' % (w['base'], w['kana'])
    if ctx.kana_only: return '\\rwk{%s}{%s}' % (w['base'], w['kana'])
    return '\\rw{%s}{%s}{%s}' % (w['base'], w['lat'], w['kana'])
def word_w(rb, ctx):
    w = word(rb); b = text_w(base_str(w['rw']), ctx.fs, True)
    if ctx.mode == 'prose' or has(rb, 'ip'):
        k = kana_w(w['rk'], 5.7) if w['rk'] else 0
        return max(b, k - (0 if ctx.group else 3))
    k = kana_w(w['rk'], 6.3) if w['rk'] else 0
    l = FONT_LAT.w(w['rl'].get_text(), 6.8) if (w['rl'] and not ctx.kana_only) else 0
    return max(b, k, l)

# ---------------------------------------------------------------- 行内の要素
IGX = object()
def copt_span(span, ctx):
    """.copt の中身（説明文・表・図）。コプト文字のフォントに入れて返す"""
    out = []
    def walk(n, c):
        for ch in n.children:
            if isinstance(ch, NavigableString): out.append(ctext(str(ch)))
            elif has(ch, 'rb'): out.append(word_tex(ch, c))
            elif has(ch, 'bg'):
                out.append('\\mbox{'); walk(ch, c.but(group=True)); out.append('}')
            elif has(ch, 'dg'): out.append('\\dg{}')
            elif has(ch, 'lb'): out.append('\\\\ ')
            elif has(ch, 'copt'): walk(ch, c)
            else: walk(ch, c)
    walk(span, ctx)
    s = ''.join(out)
    return '{\\copfont ' + s + '}' if s.strip() else ''
def copt_w(span, ctx):
    """.copt の幅（一行に置いたとき）と、切れない単位の最大幅"""
    tot = [0.0]; unit = [0.0]; cur = [0.0]
    def add(w, brk=False):
        tot[0] += w
        if brk: unit[0] = max(unit[0], cur[0]); cur[0] = 0
        else: cur[0] += w
    def walk(n, c):
        for ch in n.children:
            if isinstance(ch, NavigableString):
                for part in re.split(r'(\s+)', ws(str(ch))):
                    if not part: continue
                    if part.isspace(): add(c.fs * .3, True)
                    else: add(text_w(part, c.fs, True))
            elif has(ch, 'rb'): add(word_w(ch, c) + (0 if c.group or c.mode == 'prose' or has(ch, 'ip') else 0))
            elif has(ch, 'bg'): walk(ch, c.but(group=True))
            else: walk(ch, c)
    walk(span, ctx); unit[0] = max(unit[0], cur[0])
    return tot[0], unit[0]

def inline(node, ctx, parts=None):
    """行内の中身を LaTeX に。parts を渡すと、取り出した例（.igx）のところで区切って積む"""
    out = []
    def flush():
        if parts is not None:
            parts.append(('t', ''.join(out))); out.clear()
    def walk(n):
        for c in n.children:
            if isinstance(c, NavigableString): out.append(plain(str(c))); continue
            k = cls(c)
            if 'copt' in k: out.append(copt_span(c, ctx))
            elif 'igx' in k:
                if parts is None: out.append(igx_inline(c, ctx))
                else: flush(); parts.append(('x', c))
            elif 'ex-n' in k: continue
            elif 'dg' in k: out.append('{\\copfont\\dg{}}')
            elif 'sc' in k: out.append('\\gsc{' + esc(c.get_text().lower()) + '}')
            elif 'kc' in k: out.append('\\kc{' + esc(c.get_text()) + '}')
            elif c.name in ('strong', 'b'): out.append('\\textbf{\\sffamily '); walk(c); out.append('}')
            elif c.name in ('em', 'i'): out.append('\\emph{'); walk(c); out.append('}')
            elif c.name == 'small': out.append('{\\footnotesize '); walk(c); out.append('}')
            elif c.name == 'sup': out.append('\\textsuperscript{'); walk(c); out.append('}')
            elif c.name == 'sub': out.append('\\textsubscript{'); walk(c); out.append('}')
            elif c.name == 'br': out.append('\\\\ ')
            elif c.name in ('ul', 'ol', 'table', 'div', 'blockquote', 'p'):
                if parts is None: out.append(' ' + blocks([c], ctx) + ' ')
                else: flush(); parts.append(('b', c))
            elif c.name in ('textarea', 'button'): continue
            else: walk(c)
    walk(node)
    if parts is not None:
        flush(); return None
    return ''.join(out).strip()

def inline_w(node, ctx):
    """行内の中身の幅（一行に置いたとき）と、切れない単位の最大幅"""
    tot = 0.0; unit = 0.0
    for c in node.children:
        if isinstance(c, NavigableString):
            s = ws(str(c))
            tot += text_w(s, ctx.fs)
            for tok in re.split(r'[\s]+', s):
                # 和文は一字ごとに切れる。欧文の語は切れない
                lat = re.findall(r'[^\u3000-\u9fff\uff00-\uffef\s]+', tok)
                for l in lat: unit = max(unit, text_w(l, ctx.fs))
                if re.search(r'[\u3000-\u9fff\uff00-\uffef]', tok): unit = max(unit, ctx.fs * 2)
        elif has(c, 'copt'):
            a, b = copt_w(c, ctx); tot += a; unit = max(unit, b)
        elif c.name in ('textarea', 'button') or has(c, 'ex-n'): continue
        else:
            a, b = inline_w(c, ctx); tot += a; unit = max(unit, b)
    return tot, unit

# ---------------------------------------------------------------- 例文・講読本文の行
def disp_words(container):
    """例文の一行を、語（辞書）と区切り（'gap'、'join'、'br'）の並びにする"""
    seq = []
    def walk(n, joined):
        for c in n.children:
            if isinstance(c, NavigableString):
                s = str(c)
                if not s.strip():
                    if s and not joined: seq.append('gap')
                    continue
                for part in re.split(r'(\s+)', s):
                    if not part: continue
                    if part.isspace():
                        if not joined: seq.append('gap')
                    else: seq.append(dict(bare=ctext(part)))
            elif has(c, 'rb'): seq.append(word(c))
            elif has(c, 'bg'): walk(c, True)
            elif has(c, 'lb'): seq.append('br')
            elif has(c, 'dg'): seq.append(dict(bare='\\dg{}'))
            else: walk(c, joined)
    walk(container, False)
    # 行頭・行末・連続する区切りを整理
    out = []
    for x in seq:
        if x == 'gap' and (not out or out[-1] in ('gap', 'br')): continue
        out.append(x)
    while out and out[-1] in ('gap', 'br'): out.pop()
    return out
def disp_tex(seq, lead, rows):
    """rows: 2 = グロス二段、1 = 略号のグロスだけ、0 = グロスなし"""
    out = [lead]
    for x in seq:
        if x == 'gap': out.append('\\gs ')
        elif x == 'br': out.append('\\hfil\\break ')
        elif 'bare' in x:
            b = x['bare']
            out.append({2: '\\gw{%s}{}{}{}{}', 1: '\\gv{%s}{}{}{}', 0: '\\gu{%s}{}{}'}[rows] % b)
        else:
            if rows == 2: out.append('\\gw{%s}{%s}{%s}{%s}{%s}' % (x['base'], x['lat'], x['kana'], x['gl'], x['gp']))
            elif rows == 1: out.append('\\gv{%s}{%s}{%s}{%s}' % (x['base'], x['lat'], x['kana'], x['gl']))
            else: out.append('\\gu{%s}{%s}{%s}' % (x['base'], x['lat'], x['kana']))
    return ''.join(out)
def rows_of(seqs):
    gl = any(isinstance(x, dict) and x.get('glraw', '').strip() for s in seqs for x in s)
    gp = any(isinstance(x, dict) and x.get('gpraw', '').strip() for s in seqs for x in s)
    return 2 if gp else 1 if gl else 0

def example(line_el, tr_el, src_el, ctx, num=None, env='ex'):
    seq = disp_words(line_el); rows = rows_of([seq])
    lead = '\\exno{%s}' % num if num is not None else ''
    tr = inline(tr_el, ctx.but(mode='prose')) if tr_el is not None else ''
    src = inline(src_el, ctx.but(mode='prose')) if src_el is not None else ''
    src = re.sub(r'^\{\\footnotesize (.*)\}$', r'\1', src, flags=re.S)
    s = '\\begin{%s}\\begin{igl}%s\\end{igl}' % (env, disp_tex(seq, lead, rows))
    if tr or src: s += '\\ext{%s}{%s}' % (tr, src)
    return s + '\\end{%s}\n' % env
def igx_inline(el, ctx):
    return example(el.find(class_='igx-l'), el.find(class_='igx-t'), el.find(class_='igx-s'), ctx, None, 'exi')

def reading(bq, ctx):
    out = []
    for vs in bq.find_all('div', class_='vs', recursive=False):
        vn = vs.find(class_='vn'); body = vs.find(class_='vbody')
        lines = [disp_words(vl) for vl in body.find_all('div', class_='vl', recursive=False)]
        rows = rows_of(lines)
        out.append('\\begin{rdv}')
        for i, seq in enumerate(lines):
            lead = '\\vsno{%s}' % esc(vn.get_text().strip()) if (vn is not None and i == 0) else ''
            out.append('\\begin{igl}%s\\end{igl}' % disp_tex(seq, lead, rows))
        for vt in body.find_all('p', class_='vt', recursive=False):
            out.append('\\vtr{%s}' % inline(vt, ctx.but(mode='prose')))
        out.append('\\end{rdv}\n')
    if not out:   # 節に分かれていない本文
        seq = disp_words(bq); out.append('\\begin{rdv}\\begin{igl}%s\\end{igl}\\end{rdv}\n' % disp_tex(seq, '', rows_of([seq])))
    return ''.join(out)

# ---------------------------------------------------------------- 表
LW = 345.6          # 本文の幅（36字 × 9.6pt）
SIZES = [('\\small', 9.0), ('\\footnotesize', 8.0), ('\\scriptsize', 7.0)]
def table(tb, ctx, avail=LW, long=True):
    table.info = None
    head = [tr for tr in tb.select('thead > tr')] ; body = [tr for tr in tb.select('tbody > tr')]
    if not body: body = [tr for tr in tb.find_all('tr') if tr not in head]
    hastr = has(tb, 'has-tr')
    ncol = max(len(tr.find_all(['td', 'th'], recursive=False)) for tr in head + body)
    def cells(tr): return tr.find_all(['td', 'th'], recursive=False)
    def cctx(j, td, fs):
        prose = has(td, 'lh')
        return Ctx('prose' if prose else 'cell', fs, kana_only=(hastr and j == 0))
    for cmd, fs in SIZES:
        sep = 8.0
        nat = [0.0] * ncol; mn = [0.0] * ncol
        for tr in head + body:
            for j, td in enumerate(cells(tr)):
                a, b = inline_w(td, cctx(j, td, fs))
                if td.name == 'th' or has(td, 'rh'): a *= 1.06; b *= 1.06
                a += 2.5; b += 2.5
                nat[j] = max(nat[j], a)
                mn[j] = max(mn[j], a if (has(td, 'nw') or td.name == 'th') else min(a, max(b, fs * 4.2)))
        room = avail - sep * (ncol - 1)
        if sum(nat) <= room:
            wid = list(nat)
            # 余りは広い列に少し配る（詰まりすぎないように）
            extra = min(room - sum(wid), 10.0 * ncol)
            for j in range(ncol): wid[j] += extra / ncol
            break
        if sum(mn) <= room:
            flex = [max(nat[j] - mn[j], 0) for j in range(ncol)]; tot = sum(flex) or 1
            wid = [mn[j] + (room - sum(mn)) * flex[j] / tot for j in range(ncol)]
            break
    else:
        tot = sum(mn); wid = [m * room / tot for m in mn]
    spec = '@{}' + ''.join('>{\\raggedright\\arraybackslash}p{%.1fpt}' % w for w in wid) + '@{}'
    def row(tr, hd):
        out = []
        cs = cells(tr)
        for j in range(ncol):
            if j >= len(cs): out.append(''); continue
            td = cs[j]; t = inline(td, cctx(j, td, fs))
            pr = '\\pr' in t
            if hd or td.name == 'th' or has(td, 'rh'): t = '\\thd{' + t + '}' if t else ''
            if pr: t = '\\prs ' + t                    # カナが上に載る分、一行目の高さと行送りを広げる
            out.append(t)
        return ' & '.join(out)
    env = 'longtable' if long else 'tabular'
    out = ['{' + cmd + '\\tblskip\\setlength\\tblw{%.1fpt}\n\\begin{%s}{%s}\\toprule\n' % (sum(wid) + sep * (ncol - 1), env, spec)]
    if head:
        out.append('\\\\\n'.join(row(tr, True) for tr in head) + '\\\\\\midrule' + ('\\endhead' if long else '') + '\n')
    # 行数の見積もり（各行で、いちばん折り返しの多いセルの行数）。短い表はページをまたがせない
    est = 0; ht = 22.0 * max(len(head), 1) + 16
    rs = [row(tr, False) for tr in body]; n = len(rs)
    for tr, r in zip(body, rs):
        ln = max([1] + [math.ceil(inline_w(td, cctx(j, td, fs))[0] / max(wid[j], 1)) for j, td in enumerate(cells(tr)) if j < ncol])
        est += ln
        # 行の高さの見積もり：転写・カナ・語形を積んだ語は約29pt、カナ付きの説明文は一行17pt、ふつうの文は一行14pt
        ht += max(29.0 if '\\rw{' in r else 23.0 if '\\rwk{' in r else 0.0, ln * (17.0 if '\\pr' in r else 14.0) * fs / 9.0) + 5.2
    keep = long and len(body) <= 9 and est <= 16
    table.info = {'keep': keep, 'h': ht * 1.06}
    for i, r in enumerate(rs[:-1]):         # 長い表でも、先頭と末尾で一行だけが別のページに残らないようにする
        out.append(r + ('\\\\\\rowsepk\n' if keep or i == 0 or i == n - 2 else '\\\\\\rowsep\n'))
    if rs: out.append(rs[-1])
    out.append('\\\\*\n\\bottomrule\\end{%s}}\n' % env)
    s = ''.join(out)
    if not long: s = '\\par\\smallskip\\noindent ' + s + '\\par\\smallskip\n'
    return s

# ---------------------------------------------------------------- 図
BLK = {'v': 'blkv', 'o': 'blko', 'b': 'blkb', 's': 'blks', 'a': 'blka', 'st': 'blkst'}
def preglue(root):
    """図の中：語のすぐ後ろの - と ⸗ を語の箱に入れる（ウェブ版が図の外でしているのと同じ）"""
    for c in root.find_all(class_='copt'):
        nx = c.next_sibling
        kids = [k for k in c.children if not (isinstance(k, NavigableString) and not str(k).strip())]
        if not kids or not isinstance(kids[-1], Tag) or not has(kids[-1], 'rb'): continue
        if isinstance(nx, NavigableString):
            m = re.match(r'[-⸗]+', str(nx))
            if m:
                rw = kids[-1].find(class_='rw'); tg = rw.find(class_='w1') or rw
                tg.append(m.group(0)); nx.replace_with(str(nx)[m.end():])
def figure(fig, ctx):
    preglue(fig)
    t = fig.find(class_='fig-t', recursive=False)
    title = inline(t, ctx) if t is not None else ''
    c = ctx.but(mode='cell', fs=10.0)
    rows = []
    for fr in fig.find_all('div', class_='frow', recursive=False):
        lab = fr.find(class_='flab'); blks = fr.find(class_='fblks'); res = fr.find(class_='fres')
        l1 = ''; l2 = ''
        if lab is not None:
            sm = lab.find('small')
            l2 = inline(sm, ctx) if sm is not None else ''
            tmp = BeautifulSoup(lab.decode(), 'lxml').find(class_='flab')
            for s_ in tmp.find_all('small'): s_.decompose()
            l1 = inline(tmp, ctx)
        cards = []; cw = 0.0
        if blks is not None:
            strut = '\\fgs ' if blks.find(class_='rt') else ''
            for ch in blks.children:
                if isinstance(ch, NavigableString):
                    if str(ch).strip(): cards.append(plain(str(ch))); cw += text_w(str(ch).strip(), 10)
                    continue
                k = cls(ch)
                if 'blk' in k:
                    style = next((BLK[x] for x in k if x in BLK), 'blkn')
                    bc = ch.find(class_='bc'); sm = ch.find('small', recursive=False)
                    body = inline(bc, c) if bc is not None else ''
                    note = inline(sm, ctx) if sm is not None else ''
                    note = re.sub(r'^\{\\footnotesize (.*)\}$', r'\1', note, flags=re.S)
                    cards.append('\\blk{%s}{%s%s}{%s}' % (style, strut, body, note))
                    w1 = inline_w(bc, c)[0] if bc is not None else 0
                    w2 = text_w(sm.get_text(), 6.4) if sm is not None else 0
                    cw += max(w1, w2) + 9.4 + 3
                elif 'gapx' in k: cards.append('\\enskip…\\enskip '); cw += 20
                else: cards.append(inline(ch, c)); cw += inline_w(ch, c)[0] + 3
        r = inline(res, c) if res is not None else ''
        rows.append((l1, l2, ' '.join(cards), r, cw))
    inner = LW - 22.9          # 枠の線（0.6pt）と左右の余白（8pt＋tcolorbox の boxsep 1mm）を引いた幅
    wl = min(max((text_w(re.sub(r'\\[a-z]+|[{}]', '', a), 9.0) * 1.08 for a, b, c_, d, e in rows), default=40) + 4, inner * .24)
    wl = max(wl, 42)
    wc = min(max((e for a, b, c_, d, e in rows), default=0) + 2, inner * .56)
    wr = inner - wl - wc - 16
    out = ['\\begin{figbox}{%s}\n' % title]
    if rows:
        three = any(r[3] for r in rows)
        if three: spec = '@{}p{%.1fpt}p{%.1fpt}p{%.1fpt}@{}' % (wl, wc, wr)
        else:
            wc = inner - wl - 8; spec = '@{}p{%.1fpt}p{%.1fpt}@{}' % (wl, wc)
        out.append('{\\setlength\\tabcolsep{4pt}\\renewcommand\\arraystretch{1}\\noindent\\begin{tabular}{%s}\n' % spec)
        lines = []
        for l1, l2, cards, r, _ in rows:
            cell1 = '\\flab{%s}{%s}' % (l1, l2)
            cell2 = '{\\raggedright\\lineskip=4pt ' + cards + '\\par}'
            cell3 = '{\\raggedright\\small ' + ('$\\rightarrow$\\ ' + r if r else '') + '\\par}'
            lines.append(' & '.join([cell1, cell2, cell3] if three else [cell1, cell2]))
        out.append(('\\\\[3pt]\\arrayrulecolor{rule!70}\\specialrule{.3pt}{2pt}{5pt}\\arrayrulecolor{black}\n').join(lines))
        out.append('\\\\\n\\end{tabular}}\n')
    for capn in fig.find_all('div', class_='fcap', recursive=False):
        out.append('\\figcap{%s}\n' % inline(capn, ctx))
    # 図の中に行以外のもの（段落など）があればそのまま
    for ch in fig.find_all(recursive=False):
        if not (set(cls(ch)) & {'fig-t', 'frow', 'fcap'}): out.append(blocks([ch], ctx))
    out.append('\\end{figbox}\n')
    return ''.join(out)

# ---------------------------------------------------------------- 段落と箇条書き
def para(node, ctx, lead='', first_noindent=False):
    """段落。途中に取り出した例（.igx）や箇条書きがあれば、そこで段落を分ける"""
    parts = []; inline(node, ctx, parts)
    out = []; first = True; after_block = False
    for kind, v in parts:
        if kind == 't':
            t = v.strip()
            if first: t = lead + t
            if not t: continue
            t = re.sub(r'^[、。]\s*', '', t) if after_block and re.match(r'^[、。]\s*$', t) else t
            if not t: continue
            out.append(('\\noindent ' if (after_block or (first and first_noindent)) else '') + t + '\\par\n')
            first = False; after_block = False
        elif kind == 'x':
            out.append(igx_inline(v, ctx)); after_block = True; first = False
        else:
            out.append(blocks([v], ctx)); after_block = True; first = False
    return ''.join(out)

def li_items(lst, ctx):
    """箇条書きの中身。例文（li.igt）は番号つきの例、見出しつき（li.pt）は帯つきの囲みにする"""
    out = []; n = 0; open_list = False
    env = 'enumerate' if lst.name == 'ol' else 'itemize'
    def close():
        nonlocal open_list
        if open_list: out.append('\\end{%s}\n' % env); open_list = False
    for li in lst.find_all('li', recursive=False):
        k = cls(li)
        if 'igt' in k:
            close(); n += 1
            b = li.find(class_='igt-b')
            out.append(example(b.find(class_='igt-l'), b.find(class_='igt-t'), b.find(class_='igt-s'), ctx, n))
        elif 'pt' in k:
            close()
            h = li.find(class_='pt-h', recursive=False); b = li.find(class_='pt-b', recursive=False)
            ht = inline(h, ctx) if h is not None else ''
            if '\\pr' in ht: ht = '\\prs ' + ht          # 見出しのコプト語にカナが載るとき、上の箱とぶつからないようにする
            out.append('\\begin{ptbox}\\pth{%s}%s\\end{ptbox}\n' % (ht, para(b, ctx) if b is not None else ''))
        else:
            if not open_list: out.append('\\begin{%s}\n' % env); open_list = True
            body = para(li, ctx).strip()
            body = re.sub(r'\\par$', '', body)
            out.append('\\item ' + body + '\n')
    close()
    return ''.join(out)

def exercise(ex, ctx):
    q = ex.find(class_='ex-q'); n = q.find(class_='ex-n') if q is not None else None
    title = esc(n.get_text().strip()) if n is not None else '練習'
    return '\\begin{exbox}{%s}%s\\end{exbox}\n' % (title, para(q, ctx).strip() if q is not None else '')

def blocks(nodes, ctx):
    out = []
    nodes = [e for e in nodes if not (isinstance(e, NavigableString) and not str(e).strip())]
    skip = None
    for idx, e in enumerate(nodes):
        if e is skip: continue
        if isinstance(e, NavigableString):
            out.append(plain(str(e)) + '\\par\n')
            continue
        k = cls(e); nm = e.name
        if nm in ('h3', 'h4', 'h5'):
            # 見出しだけがページの下に残らないようにする（表や図が続くときは、その頭の数行分も確保する）
            nx = nodes[idx + 1] if idx + 1 < len(nodes) else None
            big = isinstance(nx, Tag) and (nx.name == 'table' or (nx.name == 'div' and set(cls(nx)) & {'tbl', 'fig'}))
            out.append('\\Needspace{%d\\baselineskip}' % (9 if big else 4)); need = len(out) - 1 if big else None
            out.append('\\%s*{%s}\n' % ('section' if nm == 'h3' else 'subsection', inline(e, ctx)))
            if need is not None:
                # 続く表がページをまたがない組み方（短い表）なら、見出しと表の全体が入る余地を確保する
                table.info = None; nxt = blocks([nx], ctx); inf = table.info
                if inf and inf['keep']: out[need] = '\\Needspace{%.0fpt}' % (inf['h'] + 44)
                out.append(nxt); skip = nx
        elif nm == 'p':
            if 'refp' in k: out.append('\\refp{%s}\n' % inline(e, ctx))
            elif 'trp' in k: out.append('\\vtr{%s}\n' % inline(e, ctx))
            elif set(k) & {'q-meta', 'sub', 'q-ask', 'q-fb'}: continue
            else: out.append(para(e, ctx))
        elif nm in ('ul', 'ol'): out.append(li_items(e, ctx))
        elif nm == 'table': out.append(table(e, ctx, long=not ctx.group))
        elif nm == 'blockquote': out.append(reading(e, ctx))
        elif nm == 'div':
            if 'tbl' in k:
                for tb in e.find_all('table', recursive=False): out.append(table(tb, ctx, long=not ctx.group))
            elif 'fig' in k: out.append(figure(e, ctx))
            elif 'ex' in k: out.append(exercise(e, ctx))
            elif set(k) & {'panel', 'ans', 'vbar', 'filters', 'opts'}: continue
            elif 'step' in k: out.append(step(e, ctx))
            else: out.append(blocks(list(e.children), ctx))
        elif nm in ('textarea', 'button', 'script', 'style'): continue
        else:
            t = inline(e, ctx)
            if t: out.append(t + '\\par\n')
    return ''.join(out)

def step(st, ctx):
    if st.find(class_='panel') is not None: return ''          # 確認クイズは本には入れない
    kids = [c for c in st.children if not (isinstance(c, NavigableString) and not str(c).strip())]
    if 'kp' in cls(st):
        h = st.find('h3', recursive=False)
        rest = [c for c in kids if c is not h]
        return '\\begin{kpbox}{%s}\n%s\\end{kpbox}\n' % (inline(h, ctx) if h is not None else '', blocks(rest, ctx.but(group=True)))
    return blocks(kids, ctx)

# ---------------------------------------------------------------- 本の構成
BOOK = {
 'sahidic': dict(sub='文字から聖書・トマス福音書の講読まで\\quad 全24課', titlebr='基礎コプト語\\\\[2mm]サイード方言文法入門',
    lead='コプト語の古典的な文語であるサイード方言を、文字から講読まで順に学ぶ入門書です。コプト語には、大学の授業で使われる発音のカタカナとラテン文字転写を付け、例文と講読本文には行間グロスを付けています。'),
 'bohairic': dict(sub='文字から聖書・典礼文の講読まで\\quad 全24課', titlebr='コプト語教会ボハイラ方言入門',
    lead='コプト正教会の典礼で今も用いられるボハイラ方言を、文字から講読まで順に学ぶ入門書です。コプト語には、教会発音のカタカナとラテン文字転写を付け、例文と講読本文には行間グロスを付けています。'),
}
SKIP = {'home', 'cards', 'quiz', 'search'}

def guide(home, ctx):
    """「例文の読み方」：ウェブ版ホームの「画面の見方」の例をもとに、本の凡例を作る"""
    g = home.find(class_='guide-ex')
    if g is None: return ''
    line = g.find(class_='igt-l'); tr = g.find(class_='igt-t')
    seq = disp_words(line)
    lab = seq[0] if seq and isinstance(seq[0], dict) else None
    rest = seq[1:] if lab else seq
    while rest and rest[0] == 'gap': rest = rest[1:]
    labbox = ('\\leavevmode\\vtop{\\offinterlineskip\\halign{#\\hfil\\cr\\vbox{\\offinterlineskip\\halign{#\\hfil\\cr'
              '{\\sffamily\\bfseries\\fontsize{6.4}{6.4}\\selectfont 転写}\\sL\\cr{\\sffamily\\bfseries\\fontsize{6.4}{6.4}\\selectfont カナ}\\sK\\cr\\noalign{\\vskip1pt}'
              '{\\sffamily\\bfseries\\fontsize{6.4}{6.4}\\selectfont 語形}{\\copx\\sB}\\cr}}\\cr\\noalign{\\vskip1.6pt}'
              '{\\sffamily\\bfseries\\fontsize{6.4}{6.4}\\selectfont 略号のグロス}\\sG\\cr{\\sffamily\\bfseries\\fontsize{6.4}{6.4}\\selectfont やさしいグロス}\\sG\\cr}}'
              '\\hskip 8pt{\\color{rule}\\vrule width .5pt height 26pt depth 22pt}\\hskip 8pt ')
    trt = ''
    if tr is not None:
        t2 = BeautifulSoup(tr.decode(), 'lxml').find(class_='igt-t')
        for b in t2.find_all('b'): b.decompose()
        trt = inline(t2, ctx)
    s = ['\\section*{この本の見方}\n\\begin{figbox}{例文の読み方}\n']
    s.append('{\\raggedright\\noindent ' + labbox + disp_tex(rest, '', 2) + '\\par}\n')
    s.append('\\vskip 3pt{\\noindent\\hskip 62pt{\\sffamily\\bfseries\\fontsize{6.6}{6.6}\\selectfont\\color{accent}訳}\\enskip ' + trt + '\\par}\n')
    s.append('\\end{figbox}\n\\begin{itemize}\n')
    s.append('\\item 例文と講読本文は、語ごとに、上から転写、カナ、語形（形態素をハイフンで区切った形）、略号のグロス、やさしい日本語のグロスの順に並べ、その下に訳を置きます。\n')
    s.append('\\item 説明文の中のコプト語には、上にカナの読みだけを添えます。表の中のコプト語には転写とカナを添えます（転写の列がある語彙表ではカナだけ）。\n')
    s.append('\\item グロスの略号の意味は付録Cにまとめてあります。\n')
    s.append('\\end{itemize}\n')
    return ''.join(s)

# ウェブ版の操作だけを説明している文（本では意味をなさない）
WEBONLY = re.compile('表示設定で[^。<]*。')
def build(data, name):
    ctx = Ctx('prose', 10.0)
    sec = {s['id']: s for s in data['sections']}
    home = BeautifulSoup(sec['home']['html'], 'lxml')
    eb = home.find(class_='eyebrow'); h1 = home.find('h1')
    copt_title = eb.get_text().split('·')[0].strip() if eb is not None else ''
    title = h1.get_text().strip() if h1 is not None else data['title']
    body = []
    for part in data['parts']:
        ids = [i for i in part['ids'] if i not in SKIP]
        if not ids: continue
        if part['name']: body.append('\\partpage{%s}\n' % plain(part['name']))
        for i in ids:
            s = sec[i]
            ttl = plain(BeautifulSoup(s['title'], 'lxml').get_text().strip())
            eyebrow = '' if i in ('intro', 'bib') else plain(s['eyebrow'])
            toc = (eyebrow + '\u3000' + ttl) if eyebrow else ttl
            body.append('\n\\lesson{%s}{%s}{%s}\n' % (eyebrow, ttl, toc))
            soup = BeautifulSoup(WEBONLY.sub('', s['html']), 'lxml')
            root = soup.body if soup.body is not None else soup
            body.append(blocks(list(root.children), ctx))
            if i == 'intro': body.append(guide(home, ctx))
    return dict(TITLE=plain(title), COPT=ctext(copt_title), BODY=''.join(body), SUB=BOOK[name]['sub'], LEAD=BOOK[name]['lead'], TITLEBR=BOOK[name]['titlebr'])

def main():
    src, name, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
    only = sys.argv[4].split(',') if len(sys.argv) > 4 else None
    date = os.environ.get('BOOK_DATE', '2026年11月')
    load_fonts(os.path.join(outdir, 'Antinoou.ttf'))
    data = json.load(open(src, encoding='utf-8'))
    if only:
        for p in data['parts']: p['ids'] = [i for i in p['ids'] if i in only or i == 'home']
    v = build(data, name); v['DATE'] = date
    t = open(os.path.join(HERE, 'template.tex'), encoding='utf-8').read()
    for k, val in v.items(): t = t.replace('@@' + k + '@@', val)
    out = os.path.join(outdir, name + '.tex')
    open(out, 'w', encoding='utf-8').write(t)
    print(out, len(t), 'bytes;', t.count('\\lesson{'), 'chapters;', t.count('\\begin{ex}'), 'examples;', t.count('\\begin{exi}'), 'inline examples;',
          t.count('\\begin{rdv}'), 'verses;', t.count('\\begin{longtable}'), 'tables;', t.count('\\begin{figbox}'), 'figures;', t.count('\\begin{ptbox}'), 'points;', t.count('\\begin{exbox}'), 'exercises')

if __name__ == '__main__':
    main()
