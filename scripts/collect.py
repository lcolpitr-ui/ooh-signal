#!/usr/bin/env python3
"""主采集入口 - 运行所有采集器"""

import sys
import os
import sqlite3
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'ooh_signal.db')

from collectors.rss_collector import collect_rss
from collectors.web_scraper import collect_web
from collectors.business_scraper import collect_business
from collectors.social_collector import collect_social
from collectors.platform_collector import collect_platforms
from processors.ai_scorer import score_signals
from processors.brand_identifier import identify_brands
from processors.ai_deep_scorer import deep_score_signals
from processors.event_aggregator import aggregate_signals

def get_signal_count():
    """获取当前信号总数"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM signals")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except:
        return 0

def safe_run(name, func):
    """安全运行某个步骤，失败时不中断整体流程"""
    try:
        func()
        return True
    except Exception as e:
        print(f"  [ERROR] {name} failed: {e}")
        return False

def main():
    print("=" * 50)
    print("OOH Signal - 数据采集")
    print(f"时间: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 50)

    initial_count = get_signal_count()
    print(f"当前信号数: {initial_count}")

    results = {}

    print("\n[1/8] RSS 采集...")
    results["RSS"] = safe_run("RSS", collect_rss)

    print("\n[2/8] 网页爬虫...")
    results["Web"] = safe_run("Web", collect_web)

    print("\n[3/8] 商业数据源...")
    results["Business"] = safe_run("Business", collect_business)

    print("\n[4/8] 社交媒体...")
    results["Social"] = safe_run("Social", collect_social)

    print("\n[5/9] 小红书/抖音...")
    results["Platforms"] = safe_run("Platforms", collect_platforms)

    print("\n[6/9] 事件聚合...")
    def run_aggregator():
        stats = aggregate_signals()
        if stats['groups_found'] > 0:
            print(f"  聚合了 {stats['groups_found']} 组事件，删除 {stats['signals_deleted']} 条重复信号")
    results["Aggregator"] = safe_run("Aggregator", run_aggregator)

    print("\n[7/9] AI 基础打分...")
    results["AI Score"] = safe_run("AI Score", score_signals)

    print("\n[8/9] 品牌识别...")
    results["Brand ID"] = safe_run("Brand ID", identify_brands)

    print("\n[9/9] AI 深度打分...")
    results["Deep Score"] = safe_run("Deep Score", deep_score_signals)

    final_count = get_signal_count()
    new_signals = final_count - initial_count

    print("\n" + "=" * 50)
    print("采集报告")
    print("=" * 50)
    print(f"初始信号数: {initial_count}")
    print(f"最终信号数: {final_count}")
    print(f"新增信号: {new_signals}")
    print()
    print("步骤状态:")
    for name, success in results.items():
        status = "✅" if success else "❌"
        print(f"  {status} {name}")

    failed = [name for name, success in results.items() if not success]
    if failed:
        print(f"\n⚠️  失败步骤: {', '.join(failed)}")
        print("请检查 GitHub Secrets 配置和网络连接")
        sys.exit(1)
    elif new_signals == 0:
        print("\n⚠️  未采集到新信号（可能原因：数据源无更新、爬虫被封、Cookie过期）")
    else:
        print("\n✅ 采集完成！")

if __name__ == '__main__':
    main()
