#!/usr/bin/env python3
"""数据清理脚本 - 去重 + 老旧数据清理 + 链接检查

功能：
1. 清理重复信号（基于标题相似度）
2. 删除超过30天的信号
3. 检查链接有效性（可选）
4. 导出清理后的数据

用法：
  python scripts/cleanup_data.py              # 去重 + 清理旧数据
  python scripts/cleanup_data.py --check-links # 去重 + 链接检查
  python scripts/cleanup_data.py --no-export   # 不导出JSON
"""

import sqlite3
import os
import sys
import argparse
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'collectors'))
from signal_utils import is_similar_title, check_url_accessible

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'ooh_signal.db')


def cleanup_duplicates(conn: sqlite3.Connection) -> int:
    """清理重复信号（基于标题相似度），返回删除的数量"""
    cursor = conn.cursor()

    # 获取所有信号，按收集时间降序（保留最新的）
    cursor.execute('SELECT id, title, source_url FROM signals ORDER BY collected_at DESC')
    all_signals = cursor.fetchall()

    seen_titles = []  # (id, title) 列表
    ids_to_delete = []

    for signal_id, title, source_url in all_signals:
        is_dup = False

        # 检查是否与已保留的信号相似
        for seen_id, seen_title in seen_titles:
            if is_similar_title(title, seen_title, threshold=0.85):
                is_dup = True
                ids_to_delete.append(signal_id)
                break

        if not is_dup:
            seen_titles.append((signal_id, title))

    # 删除重复信号
    if ids_to_delete:
        placeholders = ','.join(['?'] * len(ids_to_delete))
        cursor.execute(f'DELETE FROM signals WHERE id IN ({placeholders})', ids_to_delete)
        conn.commit()
        print(f"  删除了 {len(ids_to_delete)} 条重复信号")

    return len(ids_to_delete)


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


def check_invalid_links(conn: sqlite3.Connection, sample_size: int = 50) -> int:
    """检查并报告无效链接"""
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, title, source_url FROM signals
        WHERE source_url IS NOT NULL AND source_url != ''
        ORDER BY RANDOM() LIMIT ?
    ''', (sample_size,))

    signals = cursor.fetchall()
    invalid_count = 0

    print(f"  检查 {len(signals)} 条链接...")

    for i, (signal_id, title, url) in enumerate(signals):
        if not check_url_accessible(url, timeout=8):
            invalid_count += 1
            print(f"    [{i+1}/{len(signals)}] ❌ {title[:40]} | {url[:50]}")
        else:
            print(f"    [{i+1}/{len(signals)}] ✅ {url[:60]}")

    return invalid_count


def export_data():
    """导出数据到JSON"""
    export_script = os.path.join(os.path.dirname(__file__), 'export_json.py')
    os.system(f'python "{export_script}"')


def main():
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description='数据清理工具')
    parser.add_argument('--check-links', action='store_true', help='检查链接有效性')
    parser.add_argument('--link-sample', type=int, default=50, help='链接检查样本数量')
    parser.add_argument('--no-export', action='store_true', help='不导出JSON')
    args = parser.parse_args()

    print("=" * 50)
    print("OOH Signal - 数据清理")
    print(f"时间: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 50)

    if not os.path.exists(DB_PATH):
        print(f"数据库不存在: {DB_PATH}")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 获取清理前统计
    cursor.execute('SELECT COUNT(*) FROM signals')
    before_count = cursor.fetchone()[0]
    print(f"\n清理前信号数: {before_count}")

    # 1. 清理重复信号
    print("\n[1/3] 清理重复信号...")
    dup_deleted = cleanup_duplicates(conn)

    # 2. 清理旧数据
    print("\n[2/3] 清理超过30天的信号...")
    old_deleted = cleanup_old_signals()

    # 3. 检查链接（可选）
    if args.check_links:
        print(f"\n[3/3] 检查链接有效性（样本: {args.link_sample}）...")
        invalid = check_invalid_links(conn, args.link_sample)
    else:
        print("\n[3/3] 跳过链接检查（使用 --check-links 启用）")

    # 获取清理后统计
    cursor.execute('SELECT COUNT(*) FROM signals')
    after_count = cursor.fetchone()[0]

    print("\n" + "=" * 50)
    print("清理报告")
    print("=" * 50)
    print(f"清理前: {before_count} 条")
    print(f"清理后: {after_count} 条")
    print(f"删除重复: {dup_deleted} 条")
    print(f"删除旧数据: {old_deleted} 条")

    conn.close()

    # 导出数据
    if not args.no_export:
        print("\n导出数据到JSON...")
        export_data()

    print("\n✅ 清理完成！")


if __name__ == '__main__':
    main()
