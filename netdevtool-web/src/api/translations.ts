import { API_BASE, authHeaders, toRequestError } from './client'

export type TranslationStatus = 'pending' | 'running' | 'succeeded' | 'failed'
export type TranslationTone = 'focus' | 'success' | 'warn' | 'error' | 'muted'

export interface TranslationCreateInput {
  source_text: string
  source_vendor: string
  source_model: string
  target_vendor: string
  target_model: string
}

export interface TranslationResultLines {
  /** 渲染输出的一行纯文本，顺序即目标配置顺序。 */
  text: string
  tone: TranslationTone
}

export interface TranslationWarning {
  /** 告警直接关联到某个实体（可选） */
  entity_id?: string | null
  /** 告警覆盖的源配置行号（冗余） */
  no: number[]
  message: string
  code: string
  severity: 'warn' | 'error'
}

export interface TranslationEntityInfo {
  id: string
  /** 该实体覆盖的源配置行号，用于源面板高亮 */
  source_nos: number[]
  /** 实体自身命令行号（不含视图头行），用于区分视图行与命令行 */
  command_nos?: number[]
  /** 该实体在目标输出中的行号索引，用于目标面板高亮 */
  target_line_indices: number[]
  description: string | null
}

export interface TranslationResult {
  lines: TranslationResultLines[]
  /** 与 lines 平行的源行号映射：无实体行（未识别命令、显示命令）记录其源行号，其余为 null */
  line_source_nos?: (number | null)[]
  entities?: TranslationEntityInfo[]
  warnings?: TranslationWarning[]
  summary: {
    total: number
    duration_ms: number
  }
}

export interface TranslationTask {
  request_id: string
  status: TranslationStatus
  result?: TranslationResult | null
  error?: string | null
}

export interface TranslationListItem {
  request_id: string
  status: TranslationStatus
  source_vendor: string
  source_model: string
  target_vendor: string
  target_model: string
  created_at: string
  finished_at: string | null
}

export interface TranslationSource {
  request_id: string
  source_text: string
  source_vendor: string
  source_model: string
  target_vendor: string
  target_model: string
  status: TranslationStatus
}

export async function createTranslation(
  input: TranslationCreateInput,
): Promise<Pick<TranslationTask, 'request_id' | 'status'>> {
  const response = await fetch(`${API_BASE}/api/v1/translations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify(input),
  })
  if (!response.ok) throw await toRequestError(response, '创建翻译任务失败')
  return (await response.json()) as Pick<TranslationTask, 'request_id' | 'status'>
}

export async function getTranslation(requestId: string): Promise<TranslationTask> {
  const response = await fetch(`${API_BASE}/api/v1/translations/${requestId}`, {
    headers: authHeaders(),
  })
  if (!response.ok) throw await toRequestError(response, '查询翻译任务失败')
  return (await response.json()) as TranslationTask
}

export async function listTranslations(limit = 20): Promise<TranslationListItem[]> {
  const response = await fetch(`${API_BASE}/api/v1/translations?limit=${limit}`, {
    headers: authHeaders(),
  })
  if (!response.ok) throw await toRequestError(response, '查询翻译记录失败')
  return (await response.json()) as TranslationListItem[]
}

export async function getTranslationSource(requestId: string): Promise<TranslationSource> {
  const response = await fetch(`${API_BASE}/api/v1/translations/${requestId}/source`, {
    headers: authHeaders(),
  })
  if (!response.ok) throw await toRequestError(response, '查询源配置失败')
  return (await response.json()) as TranslationSource
}
