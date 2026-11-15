import { API_BASE, authHeaders, toRequestError } from './client'

export interface SupplementValidation {
  passed?: boolean
  errors?: string[]
  checks?: Record<string, string>
}

export interface SupplementCandidateDto {
  id: number
  gap_id: number
  status: 'pending' | 'passed' | 'failed' | 'accepted' | 'rejected'
  llm_model: string
  prompt_version: string
  response: {
    target_command?: string
    target_view_path?: string[]
    reasoning?: string
    confidence?: string
  } | null
  validation: SupplementValidation | null
  created_at: string
  reviewed_at: string | null
}

/** 按知识缺口调用大模型生成候选，同步返回校验结果。 */
export async function generateCandidate(
  gapId: number,
  targetVendor: string,
  targetModel: string,
): Promise<SupplementCandidateDto> {
  const response = await fetch(`${API_BASE}/api/v1/knowledge/gaps/${gapId}/candidates`, {
    method: 'POST',
    headers: { ...authHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify({ target_vendor: targetVendor, target_model: targetModel }),
  })
  if (!response.ok) throw await toRequestError(response, '生成候选失败')
  return (await response.json()) as SupplementCandidateDto
}
