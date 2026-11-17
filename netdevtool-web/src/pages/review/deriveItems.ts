/** 后端待审核条目 → 页面展示模型；已处置的条目由后端过滤，不再出现在列表中。 */

import type {
  ReviewCandidateDto,
  ReviewItemDto,
  ReviewSeverity,
} from '../../api/review'

export interface ReviewItem {
  /** 跨任务稳定标识，与后端 review_decisions.item_key 一致 */
  key: string
  codes: string[]
  severity: ReviewSeverity
  sourceVendor: string
  sourceModel: string
  targetVendor: string
  targetModel: string
  /** 关联的知识缺口 id，空表示该命令未采集到缺口 */
  gapId: number | null
  /** 最近一次 AI 候选，空表示尚未生成 */
  candidate: ReviewCandidateDto | null
  /** 源命令所在的配置视图 */
  view: string
  sourceText: string
  targetText: string
  message: string
}

export const WARNING_LABELS: Record<string, string> = {
  unknown_command: '未识别命令',
  unsupported_entity: '目标不支持',
  unverified_impl: '实现未验证',
  low_confidence: '低置信度',
  supplement_applied: '已采纳',
}

export function toReviewItems(items: ReviewItemDto[]): ReviewItem[] {
  return items.map((item) => ({
    key: item.item_key,
    codes: item.codes,
    severity: item.severity,
    sourceVendor: item.source_vendor,
    sourceModel: item.source_model,
    targetVendor: item.target_vendor,
    targetModel: item.target_model,
    gapId: item.gap_id,
    candidate: item.candidate,
    view: item.view,
    sourceText: item.source_text,
    targetText: item.target_text,
    message: item.message,
  }))
}
