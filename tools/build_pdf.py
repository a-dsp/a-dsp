"""ガイドを印刷用PDFにする。

使い方（リポジトリの直下で）: python3 tools/build_pdf.py [出力先フォルダ]
出力: 雨天出動_報告メール_使い方.pdf / 雨天出動_報告メール_管理者向け.pdf（既定は dist/）
フォントの前提は tools/shots.py と同じ。
"""
import re, sys, pathlib
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'dist'
OUT.mkdir(parents=True, exist_ok=True)
FONT = ROOT / 'tools' / '.fonts' / 'package'
css = ''
if (FONT / '400.css').exists():
    css = ''.join((FONT / f'{w}.css').read_text().replace('./files/', (FONT / 'files').as_uri() + '/') for w in ('400', '700'))

with sync_playwright() as p:
    b = p.chromium.launch(args=['--lang=ja-JP'])
    ctx = b.new_context(locale='ja-JP', color_scheme='light')
    if css: ctx.route(re.compile(r'https://fonts\.(googleapis|gstatic)\.com/.*'), lambda r: r.abort())
    for src, name in ((ROOT / 'guide.html', '雨天出動_報告メール_使い方.pdf'), (ROOT / 'docs' / 'admin.html', '雨天出動_報告メール_管理者向け.pdf')):
        pg = ctx.new_page(); pg.goto(src.as_uri())
        if css: pg.add_style_tag(content=css)
        pg.wait_for_timeout(800); pg.emulate_media(media='print')
        pg.pdf(path=str(OUT / name), format='A4', print_background=True, prefer_css_page_size=True)
    b.close()
print('PDF ->', OUT)
