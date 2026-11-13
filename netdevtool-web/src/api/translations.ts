import { API_BASE, toRequestError } from './client'

export type TranslationStatus = 'pending' | 'running' | 'succeeded' | 'failed'
export type TranslationTone = 'focus' | 'success' | 'warn' | 'error' | 'muted'

export interface TranslationCreateInput {
  source_text: string
  source_vendor: string
  source_model: string
  target_vendor: string
  target_model: string
}

export interface TranslationResultLine {
  no: number
  text: string
  tone: TranslationTone
  source_no: number | null
  entity_id?: string | null
}

export interface TranslationWarning {
  /** 源配置行号 */
  no: number
  message: string
  /** 告警类型，用于前端聚合展示 */
  code: string
  severity: 'warn' | 'error'
}

export interface TranslationEntityInfo {
  id: string
  description: string | null
}

export interface TranslationResult {
  lines: TranslationResultLine[]
  warnings?: TranslationWarning[]
  entities?: TranslationEntityInfo[]
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

export async function createTranslation(
  input: TranslationCreateInput,
): Promise<Pick<TranslationTask, 'request_id' | 'status'>> {
  const response = await fetch(`${API_BASE}/api/v1/translations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
  if (!response.ok) throw await toRequestError(response, '创建翻译任务失败')
  return (await response.json()) as Pick<TranslationTask, 'request_id' | 'status'>
}

export async function getTranslation(requestId: string): Promise<TranslationTask> {
  const response = await fetch(`${API_BASE}/api/v1/translations/${requestId}`)
  if (!response.ok) throw await toRequestError(response, '查询翻译任务失败')
  return (await response.json()) as TranslationTask
}
