import feedparser
import sqlite3
import json
import os
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'ooh_signal.db')
SOURCES_PATH = os.path.join(os.path.dirname(__file__), '..', 'config', 'sources.json')

import sys
sys.path.insert(0, os.path.dirname(__file__))
from signal_utils import save_signal_safe

def load_sources():
    with open(SOURCES_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def collect_rss():
    sources = load_sources()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for source in sources.get('rss_sources', []):
        print(f"Collecting from {source['name']}...")
        try:
            feed = feedparser.parse(source['url'])
            for entry in feed.entries[:20]:
                save_signal_safe(
                    conn,
                    brand_name='待识别',
                    industry=source.get('category', ''),
                    signal_type=source.get('type', 'industry'),
                    title=entry.get('title', ''),
                    summary=entry.get('summary', ''),
                    source_url=entry.get('link', ''),
                    source_name=source['name'],
                    published_at=entry.get('published', None)
                )

            print(f"  Collected {len(feed.entries)} entries from {source['name']}")
        except Exception as e:
            print(f"  Error collecting from {source['name']}: {e}")

    conn.commit()
    conn.close()

if __name__ == '__main__':
    collect_rss()
