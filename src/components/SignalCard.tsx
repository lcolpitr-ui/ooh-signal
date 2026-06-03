import ScoreBadge from './ScoreBadge'
import { Signal } from '@/lib/types'
import { stripHtml } from '@/lib/utils'

const signalTypeLabels: Record<string, string> = {
  expansion: '扩张',
  funding: '融资',
  product: '产品',
  competitor: '竞品',
  policy: '政策',
  industry: '行业',
}

const signalTypeColors: Record<string, string> = {
  expansion: 'bg-green-500/10 text-green-400',
  funding: 'bg-yellow-500/10 text-yellow-400',
  product: 'bg-blue-500/10 text-blue-400',
  competitor: 'bg-purple-500/10 text-purple-400',
  policy: 'bg-red-500/10 text-red-400',
  industry: 'bg-gray-500/10 text-gray-400',
}

export default function SignalCard({ signal }: { signal: Signal }) {
  return (
    <article className="bg-[var(--card)] border border-[var(--border)] rounded-lg p-4 hover:border-[var(--accent)]/30 transition-colors cursor-pointer group">
      <a href={signal.sourceUrl} target="_blank" rel="noopener noreferrer" className="block">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <span className="font-medium text-[var(--foreground)]">{signal.brandName}</span>
              <span className={`px-2 py-0.5 rounded text-xs ${signalTypeColors[signal.signalType]}`}>
                {signalTypeLabels[signal.signalType]}
              </span>
              {signal.industry && (
                <span className="px-2 py-0.5 rounded text-xs bg-white/5 text-[var(--text-secondary)]">
                  {signal.industry}
                </span>
              )}
            </div>
            <h3 className="text-sm font-medium mb-1 group-hover:text-[var(--accent)] transition-colors">
              {signal.title}
            </h3>
            <p className="text-sm text-[var(--text-secondary)] line-clamp-2">{stripHtml(signal.summary)}</p>
            <p className="text-xs text-[var(--accent)] mt-2 italic">{signal.reason}</p>
          </div>
          <ScoreBadge score={signal.score} />
        </div>
        <div className="flex items-center gap-4 mt-3 text-xs text-[var(--text-secondary)]">
          <span>{signal.sourceName}</span>
          <span>{new Date(signal.publishedAt).toLocaleDateString('zh-CN')}</span>
          <span className="text-[var(--accent)] opacity-0 group-hover:opacity-100 transition-opacity">
            查看原文 →
          </span>
        </div>
      </a>
    </article>
  )
}
