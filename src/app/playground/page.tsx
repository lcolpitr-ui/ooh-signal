'use client'

import { useState, useEffect } from 'react'

interface Match {
  signal_id: string
  signal_title: string
  brand_name: string
  signal_score: number
  resource_id: string
  resource_name: string
  resource_type: string
  resource_location: string
  match_score: number
  reasons: string[]
  reason_text: string
  recommended_budget: string
  daily_traffic: number
}

interface MatchData {
  generated_at: string
  total_matches: number
  matches: Match[]
}

export default function PlaygroundPage() {
  const [data, setData] = useState<MatchData | null>(null)
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [industryFilter, setIndustryFilter] = useState('all')
  const [locationFilter, setLocationFilter] = useState('all')

  useEffect(() => {
    fetch('/data/matches.json')
      .then(res => res.json())
      .then(data => {
        setData(data)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">加载中...</p>
        </div>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600">暂无匹配数据</p>
          <p className="text-sm text-gray-500 mt-2">请先运行资源匹配脚本</p>
        </div>
      </div>
    )
  }

  const filteredMatches = data.matches.filter(match => {
    const matchesSearch = searchTerm === '' ||
      match.brand_name.includes(searchTerm) ||
      match.signal_title.includes(searchTerm) ||
      match.resource_name.includes(searchTerm)

    const matchesLocation = locationFilter === 'all' ||
      match.resource_location === locationFilter

    return matchesSearch && matchesLocation
  })

  const locations = [...new Set(data.matches.map(m => m.resource_location))]

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">🎯 品牌-资源匹配 Playground</h1>
          <p className="mt-2 text-gray-600">
            智能匹配品牌信号与广告媒体资源 | 共 {data.total_matches} 个匹配
          </p>
          <p className="text-sm text-gray-500">
            生成时间: {new Date(data.generated_at).toLocaleString('zh-CN')}
          </p>
        </div>

        {/* 筛选器 */}
        <div className="bg-white rounded-lg shadow-sm p-4 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">搜索</label>
              <input
                type="text"
                placeholder="搜索品牌、信号或资源..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">地区</label>
              <select
                value={locationFilter}
                onChange={(e) => setLocationFilter(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">全部地区</option>
                {locations.map(loc => (
                  <option key={loc} value={loc}>{loc}</option>
                ))}
              </select>
            </div>
            <div className="flex items-end">
              <p className="text-sm text-gray-600">
                显示 {filteredMatches.length} / {data.total_matches} 个匹配
              </p>
            </div>
          </div>
        </div>

        {/* 匹配结果 */}
        <div className="space-y-4">
          {filteredMatches.map((match, index) => (
            <div key={`${match.signal_id}-${match.resource_id}-${index}`}
              className="bg-white rounded-lg shadow-sm p-6 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-2xl font-bold text-gray-400">#{index + 1}</span>
                    <h3 className="text-lg font-semibold text-gray-900">
                      {match.brand_name} × {match.resource_name}
                    </h3>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                    <div>
                      <p className="text-sm text-gray-500 mb-1">品牌信号</p>
                      <p className="text-gray-700">{match.signal_title}</p>
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
                      <p className="text-sm text-gray-500 mb-1">广告资源</p>
                      <p className="text-gray-700">{match.resource_type} - {match.resource_location}</p>
                      <p className="text-sm text-gray-500 mt-1">
                        日均客流: {match.daily_traffic.toLocaleString()}
                      </p>
                    </div>
                  </div>

                  <div className="bg-gray-50 rounded-md p-3">
                    <p className="text-sm text-gray-500 mb-1">匹配理由</p>
                    <p className="text-gray-700">{match.reason_text}</p>
                    <div className="flex flex-wrap gap-2 mt-2">
                      {match.reasons.map((reason, i) => (
                        <span key={i} className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">
                          {reason}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="ml-4 text-right">
                  <div className={`text-3xl font-bold ${
                    match.match_score >= 80 ? 'text-green-600' :
                    match.match_score >= 60 ? 'text-blue-600' :
                    'text-gray-600'
                  }`}>
                    {match.match_score}
                  </div>
                  <p className="text-sm text-gray-500">匹配分</p>
                </div>
              </div>
            </div>
          ))}
        </div>

        {filteredMatches.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-500">没有找到匹配的结果</p>
          </div>
        )}
      </div>
    </div>
  )
}
