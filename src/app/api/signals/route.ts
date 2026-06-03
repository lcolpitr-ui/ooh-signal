import { NextRequest, NextResponse } from 'next/server'
import { getFilteredSignals } from '@/lib/data'

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams

  const signals = await getFilteredSignals({
    limit: parseInt(searchParams.get('limit') || '50'),
    offset: parseInt(searchParams.get('offset') || '0'),
    industry: searchParams.get('industry') || undefined,
    signalType: searchParams.get('signalType') || undefined,
    minScore: searchParams.get('minScore') ? parseInt(searchParams.get('minScore')!) : undefined,
    search: searchParams.get('search') || undefined,
  })

  return NextResponse.json({ signals })
}
