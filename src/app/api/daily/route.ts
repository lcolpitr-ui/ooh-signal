import { NextRequest, NextResponse } from 'next/server'
import fs from 'fs'
import path from 'path'

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams
  const date = searchParams.get('date') || new Date().toISOString().split('T')[0]

  const dailyDir = path.join(process.cwd(), 'data', 'daily')
  const filePath = path.join(dailyDir, `${date}.md`)

  try {
    if (fs.existsSync(filePath)) {
      const content = fs.readFileSync(filePath, 'utf-8')
      return NextResponse.json({ date, content })
    } else {
      return NextResponse.json({ date, content: null, message: '该日期暂无日报' })
    }
  } catch (error) {
    return NextResponse.json({ error: '读取日报失败' }, { status: 500 })
  }
}
