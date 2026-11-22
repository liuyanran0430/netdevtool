import {
  AimOutlined,
  ArrowUpOutlined,
  BookOutlined,
  BulbOutlined,
  CloseOutlined,
  CodeOutlined,
  CommentOutlined,
  CopyOutlined,
  DislikeFilled,
  DislikeOutlined,
  EllipsisOutlined,
  ExclamationCircleOutlined,
  FileTextOutlined,
  InfoCircleOutlined,
  LikeFilled,
  LikeOutlined,
  PlusOutlined,
  SafetyCertificateOutlined,
  ScanOutlined,
  SearchOutlined,
  ToolOutlined,
  UserOutlined,
} from '@ant-design/icons'
import { Dropdown, Input, message, Modal, Popover, Select } from 'antd'
import { useEffect, useRef, useState, type ReactNode } from 'react'
import { useLocation } from 'react-router-dom'
import { MarkdownContent } from '../components/Markdown'
import { PageHeader } from '../components/PageHeader'
import {
  fetchChatProgress,
  setChatMessageFeedback,
  type ChatQuestionMode,
  type ChatSessionDto,
} from '../api/chat'
import { fetchDevices } from '../api/devices'
import { fetchKnowledgeStatus } from '../api/knowledge'
import { useChatSession } from '../hooks/useChatSession'
import type { ChatMessageView } from '../lib/chat'
import type { ChatCitationDto } from '../api/chat'

const VENDOR_LS_KEY = 'chat:vendor'
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

interface TroubleshootData {
  hypotheses: Array<{ cause: string; confidence: number; evidence_refs?: string[] }>
  steps: Array<{ action: string; command?: string | null; pass_criteria?: string | null }>
  solutions: Array<{ action: string; risk?: string | null }>
  summary: string
}

function tryParseTroubleshoot(content: string): TroubleshootData | null {
  try {
    const parsed = JSON.parse(content)
    if (
      parsed &&
      typeof parsed === 'object' &&
      Array.isArray(parsed.hypotheses) &&
      typeof parsed.summary === 'string'
    ) {
      return parsed as TroubleshootData
    }
  } catch {
    // 不是合法 JSON 或结构不符，走纯文本渲染
  }
  return null
}

function Section({
  icon,
  title,
  count,
  children,
}: {
  icon: ReactNode
  title: string
  count: number
  children: ReactNode
}) {
  return (
    <div>
      <div className="mb-2.5 flex items-center gap-1.5">
        <span className="inline-flex text-[12px] text-brand-strong">{icon}</span>
        <span className="text-[12px] font-bold text-ink-700">{title}</span>
        <span className="rounded-full bg-soft px-1.5 py-[1px] text-[10px] font-medium text-ink-400">
          {count}
        </span>
      </div>
      {children}
    </div>
  )
}

/** 多行命令统一成单行展示：换行替换为英文分号 */
function formatCommand(command: string): string {
  return command
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .join(';')
}

function TroubleshootCard({ data }: { data: TroubleshootData }) {
  return (
    <div className="overflow-hidden rounded-lg border border-line bg-white">
      {/* 标题栏 */}
      <div className="flex items-center gap-2 border-b border-line bg-brand-soft/40 px-4 py-2.5">
        <ScanOutlined className="text-[14px] text-brand-strong" />
        <span className="text-[14px] font-bold text-brand-strong">故障排查表</span>
      </div>

      <div className="space-y-5 p-4">
        {/* 可能原因 */}
        {data.hypotheses.length > 0 ? (
          <Section icon={<BulbOutlined />} title="可能原因" count={data.hypotheses.length}>
            <ol className="divide-y divide-line/70 overflow-hidden rounded-lg border border-line/70 bg-soft/40">
              {data.hypotheses.map((item, idx) => (
                <li key={idx} className="flex items-start gap-2.5 px-3 py-2">
                  <span className="mt-[2px] inline-flex h-[18px] min-w-[18px] shrink-0 items-center justify-center rounded-md bg-brand-strong/10 px-1 text-[11px] font-bold text-brand-strong">
                    {idx + 1}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="text-[13px] leading-[1.65] text-ink-900">{item.cause}</p>
                  </div>
                </li>
              ))}
            </ol>
          </Section>
        ) : null}

        {/* 诊断步骤 */}
        {data.steps.length > 0 ? (
          <Section icon={<ToolOutlined />} title="诊断步骤" count={data.steps.length}>
            <ol className="space-y-2">
              {data.steps.map((item, idx) => (
                <li key={idx} className="rounded-lg border border-line/70 px-3 py-2">
                  <div className="flex items-start gap-2.5">
                    <span className="mt-[2px] inline-flex h-[18px] min-w-[18px] shrink-0 items-center justify-center rounded-full bg-soft px-1 text-[11px] font-bold text-ink-500">
                      {idx + 1}
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="break-words text-[13px] leading-[1.65] text-ink-900">
                        {item.action}
                      </p>
                      {item.command || item.pass_criteria ? (
                        <div className="mt-1.5 flex flex-wrap items-center gap-2">
                          {item.command ? (
                            <code className="rounded-md bg-[#f5f6f8] px-2 py-0.5 font-mono text-[11px] text-brand-strong">
                              {formatCommand(item.command)}
                            </code>
                          ) : null}
                          {item.pass_criteria ? (
                            <span className="inline-flex items-center gap-1 text-[11px] text-success">
                              <AimOutlined className="text-[10px]" />
                              通过标准：{item.pass_criteria}
                            </span>
                          ) : null}
                        </div>
                      ) : null}
                    </div>
                  </div>
                </li>
              ))}
            </ol>
          </Section>
        ) : null}

        {/* 解决方案 */}
        {data.solutions.length > 0 ? (
          <Section icon={<SafetyCertificateOutlined />} title="解决方案" count={data.solutions.length}>
            <ul className="divide-y divide-success/15 overflow-hidden rounded-lg border border-success/15 bg-success/5">
              {data.solutions.map((item, idx) => (
                <li key={idx} className="flex items-start gap-2.5 px-3 py-2">
                  <SafetyCertificateOutlined className="mt-[3px] shrink-0 text-[12px] text-success" />
                  <div className="min-w-0 flex-1">
                    <p className="break-words text-[13px] leading-[1.65] text-ink-900">
                      {item.action}
                      {item.risk ? (
                        <span className="ml-2 inline-flex items-center gap-1 text-[11px] text-warn">
                          <ExclamationCircleOutlined className="text-[10px]" />
                          风险：{item.risk}
                        </span>
                      ) : null}
                    </p>
                  </div>
                </li>
              ))}
            </ul>
          </Section>
        ) : null}
      </div>

      {/* 执行提示 */}
      <div className="flex items-start gap-1.5 border-t border-line bg-soft px-4 py-2.5 text-[11px] leading-[1.6] text-ink-400">
        <InfoCircleOutlined className="mt-0.5 shrink-0 text-[11px]" />
        <span>建议先执行只读诊断命令；修改配置前，请备份并确认业务影响。</span>
      </div>
    </div>
  )
}

const STAGE_LABELS: Record<string, string> = {
  intent: '正在识别问题意图…',
  retrieval: '正在检索知识库…',
  tool: '正在补查手册…',
  generation: '正在生成回答…',
}

function PendingReply({ requestId }: { requestId?: string }) {
  const [elapsed, setElapsed] = useState(0)
  const [stage, setStage] = useState<string | null>(null)

  useEffect(() => {
    const timer = window.setInterval(() => setElapsed((value) => value + 1), 1000)
    return () => window.clearInterval(timer)
  }, [])

  // 轮询后端记录的真实处理阶段，避免用固定时长猜测
  useEffect(() => {
    if (!requestId) return
    let cancelled = false
    const tick = () => {
      fetchChatProgress(requestId)
        .then((value) => {
          if (!cancelled && value) setStage(value)
        })
        .catch(() => undefined)
    }
    tick()
    const timer = window.setInterval(tick, 1000)
    return () => {
      cancelled = true
      window.clearInterval(timer)
    }
  }, [requestId])

  const label = (stage && STAGE_LABELS[stage]) ?? '正在处理…'

  return (
    <div className="rounded-lg border border-brand-line bg-brand-soft/40 px-3 py-2.5">
      <div className="flex items-center gap-2 text-[13px] text-ink-700">
        <span className="flex items-center gap-1">
          <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-brand-strong" />
          <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-brand-strong [animation-delay:150ms]" />
          <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-brand-strong [animation-delay:300ms]" />
        </span>
        <span>{label}</span>
        <span className="text-[11px] text-ink-400">已等待 {elapsed} 秒</span>
      </div>
      {elapsed >= 30 ? (
        <p className="mt-1.5 text-[11px] text-ink-400">
          仍在生成，请耐心等待，不要重复提交。
        </p>
      ) : null}
    </div>
  )
}

function citationLabel(fileName?: string | null, snippet?: string | null): string {
  const base = (fileName ?? '文档').replace(/\.[^.]+$/, '')
  const heading = snippet
    ?.split('\n')
    .map((line) => line.trim())
    .find((line) => /^#{1,6}\s+\S/.test(line))
  if (!heading) return base
  const title = heading.replace(/^#{1,6}\s+/, '').trim()
  return `${base}·${title}`
}

/** 历史消息里可能存有重复引用，展示前按片段文本去重 */
function dedupeCitations(citations: ChatCitationDto[]): ChatCitationDto[] {
  const seen = new Set<string>()
  return citations.filter((item) => {
    const text = (item.snippet ?? '').replace(/\s+/g, ' ').trim()
    const key =
      text.length >= 20
        ? `text:${text}`
        : `doc:${item.doc_id ?? ''}:${item.file_name ?? ''}`
    if (seen.has(key)) return false
    seen.add(key)
    return true
  })
}

/** 复制时使用的纯文本：故障排查的结构化 JSON 转成可读文本 */
function answerPlainText(message: ChatMessageView): string {
  if (message.mode !== 'troubleshoot') return message.content
  const data = tryParseTroubleshoot(message.content)
  if (!data) return message.content
  const lines: string[] = [data.summary]
  if (data.hypotheses.length > 0) {
    lines.push('', '可能原因：')
    data.hypotheses.forEach((item, index) => {
      lines.push(`${index + 1}. ${item.cause}`)
    })
  }
  if (data.steps.length > 0) {
    lines.push('', '诊断步骤：')
    data.steps.forEach((item, index) => {
      const extra = [
        item.command ? `命令：${formatCommand(item.command)}` : '',
        item.pass_criteria ? `通过标准：${item.pass_criteria}` : '',
      ]
        .filter(Boolean)
        .join('；')
      lines.push(`${index + 1}. ${item.action}${extra ? `（${extra}）` : ''}`)
    })
  }
  if (data.solutions.length > 0) {
    lines.push('', '解决方案：')
    data.solutions.forEach((item, index) => {
      lines.push(
        `${index + 1}. ${item.action}${item.risk ? `（风险：${item.risk}）` : ''}`,
      )
    })
  }
  return lines.join('\n')
}

/** 点踩原因预设，选择后可继续补充说明 */
const DISLIKE_REASONS = ['答非所问', '内容不准确', '步骤无法执行', '内容不完整']

function MessageActions({
  messageId,
  text,
  initialFeedback,
}: {
  messageId?: number
  text: string
  initialFeedback?: 1 | -1 | null
}) {
  const [copied, setCopied] = useState(false)
  const [feedback, setFeedback] = useState<1 | -1 | null>(initialFeedback ?? null)
  const [reasonOpen, setReasonOpen] = useState(false)
  const [reason, setReason] = useState('')
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (!copied) return
    const timer = window.setTimeout(() => setCopied(false), 1500)
    return () => window.clearTimeout(timer)
  }, [copied])

  const copy = () => {
    navigator.clipboard?.writeText(text).then(
      () => setCopied(true),
      () => undefined,
    )
  }

  const submit = (rating: 1 | -1 | 0, reasonText?: string) => {
    if (!messageId || submitting) return
    const previous = feedback
    setFeedback(rating === 0 ? null : rating)
    setSubmitting(true)
    setChatMessageFeedback(messageId, rating, reasonText)
      .catch((error: unknown) => {
        setFeedback(previous)
        message.error(error instanceof Error ? error.message : '提交反馈失败')
      })
      .finally(() => setSubmitting(false))
  }

  const confirmDislike = () => {
    const value = reason.trim()
    if (!value) {
      message.warning('请填写点踩原因')
      return
    }
    setReasonOpen(false)
    submit(-1, value)
  }

  const buttonClass =
    'inline-flex h-7 items-center gap-1 rounded-md px-1.5 text-ink-400 transition-colors hover:bg-soft hover:text-ink-700 disabled:cursor-not-allowed disabled:opacity-50'

  return (
    <div className="mt-2.5 flex items-center gap-1 text-[12px]">
      <button type="button" onClick={copy} className={buttonClass}>
        <CopyOutlined className="text-[13px]" />
        {copied ? '已复制' : '复制'}
      </button>
      <span className="mx-1 h-3.5 w-px bg-line" />
      <button
        type="button"
        aria-label="有帮助"
        aria-pressed={feedback === 1}
        disabled={!messageId || submitting}
        onClick={() => submit(feedback === 1 ? 0 : 1)}
        className={`${buttonClass} ${feedback === 1 ? 'bg-brand-soft text-brand-strong' : ''}`}
      >
        {feedback === 1 ? (
          <LikeFilled className="text-[14px]" />
        ) : (
          <LikeOutlined className="text-[14px]" />
        )}
      </button>
      <Popover
        open={reasonOpen}
        onOpenChange={(open) => {
          if (open && feedback === -1) return
          setReason('')
          setReasonOpen(open)
        }}
        trigger="click"
        placement="top"
        content={
          <div className="w-[280px]">
            <span className="block text-[12px] font-bold text-ink-700">
              请选择点踩原因
            </span>
            <p className="mt-0.5 text-[11px] text-ink-400">
              可点选预设原因，也可以自行填写
            </p>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {DISLIKE_REASONS.map((option) => (
                <button
                  key={option}
                  type="button"
                  onClick={() => setReason(option)}
                  className={`rounded-md border px-2 py-1 text-[11px] transition-colors ${
                    reason === option
                      ? 'border-brand-line bg-brand-soft text-brand-strong'
                      : 'border-line text-ink-500 hover:border-brand-line hover:text-brand-strong'
                  }`}
                >
                  {option}
                </button>
              ))}
            </div>
            <Input.TextArea
              value={reason}
              onChange={(event) => setReason(event.target.value)}
              placeholder="补充说明（必填，最多 100 字）"
              autoSize={{ minRows: 2, maxRows: 3 }}
              maxLength={100}
              className="mt-2 text-[12px]"
            />
            <div className="mt-2 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setReasonOpen(false)}
                className="h-7 rounded-md border border-line px-2.5 text-[12px] text-ink-500 transition-colors hover:text-ink-700"
              >
                取消
              </button>
              <button
                type="button"
                onClick={confirmDislike}
                disabled={submitting}
                className="h-7 rounded-md bg-brand px-2.5 text-[12px] font-medium text-white transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
              >
                提交
              </button>
            </div>
          </div>
        }
      >
        <button
          type="button"
          aria-label="没有帮助"
          aria-pressed={feedback === -1}
          disabled={!messageId || submitting}
          onClick={() => {
            if (feedback === -1) {
              setReasonOpen(false)
              submit(0)
            }
          }}
          className={`${buttonClass} ${feedback === -1 ? 'bg-brand-soft text-brand-strong' : ''}`}
        >
          {feedback === -1 ? (
            <DislikeFilled className="text-[14px]" />
          ) : (
            <DislikeOutlined className="text-[14px]" />
          )}
        </button>
      </Popover>
    </div>
  )
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
              <div className="mb-1 flex items-center gap-2">
                <span className="text-[13px] font-bold text-ink-900">网络知识助手</span>
                {message.evidenced ? (
                  <span className="inline-flex items-center rounded-full bg-success/10 px-2 py-0.5 text-[11px] font-medium text-success">
                    知识库增强
                  </span>
                ) : null}
              </div>
              {message.pending || (message.streaming && !message.content) ? (
                <PendingReply requestId={message.requestId} />
              ) : message.clarifying ? (
                <div className="rounded-lg border border-brand-line bg-brand-soft/60 px-3 py-2">
                  <span className="mb-1 flex items-center gap-1 text-[11px] font-bold text-brand-strong">
                    <InfoCircleOutlined />
                    需要补充信息
                  </span>
                  <p className="whitespace-pre-wrap text-[13px] leading-[1.7] text-ink-900">
                    {message.content}
                  </p>
                </div>
              ) : message.mode === 'troubleshoot' ? (
                (() => {
                  const data = tryParseTroubleshoot(message.content)
                  if (data)
                    return (
                      <div className="space-y-2">
                        <p className="whitespace-pre-wrap text-[14px] leading-[1.7] text-ink-900">
                          {data.summary}
                        </p>
                        <TroubleshootCard data={data} />
                      </div>
                    )
                  // 兜底：不是合法 JSON，按普通文本渲染
                  return (
                    <p className="whitespace-pre-wrap text-[14px] leading-[1.7] text-ink-900">
                      {message.content}
                    </p>
                  )
                })()
              ) : message.mode === 'command' || message.mode === 'knowledge' ? (
                <div className="rounded-lg border border-line bg-white px-3.5 py-3">
                  <MarkdownContent content={message.content} variant="answer" />
                </div>
              ) : (
                <p className="whitespace-pre-wrap text-[14px] leading-[1.7] text-ink-900">
                  {message.content}
                </p>
              )}

              {message.streaming ? (
                <div className="mt-1.5 flex items-center gap-1.5 text-[11px] text-ink-400">
                  <span className="inline-block h-3 w-1 animate-pulse bg-brand-strong" />
                  <span>
                    {message.stage
                      ? STAGE_LABELS[message.stage] ?? '正在生成回答…'
                      : '正在生成回答…'}
                  </span>
                </div>
              ) : null}

              {message.citations && message.citations.length > 0 ? (
                <div className="mt-2.5 flex flex-wrap items-center gap-2">
                  <span className="text-[11px] text-ink-400">参考来源</span>
                  {dedupeCitations(message.citations).map((citation, index) => (
                    <span
                      key={`${citation.doc_id ?? 'doc'}-${index}`}
                      className="inline-flex max-w-[280px] items-center gap-1 rounded-md border border-line bg-white px-2 py-1 text-[11px] text-ink-500"
                    >
                      <FileTextOutlined className="shrink-0 text-[11px]" />
                      <span className="truncate">
                        {citationLabel(citation.file_name, citation.snippet)}
                      </span>
                      <Popover
                        trigger="click"
                        placement="top"
                        content={
                          <div className="-m-3 w-[420px] max-w-[80vw] overflow-hidden rounded-lg bg-white">
                            <div className="flex items-center gap-2 border-b border-line bg-brand-soft/50 px-3 py-2">
                              <FileTextOutlined className="shrink-0 text-[12px] text-brand-strong" />
                              <span className="min-w-0 flex-1 truncate text-[12px] font-bold text-ink-900">
                                {citation.file_name ?? `文档 #${citation.doc_id ?? '-'}`}
                              </span>
                              <span className="shrink-0 rounded-full bg-white px-2 py-0.5 text-[10px] text-ink-400">
                                相关度 {Math.round((citation.score ?? 0) * 100)}%
                              </span>
                            </div>
                            <div className="thin-scrollbar max-h-[300px] overflow-y-auto whitespace-pre-wrap px-3 py-2.5 text-[12px] leading-[1.75] text-ink-700">
                              {citation.snippet ?? '暂无片段内容'}
                            </div>
                          </div>
                        }
                      >
                        <button
                          type="button"
                          aria-label="查看引用片段"
                          className="shrink-0 rounded p-0.5 text-ink-400 transition-colors hover:bg-brand-soft hover:text-brand-strong"
                        >
                          <ArrowUpOutlined rotate={45} className="text-[11px]" />
                        </button>
                      </Popover>
                    </span>
                  ))}
                </div>
              ) : null}

              {message.pending || message.clarifying || message.streaming ? null : (
                <MessageActions
                  messageId={message.dbId}
                  initialFeedback={message.feedback}
                  text={answerPlainText(message)}
                />
              )}
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
  const messageListRef = useRef<HTMLDivElement | null>(null)
  const {
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
  } = useChatSession(vendor || null)

  // 消息变化或进入等待态时保持滚动到底部
  useEffect(() => {
    const node = messageListRef.current
    if (node) node.scrollTop = node.scrollHeight
  }, [messages, sending])

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

          {intentNotice ? (
            <div className="px-6 pb-2 text-[11px] text-ink-400 lg:px-12">
              {intentNotice}
            </div>
          ) : null}

          {clarify && clarify.options.length > 0 ? (
            <div className="px-6 pb-2 lg:px-12">
              <div className="flex flex-wrap items-center gap-2 rounded-lg border border-brand-line bg-brand-soft/50 px-3 py-2">
                <span className="text-[12px] text-ink-500">快速选择：</span>
                {clarify.options.map((option) => (
                  <button
                    key={option}
                    type="button"
                    disabled={sending}
                    onClick={() => void handleSend(option, lastMode)}
                    className="rounded-full border border-brand-line bg-white px-3 py-1 text-[12px] text-brand-strong transition-colors hover:border-brand disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {option}
                  </button>
                ))}
              </div>
            </div>
          ) : null}

          <ChatInput onSend={handleSend} sending={sending} />
        </div>
      </div>
    </div>
  )
}
