# -*- coding: utf-8 -*-
"""コプト語の語形から、転写とカタカナの読みを作り、ルビつきのマークアップにする。追加した記述（tools/add2.py）で使う。

書き方（一つの例を一つの文字列で書く）
    'ⲁ⸗ϥ-ⲉⲓ ⲉϩⲣⲁⲓ ϩⲙ̄-ⲡ|ⲙⲟⲟⲩ'
    空白 … 語の切れ目      -  … ハイフンで示す切れ目（ルビの単位もここで切る）
    |  … 表示しない形態素の切れ目（カナの中黒になる）      ⸗ … 人称形の印（表示する）

読みは、まずページの中にすでにある同じ語形の読みを使い、なければ下の規則で作る。規則で作れない読み
（強勢のある ⲟⲩ の長音、ギリシア語の語など）は OVERRIDE に書く。
"""
import re, collections

V = 'aeêioôu'
BASE = {'ⲁ': 'a', 'ⲉ': 'e', 'ⲏ': 'ê', 'ⲓ': 'i', 'ⲟ': 'o', 'ⲱ': 'ô', 'ⲩ': 'u', 'ⲃ': 'b', 'ⲅ': 'g', 'ⲇ': 'd', 'ⲍ': 'z', 'ⲕ': 'k', 'ⲗ': 'l',
        'ⲙ': 'm', 'ⲛ': 'n', 'ⲡ': 'p', 'ⲣ': 'r', 'ⲥ': 's', 'ⲧ': 't', 'ϣ': 'š', 'ϥ': 'f', 'ϩ': 'h', 'ϫ': 'č'}
ASP = {'s': {'ⲑ': 'th', 'ⲫ': 'ph', 'ⲭ': 'kh', 'ϭ': 'kʸ', 'ϧ': 'ḫ'}, 'b': {'ⲑ': 'tʰ', 'ⲫ': 'pʰ', 'ⲭ': 'kʰ', 'ϭ': 'čʰ', 'ϧ': 'ḫ'}}
TWO = {'ⲝ': ('k', 's'), 'ⲯ': ('p', 's'), 'ϯ': ('t', 'i')}
MARK = '̄̅̀︤︥︦'
VOW = ('a', 'e', 'ê', 'i', 'o', 'ô', 'u', 'ou', 'ə')

def phones(chunk, d):
    """[[音, 元の文字, 直前に形態素の切れ目があるか]]。音は a e ê i o ô u ou ə と子音"""
    out = []; i = 0; cut = False; s = chunk.replace('†', '')
    while i < len(s):
        ch = s[i]
        if ch in '|⸗': cut = cut or ch == '|'; i += 1; continue
        if ch in MARK or ch == '-': i += 1; continue
        mk = i + 1 < len(s) and s[i + 1] in MARK
        if ch == 'ⲟ' and s[i + 1:i + 2] == 'ⲩ' and not (i + 2 < len(s) and s[i + 2] in MARK):
            out.append(['ou', 'ⲟⲩ', cut]); cut = False; i += 2; continue
        if ch in TWO:
            if mk: out.append(['ə', '', cut]); cut = False
            out.append([TWO[ch][0], ch, cut]); out.append([TWO[ch][1], ch, False]); cut = False; i += 1; continue
        p = BASE.get(ch) or ASP[d].get(ch)
        if p is None: i += 1; continue
        if mk and p not in VOW: out.append(['ə', '', cut]); cut = False
        out.append([p, ch, cut]); cut = False; i += 1
    return out

def latin(chunk, d):
    ph = phones(chunk, d); out = []
    for j, (p, src, cut) in enumerate(ph):
        if p == 'ə' and d == 'b' and j > 0: continue          # ボハイラ方言：語中のジンキムは転写に出さない
        if d == 'b' and p == 'g' and j + 1 < len(ph) and ph[j + 1][0] in ('g', 'k', 'kʰ'): p = 'n'
        out.append(p)
    return ''.join(out)

ROWS = {'': 'アイウエオ', 'k': 'カキクケコ', 's': 'サ1スセソ', 't': 'タ2トテト', 'n': 'ナニヌネノ', 'h': 'ハヒフヘホ',
        'm': 'マミムメモ', 'r': 'ラリルレロ', 'l': 'ラリルレロ', 'p': 'パピプペポ', 'g': 'ガギグゲゴ', 'd': 'ダ3ドデド', 'z': 'ザ4ズゼゾ'}
MULTI = {'1': 'スィ', '2': 'ティ', '3': 'ディ', '4': 'ズィ'}
COMB = {'b': ['ヴァ', 'ヴィ', 'ヴ', 'ヴェ', 'ヴォ'], 'f': ['ファ', 'フィ', 'フ', 'フェ', 'フォ'], 'š': ['シャ', 'シ', 'シュ', 'シェ', 'ショ'],
        'č': ['ジャ', 'ジ', 'ジュ', 'ジェ', 'ジョ'], 'kʸ': ['キャ', 'キ', 'キュ', 'キェ', 'キョ'], 'w': ['ワ', 'ウィ', 'ウ', 'ウェ', 'ウオ'],
        'y': ['ヤ', 'イ', 'ユ', 'イェ', 'ヨ'], 'čʰ': ['チャ', 'チ', 'チュ', 'チェ', 'チョ'], 'tʰ': ['さ', 'すぃ', 'す', 'せ', 'そ'], 'ḫ': ['は', 'ひ', 'ふ', 'へ', 'ほ'],
        'pʰ': ['ファ', 'フィ', 'フ', 'フェ', 'フォ'], 'kʰ': ['カ', 'キ', 'ク', 'ケ', 'コ']}
VI = {'a': 0, 'i': 1, 'u': 1, 'ou': 2, 'e': 3, 'ê': 3, 'ə': 3, 'o': 4, 'ô': 4}
SMALL = {'k': 'ク', 's': 'ス', 't': 'ト', 'p': 'プ', 'm': 'ム', 'r': 'ル', 'l': 'ル', 'g': 'グ', 'd': 'ド', 'z': 'ズ', 'b': 'ヴ', 'f': 'フ', 'š': 'シュ',
         'č': 'ジ', 'kʸ': 'キ', 'čʰ': 'チ', 'tʰ': 'す', 'pʰ': 'フ', 'kʰ': 'ク', 'ḫ': 'ふ', 'th': 'ト', 'ph': 'プ', 'kh': 'ク', 'v': 'ヴ'}
STOP = {'th': 't', 'ph': 'p', 'kh': 'k'}
HIRA = {'ハ': 'は', 'ヒ': 'ひ', 'フ': 'ふ', 'ヘ': 'へ', 'ホ': 'ほ'}
def cv(c, v):
    i = VI[v]
    k = COMB[c][i] if c in COMB else MULTI.get(ROWS[c][i], ROWS[c][i])
    if c == 't' and v == 'ou': k = 'トゥ'
    if c == 'd' and v == 'ou': k = 'ドゥ'
    return k + ('ー' if v in ('ê', 'ô') else '')

def kana(chunk, d, long_ou=False):
    ph = phones(chunk, d); n = len(ph)
    isv = lambda j: 0 <= j < n and ph[j][0] in VOW
    # ⲉⲓ・ⲓ：切れ目の頭か母音の後で、次が a e o ô なら y。切れ目の頭の ⲉⲓ は i
    k2 = []; j = 0
    while j < n:
        p, src, cut = ph[j]; start = (j == 0 or cut); aftv = bool(k2) and k2[-1][0] in VOW and not cut
        if p == 'e' and j + 1 < n and ph[j + 1][0] == 'i' and not ph[j + 1][2] and (start or aftv):
            nx = ph[j + 2] if j + 2 < n else None
            k2.append(['y' if (nx and nx[0] in ('a', 'e', 'o', 'ô') and not nx[2]) else 'i', 'ⲉⲓ', cut]); j += 2; continue
        if p == 'i' and start and j + 1 < n and ph[j + 1][0] in ('a', 'o', 'ô') and not ph[j + 1][2]:
            k2.append(['y', src, cut]); j += 1; continue
        k2.append(ph[j]); j += 1
    ph = k2; n = len(ph)
    for j in range(n):
        p, src, cut = ph[j]; nx = ph[j + 1] if j + 1 < n else None; pv = ph[j - 1][0] if j and not cut else ''
        if p == 'ou' and nx and nx[0] in VOW and nx[0] not in ('ou', 'ə') and not nx[2]:
            if pv not in VOW or (d == 'b' and nx[0] == 'i'): ph[j][0] = 'w'
        if d == 'b':
            if p == 'č' and not (nx and nx[0] in ('e', 'ê', 'i', 'ə')): ph[j][0] = 'g'
            if p == 'u' and pv in ('a', 'e'): ph[j][0] = 'v'
            if p == 'tʰ' and pv == 's': ph[j][0] = 't'
        if p == 'g' and nx and nx[0] in ('g', 'k', 'kʰ', 'kh'): ph[j][0] = 'n'
    out = []; j = 0; lastv = ''
    while j < n:
        p, src, cut = ph[j]
        if cut:
            if out: out.append('・')
            lastv = ''
        nx = ph[j + 1] if j + 1 < n else None
        if p in VOW:
            if p in ('u', 'ou') and lastv: out.append('ウ')
            elif p == 'i' and lastv: out.append('イ')
            elif p == lastv and p in ('a', 'e', 'o'): out.append('アイウエオ'[VI[p]])            # 重ね書きの母音
            elif p == lastv and p in ('ê', 'ô'): out.append('エ' if p == 'ê' else 'オ')
            elif p == 'u' and j == 0: out.append('ウ')
            else: out.append(cv('', p) + ('ー' if p == 'ou' and long_ou else ''))
            lastv = p; j += 1; continue
        if nx and nx[0] in VOW and not nx[2]:
            v = nx[0]
            if p in STOP:
                if v == 'ə': k = cv(STOP[p], v)
                else: k = '[' + SMALL[p] + ']' + cv('h', v)
            else: k = cv('b' if p == 'v' else p, v)
            if v == 'ou' and long_ou: k += 'ー'
            out.append(k); lastv = v; j += 2; continue
        if p == 'w': out.append('ウ'); lastv = 'ou'
        elif p == 'y': out.append('イ'); lastv = 'i'
        elif p == 'n': out.append('ン')
        elif p == 'm' and nx and nx[0] in ('m', 'p', 'b', 'pʰ', 'ph') and not nx[2]: out.append('ン')
        elif p == 'h':
            e = 'ハヒフヘホ'[VI[lastv]] if (lastv and not (nx and nx[0] == 'w')) else 'フ'
            out.append('[' + (HIRA[e] if d == 'b' else e) + ']')
        else: out.append('[' + SMALL.get(p, '?') + ']')
        j += 1
    return ''.join(out)

# ── 読みの修正（規則で作れないもの）。語形 → カナ ─────────────────────────
OVERRIDE = {
    's': {'ⲡⲉ|ⲥⲃⲟⲩⲓ': 'ペ・[ス]ヴイ', 'ϩⲟⲩⲛ': 'フーン', 'ⲡⲁⲣⲙⲟⲩⲧⲉ': 'パ[ル]ムーテ', 'ϩⲓⲧⲟⲩⲱ⸗': 'ヒトゥオー', 'ⲛⲟⲩⲛⲉ': 'ヌーネ', 'ϩⲉⲛ|ⲕⲟⲩⲓ': 'ヘン・クイ',
          'ϣⲟⲩϣⲟⲩ': 'シュシュー', 'ⲛ̄ⲧⲉⲩⲛⲟⲩ': 'エンテウヌー', 'ⲛ̄ϩⲟⲩⲟ': 'エン[ヘ]ウオ', 'ⲛⲟⲩⲃ': 'ヌー[ヴ]', 'ϫⲛⲟⲩ⸗ϥ': '[ジ]ヌー[フ]', 'ⲥⲟⲩⲁ': 'スワ'},
    'b': {'ⲡⲓ|ⲙⲁⲑⲏⲧⲏⲥ': 'ピ・マせテー[ス]', 'ⲥⲁϧⲟⲩⲛ': 'サふーン', 'ⲫⲁⲣⲙⲟⲩⲑⲓ': 'ファ[ル]ムーすぃ', 'ⲛⲟⲩⲛⲓ': 'ヌーニ', 'ϣⲟⲩϣⲟⲩ': 'シュシュー',
          'ⲙ̀ⲫ̀ⲣⲏϯ': 'エ[ム]・エ[フ]・レーティ', 'ⲁⲣⲭⲉⲗⲁⲟⲥ': 'ア[ル]シェラオ[ス]', 'ϯ|ⲓⲟⲩⲇⲉⲁ': 'ティ・ユデア', 'ϩⲩⲅⲟⲩⲙⲉⲛⲟⲥ': 'ヒグーメノ[ス]',
          'ⲡⲓ|ⲕⲟⲩϫⲓ': 'ピ・クージ', 'ϩⲁⲛ|ⲕⲟⲩϫⲓ': 'ハン・クージ', 'ⲡⲓ|ϯⲟⲩ': 'ピ・ティウー', 'ⲡⲓ|ⲧ̀ⲓⲟⲩ': 'ピ・エティウー', 'ⲡⲓ|ϥ̀ⲧⲟⲩ': 'ピ・エ[フ]トゥー'}}
LAT_OVERRIDE = {'s': {}, 'b': {}}

UNIT = re.compile(r'<span class="rb"><span class="rt" aria-hidden="true"><span class="rl">([^<]*)</span><span class="rk">((?:[^<]|<i class="kc">[^<]*</i>)*)</span></span><span class="rw">([^<]*)</span></span>')
UNITG = re.compile(r'<span class="rl">([^<]*)</span><span class="rk">((?:[^<]|<i class="kc">[^<]*</i>)*)</span></span><span class="rw"><span class="w0">([^<]*)</span>')

KATA = str.maketrans('はひふへほさしすせそぃ', 'ハヒフヘホサシスセソィ')
class Ruby:
    """page：ページ全体（すでにある読みを拾う）。d：語の方言。home：ページの方言"""
    def __init__(self, page, d, home=None):
        self.d = d; self.home = home or d; self.lex = {}; self.made = collections.OrderedDict()
        c = collections.defaultdict(collections.Counter)
        for lat, k, w in UNIT.findall(page): c[w][(lat, k)] += 1
        for lat, k, w in UNITG.findall(page): c[w][(lat, k)] += 0.5
        for w, cc in c.items(): self.lex[w] = cc.most_common(1)[0][0]
    def known(self, show):
        if show not in self.lex: return False
        if self.d == self.home: return True
        return bool(re.search('[\u0300ϧ]' if self.d == 'b' else '[\u0304]', show))    # 他方言の語は、その方言の印がある語形だけ拾う
    def unit(self, chunk):
        show = chunk.replace('|', '')
        if chunk in OVERRIDE[self.d]:
            lat = LAT_OVERRIDE[self.d].get(chunk) or latin(chunk, self.d); k = OVERRIDE[self.d][chunk]
            if self.d == 'b' and self.home == 's': k = k.translate(KATA)
            k = kc(k)
        elif self.known(show) and ('|' not in chunk or '・' in self.lex[show][1]): lat, k = self.lex[show]
        else:
            lat = latin(chunk, self.d); k = kana(chunk, self.d)
            if self.d == 'b' and self.home == 's': k = k.translate(KATA)
            self.made[chunk] = (lat, k); k = kc(k)
        return ('<span class="rb"><span class="rt" aria-hidden="true"><span class="rl">%s</span><span class="rk">%s</span></span>'
                '<span class="rw">%s</span></span>') % (lat, k, show)
    def x(self, s):
        """例を一つ、ルビつきにする"""
        words = []
        for w in s.split(' '):
            parts = []
            for ch in re.split('(-)', w):
                if ch == '-': parts.append('-')
                elif ch == '': continue
                elif not re.search('[\u2c80-\u2cff\u03e2-\u03ef]', ch): parts.append(ch)
                else: parts.append(self.unit(ch))
            words.append(''.join(parts))
        return '<span class="copt" lang="cop">' + ' '.join(words) + '</span>'

def kc(s): return re.sub(r'\[([^\]]*)\]', r'<i class="kc">\1</i>', s)
