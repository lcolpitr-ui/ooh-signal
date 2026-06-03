#!/usr/bin/env python3
"""主采集入口 - 运行所有采集器"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from collectors.rss_collector import collect_rss
from collectors.web_scraper import collect_web
from processors.ai_scorer import score_signals
from processors.brand_identifier import identify_brands

def main():
    print("=" * 50)
    print("OOH Signal - 数据采集")
    print("=" * 50)

    print("\n[1/4] RSS 采集...")
    collect_rss()

    print("\n[2/4] 网页爬虫...")
    collect_web()

    print("\n[3/4] AI 打分...")
    score_signals()

    print("\n[4/4] 品牌识别...")
    identify_brands()

    print("\n采集完成！")

if __name__ == '__main__':
    main()
