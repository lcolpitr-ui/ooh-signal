import { NextRequest, NextResponse } from 'next/server'
import { getFilteredBrands } from '@/lib/data'

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams

  const brands = await getFilteredBrands({
    industry: searchParams.get('industry') || undefined,
    limit: parseInt(searchParams.get('limit') || '100'),
  })

  return NextResponse.json({ brands })
}
