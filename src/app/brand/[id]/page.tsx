'use client'

import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import Sidebar from '@/components/Sidebar'
import SignalCard from '@/components/SignalCard'
import ScoreBadge from '@/components/ScoreBadge'
import { Signal, Brand } from '@/lib/types'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

interface ScorePoint {
  date: string
  avgScore: number
  maxScore: number
  count: number
}

export default function BrandDetailPage() {
  const params = useParams()
  const brandId = params.id as string

  const [brand, setBrand] = useState<Brand | null>(null)
  const [signals, setSignals] = useState<Signal[]>([])
  const [scores, setScores] = useState<ScorePoint[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchBrandData()
  }, [brandId])

  async function fetchBrandData() {
    setLoading(true)

    // 获取品牌信息
    const brandsRes = await fetch('/api/brands')
    const brandsData = await brandsRes.json()
    const foundBrand = brandsData.brands.find((b: Brand) => b.id === brandId)
    setBrand(foundBrand || null)

    // 获取品牌相关信号
    const signalsRes = await fetch(`/api/signals?search=${encodeURIComponent(foundBrand?.name || '')}`)
    const signalsData = await signalsRes.json()
    setSignals(signalsData.signals || [])

    // 获取评分历史
    if (foundBrand?.name) {
      const scoresRes = await fetch(`/api/brands/${encodeURIComponent(foundBrand.name)}/scores`)
      const scoresData = await scoresRes.json()
      setScores(scoresData.scores || [])
    }

    setLoading(false)
  }

  if (loading) {
    return (
      <div className="flex min-h-screen">
        <Sidebar />
        <main className="ml-60 flex-1 p-6">
          <div className="text-center py-8 text-[var(--text-secondary)]">加载中...</div>
        </main>
      </div>
    )
  }

  if (!brand) {
    return (
      <div className="flex min-h-screen">
        <Sidebar />
        <main className="ml-60 flex-1 p-6">
          <div className="text-center py-8 text-[var(--text-secondary)]">品牌未找到</div>
        </main>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="ml-60 flex-1 p-6">
        {/* 品牌头部信息 */}
        <div className="bg-[var(--card)] border border-[var(--border)] rounded-lg p-6 mb-6">
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-2xl font-bold mb-2">{brand.name}</h1>
              <div className="flex items-center gap-3">
                <span className="px-3 py-1 rounded text-sm bg-white/5 text-[var(--text-secondary)]">
                  {brand.industry || '未分类'}
                </span>
                {brand.isListed && (
                  <span className="px-3 py-1 rounded text-sm bg-blue-500/10 text-blue-400">
                    上市公司
                  </span>
                )}
                <span className="px-3 py-1 rounded text-sm bg-white/5 text-[var(--text-secondary)]">
                  {brand.scale === 'large' ? '大型企业' : brand.scale === 'medium' ? '中型企业' : '小型企业'}
                </span>
              </div>
            </div>
            <div className="text-right">
              <div className="text-sm text-[var(--text-secondary)] mb-1">投放可能性评分</div>
              <ScoreBadge score={brand.latestScore} />
            </div>
          </div>

          {/* 统计数据 */}
          <div className="grid grid-cols-3 gap-4 mt-6 pt-6 border-t border-[var(--border)]">
            <div>
              <div className="text-2xl font-bold text-[var(--accent)]">{brand.signalCount}</div>
              <div className="text-sm text-[var(--text-secondary)]">信号总数</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-[var(--accent)]">{brand.latestScore}</div>
              <div className="text-sm text-[var(--text-secondary)]">最高评分</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-[var(--accent)]">
                {signals.filter(s => s.score >= 60).length}
              </div>
              <div className="text-sm text-[var(--text-secondary)]">高分信号</div>
            </div>
          </div>
        </div>

        {/* 评分趋势图 */}
        {scores.length > 0 && (
          <div className="bg-[var(--card)] border border-[var(--border)] rounded-lg p-6 mb-6">
            <h2 className="text-lg font-semibold mb-4">评分趋势</h2>
            <ResponsiveContainer width="100%" height={240}>
              <AreaChart data={scores}>
                <defs>
                  <linearGradient id="colorAvg" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="colorMax" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e1e2e" />
                <XAxis
                  dataKey="date"
                  stroke="#a1a1aa"
                  fontSize={12}
                  tickFormatter={(v) => v.slice(5)}
                />
                <YAxis domain={[0, 100]} stroke="#a1a1aa" fontSize={12} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0f1117',
                    border: '1px solid #1e1e2e',
                    borderRadius: '8px',
                    fontSize: '12px',
                  }}
                  labelStyle={{ color: '#e4e4e7' }}
                  formatter={(value, name) => [
                    value,
                    name === 'avgScore' ? '平均分' : '最高分',
                  ]}
                  labelFormatter={(label) => `日期: ${label}`}
                />
                <Area
                  type="monotone"
                  dataKey="avgScore"
                  stroke="#6366f1"
                  fillOpacity={1}
                  fill="url(#colorAvg)"
                  name="avgScore"
                />
                <Area
                  type="monotone"
                  dataKey="maxScore"
                  stroke="#22c55e"
                  fillOpacity={1}
                  fill="url(#colorMax)"
                  name="maxScore"
                />
              </AreaChart>
            </ResponsiveContainer>
            <div className="flex items-center gap-6 mt-3 text-sm text-[var(--text-secondary)]">
              <span className="flex items-center gap-1.5">
                <span className="w-3 h-0.5 bg-[#6366f1] inline-block" /> 平均分
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-3 h-0.5 bg-[#22c55e] inline-block" /> 最高分
              </span>
              <span className="ml-auto text-xs">共 {scores.length} 个数据点</span>
            </div>
          </div>
        )}

        {/* 品牌信号列表 */}
        <div className="mb-6">
          <h2 className="text-lg font-semibold mb-4">相关信号 ({signals.length})</h2>
          {signals.length === 0 ? (
            <div className="text-center py-8 text-[var(--text-secondary)]">暂无相关信号</div>
          ) : (
            <div className="space-y-3">
              {signals.map((signal) => (
                <SignalCard key={signal.id} signal={signal} />
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
