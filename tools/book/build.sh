#!/bin/bash
# 書籍版（PDF）を作る。ウェブ版のページ（sahidic.html / bohairic.html）がそのまま原稿になる。
#   使い方: tools/book/build.sh <出力先のフォルダ> [sahidic] [bohairic]
#   必要なもの: node と playwright（Chromium）、python3（beautifulsoup4・lxml・fonttools）、
#               LuaLaTeX（jlreq・luatexja・tcolorbox・needspace）、Noto Serif/Sans CJK JP、Gentium Plus
#   LuaLaTeX は一冊あたり約 6GB のメモリを使うので、二冊を同時には組まない。
set -e
HERE=$(cd "$(dirname "$0")" && pwd); ROOT=$(cd "$HERE/../.." && pwd)
OUT=${1:?出力先のフォルダを指定してください}; shift || true
mkdir -p "$OUT"; OUT=$(cd "$OUT" && pwd)
[ $# -eq 0 ] && set -- sahidic bohairic
# コプト文字のフォントは、ページに埋め込んである Antinoou を取り出して使う
[ -f "$OUT/Antinoou.ttf" ] || python3 "$HERE/font.py" "$ROOT/sahidic.html" "$OUT/Antinoou.ttf"
for n in "$@"; do
  node "$HERE/dump.js" "$ROOT/$n.html" "$OUT/$n.json"        # 課を組み直した後の本文を取り出す
  python3 "$HERE/tex.py" "$OUT/$n.json" "$n" "$OUT"          # LuaLaTeX の原稿にする
  ( cd "$OUT" && rm -f "$n.aux" "$n.toc" "$n.out" &&
    for i in 1 2 3; do lualatex -interaction=nonstopmode -halt-on-error "$n.tex" > "$n.stdout" 2>&1 || { grep -n '^!' -A8 "$n.stdout" | head -30; exit 1; }; done &&
    echo "$n.pdf: $(grep -o 'Output written.*' "$n.stdout")  overfull $(grep -c Overfull "$n.log")  missing chars $(grep -c 'Missing character' "$n.log")" )
done
