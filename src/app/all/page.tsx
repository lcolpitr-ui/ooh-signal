import Sidebar from '@/components/Sidebar'
import SignalList from '@/components/SignalList'

export default function AllPage() {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="ml-60 flex-1 p-6">
        <div className="mb-6">
          <h1 className="text-2xl font-bold">全部动态</h1>
          <p className="text-sm text-[var(--text-secondary)] mt-1">
            所有采集到的投放信号
          </p>
        </div>
        <SignalList />
      </main>
    </div>
  )
}
