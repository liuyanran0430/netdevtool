import { ArrowRightOutlined, CloseOutlined } from '@ant-design/icons'

interface ReviewBatchBarProps {
  selectedCount: number
  page: number
  totalPages: number
  rangeText: string
  onPage: (page: number) => void
  onClear: () => void
  onBatchAccept: () => void
  onBatchSkip: () => void
}

function Pagination({
  page,
  totalPages,
  onPage,
}: Pick<ReviewBatchBarProps, 'page' | 'totalPages' | 'onPage'>) {
  if (totalPages <= 1) return null
  const pages = Array.from({ length: totalPages }, (_, index) => index + 1)
  return (
    <div className="flex items-center gap-1">
      <button
        type="button"
        disabled={page === 1}
        onClick={() => onPage(page - 1)}
        className="flex h-8 w-8 items-center justify-center rounded-md border border-line bg-white text-[13px] text-ink-500 disabled:opacity-40"
      >
        ‹
      </button>
      {pages.map((item) => (
        <button
          key={item}
          type="button"
          onClick={() => onPage(item)}
          className={`flex h-8 w-8 items-center justify-center rounded-md text-[13px] ${
            item === page
              ? 'bg-brand font-medium text-white'
              : 'border border-line bg-white text-ink-900'
          }`}
        >
          {item}
        </button>
      ))}
      <button
        type="button"
        disabled={page === totalPages}
        onClick={() => onPage(page + 1)}
        className="flex h-8 w-8 items-center justify-center rounded-md border border-line bg-white text-[13px] text-ink-500 disabled:opacity-40"
      >
        ›
      </button>
    </div>
  )
}

export function ReviewBatchBar({
  selectedCount,
  page,
  totalPages,
  rangeText,
  onPage,
  onClear,
  onBatchAccept,
  onBatchSkip,
}: ReviewBatchBarProps) {
  const canBatch = selectedCount > 0
  return (
    <section className="flex flex-col gap-3 rounded-lg border border-line bg-white px-4 py-3 xl:h-[66px] xl:flex-row xl:items-center">
      <div className="flex items-center gap-3">
        <span className="text-[13px] text-ink-900">已选 {selectedCount} 项</span>
        <span className="text-xs text-ink-400">通过后将写入知识库</span>
      </div>

      <div className="flex flex-1 flex-wrap items-center justify-between gap-3 xl:justify-center">
        <span className="text-xs text-ink-400">{rangeText}</span>
        <Pagination page={page} totalPages={totalPages} onPage={onPage} />
      </div>

      <div className="flex flex-wrap items-center gap-2.5">
        <button
          type="button"
          onClick={onClear}
          disabled={!canBatch}
          className="flex h-8 items-center rounded-md border border-line bg-white px-4 text-[13px] text-ink-900 disabled:opacity-40"
        >
          取消选择
        </button>
        <button
          type="button"
          onClick={onBatchSkip}
          disabled={!canBatch}
          className="flex h-8 items-center gap-1.5 rounded-md border border-danger-line bg-white px-4 text-[13px] text-danger disabled:opacity-40"
        >
          <CloseOutlined className="text-[12px]" />
          批量拒绝
        </button>
        <button
          type="button"
          onClick={onBatchAccept}
          disabled={!canBatch}
          className="flex h-8 items-center gap-1.5 rounded-md bg-brand px-4 text-[13px] font-medium text-white disabled:opacity-40"
        >
          批量采纳
          <ArrowRightOutlined className="text-[11px]" />
        </button>
      </div>
    </section>
  )
}
