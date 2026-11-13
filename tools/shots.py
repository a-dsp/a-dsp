"""ガイド用のスクリーンショットを撮り直す。

使い方（リポジトリの直下で）:
  python3 tools/shots.py
前提:
  - Python の playwright と Chromium が入っていること
  - 日本語フォント: tools/.fonts/package に @fontsource/biz-udpgothic を展開しておくと見た目が本番と同じになる
      (cd tools/.fonts && npm pack @fontsource/biz-udpgothic && tar xzf fontsource-biz-udpgothic-*.tgz)
    無ければシステムのフォントで撮る
出力: img/01_link.png 〜 img/10_admin.png（例のデータはすべてダミー）
"""
import json, base64, re, pathlib
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / 'img'
PAGE = (ROOT / 'index.html').as_uri()
FONT = ROOT / 'tools' / '.fonts' / 'package'

css = ''
if (FONT / '400.css').exists():
    for w in ('400', '700'):
        css += (FONT / f'{w}.css').read_text().replace('./files/', (FONT / 'files').as_uri() + '/')

cfg = {"to": ["report1@example.jp", "report2@example.jp"], "cc": ["copy1@example.jp"], "company": "ミザック株式会社"}
def b64e(s): return base64.urlsafe_b64encode(s.encode()).decode().rstrip('=')
base_form = {"me": "山田", "area": "東部方面", "rDate": "2026-11-05", "rTime": "21:10", "n1": "山田 太郎", "p1": "090-0000-0000",
  "n2": "佐藤 次郎", "p2": "090-1111-1111", "type": "start", "planFrom": "21:10", "planTo": "06:00", "doneFrom": "21:10", "doneTo": "00:30",
  "result": "ok", "abnN": "1", "other": "", "contSame": True, "cn1": "", "cp1": "", "cn2": "", "cp2": "", "contFrom": "00:30", "contTo": "06:00"}

def shot(page, sels, name, pad=6):
    bx = [page.locator(s).first.bounding_box() for s in sels]
    x0 = min(b['x'] for b in bx) - pad; y0 = min(b['y'] for b in bx) - pad
    x1 = max(b['x'] + b['width'] for b in bx) + pad; y1 = max(b['y'] + b['height'] for b in bx) + pad
    page.screenshot(path=str(OUT / name), clip={'x': max(0, x0), 'y': max(0, y0), 'width': x1 - x0, 'height': y1 - y0}, full_page=True)

with sync_playwright() as p:
    b = p.chromium.launch(args=['--lang=ja-JP'])
    def newpage(form=None, cfg_store=None, url=PAGE):
        ctx = b.new_context(viewport={'width': 390, 'height': 900}, device_scale_factor=2, color_scheme='light', locale='ja-JP')
        if css: ctx.route(re.compile(r'https://fonts\.(googleapis|gstatic)\.com/.*'), lambda r: r.abort())
        init = "localStorage.clear();"
        if cfg_store: init += f"localStorage.setItem('rainReport.cfg.v1', {json.dumps(json.dumps(cfg_store))});"
        if form: init += f"localStorage.setItem('rainReport.form.v1', {json.dumps(json.dumps(form))});"
        ctx.add_init_script("if(!sessionStorage.getItem('seeded')){" + init + "sessionStorage.setItem('seeded','1');}")
        pg = ctx.new_page(); pg.goto(url)
        if css: pg.add_style_tag(content=css)
        pg.wait_for_timeout(600)
        return pg
    pg = newpage(form=dict(base_form, me=''), url=PAGE + '#c=' + b64e(json.dumps(cfg, ensure_ascii=False)))
    shot(pg, ['header', '#banner', 'section:has(#rcpt)'], '01_link.png')
    pg = newpage(form=base_form, cfg_store=cfg)
    shot(pg, ['section:has(#rDate)'], '02_info.png')
    shot(pg, ['section:has(#t-start)'], '03_type.png')
    shot(pg, ['section:has(#planFrom)'], '04_start.png')
    shot(pg, ['section:has(#status)'], '05_send.png')
    f = dict(base_form, type='end', result='ng', doneTo='05:40', abnN='1', place1='生野区中川4丁目 〇〇付近',
             what1='マンホールより水柱', cwo1='鈴木', act1='約10ｍ後方より自主警備実施（CWOと交代まで）')
    pg = newpage(form=f, cfg_store=cfg)
    shot(pg, ['section:has(#planFrom)'], '06_prog.png')
    pg = newpage(form=dict(base_form, planTo='', p2=''), cfg_store=cfg)
    shot(pg, ['#status', '.mail'], '07_missing.png')
    shot(pg, ['.copies'], '08_copy.png')
    pg = newpage(form=base_form, cfg_store=cfg)
    pg.click('#resetBtn'); pg.wait_for_timeout(100)
    shot(pg, ['#resetBtn'], '09_reset.png')
    pg = newpage(url=PAGE + '#admin')
    pg.fill('#aTo', "report1@example.jp\nreport2@example.jp"); pg.fill('#aCc', "copy1@example.jp")
    pg.click('#aMake'); pg.wait_for_timeout(200)
    pg.evaluate("document.getElementById('aOut').value = document.getElementById('aOut').value.replace(/^file:[^#]*/, 'https://a-dsp.github.io/a-dsp/')")
    pg.evaluate("window.scrollTo(0,0)")
    pg.locator('#admin').screenshot(path=str(OUT / '10_admin.png'))
    b.close()
print('done')
