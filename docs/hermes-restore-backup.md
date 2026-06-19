# Hermes Lesson Preferences Restore Backup

Generated: 2026-06-15T03:01:21Z

This file is meant to be kept outside Hermes. If Hermes local data disappears, give this file to a fresh Hermes agent and ask it to restore the lesson workflows, preferences, cron jobs, and website publishing behavior.

**Important:** This file intentionally contains **no secrets**. It does not include Vercel tokens, GitHub tokens, Telegram IDs beyond public/contextual references, or passwords.

---

## One-shot restore prompt

Copy/paste this section into a new Hermes session:

```text
Please restore my English and Chinese lesson website preferences and automation using the backup below.

Do not ask me to repeat preferences unless something is missing. Recreate/update Hermes skills, cron prompts, verifier scripts, local wrappers, and website generators as needed. Do not store or print secrets. Use /opt/data/.env for VERCEL_TOKEN and optional GITHUB_TOKEN. Preserve the live public URLs and GitHub repo names below.

Restore from this backup:
[PASTE THE REST OF THIS FILE]
```

---

## Public sites and repos

- Public website branding is neutral. Do not include personal names in public titles, subtitles, page body, footers, navigation, README files, restore docs copied to repos, generated pages, or future site updates. Use `Daily English Lessons` and `Daily Chinese` / `Daily Chinese Lessons` instead of personal wording.
- 5dailywords mobile/top header branding should display the shorter title `Daily English` instead of `Daily English Lessons` so it does not get cut off on phones.
- 5dailywords navigation drawer should not include an internal Close button; users should dismiss it by tapping/clicking the backdrop/main page area, selecting a lesson, pressing Escape, or tapping the blank/header area above the first nav link.
- 5dailywords English vocabulary cards should order detail rows as unlabeled English definition, then `In article:`, then unlabeled native-language definition; do not show `English definition:` or `中文定義:` labels.
- 5dailywords English lessons should make the 5th/final vocabulary item one level harder than the first four when the article supports it, using a genuine C1-ish article term or precise technical phrase.

## GitHub backup copies

This restore document is also saved inside the existing lesson repositories at:

- Chinese repo: `docs/hermes-restore-backup.md`
- English repo: `docs/hermes-restore-backup.md`

The publish scripts refresh these copies during site publishing.

### Chinese lessons

- Live site: https://chinese-lessons-web.vercel.app
- GitHub repo: https://github.com/Windswell284/Chinese-lessons-web
- Local source lessons: `/opt/data/chinese-lessons/`
- Local generated website: `/opt/data/chinese-lessons-web/`
- Publish wrapper expected at: `/opt/data/scripts/publish_chinese_lessons_site.py`
- Real publish script previously lived under: `/opt/data/.hermes/scripts/publish_chinese_lessons_site.py`

### English lessons

- Live site: https://5dailywords.com
- Legacy Vercel alias: https://english-lessons-web-blue.vercel.app
- GitHub repo: https://github.com/Windswell284/English-lessons-web
- Local source lessons: `/opt/data/english-lessons/`
- Local generated website: `/opt/data/english-lessons-web/`
- Publish wrapper expected at: `/opt/data/scripts/publish_english_lessons_site.py`
- Real publish script previously lived under: `/opt/data/.hermes/scripts/publish_english_lessons_site.py`

---

## Secure environment

Use `/opt/data/.env` for secrets. Do **not** commit this file or include its values in chat.

Expected variable names:

```env
VERCEL_TOKEN=...
GITHUB_TOKEN=...
```

Permissions should be restrictive:

```bash
chmod 600 /opt/data/.env
```

Publish scripts should self-load `/opt/data/.env` so scheduled jobs do not depend on the gateway process already having these environment variables.

---

## General website preferences

- Mobile-friendly lesson websites are preferred over Telegram-only attachments.
- Website navigation should be lesson-first on mobile.
- Use a 3-line hamburger menu for direct/standalone lesson pages.
- Direct lesson pages must have navigation. Embedded homepage lesson views should hide duplicate standalone nav via `?embedded=1`, but only when the lesson is actually inside the homepage iframe; if an iPhone/Safari direct URL opens with `?embedded=1` outside an iframe, the standalone nav should still appear.
- Menus should be daily-only unless explicitly restored.
- Daily lesson navigation should be capped at 10 total daily links; nav panels initially show Today / Latest plus 5 past lesson links (6 total when available), then a left-aligned `…` control expands the remaining links up to the 10-link cap.
- Do not show weekly/monthly review sections in website navigation unless explicitly asked.
- Do not show old/test pages in public navigation after a test is accepted.
- Remove accepted test pages from source and generated folders, rebuild, publish, and verify old URLs return 404.

---

## Chinese lesson preferences

Skill name to restore/update: `traditional-chinese-current-events`

### Content format

- Traditional Chinese current-events lesson, preferably based on CNA when suitable.
- Do not reproduce full copyrighted articles.
- Include source/title/date/link and short excerpts only.
- Public page labels should be only `Easy` and `Challenge`; default to Easy and do not show Chinese grade labels.
- Use the same weekly cadence logic as the Daily English lesson, but with this Daily Chinese long-run topic mix: about 20% world/geopolitics, 20% business/economy, 15% technology/AI, 15% science/health/climate, 25% culture/society/lifestyle, and 5% wildcard/human-interest. Default weekly cadence: Monday business, Tuesday world affairs, Wednesday science/health/climate, Thursday tech/AI, Friday culture/society/lifestyle, Saturday world or biggest major headline, Sunday lighter/wildcard. Choose vocabulary-rich Traditional Chinese articles from the rotating category; avoid several consecutive geopolitics lessons unless major news requires it.
- No quiz unless explicitly requested.
- Summary heading: `中文摘要`; Easy summary should live in this normal section, not an extra nested panel/card.
- Vocabulary heading: `Key Words`.
- Exactly 5 Easy vocabulary cards and exactly 5 Challenge vocabulary cards on public generated lesson pages.
- Each vocabulary card must include:
  - word/phrase
  - Zhuyin
  - Chinese definition
  - English definition
  - `原文句子` with the target word highlighted using `<mark>` when possible
- Do not use redundant count labels such as `5 個重點詞彙`, `6 個重點詞彙`, `五個挑戰詞彙`, or `六個挑戰詞彙`.
- Avoid the literal phrase `Traditional Chinese` in generated Chinese daily lesson HTML.

### Chinese vocabulary count and length mix

For public generated Daily Chinese pages:

- Show **exactly 5 Easy cards** and **exactly 5 Challenge cards**.
- Easy words should be genuinely easier/different where possible, not just a subset of Challenge.
- Challenge words should remain useful news-reading terms.
- Use a mix of two-character words and longer terms when possible.
- Do not make all cards 4-character phrases.
- Do not group all two-character words first and all longer terms last.
- Mix/interleave the ordering visually.

Good 2-character examples:

- `受惠`
- `繁榮`
- `涵蓋`
- `納管`
- `磋商`
- `制裁`
- `監管`
- `出口`
- `強勁`

Good longer examples:

- `產業結構`
- `系統半導體`
- `後端製程`
- `基礎設施`
- `場域驗證`

### Chinese phonetic toggle

Normal daily Chinese lesson pages should include a compact **single-button** phonetic toggle beside `Key Words`.

Behavior:

- Default displayed pronunciation: Zhuyin / `ㄅㄆㄇ`.
- When Zhuyin is displayed, the button shows only `Pinyin`.
- When Pinyin is displayed, the button shows only `ㄅㄆㄇ`.
- No explanatory description such as “Pronunciation display” or “Tap the buttons…”.
- Store pronunciations as:
  - `data-zhuyin="..."`
  - `data-pinyin="..."`
- Use JavaScript to switch displayed `.phonetic` / `.zhuyin` text and update the single button to the other mode.

### Chinese direct-page navigation

- Direct lesson pages should keep a 3-line hamburger navigation.
- The top `Daily Chinese` label should be clickable and link to:

```text
https://chinese-lessons-web.vercel.app
```

### Chinese look and feel

- Match the newer Daily English/5dailywords visual direction where possible: modern sans/system typography, warm neutral background, flat cards, no blue radial/hero gradients, no large shadowed outer viewer panel, and no duplicate viewer title bar above the iframe.
- Homepage and standalone lesson navigation drawers should not include an internal `Close` button; dismiss via backdrop/main page, lesson selection, Escape, or tapping the blank/header area above the first nav link.
- Direct lesson pages with `?embedded=1` should hide standalone nav only when actually inside the homepage iframe.

### Chinese pages removed / not wanted

- The old Siri page should not appear on the site:
  - `/lessons/siri-ai-news-study`
  - `/lessons/siri-ai-news-study.html`
- Toggle test pages should not remain public:
  - `/lessons/zhuyin-pinyin-toggle-test`
  - `/lessons/zhuyin-pinyin-single-toggle-test`

These should return 404 if removed.

### Chinese verifier requirements

The Chinese verifier script should check generated public Daily Chinese pages:

- `中文摘要` present.
- `Key Words` present.
- Exactly 5 Easy vocab cards and exactly 5 Challenge vocab cards.
- Each word heading is highlighted in its source snippet with `<mark>`.
- Vocab uses a reasonable mix of two-character words and longer terms when possible.
- No quiz terms.
- Mobile font requirements remain readable.

Verifier path:

```text
/opt/data/skills/language-learning/traditional-chinese-current-events/scripts/verify_daily_lesson.py
```

---

## English lesson preferences

Skill name to restore/update: `daily-english-lessons`

- Homepage native-language selector: show a simple globe icon, a vertical divider, then a dropdown in the top-right homepage header. Default is `繁體中文`; include options `繁體中文`, `简体中文`, `한국어`, `日本語`, and Brazilian Portuguese / compact `PT-BR` where space is tight. The selected value controls the native-language translation sections in lesson pages, including the article-summary translation and vocabulary-definition translations.

### Content format

Each daily English lesson should be a current-events vocabulary page based on a reputable English-language article.

Topic variety matters for reader interest. Do not default mostly to geopolitics. Use this default cadence unless the day's news strongly suggests a better non-repetitive choice:

- Monday: business / economy / markets.
- Tuesday: world affairs / geopolitics.
- Wednesday: science / health / climate.
- Thursday: technology / AI / internet / cybersecurity.
- Friday: culture / society / lifestyle / education / work.
- Saturday: world affairs or the genuinely biggest major headline.
- Sunday: lighter interesting feature, human-interest, science discovery, sports, travel, food, education, or culture.

Long-run target mix: about 30% world affairs/geopolitics, 20% business/economy, 15% technology/AI, 15% science/health/climate, 15% culture/society/lifestyle, and 5% wildcard/human-interest.

Required format:

- Source box with article title, source, date, link only.
- Do not include a `Focus:` pill/bubble.
- Do not include the small `Article base: title/source link + short learning snippets only.` description below the article link.
- English summary heading: `Article Summary`.
- Traditional Chinese summary heading: `文章摘要`.
- Vocabulary heading: `5 Daily Words`.
- Page `<title>`, lesson `<h1>`, and navigation names should use the clean article/topic title only; do not prefix them with labels like `Current Events English:`.
- Exactly 5 vocabulary cards.
- Vocabulary should use exactly 5 single-word cards, not phrases. If an article cannot provide five strong single-word items, choose a different reputable article.
- Each vocabulary card includes:
  - vocabulary word/phrase shown first, with no part-of-speech/type label above it
  - pronunciation button using browser Web Speech API where practical, with a clean inline SVG speaker icon (`class="sound-icon"`) instead of the `🔊` emoji or external `sound-icon.svg` file
  - unlabeled English definition
  - article/headline/RSS excerpt labeled exactly `In article:` with highlighted term
  - unlabeled native-language definition (Traditional Chinese by default, switchable by selected language)
- Do not include a `Word Origins & Notes` section in daily English lessons.
- Add a final feedback section after vocabulary only: heading `How was today’s vocabulary?` with embedded Tally iframe `https://tally.so/embed/zxbkrZ`, both `src` and `data-tally-src`, the Tally widget script, and hidden/query metadata `lesson_date` plus selected `language`; do not use `https://tally.so/r/zxbkrZ` link buttons or contact form `LZojoO` for vocab difficulty.
- Site update label should read exactly `Updates 9 AM Hong Kong / Taiwan time`.
- Desktop/non-phone homepage shell should not show a separate duplicate current-lesson title bar above the embedded lesson viewer; the embedded lesson already shows the date/topic title.
- Do not include quiz, mini practice, Language Focus, writing exercises, comprehension questions, Source context, Article Snippets, Behind the Headline, or Open full page link.
- Do not use old labels like `Short English Summary`, `繁體中文摘要`, `5 Useful Words & Patterns`, `5 Useful Words & Phrases`, or `Word Origins & Fun Notes`.

### English vocabulary difficulty

Future English daily lessons should match the **June 13 benchmark difficulty**:

- Still label the page `Level: intermediate`.
- But choose harder intermediate / B2-ish current-events vocabulary.
- Prefer formal current-events, diplomacy, policy, economy, science, technology, culture, and abstract vocabulary from the rotating topic mix.

Benchmark June 13 terms:

- `envisages`
- `blockade`
- `obligations`
- `incrementally`

Avoid easy headline words unless part of a stronger phrase, such as:

- `deal`
- `timing`
- `decided`
- `reopening`
- `meeting`
- multi-word phrases when a good single-word article term is available

If the source article does not contain enough June-13-level vocabulary, choose a different reputable article.

---

## Cron schedules to recreate

Timezone interpretation: Taiwan/Hong Kong time = UTC+8.

### Chinese

Daily Chinese lesson generation:

```cron
30 0 * * *
```

= 8:30 AM Taiwan/HK.

Prompt must include the Chinese preferences above, especially:

- exactly 6 cards
- 3–5 two-character words + 1–3 longer terms
- mixed ordering
- `中文摘要`
- `Key Words`
- no quiz

Chinese website publish:

```cron
42 0 * * *
```

= 8:42 AM Taiwan/HK.

Should run script:

```text
publish_chinese_lessons_site.py
```

With `no_agent=True` if using Hermes cron. The script should:

- rebuild the site
- update GitHub when token is available
- deploy to Vercel
- verify homepage
- send confirmation with homepage link

Chinese weekly/monthly review jobs were intentionally stopped. Do not restore them unless explicitly asked.

### English

Daily English lesson generation:

```cron
31 0 * * *
```

= 8:31 AM Taiwan/HK. This gives a review window before the publishing job runs.

Prompt must include the English preferences above, especially:

- exactly 5 vocab cards
- June 13 benchmark difficulty
- `Article Summary`
- `文章摘要`
- `5 Daily Words`
- pronunciation buttons
- `In article:` excerpts
- rotating topic cadence / not mostly geopolitics
- bottom Tally vocabulary feedback form

English website publish:

```cron
57 0 * * *
```

= 8:57 AM Taiwan/HK. If no changes are requested after the 8:31 AM lesson is delivered, publish as usual.

Should run script:

```text
publish_english_lessons_site.py
```

With `no_agent=True` if using Hermes cron. The script should:

- rebuild the site
- update GitHub
- deploy to Vercel
- verify homepage
- send confirmation with homepage link

English weekly/monthly review jobs should not be restored unless explicitly requested. Website navigation should remain daily-only unless review sections are explicitly restored.

---

## Static site publishing expectations

For both English and Chinese:

- Vercel is the live hosting layer.
- GitHub is backup/source control and should be synced when token is available.
- Website publishing should not be blocked by GitHub divergence.
- Prefer GitHub Contents API for reliable small static-site sync if normal `git push` conflicts.
- Vercel direct deploy should work from a temporary copy excluding `.git` and `.vercel` metadata.
- Scripts should use private safe cache dirs if npm/Vercel cache ownership issues appear.
- Scripts should self-load `/opt/data/.env`.
- Do not store tokens in scripts, repos, or this backup file.

---

## Restoration checklist

A fresh Hermes restore should do the following:

1. Recreate or patch skill `traditional-chinese-current-events` with the Chinese preferences above.
2. Recreate or patch skill `daily-english-lessons` with the English preferences above.
3. Recreate verifier `/opt/data/skills/language-learning/traditional-chinese-current-events/scripts/verify_daily_lesson.py` with the Chinese checks above.
4. Restore cron jobs for Chinese/English daily generation and publishing with the schedules above.
5. Recreate `/opt/data/scripts/` wrappers if Hermes cron expects scripts there.
6. Ensure `/opt/data/.env` exists with `VERCEL_TOKEN` and optional `GITHUB_TOKEN`; do not print values.
7. Clone or recreate website folders from GitHub if local website folders are missing:
   - `Windswell284/Chinese-lessons-web`
   - `Windswell284/English-lessons-web`
8. Recreate local source lesson folders if needed:
   - `/opt/data/chinese-lessons/`
   - `/opt/data/english-lessons/`
9. Rebuild sites with each `scripts/generate_site.py`.
10. Publish to Vercel and verify live homepage/direct lesson URLs return 200.

---

## Copy/paste summary for a future agent

Lesson preferences:

- Chinese and English lessons are daily current-events vocab-first web pages.
- Chinese lessons use exactly 6 vocabulary cards; English lessons use exactly 5 vocabulary cards.
- Chinese: Traditional Chinese, `中文摘要`, `Key Words`, no quiz, 國中挑戰版, source link/summary/vocab only, no full copyrighted article. Vocab should be 3–5 two-character words and 1–3 longer terms, with mixed/interleaved ordering. Include Zhuyin, Chinese definition, English definition, and original source sentence with highlight. Use single-button Pinyin/ㄅㄆㄇ toggle on normal daily pages.
- English: source box, `Article Summary`, `文章摘要`, `5 Daily Words`, audio buttons, unlabeled English/native definitions, real source excerpt labeled `In article:`. Use exactly 5 single-word cards. Vocab should match June 13 harder-intermediate benchmark, not easy headline words. Rotate topics for reader interest rather than mostly geopolitics: roughly 30% world affairs, 20% business/economy, 15% technology/AI, 15% science/health/climate, 15% culture/society/lifestyle, and 5% wildcard/human-interest.
- Both sites: mobile-first, daily-only nav capped at 10 links, hamburger direct-page nav, no duplicate iframe nav, Vercel hosting, GitHub sync when possible, confirmations after publish.

Keep this file somewhere safe outside Hermes.
