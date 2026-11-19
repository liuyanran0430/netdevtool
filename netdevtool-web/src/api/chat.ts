import { API_BASE, authHeaders, toRequestError } from './client'

export type ChatRole = 'user' | 'assistant'
export type ChatMessageStatus = 'streaming' | 'completed' | 'failed'
export type ChatQuestionMode = 'command' | 'troubleshoot' | 'knowledge' | 'unknown'

export interface ChatMessageDto {
  id: number
  role: ChatRole
  content: string
  status: ChatMessageStatus
  mode: ChatQuestionMode
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

export interface ChatSendResultDto {
  session: ChatSessionDto
  user_message: ChatMessageDto
  assistant_message: ChatMessageDto
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

/** 发送消息；不传 session_id 时后端会自动创建新会话。 */
export async function sendChatMessage(payload: ChatSendPayload): Promise<ChatSendResultDto> {
  const response = await fetch(`${API_BASE}/api/v1/chat/messages`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify(payload),
  })
  if (!response.ok) throw await toRequestError(response, '发送消息失败')
  return (await response.json()) as ChatSendResultDto
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

