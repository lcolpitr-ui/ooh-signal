import { NextRequest, NextResponse } from 'next/server'
import { Signal } from '@/lib/types'
import signalsData from '../../../../public/data/signals.json'
import { matchSignalsToResources, parseResourceData, Resource } from '@/lib/matcher'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { resources: rawResources, minScore = 50 } = body

    if (!rawResources || !Array.isArray(rawResources) || rawResources.length === 0) {
      return NextResponse.json({ error: '请提供资源数据' }, { status: 400 })
    }

    // 解析资源数据
    const resources: Resource[] = parseResourceData(rawResources)

    // 获取高分信号
    const signals = (signalsData as unknown as Signal[])
      .filter(s => s.score >= 70 && s.brandName && s.brandName !== '待识别')
      .sort((a, b) => b.score - a.score)
      .slice(0, 100)

    // 执行匹配
    const matches = matchSignalsToResources(signals, resources, minScore)

    return NextResponse.json({
      success: true,
      generated_at: new Date().toISOString(),
      total_resources: resources.length,
      total_signals: signals.length,
      total_matches: matches.length,
      matches,
    })
  } catch (error) {
    console.error('Match error:', error)
    return NextResponse.json({ error: '匹配计算失败' }, { status: 500 })
  }
}
