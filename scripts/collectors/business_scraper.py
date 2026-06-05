#!/usr/bin/env python3
"""商业数据源爬虫 - 赢商网、IT桔子、巨潮资讯"""

import requests
from bs4 import BeautifulSoup
import sqlite3
import os
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'ooh_signal.db')

import sys
sys.path.insert(0, os.path.dirname(__file__))
from signal_utils import save_signal_safe

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

def save_signal(conn, brand_name, industry, signal_type, title, summary, source_url, source_name):
    """保存信号到数据库（使用共享去重逻辑）"""
    return save_signal_safe(conn, brand_name, industry, signal_type, title, summary, source_url, source_name)

def scrape_winshang():
    """爬取赢商网 - 商业地产新闻"""
    print("Scraping 赢商网...")
    try:
        url = "https://www.winshang.com/news.html"
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'lxml')

        items = soup.select('div.news-item, li.news-item, div.list-item')[:20]
        conn = sqlite3.connect(DB_PATH)
        count = 0

        for item in items:
            link_elem = item.select_one('a[href]')
            if not link_elem:
                continue

            title = link_elem.get_text(strip=True)
            href = link_elem.get('href', '')
            if not href.startswith('http'):
                href = "https://www.winshang.com" + href

            summary_elem = item.select_one('p, div.desc, div.summary')
            summary = summary_elem.get_text(strip=True) if summary_elem else ''

            if save_signal(conn, '待识别', '商业地产', 'expansion', title, summary, href, '赢商网'):
                count += 1

        conn.commit()
        conn.close()
        print(f"  Scraped {count} articles from 赢商网")
    except Exception as e:
        print(f"  Error scraping 赢商网: {e}")

def scrape_cninfo():
    """爬取巨潮资讯 - 上市公司公告"""
    print("Scraping 巨潮资讯...")
    try:
        # 使用巨潮资讯的API获取最新公告
        api_url = "http://www.cninfo.com.cn/new/hisAnnouncement/query"
        params = {
            'pageNum': 1,
            'pageSize': 30,
            'tabName': 'fulltext',
            'plate': '',
            'stock': '',
            'searchkey': '',
            'secid': '',
            'category': '',
            'trade': '',
            'seDate': '',
        }

        response = requests.post(api_url, headers=HEADERS, data=params, timeout=30)
        data = response.json()

        conn = sqlite3.connect(DB_PATH)
        count = 0

        for item in data.get('announcements', []):
            title = item.get('announcementTitle', '')
            if not title:
                continue

            # 过滤出与品牌、融资、扩张相关的公告
            keywords = ['融资', '投资', '扩张', '收购', '合并', '新店', '开业', '品牌']
            if not any(kw in title for kw in keywords):
                continue

            sec_name = item.get('secName', '未知公司')
            announcement_url = f"http://www.cninfo.com.cn/new/disclosure/detail?announcementId={item.get('announcementId', '')}"

            save_signal(conn, sec_name, '', 'industry', title, title, announcement_url, '巨潮资讯')
            count += 1

        conn.commit()
        conn.close()
        print(f"  Scraped {count} announcements from 巨潮资讯")
    except Exception as e:
        print(f"  Error scraping 巨潮资讯: {e}")

def scrape_sina_finance():
    """爬取新浪财经 - 企业动态"""
    print("Scraping 新浪财经...")
    try:
        url = "https://finance.sina.com.cn/roll/index.d.html?cid=56592"
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'lxml')

        items = soup.select('ul.list_009 li, div.feed-card-item')[:20]
        conn = sqlite3.connect(DB_PATH)
        count = 0

        for item in items:
            link_elem = item.select_one('a[href]')
            if not link_elem:
                continue

            title = link_elem.get_text(strip=True)
            href = link_elem.get('href', '')
            if not href.startswith('http'):
                href = "https://finance.sina.com.cn" + href

            if save_signal(conn, '待识别', '财经', 'industry', title, title, href, '新浪财经'):
                count += 1

        conn.commit()
        conn.close()
        print(f"  Scraped {count} articles from 新浪财经")
    except Exception as e:
        print(f"  Error scraping 新浪财经: {e}")

def collect_business():
    """运行所有商业数据源爬虫"""
    scrape_winshang()
    scrape_cninfo()
    scrape_sina_finance()

if __name__ == '__main__':
    collect_business()
