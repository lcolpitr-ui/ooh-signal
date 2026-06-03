#!/usr/bin/env python3
"""社交媒体爬虫 - 微博移动端API"""

import requests
import sqlite3
import os
import hashlib
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'ooh_signal.db')

# 微博移动端API（无需登录）
WEIBO_API = "https://m.weibo.cn/api/container/getIndex"

# 搜索关键词配置：品牌投放相关
SEARCH_KEYWORDS = [
    "开店", "新店", "门店扩张", "融资", "IPO",
    "新品发布", "品牌升级", "广告投放", "营销",
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Referer': 'https://m.weibo.cn/',
    'X-Requested-With': 'XMLHttpRequest',
}

def generate_id(url, title):
    return hashlib.md5(f"{url}:{title}".encode()).hexdigest()

def save_signal(conn, brand_name, industry, signal_type, title, summary, source_url, source_name):
    """保存信号到数据库"""
    cursor = conn.cursor()
    signal_id = generate_id(source_url, title)

    cursor.execute('SELECT id FROM signals WHERE id = ?', (signal_id,))
    if cursor.fetchone():
        return False

    cursor.execute('''
        INSERT INTO signals (id, brand_name, industry, signal_type, title, summary, source_url, source_name, published_at, collected_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (signal_id, brand_name, industry, signal_type, title, summary[:500], source_url, source_name, datetime.now().isoformat(), datetime.now().isoformat()))
    return True

def get_known_brands():
    """从数据库获取已识别的品牌列表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM brands WHERE name != '待识别' LIMIT 50")
    brands = [row[0] for row in cursor.fetchall()]
    conn.close()
    return brands

def scrape_weibo_search(keyword, max_results=10):
    """通过微博移动端搜索API采集数据"""
    try:
        # 使用容器ID进行搜索
        containerid = f"100103type=1&q={keyword}"
        params = {
            'containerid': containerid,
            'page_type': 'searchall',
        }

        response = requests.get(WEIBO_API, params=params, headers=HEADERS, timeout=15)
        data = response.json()

        if data.get('ok') != 1:
            return []

        results = []
        cards = data.get('data', {}).get('cards', [])

        for card in cards:
            # 博文卡片
            if card.get('card_type') == 9:
                mblog = card.get('mblog', {})
                if not mblog:
                    continue

                text = mblog.get('text', '')
                # 去除HTML标签
                import re
                clean_text = re.sub(r'<[^>]+>', '', text).strip()

                if len(clean_text) < 10:
                    continue

                user = mblog.get('user', {})
                author = user.get('screen_name', '微博用户')
                mid = mblog.get('mid', '')
                url = f"https://weibo.com/{user.get('id', '')}/{mid}"

                results.append({
                    'title': clean_text[:80] + ('...' if len(clean_text) > 80 else ''),
                    'summary': clean_text,
                    'url': url,
                    'author': author,
                })

            # 搜索结果卡片组
            elif card.get('card_group'):
                for item in card.get('card_group', []):
                    if item.get('card_type') == 9:
                        mblog = item.get('mblog', {})
                        if not mblog:
                            continue

                        text = mblog.get('text', '')
                        import re
                        clean_text = re.sub(r'<[^>]+>', '', text).strip()

                        if len(clean_text) < 10:
                            continue

                        user = mblog.get('user', {})
                        author = user.get('screen_name', '微博用户')
                        mid = mblog.get('mid', '')
                        url = f"https://weibo.com/{user.get('id', '')}/{mid}"

                        results.append({
                            'title': clean_text[:80] + ('...' if len(clean_text) > 80 else ''),
                            'summary': clean_text,
                            'url': url,
                            'author': author,
                        })

        return results[:max_results]

    except Exception as e:
        print(f"  Error searching weibo for '{keyword}': {e}")
        return []

def collect_weibo():
    """采集微博品牌相关数据"""
    print("Scraping 微博...")
    conn = sqlite3.connect(DB_PATH)
    total_count = 0

    # 用已知品牌名搜索
    brands = get_known_brands()
    if not brands:
        # 如果没有已知品牌，用通用关键词
        brands = SEARCH_KEYWORDS

    searched = set()
    for brand in brands[:15]:  # 限制搜索量
        if brand in searched:
            continue
        searched.add(brand)

        results = scrape_weibo_search(brand, max_results=5)
        for item in results:
            if save_signal(conn, brand, '', 'industry', item['title'], item['summary'], item['url'], '微博'):
                total_count += 1

    # 再用通用投放关键词补充搜索
    for keyword in SEARCH_KEYWORDS[:5]:
        results = scrape_weibo_search(keyword, max_results=3)
        for item in results:
            if save_signal(conn, '待识别', '', 'industry', item['title'], item['summary'], item['url'], '微博'):
                total_count += 1

    conn.commit()
    conn.close()
    print(f"  Collected {total_count} signals from 微博")

def collect_social():
    """运行所有社交媒体采集器"""
    collect_weibo()
    # 小红书和抖音待后续实现（反爬严格，需Playwright）

if __name__ == '__main__':
    collect_social()
