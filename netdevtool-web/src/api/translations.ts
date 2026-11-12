const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8083'

export type TranslationStatus = 'pending' | 'running' | 'succeeded' | 'failed'
export type TranslationTone = 'focus' | 'success' | 'warn' | 'muted'

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
}

export interface TranslationResult {
  lines: TranslationResultLine[]
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

async function ensureOk(response: Response): Promise<void> {
  if (response.ok) return
  const body = (await response.json().catch(() => null)) as { message?: string } | null
  throw new Error(body?.message ?? `请求失败：${response.status}`)
}

export async function createTranslation(
  input: TranslationCreateInput,
): Promise<Pick<TranslationTask, 'request_id' | 'status'>> {
  const response = await fetch(`${API_BASE}/api/v1/translations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
  await ensureOk(response)
  return (await response.json()) as Pick<TranslationTask, 'request_id' | 'status'>
}

export async function getTranslation(requestId: string): Promise<TranslationTask> {
  const response = await fetch(`${API_BASE}/api/v1/translations/${requestId}`)
  await ensureOk(response)
  return (await response.json()) as TranslationTask
}

export async function cancelTranslation(requestId: string): Promise<void> {
  const response = await fetch(`${API_BASE}/api/v1/translations/${requestId}`, {
    method: 'DELETE',
  })
  await ensureOk(response)
}
