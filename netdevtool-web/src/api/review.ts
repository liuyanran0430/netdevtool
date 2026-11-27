/**
 * 命令审核接口：条目查询走真实后端（GET /review/items）；
 * 处置/撤销按钮仅展示，功能暂未实现。审核记录抽屉使用演示数据。
 */

import { API_BASE, authHeaders, toRequestError } from './client'

export type ReviewSeverity = 'error' | 'warn' | 'info'
export type ReviewDecisionAction = 'accept' | 'edit' | 'skip'

export type ReviewItemType = 'unknown_source' | 'missing_target_impl' | 'unverified_impl'

/** 后端物化的待审条目：段信息 + 设备档案关联的厂商型号。 */
export interface ReviewItemDto {
  item_hash: string
  request_id: string
  type: ReviewItemType
  status: 'pending' | 'accepted' | 'rejected'
  source_text: string[]
  original_tone: string
  entities_id: string[] | null
  source_vendor: string
  source_model: string
  target_vendor: string
  target_model: string
  created_at: string
}

/** 审核条目全局统计，不受筛选影响。 */
export interface ReviewStatsDto {
  pending: number
  accepted: number
  rejected: number
}

/** 目的型号筛选项。 */
export interface ReviewTargetOptionDto {
  vendor: string
  model: string
}

/** 审核条目分页结果，附带全局统计与筛选项。 */
export interface ReviewItemsPageDto {
  items: ReviewItemDto[]
  total: number
  page: number
  page_size: number
  stats: ReviewStatsDto
  target_options: ReviewTargetOptionDto[]
  type_options: ReviewItemType[]
}

export interface ReviewItemsQuery {
  page?: number
  pageSize?: number
  targetVendor?: string
  targetModel?: string
  type?: ReviewItemType
}

/* ---------------------------- 审核记录（演示数据） ---------------------------- */

/** 审核条目关联的最近一次 AI 候选。 */
export interface ReviewCandidateDto {
  id: number
  status: 'pending' | 'passed' | 'failed' | 'accepted' | 'rejected'
  command: string | null
  views: string[]
  reasoning: string | null
  passed: boolean
  created_at: string
}

/** 后端持久化的审核处置结果（演示）。 */
export interface ReviewDecisionDto {
  item_key: string
  action: ReviewDecisionAction
  decided_text: string | null
  candidate_id: number | null
}

/** 审核记录条目：一条处置及关联命令的展示信息（演示）。 */
export interface ReviewHistoryItemDto {
  item_key: string
  action: ReviewDecisionAction
  decided_text: string | null
  request_id: string
  source_vendor: string
  source_model: string
  target_vendor: string
  target_model: string
  source_text: string
  codes: string[]
  created_at: string
  updated_at: string
}

export interface ReviewHistoryPageDto {
  items: ReviewHistoryItemDto[]
  total: number
  page: number
  page_size: number
}

export interface ReviewHistoryQuery {
  page?: number
  pageSize?: number
  action?: ReviewDecisionAction | 'all'
  keyword?: string
}

const MOCK_HISTORY: ReviewHistoryItemDto[] = [
  {
    item_key: 'mock-history-1',
    action: 'accept',
    decided_text: null,
    request_id: 'req-mock-history',
    source_vendor: '华为',
    source_model: 'S5735',
    target_vendor: 'H3C',
    target_model: 'S6520',
    source_text: 'lldp enable',
    codes: ['unknown_command'],
    created_at: '2026-11-27T09:00:00',
    updated_at: '2026-11-27T09:40:00',
  },
]

/* ---------------------------- 真实接口 ---------------------------- */

/** 分页读取当前用户的待审核条目、全局统计与筛选项。 */
export async function listReviewItems(
  query: ReviewItemsQuery = {},
): Promise<ReviewItemsPageDto> {
  const params = new URLSearchParams()
  params.set('page', String(query.page ?? 1))
  params.set('page_size', String(query.pageSize ?? 10))
  if (query.targetVendor) params.set('target_vendor', query.targetVendor)
  if (query.targetModel) params.set('target_model', query.targetModel)
  if (query.type) params.set('item_type', query.type)
  const response = await fetch(`${API_BASE}/api/v1/review/items?${params.toString()}`, {
    headers: authHeaders(),
  })
  if (!response.ok) throw await toRequestError(response, '加载待审核条目')
  return (await response.json()) as ReviewItemsPageDto
}

/** 检查点快照接口已下线，返回空列表。 */
export async function listReviewDecisionSnapshots(): Promise<
  { request_id: string; line_index: number; action: ReviewDecisionAction; decided_text: string | null; original_tone: string }[]
> {
  return []
}

/** 分页读取审核处置记录（演示数据）。 */
export async function listReviewHistory(
  query: ReviewHistoryQuery = {},
): Promise<ReviewHistoryPageDto> {
  const page = query.page ?? 1
  const pageSize = query.pageSize ?? 10
  const rows = MOCK_HISTORY.filter(
    (item) =>
      (query.action === undefined || query.action === 'all' || item.action === query.action) &&
      (!query.keyword || item.source_text.includes(query.keyword)),
  )
  return {
    items: rows.slice((page - 1) * pageSize, page * pageSize),
    total: rows.length,
    page,
    page_size: pageSize,
  }
}
