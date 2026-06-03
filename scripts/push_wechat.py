#!/usr/bin/env python3
"""企业微信推送 - 每日高分信号自动推送到企业微信群"""

import sqlite3
import os
import json
import requests
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'ooh_signal.db')

def get_wechat_webhook():
    """获取企业微信 webhook URL"""
    webhook = os.environ.get('WECHAT_WEBHOOK')
    if not webhook:
        raise ValueError("请设置 WECHAT_WEBHOOK 环境变量")
    return webhook

def get_high_score_signals(hours=24, min_score=60):
    """获取过去N小时的高分信号"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    since = (datetime.now() - timedelta(hours=hours)).isoformat()
    cursor.execute('''
        SELECT * FROM signals
        WHERE collected_at >= ? AND score >= ? AND brand_name != '待识别'
        ORDER BY score DESC
        LIMIT 10
    ''', (since, min_score))

    signals = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return signals

def format_signal_text(signal):
    """格式化信号为文本"""
    signal_type_labels = {
        'expansion': '📈扩张',
        'funding': '💰融资',
        'product': '🆕产品',
        'competitor': '⚔️竞品',
        'policy': '📜政策',
        'industry': '🏢行业',
    }

    type_label = signal_type_labels.get(signal['signal_type'], '📋其他')
    score_emoji = '🔴' if signal['score'] >= 80 else '🟡' if signal['score'] >= 60 else '⚪'

    return f"**{signal['brand_name']}** {type_label} {score_emoji}{signal['score']}分\n" \
           f">{signal['title'][:40]}{'...' if len(signal['title']) > 40 else ''}\n" \
           f">💡{signal['reason'][:25]}{'...' if len(signal.get('reason', '')) > 25 else ''}\n" \
           f">[查看原文]({signal['source_url']})"

def build_wechat_message(signals):
    """构建企业微信消息"""
    if not signals:
        return None

    now = datetime.now().strftime('%Y年%m月%d日 %H:%M')

    content = f"## 🎯 OOH Signal 每日信号推送\n"
    content += f"📊 **过去24小时高分信号** | {now}\n"
    content += f"共 {len(signals)} 条信号，评分 ≥ 60\n\n"

    for i, signal in enumerate(signals, 1):
        content += f"### {i}. {format_signal_text(signal)}\n\n"

    content += "---\n*OOH Signal - 户外广告投放信号情报系统*"

    return {
        "msgtype": "markdown",
        "markdown": {
            "content": content
        }
    }

def push_to_wechat():
    """推送到企业微信"""
    webhook = get_wechat_webhook()
    signals = get_high_score_signals()

    if not signals:
        print("No high-score signals to push")
        return

    message = build_wechat_message(signals)
    if not message:
        print("Failed to build message")
        return

    try:
        response = requests.post(
            webhook,
            json=message,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            if result.get('errcode') == 0:
                print(f"Successfully pushed {len(signals)} signals to WeChat")
            else:
                print(f"WeChat API error: {result}")
        else:
            print(f"HTTP error: {response.status_code}")
    except Exception as e:
        print(f"Push error: {e}")

if __name__ == '__main__':
    push_to_wechat()
