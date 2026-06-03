import { Signal, Brand } from './types'
import signalsData from '../../public/data/signals.json'
import brandsData from '../../public/data/brands.json'

let signalsCache: Signal[] | null = null
let brandsCache: Brand[] | null = null

function loadSignals(): Signal[] {
  if (signalsCache) return signalsCache
  signalsCache = signalsData as unknown as Signal[]
  return signalsCache
}

function loadBrands(): Brand[] {
  if (brandsCache) return brandsCache
  brandsCache = brandsData as unknown as Brand[]
  return brandsCache
}

function getTimeThreshold(period?: string): Date | null {
  if (!period || period === 'all') return null
  const now = new Date()
  switch (period) {
    case 'today':
      return new Date(now.getFullYear(), now.getMonth(), now.getDate())
    case 'week':
      const d = new Date(now)
      d.setDate(d.getDate() - 7)
      return d
    case 'month':
      const m = new Date(now)
      m.setMonth(m.getMonth() - 1)
      return m
    default:
      return null
  }
}

export function getFilteredSignals(options: {
  limit?: number
  offset?: number
  industry?: string
  signalType?: string
  minScore?: number
  search?: string
  timePeriod?: string
} = {}): { signals: Signal[]; total: number } {
  let signals = loadSignals()

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

  const threshold = getTimeThreshold(options.timePeriod)
  if (threshold) {
    signals = signals.filter(s => new Date(s.collectedAt) >= threshold)
  }

  const total = signals.length
  const offset = options.offset || 0
  const limit = options.limit || 50
  return { signals: signals.slice(offset, offset + limit), total }
}

export function getFilteredBrands(options: {
  industry?: string
  limit?: number
} = {}): Brand[] {
  let brands = loadBrands()

  if (options.industry) {
    brands = brands.filter(b => b.industry === options.industry)
  }

  return brands.slice(0, options.limit || 100)
}
