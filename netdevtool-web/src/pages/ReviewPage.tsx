import { ArrowRightOutlined, DownOutlined, EditOutlined } from '@ant-design/icons'
import { Checkbox } from 'antd'
import { PageHeader } from '../components/PageHeader'
import { StatusTag } from '../components/StatusTag'
import { reviewCandidates, type ReviewCandidate } from '../data/review'

function FilterPill({ children }: { children: string }) {
  return (
    <button
      type="button"
      className="flex h-[34px] items-center gap-2 rounded-md border border-line bg-white px-4 text-[13px] text-ink-500"
    >
      {children}
      <DownOutlined className="text-[10px] text-ink-400" />
    </button>
  )
}

function ReviewCard({ candidate }: { candidate: ReviewCandidate }) {
  return (
    <article
      className={`rounded-lg border bg-white p-4 md:px-5 md:py-3.5 ${
        candidate.checked ? 'border-brand-line' : 'border-line'
      }`}
    >
      <div className="flex flex-wrap items-start justify-between gap-x-4 gap-y-2">
        <div className="flex min-w-0 flex-1 items-start gap-3">
          <Checkbox defaultChecked={candidate.checked} className="mt-0.5 shrink-0" />
          <div className="flex min-w-0 flex-wrap items-center gap-x-3 gap-y-2">
            <span className="flex flex-wrap items-baseline gap-1.5">
              <span className="text-[13px] font-medium text-ink-900">{candidate.vendor}：</span>
              <span className="break-all font-mono text-[15px] leading-[23px] text-ink-900">
                {candidate.command}
              </span>
            </span>
            <StatusTag tone="blue">来源：{candidate.source}</StatusTag>
            <span className="flex items-baseline gap-1.5 text-[11px] text-ink-400">
              相似度
              <span className="font-mono text-[14px] leading-[22px] text-ink-900">
                {candidate.similarity}
              </span>
            </span>
            <StatusTag tone="warn">low 置信度</StatusTag>
          </div>
        </div>
      </div>

      <div className="mt-2.5 flex flex-col gap-2 rounded bg-soft px-4 py-2.5 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex min-w-0 flex-wrap items-center gap-2">
          <span className="text-xs text-ink-400">候选:</span>
          <StatusTag tone="blue">{candidate.candidateVendor}</StatusTag>
          <span className="break-all font-mono text-[13px] leading-[22px] text-brand">
            {candidate.candidateCommand}
          </span>
        </div>
        <span className="shrink-0 text-xs text-ink-400">视图：{candidate.view}</span>
      </div>

      <p className="mt-2.5 text-xs text-ink-500">理由：{candidate.reason}</p>

      <div className="mt-3 flex flex-wrap items-center gap-2.5">
        <button
          type="button"
          className="flex h-[30px] items-center rounded-md bg-brand px-4 text-xs font-medium text-white"
        >
          通过
        </button>
        <button
          type="button"
          className="flex h-[30px] items-center gap-1.5 rounded-md border border-line bg-white px-4 text-xs text-ink-700"
        >
          <EditOutlined className="text-[12px]" />
          编辑后通过
        </button>
        <button
          type="button"
          className="flex h-[30px] items-center gap-1.5 rounded-md border border-danger-line bg-white px-4 text-xs text-danger"
        >
          <span className="text-[13px] leading-none">×</span>
          拒绝
        </button>
        <span className="text-[10px] text-ink-400">
          {candidate.category} · {candidate.revision}
        </span>
        <button
          type="button"
          className="ml-auto flex items-center gap-1 text-[11px] text-brand-strong"
        >
          查看源手册
          <span className="text-[10px]">↗</span>
        </button>
      </div>
    </article>
  )
}

function Pagination() {
  return (
    <div className="flex items-center gap-1">
      <span className="flex h-8 w-8 items-center justify-center rounded-md border border-line bg-white text-[13px] text-ink-500">
        ‹
      </span>
      <span className="flex h-8 w-8 items-center justify-center rounded-md bg-brand text-[13px] font-medium text-white">
        1
      </span>
      <span className="flex h-8 w-8 items-center justify-center rounded-md border border-line bg-white text-[13px] text-ink-900">
        2
      </span>
      <span className="flex h-8 w-8 items-center justify-center rounded-md border border-line bg-white text-[13px] text-ink-900">
        3
      </span>
      <span className="flex h-8 w-8 items-center justify-center rounded-md border border-line bg-white text-[13px] text-ink-500">
        ›
      </span>
    </div>
  )
}

export function ReviewPage() {
  return (
    <div className="flex min-h-full flex-col">
      <PageHeader
        title="命令审核"
        subtitle="网络设备知识助手"
        right={
          <>
            <span className="hidden text-xs text-ink-400 lg:inline">
              人工确认后同步至命令知识库
            </span>
            <button
              type="button"
              className="flex h-[34px] items-center rounded-md border border-line bg-white px-4 text-[13px] text-ink-500"
            >
              审核记录
            </button>
          </>
        }
      />

      <div className="flex flex-1 flex-col gap-4 px-4 pb-4 pt-5 md:px-7 md:pt-[22px]">
        <section className="flex flex-wrap items-end gap-x-4 gap-y-2">
          <div className="flex items-baseline gap-2.5">
            <span className="text-[14px] font-medium leading-5 text-ink-900">待审核</span>
            <span className="text-[24px] font-bold leading-[30px] text-brand">37</span>
          </div>
          <span className="mx-2 hidden h-6 w-px bg-line sm:block" />
          <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
            <span className="text-[12px] text-ink-500">今日已审</span>
            <span className="text-[18px] font-medium leading-[24px] text-ink-900">12</span>
            <span className="text-[11px] text-ink-400">通过 10 · 拒绝 2</span>
          </div>
          <span className="ml-auto hidden text-xs text-ink-400 xl:inline">
            审核候选命令，持续完善跨厂商映射
          </span>
        </section>

        <section className="flex flex-col gap-3 rounded-lg border border-line bg-white px-4 py-2.5 xl:h-[54px] xl:flex-row xl:items-center">
          <span className="text-[13px] text-ink-500">筛选</span>
          <div className="flex flex-wrap items-center gap-3">
            <FilterPill>来源：LLM</FilterPill>
            <FilterPill>置信度：low</FilterPill>
            <FilterPill>厂商：全部</FilterPill>
            <button type="button" className="px-1 text-xs text-brand">
              重置
            </button>
          </div>
          <span className="text-xs text-ink-400 xl:ml-auto">已筛选 8 条</span>
        </section>

        <section className="flex flex-wrap items-center gap-x-3 gap-y-1.5">
          <Checkbox defaultChecked />
          <span className="text-xs text-ink-500">全选当前页</span>
          <span className="text-xs text-brand">已选 2 项</span>
          <span className="ml-auto hidden text-xs text-ink-400 xl:inline">
            相似度仅供参考，请结合源手册审核
          </span>
          <span className="text-xs text-ink-400">
            按提交时间排序 <span className="text-[11px]">↓</span>
          </span>
        </section>

        <section className="flex flex-col gap-2.5">
          {reviewCandidates.map((candidate) => (
            <ReviewCard key={candidate.id} candidate={candidate} />
          ))}
        </section>

        <section className="flex flex-col gap-3 rounded-lg border border-line bg-white px-4 py-3 xl:h-[66px] xl:flex-row xl:items-center">
          <div className="flex items-center gap-3">
            <Checkbox defaultChecked />
            <span className="text-[13px] text-ink-900">已选 2 项</span>
            <span className="text-xs text-ink-400">通过后将写入命令知识库</span>
          </div>

          <div className="flex flex-1 flex-wrap items-center justify-between gap-3 xl:justify-center">
            <span className="text-xs text-ink-400">1–3 / 8 条</span>
            <div className="hidden sm:block">
              <Pagination />
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2.5">
            <button
              type="button"
              className="flex h-8 items-center rounded-md border border-line bg-white px-4 text-[13px] text-ink-900"
            >
              取消选择
            </button>
            <button
              type="button"
              className="flex h-8 items-center gap-1.5 rounded-md bg-brand px-4 text-[13px] font-medium text-white"
            >
              批量通过选中项
              <ArrowRightOutlined className="text-[11px]" />
            </button>
          </div>
        </section>

        <footer className="flex flex-col gap-1 text-[10px] text-ink-400 sm:flex-row sm:items-center sm:justify-between">
          <span>审核记录可追溯，所有操作将保留审计日志</span>
          <span>网络设备知识助手 · 命令映射审核</span>
        </footer>
      </div>
    </div>
  )
}
