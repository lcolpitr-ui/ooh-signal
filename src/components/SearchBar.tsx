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
        className="flex-1 bg-[var(--card)] border border-[var(--border)] rounded px-4 py-2 text-sm text-[var(--foreground)] placeholder:text-[var(--text-secondary)] focus:outline-none focus:border-[var(--accent)]"
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
