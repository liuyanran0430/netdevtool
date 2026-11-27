/** 后端待审核条目 → 页面展示模型；处置按钮仅展示，功能暂未实现。 */

import type { ReviewItemDto, ReviewItemType, ReviewSeverity } from '../../api/review'

export interface ReviewItem {
  /** 跨任务稳定段标识，与后端 review_items.item_hash 一致 */
  key: string
  codes: string[]
  severity: ReviewSeverity
  sourceVendor: string
  sourceModel: string
  targetVendor: string
  targetModel: string
  sourceText: string
  targetText: string
  message: string
}

/** 条目类型 → 展示标签与说明文案 */
export const TYPE_LABELS: Record<ReviewItemType, string> = {
  unknown_source: '未识别命令',
  missing_target_impl: '目标侧无实现',
  unverified_impl: '实现未验证',
}

const TYPE_MESSAGES: Record<ReviewItemType, string> = {
  unknown_source: '未识别命令，保持原样输出，需要人工确认',
  missing_target_impl: '目标厂商缺少该实体的实现，建议沉淀补充规则',
  unverified_impl: '目标侧实现未经验证',
}

/** 条目类型筛选下拉直接使用类型值 */
export const WARNING_LABELS: Record<string, string> = TYPE_LABELS

export function toReviewItems(items: ReviewItemDto[]): ReviewItem[] {
  return items.map((item) => ({
    key: item.item_hash,
    codes: [item.type],
    severity: (item.original_tone === 'error'
      ? 'error'
      : item.original_tone === 'warn'
        ? 'warn'
        : 'info') as ReviewSeverity,
    sourceVendor: item.source_vendor,
    sourceModel: item.source_model,
    targetVendor: item.target_vendor,
    targetModel: item.target_model,
    sourceText: item.source_text.join('\n'),
    targetText: '',
    message: TYPE_MESSAGES[item.type] ?? item.type,
  }))
}
