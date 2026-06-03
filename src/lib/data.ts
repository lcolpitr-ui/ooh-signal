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

export function getFilteredSignals(options: {
  limit?: number
  offset?: number
  industry?: string
  signalType?: string
  minScore?: number
  search?: string
} = {}): Signal[] {
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

  const offset = options.offset || 0
  const limit = options.limit || 50
  return signals.slice(offset, offset + limit)
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
