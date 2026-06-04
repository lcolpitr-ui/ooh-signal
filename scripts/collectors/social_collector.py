#!/usr/bin/env python3
"""社交媒体爬虫 - 微博API（增强版）

功能：
- 两种模式：热搜模式（无需登录）/ 搜索模式（需Cookie）
- 提取互动数据（点赞、转发、评论）
- 随机限流防封
- 分页支持

环境变量：
- WEIBO_COOKIE: 微博登录Cookie（可选，启用搜索模式）
"""

import requests
import sqlite3
import os
import hashlib
import json
import re
import random
import time
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'ooh_signal.db')

# 微博API
WEIBO_API = "https://m.weibo.cn/api/container/getIndex"
WEIBO_HOT_API = "https://weibo.com/ajax/statuses/hot_band"

# 搜索关键词配置：品牌投放相关
SEARCH_KEYWORDS = [
    "开店", "新店", "门店扩张", "融资", "IPO",
    "新品发布", "品牌升级", "广告投放", "营销",
]

# 限流配置（参考weiboSpider策略）
RATE_LIMIT = {
    "min_delay": 3,
    "max_delay": 8,
    "page_delay_min": 5,
    "page_delay_max": 12,
    "batch_delay_min": 10,
    "batch_delay_max": 20,
    "max_retries": 3,
    "retry_delay": 30,
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'zh-CN,z;q=0.9',
    'Referer': 'https://weibo.com/',
}

# Cookie（可选，从环境变量读取）
WEIBO_COOKIE = os.environ.get('WEIBO_COOKIE', '')


def random_delay(min_sec=None, max_sec=None):
    """随机等待，防止被封"""
    min_sec = min_sec or RATE_LIMIT["min_delay"]
    max_sec = max_sec or RATE_LIMIT["max_delay"]
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)


def generate_id(url, title):
    return hashlib.md5(f"{url}:{title}".encode()).hexdigest()


def clean_html(text):
    """去除HTML标签"""
    return re.sub(r'<[^>]+>', '', text).strip()


def save_signal(conn, brand_name, industry, signal_type, title, summary,
                source_url, source_name, likes=0, reposts=0, comments=0,
                author='', author_followers=0, published_at=None):
    """保存信号到数据库"""
    cursor = conn.cursor()
    signal_id = generate_id(source_url, title)

    cursor.execute('SELECT id FROM signals WHERE id = ?', (signal_id,))
    if cursor.fetchone():
        return False

    cursor.execute('''
        INSERT INTO signals (id, brand_name, industry, signal_type, title, summary,
            source_url, source_name, published_at, collected_at,
            likes, reposts, comments, author, author_followers)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        signal_id, brand_name, industry, signal_type, title, summary[:500],
        source_url, source_name,
        published_at or datetime.now().isoformat(),
        datetime.now().isoformat(),
        likes, reposts, comments, author, author_followers
    ))
    return True


def get_known_brands():
    """从数据库获取已识别的品牌列表"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM brands WHERE name != '待识别' LIMIT 50")
        brands = [row[0] for row in cursor.fetchall()]
        conn.close()
        return brands
    except Exception as e:
        print(f"  Warning: Could not load brands: {e}")
        return []


def fetch_hot_search():
    """获取微博热搜榜（无需登录）"""
    try:
        response = requests.get(WEIBO_HOT_API, headers=HEADERS, timeout=15)
        data = response.json()

        if data.get('ok') != 1:
            print("  Failed to fetch hot search")
            return []

        results = []
        band_list = data.get('data', {}).get('band_list', [])

        for item in band_list:
            word = item.get('word', '')
            hot_num = item.get('raw_hot', 0)
            category = item.get('category', '')
            flag_desc = item.get('flag_desc', '')

            if word and len(word) >= 2:
                results.append({
                    'keyword': word,
                    'hot_num': hot_num,
                    'category': category,
                    'flag_desc': flag_desc,
                })

        return results

    except Exception as e:
        print(f"  Error fetching hot search: {e}")
        return []


def scrape_weibo_search_with_cookie(keyword, max_pages=2, max_results=20):
    """通过微博移动端搜索API采集数据（需要Cookie）"""
    if not WEIBO_COOKIE:
        return []

    all_results = []
    headers = {**HEADERS, 'Cookie': WEIBO_COOKIE}

    for page in range(1, max_pages + 1):
        try:
            containerid = f"100103type=1&q={keyword}"
            params = {
                'containerid': containerid,
                'page_type': 'searchall',
                'page': page,
            }

            for retry in range(RATE_LIMIT["max_retries"]):
                try:
                    response = requests.get(
                        WEIBO_API,
                        params=params,
                        headers=headers,
                        timeout=15
                    )
                    data = response.json()
                    break
                except Exception as e:
                    if retry < RATE_LIMIT["max_retries"] - 1:
                        print(f"    Retry {retry + 1}/{RATE_LIMIT['max_retries']}: {e}")
                        time.sleep(RATE_LIMIT["retry_delay"])
                    else:
                        return all_results

            if data.get('ok') != 1:
                if 'freq' in str(data.get('msg', '')):
                    print(f"    Rate limited, waiting {RATE_LIMIT['retry_delay']}s...")
                    time.sleep(RATE_LIMIT["retry_delay"])
                break

            cards = data.get('data', {}).get('cards', [])

            for card in cards:
                if card.get('card_type') == 9:
                    result = parse_weibo_card(card)
                    if result:
                        all_results.append(result)
                elif card.get('card_group'):
                    for item in card.get('card_group', []):
                        if item.get('card_type') == 9:
                            result = parse_weibo_card(item)
                            if result:
                                all_results.append(result)

            if page < max_pages:
                random_delay(RATE_LIMIT["page_delay_min"], RATE_LIMIT["page_delay_max"])

        except Exception as e:
            print(f"    Error on page {page}: {e}")
            break

    return all_results[:max_results]


def parse_weibo_card(card):
    """解析单条微博卡片"""
    mblog = card.get('mblog', {})
    if not mblog:
        return None

    text = mblog.get('text', '')
    clean_text = clean_html(text)

    if len(clean_text) < 10:
        return None

    user = mblog.get('user', {})
    author = user.get('screen_name', '微博用户')
    author_followers = user.get('followers_count', 0) or 0
    user_id = user.get('id', '')
    mid = mblog.get('mid', '')
    url = f"https://weibo.com/{user_id}/{mid}"

    likes = mblog.get('attitudes_count', 0) or 0
    reposts = mblog.get('reposts_count', 0) or 0
    comments = mblog.get('comments_count', 0) or 0

    created_at = mblog.get('created_at', '')
    published_at = None
    if created_at:
        try:
            from email.utils import parsedate_to_datetime
            published_at = parsedate_to_datetime(created_at).isoformat()
        except Exception:
            published_at = created_at

    return {
        'title': clean_text[:80] + ('...' if len(clean_text) > 80 else ''),
        'summary': clean_text,
        'url': url,
        'author': author,
        'author_followers': author_followers,
        'likes': likes,
        'reposts': reposts,
        'comments': comments,
        'published_at': published_at,
    }


def collect_weibo_hot(conn):
    """从热搜榜采集品牌相关数据"""
    print("  Fetching hot search trends...")
    hot_items = fetch_hot_search()

    if not hot_items:
        print("  No hot search data")
        return 0

    brands = get_known_brands()
    brand_set = set(brands)
    total_count = 0

    for item in hot_items:
        keyword = item['keyword']
        # 检查是否与已知品牌相关
        matched_brand = None
        for brand in brand_set:
            if brand in keyword or keyword in brand:
                matched_brand = brand
                break

        if not matched_brand:
            # 检查是否包含行业关键词
            for kw in SEARCH_KEYWORDS:
                if kw in keyword:
                    matched_brand = '待识别'
                    break

        if matched_brand:
            if save_signal(
                conn, matched_brand, '', 'industry',
                f"微博热搜: {keyword}",
                f"热度: {item['hot_num']:,} | 分类: {item['category']} | {item['flag_desc']}",
                f"https://s.weibo.com/weibo?q=%23{keyword}%23",
                '微博热搜',
                likes=item['hot_num'],
                published_at=datetime.now().isoformat()
            ):
                total_count += 1

    return total_count


def collect_weibo_search(conn):
    """通过搜索API采集品牌数据（需要Cookie）"""
    if not WEIBO_COOKIE:
        print("  Skipping search (no WEIBO_COOKIE set)")
        return 0

    print("  Searching with cookie...")
    total_count = 0

    brands = get_known_brands()
    if not brands:
        brands = SEARCH_KEYWORDS

    searched = set()

    for brand in brands[:15]:
        if brand in searched or len(brand) < 2:
            continue
        searched.add(brand)

        results = scrape_weibo_search_with_cookie(brand, max_pages=2, max_results=5)
        for item in results:
            if save_signal(
                conn, brand, '', 'industry',
                item['title'], item['summary'], item['url'], '微博',
                likes=item['likes'], reposts=item['reposts'],
                comments=item['comments'], author=item['author'],
                author_followers=item['author_followers'],
                published_at=item['published_at']
            ):
                total_count += 1

        random_delay(RATE_LIMIT["batch_delay_min"], RATE_LIMIT["batch_delay_max"])

    return total_count


def collect_weibo():
    """采集微博品牌相关数据"""
    print("Scraping 微博 (增强版)...")
    conn = sqlite3.connect(DB_PATH)
    total_count = 0

    # 模式1：热搜（无需登录）
    total_count += collect_weibo_hot(conn)

    # 模式2：搜索（需要Cookie）
    total_count += collect_weibo_search(conn)

    conn.commit()
    conn.close()
    print(f"  Collected {total_count} signals from 微博")


def collect_social():
    """运行所有社交媒体采集器"""
    collect_weibo()
    # 小红书和抖音待后续实现（反爬严格，需Playwright）


if __name__ == '__main__':
    collect_social()
