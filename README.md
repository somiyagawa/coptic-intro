# コプト語入門（サイード方言・教会ボハイラ方言）

静的サイトです。ビルドは不要です。

## Vercel への公開

GitHub の main に push すると Vercel が公開します。フレームワークは "Other"、ビルドコマンドと出力ディレクトリは空欄です。

- index.html     方言の選択画面
- sahidic.html   基礎コプト語サイード方言文法入門（全24課、文法28章）
- bohairic.html  コプト語教会ボハイラ方言入門（全24課、文法28章）

## tools/（公開には含めません）

表示の改良は、ビルド済みのページに後から重ねています。

    mkdir base && git show 2003160:sahidic.html > base/sahidic.html && git show 2003160:bohairic.html > base/bohairic.html
    python3 tools/restyle.py base .

- tools/restyle.py  重ねる処理の本体
- tools/rs.css      読みやすさの層（文字の大きさ、例文・講読本文・クイズの体裁）
- tools/rs.js       課を開いたときの組み直し（番号つき例文、節ごとの訳、語を押すと出る分析、表示の切り替え）
- tools/kana_s.py   サイード方言のカタカナ（重ね書きの母音は マアウ・ワアヴ・ウェーエヴ、ⲃ はヴ行。B2V=False でバ行に戻る）
