import { NextRequest, NextResponse } from 'next/server'
import { insertSignal } from '@/lib/db'
import crypto from 'crypto'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { brandName, signalType, title, summary, sourceUrl } = body

    // 参数校验
    if (!brandName || !signalType || !title) {
      return NextResponse.json(
        { error: '品牌名称、信号类型、标题为必填项' },
        { status: 400 }
      )
    }

    // 生成 ID（与现有采集器一致：MD5 of url:title）
    const id = crypto
      .createHash('md5')
      .update(`${sourceUrl || 'manual'}:${title}`)
      .digest('hex')

    insertSignal({
      id,
      brandName,
      industry: '',
      signalType,
      title,
      summary: summary || '',
      sourceUrl: sourceUrl || '',
      sourceName: '用户提报',
      score: 0,
      reason: '用户手动提报，待AI评分',
      publishedAt: new Date().toISOString(),
    })

    return NextResponse.json({ success: true, id })
  } catch (error) {
    console.error('Submit error:', error)
    return NextResponse.json(
      { error: '提交失败，请稍后重试' },
      { status: 500 }
    )
  }
}
