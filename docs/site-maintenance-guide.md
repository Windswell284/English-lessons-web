# 5dailywords / Daily English site maintenance guide

This repo is the durable source of truth for the public Daily English site.

## Public site

- Live site: <https://5dailywords.com>
- GitHub repository: <https://github.com/Windswell284/English-lessons-web>
- Vercel project/site: `english-lessons-web`
- Website type: static HTML site generated from standalone lesson HTML files.

## Important local paths on the VPS

- Source lessons: `/opt/data/english-lessons/`
- Generated website repository: `/opt/data/english-lessons-web/`
- Site generator: `/opt/data/english-lessons-web/scripts/generate_site.py`
- Publish script used by cron: `/opt/data/.hermes/scripts/publish_english_lessons_site.py`
- Cron-visible wrapper: `/opt/data/scripts/publish_english_lessons_site.py`
- Restore backup doc in this repo: `/opt/data/english-lessons-web/docs/hermes-restore-backup.md`
- Secrets file: `/opt/data/.env`

Do not commit `/opt/data/.env` or print its values. It should contain deployment credentials such as `GITHUB_TOKEN` and `VERCEL_TOKEN`.

## Source-of-truth rule

- Persistent lesson-content edits belong in `/opt/data/english-lessons/`.
- Files under `/opt/data/english-lessons-web/lessons/` are generated output and can be overwritten by `scripts/generate_site.py`.
- GitHub is the canonical source of truth/source control for the generated website repo.
- Vercel is the live hosting layer and should deploy from the GitHub repo.
- A direct local Vercel CLI deploy is only an emergency/preview workaround. If it is ever used, sync the exact deployed state back to GitHub immediately afterward.

## Normal manual workflow

```bash
cd /opt/data/english-lessons-web
python3 scripts/generate_site.py
python3 scripts/verify_daily_lesson.py YYYY-MM-DD

git status --short
git add -A
git commit -m "chore: publish English lessons site YYYY-MM-DD"
git push origin main
```

After pushing, verify that Vercel deploys from GitHub and that the live site is correct:

- Homepage returns HTTP 200: <https://5dailywords.com>
- Latest direct lesson URL returns HTTP 200.
- Homepage navigation contains the latest lesson and does not restore Weekly/Monthly review nav unless explicitly requested.
- Public files contain no personal-name branding and no secrets.

## Automated publish workflow

The publish script should:

1. Rebuild the site from `/opt/data/english-lessons/`.
2. Refresh `docs/hermes-restore-backup.md` if the portable restore backup exists.
3. Commit generated changes in `/opt/data/english-lessons-web/`.
4. Push `main` to GitHub using `GITHUB_TOKEN` from `/opt/data/.env`.
5. Let Vercel deploy from that GitHub push.
6. Verify the live homepage.
7. Report the homepage link, GitHub commit, and Vercel Git deployment.

If Vercel is not connected to `Windswell284/English-lessons-web`, connect the Vercel project to the GitHub repository before considering the workflow complete. Do not silently fall back to direct local Vercel deploys when GitHub is the chosen source of truth.

## Reconciliation / recovery

If local Git and GitHub diverge:

1. Create a safety backup branch and git bundle before changing history or resetting.
2. Compare local working tree, `HEAD`, and `origin/main`.
3. If GitHub already contains the generated files from a prior API sync, reset local to `origin/main` and continue from there.
4. Otherwise preserve the currently live/deployed tree, reconcile intentionally, then push.
5. Verify with `git rev-list --left-right --count origin/main...HEAD`; expected result is `0\t0`.

## Maintainer checklist for preference/workflow changes

Update this guide and `docs/hermes-restore-backup.md` every time a change affects durable preferences, lesson format, UI behavior, article selection, scheduling, generation, verification, deployment, or recovery.

For durable changes:

1. Update the active Hermes skill `daily-english-lessons`.
2. Update `docs/hermes-restore-backup.md`.
3. Update this maintenance guide.
4. Update source lessons and/or `scripts/generate_site.py` if needed.
5. Rebuild and verify locally.
6. Commit and push to GitHub.
7. Verify Vercel deployed from GitHub and live pages are correct.
