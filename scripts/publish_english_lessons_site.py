#!/usr/bin/env python3
"""Publish the 5dailywords / Daily English static site.

Durable workflow:
1. Rebuild static site from /opt/data/english-lessons/*.html
2. Commit and push /opt/data/english-lessons-web to GitHub
3. Let Vercel deploy from the GitHub push (GitHub is source of truth)
4. Verify the live 5dailywords homepage

This script intentionally does not run `vercel deploy` directly. If the Vercel
project is not connected to the GitHub repo, publishing should fail clearly so
we do not silently drift back to Vercel-only local deploys.
"""
from __future__ import annotations

import base64
import json
import os
import shutil
import subprocess
import time
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path('/opt/data/english-lessons-web')
BACKUP_SOURCE = Path('/opt/data/peter-hermes-lesson-restore-backup.md')
BACKUP_DEST = REPO / 'docs' / 'hermes-restore-backup.md'
GITHUB_OWNER = 'Windswell284'
GITHUB_REPO = 'English-lessons-web'
GITHUB_REMOTE = f'https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}.git'
SITE_URL = 'https://5dailywords.com'
VERCEL_PROJECT_ID = 'prj_fURebyvibpsQl9M5vW364Kip4XME'
VERCEL_TEAM_ID = 'team_ngMyzhuq5FcvzvQleWFanmmj'


def load_env_file(path: Path = Path('/opt/data/.env')) -> None:
    if not path.exists():
        return
    for line in path.read_text(errors='ignore').splitlines():
        s = line.strip()
        if not s or s.startswith('#') or '=' not in s:
            continue
        key, value = s.split('=', 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_env_file()
GITHUB_TOKEN = os.environ.get('GITHUB_' + 'TOKEN', '')
VERCEL_TOKEN = os.environ.get('VERCEL_' + 'TOKEN', '')


def sanitize(text: str) -> str:
    for secret in (GITHUB_TOKEN, VERCEL_TOKEN):
        if secret:
            text = text.replace(secret, '[TOKEN]')
    return text


def git_auth_header() -> str:
    raw = ('x-access-token:' + GITHUB_TOKEN).encode()
    return 'AUTHORIZATION: basic ' + base64.b64encode(raw).decode()


def run(cmd: list[str], cwd: Path = REPO, check: bool = True, git_auth: bool = False) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env['NPM_CONFIG_CACHE'] = '/opt/data/.npm-cache'
    env['HOME'] = '/opt/data'
    env['XDG_CACHE_HOME'] = '/opt/data/.cache'
    env['XDG_CONFIG_HOME'] = '/opt/data/.config'
    env['XDG_DATA_HOME'] = '/opt/data/.local/share'
    env['GIT_TERMINAL_PROMPT'] = '0'
    full_cmd = cmd
    if git_auth:
        full_cmd = ['git', '-c', f'http.https://github.com/.extraheader={git_auth_header()}'] + cmd[1:]
    p = subprocess.run(full_cmd, cwd=cwd, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if check and p.returncode:
        raise RuntimeError(f"Command failed: {sanitize(' '.join(cmd))}\n{sanitize(p.stdout)}")
    return p


def refresh_restore_backup() -> None:
    """Copy Peter's portable Hermes restore backup into the GitHub-synced repo."""
    if not BACKUP_SOURCE.exists():
        return
    BACKUP_DEST.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(BACKUP_SOURCE, BACKUP_DEST)


def verify_github_access() -> None:
    req = urllib.request.Request(
        f'https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}',
        headers={'Authorization': 'Bearer ' + GITHUB_TOKEN, 'Accept': 'application/vnd.github+json'},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    perms = data.get('permissions') or {}
    if not perms.get('push'):
        raise RuntimeError('GitHub token can read the English repo but does not have push/contents write access.')


def ensure_vercel_git_linked() -> None:
    params = urllib.parse.urlencode({'teamId': VERCEL_TEAM_ID})
    req = urllib.request.Request(
        f'https://api.vercel.com/v9/projects/{VERCEL_PROJECT_ID}?{params}',
        headers={'Authorization': 'Bearer ' + VERCEL_TOKEN},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    link = data.get('link') or data.get('gitRepository')
    if not link:
        raise RuntimeError(
            'Vercel project english-lessons-web is not connected to the GitHub repo yet. '
            'Connect it in Vercel to Windswell284/English-lessons-web, then rerun this publisher. '
            'Direct Vercel CLI deploy is intentionally disabled because GitHub is now the source of truth.'
        )


def git_sync_and_push() -> tuple[str, bool]:
    run(['git', 'remote', 'set-url', 'origin', GITHUB_REMOTE])
    run(['git', 'fetch', 'origin', 'main'], git_auth=True)
    local = run(['git', 'rev-parse', 'HEAD']).stdout.strip()
    remote = run(['git', 'rev-parse', 'origin/main']).stdout.strip()
    status = run(['git', 'status', '--porcelain']).stdout.strip()
    if local != remote and status:
        raise RuntimeError('Local English repo is both out of sync with GitHub and dirty; manual reconciliation required before publishing.')
    if local != remote:
        run(['git', 'reset', '--hard', 'origin/main'])

    build = run(['python3', 'scripts/generate_site.py']).stdout.strip()
    refresh_restore_backup()

    run(['git', 'add', '-A'])
    staged = run(['git', 'diff', '--cached', '--quiet'], check=False).returncode != 0
    if staged:
        run(['git', 'commit', '-m', 'chore: publish English lessons site'])
    sha = run(['git', 'rev-parse', 'HEAD']).stdout.strip()
    run(['git', 'push', 'origin', 'main'], git_auth=True)
    run(['git', 'fetch', 'origin', 'main'], git_auth=True)
    divergence = run(['git', 'rev-list', '--left-right', '--count', 'origin/main...HEAD']).stdout.strip()
    if divergence != '0\t0':
        raise RuntimeError('GitHub push did not leave local and origin/main synchronized: ' + divergence)
    if build:
        print(build.splitlines()[0])
    return sha, staged


def list_vercel_deployments() -> list[dict]:
    params = urllib.parse.urlencode({'projectId': VERCEL_PROJECT_ID, 'teamId': VERCEL_TEAM_ID, 'limit': 20})
    req = urllib.request.Request(
        f'https://api.vercel.com/v6/deployments?{params}',
        headers={'Authorization': 'Bearer ' + VERCEL_TOKEN},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r).get('deployments', [])


def wait_for_git_deployment(commit_sha: str, changed: bool) -> str:
    if not changed:
        deployments = list_vercel_deployments()
        ready = next((d for d in deployments if d.get('target') == 'production' and d.get('state') == 'READY'), None)
        return 'no new commit; latest production deployment remains ' + (ready.get('url') if ready else 'unknown')

    deadline = time.time() + 180
    last_seen = 'none'
    while time.time() < deadline:
        deployments = list_vercel_deployments()
        for d in deployments:
            meta = d.get('meta') or {}
            if meta.get('githubCommitSha') == commit_sha or meta.get('githubCommitRef') == 'main' and d.get('source') != 'cli':
                last_seen = f"{d.get('url')} state={d.get('state')} source={d.get('source')}"
                if d.get('state') == 'READY':
                    return d.get('url', '')
                if d.get('state') in {'ERROR', 'CANCELED'}:
                    raise RuntimeError('Vercel Git deployment failed: ' + last_seen)
        time.sleep(10)
    raise RuntimeError('Timed out waiting for Vercel Git deployment for commit ' + commit_sha[:7] + '; last seen: ' + last_seen)


def verify_live_site() -> None:
    with urllib.request.urlopen(SITE_URL, timeout=30) as r:
        text = r.read().decode('utf-8', 'ignore')
        if r.status != 200:
            raise RuntimeError(f'Live English homepage returned HTTP {r.status}')
    banned = ['Weekly reviews', 'Monthly reviews', 'Old lessons', 'Last site build']
    found = [s for s in banned if s in text]
    if found:
        raise RuntimeError('Live English homepage still contains old navigation text: ' + ', '.join(found))
    if 'Daily lessons' not in text:
        raise RuntimeError('Live English homepage did not contain Daily lessons navigation heading')


def main() -> None:
    missing = [name for name, value in {'GITHUB_TOKEN': GITHUB_TOKEN, 'VERCEL_TOKEN': VERCEL_TOKEN}.items() if not value]
    if missing:
        raise RuntimeError('Missing required environment variable(s): ' + ', '.join(missing))
    verify_github_access()
    ensure_vercel_git_linked()
    sha, changed = git_sync_and_push()
    deployment = wait_for_git_deployment(sha, changed)
    verify_live_site()
    print('English lessons website updated and verified.')
    print(f'Homepage: {SITE_URL}')
    print(f'GitHub commit: {sha[:7]}')
    print(f'Vercel Git deployment: {deployment}')


if __name__ == '__main__':
    main()
