import { NextRequest, NextResponse } from 'next/server'
import { getDb } from '@/lib/db'

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params

  const db = getDb()

  // 优先从 score_history 表查询
  const historyRows = db.prepare(`
    SELECT
      DATE(recorded_at) as date,
      ROUND(AVG(score)) as avgScore,
      MAX(score) as maxScore,
      COUNT(*) as count
    FROM score_history
    WHERE brand_name = ?
    GROUP BY DATE(recorded_at)
    ORDER BY date ASC
  `).all(id) as { date: string; avgScore: number; maxScore: number; count: number }[]

  if (historyRows.length > 0) {
    return NextResponse.json({ brandId: id, scores: historyRows })
  }

  // 降级：从 signals 表派生
  const signalRows = db.prepare(`
    SELECT
      DATE(collected_at) as date,
      ROUND(AVG(score)) as avgScore,
      MAX(score) as maxScore,
      COUNT(*) as count
    FROM signals
    WHERE brand_name = ? AND score > 0
    GROUP BY DATE(collected_at)
    ORDER BY date ASC
  `).all(id) as { date: string; avgScore: number; maxScore: number; count: number }[]

  return NextResponse.json({ brandId: id, scores: signalRows })
}
