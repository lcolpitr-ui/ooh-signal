'use client'

import { useState, useEffect } from 'react'
import Sidebar from '@/components/Sidebar'
import BrandCard from '@/components/BrandCard'

export default function BrandPage() {
  const [brands, setBrands] = useState<any[]>([])
  const [industry, setIndustry] = useState('all')
  const [loading, setLoading] = useState(true)

  const industries = ['快消', '汽车', '3C', '美妆', '金融', '地产', '教育', '医疗', '餐饮', '零售']

  useEffect(() => {
    fetchBrands()
  }, [industry])

  async function fetchBrands() {
    setLoading(true)
    const params = new URLSearchParams()
    if (industry !== 'all') params.set('industry', industry)

    const res = await fetch(`/api/brands?${params}`)
    const data = await res.json()
    setBrands(data.brands || [])
    setLoading(false)
  }

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="ml-60 flex-1 p-6">
        <div className="mb-6">
          <h1 className="text-2xl font-bold">品牌库</h1>
          <p className="text-sm text-[var(--text-secondary)] mt-1">
            按行业分组的品牌列表，含投放可能性评分
          </p>
        </div>
        <select
          value={industry}
          onChange={(e) => setIndustry(e.target.value)}
          className="bg-[var(--card)] border border-[var(--border)] rounded px-3 py-1.5 text-sm text-[var(--foreground)] mb-4"
        >
          <option value="all">全部行业</option>
          {industries.map((ind) => (
            <option key={ind} value={ind}>{ind}</option>
          ))}
        </select>
        {loading ? (
          <div className="text-center py-8 text-[var(--text-secondary)]">加载中...</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {brands.map((brand) => (
              <BrandCard key={brand.id} brand={brand} />
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
