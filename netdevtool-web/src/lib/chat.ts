import type {
  ChatCitationDto,
  ChatMessageDto,
  ChatQuestionMode,
} from '../api/chat'

/** 意图类型的中文名，用于「已按 XX 处理」提示 */
export const MODE_LABELS: Record<string, string> = {
  command: '配置查询',
  troubleshoot: '故障排查',
  knowledge: '知识提问',
  out_of_scope: '范围外',
}

export interface ChatMessageView {
  id: string
  /** 数据库消息 id，临时消息为空，用于反馈接口 */
  dbId?: number
  role: 'user' | 'assistant'
  content: string
  clarifying?: boolean
  mode?: ChatQuestionMode
  evidenced?: boolean
  citations?: ChatCitationDto[]
  feedback?: 1 | -1 | null
  pending?: boolean
  streaming?: boolean
  stage?: string
  requestId?: string
}

export function toChatView(message: ChatMessageDto): ChatMessageView {
  return {
    id: `db-${message.id}`,
    dbId: message.id,
    role: message.role,
    content: message.content,
    clarifying: message.status === 'clarifying',
    mode: message.mode,
    evidenced: message.evidenced,
    citations: message.citations,
    feedback: message.feedback ?? null,
  }
}
