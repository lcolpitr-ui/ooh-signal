#!/usr/bin/env python3
"""飞书推送 - 每日高分信号自动推送到飞书群"""

import sqlite3
import os
import json
import requests
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'ooh_signal.db')

def get_feishu_webhook():
    """获取飞书 webhook URL"""
    webhook = os.environ.get('FEISHU_WEBHOOK')
    if not webhook:
        raise ValueError("请设置 FEISHU_WEBHOOK 环境变量")
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
        LIMIT 20
    ''', (since, min_score))

    signals = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return signals

def format_signal_card(signal):
    """格式化信号为飞书卡片元素"""
    signal_type_labels = {
        'expansion': '📈 扩张',
        'funding': '💰 融资',
        'product': '🆕 产品',
        'competitor': '⚔️ 竞品',
        'policy': '📜 政策',
        'industry': '🏢 行业',
    }

    type_label = signal_type_labels.get(signal['signal_type'], '📋 其他')
    score_emoji = '🔴' if signal['score'] >= 80 else '🟡' if signal['score'] >= 60 else '⚪'

    return {
        "tag": "div",
        "text": {
            "tag": "lark_md",
            "content": f"**{signal['brand_name']}** {type_label} {score_emoji} {signal['score']}分\n"
                       f"{signal['title'][:50]}{'...' if len(signal['title']) > 50 else ''}\n"
                       f"💡 {signal['reason'][:30]}{'...' if len(signal.get('reason', '')) > 30 else ''}"
        },
        "extra": {
            "tag": "button",
            "text": {
                "tag": "plain_text",
                "content": "查看原文"
            },
            "type": "primary",
            "url": signal['source_url']
        }
    }

def build_feishu_message(signals):
    """构建飞书消息"""
    if not signals:
        return None

    now = datetime.now().strftime('%Y年%m月%d日 %H:%M')

    elements = [
        {
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"📊 **过去24小时高分信号** | {now}\n"
                           f"共 {len(signals)} 条信号，评分 ≥ 60"
            }
        },
        {"tag": "hr"}
    ]

    # 添加信号卡片
    for signal in signals[:10]:  # 最多显示10条
        elements.append(format_signal_card(signal))
        elements.append({"tag": "hr"})

    # 添加底部
    elements.append({
        "tag": "note",
        "elements": [
            {
                "tag": "plain_text",
                "content": "OOH Signal - 户外广告投放信号情报系统"
            }
        ]
    })

    return {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": "🎯 OOH Signal 每日信号推送"
                },
                "template": "blue"
            },
            "elements": elements
        }
    }

def push_to_feishu():
    """推送到飞书"""
    webhook = get_feishu_webhook()
    signals = get_high_score_signals()

    if not signals:
        print("No high-score signals to push")
        return

    message = build_feishu_message(signals)
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
            if result.get('code') == 0:
                print(f"Successfully pushed {len(signals)} signals to Feishu")
            else:
                print(f"Feishu API error: {result}")
        else:
            print(f"HTTP error: {response.status_code}")
    except Exception as e:
        print(f"Push error: {e}")

if __name__ == '__main__':
    push_to_feishu()
