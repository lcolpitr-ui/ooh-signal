#!/usr/bin/env python3
"""主采集入口 - 运行所有采集器"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from collectors.rss_collector import collect_rss
from collectors.web_scraper import collect_web
from collectors.business_scraper import collect_business
from collectors.social_collector import collect_social
from collectors.platform_collector import collect_platforms
from processors.ai_scorer import score_signals
from processors.brand_identifier import identify_brands
from processors.ai_deep_scorer import deep_score_signals

def safe_run(name, func):
    """安全运行某个步骤，失败时不中断整体流程"""
    try:
        func()
    except Exception as e:
        print(f"  [WARN] {name} failed: {e}")

def main():
    print("=" * 50)
    print("OOH Signal - 数据采集")
    print("=" * 50)

    print("\n[1/8] RSS 采集...")
    safe_run("RSS", collect_rss)

    print("\n[2/8] 网页爬虫...")
    safe_run("Web", collect_web)

    print("\n[3/8] 商业数据源...")
    safe_run("Business", collect_business)

    print("\n[4/8] 社交媒体...")
    safe_run("Social", collect_social)

    print("\n[5/8] 小红书/抖音...")
    safe_run("Platforms", collect_platforms)

    print("\n[6/8] AI 基础打分...")
    safe_run("AI Score", score_signals)

    print("\n[7/8] 品牌识别...")
    safe_run("Brand ID", identify_brands)

    print("\n[8/8] AI 深度打分...")
    safe_run("Deep Score", deep_score_signals)

    print("\n采集完成！")

if __name__ == '__main__':
    main()
