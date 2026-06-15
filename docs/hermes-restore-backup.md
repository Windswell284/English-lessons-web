# Peter Hermes Lesson Preferences Restore Backup

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
- Direct lesson pages must have navigation; embedded homepage lesson views should hide duplicate standalone nav via `?embedded=1`.
- Menus should be daily-only unless explicitly restored.
- Daily lesson navigation should be capped at 10 total daily links.
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
- Level: `國中挑戰版` by default.
- No quiz unless explicitly requested.
- Summary heading: `中文摘要`.
- Vocabulary heading: `Key Words`.
- Exactly 6 vocabulary cards.
- Each vocabulary card must include:
  - word/phrase
  - Zhuyin
  - Chinese definition
  - English definition
  - `原文句子` with the target word highlighted using `<mark>` when possible
- Do not use redundant count labels such as `5 個重點詞彙`, `6 個重點詞彙`, `五個挑戰詞彙`, or `六個挑戰詞彙`.
- Avoid the literal phrase `Traditional Chinese` in generated Chinese daily lesson HTML.

### Chinese vocabulary length mix

For exactly 6 vocabulary cards:

- Use **3–5 two-character words**.
- Use **1–3 longer 3–6 character phrases/terms**.
- This is roughly a **50/50 through 80/20** range of two-character words vs. longer phrases.
- Do not make all six cards 4-character phrases.
- Do not group all two-character words first and all longer terms last.
- Mix/interleave the ordering visually.
- Good order examples:
  - short, long, short, long, short, long
  - short, short, long, short, long, short
- Bad order example:
  - short, short, short, long, long, long

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

### Chinese pages removed / not wanted

- The old Siri page should not appear on the site:
  - `/lessons/siri-ai-news-study`
  - `/lessons/siri-ai-news-study.html`
- Toggle test pages should not remain public:
  - `/lessons/zhuyin-pinyin-toggle-test`
  - `/lessons/zhuyin-pinyin-single-toggle-test`

These should return 404 if removed.

### Chinese verifier requirements

The Chinese verifier script should check:

- `中文摘要` present.
- `Key Words` present.
- Exactly 6 vocab cards.
- Each word heading is highlighted in its source snippet with `<mark>`.
- Vocab length range: 3–5 two-character words and 1–3 longer terms.
- Vocab order is not grouped by length (`S+L+` or `L+S+` should fail).
- No quiz terms.
- Mobile font requirements remain readable.

Verifier path:

```text
/opt/data/skills/language-learning/traditional-chinese-current-events/scripts/verify_daily_lesson.py
```

---

## English lesson preferences

Skill name to restore/update: `daily-english-lessons`

### Content format

Each daily English lesson should be a current-events vocabulary page based on a reputable English-language article.

Required format:

- Source box with article title, source, date, link only.
- Do not include a `Focus:` pill/bubble.
- Do not include the small `Article base: title/source link + short learning snippets only.` description below the article link.
- English summary heading: `Article Summary`.
- Traditional Chinese summary heading: `文章摘要`.
- Vocabulary heading: `5 Daily Keywords`.
- Page `<title>`, lesson `<h1>`, and navigation names should use the clean article/topic title only; do not prefix them with labels like `Current Events English:`.
- Exactly 5 vocabulary cards.
- Each vocabulary card includes:
  - vocabulary word/phrase shown first, with no part-of-speech/type label above it
  - pronunciation button using browser Web Speech API where practical
  - English definition
  - `中文定義`
  - article/headline/RSS excerpt labeled exactly `In article:` with highlighted term
- Optional final section only if useful: `Word Origins & Notes`.
- Site update label should read exactly `Updates 9 AM Hong Kong / Taiwan time`.
- Desktop/non-phone homepage shell should not show a separate duplicate current-lesson title bar above the embedded lesson viewer; the embedded lesson already shows the date/topic title.
- Do not include quiz, mini practice, Language Focus, writing exercises, comprehension questions, Source context, Article Snippets, Behind the Headline, or Open full page link.
- Do not use old labels like `Short English Summary`, `繁體中文摘要`, `5 Useful Words & Patterns`, `5 Useful Words & Phrases`, or `Word Origins & Fun Notes`.

### English vocabulary difficulty

Future English daily lessons should match the **June 13 benchmark difficulty**:

- Still label the page `Level: intermediate`.
- But choose harder intermediate / B2-ish current-events vocabulary.
- Prefer formal current-events, diplomacy, policy, economy, abstract nouns, and useful multi-word phrases.

Benchmark June 13 terms:

- `envisages`
- `blockade`
- `obligations`
- `staged reintegration`
- `incrementally`
- `proxy groups`

Avoid easy headline words unless part of a stronger phrase, such as:

- `deal`
- `timing`
- `decided`
- `reopening`
- `meeting`

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
45 0 * * *
```

= 8:45 AM Taiwan/HK.

Prompt must include the English preferences above, especially:

- exactly 5 vocab cards
- June 13 benchmark difficulty
- `Article Summary`
- `文章摘要`
- `5 Daily Keywords`
- pronunciation buttons
- `In article:` excerpts

English website publish:

```cron
57 0 * * *
```

= 8:57 AM Taiwan/HK.

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

English weekly/monthly review jobs may still exist unless intentionally cancelled later. Website navigation should still remain daily-only unless review sections are explicitly restored.

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

Peter’s lesson preferences:

- Chinese and English lessons are daily current-events vocab-first web pages.
- Chinese lessons use exactly 6 vocabulary cards; English lessons use exactly 5 vocabulary cards.
- Chinese: Traditional Chinese, `中文摘要`, `Key Words`, no quiz, 國中挑戰版, source link/summary/vocab only, no full copyrighted article. Vocab should be 3–5 two-character words and 1–3 longer terms, with mixed/interleaved ordering. Include Zhuyin, Chinese definition, English definition, and original source sentence with highlight. Use single-button Pinyin/ㄅㄆㄇ toggle on normal daily pages.
- English: source box, `Article Summary`, `文章摘要`, `5 Daily Keywords`, audio buttons, English definition + `中文定義`, real source excerpt labeled `In article:`. Vocab should match June 13 harder-intermediate benchmark, not easy headline words.
- Both sites: mobile-first, daily-only nav capped at 10 links, hamburger direct-page nav, no duplicate iframe nav, Vercel hosting, GitHub sync when possible, confirmations after publish.

Keep this file somewhere safe outside Hermes.
