'use client'

import { useState, useEffect } from 'react'
import SignalCard from './SignalCard'
import FilterBar from './FilterBar'
import SearchBar from './SearchBar'
import { Signal } from '@/lib/types'

const PAGE_SIZE = 20

export default function SignalList({ featured = false }: { featured?: boolean }) {
  const [signals, setSignals] = useState<Signal[]>([])
  const [loading, setLoading] = useState(true)
  const [industry, setIndustry] = useState('all')
  const [signalType, setSignalType] = useState('all')
  const [timePeriod, setTimePeriod] = useState('all')
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)

  const industries = ['快消', '汽车', '3C', '美妆', '金融', '地产', '教育', '医疗', '餐饮', '零售']
  const signalTypes = ['all', 'expansion', 'funding', 'product', 'competitor', 'policy', 'industry']

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))

  useEffect(() => {
    setPage(1)
  }, [industry, signalType, timePeriod, search])

  useEffect(() => {
    fetchSignals()
  }, [industry, signalType, timePeriod, search, page])

  async function fetchSignals() {
    setLoading(true)
    const params = new URLSearchParams()
    if (industry !== 'all') params.set('industry', industry)
    if (signalType !== 'all') params.set('signalType', signalType)
    if (timePeriod !== 'all') params.set('timePeriod', timePeriod)
    if (search) params.set('search', search)
    if (featured) {
      params.set('minScore', '60')
      params.set('timePeriod', '3day')
    }
    params.set('limit', String(PAGE_SIZE))
    params.set('offset', String((page - 1) * PAGE_SIZE))

    const res = await fetch(`/api/signals?${params}`)
    const data = await res.json()
    setSignals(data.signals || [])
    setTotal(data.total || 0)
    setLoading(false)
  }

  return (
    <div>
      <SearchBar onSearch={setSearch} />
      <FilterBar
        industries={industries}
        signalTypes={signalTypes}
        selectedIndustry={industry}
        selectedType={signalType}
        selectedTime={timePeriod}
        onIndustryChange={setIndustry}
        onTypeChange={setSignalType}
        onTimeChange={setTimePeriod}
      />

      {/* 结果统计 */}
      {!loading && (
        <div className="flex items-center justify-between mb-3 text-sm text-[var(--text-secondary)]">
          <span>共 {total} 条信号</span>
          <span>第 {page} / {totalPages} 页</span>
        </div>
      )}

      {loading ? (
        <div className="text-center py-8 text-[var(--text-secondary)]">加载中...</div>
      ) : signals.length === 0 ? (
        <div className="text-center py-8 text-[var(--text-secondary)]">暂无信号数据</div>
      ) : (
        <>
          <div className="space-y-3">
            {signals.map((signal) => (
              <SignalCard key={signal.id} signal={signal} />
            ))}
          </div>

          {/* 分页控件 */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2 mt-6">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="px-3 py-1.5 text-sm rounded border border-[var(--border)] bg-[var(--card)] hover:border-[var(--accent)]/30 disabled:opacity-40 disabled:cursor-not-allowed transition"
              >
                上一页
              </button>

              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                let pageNum: number
                if (totalPages <= 5) {
                  pageNum = i + 1
                } else if (page <= 3) {
                  pageNum = i + 1
                } else if (page >= totalPages - 2) {
                  pageNum = totalPages - 4 + i
                } else {
                  pageNum = page - 2 + i
                }
                return (
                  <button
                    key={pageNum}
                    onClick={() => setPage(pageNum)}
                    className={`w-8 h-8 text-sm rounded border transition ${
                      pageNum === page
                        ? 'border-[var(--accent)] bg-[var(--accent)] text-white'
                        : 'border-[var(--border)] bg-[var(--card)] hover:border-[var(--accent)]/30'
                    }`}
                  >
                    {pageNum}
                  </button>
                )
              })}

              <button
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
                className="px-3 py-1.5 text-sm rounded border border-[var(--border)] bg-[var(--card)] hover:border-[var(--accent)]/30 disabled:opacity-40 disabled:cursor-not-allowed transition"
              >
                下一页
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
