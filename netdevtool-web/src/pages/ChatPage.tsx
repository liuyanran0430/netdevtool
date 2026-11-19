import {
  ArrowUpOutlined,
  BookOutlined,
  CloseOutlined,
  CodeOutlined,
  CommentOutlined,
  EllipsisOutlined,
  InfoCircleOutlined,
  PlusOutlined,
  SafetyCertificateOutlined,
  ScanOutlined,
  SearchOutlined,
  UserOutlined,
} from '@ant-design/icons'
import { Dropdown, Input, Modal, Select } from 'antd'
import { useEffect, useRef, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { PageHeader } from '../components/PageHeader'
import {
  deleteChatSession,
  fetchChatSession,
  fetchChatSessions,
  renameChatSession,
  sendChatMessage,
  type ChatMessageDto,
  type ChatQuestionMode,
  type ChatSessionDto,
} from '../api/chat'
import { fetchDevices } from '../api/devices'
import { fetchKnowledgeStatus } from '../api/knowledge'

const VENDOR_LS_KEY = 'chat:vendor'
const SESSION_LS_KEY = 'chat:session'
/** 不限厂商：检索与问答不按厂商收窄，数据库按 all 保存 */
const ANY_VENDOR = 'all'

const QUESTION_MODES = [
  {
    id: 'command',
    label: '命令检索',
    icon: <CodeOutlined className="text-[12px]" />,
    hint: '已开启命令检索，请输入命令或对应功能进行查询',
  },
  {
    id: 'troubleshoot',
    label: '故障排查',
    icon: <ScanOutlined className="text-[12px]" />,
    hint: '已开启故障排查，请粘贴报错信息或现象描述',
  },
  {
    id: 'knowledge',
    label: '知识提问',
    icon: <BookOutlined className="text-[12px]" />,
    hint: '已开启知识提问，请输入要提问的网络知识',
  },
]

type KnowledgeStatus = 'checking' | 'connected' | 'empty' | 'disconnected'

const KNOWLEDGE_STATUS_META: Record<
  KnowledgeStatus,
  { dot: string; text: string; desc: string }
> = {
  checking: {
    dot: 'bg-ink-300',
    text: '正在检测知识库连接',
    desc: '正在检查知识库服务状态',
  },
  connected: {
    dot: 'bg-success',
    text: '企业知识库已连接',
    desc: '回答基于设备手册与运维知识',
  },
  empty: {
    dot: 'bg-warn',
    text: '知识库暂无可用文档',
    desc: '请先在知识库中上传并完成索引',
  },
  disconnected: {
    dot: 'bg-danger',
    text: '企业知识库未连接',
    desc: '知识库服务不可用，请检查后端服务',
  },
}

function readStoredVendor(): string {
  try {
    return localStorage.getItem(VENDOR_LS_KEY) ?? ''
  } catch {
    return ''
  }
}

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

/** 会话时间显示：今天 / 昨天 / M月D日 / YYYY/M/D */
function formatSessionTime(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  const now = new Date()
  const startOfDay = (item: Date) =>
    new Date(item.getFullYear(), item.getMonth(), item.getDate()).getTime()
  const diffDays = Math.round((startOfDay(now) - startOfDay(date)) / 86_400_000)
  if (diffDays <= 0) return '今天'
  if (diffDays === 1) return '昨天'
  if (date.getFullYear() === now.getFullYear()) {
    return `${date.getMonth() + 1}月${date.getDate()}日`
  }
  return `${date.getFullYear()}/${date.getMonth() + 1}/${date.getDate()}`
}

function ContextSelect({
  label,
  value,
  options,
  loading = false,
  onChange,
}: {
  label: string
  value: string
  options: { value: string; label: string }[]
  loading?: boolean
  onChange: (value: string) => void
}) {
  return (
    <div className="flex h-9 items-center gap-1 rounded-lg border border-line bg-white pl-3 pr-1.5 text-[13px] text-ink-500">
      <span className="whitespace-nowrap">{label}</span>
      <Select
        value={value || undefined}
        onChange={onChange}
        options={options}
        loading={loading}
        placeholder="暂无厂商"
        variant="borderless"
        popupMatchSelectWidth={false}
        className="min-w-[76px] text-[13px] font-medium"
      />
    </div>
  )
}

function SessionHistory({
  className = '',
  kbStatus,
  kbDetail,
  sessions,
  activeSessionId,
  loading,
  onSelect,
  onNew,
  onRename,
  onDelete,
  keyword,
  onKeywordChange,
}: {
  className?: string
  kbStatus: KnowledgeStatus
  kbDetail: string | null
  sessions: ChatSessionDto[]
  activeSessionId: number | null
  loading: boolean
  onSelect: (sessionId: number) => void
  onNew: () => void
  onRename: (sessionId: number, title: string) => Promise<void>
  onDelete: (sessionId: number) => Promise<void>
  keyword: string
  onKeywordChange: (value: string) => void
}) {
  const knowledgeMeta = KNOWLEDGE_STATUS_META[kbStatus]
  const [renameTarget, setRenameTarget] = useState<ChatSessionDto | null>(null)
  const [renameValue, setRenameValue] = useState('')
  const [deleteTarget, setDeleteTarget] = useState<ChatSessionDto | null>(null)
  const [searchOpen, setSearchOpen] = useState(false)
  const searching = keyword.trim().length > 0

  const openRename = (session: ChatSessionDto) => {
    setRenameTarget(session)
    setRenameValue(session.title)
  }

  const submitRename = () => {
    const target = renameTarget
    const title = renameValue.trim()
    setRenameTarget(null)
    if (!target || !title || title === target.title) return
    void onRename(target.id, title)
  }

  const submitDelete = () => {
    const target = deleteTarget
    setDeleteTarget(null)
    if (!target) return
    void onDelete(target.id)
  }

  return (
    <div
      className={`flex flex-col gap-6 bg-soft px-4 pb-[22px] pt-[26px] ${className}`}
    >
      <div className="flex items-center justify-between px-1">
        <div className="flex items-center gap-2">
          <span className="text-[14px] font-bold text-ink-900">会话历史</span>
          <span className="text-[11px] text-ink-400">{sessions.length}</span>
        </div>
        <button
          type="button"
          aria-label={searchOpen ? '关闭搜索' : '搜索会话'}
          aria-expanded={searchOpen}
          onClick={() => {
            setSearchOpen((current) => !current)
            onKeywordChange('')
          }}
          className={`text-[15px] transition-colors ${
            searchOpen ? 'text-brand-strong' : 'text-ink-400 hover:text-ink-500'
          }`}
        >
          <SearchOutlined />
        </button>
      </div>

      {searchOpen ? (
        <Input
          autoFocus
          allowClear
          size="small"
          value={keyword}
          placeholder="搜索会话消息内容"
          prefix={<SearchOutlined className="text-[12px] text-ink-400" />}
          onChange={(event) => onKeywordChange(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Escape') {
              setSearchOpen(false)
              onKeywordChange('')
            }
          }}
        />
      ) : null}

      <div className="thin-scrollbar flex min-h-0 flex-1 flex-col gap-2 overflow-y-auto">
        <span className="px-1 text-[11px] text-ink-400">
          {searching ? `搜索结果 ${sessions.length}` : '最近 7 天'}
        </span>
        {sessions.length === 0 ? (
          <div className="flex flex-col items-center gap-1 rounded-lg border border-dashed border-line px-4 py-8 text-center">
            {searching ? (
              <SearchOutlined className="text-[16px] text-ink-300" />
            ) : (
              <CommentOutlined className="text-[16px] text-ink-300" />
            )}
            <span className="text-[12px] text-ink-400">
              {loading ? '会话加载中…' : searching ? '没有匹配的会话' : '暂无会话记录'}
            </span>
            <span className="text-[11px] text-ink-400">
              {searching ? '换个关键词试试' : '发起提问后会自动保存'}
            </span>
          </div>
        ) : (
          <div className="flex flex-col gap-1.5">
            {sessions.map((session) => {
              const active = session.id === activeSessionId
              return (
                <div
                  key={session.id}
                  className={`flex items-center gap-1 rounded-[10px] border py-2 pl-2.5 pr-1 transition-colors ${
                    active
                      ? 'border-brand-line bg-brand-soft'
                      : 'border-transparent hover:bg-white'
                  }`}
                >
                  <button
                    type="button"
                    onClick={() => onSelect(session.id)}
                    className="flex min-w-0 flex-1 items-center gap-2.5 text-left"
                  >
                    <CommentOutlined
                      className={`shrink-0 text-[15px] ${
                        active ? 'text-brand' : 'text-ink-400'
                      }`}
                    />
                    <span className="flex min-w-0 flex-1 flex-col gap-0.5">
                      <span
                        className={`truncate text-[13px] ${
                          active
                            ? 'font-bold text-brand-strong'
                            : 'font-medium text-ink-900'
                        }`}
                      >
                        {session.title}
                      </span>
                      <span className="text-[11px] text-ink-400">
                        {formatSessionTime(session.last_message_at ?? session.created_at)}
                      </span>
                    </span>
                  </button>
                  <Dropdown
                    trigger={['click']}
                    menu={{
                      items: [
                        { key: 'rename', label: '重命名' },
                        { key: 'delete', label: '删除', danger: true },
                      ],
                      onClick: ({ key, domEvent }) => {
                        domEvent.stopPropagation()
                        if (key === 'rename') openRename(session)
                        else setDeleteTarget(session)
                      },
                    }}
                  >
                    <button
                      type="button"
                      aria-label={`${session.title} 会话操作`}
                      className="flex h-6 w-6 shrink-0 items-center justify-center rounded text-ink-400 transition-colors hover:bg-white hover:text-ink-500"
                    >
                      <EllipsisOutlined className="text-[14px]" />
                    </button>
                  </Dropdown>
                </div>
              )
            })}
          </div>
        )}
      </div>

      <button
        type="button"
        onClick={onNew}
        className="flex h-[38px] w-full items-center justify-center gap-2 rounded-lg border border-line bg-white text-[13px] text-ink-500"
      >
        <PlusOutlined className="text-[13px]" />
        新对话
      </button>

      <div className="border-t border-line pt-4">
        <div className="flex items-center gap-1.5">
          <span className={`h-1.5 w-1.5 rounded-full ${knowledgeMeta.dot}`} />
          <span className="text-xs text-ink-500">{knowledgeMeta.text}</span>
        </div>
        <p className="mt-2 text-[11px] leading-[1.6] text-ink-400">
          {kbDetail ?? knowledgeMeta.desc}
        </p>
      </div>

      <Modal
        title="重命名会话"
        open={renameTarget !== null}
        onCancel={() => setRenameTarget(null)}
        onOk={submitRename}
        okText="保存"
        cancelText="取消"
        okButtonProps={{ disabled: !renameValue.trim() }}
        destroyOnHidden
      >
        <Input
          value={renameValue}
          onChange={(event) => setRenameValue(event.target.value)}
          onPressEnter={submitRename}
          maxLength={128}
          showCount
          autoFocus
          placeholder="请输入会话名称"
        />
      </Modal>

      <Modal
        title="删除会话"
        open={deleteTarget !== null}
        onCancel={() => setDeleteTarget(null)}
        onOk={submitDelete}
        okText="删除"
        cancelText="取消"
        okButtonProps={{ danger: true }}
      >
        <p className="text-[13px] leading-[1.7] text-ink-500">
          确定删除「{deleteTarget?.title}」吗？删除后该会话将不再显示。
        </p>
      </Modal>
    </div>
  )
}

function RobotAvatar({ size = 88 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 120 120"
      fill="none"
      role="img"
      aria-label="网络知识助手"
    >
      <defs>
        <linearGradient
          id="chat-robot-head"
          x1="30"
          y1="30"
          x2="92"
          y2="94"
          gradientUnits="userSpaceOnUse"
        >
          <stop stopColor="#6E9BF2" />
          <stop offset="1" stopColor="#2D5EBD" />
        </linearGradient>
        <linearGradient
          id="chat-robot-face"
          x1="36"
          y1="44"
          x2="84"
          y2="82"
          gradientUnits="userSpaceOnUse"
        >
          <stop stopColor="#FFFFFF" />
          <stop offset="1" stopColor="#E6EFFF" />
        </linearGradient>
        <linearGradient
          id="chat-robot-ring"
          x1="60"
          y1="8"
          x2="60"
          y2="112"
          gradientUnits="userSpaceOnUse"
        >
          <stop stopColor="#EAF1FF" />
          <stop offset="1" stopColor="#F7FAFF" stopOpacity="0.2" />
        </linearGradient>
      </defs>

      <circle cx="60" cy="62" r="52" fill="url(#chat-robot-ring)" />

      {/* 天线 */}
      <path
        d="M60 30V20"
        stroke="#8FB2F5"
        strokeWidth="4"
        strokeLinecap="round"
      />
      <circle cx="60" cy="15" r="6" fill="#4F86F7" />
      <circle cx="60" cy="15" r="2.4" fill="#FFFFFF" />

      {/* 侧耳 */}
      <rect x="12" y="48" width="10" height="24" rx="5" fill="#8FB2F5" />
      <rect x="98" y="48" width="10" height="24" rx="5" fill="#8FB2F5" />

      {/* 头部 */}
      <rect
        x="22"
        y="30"
        width="76"
        height="62"
        rx="20"
        fill="url(#chat-robot-head)"
      />
      <rect
        x="26"
        y="33"
        width="68"
        height="26"
        rx="14"
        fill="#FFFFFF"
        opacity="0.12"
      />

      {/* 屏幕脸 */}
      <rect
        x="32"
        y="42"
        width="56"
        height="40"
        rx="14"
        fill="url(#chat-robot-face)"
      />

      {/* 眼睛 */}
      <circle cx="48" cy="60" r="5.5" fill="#2D5EBD" />
      <circle cx="72" cy="60" r="5.5" fill="#2D5EBD" />
      <circle cx="49.8" cy="58.2" r="1.8" fill="#FFFFFF" />
      <circle cx="73.8" cy="58.2" r="1.8" fill="#FFFFFF" />

      {/* 微笑 */}
      <path
        d="M52 69.5C54.6 72.4 57.2 73.8 60 73.8C62.8 73.8 65.4 72.4 68 69.5"
        stroke="#2D5EBD"
        strokeWidth="3.6"
        strokeLinecap="round"
      />

      <ellipse cx="60" cy="104" rx="26" ry="5" fill="#DCE7FA" opacity="0.7" />
    </svg>
  )
}

interface ChatMessageView {
  id: string
  role: 'user' | 'assistant'
  content: string
}

function toChatView(message: ChatMessageDto): ChatMessageView {
  return { id: `db-${message.id}`, role: message.role, content: message.content }
}

function ChatMessages({
  messages = [],
}: {
  messages?: ChatMessageView[]
}) {
  if (messages.length === 0) {
    return (
      <div className="flex min-h-[320px] flex-col items-center justify-center gap-3 px-4 text-center">
        <RobotAvatar size={176} />
        <p className="max-w-[360px] text-[12px] leading-[1.7] text-ink-400">
          输入网络配置、故障现象或命令问题，助手会结合企业知识库给出解答与排查建议。
        </p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-6">
      {messages.map((message) =>
        message.role === 'user' ? (
          <div key={message.id} className="flex items-start justify-end gap-3">
            <div className="max-w-[86%] whitespace-pre-wrap rounded-[12px_2px_12px_12px] bg-brand-soft px-4 py-3 text-[14px] leading-6 text-ink-900">
              {message.content}
            </div>
            <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-brand-line bg-white text-brand-strong">
              <UserOutlined className="text-[15px]" />
            </span>
          </div>
        ) : (
          <div key={message.id} className="flex gap-3">
            <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-brand-soft">
              <RobotAvatar size={30} />
            </span>
            <div className="min-w-0 flex-1">
              <div className="mb-1 text-[13px] font-bold text-ink-900">
                网络知识助手
              </div>
              <p className="whitespace-pre-wrap text-[14px] leading-[1.7] text-ink-900">
                {message.content}
              </p>
            </div>
          </div>
        ),
      )}
    </div>
  )
}

function ChatInput({
  onSend,
  sending = false,
}: {
  onSend: (content: string, mode: ChatQuestionMode) => void
  sending?: boolean
}) {
  const [mode, setMode] = useState('unknown')
  const [draft, setDraft] = useState('')
  const activeMode = QUESTION_MODES.find((item) => item.id === mode)
  const canSend = draft.trim().length > 0 && !sending
  const submit = () => {
    const content = draft.trim()
    if (!content || sending) return
    onSend(content, mode as ChatQuestionMode)
    setDraft('')
  }
  return (
    <div className="shrink-0">
      {/* 桌面端固定 200px 输入区 */}
      <div className="hidden h-[200px] flex-col gap-2.5 border-t border-line bg-page px-6 pb-4 pt-3.5 lg:flex">
        {/* 输入框 固定 144px */}
        <div className="flex h-[144px] flex-col justify-between rounded-xl border border-input-border bg-white px-[18px] py-4 shadow-input">
          {activeMode ? (
            <div className="flex h-[18px] items-center gap-1 text-[11px] text-brand-strong">
              <span className="min-w-0 flex-1 truncate">{activeMode.hint}</span>
              <button
                type="button"
                aria-label="关闭检索模式提示"
                onClick={() => setMode('unknown')}
                className="flex h-[16px] w-[16px] shrink-0 items-center justify-center rounded text-ink-400 transition-colors hover:text-brand-strong"
              >
                <CloseOutlined className="text-[10px]" />
              </button>
            </div>
          ) : null}

          <Input.TextArea
            id="chat-question"
            name="question"
            aria-label="输入问题"
            variant="borderless"
            placeholder="输入问题，或粘贴配置/报错信息…"
            autoSize={false}
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            onPressEnter={(event) => {
              if (event.shiftKey) return
              event.preventDefault()
              submit()
            }}
            className="!h-[54px] !min-h-0 resize-none !p-0 !text-[13px] !shadow-none !outline-none placeholder:!text-ink-400 focus:!shadow-none focus:!outline-none focus-visible:!outline-none"
          />

          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-1">
              {QUESTION_MODES.map((item) => {
                const active = item.id === mode
                return (
                  <button
                    type="button"
                    key={item.id}
                    onClick={() =>
                      setMode((current) => (current === item.id ? 'unknown' : item.id))
                    }
                    className={`flex h-[29px] items-center gap-1.5 rounded-md border px-[9px] text-[11px] transition-colors ${
                      active
                        ? 'border-[#CDDCFB] bg-brand-soft text-brand-strong'
                        : 'border-transparent text-ink-500 hover:bg-brand-soft hover:text-brand-strong'
                    }`}
                  >
                    {item.icon}
                    {item.label}
                  </button>
                )
              })}
            </div>

            <button
              type="button"
              onClick={submit}
              disabled={!canSend}
              className="flex h-[34px] items-center gap-2 rounded-lg bg-brand px-[14px] text-[13px] font-medium text-white transition-opacity disabled:cursor-not-allowed disabled:opacity-50"
            >
              发送
              <ArrowUpOutlined className="text-[13px]" />
            </button>
          </div>
        </div>

        {/* 底部提示 */}
        <div className="flex items-center justify-between text-[10px] text-ink-400">
          <span className="flex items-center gap-1.5">
            <SafetyCertificateOutlined className="text-[11px]" />
            配置中的账号、密钥等信息请先脱敏
          </span>
          <span>回答仅供参考，请结合设备实际情况验证</span>
        </div>
      </div>

      {/* 移动端自适应 */}
      <div className="flex flex-col gap-2.5 border-t border-line bg-page px-4 py-3.5 lg:hidden">
        <div className="flex flex-col gap-3 rounded-xl border border-input-border bg-white px-4 py-4 shadow-input">
          {activeMode ? (
            <div className="flex items-center gap-1 bg-transparent text-[11px] text-brand-strong">
              <span className="min-w-0 flex-1 truncate">{activeMode.hint}</span>
              <button
                type="button"
                aria-label="关闭检索模式提示"
                onClick={() => setMode('unknown')}
                className="flex h-[18px] w-[18px] shrink-0 items-center justify-center rounded text-ink-400 transition-colors hover:text-brand-strong"
              >
                <CloseOutlined className="text-[10px]" />
              </button>
            </div>
          ) : null}

          <Input.TextArea
            id="chat-question-mobile"
            name="question-mobile"
            aria-label="输入问题"
            variant="borderless"
            placeholder="输入问题，或粘贴配置/报错信息…"
            autoSize={{ minRows: 2, maxRows: 4 }}
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            onPressEnter={(event) => {
              if (event.shiftKey) return
              event.preventDefault()
              submit()
            }}
            className="!p-0 !text-[14px] !shadow-none !outline-none placeholder:!text-ink-400 focus:!shadow-none focus:!outline-none focus-visible:!outline-none"
          />

          <div className="flex items-center justify-between gap-3">
            <div className="flex flex-wrap items-center gap-1">
              {QUESTION_MODES.map((item) => {
                const active = item.id === mode
                return (
                  <button
                    type="button"
                    key={item.id}
                    onClick={() =>
                      setMode((current) => (current === item.id ? 'unknown' : item.id))
                    }
                    className={`flex h-[29px] items-center gap-1.5 rounded-md border px-2.5 text-xs transition-colors ${
                      active
                        ? 'border-[#CDDCFB] bg-brand-soft text-brand-strong'
                        : 'border-transparent text-ink-500 hover:bg-brand-soft'
                    }`}
                  >
                    {item.icon}
                    {item.label}
                  </button>
                )
              })}
            </div>

            <button
              type="button"
              onClick={submit}
              disabled={!canSend}
              className="flex h-[34px] shrink-0 items-center gap-2 rounded-lg bg-brand px-3.5 text-[13px] font-medium text-white transition-opacity disabled:cursor-not-allowed disabled:opacity-50"
            >
              发送
              <ArrowUpOutlined className="text-[13px]" />
            </button>
          </div>
        </div>

        <div className="flex flex-col gap-1 text-[10px] text-ink-400 sm:flex-row sm:items-center sm:justify-between">
          <span className="flex items-center gap-1.5">
            <SafetyCertificateOutlined className="text-[11px]" />
            配置中的账号、密钥等信息请先脱敏
          </span>
          <span>回答仅供参考，请结合设备实际情况验证</span>
        </div>
      </div>
    </div>
  )
}

export function ChatPage() {
  const location = useLocation()
  const navState = location.state as { fromTranslation?: boolean; vendor?: string } | null
  const fromTranslation = Boolean(navState?.fromTranslation)
  const [vendors, setVendors] = useState<string[]>([])
  // 从翻译任务进入时优先使用任务的目的厂商，其次恢复上次选择
  const [vendor, setVendor] = useState(
    () => navState?.vendor || readStoredVendor() || ANY_VENDOR,
  )
  const [vendorsLoading, setVendorsLoading] = useState(true)
  const [kbStatus, setKbStatus] = useState<KnowledgeStatus>('checking')
  const [kbDetail, setKbDetail] = useState<string | null>(null)
  const [messages, setMessages] = useState<ChatMessageView[]>([])
  const [sessions, setSessions] = useState<ChatSessionDto[]>([])
  const [sessionsLoading, setSessionsLoading] = useState(true)
  const [sessionKeyword, setSessionKeyword] = useState('')
  const [activeSessionId, setActiveSessionId] = useState<number | null>(() =>
    readStoredSessionId(),
  )
  const [sending, setSending] = useState(false)
  const [chatError, setChatError] = useState<string | null>(null)
  const messageListRef = useRef<HTMLDivElement | null>(null)

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
            if (!cancelled) setChatError('会话列表加载失败')
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
    setSending(true)
    setChatError(null)
    try {
      const result = await sendChatMessage({
        session_id: activeSessionId,
        content,
        mode,
        vendor: vendor || null,
      })
      setActiveSessionId(result.session.id)
      setMessages((current) => [
        ...current,
        toChatView(result.user_message),
        toChatView(result.assistant_message),
      ])
      setSessions((current) => [
        result.session,
        ...current.filter((item) => item.id !== result.session.id),
      ])
    } catch (error) {
      setChatError(error instanceof Error ? error.message : '发送失败')
    } finally {
      setSending(false)
    }
  }

  const handleSelectSession = (sessionId: number) => {
    if (sending || sessionId === activeSessionId) return
    setChatError(null)
    setActiveSessionId(sessionId)
  }

  const handleNewSession = () => {
    setActiveSessionId(null)
    setMessages([])
    setChatError(null)
    // 新对话默认不限定厂商
    setVendor(ANY_VENDOR)
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

  useEffect(() => {
    const container = messageListRef.current
    if (!container) return
    container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    let cancelled = false
    fetchKnowledgeStatus()
      .then((status) => {
        if (cancelled) return
        setKbDetail(status.detail)
        if (!status.connected) {
          setKbStatus('disconnected')
        } else if (status.knowledge_bases === 0) {
          setKbStatus('empty')
        } else {
          setKbStatus('connected')
        }
      })
      .catch(() => {
        if (!cancelled) {
          setKbDetail(null)
          setKbStatus('disconnected')
        }
      })
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    let cancelled = false
    fetchDevices()
      .then((devices) => {
        if (cancelled) return
        const unique = [...new Set(devices.map((item) => item.vendor).filter(Boolean))]
        setVendors(unique)
        setVendor((current) =>
          current === ANY_VENDOR || (current && unique.includes(current))
            ? current
            : ANY_VENDOR,
        )
      })
      .catch(() => {
        if (!cancelled) setVendors([])
      })
      .finally(() => {
        if (!cancelled) setVendorsLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    if (!vendor) return
    try {
      localStorage.setItem(VENDOR_LS_KEY, vendor)
    } catch {
      // 隐私模式 / 配额满等场景下静默跳过
    }
  }, [vendor])

  return (
    <div className="flex min-h-full flex-col">
      <PageHeader
        title="智能问答"
        subtitle="网络设备知识助手"
        right={
          <>
            {fromTranslation && (
              <span className="flex h-9 items-center gap-1.5 rounded-lg border border-brand-line bg-brand-soft px-3 text-[12px] font-medium text-brand-strong">
                <InfoCircleOutlined className="text-[13px]" />
                已带入当前翻译任务
              </span>
            )}
            <ContextSelect
              label="厂商上下文："
              value={vendor}
              options={[
                { value: ANY_VENDOR, label: '不限' },
                ...vendors.map((item) => ({ value: item, label: item })),
              ]}
              loading={vendorsLoading}
              onChange={setVendor}
            />
            <button
              type="button"
              onClick={handleNewSession}
              className="flex h-9 items-center gap-2 rounded-lg bg-brand px-4 text-[13px] font-medium text-white"
            >
              新对话
              <PlusOutlined className="text-[12px]" />
            </button>
          </>
        }
      />

      <div className="flex min-h-[calc(100vh_-_80px)] flex-1 lg:h-[calc(100vh_-_80px)] lg:min-h-0 lg:flex-none">
        <SessionHistory
          className="hidden w-[248px] shrink-0 border-r border-line lg:flex"
          kbStatus={kbStatus}
          kbDetail={kbDetail}
          sessions={sessions}
          activeSessionId={activeSessionId}
          loading={sessionsLoading}
          onSelect={handleSelectSession}
          onNew={handleNewSession}
          onRename={handleRenameSession}
          onDelete={handleDeleteSession}
          keyword={sessionKeyword}
          onKeywordChange={setSessionKeyword}
        />

        <div className="flex min-w-0 flex-1 flex-col lg:min-h-0">
          <div
            ref={messageListRef}
            className="thin-scrollbar flex-1 overflow-y-auto px-4 pt-6 lg:min-h-0 lg:px-12"
          >
            <ChatMessages messages={messages} />
          </div>

          {chatError ? (
            <div className="px-6 pb-2 text-[11px] text-danger lg:px-12">
              {chatError}
            </div>
          ) : null}

          <ChatInput onSend={handleSend} sending={sending} />
        </div>
      </div>
    </div>
  )
}
