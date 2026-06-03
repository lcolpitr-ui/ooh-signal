import Sidebar from '@/components/Sidebar'

export default function AboutPage() {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="ml-60 flex-1 p-6">
        <div className="mb-6">
          <h1 className="text-2xl font-bold">关于</h1>
        </div>
        <div className="bg-[var(--card)] border border-[var(--border)] rounded-lg p-6">
          <p className="text-[var(--text-secondary)]">
            OOH Signal 是一个户外广告投放信号情报系统，
            帮助从业者发现哪些品牌正在释放投放信号。
          </p>
          <p className="text-[var(--text-secondary)] mt-4">
            每天自动采集多渠道信息，用 AI 评估品牌投放可能性，
            让销售优先跟进高意向客户。
          </p>
        </div>
      </main>
    </div>
  )
}
