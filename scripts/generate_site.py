#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
import shutil
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = Path('/opt/data/english-lessons')
LESSONS_DIR = ROOT / 'lessons'
REVIEWS_DIR = ROOT / 'reviews'
OLD_DAILY_LIMIT = 9  # plus Today / Latest = 10 daily lesson links total
COLLAPSED_DAILY_TOTAL = 5  # initial nav shows 5 total, then “…” expands the rest
TRANSLATION_CACHE = Path('/opt/data/.cache/5dailywords_native_translations.json')
NATIVE_LANGS = {
    'tc': {'label': '繁體中文', 'target': 'zh-TW', 'summary': '文章摘要', 'definition': '中文定義：'},
    'sc': {'label': '简体中文', 'target': 'zh-CN', 'summary': '文章摘要', 'definition': '简体中文定义：'},
    'ko': {'label': '한국어', 'target': 'ko', 'summary': '기사 요약', 'definition': '한국어 정의:'},
    'ja': {'label': '日本語', 'target': 'ja', 'summary': '記事要約', 'definition': '日本語の定義：'},
}


def load_translation_cache() -> dict[str, str]:
    try:
        return json.loads(TRANSLATION_CACHE.read_text(encoding='utf-8'))
    except Exception:
        return {}


def save_translation_cache(cache: dict[str, str]) -> None:
    TRANSLATION_CACHE.parent.mkdir(parents=True, exist_ok=True)
    TRANSLATION_CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=2, sort_keys=True), encoding='utf-8')


def translate_native(text: str, target: str, cache: dict[str, str]) -> str:
    clean = ' '.join(html.unescape(text).split())
    if not clean or target == 'zh-TW':
        return clean
    key = f'zh-TW|{target}|{clean}'
    if key in cache:
        return cache[key]
    try:
        url = (
            'https://translate.googleapis.com/translate_a/single?client=gtx&sl=zh-TW'
            f'&tl={urllib.parse.quote(target)}&dt=t&q={urllib.parse.quote(clean)}'
        )
        with urllib.request.urlopen(url, timeout=20) as response:
            data = json.loads(response.read().decode('utf-8'))
        translated = ''.join(part[0] for part in data[0]).strip()
    except Exception:
        translated = clean
    cache[key] = translated
    return translated


def native_attrs(text: str, cache: dict[str, str]) -> str:
    values = {'tc': ' '.join(html.unescape(text).split())}
    values['sc'] = translate_native(values['tc'], 'zh-CN', cache)
    values['ko'] = translate_native(values['tc'], 'ko', cache)
    values['ja'] = translate_native(values['tc'], 'ja', cache)
    return ' '.join(f'data-native-{code}="{html.escape(value, quote=True)}"' for code, value in values.items())


def enrich_native_language(text: str, cache: dict[str, str]) -> str:
    """Add static multilingual translation attributes to Chinese translation sections."""
    if 'data-native-lang-script' in text:
        return text

    text = re.sub(
        r'<h2>文章摘要</h2>',
        '<h2 class="native-heading" data-native-tc="文章摘要" data-native-sc="文章摘要" data-native-ko="기사 요약" data-native-ja="記事要約">文章摘要</h2>',
        text,
        count=1,
    )

    def zh_summary_repl(match: re.Match[str]) -> str:
        paragraph = match.group(1)
        plain = re.sub(r'<[^>]+>', '', paragraph)
        attrs = native_attrs(plain, cache)
        return f'<p class="native-text" {attrs}>{html.escape(html.unescape(plain))}</p>'

    text = re.sub(
        r'<section class="zh-box zh">(.*?)</section>',
        lambda section: re.sub(r'<p>(.*?)</p>', zh_summary_repl, section.group(0), flags=re.DOTALL),
        text,
        count=1,
        flags=re.DOTALL,
    )

    def definition_repl(match: re.Match[str]) -> str:
        body_html = match.group(1)
        plain = re.sub(r'<[^>]+>', '', body_html)
        attrs = native_attrs(plain, cache)
        return (
            f'<p class="def zh native-text" data-native-role="definition" {attrs}>'
            f'<span class="native-body">{html.escape(html.unescape(plain))}</span></p>'
        )

    text = re.sub(
        r'<p class="def zh">(?:<strong>中文定義：</strong>)?(.*?)</p>',
        definition_repl,
        text,
        flags=re.DOTALL,
    )

    script = '''<script data-native-lang-script>
(function(){
  const allowed = new Set(['tc','sc','ko','ja']);
  const params = new URLSearchParams(location.search);
  let lang = params.get('native') || localStorage.getItem('nativeLanguage') || 'tc';
  if(!allowed.has(lang)) lang = 'tc';
  document.documentElement.dataset.nativeLanguage = lang;
  localStorage.setItem('nativeLanguage', lang);
  function applyNativeLanguage(){
    document.querySelectorAll('.native-heading').forEach(el => {
      const value = el.dataset['native' + lang.charAt(0).toUpperCase() + lang.slice(1)] || el.dataset.nativeTc;
      if(value) el.textContent = value;
    });
    document.querySelectorAll('.native-text').forEach(el => {
      const value = el.dataset['native' + lang.charAt(0).toUpperCase() + lang.slice(1)] || el.dataset.nativeTc;
      const body = el.querySelector('.native-body');
      if(body) body.textContent = value;
      else if(value) el.textContent = value;
    });
  }
  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', applyNativeLanguage);
  else applyNativeLanguage();
})();
</script>'''
    return text.replace('</body>', script + '\n</body>') if '</body>' in text else text + script


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
    # Undated legacy/test lessons should never outrank date-based daily lessons.
    return path.stem, '0000-' + path.stem


def collect_items() -> list[Item]:
    items: list[Item] = []
    for src in sorted(SOURCE_DIR.glob('*.html')):
        kind = infer_kind(src)
        label, key = infer_date(src)
        dest_dir = REVIEWS_DIR if kind in {'weekly', 'monthly'} else LESSONS_DIR
        prefix = 'reviews' if kind in {'weekly', 'monthly'} else 'lessons'
        items.append(Item(src, dest_dir / src.name, f'{prefix}/{src.name}', parse_title(src), kind, label, key))
    return sorted(items, key=lambda x: x.sort_key, reverse=True)


def standalone_nav_html(items: list[Item], current: Item) -> str:
    daily = [x for x in items if x.kind == 'daily'][:OLD_DAILY_LIMIT + 1]
    prefix = './' if current.dest.parent == LESSONS_DIR else '../lessons/'
    contact_href = './contact-us.html' if current.dest.parent == ROOT else '../contact-us.html'
    links = []
    for idx, x in enumerate(daily):
        href = prefix + x.dest.name
        active = ' active' if x.dest.name == current.dest.name else ''
        collapsed = ' standalone-nav-extra' if idx >= COLLAPSED_DAILY_TOTAL else ''
        label = 'Today / Latest' if idx == 0 else x.date_label
        links.append(
            f'<a class="standalone-nav-link{active}{collapsed}" href="{html.escape(href)}">'
            f'<span class="standalone-date">{html.escape(label)}</span>'
            f'<span class="standalone-title">{html.escape(x.title)}</span></a>'
        )
    if len(daily) > COLLAPSED_DAILY_TOTAL:
        links.insert(
            COLLAPSED_DAILY_TOTAL,
            '<button id="standalone-expand-lessons" class="standalone-expand-lessons" type="button" '
            'aria-expanded="false" aria-label="Show more lessons">…</button>'
        )
    links.append(f'<a class="standalone-contact-link" href="{html.escape(contact_href)}">Contact us</a>')
    links_html = '\n'.join(links) or '<p class="standalone-empty">No daily lessons yet.</p>'
    return f'''<script id="standalone-embedded-detector">if(new URLSearchParams(location.search).has('embedded'))document.documentElement.classList.add('standalone-embedded');</script>
<style id="standalone-lesson-nav-style">
.standalone-nav-bar{{position:fixed;top:0;left:0;right:0;z-index:9998;display:flex;align-items:center;gap:10px;min-height:58px;padding:8px 12px;background:rgba(255,253,248,.96);border-bottom:1px solid #ded3c4;box-shadow:0 8px 24px rgba(36,24,12,.08);backdrop-filter:blur(10px);font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}
html:not(.standalone-embedded) body{{padding-top:70px!important}}
html.standalone-embedded .standalone-nav-bar,html.standalone-embedded .standalone-backdrop,html.standalone-embedded .standalone-drawer{{display:none!important}}
.standalone-menu-button{{border:1px solid #ded3c4;background:#173f5f;color:white;border-radius:12px;width:42px;height:40px;padding:0;display:inline-flex;align-items:center;justify-content:center;flex:0 0 auto}}
.standalone-hamburger{{display:block;width:19px;height:14px;position:relative}}
.standalone-hamburger::before,.standalone-hamburger::after,.standalone-hamburger span{{content:"";position:absolute;left:0;width:100%;height:2px;background:currentColor;border-radius:999px}}
.standalone-hamburger::before{{top:0}}.standalone-hamburger span{{top:6px}}.standalone-hamburger::after{{bottom:0}}
.standalone-site-title{{font-family:ui-serif,Georgia,serif;font-weight:950;font-size:clamp(23px,6vw,32px);letter-spacing:-.04em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:#1f1c18;min-width:0;flex:1}}
.standalone-language-control{{display:inline-flex;align-items:center;gap:8px;min-height:38px;padding:6px 8px;border:1px solid #ded3c4;border-radius:999px;background:rgba(255,253,248,.92);margin-left:auto;flex:0 0 auto}}
.standalone-globe-icon{{width:20px;height:20px;color:#173f5f;flex:0 0 auto}}
.standalone-language-divider{{width:1px;height:22px;background:#ded3c4;display:block}}
.standalone-native-select{{border:0;background:transparent;color:#1f1c18;font-weight:850;font-size:13px;outline:none;max-width:86px}}
.standalone-backdrop{{position:fixed;inset:0;z-index:9998;background:rgba(20,16,10,.42);opacity:0;pointer-events:none;transition:opacity .2s ease}}
.standalone-drawer{{position:fixed;top:0;bottom:0;left:0;z-index:9999;width:min(88vw,360px);height:100dvh;overflow:auto;transform:translateX(-105%);transition:transform .22s ease;background:#fffdf8;border-right:1px solid #ded3c4;box-shadow:0 18px 45px rgba(36,24,12,.18);padding:calc(18px + env(safe-area-inset-top)) 18px 24px;font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}
body.standalone-menu-open .standalone-drawer{{transform:translateX(0)}}body.standalone-menu-open .standalone-backdrop{{opacity:1;pointer-events:auto}}
.standalone-drawer-top{{display:block;margin:-8px -6px 0;padding:8px 6px 2px;border:0;background:transparent;text-align:left;color:inherit;width:calc(100% + 12px);cursor:pointer}}
.standalone-drawer-top:focus-visible{{outline:3px solid rgba(23,63,95,.35);outline-offset:3px;border-radius:16px}}
.standalone-drawer h2{{margin:18px 0 4px;font-size:30px;line-height:1.05;font-family:ui-serif,Georgia,serif;color:#1f1c18}}
.standalone-drawer p{{margin:0 0 14px;color:#6d6459;font-size:14px}}.standalone-drawer h3{{font-size:13px;letter-spacing:.12em;text-transform:uppercase;color:#173f5f;margin:20px 0 10px}}
.standalone-nav-link{{display:block;text-decoration:none;color:#1f1c18;padding:12px;border:1px solid #ded3c4;background:#fffaf2;border-radius:16px;margin:9px 0}}
.standalone-nav-extra{{display:none}}
body.standalone-lessons-expanded .standalone-nav-extra{{display:block}}
.standalone-expand-lessons{{display:block;width:100%;min-height:42px;margin:9px 0;padding:8px 12px;border:1px dashed #ded3c4;background:#fffaf2;border-radius:16px;color:#173f5f;font-size:24px;font-weight:950;line-height:1;cursor:pointer;text-align:left}}
body.standalone-lessons-expanded .standalone-expand-lessons{{display:none}}
.standalone-contact-link{{display:block;text-align:left;text-decoration:none;color:#173f5f;font-weight:900;padding:10px 12px;margin:2px 0 12px;border-radius:999px}}
.standalone-contact-link:hover{{background:#efe4d3}}
.standalone-nav-link.active{{border-color:rgba(23,63,95,.65);box-shadow:0 8px 20px rgba(45,31,16,.08)}}.standalone-date{{display:block;color:#173f5f;font-size:12px;font-weight:900;letter-spacing:.08em;text-transform:uppercase;margin-bottom:4px}}.standalone-title{{display:block;font-family:ui-serif,Georgia,serif;font-size:17px;line-height:1.35}}
</style>
<div class="standalone-nav-bar"><button id="standalone-menu-button" class="standalone-menu-button" type="button" aria-label="Browse lessons" aria-controls="standalone-lesson-menu" aria-expanded="false"><span class="standalone-hamburger" aria-hidden="true"><span></span></span></button><div class="standalone-site-title">Daily English</div><div class="standalone-language-control" aria-label="Native language selector"><svg class="standalone-globe-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M3 12h18M12 3c2.4 2.6 3.6 5.6 3.6 9S14.4 18.4 12 21M12 3C9.6 5.6 8.4 8.6 8.4 12S9.6 18.4 12 21" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg><span class="standalone-language-divider" aria-hidden="true"></span><select id="standalone-native-language" class="standalone-native-select" aria-label="Native language"><option value="tc">繁體中文</option><option value="sc">简体中文</option><option value="ko">한국어</option><option value="ja">日本語</option></select></div></div>
<div id="standalone-backdrop" class="standalone-backdrop" aria-hidden="true"></div>
<nav id="standalone-lesson-menu" class="standalone-drawer" aria-label="Lesson navigation"><button id="standalone-drawer-top" class="standalone-drawer-top" type="button" aria-label="Hide lesson navigation"><h2>Daily English</h2><p>Updates 9 AM Hong Kong / Taiwan time</p><h3>Daily lessons</h3></button>{links_html}</nav>
<script id="standalone-lesson-nav-script">
(() => {{
  const btn=document.getElementById('standalone-menu-button');
  const backdrop=document.getElementById('standalone-backdrop');
  const drawerTop=document.getElementById('standalone-drawer-top');
  const expandLessons=document.getElementById('standalone-expand-lessons');
  const nativeSelect=document.getElementById('standalone-native-language');
  const allowedNative=new Set(['tc','sc','ko','ja']);
  let nativeLanguage=(new URLSearchParams(location.search).get('native'))||localStorage.getItem('nativeLanguage')||'tc';
  if(!allowedNative.has(nativeLanguage))nativeLanguage='tc';
  if(document.querySelector('.standalone-nav-link.active.standalone-nav-extra'))document.body.classList.add('standalone-lessons-expanded');
  const setMenu=open=>{{document.body.classList.toggle('standalone-menu-open',open);btn?.setAttribute('aria-expanded',open?'true':'false')}};
  const nativeKey=lang=>'native'+lang.charAt(0).toUpperCase()+lang.slice(1);
  const applyNativeLanguage=()=>{{
    document.documentElement.dataset.nativeLanguage=nativeLanguage;
    localStorage.setItem('nativeLanguage',nativeLanguage);
    if(nativeSelect)nativeSelect.value=nativeLanguage;
    document.querySelectorAll('.native-heading').forEach(el=>{{const value=el.dataset[nativeKey(nativeLanguage)]||el.dataset.nativeTc;if(value)el.textContent=value;}});
    document.querySelectorAll('.native-text').forEach(el=>{{const value=el.dataset[nativeKey(nativeLanguage)]||el.dataset.nativeTc;const body=el.querySelector('.native-body');if(body)body.textContent=value;else if(value)el.textContent=value;}});
  }};
  nativeSelect?.addEventListener('change',()=>{{nativeLanguage=allowedNative.has(nativeSelect.value)?nativeSelect.value:'tc';applyNativeLanguage();}});
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',applyNativeLanguage);else applyNativeLanguage();
  btn?.addEventListener('click',()=>setMenu(true)); backdrop?.addEventListener('click',()=>setMenu(false)); drawerTop?.addEventListener('click',()=>setMenu(false));
  expandLessons?.addEventListener('click',()=>{{document.body.classList.add('standalone-lessons-expanded');expandLessons.setAttribute('aria-expanded','true')}});
  document.addEventListener('keydown',e=>{{if(e.key==='Escape')setMenu(false)}});
}})();
</script>'''


def inject_standalone_nav(text: str, items: list[Item], current: Item) -> str:
    if 'id="standalone-lesson-menu"' in text or '<body' not in text.lower():
        return text
    nav = standalone_nav_html(items, current)
    return re.sub(r'(<body[^>]*>)', r'\1\n' + nav, text, count=1, flags=re.IGNORECASE)


def copy_items(items: list[Item]) -> None:
    LESSONS_DIR.mkdir(parents=True, exist_ok=True)
    REVIEWS_DIR.mkdir(parents=True, exist_ok=True)
    cache = load_translation_cache()
    for item in items:
        shutil.copy2(item.src, item.dest)
        text = item.dest.read_text(encoding='utf-8', errors='ignore')
        if item.kind == 'daily':
            text = enrich_native_language(text, cache)
        item.dest.write_text(inject_standalone_nav(text, items, item), encoding='utf-8')
    save_translation_cache(cache)


def nav_link(x: Item, class_name: str = 'nav-item') -> str:
    return (
        f'<a class="{class_name}" href="#{html.escape(x.rel_url)}" data-url="{html.escape(x.rel_url)}">'
        f'<span class="date">{html.escape(x.date_label)}</span>'
        f'<span class="title">{html.escape(x.title)}</span>'
        f'</a>'
    )


def nav(items: list[Item], kind: str, limit: int | None = None) -> str:
    xs = [x for x in items if x.kind == kind]
    if limit is not None:
        xs = xs[:limit]
    if not xs:
        return '<p class="empty">No items yet.</p>'
    return '\n'.join(nav_link(x) for x in xs)


def build_index(items: list[Item]) -> str:
    daily_items = [x for x in items if x.kind == 'daily']
    latest = daily_items[0] if daily_items else None
    old_daily = daily_items[1:1 + OLD_DAILY_LIMIT]
    latest_url = latest.rel_url if latest else ''
    latest_title = latest.title if latest else 'No daily lesson yet'
    generated = datetime.now().strftime('%Y-%m-%d %H:%M')
    today_nav = nav([latest], 'daily') if latest else '<p class="empty">No latest lesson yet.</p>'
    collapsed_old_count = max(COLLAPSED_DAILY_TOTAL - (1 if latest else 0), 0)
    old_visible = old_daily[:collapsed_old_count]
    old_extra = old_daily[collapsed_old_count:OLD_DAILY_LIMIT]
    old_nav_parts = [nav_link(x) for x in old_visible]
    if old_extra:
        old_nav_parts.append('<button id="expand-lessons" class="expand-lessons" type="button" aria-expanded="false" aria-label="Show more lessons">…</button>')
        old_nav_parts.extend(nav_link(x, 'nav-item nav-extra') for x in old_extra)
    old_nav_parts.append('<a class="contact-link" href="contact-us.html">Contact us</a>')
    old_nav = '\n'.join(old_nav_parts) or '<p class="empty">No previous lessons yet.</p>'
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Daily English</title>
<style>
:root{{--bg:#f4f0e8;--paper:#fffdf8;--ink:#1f1c18;--muted:#6d6459;--line:#ded3c4;--accent:#173f5f;--soft:#efe4d3;--shadow:0 18px 45px rgba(36,24,12,.12)}}
*{{box-sizing:border-box}}
body{{margin:0;background:radial-gradient(circle at 0 0,rgba(23,63,95,.13),transparent 30rem),radial-gradient(circle at 100% 100%,rgba(143,63,47,.12),transparent 28rem),var(--bg);color:var(--ink);font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}
button{{font:inherit}}
.drawer-top{{display:block;margin:0;padding:0;border:0;background:transparent;text-align:left;color:inherit;width:100%}}
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
.nav-extra{{display:none}}
body.lessons-expanded .nav-extra{{display:block}}
.expand-lessons{{display:block;width:100%;min-height:42px;margin:9px 0;padding:8px 12px;border:1px dashed var(--line);background:var(--paper);border-radius:16px;color:var(--accent);font-size:24px;font-weight:950;line-height:1;cursor:pointer;text-align:left}}
body.lessons-expanded .expand-lessons{{display:none}}
.contact-link{{display:block;text-align:left;text-decoration:none;color:var(--accent);font-weight:900;padding:10px 12px;margin:2px 0 12px;border-radius:999px}}
.contact-link:hover{{background:var(--soft)}}
.nav-item:hover,.nav-item.active{{border-color:rgba(23,63,95,.55);transform:translateY(-1px);box-shadow:0 8px 20px rgba(45,31,16,.08)}}
.date{{display:block;color:var(--accent);font-size:12px;font-weight:900;letter-spacing:.08em;text-transform:uppercase;margin-bottom:4px}}
.title{{display:block;font-family:ui-serif,Georgia,serif;font-size:17px;line-height:1.35}}
.empty{{color:var(--muted);font-size:14px}}
.viewer-shell{{background:var(--paper);border:1px solid var(--line);border-radius:26px;box-shadow:var(--shadow);overflow:hidden;height:calc(100vh - 44px);display:flex;flex-direction:column}}
iframe{{width:100%;flex:1;border:0;background:white}}
.language-control{{position:fixed;top:14px;right:18px;z-index:45;display:inline-flex;align-items:center;gap:10px;min-height:42px;padding:7px 10px;border:1px solid var(--line);border-radius:999px;background:rgba(255,253,248,.94);box-shadow:0 10px 25px rgba(36,24,12,.1);backdrop-filter:blur(10px)}}
.language-control-mobile{{display:none}}
.globe-icon{{width:22px;height:22px;color:var(--accent);flex:0 0 auto}}
.language-divider{{width:1px;height:24px;background:var(--line);display:block}}
.native-select{{border:0;background:transparent;color:var(--ink);font-weight:850;font-size:14px;outline:none;max-width:132px}}
@media(max-width:860px){{
  body{{padding-top:calc(58px + env(safe-area-inset-top));overflow:hidden}}
  .mobile-bar{{display:flex;position:fixed;top:0;left:0;right:0;height:calc(58px + env(safe-area-inset-top));padding:env(safe-area-inset-top) 12px 8px;align-items:center;gap:10px;background:rgba(255,253,248,.96);border-bottom:1px solid var(--line);backdrop-filter:blur(10px);z-index:40}}
  .menu-button{{border:1px solid var(--line);background:var(--accent);color:white;border-radius:12px;width:42px;height:40px;padding:0;display:inline-flex;align-items:center;justify-content:center;font-weight:900;flex:0 0 auto}}
  .hamburger{{display:block;width:19px;height:14px;position:relative}}
  .hamburger::before,.hamburger::after,.hamburger span{{content:"";position:absolute;left:0;width:100%;height:2px;background:currentColor;border-radius:999px}}
  .hamburger::before{{top:0}}
  .hamburger span{{top:6px}}
  .hamburger::after{{bottom:0}}
  .site-title{{font-family:ui-serif,Georgia,serif;font-weight:950;font-size:clamp(22px,5.6vw,30px);letter-spacing:-.045em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-width:0;flex:1}}
  .language-control{{position:static;min-height:38px;padding:6px 8px;gap:7px;box-shadow:none;background:transparent;border-color:var(--line);margin-left:auto;flex:0 0 auto}}
  .language-control-mobile{{display:inline-flex}}
  .language-control-desktop{{display:none}}
  .globe-icon{{width:20px;height:20px}}.language-divider{{height:22px}}.native-select{{max-width:86px;font-size:13px}}
  .app{{display:block;min-height:calc(100vh - 58px - env(safe-area-inset-top))}}
  aside{{position:fixed;top:0;bottom:0;left:0;width:min(88vw,360px);height:100dvh;transform:translateX(-105%);transition:transform .22s ease;box-shadow:var(--shadow);border-right:1px solid var(--line);padding:calc(18px + env(safe-area-inset-top)) 18px 24px;z-index:60;background:rgba(255,253,248,.98)}}
  .drawer-top{{display:block;margin:-8px -6px 0;padding:8px 6px 2px;border:0;background:transparent;text-align:left;color:inherit;width:calc(100% + 12px);cursor:pointer}}
  .drawer-top:focus-visible{{outline:3px solid rgba(23,63,95,.35);outline-offset:3px;border-radius:16px}}
  body.menu-open aside{{transform:translateX(0)}}
  .backdrop{{display:block;position:fixed;inset:0;background:rgba(20,16,10,.42);opacity:0;pointer-events:none;transition:opacity .22s ease;z-index:50}}
  body.menu-open .backdrop{{opacity:1;pointer-events:auto}}
  aside h1{{font-size:38px}}
  aside .sub{{font-size:14px}}
  main{{padding:8px;height:calc(100dvh - 58px - env(safe-area-inset-top))}}
  .viewer-shell{{height:100%;border-radius:18px}}
}}
</style>
</head>
<body>
<div class="mobile-bar"><button id="menu-button" class="menu-button" type="button" aria-label="Browse lessons" aria-controls="lesson-menu" aria-expanded="false"><span class="hamburger" aria-hidden="true"><span></span></span></button><div class="site-title">Daily English</div><div class="language-control language-control-mobile" aria-label="Native language selector"><svg class="globe-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M3 12h18M12 3c2.4 2.6 3.6 5.6 3.6 9S14.4 18.4 12 21M12 3C9.6 5.6 8.4 8.6 8.4 12S9.6 18.4 12 21" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg><span class="language-divider" aria-hidden="true"></span><select id="native-language-mobile" class="native-select" aria-label="Native language"><option value="tc">繁體中文</option><option value="sc">简体中文</option><option value="ko">한국어</option><option value="ja">日本語</option></select></div></div>
<div class="language-control language-control-desktop" aria-label="Native language selector"><svg class="globe-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M3 12h18M12 3c2.4 2.6 3.6 5.6 3.6 9S14.4 18.4 12 21M12 3C9.6 5.6 8.4 8.6 8.4 12S9.6 18.4 12 21" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg><span class="language-divider" aria-hidden="true"></span><select id="native-language-desktop" class="native-select" aria-label="Native language"><option value="tc">繁體中文</option><option value="sc">简体中文</option><option value="ko">한국어</option><option value="ja">日本語</option></select></div>
<div id="backdrop" class="backdrop" aria-hidden="true"></div>
<div class="app">
  <aside id="lesson-menu" aria-label="Lesson archive navigation">
    <button id="drawer-top" class="drawer-top" type="button" aria-label="Hide lesson navigation"><h1>Daily English</h1>
    <p class="sub">Updates 9 AM Hong Kong / Taiwan time</p>
    <h2>Today / Latest</h2></button>{today_nav}
    <h2>Daily lessons</h2>{old_nav}
  </aside>
  <main>
    <div class="viewer-shell">
      <iframe id="viewer" src="{html.escape(latest_url)}?embedded=1" title="English lesson viewer"></iframe>
    </div>
  </main>
</div>
<script>
const links=[...document.querySelectorAll('.nav-item')];
const viewer=document.getElementById('viewer');
const menuButton=document.getElementById('menu-button');
const drawerTop=document.getElementById('drawer-top');
const expandLessons=document.getElementById('expand-lessons');
const backdrop=document.getElementById('backdrop');
const nativeSelects=[...document.querySelectorAll('.native-select')];
const allowedNative=new Set(['tc','sc','ko','ja']);
let nativeLanguage=localStorage.getItem('nativeLanguage')||'tc';
if(!allowedNative.has(nativeLanguage))nativeLanguage='tc';
function lessonSrc(url){{return url+(url.includes('?')?'&':'?')+'embedded=1&native='+encodeURIComponent(nativeLanguage)}}
function syncNativeSelects(){{nativeSelects.forEach(select=>select.value=nativeLanguage)}}
function setMenu(opened){{
  document.body.classList.toggle('menu-open', opened);
  menuButton?.setAttribute('aria-expanded', opened ? 'true' : 'false');
}}
function select(url){{
  const link=links.find(a=>a.dataset.url===url)||links[0];
  if(!link)return;
  links.forEach(a=>a.classList.toggle('active',a===link));
  if(link.classList.contains('nav-extra'))document.body.classList.add('lessons-expanded');
  viewer.src=lessonSrc(link.dataset.url);
  if(location.hash!=='#'+link.dataset.url)history.replaceState(null,'','#'+link.dataset.url);
  setMenu(false);
}}
links.forEach(a=>a.addEventListener('click',e=>{{e.preventDefault();select(a.dataset.url)}}));
nativeSelects.forEach(selectEl=>selectEl.addEventListener('change',()=>{{
  nativeLanguage=allowedNative.has(selectEl.value)?selectEl.value:'tc';
  localStorage.setItem('nativeLanguage',nativeLanguage);
  syncNativeSelects();
  const active=links.find(a=>a.classList.contains('active'))||links[0];
  if(active)viewer.src=lessonSrc(active.dataset.url);
}}));
menuButton?.addEventListener('click',()=>setMenu(true));
drawerTop?.addEventListener('click',()=>setMenu(false));
expandLessons?.addEventListener('click',()=>{{document.body.classList.add('lessons-expanded');expandLessons.setAttribute('aria-expanded','true')}});
backdrop?.addEventListener('click',()=>setMenu(false));
document.addEventListener('keydown',e=>{{if(e.key==='Escape')setMenu(false)}});
syncNativeSelects();
select(decodeURIComponent(location.hash.slice(1)).replace(/[?&]embedded=1.*$/,'')||{latest_url!r});
</script>
</body>
</html>'''


def main() -> None:
    items = collect_items()
    copy_items(items)
    (ROOT / 'index.html').write_text(build_index(items), encoding='utf-8')
    print(f'Built site with {len([x for x in items if x.kind == "daily"])} daily lessons; navigation shows up to 10 daily lesson links only')
    print(ROOT / 'index.html')


if __name__ == '__main__':
    main()
