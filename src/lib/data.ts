import { Signal, Brand } from './types'

let signalsCache: Signal[] | null = null
let brandsCache: Brand[] | null = null

async function loadSignals(): Promise<Signal[]> {
  if (signalsCache) return signalsCache

  try {
    // 尝试从 JSON 文件加载（Vercel 环境）
    const res = await fetch(`${process.env.NEXT_PUBLIC_BASE_URL || ''}/data/signals.json`)
    if (res.ok) {
      signalsCache = await res.json()
      return signalsCache!
    }
  } catch {}

  // 回退到 SQLite（本地环境）
  try {
    const { getSignals } = await import('./db')
    signalsCache = getSignals({ limit: 1000 })
    return signalsCache
  } catch {
    return []
  }
}

async function loadBrands(): Promise<Brand[]> {
  if (brandsCache) return brandsCache

  try {
    const res = await fetch(`${process.env.NEXT_PUBLIC_BASE_URL || ''}/data/brands.json`)
    if (res.ok) {
      brandsCache = await res.json()
      return brandsCache!
    }
  } catch {}

  try {
    const { getBrands } = await import('./db')
    brandsCache = getBrands({ limit: 1000 })
    return brandsCache
  } catch {
    return []
  }
}

export async function getFilteredSignals(options: {
  limit?: number
  offset?: number
  industry?: string
  signalType?: string
  minScore?: number
  search?: string
} = {}): Promise<Signal[]> {
  let signals = await loadSignals()

  if (options.industry) {
    signals = signals.filter(s => s.industry === options.industry)
  }
  if (options.signalType) {
    signals = signals.filter(s => s.signalType === options.signalType)
  }
  if (options.minScore) {
    signals = signals.filter(s => s.score >= options.minScore!)
  }
  if (options.search) {
    const term = options.search.toLowerCase()
    signals = signals.filter(s =>
      s.brandName.toLowerCase().includes(term) ||
      s.title.toLowerCase().includes(term) ||
      s.summary.toLowerCase().includes(term)
    )
  }

  const offset = options.offset || 0
  const limit = options.limit || 50
  return signals.slice(offset, offset + limit)
}

export async function getFilteredBrands(options: {
  industry?: string
  limit?: number
} = {}): Promise<Brand[]> {
  let brands = await loadBrands()

  if (options.industry) {
    brands = brands.filter(b => b.industry === options.industry)
  }

  return brands.slice(0, options.limit || 100)
}
