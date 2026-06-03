export interface Signal {
  id: string
  brandName: string
  industry: string
  signalType: 'expansion' | 'funding' | 'product' | 'competitor' | 'policy' | 'industry'
  title: string
  summary: string
  sourceUrl: string
  sourceName: string
  score: number
  reason: string
  publishedAt: string
  collectedAt: string
  tags: string[]
}

export interface Brand {
  id: string
  name: string
  industry: string
  scale: 'large' | 'medium' | 'small'
  isListed: boolean
  signalCount: number
  latestScore: number
  website: string
}

export type SignalType = Signal['signalType']
export type Industry = string
