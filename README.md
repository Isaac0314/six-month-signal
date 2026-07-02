# The Six-Month Signal

A daily analyst brief on frontier AI: model releases and capability deltas, evals and
benchmark anomalies, agent reliability, and inference economics — about ten minutes,
every weekday.

- **Feed:** https://isaac0314.github.io/six-month-signal/feed.xml
- **Artwork:** `artwork.png` (3000×3000)

## How this repo works

| File | Role |
|---|---|
| `config.json` | Show metadata (title, description, owner email for platform verification) |
| `episodes.json` | Episode manifest — appended by the publisher, source of truth for the feed |
| `feed_gen.py` | Regenerates `feed.xml` from config + manifest (stdlib only) |
| `publish.py` | Nightly publisher: transcode → upload release asset → update manifest → regen feed → push |
| `feed.xml` | Generated. Served by GitHub Pages. Do not edit by hand |

Audio files live as assets on the [`episodes` release](../../releases/tag/episodes) — the
git tree stays small forever.

## Pipeline (runs on Hermes, WSL)

1. **20:05** RSS ingest cron gathers the day's source pool.
2. **20:30** editorial brief cron writes the episode script, generates TTS audio
   (ElevenLabs), and drops a `{DATE}-episode.json` sidecar **only when the script passed
   the public-edition rules** (no personal/employer context, tight quoting of paid
   sources, attribution).
3. **21:15** `publish.py` picks up the sidecar, refuses anything not marked
   `edition: public-safe`, transcodes to MP3, uploads, regenerates the feed, pushes.

Content is analysis and commentary with attribution; quotes are kept under fair-use
length. Sources are credited in each episode's show notes.
