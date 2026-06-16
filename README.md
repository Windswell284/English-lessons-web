# Daily English Lessons

Static website for daily English lessons.

## Build locally

```bash
python3 scripts/generate_site.py
```

The generator copies lesson HTML files from `/opt/data/english-lessons/` into `lessons/` and `reviews/`, then rebuilds `index.html`.

## Vercel

Static site. Recommended settings:

- Framework preset: Other
- Build command: empty or `npm run vercel-build`
- Output directory: `.`
