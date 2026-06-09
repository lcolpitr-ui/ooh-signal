#!/usr/bin/env python3
"""社交媒体爬虫 - 微博移动端API（支持Cookie认证）"""

import requests
import sqlite3
import os
import re
import json
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'ooh_signal.db')

import sys
sys.path.insert(0, os.path.dirname(__file__))
from signal_utils import save_signal_safe

WEIBO_API = "https://m.weibo.cn/api/container/getIndex"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Referer': 'https://m.weibo.cn/',
    'X-Requested-With': 'XMLHttpRequest',
}

def get_cookies():
    """从环境变量获取微博Cookie"""
    cookie_str = os.environ.get('WEIBO_COOKIE', '')
    if not cookie_str:
        return {}
    cookies = {}
    for item in cookie_str.split(';'):
        item = item.strip()
        if '=' in item:
            key, value = item.split('=', 1)
            cookies[key.strip()] = value.strip()
    return cookies

def save_signal(conn, brand_name, industry, signal_type, title, summary, source_url, source_name):
    """保存信号到数据库（使用共享去重逻辑）"""
    return save_signal_safe(conn, brand_name, industry, signal_type, title, summary, source_url, source_name)

def get_known_brands():
    """从数据库获取已识别的品牌列表（按信号数排序，优先搜索信号少的品牌）"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM brands WHERE name != '待识别' ORDER BY signal_count ASC, name ASC LIMIT 100")
    brands = [row[0] for row in cursor.fetchall()]
    conn.close()
    return brands

def scrape_weibo_search(keyword, max_results=5):
    """通过微博移动端搜索API采集数据"""
    try:
        # type=1=综合搜索，type=61=实时搜索（可能返回空结果）
        containerid = f"100103type=1&q={keyword}"
        params = {
            'containerid': containerid,
            'page_type': 'searchall',
        }

        cookies = get_cookies()
        response = requests.get(
            WEIBO_API,
            params=params,
            headers=HEADERS,
            cookies=cookies,
            timeout=15,
        )

        if response.status_code != 200:
            return []

        data = response.json()
        if data.get('ok') != 1:
            return []

        results = []
        cards = data.get('data', {}).get('cards', [])

        for card in cards:
            card_type = card.get('card_type')

            # 博文卡片
            if card_type == 9:
                mblog = card.get('mblog', {})
                if not mblog:
                    continue

                text = mblog.get('text', '')
                clean_text = re.sub(r'<[^>]+>', '', text).strip()
                if len(clean_text) < 10:
                    continue

                user = mblog.get('user', {})
                author = user.get('screen_name', '微博用户')
                mid = mblog.get('mid', '')
                uid = user.get('id', '')
                url = f"https://weibo.com/{uid}/{mid}" if uid and mid else ''

                results.append({
                    'title': clean_text[:80] + ('...' if len(clean_text) > 80 else ''),
                    'summary': clean_text,
                    'url': url,
                    'author': author,
                })

            # 搜索结果卡片组
            elif card.get('card_group'):
                for item in card['card_group']:
                    if item.get('card_type') != 9:
                        continue
                    mblog = item.get('mblog', {})
                    if not mblog:
                        continue

                    text = mblog.get('text', '')
                    clean_text = re.sub(r'<[^>]+>', '', text).strip()
                    if len(clean_text) < 10:
                        continue

                    user = mblog.get('user', {})
                    author = user.get('screen_name', '微博用户')
                    mid = mblog.get('mid', '')
                    uid = user.get('id', '')
                    url = f"https://weibo.com/{uid}/{mid}" if uid and mid else ''

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

    # 1. 搜索已知品牌（每次轮询更多品牌）
    brands = get_known_brands()
    if not brands:
        brands = ['开店', '新店', '融资', 'IPO', '品牌升级']

    searched = set()
    for brand in brands[:50]:  # 每次搜索50个品牌
        if brand in searched or len(brand) < 2:
            continue
        searched.add(brand)

        results = scrape_weibo_search(brand, max_results=3)
        for item in results:
            if save_signal(conn, brand, '', 'industry', item['title'], item['summary'], item['url'], '微博'):
                total_count += 1

    # 2. 搜索品牌营销相关关键词（更多关键词，更多结果）
    keywords = [
        # 代言人/明星合作（高优先级）
        '官宣代言人', '品牌代言人', '全球代言人', '品牌大使',
        # 品牌活动/营销
        '品牌活动', '线下活动', '快闪', '品牌联名',
        # 商业扩张
        '新店开业', '门店扩张', '融资', 'IPO',
        # 展会/活动
        '发布会', '展会', '峰会',
        # 营销动态
        '品牌升级', '广告投放', '官宣合作',
    ]
    for keyword in keywords:
        results = scrape_weibo_search(keyword, max_results=5)  # 每个关键词取5条
        for item in results:
            if save_signal(conn, '待识别', '', 'industry', item['title'], item['summary'], item['url'], '微博'):
                total_count += 1

    conn.commit()
    conn.close()
    print(f"  Collected {total_count} signals from 微博")

def collect_social():
    """运行所有社交媒体采集器"""
    collect_weibo()

if __name__ == '__main__':
    collect_social()
