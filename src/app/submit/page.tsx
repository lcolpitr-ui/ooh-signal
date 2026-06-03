'use client'

import { useState } from 'react'
import Sidebar from '@/components/Sidebar'

const SIGNAL_TYPES = [
  { value: 'expansion', label: '📈 扩张' },
  { value: 'funding', label: '💰 融资' },
  { value: 'product', label: '🆕 产品' },
  { value: 'competitor', label: '⚔️ 竞品' },
  { value: 'policy', label: '📜 政策' },
  { value: 'industry', label: '🏢 行业' },
]

export default function SubmitPage() {
  const [form, setForm] = useState({
    brandName: '',
    signalType: 'expansion',
    title: '',
    summary: '',
    sourceUrl: '',
  })
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle')
  const [message, setMessage] = useState('')

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setStatus('loading')

    try {
      const res = await fetch('/api/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      })
      const data = await res.json()

      if (res.ok) {
        setStatus('success')
        setMessage('提交成功！信号将在下次采集后参与AI评分。')
        setForm({ brandName: '', signalType: 'expansion', title: '', summary: '', sourceUrl: '' })
      } else {
        setStatus('error')
        setMessage(data.error || '提交失败')
      }
    } catch {
      setStatus('error')
      setMessage('网络错误，请稍后重试')
    }
  }

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="ml-60 flex-1 p-6">
        <div className="mb-6">
          <h1 className="text-2xl font-bold">信源提报</h1>
          <p className="text-sm text-[var(--text-secondary)] mt-1">
            提交品牌线索或数据源，帮助发现更多投放信号
          </p>
        </div>

        <form onSubmit={handleSubmit} className="bg-[var(--card)] border border-[var(--border)] rounded-lg p-6 max-w-2xl">
          <div className="space-y-4">
            {/* 品牌名称 */}
            <div>
              <label className="block text-sm font-medium mb-1.5">品牌名称 <span className="text-red-400">*</span></label>
              <input
                type="text"
                value={form.brandName}
                onChange={(e) => setForm({ ...form, brandName: e.target.value })}
                placeholder="例如：零跑汽车"
                className="w-full bg-[var(--background)] border border-[var(--border)] rounded px-3 py-2 text-sm focus:outline-none focus:border-[var(--accent)]"
                required
              />
            </div>

            {/* 信号类型 */}
            <div>
              <label className="block text-sm font-medium mb-1.5">信号类型 <span className="text-red-400">*</span></label>
              <select
                value={form.signalType}
                onChange={(e) => setForm({ ...form, signalType: e.target.value })}
                className="w-full bg-[var(--background)] border border-[var(--border)] rounded px-3 py-2 text-sm focus:outline-none focus:border-[var(--accent)]"
              >
                {SIGNAL_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
            </div>

            {/* 标题 */}
            <div>
              <label className="block text-sm font-medium mb-1.5">标题 <span className="text-red-400">*</span></label>
              <input
                type="text"
                value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })}
                placeholder="例如：零跑汽车宣布2026年新开200家门店"
                className="w-full bg-[var(--background)] border border-[var(--border)] rounded px-3 py-2 text-sm focus:outline-none focus:border-[var(--accent)]"
                required
              />
            </div>

            {/* 摘要 */}
            <div>
              <label className="block text-sm font-medium mb-1.5">摘要</label>
              <textarea
                value={form.summary}
                onChange={(e) => setForm({ ...form, summary: e.target.value })}
                placeholder="补充详细信息..."
                rows={3}
                className="w-full bg-[var(--background)] border border-[var(--border)] rounded px-3 py-2 text-sm focus:outline-none focus:border-[var(--accent)] resize-none"
              />
            </div>

            {/* 来源链接 */}
            <div>
              <label className="block text-sm font-medium mb-1.5">来源链接</label>
              <input
                type="url"
                value={form.sourceUrl}
                onChange={(e) => setForm({ ...form, sourceUrl: e.target.value })}
                placeholder="https://..."
                className="w-full bg-[var(--background)] border border-[var(--border)] rounded px-3 py-2 text-sm focus:outline-none focus:border-[var(--accent)]"
              />
            </div>
          </div>

          {/* 状态提示 */}
          {status !== 'idle' && status !== 'loading' && (
            <div className={`mt-4 px-3 py-2 rounded text-sm ${
              status === 'success' ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'
            }`}>
              {message}
            </div>
          )}

          {/* 提交按钮 */}
          <button
            type="submit"
            disabled={status === 'loading'}
            className="mt-6 w-full bg-[var(--accent)] text-white rounded px-4 py-2.5 text-sm font-medium hover:opacity-90 disabled:opacity-50 transition"
          >
            {status === 'loading' ? '提交中...' : '提交信号'}
          </button>
        </form>
      </main>
    </div>
  )
}
