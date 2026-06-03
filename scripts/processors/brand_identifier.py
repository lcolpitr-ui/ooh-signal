#!/usr/bin/env python3
"""品牌识别器 - 使用 DeepSeek API 从信号中提取品牌信息"""

import sqlite3
import os
import json
import re
import requests

DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'ooh_signal.db')

# DeepSeek API
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

# 行业列表
INDUSTRIES = [
    '快消', '汽车', '3C', '美妆', '金融', '地产', '教育', '医疗',
    '餐饮', '零售', '互联网', '游戏', '服装', '家电', '酒水',
    '运动', '母婴', '宠物', '旅游', '航空'
]

def get_api_key():
    """获取 DeepSeek API Key"""
    key = os.environ.get('DEEPSEEK_API_KEY')
    if not key:
        raise ValueError("请设置 DEEPSEEK_API_KEY 环境变量")
    return key

def extract_brand_info(title, summary):
    """使用 DeepSeek 提取品牌信息"""
    api_key = get_api_key()

    prompt = f"""分析以下商业新闻，提取品牌信息。

标题：{title}
摘要：{summary}

请以 JSON 格式返回：
{{
  "brand_name": "品牌名称（中文或英文，取最常用的）",
  "industry": "行业分类（从以下选择：{', '.join(INDUSTRIES)}）",
  "scale": "品牌规模（large/medium/small，根据知名度判断）",
  "is_listed": true/false（是否为上市公司）
}}

只返回 JSON，不要其他内容。如果无法识别品牌，brand_name 设为 null。"""

    try:
        response = requests.post(
            DEEPSEEK_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": "你是一个品牌信息提取助手，只返回JSON格式的数据。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 200
            },
            timeout=30
        )

        if response.status_code != 200:
            print(f"  API error: {response.status_code}")
            return None

        result = response.json()
        text = result['choices'][0]['message']['content']

        # 提取 JSON
        json_match = re.search(r'\{[^}]+\}', text)
        if json_match:
            return json.loads(json_match.group())
        return None

    except Exception as e:
        print(f"  LLM error: {e}")
        return None

def identify_brands():
    """识别所有待识别的品牌"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 获取待识别的信号
    cursor.execute("SELECT * FROM signals WHERE brand_name = '待识别'")
    signals = cursor.fetchall()

    print(f"Identifying brands for {len(signals)} signals...")

    identified_count = 0
    for signal in signals:
        signal_dict = dict(signal)
        try:
            print(f"  Processing: {signal_dict['title'][:30]}...")
        except UnicodeEncodeError:
            print(f"  Processing signal {signal_dict['id'][:8]}...")

        info = extract_brand_info(signal_dict['title'], signal_dict['summary'])
        if not info or not info.get('brand_name'):
            print(f"    Skipped (no brand found)")
            continue

        brand_name = info['brand_name']
        industry = info.get('industry', '')
        scale = info.get('scale', 'small')
        is_listed = 1 if info.get('is_listed', False) else 0

        # 更新信号
        cursor.execute('''
            UPDATE signals SET brand_name = ?, industry = ? WHERE id = ?
        ''', (brand_name, industry, signal_dict['id']))

        # 更新或插入品牌
        cursor.execute('''
            INSERT INTO brands (id, name, industry, scale, is_listed, signal_count, latest_score)
            VALUES (?, ?, ?, ?, ?, 1, ?)
            ON CONFLICT(name) DO UPDATE SET
                signal_count = signal_count + 1,
                latest_score = MAX(latest_score, excluded.latest_score)
        ''', (brand_name.lower().replace(' ', '-'), brand_name, industry, scale, is_listed, signal_dict['score']))

        # 记录评分历史
        cursor.execute('''
            INSERT INTO score_history (brand_name, score, signal_count, recorded_at)
            VALUES (?, ?, 1, datetime('now'))
        ''', (brand_name, signal_dict['score']))

        identified_count += 1
        try:
            print(f"    Identified: {brand_name} ({industry})")
        except UnicodeEncodeError:
            print(f"    Identified brand successfully")

    conn.commit()
    conn.close()
    print(f"\nIdentified {identified_count} brands")

if __name__ == '__main__':
    identify_brands()
