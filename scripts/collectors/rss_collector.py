import feedparser
import sqlite3
import json
import os
import hashlib
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'ooh_signal.db')
SOURCES_PATH = os.path.join(os.path.dirname(__file__), '..', 'config', 'sources.json')

def load_sources():
    with open(SOURCES_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_id(url, title):
    return hashlib.md5(f"{url}:{title}".encode()).hexdigest()

def collect_rss():
    sources = load_sources()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for source in sources.get('rss_sources', []):
        print(f"Collecting from {source['name']}...")
        try:
            feed = feedparser.parse(source['url'])
            for entry in feed.entries[:20]:
                signal_id = generate_id(entry.get('link', ''), entry.get('title', ''))

                cursor.execute('SELECT id FROM signals WHERE id = ?', (signal_id,))
                if cursor.fetchone():
                    continue

                cursor.execute('''
                    INSERT INTO signals (id, brand_name, industry, signal_type, title, summary, source_url, source_name, published_at, collected_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    signal_id,
                    '待识别',
                    source.get('category', ''),
                    source.get('type', 'industry'),
                    entry.get('title', ''),
                    entry.get('summary', '')[:500],
                    entry.get('link', ''),
                    source['name'],
                    entry.get('published', datetime.now(timezone.utc).isoformat()),
                    datetime.now(timezone.utc).isoformat()
                ))

            print(f"  Collected {len(feed.entries)} entries from {source['name']}")
        except Exception as e:
            print(f"  Error collecting from {source['name']}: {e}")

    conn.commit()
    conn.close()

if __name__ == '__main__':
    collect_rss()
