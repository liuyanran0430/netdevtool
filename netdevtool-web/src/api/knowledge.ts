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
  response: {
    target_command?: string
    target_view_path?: string[]
    reasoning?: string
    confidence?: string
  } | null
  validation: SupplementValidation | null
  rag?: {
    status: string
    reference_count: number
    reason?: string
    rerank_error?: string
  } | null
  created_at: string
  reviewed_at: string | null
}

export interface KnowledgeBaseDto {
  id: number
  name: string
  vector_store_name: string
  chunking_mode: 'general' | 'parent-child' | 'qa'
  general_delimiter: string | null
  general_max_length: number | null
  general_overlap: number | null
  parent_max_length: number | null
  child_delimiter: string | null
  child_max_length: number | null
  heading_split_levels: string
  indexing_mode: 'high' | 'economical'
  retrieval_mode: 'embedding' | 'bm25' | 'hybrid'
  hybrid_semantic_weight: number
  hybrid_top_k: number
  hybrid_score_threshold: number
  created_at: string
  updated_at: string
}

export interface KnowledgeBaseConfigPayload {
  chunking_mode: KnowledgeBaseDto['chunking_mode']
  general_delimiter: string
  general_max_length: number | null
  general_overlap: number | null
  parent_max_length: number | null
  child_delimiter: string
  child_max_length: number | null
  heading_split_levels: string
  indexing_mode: KnowledgeBaseDto['indexing_mode']
  retrieval_mode: KnowledgeBaseDto['retrieval_mode']
  hybrid_semantic_weight: number
  hybrid_top_k: number
  hybrid_score_threshold: number
}

/** 知识库连接状态出参。 */
export interface KnowledgeStatusDto {
  connected: boolean
  database: boolean
  qdrant: boolean
  knowledge_bases: number
  detail: string | null
}

/** 查询知识库连接状态（数据库 + Qdrant）。 */
export async function fetchKnowledgeStatus(): Promise<KnowledgeStatusDto> {
  const response = await fetch(`${API_BASE}/api/v1/knowledge/status`, {
    headers: authHeaders(),
  })
  if (!response.ok) throw await toRequestError(response, '查询知识库状态失败')
  return (await response.json()) as KnowledgeStatusDto
}

/** 查询知识库列表。 */
export async function fetchKnowledgeBases(): Promise<KnowledgeBaseDto[]> {
  const response = await fetch(`${API_BASE}/api/v1/knowledge/bases`, {
    headers: authHeaders(),
  })
  if (!response.ok) throw await toRequestError(response, '加载知识库失败')
  return (await response.json()) as KnowledgeBaseDto[]
}

/** 更新知识库的向量与检索配置。 */
export async function updateKnowledgeBaseConfig(
  baseId: number,
  payload: KnowledgeBaseConfigPayload,
): Promise<KnowledgeBaseDto> {
  const response = await fetch(
    `${API_BASE}/api/v1/knowledge/bases/${baseId}/config`,
    {
      method: 'PUT',
      headers: { ...authHeaders(), 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    },
  )
  if (!response.ok) throw await toRequestError(response, '保存知识库配置失败')
  return (await response.json()) as KnowledgeBaseDto
}

export type KnowledgeDocumentStatus =
  | 'pending'
  | 'processing'
  | 'indexed'
  | 'failed'
  | 'configured'
  | 'needmanual'

export type KnowledgeDocumentStage =
  | 'parsing'
  | 'chunking'
  | 'embedding'
  | 'indexing'
  | 'verifying'
  | 'done'

export interface KnowledgeDocumentDto {
  id: number
  kb_id: number
  file_name: string
  file_type: 'pdf' | 'yaml' | 'excel' | 'markdown'
  file_size: number
  file_hash: string
  status: KnowledgeDocumentStatus
  stage: KnowledgeDocumentStage | null
  progress: number
  total_chunks: number | null
  processed_chunks: number
  chunk_count: number | null
  metadata_json: Record<string, unknown> | null
  error_message: string | null
  created_at: string
  updated_at: string
}

export interface KnowledgeDocumentListDto {
  items: KnowledgeDocumentDto[]
  total: number
  indexed_count: number
  processing_count: number
}

export interface KnowledgeDocumentListQuery {
  page?: number
  pageSize?: number
  keyword?: string
  status?: KnowledgeDocumentStatus
  fileType?: 'pdf' | 'yaml' | 'excel' | 'markdown'
}

export interface KnowledgeDocumentUploadItemDto {
  file_name: string
  result: 'created' | 'duplicated' | 'failed'
  doc: KnowledgeDocumentDto | null
  error: string | null
}

/** 分页查询知识库文档列表。 */
export async function fetchKnowledgeDocuments(
  kbId: number,
  query: KnowledgeDocumentListQuery = {},
): Promise<KnowledgeDocumentListDto> {
  const params = new URLSearchParams({
    page: String(query.page ?? 1),
    page_size: String(query.pageSize ?? 20),
  })
  if (query.keyword) params.set('keyword', query.keyword)
  if (query.status) params.set('status', query.status)
  if (query.fileType) params.set('file_type', query.fileType)
  const response = await fetch(
    `${API_BASE}/api/v1/knowledge/bases/${kbId}/documents?${params.toString()}`,
    { headers: authHeaders() },
  )
  if (!response.ok) throw await toRequestError(response, '加载文档列表失败')
  return (await response.json()) as KnowledgeDocumentListDto
}

/** 上传单个文档，返回该文件的处理结果。 */
export async function uploadKnowledgeDocument(
  kbId: number,
  file: File,
): Promise<KnowledgeDocumentUploadItemDto> {
  const form = new FormData()
  form.append('files', file)
  const response = await fetch(
    `${API_BASE}/api/v1/knowledge/bases/${kbId}/documents`,
    { method: 'POST', headers: authHeaders(), body: form },
  )
  if (!response.ok) throw await toRequestError(response, '上传文档失败')
  const body = (await response.json()) as {
    items: KnowledgeDocumentUploadItemDto[]
  }
  return (
    body.items[0] ?? {
      file_name: file.name,
      result: 'failed',
      doc: null,
      error: '服务端未返回处理结果',
    }
  )
}

/** 删除文档及其向量。 */
export async function deleteKnowledgeDocument(docId: number): Promise<void> {
  const response = await fetch(
    `${API_BASE}/api/v1/knowledge/documents/${docId}`,
    { method: 'DELETE', headers: authHeaders() },
  )
  if (!response.ok) throw await toRequestError(response, '删除文档失败')
}

/** 重试文档索引。 */
export async function retryKnowledgeDocument(
  docId: number,
): Promise<KnowledgeDocumentDto> {
  const response = await fetch(
    `${API_BASE}/api/v1/knowledge/documents/${docId}/retry`,
    { method: 'POST', headers: authHeaders() },
  )
  if (!response.ok) throw await toRequestError(response, '重试文档失败')
  return (await response.json()) as KnowledgeDocumentDto
}

/** 更新单篇文档的元数据键值对。 */
export async function updateKnowledgeDocumentMetadata(
  docId: number,
  metadata: Record<string, string>,
): Promise<KnowledgeDocumentDto> {
  const response = await fetch(
    `${API_BASE}/api/v1/knowledge/documents/${docId}/metadata`,
    {
      method: 'PATCH',
      headers: { ...authHeaders(), 'Content-Type': 'application/json' },
      body: JSON.stringify({ metadata }),
    },
  )
  if (!response.ok) throw await toRequestError(response, '保存元数据失败')
  return (await response.json()) as KnowledgeDocumentDto
}

/** 批量整组替换多篇文档的元数据键值对。 */
export async function updateKnowledgeDocumentsMetadata(
  ids: number[],
  metadata: Record<string, string>,
): Promise<KnowledgeDocumentDto[]> {
  const response = await fetch(
    `${API_BASE}/api/v1/knowledge/documents/metadata`,
    {
      method: 'PATCH',
      headers: { ...authHeaders(), 'Content-Type': 'application/json' },
      body: JSON.stringify({ ids, metadata }),
    },
  )
  if (!response.ok) throw await toRequestError(response, '批量保存元数据失败')
  return (await response.json()) as KnowledgeDocumentDto[]
}

/**
 * 按知识缺口生成 AI 候选（本地 Mock）。
 * 后端缺口/候选处理已下线，返回演示候选供审核页展示。
 */
export async function generateCandidate(
  gapId: number,
  _targetVendor: string,
  _targetModel: string,
): Promise<SupplementCandidateDto> {
  await new Promise((resolve) => setTimeout(resolve, 600))
  return {
    id: gapId + 1000,
    gap_id: gapId,
    status: 'passed',
    response: {
      target_command: 'ospf 100 router-id {id}',
      target_view_path: ['system-view'],
      reasoning: '演示数据：根据厂商配置指导库相似案例推断等价命令。',
      confidence: 'high',
    },
    validation: { passed: true, errors: [], checks: { source_template: '通过', target_views: '通过' } },
    rag: { status: 'reranked', reference_count: 3 },
    created_at: new Date().toISOString().slice(0, 19),
    reviewed_at: null,
  }
}
