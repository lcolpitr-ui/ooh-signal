'use client'

import { useState, useRef } from 'react'
import * as XLSX from 'xlsx'

// PDF.js 动态导入
let pdfjsLib: typeof import('pdfjs-dist') | null = null

const initPDFJS = async () => {
  if (typeof window === 'undefined') return null
  if (pdfjsLib) return pdfjsLib

  const pdfjs = await import('pdfjs-dist')
  pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`
  pdfjsLib = pdfjs
  return pdfjs
}

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
  filename: string
  rows: number
  data: Record<string, unknown>[]
  columns: string[]
}

export default function PlaygroundPage() {
  const [parsedData, setParsedData] = useState<ParsedData | null>(null)
  const [matchResult, setMatchResult] = useState<MatchResult | null>(null)
  const [parsing, setParsing] = useState(false)
  const [matching, setMatching] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [locationFilter, setLocationFilter] = useState('all')
  const fileInputRef = useRef<HTMLInputElement>(null)

  // 客户端解析文件
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setParsing(true)
    setError(null)
    setMatchResult(null)

    try {
      const data = await parseFileClient(file)
      if (!data || data.length === 0) {
        throw new Error('无法解析文件内容，请确保文件包含表格数据')
      }
      setParsedData({
        filename: file.name,
        rows: data.length,
        data,
        columns: Object.keys(data[0] || {}),
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : '文件解析失败')
    } finally {
      setParsing(false)
    }
  }

  // 客户端解析文件
  const parseFileClient = async (file: File): Promise<Record<string, unknown>[]> => {
    const ext = file.name.toLowerCase().split('.').pop()

    // PDF 文件特殊处理
    if (ext === 'pdf') {
      return parsePDFFile(file)
    }

    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = (e) => {
        try {
          const data = e.target?.result
          if (!data) {
            reject(new Error('无法读取文件'))
            return
          }

          // Excel 文件
          if (ext === 'xlsx' || ext === 'xls') {
            const workbook = XLSX.read(data, { type: 'array' })
            const firstSheet = workbook.Sheets[workbook.SheetNames[0]]
            const jsonData = XLSX.utils.sheet_to_json(firstSheet)
            resolve(jsonData as Record<string, unknown>[])
            return
          }

          // CSV 文件
          if (ext === 'csv') {
            const workbook = XLSX.read(data, { type: 'string' })
            const firstSheet = workbook.Sheets[workbook.SheetNames[0]]
            const jsonData = XLSX.utils.sheet_to_json(firstSheet)
            resolve(jsonData as Record<string, unknown>[])
            return
          }

          // 文本文件
          if (ext === 'txt' || ext === 'text') {
            const text = data as string
            const jsonData = parseTextFile(text)
            resolve(jsonData)
            return
          }

          reject(new Error('不支持的文件格式，请上传 Excel、CSV、TXT 或 PDF 文件'))
        } catch (err) {
          reject(new Error('文件解析失败：' + (err instanceof Error ? err.message : '未知错误')))
        }
      }
      reader.onerror = () => reject(new Error('文件读取失败'))

      // 根据文件类型选择读取方式
      if (ext === 'xlsx' || ext === 'xls') {
        reader.readAsArrayBuffer(file)
      } else {
        reader.readAsText(file, 'utf-8')
      }
    })
  }

  // 解析 PDF 文件
  const parsePDFFile = async (file: File): Promise<Record<string, unknown>[]> => {
    const pdfjs = await initPDFJS()
    if (!pdfjs) {
      throw new Error('PDF 解析库加载失败')
    }

    const arrayBuffer = await file.arrayBuffer()
    const pdf = await pdfjs.getDocument({ data: arrayBuffer }).promise

    let fullText = ''
    for (let i = 1; i <= pdf.numPages; i++) {
      const page = await pdf.getPage(i)
      const textContent = await page.getTextContent()
      const pageText = textContent.items
        .map((item) => ('str' in item ? item.str : '') || '')
        .join(' ')
      fullText += pageText + '\n'
    }

    // 尝试从 PDF 文本中提取表格数据
    const data = parsePDFText(fullText)
    if (data.length === 0) {
      throw new Error('无法从 PDF 中提取表格数据，请确保 PDF 包含表格或结构化数据')
    }
    return data
  }

  // 解析 PDF 文本内容
  const parsePDFText = (text: string): Record<string, unknown>[] => {
    const lines = text.split('\n').filter(line => line.trim())
    if (lines.length < 2) return []

    // 尝试检测表格结构
    const separator = detectSeparator(lines)
    if (separator) {
      const headers = lines[0].split(separator).map(h => h.trim()).filter(Boolean)
      if (headers.length >= 2) {
        const rows: Record<string, unknown>[] = []
        for (let i = 1; i < lines.length; i++) {
          const values = lines[i].split(separator).map(v => v.trim())
          if (values.length >= 2) {
            const row: Record<string, unknown> = {}
            headers.forEach((header, index) => {
              row[header] = values[index] || ''
            })
            rows.push(row)
          }
        }
        if (rows.length > 0) return rows
      }
    }

    // 如果没有检测到表格，尝试提取键值对
    return extractKeyValuePairs(lines)
  }

  // 提取键值对格式的数据
  const extractKeyValuePairs = (lines: string[]): Record<string, unknown>[] => {
    const resources: Record<string, unknown>[] = []
    let current: Record<string, unknown> = {}

    for (const line of lines) {
      const trimmed = line.trim()
      if (!trimmed) continue

      // 检测新资源块（数字开头或特定标记）
      if (/^\d+[.、]/.test(trimmed) || /^[【\[]/.test(trimmed)) {
        if (Object.keys(current).length > 0) {
          resources.push(current)
        }
        current = { name: trimmed.replace(/^\d+[.、]\s*/, '').replace(/[【\]】]/g, '') }
        continue
      }

      // 解析键值对
      const kvMatch = trimmed.match(/^([^：:]+)[：:](.+)$/)
      if (kvMatch) {
        const key = kvMatch[1].trim()
        const value = kvMatch[2].trim()
        current[key] = value
      } else if (current.name) {
        current.description = (current.description || '') + trimmed
      }
    }

    if (Object.keys(current).length > 0) {
      resources.push(current)
    }

    return resources
  }

  // 解析文本文件
  const parseTextFile = (text: string): Record<string, unknown>[] => {
    const lines = text.split('\n').filter(line => line.trim())
    if (lines.length < 2) return []

    // 尝试检测分隔符
    const separator = detectSeparator(lines)
    if (!separator) return []

    const headers = lines[0].split(separator).map(h => h.trim()).filter(Boolean)
    const rows: Record<string, unknown>[] = []

    for (let i = 1; i < lines.length; i++) {
      const values = lines[i].split(separator).map(v => v.trim())
      const row: Record<string, unknown> = {}
      headers.forEach((header, index) => {
        row[header] = values[index] || ''
      })
      rows.push(row)
    }

    return rows
  }

  // 检测分隔符
  const detectSeparator = (lines: string[]): string | null => {
    if (lines.length < 2) return null

    const firstLine = lines[0]
    const tabCount = (firstLine.match(/\t/g) || []).length
    const commaCount = (firstLine.match(/,/g) || []).length
    const spaceCount = (firstLine.match(/\s{2,}/g) || []).length

    if (tabCount >= 2) return '\t'
    if (commaCount >= 2) return ','
    if (spaceCount >= 2) return '  '
    if (firstLine.includes('|') && firstLine.split('|').length >= 3) return '|'

    return null
  }

  // 执行匹配
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
            <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 mb-6">
              <p className="text-red-400">{error}</p>
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
                  accept=".xlsx,.xls,.csv,.txt,.text,.pdf"
                  onChange={handleFileUpload}
                  className="hidden"
                  id="file-upload"
                />
                <label
                  htmlFor="file-upload"
                  className="cursor-pointer inline-flex items-center gap-2 px-6 py-3 bg-[var(--accent)] text-white rounded-lg hover:opacity-90 transition"
                >
                  {parsing ? (
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
                  支持 Excel (.xlsx, .xls)、CSV、TXT、PDF 格式
                </p>
                <p className="text-xs text-[var(--text-secondary)] mt-1">
                  文件应包含：名称、类型、位置、行业、受众、价格等列
                </p>
                <p className="text-xs text-[var(--text-secondary)] mt-1">
                  大文件会在本地解析，无需上传到服务器
                </p>
              </div>
            ) : (
              <div>
                {/* 文件信息 */}
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <p className="font-medium">📄 {parsedData.filename}</p>
                    <p className="text-sm text-[var(--text-secondary)]">
                      {parsedData.rows} 条资源 | 列：{parsedData.columns.slice(0, 5).join('、')}
                      {parsedData.columns.length > 5 && `...+${parsedData.columns.length - 5}列`}
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
                <div className="overflow-x-auto mb-4 max-h-60 overflow-y-auto">
                  <table className="w-full text-sm">
                    <thead className="sticky top-0 bg-[var(--card)]">
                      <tr className="border-b border-[var(--border)]">
                        {parsedData.columns.slice(0, 8).map(col => (
                          <th key={col} className="text-left p-2 font-medium whitespace-nowrap">
                            {col}
                          </th>
                        ))}
                        {parsedData.columns.length > 8 && (
                          <th className="text-left p-2 font-medium text-[var(--text-secondary)]">
                            ...+{parsedData.columns.length - 8}列
                          </th>
                        )}
                      </tr>
                    </thead>
                    <tbody>
                      {parsedData.data.slice(0, 10).map((row, i) => (
                        <tr key={i} className="border-b border-[var(--border)]">
                          {parsedData.columns.slice(0, 8).map(col => (
                            <td key={col} className="p-2 text-[var(--text-secondary)] whitespace-nowrap max-w-[200px] truncate">
                              {String(row[col] || '-')}
                            </td>
                          ))}
                          {parsedData.columns.length > 8 && (
                            <td className="p-2 text-[var(--text-secondary)]">...</td>
                          )}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {parsedData.rows > 10 && (
                    <p className="text-xs text-[var(--text-secondary)] mt-2">
                      显示前 10 条，共 {parsedData.rows} 条
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
                                match.signal_score >= 90 ? 'bg-red-500/20 text-red-400' :
                                match.signal_score >= 80 ? 'bg-orange-500/20 text-orange-400' :
                                'bg-yellow-500/20 text-yellow-400'
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
