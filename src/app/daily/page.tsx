'use client'

import { useState, useEffect } from 'react'
import Sidebar from '@/components/Sidebar'

export default function DailyPage() {
  const [report, setReport] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [date, setDate] = useState(new Date().toISOString().split('T')[0])

  useEffect(() => {
    fetchReport()
  }, [date])

  async function fetchReport() {
    setLoading(true)
    const res = await fetch(`/api/daily?date=${date}`)
    const data = await res.json()
    setReport(data.content)
    setLoading(false)
  }

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="ml-60 flex-1 p-6">
        <div className="mb-6">
          <h1 className="text-2xl font-bold">每日日报</h1>
          <p className="text-sm text-[var(--text-secondary)] mt-1">
            每日自动生成的信号汇总
          </p>
        </div>
        <div className="mb-4">
          <input
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            className="bg-[var(--card)] border border-[var(--border)] rounded px-3 py-1.5 text-sm text-[var(--foreground)]"
          />
        </div>
        {loading ? (
          <div className="text-center py-8 text-[var(--text-secondary)]">加载中...</div>
        ) : report ? (
          <div className="bg-[var(--card)] border border-[var(--border)] rounded-lg p-6">
            <pre className="whitespace-pre-wrap text-sm">{report}</pre>
          </div>
        ) : (
          <div className="text-center py-8 text-[var(--text-secondary)]">
            该日期暂无日报
          </div>
        )}
      </main>
    </div>
  )
}
