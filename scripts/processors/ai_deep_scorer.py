#!/usr/bin/env python3
"""AI 深度打分器 - 使用 DeepSeek 语义分析评估品牌投放可能性"""

import sqlite3
import os
import json
import re
import requests

DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'ooh_signal.db')

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

def get_api_key():
    """获取 DeepSeek API Key"""
    key = os.environ.get('DEEPSEEK_API_KEY')
    if not key:
        raise ValueError("请设置 DEEPSEEK_API_KEY 环境变量")
    return key

def analyze_signal(title, summary, brand_name, industry):
    """使用 DeepSeek 分析信号的投放可能性"""
    api_key = get_api_key()

    prompt = f"""你是一个户外广告行业专家。请分析以下商业新闻，评估该品牌在近期进行户外广告投放的可能性。

品牌：{brand_name}
行业：{industry}
标题：{title}
摘要：{summary[:300]}

评估维度：
1. 品牌代言人官宣 → 需大规模曝光配合，投放可能性极高（85-100分）
2. 品牌扩张信号（新店、新市场、出海）→ 投放可能性高（75-95分）
3. 融资/上市信号 → 营销预算增加，投放可能性高（70-90分）
4. 产品发布/品牌升级 → 需要广告曝光，投放可能性中高（60-80分）
5. 展会/活动信号 → 需要品牌曝光，投放可能性中高（60-80分）
6. 竞品投放动态 → 可能跟进，投放可能性中（50-70分）
7. 行业整体趋势 → 参考价值（30-50分）

请以 JSON 格式返回：
{{
  "score": 0-100的整数,
  "reason": "50字以内的推荐理由",
  "signal_strength": "strong/medium/weak",
  "recommended_channels": ["户外广告渠道建议，如：商圈大屏、地铁、公交站、电梯"]
}}

只返回 JSON，不要其他内容。"""

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
                    {"role": "system", "content": "你是一个户外广告行业数据分析专家，只返回JSON格式的评估结果。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2,
                "max_tokens": 300
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

def deep_score_signals():
    """对所有信号进行深度打分"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 获取需要深度打分的信号（优先处理代言人、活动、融资等高价值信号）
    cursor.execute("""
        SELECT * FROM signals
        WHERE brand_name != '待识别'
        AND (
            reason LIKE '%行业动态%'
            OR reason LIKE '%待分析%'
            OR reason = ''
            OR title LIKE '%代言%'
            OR title LIKE '%官宣%'
            OR title LIKE '%合作%'
            OR title LIKE '%联动%'
            OR title LIKE '%联名%'
            OR title LIKE '%活动%'
            OR title LIKE '%快闪%'
            OR title LIKE '%路演%'
            OR title LIKE '%融资%'
            OR title LIKE '%IPO%'
            OR title LIKE '%展会%'
            OR title LIKE '%峰会%'
            OR title LIKE '%发布会%'
        )
        ORDER BY
            CASE
                WHEN title LIKE '%代言%' OR title LIKE '%官宣%' THEN 0
                WHEN title LIKE '%合作%' OR title LIKE '%联动%' OR title LIKE '%联名%' THEN 1
                WHEN title LIKE '%活动%' OR title LIKE '%快闪%' OR title LIKE '%路演%' THEN 2
                WHEN title LIKE '%融资%' OR title LIKE '%IPO%' THEN 3
                WHEN title LIKE '%展会%' OR title LIKE '%峰会%' OR title LIKE '%发布会%' THEN 4
                ELSE 5
            END,
            collected_at DESC
        LIMIT 25
    """)
    signals = cursor.fetchall()

    print(f"Deep scoring {len(signals)} signals...")

    scored_count = 0
    for signal in signals:
        signal_dict = dict(signal)
        print(f"  Analyzing: {signal_dict['brand_name']} - {signal_dict['title'][:30]}...")

        result = analyze_signal(
            signal_dict['title'],
            signal_dict['summary'],
            signal_dict['brand_name'],
            signal_dict.get('industry', '')
        )

        if not result:
            print(f"    Skipped (analysis failed)")
            continue

        score = result.get('score', signal_dict['score'])
        reason = result.get('reason', signal_dict['reason'])

        # 更新信号
        cursor.execute('''
            UPDATE signals SET score = ?, reason = ? WHERE id = ?
        ''', (score, reason, signal_dict['id']))

        scored_count += 1
        print(f"    Score: {score}, Reason: {reason[:30]}...")

    conn.commit()
    conn.close()
    print(f"\nDeep scored {scored_count} signals")

if __name__ == '__main__':
    deep_score_signals()
