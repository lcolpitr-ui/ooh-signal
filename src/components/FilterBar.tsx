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
      <select
        value={selectedIndustry}
        onChange={(e) => onIndustryChange(e.target.value)}
        className="bg-[var(--card)] border border-[var(--border)] rounded px-3 py-1.5 text-sm text-[var(--foreground)]"
      >
        <option value="all">全部行业</option>
        {industries.map((ind) => (
          <option key={ind} value={ind}>{ind}</option>
        ))}
      </select>

      <select
        value={selectedType}
        onChange={(e) => onTypeChange(e.target.value)}
        className="bg-[var(--card)] border border-[var(--border)] rounded px-3 py-1.5 text-sm text-[var(--foreground)]"
      >
        {signalTypes.map((type) => (
          <option key={type} value={type}>{signalTypeLabels[type] || type}</option>
        ))}
      </select>
    </div>
  )
}
