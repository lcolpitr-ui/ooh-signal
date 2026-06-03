# OOH Signal 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个户外广告投放信号情报系统，类 AIHOT 的网页展示，AI 自动打分排序

**Architecture:** Next.js 前端 + Python 数据采集脚本 + LLM AI 打分 + SQLite 存储 + GitHub Actions 定时任务

**Tech Stack:** Next.js 14 (App Router), Tailwind CSS, Python 3.11+, SQLite, Gemini Flash API, GitHub Actions

---

## 文件结构

```
信息采集器/
├── src/
│   ├── app/
│   │   ├── layout.tsx              # 根布局（暗色主题）
│   │   ├── page.tsx                # 首页（精选信号）
│   │   ├── all/
│   │   │   └── page.tsx            # 全部动态页
│   │   ├── brand/
│   │   │   └── page.tsx            # 品牌库页
│   │   ├── daily/
│   │   │   └── page.tsx            # 每日日报页
│   │   ├── submit/
│   │   │   └── page.tsx            # 信源提报页
│   │   ├── about/
│   │   │   └── page.tsx            # 关于页
│   │   └── api/
│   │       ├── signals/
│   │       │   └── route.ts        # 信号 API
│   │       ├── brands/
│   │       │   └── route.ts        # 品牌 API
│   │       ├── feed/
│   │       │   └── route.ts        # RSS Feed
│   │       └── img-proxy/
│   │           └── route.ts        # 图片代理
│   ├── components/
│   │   ├── SignalCard.tsx           # 信号卡片组件
│   │   ├── SignalList.tsx           # 信号列表组件
│   │   ├── FilterBar.tsx           # 筛选栏组件
│   │   ├── SearchBar.tsx           # 搜索栏组件
│   │   ├── BrandCard.tsx           # 品牌卡片组件
│   │   ├── ScoreBadge.tsx          # 评分徽章组件
│   │   ├── Sidebar.tsx             # 侧边栏导航
│   │   └── Header.tsx              # 页头组件
│   ├── lib/
│   │   ├── db.ts                   # SQLite 数据库连接
│   │   ├── types.ts                # TypeScript 类型定义
│   │   └── constants.ts            # 常量定义
│   └── styles/
│       └── globals.css             # 全局样式
├── scripts/
│   ├── collectors/
│   │   ├── rss_collector.py        # RSS 采集器
│   │   ├── web_scraper.py          # 网页爬虫
│   │   ├── weibo_scraper.py        # 微博爬虫
│   │   ├── xiaohongshu_scraper.py  # 小红书爬虫
│   │   ├── douyin_scraper.py       # 抖音爬虫
│   │   ├── wechat_scraper.py       # 微信公众号爬虫
│   │   └── business_scraper.py     # 企业工商信息爬虫
│   ├── processors/
│   │   ├── signal_processor.py     # 信号处理（去重、分类）
│   │   └── ai_scorer.py            # AI 打分引擎
│   ├── config/
│   │   └── sources.json            # 数据源配置
│   ├── collect.py                  # 主采集入口
│   └── requirements.txt            # Python 依赖
├── data/
│   └── ooh_signal.db               # SQLite 数据库
├── public/
│   ├── icon.png
│   └── favicon.ico
├── .github/
│   └── workflows/
│       ├── collect.yml             # 数据采集定时任务
│       └── deploy.yml              # 部署工作流
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── next.config.js
└── docs/
    ├── superpowers/
    │   ├── specs/
    │   │   └── 2026-06-03-ooh-signal-design.md
    │   └── plans/
    │       └── 2026-06-03-ooh-signal.md
    └── README.md
```

---

## Phase 1: 项目初始化与基础架构

### Task 1: 初始化 Next.js 项目

**Files:**
- Create: `package.json`
- Create: `tsconfig.json`
- Create: `next.config.js`
- Create: `tailwind.config.ts`
- Create: `src/styles/globals.css`

- [ ] **Step 1: 创建 Next.js 项目**

```bash
npx create-next-app@latest . --typescript --tailwind --app --src-dir --no-eslint --import-alias "@/*"
```

- [ ] **Step 2: 配置暗色主题**

修改 `tailwind.config.ts`，添加暗色主题支持：

```typescript
import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: '#6366f1',
        surface: '#0a0a0f',
        card: '#12121a',
        border: '#1e1e2e',
      },
    },
  },
  plugins: [],
}
export default config
```

- [ ] **Step 3: 编写全局样式**

修改 `src/styles/globals.css`：

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --bg-primary: #060814;
  --bg-card: #0f1117;
  --text-primary: #e4e4e7;
  --text-secondary: #a1a1aa;
  --border: #1e1e2e;
  --accent: #6366f1;
}

body {
  background-color: var(--bg-primary);
  color: var(--text-primary);
}

/* 评分徽章颜色 */
.score-high { color: #22c55e; }    /* 80+ 绿色 */
.score-medium { color: #eab308; }  /* 60-80 黄色 */
.score-low { color: #6b7280; }     /* 60 以下灰色 */
```

- [ ] **Step 4: 验证项目启动**

```bash
npm run dev
# 访问 http://localhost:3000 确认页面正常
```

- [ ] **Step 5: 首次提交**

```bash
git init && git add . && git commit -m "chore: initialize Next.js project with dark theme"
```

---

### Task 2: 数据库设计与初始化

**Files:**
- Create: `src/lib/db.ts`
- Create: `src/lib/types.ts`
- Create: `scripts/init_db.py`

- [ ] **Step 1: 定义 TypeScript 类型**

创建 `src/lib/types.ts`：

```typescript
export interface Signal {
  id: string
  brandName: string
  industry: string
  signalType: 'expansion' | 'funding' | 'product' | 'competitor' | 'policy' | 'industry'
  title: string
  summary: string
  sourceUrl: string
  sourceName: string
  score: number
  reason: string
  publishedAt: string
  collectedAt: string
  tags: string[]
}

export interface Brand {
  id: string
  name: string
  industry: string
  scale: 'large' | 'medium' | 'small'
  isListed: boolean
  signalCount: number
  latestScore: number
  website: string
}

export type SignalType = Signal['signalType']
export type Industry = string
```

- [ ] **Step 2: 创建 Python 数据库初始化脚本**

创建 `scripts/init_db.py`：

```python
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'ooh_signal.db')

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 信号表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS signals (
        id TEXT PRIMARY KEY,
        brand_name TEXT NOT NULL,
        industry TEXT,
        signal_type TEXT NOT NULL,
        title TEXT,
        summary TEXT,
        source_url TEXT,
        source_name TEXT,
        score INTEGER DEFAULT 0,
        reason TEXT,
        published_at TEXT,
        collected_at TEXT DEFAULT CURRENT_TIMESTAMP,
        tags TEXT DEFAULT '[]'
    )
    ''')

    # 品牌表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS brands (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        industry TEXT,
        scale TEXT DEFAULT 'small',
        is_listed INTEGER DEFAULT 0,
        signal_count INTEGER DEFAULT 0,
        latest_score INTEGER DEFAULT 0,
        website TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # 数据源配置表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sources (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        url TEXT,
        source_type TEXT,
        is_active INTEGER DEFAULT 1,
        last_collected_at TEXT
    )
    ''')

    # 索引
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_signals_score ON signals(score DESC)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_signals_collected ON signals(collected_at DESC)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_signals_brand ON signals(brand_name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_signals_type ON signals(signal_type)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_signals_industry ON signals(industry)')

    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")

if __name__ == '__main__':
    init_db()
```

- [ ] **Step 3: 创建 Next.js 数据库工具**

创建 `src/lib/db.ts`：

```typescript
import Database from 'better-sqlite3'
import path from 'path'
import { Signal, Brand } from './types'

const DB_PATH = path.join(process.cwd(), 'data', 'ooh_signal.db')

let db: Database.Database | null = null

export function getDb(): Database.Database {
  if (!db) {
    db = new Database(DB_PATH, { readonly: true })
  }
  return db
}

export function getSignals(options: {
  limit?: number
  offset?: number
  industry?: string
  signalType?: string
  minScore?: number
  search?: string
} = {}): Signal[] {
  const db = getDb()
  let query = 'SELECT * FROM signals WHERE 1=1'
  const params: any[] = []

  if (options.industry) {
    query += ' AND industry = ?'
    params.push(options.industry)
  }
  if (options.signalType) {
    query += ' AND signal_type = ?'
    params.push(options.signalType)
  }
  if (options.minScore) {
    query += ' AND score >= ?'
    params.push(options.minScore)
  }
  if (options.search) {
    query += ' AND (brand_name LIKE ? OR title LIKE ? OR summary LIKE ?)'
    const term = `%${options.search}%`
    params.push(term, term, term)
  }

  query += ' ORDER BY collected_at DESC LIMIT ? OFFSET ?'
  params.push(options.limit || 50, options.offset || 0)

  return db.prepare(query).all(...params) as Signal[]
}

export function getBrands(options: {
  industry?: string
  limit?: number
} = {}): Brand[] {
  const db = getDb()
  let query = 'SELECT * FROM brands WHERE 1=1'
  const params: any[] = []

  if (options.industry) {
    query += ' AND industry = ?'
    params.push(options.industry)
  }

  query += ' ORDER BY latest_score DESC LIMIT ?'
  params.push(options.limit || 100)

  return db.prepare(query).all(...params) as Brand[]
}
```

- [ ] **Step 4: 安装 better-sqlite3**

```bash
npm install better-sqlite3
npm install -D @types/better-sqlite3
```

- [ ] **Step 5: 运行数据库初始化**

```bash
python scripts/init_db.py
```

- [ ] **Step 6: 提交**

```bash
git add . && git commit -m "feat: add database schema and types"
```

---

### Task 3: 构建基础 UI 组件

**Files:**
- Create: `src/components/Sidebar.tsx`
- Create: `src/components/Header.tsx`
- Create: `src/components/ScoreBadge.tsx`
- Create: `src/components/SignalCard.tsx`
- Create: `src/components/FilterBar.tsx`
- Create: `src/components/SearchBar.tsx`

- [ ] **Step 1: 创建侧边栏导航**

创建 `src/components/Sidebar.tsx`：

```typescript
'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'

const navItems = [
  { href: '/', label: '精选', icon: '⚡' },
  { href: '/all', label: '全部动态', icon: '📋' },
  { href: '/brand', label: '品牌库', icon: '🏢' },
  { href: '/daily', label: '每日日报', icon: '📰' },
  { href: '/submit', label: '信源提报', icon: '➕' },
  { href: '/about', label: '关于', icon: 'ℹ️' },
]

export default function Sidebar() {
  const pathname = usePathname()

  return (
    <aside className="fixed left-0 top-0 h-full w-60 bg-[var(--bg-card)] border-r border-[var(--border)]">
      <div className="p-4">
        <Link href="/" className="text-xl font-bold">
          <span className="text-[var(--accent)]">OOH</span>
          <span className="text-[var(--text-primary)]">Signal</span>
        </Link>
      </div>
      <nav className="mt-4">
        {navItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={`flex items-center gap-3 px-4 py-3 text-sm transition-colors ${
              pathname === item.href
                ? 'bg-[var(--accent)]/10 text-[var(--accent)]'
                : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
            }`}
          >
            <span>{item.icon}</span>
            <span>{item.label}</span>
          </Link>
        ))}
      </nav>
    </aside>
  )
}
```

- [ ] **Step 2: 创建评分徽章组件**

创建 `src/components/ScoreBadge.tsx`：

```typescript
interface ScoreBadgeProps {
  score: number
}

export default function ScoreBadge({ score }: ScoreBadgeProps) {
  const colorClass =
    score >= 80 ? 'score-high' :
    score >= 60 ? 'score-medium' :
    'score-low'

  return (
    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-bold ${colorClass} bg-white/5`}>
      {score}
    </span>
  )
}
```

- [ ] **Step 3: 创建信号卡片组件**

创建 `src/components/SignalCard.tsx`：

```typescript
import ScoreBadge from './ScoreBadge'
import { Signal } from '@/lib/types'

const signalTypeLabels: Record<string, string> = {
  expansion: '扩张',
  funding: '融资',
  product: '产品',
  competitor: '竞品',
  policy: '政策',
  industry: '行业',
}

const signalTypeColors: Record<string, string> = {
  expansion: 'bg-green-500/10 text-green-400',
  funding: 'bg-yellow-500/10 text-yellow-400',
  product: 'bg-blue-500/10 text-blue-400',
  competitor: 'bg-purple-500/10 text-purple-400',
  policy: 'bg-red-500/10 text-red-400',
  industry: 'bg-gray-500/10 text-gray-400',
}

export default function SignalCard({ signal }: { signal: Signal }) {
  return (
    <article className="bg-[var(--bg-card)] border border-[var(--border)] rounded-lg p-4 hover:border-[var(--accent)]/30 transition-colors">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2">
            <span className="font-medium text-[var(--text-primary)]">{signal.brandName}</span>
            <span className={`px-2 py-0.5 rounded text-xs ${signalTypeColors[signal.signalType]}`}>
              {signalTypeLabels[signal.signalType]}
            </span>
            {signal.industry && (
              <span className="px-2 py-0.5 rounded text-xs bg-white/5 text-[var(--text-secondary)]">
                {signal.industry}
              </span>
            )}
          </div>
          <h3 className="text-sm font-medium mb-1">{signal.title}</h3>
          <p className="text-sm text-[var(--text-secondary)] line-clamp-2">{signal.summary}</p>
          <p className="text-xs text-[var(--accent)] mt-2 italic">{signal.reason}</p>
        </div>
        <ScoreBadge score={signal.score} />
      </div>
      <div className="flex items-center gap-4 mt-3 text-xs text-[var(--text-secondary)]">
        <span>{signal.sourceName}</span>
        <span>{new Date(signal.publishedAt).toLocaleDateString('zh-CN')}</span>
        <a href={signal.sourceUrl} target="_blank" rel="noopener noreferrer" className="hover:text-[var(--accent)]">
          查看原文 →
        </a>
      </div>
    </article>
  )
}
```

- [ ] **Step 4: 创建筛选栏组件**

创建 `src/components/FilterBar.tsx`：

```typescript
'use client'

interface FilterBarProps {
  industries: string[]
  signalTypes: string[]
  selectedIndustry: string
  selectedType: string
  onIndustryChange: (industry: string) => void
  onTypeChange: (type: string) => void
}

const signalTypeLabels: Record<string, string> = {
  all: '全部类型',
  expansion: '扩张',
  funding: '融资',
  product: '产品',
  competitor: '竞品',
  policy: '政策',
  industry: '行业',
}

export default function FilterBar({
  industries,
  signalTypes,
  selectedIndustry,
  selectedType,
  onIndustryChange,
  onTypeChange,
}: FilterBarProps) {
  return (
    <div className="flex flex-wrap gap-2 mb-4">
      {/* 行业筛选 */}
      <select
        value={selectedIndustry}
        onChange={(e) => onIndustryChange(e.target.value)}
        className="bg-[var(--bg-card)] border border-[var(--border)] rounded px-3 py-1.5 text-sm text-[var(--text-primary)]"
      >
        <option value="all">全部行业</option>
        {industries.map((ind) => (
          <option key={ind} value={ind}>{ind}</option>
        ))}
      </select>

      {/* 信号类型筛选 */}
      <select
        value={selectedType}
        onChange={(e) => onTypeChange(e.target.value)}
        className="bg-[var(--bg-card)] border border-[var(--border)] rounded px-3 py-1.5 text-sm text-[var(--text-primary)]"
      >
        {signalTypes.map((type) => (
          <option key={type} value={type}>{signalTypeLabels[type] || type}</option>
        ))}
      </select>
    </div>
  )
}
```

- [ ] **Step 5: 创建搜索栏组件**

创建 `src/components/SearchBar.tsx`：

```typescript
'use client'

import { useState } from 'react'

interface SearchBarProps {
  onSearch: (query: string) => void
}

export default function SearchBar({ onSearch }: SearchBarProps) {
  const [query, setQuery] = useState('')

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault()
        onSearch(query)
      }}
      className="flex gap-2"
    >
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="搜索品牌/关键词..."
        className="flex-1 bg-[var(--bg-card)] border border-[var(--border)] rounded px-4 py-2 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-secondary)] focus:outline-none focus:border-[var(--accent)]"
      />
      <button
        type="submit"
        className="bg-[var(--accent)] text-white px-4 py-2 rounded text-sm hover:bg-[var(--accent)]/80 transition-colors"
      >
        搜索
      </button>
    </form>
  )
}
```

- [ ] **Step 6: 提交**

```bash
git add . && git commit -m "feat: add base UI components"
```

---

## Phase 2: 前端页面

### Task 4: 首页（精选信号）

**Files:**
- Modify: `src/app/layout.tsx`
- Create: `src/app/page.tsx`
- Create: `src/components/SignalList.tsx`

- [ ] **Step 1: 修改根布局**

修改 `src/app/layout.tsx`：

```typescript
import type { Metadata } from 'next'
import Sidebar from '@/components/Sidebar'
import './globals.css'

export const metadata: Metadata = {
  title: 'OOH Signal — 户外广告投放信号情报',
  description: '发现哪些品牌正在释放户外广告投放信号，AI 自动打分排序',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-CN" className="dark">
      <body className="bg-[var(--bg-primary)] text-[var(--text-primary)]">
        <Sidebar />
        <main className="ml-60 min-h-screen p-6">
          {children}
        </main>
      </body>
    </html>
  )
}
```

- [ ] **Step 2: 创建信号列表组件**

创建 `src/components/SignalList.tsx`：

```typescript
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
```

- [ ] **Step 3: 创建首页**

创建 `src/app/page.tsx`：

```typescript
import SignalList from '@/components/SignalList'

export default function HomePage() {
  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold">精选</h1>
        <p className="text-sm text-[var(--text-secondary)] mt-1">
          AI 自动筛选的高分投放信号
        </p>
      </div>
      <SignalList featured />
    </div>
  )
}
```

- [ ] **Step 4: 创建信号 API**

创建 `src/app/api/signals/route.ts`：

```typescript
import { NextRequest, NextResponse } from 'next/server'
import { getSignals } from '@/lib/db'

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams

  const signals = getSignals({
    limit: parseInt(searchParams.get('limit') || '50'),
    offset: parseInt(searchParams.get('offset') || '0'),
    industry: searchParams.get('industry') || undefined,
    signalType: searchParams.get('signalType') || undefined,
    minScore: searchParams.get('minScore') ? parseInt(searchParams.get('minScore')!) : undefined,
    search: searchParams.get('search') || undefined,
  })

  return NextResponse.json({ signals })
}
```

- [ ] **Step 5: 验证页面**

```bash
npm run dev
# 访问 http://localhost:3000 确认页面正常（此时无数据，应显示"暂无信号数据"）
```

- [ ] **Step 6: 提交**

```bash
git add . && git commit -m "feat: add homepage with signal list and API"
```

---

### Task 5: 其他页面

**Files:**
- Create: `src/app/all/page.tsx`
- Create: `src/app/brand/page.tsx`
- Create: `src/app/daily/page.tsx`
- Create: `src/app/submit/page.tsx`
- Create: `src/app/about/page.tsx`
- Create: `src/app/api/brands/route.ts`

- [ ] **Step 1: 创建全部动态页**

创建 `src/app/all/page.tsx`：

```typescript
import SignalList from '@/components/SignalList'

export default function AllPage() {
  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold">全部动态</h1>
        <p className="text-sm text-[var(--text-secondary)] mt-1">
          所有采集到的投放信号
        </p>
      </div>
      <SignalList />
    </div>
  )
}
```

- [ ] **Step 2: 创建品牌库页**

创建 `src/app/brand/page.tsx`：

```typescript
'use client'

import { useState, useEffect } from 'react'
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
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold">品牌库</h1>
        <p className="text-sm text-[var(--text-secondary)] mt-1">
          按行业分组的品牌列表，含投放可能性评分
        </p>
      </div>
      <select
        value={industry}
        onChange={(e) => setIndustry(e.target.value)}
        className="bg-[var(--bg-card)] border border-[var(--border)] rounded px-3 py-1.5 text-sm text-[var(--text-primary)] mb-4"
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
    </div>
  )
}
```

- [ ] **Step 3: 创建品牌卡片组件**

创建 `src/components/BrandCard.tsx`：

```typescript
import ScoreBadge from './ScoreBadge'

interface BrandCardProps {
  brand: {
    id: string
    name: string
    industry: string
    scale: string
    isListed: boolean
    signalCount: number
    latestScore: number
  }
}

export default function BrandCard({ brand }: BrandCardProps) {
  return (
    <div className="bg-[var(--bg-card)] border border-[var(--border)] rounded-lg p-4 hover:border-[var(--accent)]/30 transition-colors">
      <div className="flex items-start justify-between">
        <div>
          <h3 className="font-medium">{brand.name}</h3>
          <div className="flex gap-2 mt-1">
            <span className="text-xs text-[var(--text-secondary)]">{brand.industry}</span>
            {brand.isListed && (
              <span className="text-xs text-blue-400">上市</span>
            )}
          </div>
        </div>
        <ScoreBadge score={brand.latestScore} />
      </div>
      <div className="mt-3 text-xs text-[var(--text-secondary)]">
        信号数量: {brand.signalCount}
      </div>
    </div>
  )
}
```

- [ ] **Step 4: 创建品牌 API**

创建 `src/app/api/brands/route.ts`：

```typescript
import { NextRequest, NextResponse } from 'next/server'
import { getBrands } from '@/lib/db'

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams

  const brands = getBrands({
    industry: searchParams.get('industry') || undefined,
    limit: parseInt(searchParams.get('limit') || '100'),
  })

  return NextResponse.json({ brands })
}
```

- [ ] **Step 5: 创建日报页**

创建 `src/app/daily/page.tsx`：

```typescript
export default function DailyPage() {
  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold">每日日报</h1>
        <p className="text-sm text-[var(--text-secondary)] mt-1">
          每日 8:00 自动生成的信号汇总
        </p>
      </div>
      <div className="text-center py-8 text-[var(--text-secondary)]">
        日报功能将在数据采集配置完成后启用
      </div>
    </div>
  )
}
```

- [ ] **Step 6: 创建信源提报页和关于页**

创建 `src/app/submit/page.tsx`：

```typescript
export default function SubmitPage() {
  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold">信源提报</h1>
        <p className="text-sm text-[var(--text-secondary)] mt-1">
          提交新的数据源，帮助我们发现更多投放信号
        </p>
      </div>
      <div className="bg-[var(--bg-card)] border border-[var(--border)] rounded-lg p-6">
        <p className="text-[var(--text-secondary)]">信源提报功能开发中...</p>
      </div>
    </div>
  )
}
```

创建 `src/app/about/page.tsx`：

```typescript
export default function AboutPage() {
  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold">关于</h1>
      </div>
      <div className="bg-[var(--bg-card)] border border-[var(--border)] rounded-lg p-6">
        <p className="text-[var(--text-secondary)]">
          OOH Signal 是一个户外广告投放信号情报系统，
          帮助从业者发现哪些品牌正在释放投放信号。
        </p>
        <p className="text-[var(--text-secondary)] mt-4">
          每天自动采集多渠道信息，用 AI 评估品牌投放可能性，
          让销售优先跟进高意向客户。
        </p>
      </div>
    </div>
  )
}
```

- [ ] **Step 7: 提交**

```bash
git add . && git commit -m "feat: add all pages (all, brand, daily, submit, about)"
```

---

## Phase 3: 数据采集

### Task 6: RSS 采集器

**Files:**
- Create: `scripts/requirements.txt`
- Create: `scripts/config/sources.json`
- Create: `scripts/collectors/rss_collector.py`
- Create: `scripts/collect.py`

- [ ] **Step 1: 创建 Python 依赖文件**

创建 `scripts/requirements.txt`：

```
feedparser>=6.0
requests>=2.31
beautifulsoup4>=4.12
lxml>=5.0
sqlite-utils>=3.36
```

- [ ] **Step 2: 创建数据源配置**

创建 `scripts/config/sources.json`：

```json
{
  "rss_sources": [
    {
      "name": "36kr",
      "url": "https://36kr.com/feed",
      "type": "industry",
      "category": "科技/创业"
    },
    {
      "name": "赢商网",
      "url": "https://www.winshang.com/rss.xml",
      "type": "expansion",
      "category": "商业地产"
    },
    {
      "name": "联商网",
      "url": "https://www.linkshop.com.cn/rss.xml",
      "type": "expansion",
      "category": "零售"
    }
  ],
  "web_sources": [
    {
      "name": "IT桔子",
      "url": "https://www.itjuzi.com/",
      "type": "funding",
      "category": "融资"
    },
    {
      "name": "巨潮资讯",
      "url": "http://www.cninfo.com.cn/",
      "type": "industry",
      "category": "上市公司公告"
    }
  ],
  "social_sources": [
    {
      "name": "微博",
      "url": "https://weibo.com/",
      "type": "industry",
      "category": "社交媒体"
    },
    {
      "name": "小红书",
      "url": "https://www.xiaohongshu.com/",
      "type": "industry",
      "category": "社交媒体"
    }
  ]
}
```

- [ ] **Step 3: 创建 RSS 采集器**

创建 `scripts/collectors/rss_collector.py`：

```python
import feedparser
import sqlite3
import json
import os
import hashlib
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'ooh_signal.db')
SOURCES_PATH = os.path.join(os.path.dirname(__file__), '..', 'config', 'sources.json')

def load_sources():
    with open(SOURCES_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_id(url, title):
    return hashlib.md5(f"{url}:{title}".encode()).hexdigest()

def collect_rss():
    sources = load_sources()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for source in sources.get('rss_sources', []):
        print(f"Collecting from {source['name']}...")
        try:
            feed = feedparser.parse(source['url'])
            for entry in feed.entries[:20]:  # 每个源最多20条
                signal_id = generate_id(entry.get('link', ''), entry.get('title', ''))

                # 检查是否已存在
                cursor.execute('SELECT id FROM signals WHERE id = ?', (signal_id,))
                if cursor.fetchone():
                    continue

                cursor.execute('''
                    INSERT INTO signals (id, brand_name, industry, signal_type, title, summary, source_url, source_name, published_at, collected_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    signal_id,
                    '待识别',  # 品牌名需要 AI 识别
                    source.get('category', ''),
                    source.get('type', 'industry'),
                    entry.get('title', ''),
                    entry.get('summary', '')[:500],
                    entry.get('link', ''),
                    source['name'],
                    entry.get('published', datetime.now().isoformat()),
                    datetime.now().isoformat()
                ))

            print(f"  Collected {len(feed.entries)} entries from {source['name']}")
        except Exception as e:
            print(f"  Error collecting from {source['name']}: {e}")

    conn.commit()
    conn.close()

if __name__ == '__main__':
    collect_rss()
```

- [ ] **Step 4: 创建主采集入口**

创建 `scripts/collect.py`：

```python
#!/usr/bin/env python3
"""主采集入口 - 运行所有采集器"""

import sys
import os

# 添加脚本目录到 path
sys.path.insert(0, os.path.dirname(__file__))

from collectors.rss_collector import collect_rss

def main():
    print("=" * 50)
    print("OOH Signal - 数据采集")
    print("=" * 50)

    print("\n[1/3] RSS 采集...")
    collect_rss()

    print("\n[2/3] 网页爬虫...")
    # TODO: 添加网页爬虫

    print("\n[3/3] 社交媒体采集...")
    # TODO: 添加社交媒体爬虫

    print("\n采集完成！")

if __name__ == '__main__':
    main()
```

- [ ] **Step 5: 测试 RSS 采集**

```bash
cd scripts
pip install -r requirements.txt
python collect.py
```

- [ ] **Step 6: 提交**

```bash
git add . && git commit -m "feat: add RSS collector and main collect script"
```

---

### Task 7: AI 打分引擎

**Files:**
- Create: `scripts/processors/ai_scorer.py`

- [ ] **Step 1: 创建 AI 打分引擎**

创建 `scripts/processors/ai_scorer.py`：

```python
import sqlite3
import os
import json
import re

DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'ooh_signal.db')

# 信号类型基础分
SIGNAL_TYPE_SCORES = {
    'funding': 80,
    'expansion': 70,
    'product': 60,
    'competitor': 55,
    'industry': 50,
    'policy': 45,
}

# 高投放行业
HIGH_SPEND_INDUSTRIES = ['快消', '汽车', '地产', '3C', '美妆', '金融']

def calculate_score(signal):
    """计算信号的投放可能性评分"""
    base_score = SIGNAL_TYPE_SCORES.get(signal['signal_type'], 50)

    # 调整因子
    adjustments = 0

    # 行业加分
    if signal.get('industry') in HIGH_SPEND_INDUSTRIES:
        adjustments += 10

    # 上市公司加分（需要额外数据，暂时跳过）
    # if signal.get('is_listed'):
    #     adjustments += 15

    # 信号来源权威性
    authoritative_sources = ['巨潮资讯', '上交所', '深交所', 'IT桔子', '36kr']
    if signal.get('source_name') in authoritative_sources:
        adjustments += 5

    return min(base_score + adjustments, 100)

def generate_reason(signal, score):
    """生成推荐理由"""
    reasons = []

    if signal['signal_type'] == 'funding':
        reasons.append(f"融资信号，品牌可能有营销预算扩张")
    elif signal['signal_type'] == 'expansion':
        reasons.append(f"扩张信号，新店/新市场需要广告曝光")
    elif signal['signal_type'] == 'product':
        reasons.append(f"产品发布，新品上市通常伴随广告投放")

    if signal.get('industry') in HIGH_SPEND_INDUSTRIES:
        reasons.append(f"{signal['industry']}行业是户外广告高投放行业")

    if score >= 80:
        reasons.append("综合评估为高优先级线索")
    elif score >= 60:
        reasons.append("综合评估为中优先级线索")

    return '；'.join(reasons) if reasons else '待分析'

def score_signals():
    """为所有未打分的信号计算评分"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 获取未打分的信号
    cursor.execute('SELECT * FROM signals WHERE score = 0 OR reason IS NULL OR reason = ""')
    signals = cursor.fetchall()

    print(f"Scoring {len(signals)} signals...")

    for signal in signals:
        signal_dict = dict(signal)
        score = calculate_score(signal_dict)
        reason = generate_reason(signal_dict, score)

        cursor.execute('''
            UPDATE signals SET score = ?, reason = ? WHERE id = ?
        ''', (score, reason, signal['id']))

    conn.commit()
    conn.close()
    print(f"Scored {len(signals)} signals")

if __name__ == '__main__':
    score_signals()
```

- [ ] **Step 2: 更新采集脚本加入打分**

修改 `scripts/collect.py`，在采集后调用打分：

```python
#!/usr/bin/env python3
"""主采集入口 - 运行所有采集器"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from collectors.rss_collector import collect_rss
from processors.ai_scorer import score_signals

def main():
    print("=" * 50)
    print("OOH Signal - 数据采集")
    print("=" * 50)

    print("\n[1/3] RSS 采集...")
    collect_rss()

    print("\n[2/3] 网页爬虫...")
    # TODO: 添加网页爬虫

    print("\n[3/3] 社交媒体采集...")
    # TODO: 添加社交媒体爬虫

    print("\n[4/4] AI 打分...")
    score_signals()

    print("\n采集完成！")

if __name__ == '__main__':
    main()
```

- [ ] **Step 3: 测试打分**

```bash
python scripts/collect.py
```

- [ ] **Step 4: 提交**

```bash
git add . && git commit -m "feat: add AI scoring engine"
```

---

## Phase 4: GitHub Actions 部署

### Task 8: 配置 GitHub Actions

**Files:**
- Create: `.github/workflows/collect.yml`
- Create: `.github/workflows/deploy.yml`

- [ ] **Step 1: 创建数据采集工作流**

创建 `.github/workflows/collect.yml`：

```yaml
name: Data Collection

on:
  schedule:
    # 每小时运行一次
    - cron: '0 * * * *'
  workflow_dispatch:

jobs:
  collect:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd scripts
          pip install -r requirements.txt

      - name: Run collection
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        run: python scripts/collect.py

      - name: Commit and push
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add data/
          git diff --staged --quiet || git commit -m "chore: update data"
          git push
```

- [ ] **Step 2: 提交**

```bash
git add . && git commit -m "ci: add GitHub Actions workflows"
```

---

## Phase 5: RSS Feed 生成

### Task 9: RSS Feed

**Files:**
- Create: `src/app/feed/route.ts`

- [ ] **Step 1: 创建 RSS Feed 路由**

创建 `src/app/feed/route.ts`：

```typescript
import { NextResponse } from 'next/server'
import { getSignals } from '@/lib/db'

export async function GET() {
  const signals = getSignals({ limit: 50, minScore: 60 })

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
```

- [ ] **Step 2: 提交**

```bash
git add . && git commit -m "feat: add RSS feed generation"
```

---

## 完成清单

- [ ] Phase 1: 项目初始化与基础架构（Task 1-3）
- [ ] Phase 2: 前端页面（Task 4-5）
- [ ] Phase 3: 数据采集（Task 6-7）
- [ ] Phase 4: GitHub Actions 部署（Task 8）
- [ ] Phase 5: RSS Feed（Task 9）
- [ ] 整体测试
- [ ] 部署到 Vercel
