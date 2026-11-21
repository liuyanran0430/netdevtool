import { API_BASE, authHeaders, toRequestError } from './client'

export type ChatRole = 'user' | 'assistant'
export type ChatMessageStatus = 'streaming' | 'completed' | 'clarifying' | 'failed'
export type ChatQuestionMode =
  | 'command'
  | 'troubleshoot'
  | 'knowledge'
  | 'unknown'
  | 'out_of_scope'

/** 回答引用的知识库来源。 */
export interface ChatCitationDto {
  doc_id: number | null
  file_name: string | null
  score: number | null
  snippet: string | null
}

/** 回答反馈：1=赞, -1=踩, 0=取消。 */
export type ChatFeedbackRating = 1 | -1 | 0

export interface ChatFeedbackDto {
  message_id: number
  rating: ChatFeedbackRating
  reason: string | null
}

export interface ChatMessageDto {
  id: number
  role: ChatRole
  content: string
  status: ChatMessageStatus
  mode: ChatQuestionMode
  evidenced: boolean
  citations: ChatCitationDto[]
  feedback: 1 | -1 | null
  created_at: string
}

export interface ChatSessionDto {
  id: number
  title: string
  vendor: string | null
  message_count: number
  last_message_at: string | null
  created_at: string
}

export interface ChatSessionDetailDto extends ChatSessionDto {
  messages: ChatMessageDto[]
}

export interface ChatSendPayload {
  session_id?: number | null
  content: string
  mode: ChatQuestionMode
  vendor?: string | null
}

/** 追问信息：问题、可选项与是否允许自由输入。 */
export interface ChatClarifyDto {
  question: string
  options: string[]
  allow_free_text: boolean
}

/** 当前用户的会话列表；`keyword` 按会话消息内容过滤。 */
export async function fetchChatSessions(keyword?: string): Promise<ChatSessionDto[]> {
  const params = new URLSearchParams()
  if (keyword) params.set('keyword', keyword)
  const query = params.size > 0 ? `?${params.toString()}` : ''
  const response = await fetch(`${API_BASE}/api/v1/chat/sessions${query}`, {
    headers: authHeaders(),
  })
  if (!response.ok) throw await toRequestError(response, '加载会话失败')
  return (await response.json()) as ChatSessionDto[]
}

/** 会话详情：包含按时间排列的全部消息。 */
export async function fetchChatSession(sessionId: number): Promise<ChatSessionDetailDto> {
  const response = await fetch(`${API_BASE}/api/v1/chat/sessions/${sessionId}`, {
    headers: authHeaders(),
  })
  if (!response.ok) throw await toRequestError(response, '加载会话消息失败')
  return (await response.json()) as ChatSessionDetailDto
}

/** 查询问答处理阶段：intent / retrieval / generation，null 表示已结束。 */
export async function fetchChatProgress(requestId: string): Promise<string | null> {
  const response = await fetch(`${API_BASE}/api/v1/chat/progress/${requestId}`, {
    headers: authHeaders(),
  })
  if (!response.ok) return null
  const data = (await response.json()) as { stage: string | null }
  return data.stage
}

/** 流式问答的事件回调。 */
export interface ChatStreamHandlers {
  onMeta?: (meta: {
    session_id: number
    user_message_id: number
    assistant_message_id: number
    intent: ChatQuestionMode
    mode: ChatQuestionMode
  }) => void
  onStage?: (stage: string) => void
  onDelta?: (text: string) => void
  onResult?: (data: { content: string }) => void
  onCitations?: (citations: ChatCitationDto[]) => void
  onDone?: (data: {
    assistant_message_id: number
    status: ChatMessageStatus
    clarify?: ChatClarifyDto | null
  }) => void
  onError?: (data: { message: string; kind?: string; trace_id?: string }) => void
}

/** 解析 SSE 帧：event + data，兼容多行 data。 */
async function* readSse(
  body: ReadableStream<Uint8Array>,
): AsyncGenerator<{ event: string; data: string }> {
  const reader = body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, '\n')
      let boundary = buffer.indexOf('\n\n')
      while (boundary >= 0) {
        const frame = buffer.slice(0, boundary)
        buffer = buffer.slice(boundary + 2)
        let event = 'message'
        const data: string[] = []
        for (const line of frame.split('\n')) {
          if (line.startsWith('event:')) event = line.slice(6).trim()
          else if (line.startsWith('data:')) data.push(line.slice(5).trimStart())
        }
        if (data.length > 0) yield { event, data: data.join('\n') }
        boundary = buffer.indexOf('\n\n')
      }
    }
  } finally {
    reader.releaseLock()
  }
}

/** SSE 发送消息：命令/知识逐字回调，故障排查通过 onResult 一次性返回。 */
export async function streamChatMessage(
  payload: ChatSendPayload,
  requestId: string,
  handlers: ChatStreamHandlers,
  signal?: AbortSignal,
): Promise<void> {
  const response = await fetch(`${API_BASE}/api/v1/chat/messages/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
      'X-Chat-Request-Id': requestId,
    },
    body: JSON.stringify(payload),
    signal,
  })
  if (!response.ok) throw await toRequestError(response, '发送消息失败')
  if (!response.body) throw new Error('浏览器不支持流式响应')

  for await (const frame of readSse(response.body)) {
    let data: any
    try {
      data = JSON.parse(frame.data)
    } catch {
      continue
    }
    switch (frame.event) {
      case 'meta':
        handlers.onMeta?.(data)
        break
      case 'stage':
        if (data?.stage) handlers.onStage?.(String(data.stage))
        break
      case 'delta':
        if (typeof data?.text === 'string') handlers.onDelta?.(data.text)
        break
      case 'result':
        handlers.onResult?.(data)
        break
      case 'citations':
        if (Array.isArray(data)) handlers.onCitations?.(data)
        break
      case 'done':
        handlers.onDone?.(data)
        break
      case 'error':
        handlers.onError?.(data)
        break
      default:
        break
    }
  }
}

/** 对回答点赞/点踩：rating=0 取消；点踩需给出原因。 */
export async function setChatMessageFeedback(
  messageId: number,
  rating: ChatFeedbackRating,
  reason?: string,
): Promise<ChatFeedbackDto> {
  const response = await fetch(
    `${API_BASE}/api/v1/chat/messages/${messageId}/feedback`,
    {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify(reason ? { rating, reason } : { rating }),
    },
  )
  if (!response.ok) throw await toRequestError(response, '提交反馈失败')
  return (await response.json()) as ChatFeedbackDto
}

/** 重命名会话。 */
export async function renameChatSession(
  sessionId: number,
  title: string,
): Promise<ChatSessionDto> {
  const response = await fetch(`${API_BASE}/api/v1/chat/sessions/${sessionId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify({ title }),
  })
  if (!response.ok) throw await toRequestError(response, '重命名会话失败')
  return (await response.json()) as ChatSessionDto
}

/** 删除会话（后端软删除，列表不再返回）。 */
export async function deleteChatSession(sessionId: number): Promise<void> {
  const response = await fetch(`${API_BASE}/api/v1/chat/sessions/${sessionId}`, {
    method: 'DELETE',
    headers: authHeaders(),
  })
  if (!response.ok) throw await toRequestError(response, '删除会话失败')
}

