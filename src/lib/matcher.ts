import { Signal } from './types'

export interface Resource {
  id?: string
  name: string
  type: string
  location?: string
  district?: string
  audience?: string[]
  industries?: string[]
  price_range?: string
  daily_traffic?: number
  contact?: string
  description?: string
}

export interface MatchResult {
  resource_name: string
  resource_type: string
  resource_location: string
  brand_name: string
  signal_id: string
  signal_title: string
  signal_score: number
  match_score: number
  reasons: string[]
  reason_text: string
  recommended_budget: string
  daily_traffic: number
}

// 行业推荐媒体类型映射
const INDUSTRY_MEDIA_MAP: Record<string, string[]> = {
  '运动': ['商圈大屏', '地铁', '公交'],
  '美妆': ['商圈大屏', '电梯', '地铁'],
  '服装': ['商圈大屏', '地铁', '电梯'],
  '3C': ['商圈大屏', '地铁', '机场'],
  '汽车': ['商圈大屏', '机场', '高铁站'],
  '快消': ['社区媒体', '电梯', '公交'],
  '餐饮': ['社区媒体', '商圈大屏', '电梯'],
  '零售': ['商圈大屏', '社区媒体', '地铁'],
  '金融': ['机场', '高铁站', '商圈大屏'],
  '地产': ['商圈大屏', '机场', '高铁站'],
  '教育': ['地铁', '社区媒体', '公交'],
  '医疗': ['社区媒体', '电梯', '地铁'],
  '互联网': ['商圈大屏', '地铁', '电梯'],
  '游戏': ['商圈大屏', '地铁', '电梯'],
  '家电': ['商圈大屏', '社区媒体', '电梯'],
  '酒水': ['商圈大屏', '餐饮', '社区媒体'],
  '母婴': ['社区媒体', '电梯', '商圈大屏'],
  '宠物': ['社区媒体', '电梯', '商圈大屏'],
  '旅游': ['机场', '高铁站', '商圈大屏'],
  '航空': ['机场', '高铁站', '商圈大屏'],
}

// 预算等级映射
const BUDGET_TIERS: Record<string, { min: number; max: number; label: string }> = {
  'high': { min: 90, max: 100, label: '高预算' },
  'medium_high': { min: 80, max: 89, label: '中高预算' },
  'medium': { min: 70, max: 79, label: '中等预算' },
  'low': { min: 60, max: 69, label: '低预算' },
}

function getBudgetTier(score: number): string {
  if (score >= 90) return 'high'
  if (score >= 80) return 'medium_high'
  if (score >= 70) return 'medium'
  if (score >= 60) return 'low'
  return 'low'
}

function getRecommendedMediaTypes(industry: string): string[] {
  for (const [key, types] of Object.entries(INDUSTRY_MEDIA_MAP)) {
    if (industry.includes(key) || key.includes(industry)) {
      return types
    }
  }
  return []
}

export function calculateMatchScore(
  signal: Signal,
  resource: Resource
): { score: number; reasons: string[] } {
  let score = 0
  const reasons: string[] = []

  // 1. 行业匹配 (40分)
  if (signal.industry && resource.industries?.length) {
    const industryMatch = resource.industries.some(
      (ind) => ind.includes(signal.industry) || signal.industry.includes(ind)
    )
    if (industryMatch) {
      score += 40
      reasons.push('行业匹配')
    }
  }

  // 2. 媒体类型匹配 (30分)
  if (signal.industry && resource.type) {
    const recommendedTypes = getRecommendedMediaTypes(signal.industry)
    const typeMatch = recommendedTypes.some(
      (t) => resource.type.includes(t) || t.includes(resource.type)
    )
    if (typeMatch) {
      score += 30
      reasons.push('媒体类型匹配')
    }
  }

  // 3. 预算匹配 (20分)
  if (signal.score && resource.price_range) {
    const signalTier = getBudgetTier(signal.score)
    if (resource.price_range.startsWith(signalTier.split('_')[0])) {
      score += 20
      reasons.push('预算匹配')
    }
  }

  // 4. 受众匹配 (10分)
  if (signal.title && resource.audience?.length) {
    const titleLower = signal.title.toLowerCase()
    const audienceMatch = resource.audience.some(
      (a) => titleLower.includes(a.toLowerCase())
    )
    if (audienceMatch) {
      score += 10
      reasons.push('受众匹配')
    }
  }

  return { score, reasons }
}

export function generateMatchReason(
  signal: Signal,
  resource: Resource,
  reasons: string[]
): string {
  const parts: string[] = []

  if (reasons.includes('行业匹配')) {
    parts.push(`${signal.brandName}所在行业与${resource.type}受众契合`)
  }
  if (reasons.includes('媒体类型匹配')) {
    parts.push(`${resource.type}适合品牌曝光`)
  }
  if (reasons.includes('预算匹配')) {
    parts.push('预算范围匹配')
  }
  if (reasons.includes('受众匹配')) {
    parts.push('目标受众匹配')
  }

  return parts.join('；') || '综合评估推荐'
}

export function matchSignalsToResources(
  signals: Signal[],
  resources: Resource[],
  minScore: number = 50
): MatchResult[] {
  const results: MatchResult[] = []

  for (const signal of signals) {
    for (const resource of resources) {
      const { score, reasons } = calculateMatchScore(signal, resource)

      if (score >= minScore) {
        results.push({
          resource_name: resource.name,
          resource_type: resource.type,
          resource_location: resource.location || '',
          brand_name: signal.brandName,
          signal_id: signal.id,
          signal_title: signal.title,
          signal_score: signal.score,
          match_score: score,
          reasons,
          reason_text: generateMatchReason(signal, resource, reasons),
          recommended_budget: getBudgetTier(signal.score),
          daily_traffic: resource.daily_traffic || 0,
        })
      }
    }
  }

  // 按匹配分数降序排序
  results.sort((a, b) => b.match_score - a.match_score)

  return results
}

// 解析上传的资源数据
export function parseResourceData(data: Record<string, unknown>[]): Resource[] {
  return data.map((row, index) => {
    // 自动识别列名
    const name = findField(row, ['名称', 'name', '资源名称', '广告位名称']) || `资源${index + 1}`
    const type = findField(row, ['类型', 'type', '广告类型', '媒体类型']) || '商圈大屏'
    const location = findField(row, ['位置', 'location', '城市', '地区']) || ''
    const district = findField(row, ['区域', 'district', '区县']) || ''
    const priceRange = findField(row, ['价格', 'price', '预算', 'budget', 'price_range']) || 'medium'
    const dailyTraffic = parseInt(findField(row, ['流量', 'traffic', '日流量', 'daily_traffic']) || '0') || 0
    const contact = findField(row, ['联系人', 'contact', '联系方式']) || ''
    const description = findField(row, ['描述', 'description', '说明']) || ''

    // 解析行业和受众（可能是逗号分隔的字符串）
    const industriesStr = findField(row, ['行业', 'industries', '适用行业']) || ''
    const audienceStr = findField(row, ['受众', 'audience', '目标受众', '人群']) || ''

    const industries = industriesStr ? industriesStr.split(/[,，、]/).map(s => s.trim()).filter(Boolean) : []
    const audience = audienceStr ? audienceStr.split(/[,，、]/).map(s => s.trim()).filter(Boolean) : []

    return {
      id: `upload_${index}`,
      name,
      type,
      location,
      district,
      audience,
      industries,
      price_range: normalizePriceRange(priceRange),
      daily_traffic: dailyTraffic,
      contact,
      description,
    }
  })
}

function findField(row: Record<string, unknown>, candidates: string[]): string {
  for (const key of candidates) {
    // 精确匹配
    if (row[key] !== undefined && row[key] !== null) {
      return String(row[key]).trim()
    }
    // 模糊匹配（忽略大小写和空格）
    const normalizedKey = key.toLowerCase().replace(/\s/g, '')
    for (const rowKey of Object.keys(row)) {
      const normalizedRowKey = rowKey.toLowerCase().replace(/\s/g, '')
      if (normalizedRowKey === normalizedKey || normalizedRowKey.includes(normalizedKey)) {
        return String(row[rowKey]).trim()
      }
    }
  }
  return ''
}

function normalizePriceRange(value: string): string {
  const lower = value.toLowerCase()
  if (lower.includes('high') || lower.includes('高')) return 'high'
  if (lower.includes('medium_high') || lower.includes('中高')) return 'medium_high'
  if (lower.includes('medium') || lower.includes('中')) return 'medium'
  if (lower.includes('low') || lower.includes('低')) return 'low'
  return 'medium'
}
