#!/usr/bin/env python3
from __future__ import annotations

import html
import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = Path('/opt/data/english-lessons')
LESSONS_DIR = ROOT / 'lessons'
REVIEWS_DIR = ROOT / 'reviews'
OLD_DAILY_LIMIT = 5


class TitleParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_title = False
        self.in_h1 = False
        self.title: list[str] = []
        self.h1: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == 'title':
            self.in_title = True
        if tag == 'h1':
            self.in_h1 = True

    def handle_endtag(self, tag):
        if tag == 'title':
            self.in_title = False
        if tag == 'h1':
            self.in_h1 = False

    def handle_data(self, data):
        if self.in_title:
            self.title.append(data)
        if self.in_h1:
            self.h1.append(data)

    def result(self) -> str:
        h = ' '.join(''.join(self.h1).split()).strip()
        t = ' '.join(''.join(self.title).split()).strip()
        return h or t or 'English lesson'


@dataclass
class Item:
    src: Path
    dest: Path
    rel_url: str
    title: str
    kind: str
    date_label: str
    sort_key: str


def parse_title(path: Path) -> str:
    parser = TitleParser()
    parser.feed(path.read_text(encoding='utf-8', errors='ignore'))
    return parser.result()


def infer_kind(path: Path) -> str:
    name = path.name.lower()
    if 'weekly' in name:
        return 'weekly'
    if 'monthly' in name:
        return 'monthly'
    return 'daily'


def infer_date(path: Path) -> tuple[str, str]:
    m = re.search(r'(20\d{2})-(\d{2})-(\d{2})', path.name)
    if m:
        iso = '-'.join(m.groups())
        try:
            label = datetime.strptime(iso, '%Y-%m-%d').strftime('%b %-d, %Y')
        except Exception:
            label = iso
        return label, iso
    m = re.search(r'(20\d{2})-(\d{2})', path.name)
    if m:
        iso = '-'.join(m.groups())
        return iso, iso
    return path.stem, path.stem


def collect_items() -> list[Item]:
    items: list[Item] = []
    for src in sorted(SOURCE_DIR.glob('*.html')):
        kind = infer_kind(src)
        label, key = infer_date(src)
        dest_dir = REVIEWS_DIR if kind in {'weekly', 'monthly'} else LESSONS_DIR
        prefix = 'reviews' if kind in {'weekly', 'monthly'} else 'lessons'
        items.append(Item(src, dest_dir / src.name, f'{prefix}/{src.name}', parse_title(src), kind, label, key))
    return sorted(items, key=lambda x: x.sort_key, reverse=True)


def copy_items(items: list[Item]) -> None:
    LESSONS_DIR.mkdir(parents=True, exist_ok=True)
    REVIEWS_DIR.mkdir(parents=True, exist_ok=True)
    for item in items:
        shutil.copy2(item.src, item.dest)


def nav(items: list[Item], kind: str, limit: int | None = None) -> str:
    xs = [x for x in items if x.kind == kind]
    if limit is not None:
        xs = xs[:limit]
    if not xs:
        return '<p class="empty">No items yet.</p>'
    return '\n'.join(
        f'<a class="nav-item" href="#{html.escape(x.rel_url)}" data-url="{html.escape(x.rel_url)}">'
        f'<span class="date">{html.escape(x.date_label)}</span>'
        f'<span class="title">{html.escape(x.title)}</span>'
        f'</a>'
        for x in xs
    )


def build_index(items: list[Item]) -> str:
    daily_items = [x for x in items if x.kind == 'daily']
    latest = daily_items[0] if daily_items else None
    old_daily = daily_items[1:1 + OLD_DAILY_LIMIT]
    latest_url = latest.rel_url if latest else ''
    latest_title = latest.title if latest else 'No daily lesson yet'
    generated = datetime.now().strftime('%Y-%m-%d %H:%M')
    today_nav = nav([latest], 'daily') if latest else '<p class="empty">No latest lesson yet.</p>'
    old_nav = nav(old_daily, 'daily', limit=OLD_DAILY_LIMIT)
    weekly_nav = nav(items, 'weekly')
    monthly_nav = nav(items, 'monthly')

    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Peter’s Daily English Lessons</title>
<style>
:root{{--bg:#f4f0e8;--paper:#fffdf8;--ink:#1f1c18;--muted:#6d6459;--line:#ded3c4;--accent:#173f5f;--soft:#efe4d3;--shadow:0 18px 45px rgba(36,24,12,.12)}}
*{{box-sizing:border-box}}
body{{margin:0;background:radial-gradient(circle at 0 0,rgba(23,63,95,.13),transparent 30rem),radial-gradient(circle at 100% 100%,rgba(143,63,47,.12),transparent 28rem),var(--bg);color:var(--ink);font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}
button{{font:inherit}}
.mobile-bar{{display:none}}
.backdrop{{display:none}}
.app{{min-height:100vh;display:grid;grid-template-columns:360px 1fr}}
aside{{position:sticky;top:0;height:100vh;overflow:auto;border-right:1px solid var(--line);background:rgba(255,253,248,.88);padding:22px;backdrop-filter:blur(8px);z-index:20}}
main{{padding:22px;min-width:0}}
h1{{font-family:ui-serif,Georgia,serif;font-size:42px;line-height:1.02;letter-spacing:-.045em;margin:0 0 10px}}
.sub{{color:var(--muted);font-size:15px;line-height:1.55;margin:0 0 18px}}
.badge{{display:inline-flex;min-height:34px;align-items:center;padding:6px 11px;border-radius:999px;border:1px solid var(--line);background:var(--soft);font-size:13px;font-weight:800;margin:0 0 18px}}
h2{{font-size:13px;letter-spacing:.12em;text-transform:uppercase;color:var(--accent);margin:22px 0 10px}}
.nav-item{{display:block;text-decoration:none;color:var(--ink);padding:12px;border:1px solid var(--line);background:var(--paper);border-radius:16px;margin:9px 0;transition:.15s ease}}
.nav-item:hover,.nav-item.active{{border-color:rgba(23,63,95,.55);transform:translateY(-1px);box-shadow:0 8px 20px rgba(45,31,16,.08)}}
.date{{display:block;color:var(--accent);font-size:12px;font-weight:900;letter-spacing:.08em;text-transform:uppercase;margin-bottom:4px}}
.title{{display:block;font-family:ui-serif,Georgia,serif;font-size:17px;line-height:1.35}}
.empty{{color:var(--muted);font-size:14px}}
.viewer-shell{{background:var(--paper);border:1px solid var(--line);border-radius:26px;box-shadow:var(--shadow);overflow:hidden;height:calc(100vh - 44px);display:flex;flex-direction:column}}
.viewer-top{{display:flex;align-items:center;gap:12px;padding:14px 16px;border-bottom:1px solid var(--line);background:#fffaf2}}
#current-title{{font-weight:900;overflow:hidden;white-space:nowrap;text-overflow:ellipsis}}
iframe{{width:100%;flex:1;border:0;background:white}}
.close-menu{{display:none}}
@media(max-width:860px){{
  body{{padding-top:calc(58px + env(safe-area-inset-top));overflow:hidden}}
  .mobile-bar{{display:flex;position:fixed;top:0;left:0;right:0;height:calc(58px + env(safe-area-inset-top));padding:env(safe-area-inset-top) 12px 8px;align-items:center;gap:10px;background:rgba(255,253,248,.96);border-bottom:1px solid var(--line);backdrop-filter:blur(10px);z-index:40}}
  .menu-button{{border:1px solid var(--line);background:var(--accent);color:white;border-radius:12px;width:42px;height:40px;padding:0;display:inline-flex;align-items:center;justify-content:center;font-weight:900;flex:0 0 auto}}
  .hamburger{{display:block;width:19px;height:14px;position:relative}}
  .hamburger::before,.hamburger::after,.hamburger span{{content:"";position:absolute;left:0;width:100%;height:2px;background:currentColor;border-radius:999px}}
  .hamburger::before{{top:0}}
  .hamburger span{{top:6px}}
  .hamburger::after{{bottom:0}}
  .site-title{{font-family:ui-serif,Georgia,serif;font-weight:950;font-size:clamp(25px,6.3vw,32px);letter-spacing:-.045em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
  .app{{display:block;min-height:calc(100vh - 58px - env(safe-area-inset-top))}}
  aside{{position:fixed;top:0;bottom:0;left:0;width:min(88vw,360px);height:100dvh;transform:translateX(-105%);transition:transform .22s ease;box-shadow:var(--shadow);border-right:1px solid var(--line);padding:calc(18px + env(safe-area-inset-top)) 18px 24px;z-index:60;background:rgba(255,253,248,.98)}}
  body.menu-open aside{{transform:translateX(0)}}
  .backdrop{{display:block;position:fixed;inset:0;background:rgba(20,16,10,.42);opacity:0;pointer-events:none;transition:opacity .22s ease;z-index:50}}
  body.menu-open .backdrop{{opacity:1;pointer-events:auto}}
  .close-menu{{display:inline-flex;align-items:center;justify-content:center;float:right;border:1px solid var(--line);background:var(--soft);border-radius:999px;min-height:36px;padding:0 12px;font-weight:900}}
  aside h1{{font-size:38px;clear:both}}
  aside .sub{{font-size:14px}}
  main{{padding:8px;height:calc(100dvh - 58px - env(safe-area-inset-top))}}
  .viewer-shell{{height:100%;border-radius:18px}}
  .viewer-top{{padding:10px 12px}}
  #current-title{{display:none}}
}}
</style>
</head>
<body>
<div class="mobile-bar"><button id="menu-button" class="menu-button" type="button" aria-label="Browse lessons" aria-controls="lesson-menu" aria-expanded="false"><span class="hamburger" aria-hidden="true"><span></span></span></button><div class="site-title">Daily English Lessons</div></div>
<div id="backdrop" class="backdrop" aria-hidden="true"></div>
<div class="app">
  <aside id="lesson-menu" aria-label="Lesson archive navigation">
    <button id="close-menu" class="close-menu" type="button">Close</button>
    <h1>Daily English<br>Lessons</h1>
    <p class="sub">A readable archive for daily English lessons plus weekly/monthly reviews.</p>
    <span class="badge">Last site build: {html.escape(generated)}</span>
    <h2>Today / Latest</h2>{today_nav}
    <h2>Old lessons</h2>{old_nav}
    <h2>Weekly reviews</h2>{weekly_nav}
    <h2>Monthly reviews</h2>{monthly_nav}
  </aside>
  <main>
    <div class="viewer-shell">
      <div class="viewer-top"><div id="current-title">{html.escape(latest_title)}</div></div>
      <iframe id="viewer" src="{html.escape(latest_url)}" title="English lesson viewer"></iframe>
    </div>
  </main>
</div>
<script>
const links=[...document.querySelectorAll('.nav-item')];
const viewer=document.getElementById('viewer');
const title=document.getElementById('current-title');
const menuButton=document.getElementById('menu-button');
const closeMenu=document.getElementById('close-menu');
const backdrop=document.getElementById('backdrop');
function setMenu(opened){{
  document.body.classList.toggle('menu-open', opened);
  menuButton?.setAttribute('aria-expanded', opened ? 'true' : 'false');
}}
function select(url){{
  const link=links.find(a=>a.dataset.url===url)||links[0];
  if(!link)return;
  links.forEach(a=>a.classList.toggle('active',a===link));
  viewer.src=link.dataset.url;
  const text=link.querySelector('.title')?.textContent||'English lesson';
  title.textContent=text;
  if(location.hash!=='#'+link.dataset.url)history.replaceState(null,'','#'+link.dataset.url);
  setMenu(false);
}}
links.forEach(a=>a.addEventListener('click',e=>{{e.preventDefault();select(a.dataset.url)}}));
menuButton?.addEventListener('click',()=>setMenu(true));
closeMenu?.addEventListener('click',()=>setMenu(false));
backdrop?.addEventListener('click',()=>setMenu(false));
document.addEventListener('keydown',e=>{{if(e.key==='Escape')setMenu(false)}});
select(decodeURIComponent(location.hash.slice(1))||{latest_url!r});
</script>
</body>
</html>'''


def main() -> None:
    items = collect_items()
    copy_items(items)
    (ROOT / 'index.html').write_text(build_index(items), encoding='utf-8')
    print(f'Built site with {len([x for x in items if x.kind == "daily"])} daily lessons, {len([x for x in items if x.kind == "weekly"])} weekly reviews, {len([x for x in items if x.kind == "monthly"])} monthly reviews')
    print(ROOT / 'index.html')


if __name__ == '__main__':
    main()
