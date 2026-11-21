import { useEffect, useRef, useState } from 'react'
import {
  deleteChatSession,
  fetchChatSession,
  fetchChatSessions,
  renameChatSession,
  streamChatMessage,
  type ChatClarifyDto,
  type ChatQuestionMode,
  type ChatSessionDto,
} from '../api/chat'
import { readSession } from '../auth/session'
import { MODE_LABELS, toChatView, type ChatMessageView } from '../lib/chat'

const SESSION_LS_KEY = 'chat:session'

/** 恢复上次停留的会话，切换页面回来后继续该会话 */
function readStoredSessionId(): number | null {
  try {
    const raw = localStorage.getItem(SESSION_LS_KEY)
    const parsed = raw ? Number(raw) : Number.NaN
    return Number.isInteger(parsed) && parsed > 0 ? parsed : null
  } catch {
    return null
  }
}

/** 会话列表、消息流与发送流程：从页面组件抽离，便于维护与测试 */
export function useChatSession(vendor: string | null) {
  const [messages, setMessages] = useState<ChatMessageView[]>([])
  const [sessions, setSessions] = useState<ChatSessionDto[]>([])
  const [sessionsLoading, setSessionsLoading] = useState(true)
  const [sessionKeyword, setSessionKeyword] = useState('')
  const [activeSessionId, setActiveSessionId] = useState<number | null>(() =>
    readStoredSessionId(),
  )
  const [sending, setSending] = useState(false)
  const [chatError, setChatError] = useState<string | null>(null)
  const [intentNotice, setIntentNotice] = useState<string | null>(null)
  const [clarify, setClarify] = useState<ChatClarifyDto | null>(null)
  const [lastMode, setLastMode] = useState<ChatQuestionMode>('unknown')
  // 新会话在流结束后才切换 activeSessionId，避免加载详情覆盖正在渲染的消息
  const skipFetchRef = useRef(false)

  useEffect(() => {
    let cancelled = false
    const keyword = sessionKeyword.trim()
    // 输入停顿后再请求，避免逐字触发数据库模糊查询
    const timer = window.setTimeout(
      () => {
        setSessionsLoading(true)
        fetchChatSessions(keyword || undefined)
          .then((items) => {
            if (!cancelled) {
              setSessions(items)
              setChatError(null)
            }
          })
          .catch(() => {
            // 401 时 client 已清理登录态并跳转登录页，这里不再提示加载失败
            if (!cancelled && readSession()) setChatError('会话列表加载失败')
          })
          .finally(() => {
            if (!cancelled) setSessionsLoading(false)
          })
      },
      keyword ? 300 : 0,
    )
    return () => {
      cancelled = true
      window.clearTimeout(timer)
    }
  }, [sessionKeyword])

  useEffect(() => {
    try {
      if (activeSessionId) {
        localStorage.setItem(SESSION_LS_KEY, String(activeSessionId))
      } else {
        localStorage.removeItem(SESSION_LS_KEY)
      }
    } catch {
      // 隐私模式 / 配额满等场景下静默跳过
    }
  }, [activeSessionId])

  useEffect(() => {
    if (activeSessionId === null) return
    if (skipFetchRef.current) {
      skipFetchRef.current = false
      return
    }
    let cancelled = false
    fetchChatSession(activeSessionId)
      .then((detail) => {
        if (!cancelled) setMessages(detail.messages.map(toChatView))
      })
      .catch(() => {
        // 会话已被删除或无权访问，回到新对话状态
        if (!cancelled) {
          setActiveSessionId(null)
          setMessages([])
        }
      })
    return () => {
      cancelled = true
    }
  }, [activeSessionId])

  const handleSend = async (content: string, mode: ChatQuestionMode) => {
    if (sending) return
    const optimisticUserMessage: ChatMessageView = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content,
    }
    const pendingId = `pending-${Date.now()}`
    const requestId =
      typeof crypto !== 'undefined' && 'randomUUID' in crypto
        ? crypto.randomUUID()
        : `req-${Date.now()}-${Math.random().toString(16).slice(2)}`
    let assistantId = pendingId
    let newSessionId: number | null = null
    let finished = false

    setMessages((current) => [
      ...current,
      optimisticUserMessage,
      {
        id: pendingId,
        role: 'assistant',
        content: '',
        pending: true,
        streaming: false,
        requestId,
      },
    ])
    setSending(true)
    setChatError(null)
    setClarify(null)
    setIntentNotice(null)
    setLastMode(mode)

    try {
      await streamChatMessage(
        { session_id: activeSessionId, content, mode, vendor },
        requestId,
        {
          onMeta: (meta) => {
            newSessionId = meta.session_id
            assistantId = `db-${meta.assistant_message_id}`
            setMessages((current) =>
              current.map((item) =>
                item.id === pendingId
                  ? {
                      ...item,
                      id: assistantId,
                      dbId: meta.assistant_message_id,
                      pending: false,
                      streaming: true,
                      mode: meta.intent,
                      content: '',
                    }
                  : item,
              ),
            )
            if (
              meta.intent !== mode &&
              mode !== 'unknown' &&
              meta.intent !== 'out_of_scope'
            ) {
              setIntentNotice(
                `已按「${MODE_LABELS[meta.intent] ?? meta.intent}」处理`,
              )
            }
          },
          onStage: (stage) => {
            setMessages((current) =>
              current.map((item) =>
                item.id === assistantId ? { ...item, stage } : item,
              ),
            )
          },
          onDelta: (text) => {
            setMessages((current) =>
              current.map((item) =>
                item.id === assistantId
                  ? {
                      ...item,
                      content: item.content + text,
                      pending: false,
                      streaming: true,
                    }
                  : item,
              ),
            )
          },
          onResult: (data) => {
            setMessages((current) =>
              current.map((item) =>
                item.id === assistantId
                  ? { ...item, content: data.content ?? '' }
                  : item,
              ),
            )
          },
          onCitations: (citations) => {
            setMessages((current) =>
              current.map((item) =>
                item.id === assistantId
                  ? {
                      ...item,
                      citations,
                      evidenced: citations.length > 0,
                    }
                  : item,
              ),
            )
          },
          onDone: (data) => {
            finished = true
            setMessages((current) =>
              current.map((item) =>
                item.id === assistantId
                  ? {
                      ...item,
                      dbId: data.assistant_message_id,
                      streaming: false,
                      stage: undefined,
                      pending: false,
                      clarifying: data.status === 'clarifying',
                    }
                  : item,
              ),
            )
            setClarify(data.clarify ?? null)
          },
          onError: (data) => {
            setChatError(data.message)
          },
        },
      )

      if (!finished) {
        setMessages((current) =>
          current.map((item) =>
            item.id === assistantId
              ? { ...item, streaming: false, stage: undefined }
              : item,
          ),
        )
        setChatError('连接中断，回答可能不完整')
      }
      if (newSessionId && newSessionId !== activeSessionId) {
        skipFetchRef.current = true
        setActiveSessionId(newSessionId)
      }
      fetchChatSessions()
        .then((items) => setSessions(items))
        .catch(() => undefined)
    } catch (error) {
      // 保留已生成的部分内容；仅在没有任何内容时移除占位
      setMessages((current) =>
        current
          .map((item) =>
            item.id === assistantId
              ? { ...item, streaming: false, stage: undefined, pending: false }
              : item,
          )
          .filter((item) => item.id !== assistantId || item.content.length > 0),
      )
      setChatError(error instanceof Error ? error.message : '发送失败')
    } finally {
      setSending(false)
    }
  }

  const handleSelectSession = (sessionId: number) => {
    if (sending || sessionId === activeSessionId) return
    setChatError(null)
    setClarify(null)
    setIntentNotice(null)
    setActiveSessionId(sessionId)
  }

  const handleNewSession = () => {
    setActiveSessionId(null)
    setMessages([])
    setChatError(null)
    setClarify(null)
    setIntentNotice(null)
    // 厂商上下文与具体会话无关，新对话沿用当前选择
  }

  const handleRenameSession = async (sessionId: number, title: string) => {
    try {
      const updated = await renameChatSession(sessionId, title)
      setSessions((current) =>
        current.map((item) => (item.id === updated.id ? updated : item)),
      )
      setChatError(null)
    } catch (error) {
      setChatError(error instanceof Error ? error.message : '重命名会话失败')
    }
  }

  const handleDeleteSession = async (sessionId: number) => {
    try {
      await deleteChatSession(sessionId)
      setSessions((current) => current.filter((item) => item.id !== sessionId))
      if (sessionId === activeSessionId) {
        setActiveSessionId(null)
        setMessages([])
      }
      setChatError(null)
    } catch (error) {
      setChatError(error instanceof Error ? error.message : '删除会话失败')
    }
  }

  return {
    messages,
    sessions,
    sessionsLoading,
    sessionKeyword,
    setSessionKeyword,
    activeSessionId,
    sending,
    chatError,
    intentNotice,
    clarify,
    lastMode,
    handleSend,
    handleSelectSession,
    handleNewSession,
    handleRenameSession,
    handleDeleteSession,
  }
}
