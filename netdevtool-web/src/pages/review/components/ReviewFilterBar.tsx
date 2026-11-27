import { WARNING_LABELS } from '../deriveItems'
import type { ReviewItemType } from '../../../api/review'

interface ModelOption {
  value: string
  label: string
}

interface ReviewFilterBarProps {
  targetModel: string
  type: ReviewItemType | 'all'
  modelOptions: ModelOption[]
  typeOptions: ReviewItemType[]
  filteredCount: number
  onTargetModelChange: (value: string) => void
  onTypeChange: (value: ReviewItemType | 'all') => void
  onReset: () => void
}

const selectClass =
  'h-[34px] min-w-[180px] rounded-md border border-line bg-white px-3 text-[13px] text-ink-500 outline-none focus:border-brand-line'

export function ReviewFilterBar({
  targetModel,
  type,
  modelOptions,
  typeOptions,
  filteredCount,
  onTargetModelChange,
  onTypeChange,
  onReset,
}: ReviewFilterBarProps) {
  return (
    <section className="flex flex-col gap-3 rounded-lg border border-line bg-white px-4 py-2.5 xl:h-[54px] xl:flex-row xl:items-center">
      <div className="flex flex-wrap items-center gap-3">
        <span className="text-[13px] text-ink-500">目的型号：</span>
        <select
          className={selectClass}
          value={targetModel}
          onChange={(event) => onTargetModelChange(event.target.value)}
        >
          <option value="all">全部</option>
          {modelOptions.map((item) => (
            <option key={item.value} value={item.value}>
              {item.label}
            </option>
          ))}
        </select>

        <span className="text-[13px] text-ink-500">类型：</span>
        <select
          className={selectClass}
          value={type}
          onChange={(event) => onTypeChange(event.target.value as ReviewItemType | 'all')}
        >
          <option value="all">全部</option>
          {typeOptions.map((item) => (
            <option key={item} value={item}>
              {WARNING_LABELS[item] ?? item}
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
