#!/usr/bin/env python3
"""每日日报生成器"""

import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'ooh_signal.db')

def generate_daily_report():
    """生成每日日报"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 获取过去 24 小时的高分信号
    yesterday = (datetime.now() - timedelta(days=1)).isoformat()
    cursor.execute('''
        SELECT * FROM signals
        WHERE collected_at >= ? AND score >= 60
        ORDER BY score DESC
        LIMIT 50
    ''', (yesterday,))
    signals = cursor.fetchall()

    if not signals:
        print("No high-score signals in the past 24 hours")
        return

    # 生成日报内容
    report_date = datetime.now().strftime('%Y年%m月%d日')
    report = f"# OOH Signal 每日日报 - {report_date}\n\n"
    report += f"过去 24 小时共有 **{len(signals)}** 条高分信号：\n\n"

    # 按信号类型分组
    type_groups = {}
    for signal in signals:
        signal_type = signal['signal_type']
        if signal_type not in type_groups:
            type_groups[signal_type] = []
        type_groups[signal_type].append(signal)

    type_labels = {
        'funding': '💰 融资信号',
        'expansion': '📈 扩张信号',
        'product': '🆕 产品信号',
        'competitor': '⚔️ 竞品信号',
        'policy': '📜 政策信号',
        'industry': '🏢 行业动态',
    }

    for signal_type, items in type_groups.items():
        report += f"## {type_labels.get(signal_type, signal_type)}\n\n"
        for signal in items:
            report += f"### {signal['brand_name']} (评分: {signal['score']})\n"
            report += f"**{signal['title']}**\n\n"
            report += f"{signal['summary'][:200]}...\n\n"
            report += f"💡 {signal['reason']}\n\n"
            report += f"📎 [查看原文]({signal['source_url']})\n\n---\n\n"

    # 保存日报
    daily_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'daily')
    os.makedirs(daily_dir, exist_ok=True)

    report_file = os.path.join(daily_dir, f"{datetime.now().strftime('%Y-%m-%d')}.md")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"Daily report generated: {report_file}")
    print(f"Total signals: {len(signals)}")

if __name__ == '__main__':
    generate_daily_report()
