import { NextRequest, NextResponse } from 'next/server'
import { getDb } from '@/lib/db'

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params

  const db = getDb()

  // 用品牌名查询 signals 表，按日期聚合评分
  const rows = db.prepare(`
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

  return NextResponse.json({ brandId: id, scores: rows })
}
