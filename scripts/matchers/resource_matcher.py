#!/usr/bin/env python3
"""资源匹配器 - 将品牌信号与广告媒体资源进行智能匹配"""

import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'ooh_signal.db')
RESOURCES_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'resources.json')
MATCHES_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'public', 'data', 'matches.json')

# 行业→媒体 匹配规则
INDUSTRY_MEDIA_MAP = {
    '快消': ['商圈大屏', '便利店', '超市', '社区媒体'],
    '食品': ['商圈大屏', '便利店', '超市', '社区媒体'],
    '汽车': ['高速大屏', '商圈', '机场', '高铁站'],
    '3C': ['电脑城', '数码广场', '写字楼', '商圈'],
    '数码': ['电脑城', '数码广场', '写字楼', '商圈'],
    '美妆': ['商圈', '购物中心', '地铁', '电梯'],
    '服装': ['商圈', '购物中心', '步行街', '地铁'],
    '金融': ['写字楼', '银行', '机场', '高铁站'],
    '餐饮': ['商圈', '社区', '地铁', '步行街'],
    '教育': ['学校周边', '社区', '写字楼', '地铁'],
    '医疗': ['医院周边', '社区', '药店', '地铁'],
    '地产': ['高速大屏', '商圈', '社区', '写字楼'],
    '运动': ['商圈', '体育馆', '学校周边', '地铁'],
    '酒水': ['商圈', '餐饮', '酒吧', 'KTV'],
    '互联网': ['写字楼', '商圈', '地铁', '公交站'],
}

# 预算档次匹配规则
BUDGET_TIERS = {
    'high': {'score_range': (90, 100), 'media_types': ['核心商圈大屏', '机场', '高铁站']},
    'medium_high': {'score_range': (80, 89), 'media_types': ['商圈大屏', '地铁', '公交站']},
    'medium': {'score_range': (70, 79), 'media_types': ['社区媒体', '电梯', '便利店']},
    'low': {'score_range': (60, 69), 'media_types': ['线上广告', '社交媒体']},
}

def load_resources():
    """加载资源库"""
    if not os.path.exists(RESOURCES_PATH):
        return []
    with open(RESOURCES_PATH, 'r', encoding='utf-8') as f:
        return json.load(f).get('resources', [])

def load_signals(min_score=70):
    """加载高分信号"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM signals
        WHERE score >= ? AND brand_name != '待识别'
        ORDER BY score DESC
        LIMIT 50
    ''', (min_score,))

    signals = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return signals

def get_industry(signal):
    """获取信号所属行业"""
    return signal.get('industry', '互联网')

def get_budget_tier(score):
    """根据评分获取预算档次"""
    for tier, config in BUDGET_TIERS.items():
        if config['score_range'][0] <= score <= config['score_range'][1]:
            return tier
    return 'low'

def calculate_match_score(signal, resource):
    """计算匹配分数"""
    score = 0
    reasons = []

    # 行业匹配
    signal_industry = get_industry(signal)
    resource_industries = resource.get('industries', [])
    if signal_industry in resource_industries:
        score += 40
        reasons.append('行业匹配')

    # 媒体类型匹配
    signal_industry_key = signal_industry.rstrip('业')
    recommended_media = INDUSTRY_MEDIA_MAP.get(signal_industry_key, [])
    resource_type = resource.get('type', '')
    if any(media in resource_type for media in recommended_media):
        score += 30
        reasons.append('媒体类型匹配')

    # 预算匹配
    budget_tier = get_budget_tier(signal.get('score', 0))
    resource_price = resource.get('price_range', 'medium')
    if budget_tier.startswith(resource_price) or resource_price.startswith(budget_tier):
        score += 20
        reasons.append('预算匹配')

    # 受众匹配
    signal_title = signal.get('title', '')
    resource_audience = resource.get('audience', [])
    if any(audience in signal_title for audience in resource_audience):
        score += 10
        reasons.append('受众匹配')

    return score, reasons

def generate_match_reason(signal, resource, reasons):
    """生成匹配理由"""
    brand = signal.get('brand_name', '')
    title = signal.get('title', '')[:30]
    resource_name = resource.get('name', '')
    resource_type = resource.get('type', '')

    reason_parts = []
    if '行业匹配' in reasons:
        reason_parts.append(f"{brand}所在行业与{resource_type}受众契合")
    if '媒体类型匹配' in reasons:
        reason_parts.append(f"{resource_type}适合品牌曝光")
    if '预算匹配' in reasons:
        reason_parts.append("预算范围匹配")
    if '受众匹配' in reasons:
        reason_parts.append("目标受众重叠")

    return '；'.join(reason_parts) if reason_parts else f"推荐{resource_name}进行品牌曝光"

def match_signals_to_resources(signals, resources, min_match_score=50):
    """匹配信号与资源"""
    matches = []

    for signal in signals:
        for resource in resources:
            score, reasons = calculate_match_score(signal, resource)
            if score >= min_match_score:
                match = {
                    'signal_id': signal.get('id', ''),
                    'signal_title': signal.get('title', '')[:50],
                    'brand_name': signal.get('brand_name', ''),
                    'signal_score': signal.get('score', 0),
                    'resource_id': resource.get('id', ''),
                    'resource_name': resource.get('name', ''),
                    'resource_type': resource.get('type', ''),
                    'resource_location': resource.get('location', ''),
                    'match_score': score,
                    'reasons': reasons,
                    'reason_text': generate_match_reason(signal, resource, reasons),
                    'recommended_budget': resource.get('price_range', ''),
                    'daily_traffic': resource.get('daily_traffic', 0),
                }
                matches.append(match)

    # 按匹配分数排序
    matches.sort(key=lambda x: x['match_score'], reverse=True)
    return matches

def save_matches(matches):
    """保存匹配结果"""
    os.makedirs(os.path.dirname(MATCHES_PATH), exist_ok=True)
    with open(MATCHES_PATH, 'w', encoding='utf-8') as f:
        json.dump({
            'generated_at': datetime.now().isoformat(),
            'total_matches': len(matches),
            'matches': matches
        }, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(matches)} matches to {MATCHES_PATH}")

def run_matching():
    """运行匹配流程"""
    print("=" * 50)
    print("OOH Resource Matcher - 资源匹配")
    print("=" * 50)

    print("\n[1/3] Loading resources...")
    resources = load_resources()
    print(f"  Loaded {len(resources)} resources")

    print("\n[2/3] Loading signals...")
    signals = load_signals(min_score=70)
    print(f"  Loaded {len(signals)} signals")

    print("\n[3/3] Matching signals to resources...")
    matches = match_signals_to_resources(signals, resources)
    print(f"  Found {len(matches)} matches")

    save_matches(matches)
    print("\nMatching complete!")

if __name__ == '__main__':
    run_matching()
