import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'ooh_signal.db')

SIGNAL_TYPE_SCORES = {
    'funding': 80,
    'expansion': 70,
    'product': 60,
    'competitor': 55,
    'industry': 50,
    'policy': 45,
}

HIGH_SPEND_INDUSTRIES = ['快消', '汽车', '地产', '3C', '美妆', '金融', '家电', '服装', '酒水']

AUTHORITATIVE_SOURCES = ['巨潮资讯', '上交所', '深交所', 'IT桔子', '36kr']

# 融资相关关键词
FUNDING_KEYWORDS = ['融资', '投资', '获投', '估值', 'B轮', 'A轮', 'C轮', 'Pre-A', 'IPO', '上市', '募资']

# 扩张相关关键词
EXPANSION_KEYWORDS = ['开店', '扩张', '新市场', '出海', '海外', '门店', '布局', '进入']

# 产品相关关键词
PRODUCT_KEYWORDS = ['发布', '推出', '上线', '新品', '升级', '付费', '商业化']

# 代言人相关关键词
SPOKESPERSON_KEYWORDS = ['代言人', '品牌大使', '官宣合作', '品牌代言', '代言', '大使']

# 展会/活动相关关键词
EXHIBITION_KEYWORDS = ['展会', '博览会', '峰会', '论坛', '发布会', '活动', '开幕']

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

    return min(base_score + adjustments, 100)

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
            reasons.append(f"品牌代言人官宣，需高曝光配合")
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

    cursor.execute('SELECT * FROM signals WHERE score = 0 OR reason IS NULL OR reason = "" OR reason = "待分析"')
    signals = cursor.fetchall()

    print(f"Scoring {len(signals)} signals...")

    for signal in signals:
        signal_dict = dict(signal)
        score = calculate_score(signal_dict)
        reason = generate_reason(signal_dict, score)

        cursor.execute('''
            UPDATE signals SET score = ?, reason = ? WHERE id = ?
        ''', (score, reason, signal['id']))

    conn.commit()
    conn.close()
    print(f"Scored {len(signals)} signals")

if __name__ == '__main__':
    score_signals()
