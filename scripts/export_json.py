#!/usr/bin/env python3
"""导出数据库为 JSON 文件，供 Vercel 部署使用"""

import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'ooh_signal.db')
EXPORT_DIR = os.path.join(os.path.dirname(__file__), '..', 'public', 'data')

def export_data():
    os.makedirs(EXPORT_DIR, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 导出信号
    cursor.execute('SELECT * FROM signals ORDER BY score DESC, collected_at DESC')
    signals = [dict(row) for row in cursor.fetchall()]

    # 转换字段名为 camelCase
    def snake_to_camel(s):
        parts = s.split('_')
        return parts[0] + ''.join(p.capitalize() for p in parts[1:])

    signals_camel = []
    for s in signals:
        signals_camel.append({snake_to_camel(k): v for k, v in s.items()})

    with open(os.path.join(EXPORT_DIR, 'signals.json'), 'w', encoding='utf-8') as f:
        json.dump(signals_camel, f, ensure_ascii=False, indent=2)

    # 导出品牌
    cursor.execute('SELECT * FROM brands ORDER BY latest_score DESC')
    brands = [dict(row) for row in cursor.fetchall()]

    brands_camel = []
    for b in brands:
        brands_camel.append({snake_to_camel(k): v for k, v in b.items()})

    with open(os.path.join(EXPORT_DIR, 'brands.json'), 'w', encoding='utf-8') as f:
        json.dump(brands_camel, f, ensure_ascii=False, indent=2)

    # 导出评分历史
    cursor.execute('SELECT * FROM score_history ORDER BY brand_name, recorded_at')
    history = [dict(row) for row in cursor.fetchall()]
    history_camel = [{snake_to_camel(k): v for k, v in h.items()} for h in history]

    with open(os.path.join(EXPORT_DIR, 'score_history.json'), 'w', encoding='utf-8') as f:
        json.dump(history_camel, f, ensure_ascii=False, indent=2)

    conn.close()

    print(f"Exported {len(signals)} signals to {EXPORT_DIR}/signals.json")
    print(f"Exported {len(brands)} brands to {EXPORT_DIR}/brands.json")
    print(f"Exported {len(history)} score history records to {EXPORT_DIR}/score_history.json")

if __name__ == '__main__':
    export_data()
