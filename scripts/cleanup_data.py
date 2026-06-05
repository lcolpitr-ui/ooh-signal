#!/usr/bin/env python3
"""数据清理脚本 - 删除超过30天的信号"""

import sqlite3
import os
from datetime import datetime, timezone, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'ooh_signal.db')

def cleanup_old_signals():
    """删除超过30天的信号"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 统计清理前的数据
    cursor.execute("SELECT COUNT(*) FROM signals")
    total_before = cursor.fetchone()[0]

    # 计算30天前的时间（UTC）
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    cutoff_date = thirty_days_ago.isoformat()
    print(f"清理 {cutoff_date} 之前的信号...")

    # 删除超过30天的信号
    cursor.execute("""
        DELETE FROM signals
        WHERE collected_at < ? AND collected_at != ''
    """, (cutoff_date,))
    deleted_count = cursor.rowcount

    # 清理孤立的品牌（没有关联信号的品牌）
    cursor.execute("""
        DELETE FROM brands
        WHERE name != '待识别'
        AND name NOT IN (
            SELECT DISTINCT brand_name FROM signals
            WHERE brand_name != '待识别'
        )
    """)
    deleted_brands = cursor.rowcount

    # 清理旧的评分历史（保留最近30天）
    cursor.execute("""
        DELETE FROM score_history
        WHERE recorded_at < ?
    """, (cutoff_date,))
    deleted_history = cursor.rowcount

    conn.commit()

    # 统计清理后的数据
    cursor.execute("SELECT COUNT(*) FROM signals")
    total_after = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM brands")
    brands_after = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM score_history")
    history_after = cursor.fetchone()[0]

    conn.close()

    print(f"\n清理完成:")
    print(f"  信号: {total_before} → {total_after} (删除 {deleted_count})")
    print(f"  品牌: {brands_after} (删除 {deleted_brands} 孤立品牌)")
    print(f"  评分历史: {history_after} (删除 {deleted_history} 条旧记录)")

    return deleted_count

if __name__ == '__main__':
    cleanup_old_signals()
