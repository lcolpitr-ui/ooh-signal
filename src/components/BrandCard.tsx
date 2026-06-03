import Link from 'next/link'
import ScoreBadge from './ScoreBadge'

interface BrandCardProps {
  brand: {
    id: string
    name: string
    industry: string
    scale: string
    isListed: boolean
    signalCount: number
    latestScore: number
  }
}

export default function BrandCard({ brand }: BrandCardProps) {
  return (
    <Link href={`/brand/${brand.id}`}>
      <div className="bg-[var(--card)] border border-[var(--border)] rounded-lg p-4 hover:border-[var(--accent)]/30 transition-colors cursor-pointer group">
        <div className="flex items-start justify-between">
          <div>
            <h3 className="font-medium group-hover:text-[var(--accent)] transition-colors">{brand.name}</h3>
            <div className="flex gap-2 mt-1">
              <span className="text-xs text-[var(--text-secondary)]">{brand.industry}</span>
              {brand.isListed && (
                <span className="text-xs text-blue-400">上市</span>
              )}
            </div>
          </div>
          <ScoreBadge score={brand.latestScore} />
        </div>
        <div className="mt-3 text-xs text-[var(--text-secondary)]">
          信号数量: {brand.signalCount}
        </div>
      </div>
    </Link>
  )
}
