import type { ReviewStatusFilter } from '../../../api/review'
import { WARNING_LABELS } from '../deriveItems'

export type StatusFilter = ReviewStatusFilter

const STATUS_OPTIONS: { value: Exclude<StatusFilter, 'all'>; label: string }[] = [
  { value: 'pending', label: '待审核' },
  { value: 'accepted', label: '已采纳' },
  { value: 'skipped', label: '已拒绝' },
]

interface ModelOption {
  value: string
  label: string
}

interface ReviewFilterBarProps {
  targetModel: string
  status: StatusFilter
  code: string
  modelOptions: ModelOption[]
  codeOptions: string[]
  filteredCount: number
  onTargetModelChange: (value: string) => void
  onStatusChange: (value: StatusFilter) => void
  onCodeChange: (value: string) => void
  onReset: () => void
}

const selectClass =
  'h-[34px] min-w-[180px] rounded-md border border-line bg-white px-3 text-[13px] text-ink-500 outline-none focus:border-brand-line'

export function ReviewFilterBar({
  targetModel,
  status,
  code,
  modelOptions,
  codeOptions,
  filteredCount,
  onTargetModelChange,
  onStatusChange,
  onCodeChange,
  onReset,
}: ReviewFilterBarProps) {
  return (
    <section className="flex flex-col gap-3 rounded-lg border border-line bg-white px-4 py-2.5 xl:h-[54px] xl:flex-row xl:items-center">
      <span className="text-[13px] text-ink-500">筛选</span>
      <div className="flex flex-wrap items-center gap-3">
        <select
          className={selectClass}
          value={targetModel}
          onChange={(event) => onTargetModelChange(event.target.value)}
        >
          <option value="all">目的型号：全部</option>
          {modelOptions.map((item) => (
            <option key={item.value} value={item.value}>
              目的型号：{item.label}
            </option>
          ))}
        </select>

        <select
          className={selectClass}
          value={status}
          onChange={(event) => onStatusChange(event.target.value as StatusFilter)}
        >
          <option value="all">状态：全部</option>
          {STATUS_OPTIONS.map((item) => (
            <option key={item.value} value={item.value}>
              状态：{item.label}
            </option>
          ))}
        </select>

        <select className={selectClass} value={code} onChange={(event) => onCodeChange(event.target.value)}>
          <option value="all">类型：全部</option>
          {codeOptions.map((item) => (
            <option key={item} value={item}>
              类型：{WARNING_LABELS[item] ?? item}
            </option>
          ))}
        </select>

        <button type="button" className="px-1 text-xs text-brand" onClick={onReset}>
          重置
        </button>
      </div>
      <span className="text-xs text-ink-400 xl:ml-auto">已筛选 {filteredCount} 条</span>
    </section>
  )
}
