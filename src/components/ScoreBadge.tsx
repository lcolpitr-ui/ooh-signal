interface ScoreBadgeProps {
  score: number
}

export default function ScoreBadge({ score }: ScoreBadgeProps) {
  const colorClass =
    score >= 80 ? 'score-high' :
    score >= 60 ? 'score-medium' :
    'score-low'

  return (
    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-bold ${colorClass} bg-white/5`}>
      {score}
    </span>
  )
}
