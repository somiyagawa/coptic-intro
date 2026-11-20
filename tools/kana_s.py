# -*- coding: utf-8 -*-
"""サイード方言のカタカナ読みの後処理。
1. 重ね書きの母音：長音説・声門閉鎖音説のどちらでも読めるように、二つ目の母音字を
   ふつうの大きさのカナで書く（ⲙⲁⲁⲩ マアウ、ϣⲟⲟⲡ ショオプ、ϩⲏⲏⲧⲉ ヘーエテ、ϫⲱⲱⲙⲉ ジョーオメ）。
2. ⲃ をヴ行で書く（ⲟⲩⲁⲁⲃ ワアヴ、ⲉⲃⲟⲗ エヴォル）。B2V=False でバ行に戻せる。
"""
import re, itertools
B2V = True
STRIP = re.compile('[̀̄̅︤-︦†⸗\\-·\\s]')
ROW = {'a': 'アカサタナハマヤラワガザダバパァャヮ', 'e': 'エケセテネヘメレゲゼデベペェ', 'o': 'オコソトノホモヨロヲゴゾドボポォョ',
       'u': 'ウクスツヌフムユルグズブプゥュヴ'}
ADD = {'AA': 'ア', 'EE': 'エ', 'OO': 'オ'}
def sources(w):
    w = STRIP.sub('', w); out = []; i = 0
    while i < len(w):
        two = w[i:i + 2]
        if two in ('ⲏⲏ', 'ⲱⲱ'): out.append(('HH' if two == 'ⲏⲏ' else 'WW', True)); i += 2
        elif two in ('ⲁⲁ', 'ⲉⲉ', 'ⲟⲟ'):
            if two == 'ⲉⲉ' and w[i + 2:i + 3] == 'ⲓ': i += 1; continue
            out.append(({'ⲁⲁ': 'AA', 'ⲉⲉ': 'EE', 'ⲟⲟ': 'OO'}[two], False)); i += 2
        elif two == 'ⲟⲩ': out.append(('U', False)); i += 2
        elif w[i] == 'ⲏ': out.append(('H', True)); i += 1
        elif w[i] == 'ⲱ': out.append(('W', True)); i += 1
        else: i += 1
    return out
def qual(src): return {'AA': 'a', 'EE': 'e', 'OO': 'o', 'H': 'e', 'HH': 'e', 'W': 'o', 'WW': 'o', 'U': 'u'}[src]
def patch_dv(w, k):
    """k: カナ（<i class="kc"> を含んでよい）。戻り値 (新しいカナ, 状態)"""
    if not re.search('ⲁⲁ|ⲉⲉ|ⲏⲏ|ⲟⲟ|ⲱⲱ', STRIP.sub('', w)): return k, 'none'
    pos = [m.start() for m in re.finditer('ー', k)]
    src = sources(w)
    if not any(s in ('AA', 'EE', 'OO', 'HH', 'WW') for s, _ in src): return k, 'none'
    opt = [i for i, (s, mand) in enumerate(src) if not mand]
    sols = []
    for r in range(len(opt) + 1):
        for comb in itertools.combinations(opt, r):
            use = [s for i, (s, mand) in enumerate(src) if mand or i in comb]
            if len(use) != len(pos): continue
            ok = True
            for p, s in zip(pos, use):
                prev = re.sub(r'<[^>]+>', '', k[:p])[-1:] 
                if prev not in ROW[qual(s)]: ok = False; break
            if ok: sols.append(use)
    if len(sols) != 1: return k, 'ambiguous' if sols else 'nomatch'
    out = []; last = 0
    for p, s in zip(pos, sols[0]):
        out.append(k[last:p])
        out.append(ADD[s] if s in ADD else 'ーエ' if s == 'HH' else 'ーオ' if s == 'WW' else 'ー')
        last = p + 1
    out.append(k[last:])
    return ''.join(out), 'ok'
BV = {'バ': 'ヴァ', 'ビ': 'ヴィ', 'ブ': 'ヴ', 'ベ': 'ヴェ', 'ボ': 'ヴォ'}
def patch_b(w, k):
    if not B2V or 'ⲃ' not in w: return k, 'none'
    n = len(re.findall('[バビブベボ]', k))
    k2 = re.sub('[バビブベボ]', lambda m: BV[m.group(0)], k)
    return k2, 'ok' if n == w.count('ⲃ') else 'count%d/%d' % (n, w.count('ⲃ'))
def patch(w, k):
    k1, s1 = patch_dv(w, k)
    k2, s2 = patch_b(w, k1)
    return k2, (s1, s2)
