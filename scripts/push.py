#!/usr/bin/env python3
"""统一推送入口 - 支持企业微信、Server酱、飞书"""

import sqlite3
import os
import json
import requests
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'ooh_signal.db')

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
        LIMIT 30
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
    score = signal['score']
    score_emoji = '🔴' if score >= 80 else '🟡' if score >= 60 else '⚪'

    return {
        'brand': signal['brand_name'],
        'type': type_label,
        'score': score,
        'score_emoji': score_emoji,
        'title': signal['title'][:40] + ('...' if len(signal['title']) > 40 else ''),
        'reason': signal['reason'][:25] + ('...' if len(signal.get('reason', '')) > 25 else ''),
        'url': signal['source_url']
    }

# ============ 企业微信推送 ============

def push_to_wechat_work():
    """推送到企业微信群"""
    webhook = os.environ.get('WECHAT_WEBHOOK')
    if not webhook:
        print("WECHAT_WEBHOOK not set, skipping")
        return False

    signals = get_high_score_signals()
    if not signals:
        print("No high-score signals to push")
        return True

    now = datetime.now().strftime('%Y-%m-%d %H:%M')

    # 构建 Markdown 消息
    content = f"## 🎯 OOH Signal 每日推送\n"
    content += f"📊 {now} | 共{len(signals)}条高分信号\n\n"

    for i, signal in enumerate(signals, 1):
        s = format_signal_text(signal)
        content += f"**{i}. {s['brand']}** {s['type']} {s['score_emoji']}{s['score']}分\n"
        content += f"> {s['title']}\n"
        content += f"> 💡{s['reason']}\n"
        content += f"> [查看原文]({s['url']})\n\n"

    content += "---\n*OOH Signal 户外广告投放信号情报*"

    message = {
        "msgtype": "markdown",
        "markdown": {"content": content}
    }

    try:
        response = requests.post(webhook, json=message, timeout=10)
        result = response.json()
        if result.get('errcode') == 0:
            print(f"✅ 企业微信推送成功: {len(signals)}条信号")
            return True
        else:
            print(f"❌ 企业微信推送失败: {result}")
            return False
    except Exception as e:
        print(f"❌ 企业微信推送错误: {e}")
        return False

# ============ Server酱推送 ============

def push_to_serverchan():
    """推送到Server酱（个人微信）"""
    send_key = os.environ.get('SERVERCHAN_SENDKEY')
    if not send_key:
        print("SERVERCHAN_SENDKEY not set, skipping")
        return False

    signals = get_high_score_signals()
    if not signals:
        print("No high-score signals to push")
        return True

    now = datetime.now().strftime('%Y-%m-%d %H:%M')

    # 构建消息内容
    title = f"OOH Signal: {len(signals)}条高分信号"

    content = f"## 🎯 OOH Signal 每日推送\n\n"
    content += f"📊 **{now}** | 共{len(signals)}条高分信号\n\n"

    for i, signal in enumerate(signals, 1):
        s = format_signal_text(signal)
        content += f"### {i}. {s['brand']} {s['type']} {s['score_emoji']}{s['score']}分\n"
        content += f"{s['title']}\n\n"
        content += f"💡{s['reason']}\n\n"
        content += f"🔗 [查看原文]({s['url']})\n\n"
        content += "---\n\n"

    content += "*OOH Signal 户外广告投放信号情报*"

    url = f"https://sctapi.ftqq.com/{send_key}.send"
    data = {
        "title": title,
        "desp": content,
        "channel": "9",  # 微信服务号
    }

    try:
        response = requests.post(url, data=data, timeout=10)
        result = response.json()
        if result.get('code') == 0:
            try:
                print(f"✅ Server酱推送成功: {len(signals)}条信号")
            except UnicodeEncodeError:
                print(f"Server酱推送成功: {len(signals)}条信号")
            return True
        else:
            try:
                print(f"❌ Server酱推送失败: {result}")
            except UnicodeEncodeError:
                print(f"Server酱推送失败: {result}")
            return False
    except Exception as e:
        try:
            print(f"❌ Server酱推送错误: {e}")
        except UnicodeEncodeError:
            print(f"Server酱推送错误: {e}")
        return False

# ============ PushPlus推送 ============

def push_to_pushplus():
    """推送到PushPlus（个人微信）"""
    token = os.environ.get('PUSHPLUS_TOKEN')
    if not token:
        print("PUSHPLUS_TOKEN not set, skipping")
        return False

    signals = get_high_score_signals()
    if not signals:
        print("No high-score signals to push")
        return True

    now = datetime.now().strftime('%Y-%m-%d %H:%M')

    # 构建 HTML 消息
    content = f"<h2>🎯 OOH Signal 每日推送</h2>"
    content += f"<p>📊 {now} | 共{len(signals)}条高分信号</p><hr>"

    for i, signal in enumerate(signals, 1):
        s = format_signal_text(signal)
        content += f"<h3>{i}. {s['brand']} {s['type']} {s['score_emoji']}{s['score']}分</h3>"
        content += f"<p>{s['title']}</p>"
        content += f"<p>💡{s['reason']}</p>"
        content += f"<p><a href='{s['url']}'>查看原文</a></p><hr>"

    content += "<p><em>OOH Signal 户外广告投放信号情报</em></p>"

    url = "http://www.pushplus.plus/send"
    data = {
        "token": token,
        "title": f"OOH Signal: {len(signals)}条高分信号",
        "content": content,
        "template": "html",
    }

    try:
        response = requests.post(url, json=data, timeout=10)
        result = response.json()
        if result.get('code') == 200:
            print(f"✅ PushPlus推送成功: {len(signals)}条信号")
            return True
        else:
            print(f"❌ PushPlus推送失败: {result}")
            return False
    except Exception as e:
        print(f"❌ PushPlus推送错误: {e}")
        return False

# ============ 主入口 ============

def main():
    print("=" * 50)
    print("OOH Signal - 消息推送")
    print("=" * 50)

    results = []

    print("\n[1/3] 企业微信推送...")
    results.append(push_to_wechat_work())

    print("\n[2/3] Server酱推送...")
    results.append(push_to_serverchan())

    print("\n[3/3] PushPlus推送...")
    results.append(push_to_pushplus())

    success_count = sum(1 for r in results if r)
    print(f"\n推送完成: {success_count}/3 个渠道成功")

if __name__ == '__main__':
    main()
