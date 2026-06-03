#!/usr/bin/env python3
"""网页爬虫 - 采集商业新闻"""

import requests
from bs4 import BeautifulSoup
import sqlite3
import os
import hashlib
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'ooh_signal.db')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def generate_id(url, title):
    return hashlib.md5(f"{url}:{title}".encode()).hexdigest()

def scrape_36kr_news():
    """爬取 36kr 新闻"""
    print("Scraping 36kr news...")
    try:
        url = "https://36kr.com/newsflashes"
        response = requests.get(url, headers=HEADERS, timeout=30)
        soup = BeautifulSoup(response.text, 'lxml')

        articles = soup.select('div.newsflash-item')[:20]
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        count = 0
        for article in articles:
            title_elem = article.select_one('a.title')
            if not title_elem:
                continue

            title = title_elem.text.strip()
            link = "https://36kr.com" + title_elem.get('href', '')
            summary_elem = article.select_one('p.description')
            summary = summary_elem.text.strip()[:500] if summary_elem else ''

            signal_id = generate_id(link, title)

            cursor.execute('SELECT id FROM signals WHERE id = ?', (signal_id,))
            if cursor.fetchone():
                continue

            cursor.execute('''
                INSERT INTO signals (id, brand_name, industry, signal_type, title, summary, source_url, source_name, published_at, collected_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (signal_id, '待识别', '科技/创业', 'industry', title, summary, link, '36kr', datetime.now().isoformat(), datetime.now().isoformat()))
            count += 1

        conn.commit()
        conn.close()
        print(f"  Scraped {count} articles from 36kr")
    except Exception as e:
        print(f"  Error scraping 36kr: {e}")

def scrape_itjuzi_funding():
    """爬取 IT桔子融资信息"""
    print("Scraping ITjuzi funding...")
    try:
        url = "https://www.itjuzi.com/investevents"
        response = requests.get(url, headers=HEADERS, timeout=30)
        soup = BeautifulSoup(response.text, 'lxml')

        items = soup.select('div.list-item')[:20]
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        count = 0
        for item in items:
            title_elem = item.select_one('a.name')
            if not title_elem:
                continue

            brand_name = title_elem.text.strip()
            detail_elem = item.select_one('div.detail')
            summary = detail_elem.text.strip()[:500] if detail_elem else ''

            signal_id = generate_id(url, brand_name)

            cursor.execute('SELECT id FROM signals WHERE id = ?', (signal_id,))
            if cursor.fetchone():
                continue

            cursor.execute('''
                INSERT INTO signals (id, brand_name, industry, signal_type, title, summary, source_url, source_name, published_at, collected_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (signal_id, brand_name, '', 'funding', f"{brand_name} 获得融资", summary, url, 'IT桔子', datetime.now().isoformat(), datetime.now().isoformat()))
            count += 1

        conn.commit()
        conn.close()
        print(f"  Scraped {count} funding events from ITjuzi")
    except Exception as e:
        print(f"  Error scraping ITjuzi: {e}")

def collect_web():
    """运行所有网页爬虫"""
    scrape_36kr_news()
    scrape_itjuzi_funding()

if __name__ == '__main__':
    collect_web()
