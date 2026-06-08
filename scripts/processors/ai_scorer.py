import sqlite3
import os
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'ooh_signal.db')

SIGNAL_TYPE_SCORES = {
    'funding': 80,
    'expansion': 70,
    'product': 60,
    'competitor': 55,
    'industry': 50,
    'policy': 45,
}

# 时间衰减配置（指数衰减）
DECAY_HALF_LIFE = 14     # 半衰期14天（14天后保留50%）
DECAY_FLOOR = 0.15       # 最低保留15%

HIGH_SPEND_INDUSTRIES = ['快消', '汽车', '地产', '3C', '美妆', '金融', '家电', '服装', '酒水']

AUTHORITATIVE_SOURCES = ['巨潮资讯', '上交所', '深交所', 'IT桔子', '36kr']

# 融资相关关键词
FUNDING_KEYWORDS = ['融资', '投资', '获投', '估值', 'B轮', 'A轮', 'C轮', 'Pre-A', 'IPO', '上市', '募资']

# 扩张相关关键词
EXPANSION_KEYWORDS = ['开店', '扩张', '新市场', '出海', '海外', '门店', '布局', '进入']

# 产品相关关键词
PRODUCT_KEYWORDS = ['发布', '推出', '上线', '新品', '升级', '付费', '商业化']

# 代言人/明星合作相关关键词
SPOKESPERSON_KEYWORDS = ['代言人', '品牌大使', '官宣合作', '品牌代言', '代言', '大使',
                         '明星合作', '艺人合作', 'KOL合作', '博主合作', '联动', '联名']

# 品牌活动/营销相关关键词
ACTIVITY_KEYWORDS = ['品牌活动', '线下活动', '快闪', '路演', '巡演', '营销活动',
                     '推广活动', '宣传活动', '活动发布']

# 商业合作相关关键词
COOPERATION_KEYWORDS = ['跨界合作', '战略合作', '签约合作', '合作发布', '联名款']

# 展会/活动相关关键词
EXHIBITION_KEYWORDS = ['展会', '博览会', '峰会', '论坛', '发布会', '活动', '开幕']

def calculate_time_decay(published_at: str) -> float:
    """计算时间衰减系数（指数衰减，半衰期14天）

    今天=1.0, 7天=0.71, 14天=0.50, 21天=0.35, 30天=0.23
    """
    import math

    if not published_at:
        return 0.6  # 无发布时间，给一个中等系数

    try:
        # 解析发布时间
        if 'T' in published_at:
            pub_time = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
            # 如果没有时区信息，假设为UTC
            if pub_time.tzinfo is None:
                pub_time = pub_time.replace(tzinfo=timezone.utc)
        else:
            pub_time = datetime.strptime(published_at, '%Y-%m-%d').replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        age_days = max(0, (now - pub_time).total_seconds() / 86400)

        # 指数衰减
        decay = math.pow(0.5, age_days / DECAY_HALF_LIFE)
        return max(DECAY_FLOOR, decay)
    except Exception:
        return 0.6


def calculate_score(signal):
    base_score = SIGNAL_TYPE_SCORES.get(signal['signal_type'], 50)
    adjustments = 0

    if signal.get('industry') in HIGH_SPEND_INDUSTRIES:
        adjustments += 10

    if signal.get('source_name') in AUTHORITATIVE_SOURCES:
        adjustments += 5

    # 根据品牌规模加分
    if signal.get('brand_scale') == 'large':
        adjustments += 10
    elif signal.get('brand_scale') == 'medium':
        adjustments += 5

    # 根据内容关键词提升信号类型
    title = signal.get('title', '')
    summary = signal.get('summary', '')
    content = title + summary

    for kw in FUNDING_KEYWORDS:
        if kw in content:
            base_score = max(base_score, SIGNAL_TYPE_SCORES['funding'])
            break

    for kw in EXPANSION_KEYWORDS:
        if kw in content:
            base_score = max(base_score, SIGNAL_TYPE_SCORES['expansion'])
            break

    for kw in SPOKESPERSON_KEYWORDS:
        if kw in content:
            base_score = max(base_score, 75)  # 代言人合作高分
            break

    for kw in COOPERATION_KEYWORDS:
        if kw in content:
            base_score = max(base_score, 65)
            break

    for kw in ACTIVITY_KEYWORDS:
        if kw in content:
            base_score = max(base_score, 65)
            break

    raw_score = min(base_score + adjustments, 100)

    # 时间衰减
    published_at = signal.get('published_at') or signal.get('collected_at', '')
    decay = calculate_time_decay(published_at)
    final_score = max(1, round(raw_score * decay))

    return final_score

def generate_reason(signal, score):
    reasons = []
    title = signal.get('title', '')
    summary = signal.get('summary', '')
    content = title + summary

    # 根据信号类型
    if signal['signal_type'] == 'funding':
        reasons.append("融资信号，品牌可能有营销预算扩张")
    elif signal['signal_type'] == 'expansion':
        reasons.append("扩张信号，新店/新市场需要广告曝光")
    elif signal['signal_type'] == 'product':
        reasons.append("产品发布，新品上市通常伴随广告投放")

    # 根据关键词
    for kw in FUNDING_KEYWORDS:
        if kw in content:
            reasons.append(f"包含融资关键词「{kw}」")
            break

    for kw in EXPANSION_KEYWORDS:
        if kw in content:
            reasons.append(f"包含扩张关键词「{kw}」")
            break

    for kw in PRODUCT_KEYWORDS:
        if kw in content:
            reasons.append(f"包含产品关键词「{kw}」")
            break

    for kw in SPOKESPERSON_KEYWORDS:
        if kw in content:
            reasons.append(f"明星/代言人合作，需高曝光配合")
            break

    for kw in ACTIVITY_KEYWORDS:
        if kw in content:
            reasons.append(f"品牌活动信号，需提升品牌曝光")
            break

    for kw in COOPERATION_KEYWORDS:
        if kw in content:
            reasons.append(f"商业合作信号，需提升品牌影响力")
            break

    for kw in EXHIBITION_KEYWORDS:
        if kw in content:
            reasons.append(f"展会/活动信号，需提升品牌曝光")
            break

    # 根据行业
    if signal.get('industry') in HIGH_SPEND_INDUSTRIES:
        reasons.append(f"{signal['industry']}行业是户外广告高投放行业")

    # 根据评分
    if score >= 80:
        reasons.append("综合评估为高优先级线索")
    elif score >= 60:
        reasons.append("综合评估为中优先级线索")

    return '；'.join(reasons) if reasons else '行业动态，值得关注'

def score_signals():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 对所有信号重新计算分数（包含时间衰减）
    cursor.execute('SELECT * FROM signals')
    signals = cursor.fetchall()

    print(f"Scoring {len(signals)} signals (with time decay)...")

    scored = 0
    for signal in signals:
        signal_dict = dict(signal)
        new_score = calculate_score(signal_dict)

        # 只有分数变化时才更新
        if new_score != signal['score']:
            reason = generate_reason(signal_dict, new_score)
            cursor.execute('''
                UPDATE signals SET score = ?, reason = ? WHERE id = ?
            ''', (new_score, reason, signal['id']))
            scored += 1

    conn.commit()
    conn.close()
    print(f"Updated {scored} signals (total: {len(signals)})")

if __name__ == '__main__':
    score_signals()
