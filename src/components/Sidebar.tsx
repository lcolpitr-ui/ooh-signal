'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'

const navItems = [
  { href: '/', label: '精选', icon: '⚡' },
  { href: '/all', label: '全部动态', icon: '📋' },
  { href: '/playground', label: '资源匹配', icon: '🎯' },
  { href: '/daily', label: '每日日报', icon: '📰' },
  { href: '/submit', label: '信源提报', icon: '➕' },
  { href: '/about', label: '关于', icon: 'ℹ️' },
]

export default function Sidebar() {
  const pathname = usePathname()

  return (
    <aside className="fixed left-0 top-0 h-full w-60 bg-[var(--card)] border-r border-[var(--border)]">
      <div className="p-4">
        <Link href="/" className="text-xl font-bold">
          <span className="text-[var(--accent)]">OOH</span>
          <span className="text-[var(--foreground)]">Signal</span>
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
                : 'text-[var(--text-secondary)] hover:text-[var(--foreground)]'
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
