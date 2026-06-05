#!/usr/bin/env python3
"""信号采集工具模块 - 去重、链接检查等共享逻辑"""

import hashlib
import sqlite3
import re
from difflib import SequenceMatcher
from urllib.parse import urlparse


def generate_id(url: str, title: str) -> str:
    """生成信号唯一ID（MD5哈希）"""
    return hashlib.md5(f"{url}:{title}".encode()).hexdigest()


def normalize_title(title: str) -> str:
    """标准化标题，用于相似度比较"""
    # 去除标点符号、空格、特殊字符
    title = re.sub(r'[^\w一-鿿]', '', title)
    # 统一大小写
    return title.lower().strip()


def is_similar_title(title1: str, title2: str, threshold: float = 0.85) -> bool:
    """判断两个标题是否相似"""
    if not title1 or not title2:
        return False
    norm1 = normalize_title(title1)
    norm2 = normalize_title(title2)
    if not norm1 or not norm2:
        return False
    # 完全相同
    if norm1 == norm2:
        return True
    # 相似度比较
    return SequenceMatcher(None, norm1, norm2).ratio() >= threshold


def is_valid_url(url: str) -> bool:
    """检查URL格式是否有效"""
    if not url:
        return False
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def check_url_accessible(url: str, timeout: int = 10) -> bool:
    """检查URL是否可访问（HEAD请求）"""
    if not is_valid_url(url):
        return False
    try:
        import requests
        resp = requests.head(url, timeout=timeout, allow_redirects=True,
                             headers={'User-Agent': 'Mozilla/5.0'})
        return resp.status_code < 400
    except Exception:
        return False


def find_similar_in_db(conn: sqlite3.Connection, title: str, source_url: str = '',
                       threshold: float = 0.85) -> bool:
    """检查数据库中是否存在相似信号（基于标题相似度和URL去重）"""
    cursor = conn.cursor()

    # 1. 精确URL去重
    if source_url:
        cursor.execute('SELECT id FROM signals WHERE source_url = ?', (source_url,))
        if cursor.fetchone():
            return True

    # 2. 标题相似度去重（仅对最近1000条比较，避免性能问题）
    cursor.execute('SELECT title FROM signals ORDER BY collected_at DESC LIMIT 1000')
    for row in cursor.fetchall():
        if is_similar_title(title, row[0], threshold):
            return True

    return False


def save_signal_safe(conn: sqlite3.Connection, brand_name: str, industry: str,
                     signal_type: str, title: str, summary: str, source_url: str,
                     source_name: str, **kwargs) -> bool:
    """安全保存信号 - 包含完整去重逻辑

    去重策略：
    1. MD5(url+title) 精确去重
    2. source_url 精确去重
    3. 标题相似度去重（阈值0.85）

    返回 True 表示新插入，False 表示已存在（跳过）
    """
    cursor = conn.cursor()
    signal_id = generate_id(source_url, title)

    # 第一层：ID精确去重
    cursor.execute('SELECT id FROM signals WHERE id = ?', (signal_id,))
    if cursor.fetchone():
        return False

    # 第二层：URL精确去重
    if source_url:
        cursor.execute('SELECT id FROM signals WHERE source_url = ?', (source_url,))
        if cursor.fetchone():
            return False

    # 第三层：标题相似度去重
    cursor.execute('SELECT title FROM signals ORDER BY collected_at DESC LIMIT 500')
    for row in cursor.fetchall():
        if is_similar_title(title, row[0], threshold=0.85):
            return False

    # 构建字段
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    published_at = kwargs.get('published_at') or now

    # 判断是否有扩展字段
    has_social_fields = any(k in kwargs for k in ['likes', 'reposts', 'comments', 'author', 'author_followers'])

    if has_social_fields:
        cursor.execute('''
            INSERT INTO signals (id, brand_name, industry, signal_type, title, summary,
                source_url, source_name, published_at, collected_at,
                likes, reposts, comments, author, author_followers)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            signal_id, brand_name, industry, signal_type, title, summary[:500],
            source_url, source_name, published_at, now,
            kwargs.get('likes', 0), kwargs.get('reposts', 0),
            kwargs.get('comments', 0), kwargs.get('author', ''),
            kwargs.get('author_followers', 0)
        ))
    else:
        cursor.execute('''
            INSERT INTO signals (id, brand_name, industry, signal_type, title, summary,
                source_url, source_name, published_at, collected_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            signal_id, brand_name, industry, signal_type, title, summary[:500],
            source_url, source_name, published_at, now
        ))

    return True
