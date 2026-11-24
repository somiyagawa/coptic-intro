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

- tools/restyle.py  重ねる処理の本体（活用形の名前を 第一現在・第二完了・第三未来 と書く処理、縮約した不定冠詞 ⲉ-ⲩ-ⲣⲱⲙⲉ の修正、
                    誤っていたグロスの修正（ⲛⲁⲩ「見る」、ⲟⲩⲇⲉ、ⲛ̄ϩⲏⲧ「私の中に」、ϯ-ⲥ̀ⲃⲱ「知恵」）、「コースの構成」の表の修正を含む）
- tools/ang.py      独立代名詞の短い形（ⲁⲛⲅ̄-、ⲛ̄ⲧⲕ̄-、ⲛ̄ⲧⲉ-、ⲛ̄ⲧⲉⲧⲛ̄-）の説明（第4課、文法1・4・10・15・23、ボハイラ方言版の第4課・文法1）。
- tools/add2.py     Layton の文法書（A Coptic Grammar、Coptic in 20 Lessons）と照らして足した項目：相関の比較、理由の節、間接話法、非人称の述語、
  動詞の前に付く要素、まれな準動詞、曜日・月名・日付、複合前置詞、場所の副詞、文頭の小辞、応答の語など（文法1・4・6・10・12・13・14・17・18・20・21・24・26、第12課）。
  節番号は Layton の二冊の本文で確かめ、付録Fと各章の「他の文法書」の欄（Coptic in 20 Lessons の課、A Coptic Grammar の §95・§§131–135・§§505–507）も
  同書の目次と段落の見出しに合わせて直す。ボハイラ方言の曜日と月の名は Younan『So, you want to learn Coptic?』第9章による。
- tools/rb.py       語形から転写とカタカナの読みを作り、ルビつきのマークアップにする（add2.py が使う）。ページにすでにある読みを優先する。
                    実例と数は Coptic SCRIPTORIUM のコーパスで確かめたもの（確かめた内容はファイルの冒頭に記載）
- tools/rs.css      読みやすさの層（文字の大きさ、面と余白、例文・講読本文・表・クイズの体裁、狭い画面の帯）
- tools/rs.js       課を開いたときの組み直し（番号つき例文、節ごとの訳、語を押すと出る分析、表示の切り替え、説明文の中のルビを行の高さに数えない処理）
- tools/kana_s.py   サイード方言のカタカナ（重ね書きの母音は マアウ・ワアヴ・ウェーエヴ、ⲟⲟⲩ は オウ（ⲙⲟⲟⲩ モウ）、ⲃ はヴ行。B2V=False でバ行に戻る）

## 書籍版（PDF）

ウェブ版のページがそのまま原稿です。ページを直してから次を実行すると、同じ内容の PDF ができます。

    tools/book/build.sh out            # out/sahidic.pdf と out/bohairic.pdf（一冊ずつ順に組む）

- tools/book/dump.js       ページを開いて全部の課を組み直し、本文を JSON に書き出す（Playwright）
- tools/book/tex.py        JSON から LuaLaTeX の原稿を作る。例文・講読本文は 転写／カナ／語形／略号のグロス／やさしいグロス を左そろえで積み、
                           説明文の中の語はカナだけを上に置く（行送りは一定）。確認クイズと「解答を見る」は入れない（解答は付録B）
- tools/book/template.tex  体裁（B5、jlreq、Noto Serif/Sans CJK JP、Gentium Plus、Antinoou）
- tools/book/font.py       ページに埋め込んである Antinoou（WOFF）を TTF に直す
- tools/book/build.sh      上の一連の作業

LuaLaTeX は一冊あたり約 6GB のメモリを使います（和文フォントを多くの大きさで読み込むため）。

