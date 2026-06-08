#!/usr/bin/env python3
"""事件聚合器 - 将同品牌、同事件的多条信号聚合为一条

聚合策略：
1. 按 brand_name 分组（排除"待识别"）
2. 同品牌内用标题+摘要相似度判断是否为同一事件
3. 保留得分最高的信号，聚合互动数据
4. 删除被合并的信号

用法：
  python scripts/processors/event_aggregator.py
  python scripts/processors/event_aggregator.py --threshold 0.55  # 调整相似度阈值
  python scripts/processors/event_aggregator.py --dry-run         # 仅预览，不执行
"""

import sqlite3
import os
import re
import sys
import argparse
from collections import defaultdict
from difflib import SequenceMatcher

DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'ooh_signal.db')

# 相似度阈值
TITLE_HIGH_THRESHOLD = 0.85   # 标题高度相似（现有去重已覆盖）
SUMMARY_THRESHOLD = 0.60       # 摘要相似度阈值
KEYWORD_THRESHOLD = 0.50       # 关键词重合度阈值


def normalize_text(text: str) -> str:
    """标准化文本用于比较"""
    if not text:
        return ''
    text = re.sub(r'[^\w一-鿿]', '', text)
    return text.lower().strip()


def extract_hashtags(text: str) -> set:
    """提取话题标签 #xxx#"""
    if not text:
        return set()
    tags = re.findall(r'#([^#\s]{2,30})#', text)
    return {t.lower().strip() for t in tags}


# 事件类型关键词
EVENT_TYPES = {
    '融资', '投资', '募资', '增资', '入股', '加仓',
    'IPO', '上市', '挂牌', '退市',
    '代言', '品牌大使', '品牌代言人', '全球代言人', '全球品牌代言人',
    '发布', '上线', '推出', '官宣', '正式官宣',
    '开店', '新店', '扩张', '门店',
    '收购', '并购', '合并',
    '降价', '涨价', '调价',
    '合作', '战略', '签约', '联动', '联名',
    '裁员', '招人', '招聘',
    '升级', '更新',
}

# 事件类型关联组：同组内的事件类型视为相关
EVENT_GROUPS = [
    {'代言', '品牌大使', '品牌代言人', '全球代言人', '全球品牌代言人', '官宣', '正式官宣'},
    {'融资', '投资', '募资', '增资'},
    {'IPO', '上市', '挂牌'},
    {'开店', '新店', '扩张', '门店'},
    {'收购', '并购', '合并'},
    {'降价', '涨价', '调价'},
    {'合作', '战略', '签约', '联动', '联名'},
]


def has_related_event(events1: set, events2: set) -> bool:
    """判断两组事件类型是否相关（同组内视为相关）"""
    if events1 & events2:
        return True
    for group in EVENT_GROUPS:
        if events1 & group and events2 & group:
            return True
    return False


def extract_amounts(text: str) -> set:
    """提取金额（如 800亿美元、10亿、100亿）"""
    if not text:
        return set()
    amounts = set()
    # 匹配: 数字 + 万/亿 + 美元/元/人民币
    for m in re.finditer(r'([\d,.]+)\s*(万亿|亿|万)\s*(美元|美金|港币|人民币|元)?', text):
        num, unit, currency = m.group(1), m.group(2), m.group(3) or ''
        amounts.add(f"{num}{unit}{currency}")
    # 单独匹配大数字
    for m in re.finditer(r'([\d,]{3,})\s*(万美元|万美元|美元|元)', text):
        amounts.add(m.group(0).replace(' ', ''))
    return amounts


def extract_event_keywords(text: str) -> set:
    """提取事件类型关键词"""
    if not text:
        return set()
    found = set()
    for kw in EVENT_TYPES:
        if kw in text:
            found.add(kw)
    return found


def extract_keywords(text: str) -> set:
    """从文本中提取结构化关键信息"""
    if not text:
        return set()
    keywords = set()

    # 1. 话题标签
    keywords.update(extract_hashtags(text))

    # 2. 英文词（品牌名、人名）- 提取多词短语和单个词
    en_phrases = re.findall(r'[A-Za-z][A-Za-z\s]{1,20}[A-Za-z]', text)
    for phrase in en_phrases:
        phrase = phrase.strip().lower()
        if len(phrase) >= 2:
            keywords.add(phrase)
            # 同时添加单个词（解决 "in bobbi brown" vs "bobbi brown" 问题）
            for word in phrase.split():
                if len(word) >= 2:
                    keywords.add(word)

    # 3. 金额
    keywords.update(extract_amounts(text))

    # 4. 事件类型
    keywords.update(extract_event_keywords(text))

    return keywords


def calculate_keyword_overlap(kw1: set, kw2: set) -> float:
    """计算关键词重合度（使用较小集合为分母）"""
    if not kw1 or not kw2:
        return 0.0
    intersection = kw1 & kw2
    min_size = min(len(kw1), len(kw2))
    return len(intersection) / min_size if min_size else 0.0


# 新闻汇总/市场评论类标题模式（不应被合并）
ROUNDUP_PATTERNS = [
    '氪星晚报', '早报', '晚报', '日报', '速报', '快讯',
    '盘前', '盘后', '涨跌不一', '收涨', '收跌',
    'Edge AI Daily', '每日', '一周', '盘点',
    '东方财富', '雪球', '股吧', '暴涨', '暴跌', '翻倍',
    '产业链梳理', '概念股',
]


def is_news_roundup(title: str) -> bool:
    """判断是否为新闻汇总/市场评论类信号"""
    if not title:
        return False
    return any(p in title for p in ROUNDUP_PATTERNS)


def is_same_event(title1: str, summary1: str, title2: str, summary2: str) -> bool:
    """判断两条信号是否描述同一事件

    判断逻辑（任一条件满足即判定为同一事件）：
    1. 标题高度相似（>= 0.85）
    2. 共享话题标签（#xxx#）
    3. 结构化关键词匹配：共享金额 + 事件类型
    4. 摘要相似度（>= 0.60）
    5. 关键词重合度（>= 0.40）

    特殊规则：新闻汇总/市场评论类信号只通过标题高度相似度合并
    """
    # 新闻汇总类信号：只允许标题高度相似（防止不同期的晚报被合并）
    if is_news_roundup(title1) or is_news_roundup(title2):
        norm_t1 = normalize_text(title1)
        norm_t2 = normalize_text(title2)
        if norm_t1 and norm_t2:
            return SequenceMatcher(None, norm_t1, norm_t2).ratio() >= 0.90
        return False

    # 1. 标题高度相似
    norm_t1 = normalize_text(title1)
    norm_t2 = normalize_text(title2)
    if norm_t1 and norm_t2:
        title_sim = SequenceMatcher(None, norm_t1, norm_t2).ratio()
        if title_sim >= TITLE_HIGH_THRESHOLD:
            return True

    # 2. 共享话题标签（社交帖子的强信号）
    ht1 = extract_hashtags(f"{title1 or ''} {summary1 or ''}")
    ht2 = extract_hashtags(f"{title2 or ''} {summary2 or ''}")
    if ht1 and ht2:
        shared_ht = ht1 & ht2
        if shared_ht and len(shared_ht) >= min(len(ht1), len(ht2)) * 0.5:
            return True

    # 3. 结构化匹配：共享金额 + 事件类型
    combined1 = f"{title1 or ''} {summary1 or ''}"
    combined2 = f"{title2 or ''} {summary2 or ''}"
    amounts1 = extract_amounts(combined1)
    amounts2 = extract_amounts(combined2)
    events1 = extract_event_keywords(combined1)
    events2 = extract_event_keywords(combined2)

    # 共享金额 → 很可能是同一事件
    if amounts1 and amounts2 and amounts1 & amounts2:
        return True

    # 相关事件类型 + 高关键词重合
    if events1 and events2 and has_related_event(events1, events2):
        kw1 = extract_keywords(combined1)
        kw2 = extract_keywords(combined2)
        overlap = calculate_keyword_overlap(kw1, kw2)
        if overlap >= 0.25:
            return True

    # 4. 摘要相似度
    norm_s1 = normalize_text(summary1)
    norm_s2 = normalize_text(summary2)
    if norm_s1 and norm_s2 and len(norm_s1) > 10 and len(norm_s2) > 10:
        summary_sim = SequenceMatcher(None, norm_s1, norm_s2).ratio()
        if summary_sim >= SUMMARY_THRESHOLD:
            return True

    # 5. 关键词重合度
    kw1 = extract_keywords(combined1)
    kw2 = extract_keywords(combined2)
    if kw1 and kw2:
        overlap = calculate_keyword_overlap(kw1, kw2)
        if overlap >= KEYWORD_THRESHOLD:
            return True

    return False


# 品牌别名映射：将中英文名称统一为一个标准名
BRAND_ALIASES = {
    '芭比波朗': 'Bobbi Brown',
    '谷歌': 'Alphabet',
    '宝格丽': 'BVLGARI',
    '爱马仕': 'Hermes',
    '路易威登': 'Louis Vuitton',
    '香奈儿': 'Chanel',
    '迪奥': 'Dior',
    '古驰': 'Gucci',
    '普拉达': 'Prada',
    '卡地亚': 'Cartier',
    '蒂芙尼': 'Tiffany',
    '华为云': '华为',
    '腾讯云': '腾讯',
    '腾讯会议': '腾讯',
    '长安汽车': '长安',
    '小鹏集团': '小鹏',
    '阿里速卖通': '阿里',
    '高德地图': '高德',
    '京东方A': '京东方',
    'MiuMiu': 'Miu Miu',
}


def normalize_brand(brand_name: str) -> str:
    """统一品牌名称（将别名映射到标准名）"""
    return BRAND_ALIASES.get(brand_name, brand_name)


def aggregate_signals(dry_run: bool = False, threshold: float = SUMMARY_THRESHOLD) -> dict:
    """聚合同品牌同事件的信号

    返回聚合统计信息
    """
    global SUMMARY_THRESHOLD
    SUMMARY_THRESHOLD = threshold

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 获取所有已识别品牌的信号，按品牌分组
    cursor.execute("""
        SELECT id, brand_name, title, summary, source_url, source_name,
               score, likes, reposts, comments, author, author_followers,
               related_count
        FROM signals
        WHERE brand_name != '待识别'
        ORDER BY brand_name, score DESC, collected_at DESC
    """)
    all_signals = cursor.fetchall()

    # 按品牌分组（使用标准化品牌名）
    by_brand = defaultdict(list)
    for row in all_signals:
        normalized = normalize_brand(row['brand_name'])
        row_dict = dict(row)
        row_dict['_normalized_brand'] = normalized
        by_brand[normalized].append(row_dict)

    stats = {
        'total_before': len(all_signals),
        'brands_processed': 0,
        'groups_found': 0,
        'signals_deleted': 0,
        'details': []
    }

    ids_to_delete = []
    updates = []  # (id, aggregated_likes, aggregated_reposts, aggregated_comments, related_count)

    for brand, signals in by_brand.items():
        if len(signals) < 2:
            continue

        stats['brands_processed'] += 1
        # 已聚合的信号列表，每项是 (signal_dict, [被聚合的信号列表])
        groups = []

        for signal in signals:
            merged = False
            for group in groups:
                primary = group[0]
                if is_same_event(
                    primary['title'], primary['summary'],
                    signal['title'], signal['summary']
                ):
                    # 合并到该组
                    group.append(signal)
                    merged = True
                    break

            if not merged:
                groups.append([signal])

        # 处理聚合结果
        for group in groups:
            if len(group) <= 1:
                continue

            stats['groups_found'] += 1

            # 按 score 降序，保留得分最高的
            group.sort(key=lambda x: (x['score'] or 0, x['likes'] or 0), reverse=True)
            primary = group[0]
            to_merge = group[1:]

            # 聚合互动数据
            total_likes = sum(s['likes'] or 0 for s in group)
            total_reposts = sum(s['reposts'] or 0 for s in group)
            total_comments = sum(s['comments'] or 0 for s in group)
            # 保留互动最高的作者
            best_author = max(group, key=lambda x: (x['likes'] or 0) + (x['comments'] or 0))['author']

            # 选择信息最完整的 summary
            best_summary = max(group, key=lambda x: len(x['summary'] or ''))['summary']

            existing_related = primary.get('related_count') or 1
            new_related = existing_related + len(to_merge)

            # 检查是否需要更新品牌名为标准名
            normalized_brand = primary.get('_normalized_brand', brand)
            brand_update = normalized_brand if normalized_brand != primary['brand_name'] else None

            updates.append({
                'id': primary['id'],
                'likes': total_likes,
                'reposts': total_reposts,
                'comments': total_comments,
                'author': best_author or primary['author'],
                'summary': best_summary[:500] if best_summary else primary['summary'],
                'related_count': new_related,
                'brand_name': brand_update,
            })

            for s in to_merge:
                ids_to_delete.append(s['id'])

            detail = {
                'brand': brand,
                'primary_title': primary['title'][:50],
                'merged_count': len(to_merge),
                'merged_titles': [s['title'][:40] for s in to_merge[:3]]
            }
            stats['details'].append(detail)

            if not dry_run:
                try:
                    print(f"  [{brand}] 聚合 {len(to_merge)} 条 -> {primary['title'][:40]}...")
                except UnicodeEncodeError:
                    print(f"  [{brand}] merged {len(to_merge)} signals")

    # 执行数据库更新
    if not dry_run and (updates or ids_to_delete):
        # 更新主信号的互动数据、品牌名和 related_count
        for u in updates:
            if u['brand_name']:
                cursor.execute("""
                    UPDATE signals SET
                        brand_name = ?, likes = ?, reposts = ?, comments = ?,
                        author = ?, summary = ?, related_count = ?
                    WHERE id = ?
                """, (u['brand_name'], u['likes'], u['reposts'], u['comments'],
                      u['author'], u['summary'], u['related_count'], u['id']))
            else:
                cursor.execute("""
                    UPDATE signals SET
                        likes = ?, reposts = ?, comments = ?,
                        author = ?, summary = ?, related_count = ?
                    WHERE id = ?
                """, (u['likes'], u['reposts'], u['comments'],
                      u['author'], u['summary'], u['related_count'], u['id']))

        # 删除被合并的信号
        if ids_to_delete:
            placeholders = ','.join(['?'] * len(ids_to_delete))
            cursor.execute(f"DELETE FROM signals WHERE id IN ({placeholders})", ids_to_delete)

        conn.commit()
        stats['signals_deleted'] = len(ids_to_delete)

    # 统计最终数量
    cursor.execute("SELECT COUNT(*) FROM signals")
    stats['total_after'] = cursor.fetchone()[0]

    conn.close()
    return stats


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description='事件聚合器 - 合并同品牌同事件信号')
    parser.add_argument('--threshold', type=float, default=0.60, help='摘要相似度阈值 (默认0.60)')
    parser.add_argument('--dry-run', action='store_true', help='仅预览，不执行删除')
    args = parser.parse_args()

    print("=" * 50)
    print("OOH Signal - 事件聚合")
    print("=" * 50)

    if args.dry_run:
        print("[DRY RUN] 仅预览，不执行实际操作\n")

    stats = aggregate_signals(dry_run=args.dry_run, threshold=args.threshold)

    print(f"\n聚合统计:")
    print(f"  处理品牌数: {stats['brands_processed']}")
    print(f"  发现事件组: {stats['groups_found']}")
    print(f"  聚合前信号: {stats['total_before']}")
    print(f"  删除重复信号: {stats['signals_deleted']}")
    print(f"  聚合后信号: {stats['total_after']}")

    if stats['details']:
        print(f"\n聚合详情 (共 {len(stats['details'])} 组):")
        for d in stats['details'][:20]:
            try:
                print(f"  [{d['brand']}] {d['primary_title']} (+{d['merged_count']}条)")
            except UnicodeEncodeError:
                print(f"  [{d['brand']}] merged {d['merged_count']} signals")

    print("\n✅ 聚合完成！")


if __name__ == '__main__':
    main()
