import {
  ArrowUpOutlined,
  BookOutlined,
  CodeOutlined,
  CommentOutlined,
  InfoCircleOutlined,
  PlusOutlined,
  SafetyCertificateOutlined,
  ScanOutlined,
  SearchOutlined,
} from '@ant-design/icons'
import { Input, Select } from 'antd'
import { useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { PageHeader } from '../components/PageHeader'
import { fetchDevices } from '../api/devices'
import { fetchKnowledgeStatus } from '../api/knowledge'

const VENDOR_LS_KEY = 'chat:vendor'

const QUESTION_MODES = [
  {
    id: 'command',
    label: '命令检索',
    icon: <CodeOutlined className="text-[12px]" />,
  },
  {
    id: 'troubleshoot',
    label: '故障排查',
    icon: <ScanOutlined className="text-[12px]" />,
  },
  {
    id: 'knowledge',
    label: '知识提问',
    icon: <BookOutlined className="text-[12px]" />,
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
}: {
  className?: string
  kbStatus: KnowledgeStatus
  kbDetail: string | null
}) {
  const knowledgeMeta = KNOWLEDGE_STATUS_META[kbStatus]
  return (
    <div
      className={`flex flex-col gap-6 bg-soft px-4 pb-[22px] pt-[26px] ${className}`}
    >
      <div className="flex items-center justify-between px-1">
        <div className="flex items-center gap-2">
          <span className="text-[14px] font-bold text-ink-900">会话历史</span>
          <span className="text-[11px] text-ink-400">0</span>
        </div>
        <button type="button" aria-label="搜索会话" className="text-[15px] text-ink-400">
          <SearchOutlined />
        </button>
      </div>

      <div className="flex flex-col gap-2">
        <span className="px-1 text-[11px] text-ink-400">最近 7 天</span>
        <div className="flex flex-col items-center gap-1 rounded-lg border border-dashed border-line px-4 py-8 text-center">
          <CommentOutlined className="text-[16px] text-ink-300" />
          <span className="text-[12px] text-ink-400">暂无会话记录</span>
          <span className="text-[11px] text-ink-400">发起提问后会自动保存</span>
        </div>
      </div>

      <button
        type="button"
        className="flex h-[38px] w-full items-center justify-center gap-2 rounded-lg border border-line bg-white text-[13px] text-ink-500"
      >
        <PlusOutlined className="text-[13px]" />
        新对话
      </button>

      <div className="flex-1" />

      <div className="border-t border-line pt-4">
        <div className="flex items-center gap-1.5">
          <span className={`h-1.5 w-1.5 rounded-full ${knowledgeMeta.dot}`} />
          <span className="text-xs text-ink-500">{knowledgeMeta.text}</span>
        </div>
        <p className="mt-2 text-[11px] leading-[1.6] text-ink-400">
          {kbDetail ?? knowledgeMeta.desc}
        </p>
      </div>
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
          <div key={message.id} className="flex flex-col items-end gap-2">
            <div className="max-w-[86%] rounded-[12px_2px_12px_12px] bg-brand-soft px-4 py-3 text-[14px] leading-6 text-ink-900">
              {message.content}
            </div>
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

function ChatInput() {
  const [mode, setMode] = useState('command')
  return (
    <div className="shrink-0">
      {/* 桌面端固定 184px 输入区 */}
      <div className="hidden h-[184px] flex-col gap-2.5 border-t border-line bg-page px-12 pb-4 pt-3.5 lg:flex">
        {/* 输入框 固定 126px */}
        <div className="flex h-[126px] flex-col justify-between rounded-xl border border-input-border bg-white px-[18px] py-4 shadow-input">
          <Input.TextArea
            id="chat-question"
            name="question"
            aria-label="输入问题"
            variant="borderless"
            placeholder="输入问题，或粘贴配置/报错信息…"
            autoSize={false}
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
              className="flex h-[34px] items-center gap-2 rounded-lg bg-brand px-[14px] text-[13px] font-medium text-white"
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
          <Input.TextArea
            id="chat-question-mobile"
            name="question-mobile"
            aria-label="输入问题"
            variant="borderless"
            placeholder="输入问题，或粘贴配置/报错信息…"
            autoSize={{ minRows: 2, maxRows: 4 }}
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
              className="flex h-[34px] shrink-0 items-center gap-2 rounded-lg bg-brand px-3.5 text-[13px] font-medium text-white"
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
  const [vendor, setVendor] = useState(() => navState?.vendor || readStoredVendor())
  const [vendorsLoading, setVendorsLoading] = useState(true)
  const [kbStatus, setKbStatus] = useState<KnowledgeStatus>('checking')
  const [kbDetail, setKbDetail] = useState<string | null>(null)

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
        setVendor((current) => (current && unique.includes(current) ? current : (unique[0] ?? '')))
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
              options={vendors.map((item) => ({ value: item, label: item }))}
              loading={vendorsLoading}
              onChange={setVendor}
            />
            <button
              type="button"
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
        />

        <div className="flex min-w-0 flex-1 flex-col lg:min-h-0">
          <div className="thin-scrollbar flex-1 overflow-y-auto px-4 pt-6 lg:min-h-0 lg:px-12">
            <ChatMessages />
          </div>

          <ChatInput />
        </div>
      </div>
    </div>
  )
}
