import Sidebar from '@/components/Sidebar'

export default function SubmitPage() {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="ml-60 flex-1 p-6">
        <div className="mb-6">
          <h1 className="text-2xl font-bold">信源提报</h1>
          <p className="text-sm text-[var(--text-secondary)] mt-1">
            提交新的数据源，帮助我们发现更多投放信号
          </p>
        </div>
        <div className="bg-[var(--card)] border border-[var(--border)] rounded-lg p-6">
          <p className="text-[var(--text-secondary)]">信源提报功能开发中...</p>
        </div>
      </main>
    </div>
  )
}
