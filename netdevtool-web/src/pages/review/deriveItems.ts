/** 后端聚合条目 → 页面展示模型；审核状态来自后端持久化的处置结果。 */

import type {
  ReviewCandidateDto,
  ReviewDecisionDto,
  ReviewItemDto,
  ReviewSeverity,
} from '../../api/review'

export type ReviewStatus = 'pending' | 'done' | 'skipped'

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
  /** 后端持久化的审核处置，空表示待审核 */
  decision: ReviewDecisionDto | null
  /** 源命令所在的配置视图 */
  view: string
  sourceText: string
  targetText: string
  message: string
  status: ReviewStatus
}

export const WARNING_LABELS: Record<string, string> = {
  unknown_command: '未识别命令',
  unsupported_entity: '目标不支持',
  unverified_impl: '实现未验证',
  low_confidence: '低置信度',
  supplement_applied: '已采纳',
}

function statusOf(decision: ReviewDecisionDto | null): ReviewStatus {
  if (!decision) return 'pending'
  return decision.action === 'skip' ? 'skipped' : 'done'
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
    decision: item.decision,
    view: item.view,
    sourceText: item.source_text,
    targetText:
      item.decision?.action === 'edit' && item.decision.decided_text
        ? item.decision.decided_text
        : item.target_text,
    message: item.message,
    status: statusOf(item.decision),
  }))
}
