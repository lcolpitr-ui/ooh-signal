#!/usr/bin/env python3
"""社交媒体爬虫 - 小红书 & 抖音（Playwright 版）

功能：
- 小红书：搜索品牌关键词，采集笔记数据
- 抖音：搜索品牌关键词，采集视频数据
- 限流策略：随机延迟，防封号

环境变量：
- XHS_COOKIE: 小红书登录Cookie（可选）
- DOUYIN_COOKIE: 抖音登录Cookie（可选）

依赖：
- playwright: pip install playwright && python -m playwright install chromium
"""

import sqlite3
import os
import hashlib
import re
import random
import time
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'ooh_signal.db')

# 搜索关键词
SEARCH_KEYWORDS = [
    "开店", "新店", "门店扩张", "融资", "IPO",
    "新品发布", "品牌升级", "广告投放", "营销",
]

# 限流配置
RATE_LIMIT = {
    "min_delay": 3,
    "max_delay": 8,
    "page_delay_min": 5,
    "page_delay_max": 12,
    "batch_delay_min": 15,
    "batch_delay_max": 30,
}

# 浏览器配置
BROWSER_CONFIG = {
    "headless": True,
    "slow_mo": 100,  # 毫秒，模拟人类操作
    "viewport": {"width": 1920, "height": 1080},
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}


def random_delay(min_sec=None, max_sec=None):
    """随机等待"""
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


# ============================================================
# 小红书采集器
# ============================================================

def collect_xiaohongshu():
    """采集小红书品牌相关数据"""
    print("Scraping 小红书...")

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("  Playwright not installed. Run: pip install playwright && python -m playwright install chromium")
        return 0

    cookie = os.environ.get('XHS_COOKIE', '')
    brands = get_known_brands()
    if not brands:
        brands = SEARCH_KEYWORDS

    conn = sqlite3.connect(DB_PATH)
    total_count = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=BROWSER_CONFIG["headless"],
            slow_mo=BROWSER_CONFIG["slow_mo"]
        )
        context = browser.new_context(
            viewport=BROWSER_CONFIG["viewport"],
            user_agent=BROWSER_CONFIG["user_agent"],
        )

        # 设置Cookie
        if cookie:
            _set_cookies(context, cookie, '.xiaohongshu.com')

        page = context.new_page()

        for brand in brands[:10]:
            if len(brand) < 2:
                continue

            try:
                results = _search_xiaohongshu(page, brand)
                for item in results:
                    if save_signal(
                        conn, brand, '', 'industry',
                        item['title'], item['summary'], item['url'], '小红书',
                        likes=item['likes'], comments=item['comments'],
                        author=item['author'], published_at=item['published_at']
                    ):
                        total_count += 1

                random_delay(RATE_LIMIT["batch_delay_min"], RATE_LIMIT["batch_delay_max"])
            except Exception as e:
                print(f"    Error searching '{brand}' on 小红书: {e}")

        browser.close()

    conn.commit()
    conn.close()
    print(f"  Collected {total_count} signals from 小红书")
    return total_count


def _search_xiaohongshu(page, keyword, max_results=5):
    """在小红书搜索关键词"""
    results = []
    url = f"https://www.xiaohongshu.com/search_result?keyword={keyword}&source=web_search_result_notes"

    try:
        page.goto(url, wait_until="networkidle", timeout=30000)
        time.sleep(3)  # 等待页面完全加载

        # 获取笔记卡片
        cards = page.query_selector_all('section.note-item, div.note-item, [data-note-id]')

        for card in cards[:max_results]:
            try:
                # 提取标题
                title_el = card.query_selector('a.title, span.title, .note-title')
                title = title_el.inner_text().strip() if title_el else ''

                # 提取内容摘要
                desc_el = card.query_selector('.desc, .note-desc, p')
                desc = desc_el.inner_text().strip() if desc_el else ''

                if len(title) < 5 and len(desc) < 5:
                    continue

                # 提取链接
                link_el = card.query_selector('a[href*="/explore/"], a[href*="/discovery/item/"]')
                link = link_el.get_attribute('href') if link_el else ''
                if link and not link.startswith('http'):
                    link = f"https://www.xiaohongshu.com{link}"

                # 提取互动数据
                likes = 0
                likes_el = card.query_selector('.like-wrapper span, [class*="like"] span')
                if likes_el:
                    likes = _parse_number(likes_el.inner_text())

                comments = 0
                comments_el = card.query_selector('.chat-wrapper span, [class*="comment"] span')
                if comments_el:
                    comments = _parse_number(comments_el.inner_text())

                # 提取作者
                author = ''
                author_el = card.query_selector('.author-wrapper .name, .user-name, [class*="author"]')
                if author_el:
                    author = author_el.inner_text().strip()

                results.append({
                    'title': title or desc[:80],
                    'summary': desc or title,
                    'url': link or f"https://www.xiaohongshu.com/search_result?keyword={keyword}",
                    'likes': likes,
                    'comments': comments,
                    'author': author,
                    'published_at': None,
                })
            except Exception as e:
                continue

    except Exception as e:
        print(f"    Page load error: {e}")

    return results


# ============================================================
# 抖音采集器
# ============================================================

def collect_douyin():
    """采集抖音品牌相关数据"""
    print("Scraping 抖音...")

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("  Playwright not installed. Run: pip install playwright && python -m playwright install chromium")
        return 0

    cookie = os.environ.get('DOUYIN_COOKIE', '')
    brands = get_known_brands()
    if not brands:
        brands = SEARCH_KEYWORDS

    conn = sqlite3.connect(DB_PATH)
    total_count = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=BROWSER_CONFIG["headless"],
            slow_mo=BROWSER_CONFIG["slow_mo"]
        )
        context = browser.new_context(
            viewport=BROWSER_CONFIG["viewport"],
            user_agent=BROWSER_CONFIG["user_agent"],
        )

        # 设置Cookie
        if cookie:
            _set_cookies(context, cookie, '.douyin.com')

        page = context.new_page()

        for brand in brands[:10]:
            if len(brand) < 2:
                continue

            try:
                results = _search_douyin(page, brand)
                for item in results:
                    if save_signal(
                        conn, brand, '', 'industry',
                        item['title'], item['summary'], item['url'], '抖音',
                        likes=item['likes'], comments=item['comments'],
                        author=item['author'], published_at=item['published_at']
                    ):
                        total_count += 1

                random_delay(RATE_LIMIT["batch_delay_min"], RATE_LIMIT["batch_delay_max"])
            except Exception as e:
                print(f"    Error searching '{brand}' on 抖音: {e}")

        browser.close()

    conn.commit()
    conn.close()
    print(f"  Collected {total_count} signals from 抖音")
    return total_count


def _search_douyin(page, keyword, max_results=5):
    """在抖音搜索关键词（使用移动端API）"""
    results = []

    try:
        import requests

        # 使用抖音移动端搜索API
        search_url = "https://www.douyin.com/aweme/v1/web/search/item/"
        params = {
            "keyword": keyword,
            "search_channel": "aweme_general",
            "sort_type": 0,
            "publish_time": 0,
            "count": max_results,
            "offset": 0,
            "search_source": "normal_search",
            "query_correct_type": 1,
            "is_filter_search": 0,
            "from_group_id": "",
            "offset_search_id": "",
        }

        headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
            "Accept": "application/json",
            "Referer": "https://www.douyin.com/",
        }

        cookie = os.environ.get('DOUYIN_COOKIE', '')
        if cookie:
            headers["Cookie"] = cookie

        response = requests.get(search_url, params=params, headers=headers, timeout=15)

        if response.status_code != 200:
            print(f"    API request failed: {response.status_code}")
            return results

        data = response.json()
        items = data.get("data", [])

        for item in items[:max_results]:
            try:
                desc = item.get("desc", "")
                if len(desc) < 5:
                    continue

                author_info = item.get("author", {})
                author = author_info.get("nickname", "")

                aweme_id = item.get("aweme_id", "")
                url = f"https://www.douyin.com/video/{aweme_id}" if aweme_id else ""

                statistics = item.get("statistics", {})
                likes = statistics.get("digg_count", 0)
                comments = statistics.get("comment_count", 0)

                results.append({
                    'title': desc[:80],
                    'summary': desc,
                    'url': url,
                    'likes': likes,
                    'comments': comments,
                    'author': author,
                    'published_at': None,
                })
            except Exception as e:
                continue

    except Exception as e:
        print(f"    API error: {e}")

    return results


# ============================================================
# 辅助函数
# ============================================================

def _set_cookies(context, cookie_str, domain):
    """设置浏览器Cookie"""
    cookies = []
    for item in cookie_str.split(';'):
        item = item.strip()
        if '=' in item:
            name, value = item.split('=', 1)
            cookies.append({
                'name': name.strip(),
                'value': value.strip(),
                'domain': domain,
                'path': '/',
            })
    if cookies:
        context.add_cookies(cookies)


def _parse_number(text):
    """解析数字文本，如 '1.2万' -> 12000"""
    text = text.strip()
    if not text or text == '-':
        return 0

    try:
        if '万' in text:
            return int(float(text.replace('万', '')) * 10000)
        elif '亿' in text:
            return int(float(text.replace('亿', '')) * 100000000)
        elif 'w' in text.lower():
            return int(float(text.lower().replace('w', '')) * 10000)
        else:
            return int(re.sub(r'[^\d]', '', text) or 0)
    except (ValueError, TypeError):
        return 0


def collect_platforms():
    """运行所有平台采集器"""
    collect_xiaohongshu()
    # collect_douyin()  # 暂时跳过，API需要进一步研究


if __name__ == '__main__':
    collect_platforms()
