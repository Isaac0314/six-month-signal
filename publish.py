#!/usr/bin/env python3
"""Publish one episode of The Six-Month Signal.

Runs as a Hermes no-agent cron in WSL after the 20:30 audio brief. Stdlib only;
external tools: ffmpeg, ffprobe, gh, git.

Contract: the weekday-newsletter-podcast job writes a sidecar JSON per episode at
{AUDIO_DIR}/{DATE}-episode.json:
  { "date": "YYYY-MM-DD", "edition": "public-safe", "title": "...",
    "description": "...", "audio_path": "/mnt/c/..." }
The publisher REFUSES anything not marked edition=public-safe — that is the gate
that keeps Isaac's private layer off the public feed.
"""
import argparse
import datetime as dt
import json
import subprocess
import sys
import zoneinfo
from pathlib import Path

REPO = Path(__file__).resolve().parent
AUDIO_DIR = Path('/mnt/c/Users/Isaac Luo/Desktop/Dein/Dein Remote/03 Resources/Daily Intel/Audio')
GH_REPO = 'Isaac0314/six-month-signal'
RELEASE_TAG = 'episodes'
LONDON = zoneinfo.ZoneInfo('Europe/London')


def run(cmd, **kw):
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--date', default=dt.datetime.now(LONDON).strftime('%Y-%m-%d'))
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()

    sidecar = AUDIO_DIR / f'{a.date}-episode.json'
    if not sidecar.exists():
        print(f'No public-safe episode sidecar for {a.date} - nothing to publish.')
        return 0
    meta = json.loads(sidecar.read_text(encoding='utf-8'))
    if meta.get('edition') != 'public-safe':
        print(f'REFUSED: sidecar for {a.date} is not marked edition=public-safe.')
        return 1
    src = Path(meta['audio_path'])
    if not src.exists():
        print(f'ERROR: audio file missing: {src}')
        return 1

    # Cache-busting name: platforms (Spotify) cache audio by URL and may never
    # re-fetch a changed file behind an unchanged URL. Unique name per publish
    # makes replacements propagate; superseded assets are deleted after push.
    stamp = dt.datetime.now(LONDON).strftime('%H%M%S')
    mp3 = REPO / f'{a.date}-{stamp}.mp3'
    if src.suffix.lower() == '.mp3':
        mp3.write_bytes(src.read_bytes())
    else:
        run(['ffmpeg', '-y', '-i', str(src), '-ac', '1', '-codec:a', 'libmp3lame',
             '-b:a', '112k', '-ar', '44100', str(mp3)])
    dur = float(run(['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                     '-of', 'csv=p=0', str(mp3)]).stdout.strip())
    size = mp3.stat().st_size
    if dur < 60:
        print(f'REFUSED: episode is only {dur:.0f}s - looks like a broken TTS artifact.')
        return 1

    if a.dry_run:
        print(f'DRY RUN ok: {mp3.name} {dur/60:.1f}min {size/1e6:.1f}MB')
        return 0

    run(['gh', 'release', 'upload', RELEASE_TAG, str(mp3), '--clobber', '--repo', GH_REPO])

    epath = REPO / 'episodes.json'
    episodes = json.loads(epath.read_text(encoding='utf-8'))
    episodes = [e for e in episodes if e['guid'] != f'sms-{a.date}']
    episodes.append({
        'guid': f'sms-{a.date}',
        'title': meta['title'],
        'description': meta['description'],
        'mp3_url': f'https://github.com/{GH_REPO}/releases/download/{RELEASE_TAG}/{mp3.name}',
        'bytes': size,
        'duration_sec': int(dur),
        'published_at': dt.datetime.now(LONDON).isoformat(timespec='seconds'),
    })
    epath.write_text(json.dumps(episodes, indent=1, ensure_ascii=False), encoding='utf-8')

    run([sys.executable, str(REPO / 'feed_gen.py')])
    run(['git', '-C', str(REPO), 'add', 'episodes.json', 'feed.xml'])
    run(['git', '-C', str(REPO), 'commit', '-m', f'episode {a.date}'])
    run(['git', '-C', str(REPO), 'push'])
    mp3.unlink()  # asset lives on the release; keep the clone slim

    # delete superseded same-date assets (old cache-busted names)
    assets = json.loads(run(['gh', 'release', 'view', RELEASE_TAG, '--repo', GH_REPO,
                             '--json', 'assets']).stdout)['assets']
    for asset in assets:
        n = asset['name']
        if n.endswith('.mp3') and n.startswith(a.date) and n != mp3.name:
            run(['gh', 'release', 'delete-asset', RELEASE_TAG, n, '--repo', GH_REPO, '--yes'])

    print(f'Published "{meta["title"]}" - {dur/60:.1f} min, {size/1e6:.1f} MB. '
          f'Feed updated ({len(episodes)} episodes).')
    return 0


if __name__ == '__main__':
    sys.exit(main())
