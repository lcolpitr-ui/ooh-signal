'use client'

import { useState, useEffect } from 'react'
import SignalCard from './SignalCard'
import FilterBar from './FilterBar'
import SearchBar from './SearchBar'
import { Signal } from '@/lib/types'

export default function SignalList({ featured = false }: { featured?: boolean }) {
  const [signals, setSignals] = useState<Signal[]>([])
  const [loading, setLoading] = useState(true)
  const [industry, setIndustry] = useState('all')
  const [signalType, setSignalType] = useState('all')
  const [search, setSearch] = useState('')

  const industries = ['快消', '汽车', '3C', '美妆', '金融', '地产', '教育', '医疗', '餐饮', '零售']
  const signalTypes = ['all', 'expansion', 'funding', 'product', 'competitor', 'policy', 'industry']

  useEffect(() => {
    fetchSignals()
  }, [industry, signalType, search])

  async function fetchSignals() {
    setLoading(true)
    const params = new URLSearchParams()
    if (industry !== 'all') params.set('industry', industry)
    if (signalType !== 'all') params.set('signalType', signalType)
    if (search) params.set('search', search)
    if (featured) params.set('minScore', '60')

    const res = await fetch(`/api/signals?${params}`)
    const data = await res.json()
    setSignals(data.signals || [])
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
        onIndustryChange={setIndustry}
        onTypeChange={setSignalType}
      />
      {loading ? (
        <div className="text-center py-8 text-[var(--text-secondary)]">加载中...</div>
      ) : signals.length === 0 ? (
        <div className="text-center py-8 text-[var(--text-secondary)]">暂无信号数据</div>
      ) : (
        <div className="space-y-3">
          {signals.map((signal) => (
            <SignalCard key={signal.id} signal={signal} />
          ))}
        </div>
      )}
    </div>
  )
}
