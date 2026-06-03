import { NextResponse } from 'next/server'
import { getFilteredSignals } from '@/lib/data'

export async function GET() {
  const signals = getFilteredSignals({ limit: 50, minScore: 60 })

  const items = signals.map((signal) => `
    <item>
      <title><![CDATA[${signal.brandName} - ${signal.title}]]></title>
      <link>${signal.sourceUrl}</link>
      <description><![CDATA[${signal.summary}\n\n推荐理由: ${signal.reason}]]></description>
      <pubDate>${new Date(signal.publishedAt).toUTCString()}</pubDate>
      <guid>${signal.id}</guid>
      <author>noreply@oohsignal.com (${signal.sourceName})</author>
    </item>
  `).join('')

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>OOH Signal — 精选</title>
    <link>https://oohsignal.com</link>
    <description>户外广告投放信号情报</description>
    <language>zh-CN</language>
    <atom:link href="https://oohsignal.com/feed" rel="self" type="application/rss+xml" />
    <lastBuildDate>${new Date().toUTCString()}</lastBuildDate>
    ${items}
  </channel>
</rss>`

  return new NextResponse(xml, {
    headers: {
      'Content-Type': 'application/rss+xml',
    },
  })
}
