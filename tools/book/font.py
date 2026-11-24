#!/usr/bin/env python3
"""ページに埋め込んである Antinoou（WOFF）を取り出して TTF に直す（LuaLaTeX と列幅の計算で使う）。
使い方: python3 font.py <sahidic.html> <Antinoou.ttf>"""
import base64, io, re, sys
from fontTools.ttLib import TTFont
html = open(sys.argv[1], encoding='utf-8').read()
m = re.search(r'@font-face\{font-family:"Antinoou";[^}]*?url\(data:font/woff;base64,([A-Za-z0-9+/=]+)\)', html)
if not m: sys.exit('Antinoou の @font-face が見つかりません')
f = TTFont(io.BytesIO(base64.b64decode(m.group(1)))); f.flavor = None; f.save(sys.argv[2])
print('wrote', sys.argv[2], len(f.getGlyphOrder()), 'glyphs')
