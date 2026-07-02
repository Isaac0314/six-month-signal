#!/usr/bin/env python3
"""Regenerate feed.xml from config.json + episodes.json. Stdlib only."""
import json
import email.utils
from pathlib import Path
from xml.sax.saxutils import escape

HERE = Path(__file__).resolve().parent


def rfc822(iso):
    import datetime as dt
    d = dt.datetime.fromisoformat(iso)
    if d.tzinfo is None:
        d = d.replace(tzinfo=dt.timezone.utc)
    return email.utils.format_datetime(d)


def hms(seconds):
    s = int(seconds)
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"


def main():
    cfg = json.loads((HERE / 'config.json').read_text(encoding='utf-8'))
    episodes = json.loads((HERE / 'episodes.json').read_text(encoding='utf-8'))
    episodes = sorted(episodes, key=lambda e: e['published_at'], reverse=True)[: cfg['max_feed_items']]

    items = []
    for e in episodes:
        items.append(f"""    <item>
      <title>{escape(e['title'])}</title>
      <description>{escape(e['description'])}</description>
      <enclosure url="{escape(e['mp3_url'])}" length="{e['bytes']}" type="audio/mpeg"/>
      <guid isPermaLink="false">{escape(e['guid'])}</guid>
      <pubDate>{rfc822(e['published_at'])}</pubDate>
      <itunes:duration>{hms(e['duration_sec'])}</itunes:duration>
      <itunes:explicit>false</itunes:explicit>
    </item>""")

    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>{escape(cfg['title'])}</title>
    <description>{escape(cfg['description'])}</description>
    <link>{escape(cfg['link'])}</link>
    <language>{cfg['language']}</language>
    <atom:link href="{escape(cfg['feed_url'])}" rel="self" type="application/rss+xml"/>
    <itunes:author>{escape(cfg['author'])}</itunes:author>
    <itunes:owner>
      <itunes:name>{escape(cfg['author'])}</itunes:name>
      <itunes:email>{escape(cfg['owner_email'])}</itunes:email>
    </itunes:owner>
    <itunes:image href="{escape(cfg['artwork_url'])}"/>
    <itunes:category text="{escape(cfg['category'])}"/>
    <itunes:explicit>{'true' if cfg['explicit'] else 'false'}</itunes:explicit>
{chr(10).join(items)}
  </channel>
</rss>
"""
    (HERE / 'feed.xml').write_text(feed, encoding='utf-8', newline='\n')
    print(f"feed.xml written: {len(episodes)} episode(s)")


if __name__ == '__main__':
    main()
