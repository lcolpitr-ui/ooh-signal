'use client'

import { useState, useRef } from 'react'

interface Match {
  signal_id: string
  signal_title: string
  brand_name: string
  signal_score: number
  resource_name: string
  resource_type: string
  resource_location: string
  match_score: number
  reasons: string[]
  reason_text: string
  recommended_budget: string
  daily_traffic: number
}

interface MatchResult {
  success: boolean
  generated_at: string
  total_resources: number
  total_signals: number
  total_matches: number
  matches: Match[]
}

interface ParsedData {
  success: boolean
  filename: string
  rows: number
  data: Record<string, unknown>[]
  columns: string[]
}

export default function PlaygroundPage() {
  const [parsedData, setParsedData] = useState<ParsedData | null>(null)
  const [matchResult, setMatchResult] = useState<MatchResult | null>(null)
  const [uploading, setUploading] = useState(false)
  const [matching, setMatching] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [locationFilter, setLocationFilter] = useState('all')
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setUploading(true)
    setError(null)
    setMatchResult(null)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const res = await fetch('/api/match/upload', {
        method: 'POST',
        body: formData,
      })

      // 检查响应是否是 JSON
      const contentType = res.headers.get('content-type')
      if (!contentType || !contentType.includes('application/json')) {
        throw new Error('服务器返回了非JSON响应，请检查文件格式')
      }

      const data = await res.json()

      if (!res.ok) {
        throw new Error(data.error || '上传失败')
      }

      setParsedData(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : '上传失败，请检查文件格式')
    } finally {
      setUploading(false)
    }
  }

  const handleMatch = async () => {
    if (!parsedData?.data) return

    setMatching(true)
    setError(null)

    try {
      const res = await fetch('/api/match', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ resources: parsedData.data }),
      })

      const data = await res.json()

      if (!res.ok) {
        throw new Error(data.error || '匹配失败')
      }

      setMatchResult(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : '匹配失败')
    } finally {
      setMatching(false)
    }
  }

  const handleReset = () => {
    setParsedData(null)
    setMatchResult(null)
    setError(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const filteredMatches = matchResult?.matches.filter(match => {
    const matchesSearch = searchTerm === '' ||
      match.brand_name.includes(searchTerm) ||
      match.signal_title.includes(searchTerm) ||
      match.resource_name.includes(searchTerm)
    const matchesLocation = locationFilter === 'all' ||
      match.resource_location === locationFilter
    return matchesSearch && matchesLocation
  }) || []

  const locations = matchResult
    ? [...new Set(matchResult.matches.map(m => m.resource_location))]
    : []

  return (
    <div className="flex min-h-screen">
      <div className="flex-1 p-6">
        <div className="max-w-7xl mx-auto">
          {/* 标题 */}
          <div className="mb-6">
            <h1 className="text-2xl font-bold">🎯 资源匹配</h1>
            <p className="text-sm text-[var(--text-secondary)] mt-1">
              上传广告资源文件，自动匹配高分品牌信号
            </p>
          </div>

          {/* 错误提示 */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
              <p className="text-red-800">{error}</p>
            </div>
          )}

          {/* 上传区域 */}
          <div className="bg-[var(--card)] border border-[var(--border)] rounded-lg p-6 mb-6">
            <h2 className="text-lg font-semibold mb-4">📁 上传资源文件</h2>

            {!parsedData ? (
              <div className="border-2 border-dashed border-[var(--border)] rounded-lg p-8 text-center">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".xlsx,.xls,.csv,.txt,.text,.docx,.doc,.pdf"
                  onChange={handleFileUpload}
                  className="hidden"
                  id="file-upload"
                />
                <label
                  htmlFor="file-upload"
                  className="cursor-pointer inline-flex items-center gap-2 px-4 py-2 bg-[var(--accent)] text-white rounded-lg hover:opacity-90 transition"
                >
                  {uploading ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      解析中...
                    </>
                  ) : (
                    <>
                      📎 选择文件
                    </>
                  )}
                </label>
                <p className="text-sm text-[var(--text-secondary)] mt-3">
                  支持 Excel、CSV、TXT、Word、PDF 格式
                </p>
                <p className="text-xs text-[var(--text-secondary)] mt-1">
                  文件应包含：名称、类型、位置、行业、受众、价格等列
                </p>
              </div>
            ) : (
              <div>
                {/* 文件信息 */}
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <p className="font-medium">📄 {parsedData.filename}</p>
                    <p className="text-sm text-[var(--text-secondary)]">
                      {parsedData.rows} 条资源 | 列：{parsedData.columns.join('、')}
                    </p>
                  </div>
                  <button
                    onClick={handleReset}
                    className="px-3 py-1 text-sm border border-[var(--border)] rounded hover:bg-[var(--border)] transition"
                  >
                    重新上传
                  </button>
                </div>

                {/* 数据预览 */}
                <div className="overflow-x-auto mb-4">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-[var(--border)]">
                        {parsedData.columns.slice(0, 6).map(col => (
                          <th key={col} className="text-left p-2 font-medium">
                            {col}
                          </th>
                        ))}
                        {parsedData.columns.length > 6 && (
                          <th className="text-left p-2 font-medium text-[var(--text-secondary)]">
                            ...+{parsedData.columns.length - 6}列
                          </th>
                        )}
                      </tr>
                    </thead>
                    <tbody>
                      {parsedData.data.slice(0, 5).map((row, i) => (
                        <tr key={i} className="border-b border-[var(--border)]">
                          {parsedData.columns.slice(0, 6).map(col => (
                            <td key={col} className="p-2 text-[var(--text-secondary)]">
                              {String(row[col] || '-')}
                            </td>
                          ))}
                          {parsedData.columns.length > 6 && (
                            <td className="p-2 text-[var(--text-secondary)]">...</td>
                          )}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {parsedData.rows > 5 && (
                    <p className="text-xs text-[var(--text-secondary)] mt-2">
                      显示前 5 条，共 {parsedData.rows} 条
                    </p>
                  )}
                </div>

                {/* 匹配按钮 */}
                <button
                  onClick={handleMatch}
                  disabled={matching}
                  className="w-full px-4 py-3 bg-[var(--accent)] text-white rounded-lg hover:opacity-90 transition disabled:opacity-50 font-medium"
                >
                  {matching ? (
                    <span className="flex items-center justify-center gap-2">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      匹配中...
                    </span>
                  ) : (
                    '🔍 开始匹配品牌信号'
                  )}
                </button>
              </div>
            )}
          </div>

          {/* 匹配结果 */}
          {matchResult && (
            <div>
              {/* 结果统计 */}
              <div className="bg-[var(--card)] border border-[var(--border)] rounded-lg p-4 mb-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-lg font-semibold">📊 匹配结果</h2>
                    <p className="text-sm text-[var(--text-secondary)]">
                      {matchResult.total_resources} 个资源 × {matchResult.total_signals} 个高分信号
                      = {matchResult.total_matches} 个匹配
                    </p>
                  </div>
                  <p className="text-xs text-[var(--text-secondary)]">
                    {new Date(matchResult.generated_at).toLocaleString('zh-CN')}
                  </p>
                </div>
              </div>

              {/* 筛选器 */}
              <div className="bg-[var(--card)] border border-[var(--border)] rounded-lg p-4 mb-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">搜索</label>
                    <input
                      type="text"
                      placeholder="搜索品牌、信号或资源..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="w-full px-3 py-2 border border-[var(--border)] rounded-md bg-[var(--background)]"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">地区</label>
                    <select
                      value={locationFilter}
                      onChange={(e) => setLocationFilter(e.target.value)}
                      className="w-full px-3 py-2 border border-[var(--border)] rounded-md bg-[var(--background)]"
                    >
                      <option value="all">全部地区</option>
                      {locations.map(loc => (
                        <option key={loc} value={loc}>{loc}</option>
                      ))}
                    </select>
                  </div>
                  <div className="flex items-end">
                    <p className="text-sm text-[var(--text-secondary)]">
                      显示 {filteredMatches.length} / {matchResult.total_matches} 个匹配
                    </p>
                  </div>
                </div>
              </div>

              {/* 匹配列表 */}
              <div className="space-y-4">
                {filteredMatches.map((match, index) => (
                  <div
                    key={`${match.signal_id}-${match.resource_name}-${index}`}
                    className="bg-[var(--card)] border border-[var(--border)] rounded-lg p-6 hover:border-[var(--accent)]/30 transition"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <span className="text-2xl font-bold text-[var(--text-secondary)]">
                            #{index + 1}
                          </span>
                          <h3 className="text-lg font-semibold">
                            {match.brand_name} × {match.resource_name}
                          </h3>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                          <div>
                            <p className="text-sm text-[var(--text-secondary)] mb-1">品牌信号</p>
                            <p>{match.signal_title}</p>
                            <div className="flex items-center gap-2 mt-1">
                              <span className={`px-2 py-1 rounded text-xs font-medium ${
                                match.signal_score >= 90 ? 'bg-red-100 text-red-800' :
                                match.signal_score >= 80 ? 'bg-orange-100 text-orange-800' :
                                'bg-yellow-100 text-yellow-800'
                              }`}>
                                信号评分: {match.signal_score}
                              </span>
                            </div>
                          </div>

                          <div>
                            <p className="text-sm text-[var(--text-secondary)] mb-1">广告资源</p>
                            <p>{match.resource_type} - {match.resource_location}</p>
                            {match.daily_traffic > 0 && (
                              <p className="text-sm text-[var(--text-secondary)] mt-1">
                                日均客流: {match.daily_traffic.toLocaleString()}
                              </p>
                            )}
                          </div>
                        </div>

                        <div className="bg-[var(--background)] rounded-md p-3">
                          <p className="text-sm text-[var(--text-secondary)] mb-1">匹配理由</p>
                          <p>{match.reason_text}</p>
                          <div className="flex flex-wrap gap-2 mt-2">
                            {match.reasons.map((reason, i) => (
                              <span
                                key={i}
                                className="px-2 py-1 bg-[var(--accent)]/10 text-[var(--accent)] rounded text-xs"
                              >
                                {reason}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>

                      <div className="ml-4 text-right">
                        <div className={`text-3xl font-bold ${
                          match.match_score >= 80 ? 'text-green-500' :
                          match.match_score >= 60 ? 'text-blue-500' :
                          'text-[var(--text-secondary)]'
                        }`}>
                          {match.match_score}
                        </div>
                        <p className="text-sm text-[var(--text-secondary)]">匹配分</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {filteredMatches.length === 0 && (
                <div className="text-center py-12">
                  <p className="text-[var(--text-secondary)]">没有找到匹配的结果</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
