import { API_BASE, authHeaders, toRequestError } from './client'

export type ReviewSeverity = 'error' | 'warn' | 'info'
export type ReviewDecisionAction = 'accept' | 'edit' | 'skip'

/** 后端持久化的审核处置结果。 */
export interface ReviewDecisionDto {
  item_key: string
  action: ReviewDecisionAction
  decided_text: string | null
  candidate_id: number | null
}

export interface ReviewDecisionPayload {
  source_vendor: string
  source_model: string
  target_vendor: string
  target_model: string
  source_text: string
  action: ReviewDecisionAction
  decided_text?: string
  candidate_id?: number
}

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

/** 后端物化的待审条目，`line_index` 为结果行序号（从 1 开始）。 */
export interface ReviewItemDto {
  request_id: string
  line_index: number
  item_key: string
  source_no: number | null
  codes: string[]
  severity: ReviewSeverity
  source_vendor: string
  source_model: string
  target_vendor: string
  target_model: string
  gap_id: number | null
  candidate: ReviewCandidateDto | null
  view: string
  source_text: string
  target_text: string
  message: string
  created_at: string
}

/** 审核条目全局统计，不受筛选影响。 */
export interface ReviewStatsDto {
  pending: number
  accepted: number
  edited: number
  skipped: number
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
  code_options: string[]
}

export interface ReviewItemsQuery {
  page?: number
  pageSize?: number
  targetVendor?: string
  targetModel?: string
  code?: string
}

/** 处置快照：审核页生成检查点时按来源行回填。 */
export interface ReviewDecisionSnapshotDto {
  request_id: string
  line_index: number
  action: ReviewDecisionAction
  decided_text: string | null
  original_tone: string
}

/** 审核记录条目：一条处置及关联命令的展示信息。 */
export interface ReviewHistoryItemDto {
  item_key: string
  action: ReviewDecisionAction
  decided_text: string | null
  request_id: string
  source_vendor: string
  source_model: string
  target_vendor: string
  target_model: string
  view: string
  source_text: string
  target_text: string
  codes: string[]
  candidate: ReviewCandidateDto | null
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

export async function listReviewItems(
  query: ReviewItemsQuery = {},
): Promise<ReviewItemsPageDto> {
  const params = new URLSearchParams()
  params.set('page', String(query.page ?? 1))
  params.set('page_size', String(query.pageSize ?? 10))
  if (query.targetVendor) params.set('target_vendor', query.targetVendor)
  if (query.targetModel) params.set('target_model', query.targetModel)
  if (query.code) params.set('code', query.code)
  const response = await fetch(`${API_BASE}/api/v1/review/items?${params.toString()}`, {
    headers: authHeaders(),
  })
  if (!response.ok) throw await toRequestError(response, '加载待审核条目失败')
  return (await response.json()) as ReviewItemsPageDto
}

/** 当前用户全部审核处置快照，用于生成检查点。 */
export async function listReviewDecisionSnapshots(): Promise<ReviewDecisionSnapshotDto[]> {
  const response = await fetch(`${API_BASE}/api/v1/review/decisions`, {
    headers: authHeaders(),
  })
  if (!response.ok) throw await toRequestError(response, '加载审核处置快照失败')
  return (await response.json()) as ReviewDecisionSnapshotDto[]
}

/** 分页读取当前用户的审核处置记录。 */
export async function listReviewHistory(
  query: ReviewHistoryQuery = {},
): Promise<ReviewHistoryPageDto> {
  const params = new URLSearchParams()
  params.set('page', String(query.page ?? 1))
  params.set('page_size', String(query.pageSize ?? 10))
  if (query.action && query.action !== 'all') params.set('action', query.action)
  if (query.keyword) params.set('keyword', query.keyword)
  const response = await fetch(`${API_BASE}/api/v1/review/history?${params.toString()}`, {
    headers: authHeaders(),
  })
  if (!response.ok) throw await toRequestError(response, '加载审核记录失败')
  return (await response.json()) as ReviewHistoryPageDto
}

/** 记录审核处置：采纳 / 修改后采纳 / 拒绝，结果持久化到后端。 */
export async function createReviewDecision(
  payload: ReviewDecisionPayload,
): Promise<ReviewDecisionDto> {
  const response = await fetch(`${API_BASE}/api/v1/review/decisions`, {
    method: 'POST',
    headers: { ...authHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) throw await toRequestError(response, '提交审核处置失败')
  return (await response.json()) as ReviewDecisionDto
}

/** 撤销审核处置；已采纳的 AI 候选会同步回滚补充知识库。 */
export async function deleteReviewDecision(itemKey: string): Promise<void> {
  const response = await fetch(
    `${API_BASE}/api/v1/review/decisions/${encodeURIComponent(itemKey)}`,
    { method: 'DELETE', headers: authHeaders() },
  )
  if (!response.ok) throw await toRequestError(response, '撤销审核处置失败')
}
