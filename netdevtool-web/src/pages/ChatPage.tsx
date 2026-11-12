import { useState } from 'react'
import {
  ArrowUpOutlined,
  BookOutlined,
  CodeOutlined,
  CommentOutlined,
  CopyOutlined,
  DislikeOutlined,
  DownOutlined,
  FileTextOutlined,
  InfoCircleOutlined,
  LikeOutlined,
  MoreOutlined,
  PlusOutlined,
  RobotFilled,
  SafetyCertificateOutlined,
  ScanOutlined,
  SearchOutlined,
  UserOutlined,
} from '@ant-design/icons'
import { Checkbox, Drawer, Input } from 'antd'
import { PageHeader } from '../components/PageHeader'
import { StatusTag } from '../components/StatusTag'
import {
  chatSessions,
  diagnosticSteps,
  probableCauses,
  questionModes,
} from '../data/chat'

function ContextSelect({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex h-9 items-center justify-between gap-2 rounded-lg border border-line bg-white px-3 text-[13px] text-ink-500">
      <span className="whitespace-nowrap">
        {label}
        <span className="ml-0.5 font-medium text-ink-900">{value}</span>
      </span>
      <DownOutlined className="text-[10px] text-ink-400" />
    </div>
  )
}

function SessionHistory({ className = '' }: { className?: string }) {
  return (
    <div
      className={`flex flex-col gap-6 bg-soft px-4 pb-[22px] pt-[26px] ${className}`}
    >
      <div className="flex items-center justify-between px-1">
        <div className="flex items-center gap-2">
          <span className="text-[14px] font-bold text-ink-900">会话历史</span>
          <span className="text-[11px] text-ink-400">3</span>
        </div>
        <button type="button" aria-label="搜索会话" className="text-[15px] text-ink-400">
          <SearchOutlined />
        </button>
      </div>

      <div className="flex flex-col gap-2">
        <span className="px-1 text-[11px] text-ink-400">最近 7 天</span>
        {chatSessions.map((session) => (
          <button
            type="button"
            key={session.id}
            className={`flex items-center gap-2.5 rounded-lg border px-3 py-2.5 text-left ${
              session.active
                ? 'border-brand-line bg-brand-soft'
                : 'border-line bg-white'
            }`}
          >
            <span
              className={`shrink-0 text-[13px] ${
                session.active ? 'text-brand-strong' : 'text-ink-400'
              }`}
            >
              <CommentOutlined />
            </span>
            <span className="min-w-0 flex-1">
              <span
                className={`block truncate text-[13px] ${
                  session.active ? 'font-medium text-brand-strong' : 'text-ink-900'
                }`}
              >
                {session.title}
              </span>
              <span className="mt-0.5 block text-[11px] text-ink-400">{session.time}</span>
            </span>
            <MoreOutlined className="shrink-0 text-[13px] text-ink-400" />
          </button>
        ))}
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
          <span className="h-1.5 w-1.5 rounded-full bg-success" />
          <span className="text-xs text-ink-500">企业知识库已连接</span>
        </div>
        <p className="mt-2 text-[11px] leading-[1.6] text-ink-400">
          回答基于设备手册与运维知识
        </p>
      </div>
    </div>
  )
}

function TroubleshootCard() {
  return (
    <div className="overflow-hidden rounded-xl border border-line bg-white">
      <div className="flex h-12 items-center justify-between gap-3 border-b border-line bg-head px-5">
        <div className="flex min-w-0 items-center gap-2">
          <ScanOutlined className="shrink-0 text-[15px] text-brand-strong" />
          <span className="truncate text-[14px] font-bold text-ink-900">
            VLAN 间连通性排查
          </span>
        </div>
        <span className="flex shrink-0 items-center gap-1.5 text-[11px] text-ink-500">
          华为 S5735
          <span className="text-ink-300">/</span>
          三层互通
        </span>
      </div>

      <div className="flex flex-col gap-2.5 px-5 pb-2.5 pt-3.5">
        <div className="flex items-center justify-between">
          <span className="text-[13px] font-bold text-ink-900">可能原因</span>
          <span className="text-[11px] text-ink-400">按概率排序 · 基于相似案例</span>
        </div>

        <div className="flex flex-col gap-1 rounded-md bg-[#F5F8FE] px-3 py-1">
          {probableCauses.map((cause) => (
            <div key={cause.text} className="flex items-center gap-2.5">
              <span className="w-[38px] shrink-0 text-right font-mono text-[14px] font-semibold text-brand-strong">
                {cause.percent}
              </span>
              <span className="flex h-[5px] w-[74px] shrink-0 items-center overflow-hidden rounded-full bg-[#DDE6F4]">
                <span
                  className="h-[5px] rounded-full bg-brand"
                  style={{ width: `${(cause.width / 74) * 100}%` }}
                />
              </span>
              <span className="truncate text-[13px] text-ink-900">{cause.text}</span>
            </div>
          ))}
        </div>

        <div className="flex items-center justify-between pt-1">
          <span className="text-[13px] font-bold text-ink-900">诊断步骤</span>
          <span className="text-[11px] text-brand-strong">1 / 4 已确认</span>
        </div>

        <div>
          {diagnosticSteps.map((step) => (
            <div
              key={step.id}
              className="flex items-center gap-2.5 border-b border-line-soft py-2 last:border-b-0"
            >
              <Checkbox defaultChecked={step.done} />
              <span className="min-w-0 flex-1 text-[13px] leading-5 text-ink-900">
                {step.text}
              </span>
              <span className="hidden shrink-0 rounded border border-line bg-soft px-2 py-0.5 font-mono text-[11px] text-ink-500 sm:block">
                {step.command}
              </span>
            </div>
          ))}
        </div>
      </div>

      <div className="flex items-start gap-2 border-t border-line bg-soft px-5 py-2.5">
        <InfoCircleOutlined className="mt-0.5 shrink-0 text-[12px] text-ink-400" />
        <span className="text-[11px] leading-[1.6] text-ink-500">
          建议先执行只读诊断命令；修改配置前，请备份并确认业务影响。
        </span>
      </div>
    </div>
  )
}

function ChatMessages() {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col items-end gap-2">
        <div className="flex items-center gap-2 text-[11px]">
          <span className="text-ink-400">昨天 14:32</span>
          <span className="text-xs font-medium text-ink-500">我</span>
          <span className="flex h-[25px] w-[25px] items-center justify-center rounded-full bg-[#E2E9F5] text-[12px] text-ink-500">
            <UserOutlined />
          </span>
        </div>
        <div className="max-w-[86%] rounded-[12px_2px_12px_12px] bg-brand-soft px-5 py-3.5 text-[15px] font-medium leading-6 text-ink-900">
          华为 S5735 两个 VLAN 间不通，怎么排查？
        </div>
      </div>

      <div className="flex flex-col gap-3">
        <div className="flex items-center gap-2">
          <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-brand text-[14px] text-white">
            <RobotFilled />
          </span>
          <span className="text-[13px] font-bold text-ink-900">网络知识助手</span>
          <StatusTag tone="green">知识库增强</StatusTag>
        </div>

        <p className="text-[14px] leading-[1.7] text-ink-900">
          先确认三层接口和 VLAN 放行顺序……建议按以下步骤逐项排查，优先检查 Vlanif 状态。
        </p>

        <TroubleshootCard />

        <div className="flex flex-wrap items-center gap-2">
          <span className="text-[11px] text-ink-400">参考来源</span>
          <button
            type="button"
            className="flex items-center gap-1.5 rounded-md border border-line bg-white px-2 py-1 text-[11px] text-brand-strong"
          >
            <FileTextOutlined className="text-[12px] text-ink-400" />
            KB-0231 · 手册 §4.3
            <span className="text-[10px] text-ink-400">↗</span>
          </button>
        </div>

        <div className="flex items-center gap-5 text-[12px] text-ink-500">
          <button type="button" className="flex items-center gap-1.5">
            <CopyOutlined className="text-[13px] text-ink-400" />
            复制
          </button>
          <button type="button" className="flex items-center gap-1.5">
            <CommentOutlined className="text-[13px] text-ink-400" />
            继续追问
          </button>
          <span className="h-[13px] w-px bg-line" />
          <button type="button" aria-label="有帮助">
            <LikeOutlined className="text-[14px] text-ink-400" />
          </button>
          <button type="button" aria-label="没帮助">
            <DislikeOutlined className="text-[14px] text-ink-400" />
          </button>
        </div>
      </div>
    </div>
  )
}

function ChatInput() {
  const modes = questionModes.map((mode, idx) => ({
    ...mode,
    icon:
      idx === 0 ? (
        <CodeOutlined className="text-[12px]" />
      ) : idx === 1 ? (
        <ScanOutlined className="text-[12px]" />
      ) : (
        <BookOutlined className="text-[12px]" />
      ),
  }))

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
            className="!h-[54px] !min-h-0 resize-none !p-0 !text-[13px] placeholder:!text-ink-400"
          />

          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-1">
              {modes.map((mode) => {
                const active = mode.id === 'troubleshoot'
                return (
                  <span
                    key={mode.id}
                    className={`flex h-[29px] items-center gap-1.5 rounded-md border px-[9px] text-[11px] ${
                      active
                        ? 'border-[#CDDCFB] bg-brand-soft text-brand-strong'
                        : 'border-transparent text-ink-500'
                    }`}
                  >
                    {mode.icon}
                    {mode.label}
                  </span>
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
            className="!p-0 !text-[14px] placeholder:!text-ink-400"
          />

          <div className="flex items-center justify-between gap-3">
            <div className="flex flex-wrap items-center gap-1">
              {modes.map((mode) => {
                const active = mode.id === 'troubleshoot'
                return (
                  <span
                    key={mode.id}
                    className={`flex h-[29px] items-center gap-1.5 rounded-md px-2.5 text-xs ${
                      active
                        ? 'border border-[#CDDCFB] bg-brand-soft text-brand-strong'
                        : 'text-ink-500'
                    }`}
                  >
                    {mode.icon}
                    {mode.label}
                  </span>
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
  const [historyOpen, setHistoryOpen] = useState(false)

  return (
    <div className="flex min-h-full flex-col">
      <PageHeader
        title="智能问答"
        subtitle="网络设备知识助手"
        right={
          <>
            <ContextSelect label="厂商上下文：" value="华为" />
            <ContextSelect label="知识域：" value="全部" />
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
        <SessionHistory className="hidden w-[248px] shrink-0 border-r border-line lg:flex" />

        <div className="flex min-w-0 flex-1 flex-col lg:min-h-0">
          <div className="flex h-[54px] shrink-0 items-center justify-between gap-3 border-b border-line bg-white px-4 lg:px-8">
            <div className="flex min-w-0 items-center gap-2.5">
              <button
                type="button"
                onClick={() => setHistoryOpen(true)}
                className="flex items-center gap-1 text-[12px] text-ink-500 lg:hidden"
              >
                会话
                <span className="text-[10px]">›</span>
              </button>
              <span className="truncate text-[13px] font-medium text-ink-900">
                VLAN 间不通
              </span>
              <StatusTag tone="blue">故障排查</StatusTag>
            </div>
            <div className="flex shrink-0 items-center gap-3">
              <span className="hidden text-[11px] text-ink-400 sm:inline">已自动保存</span>
              <MoreOutlined className="text-[16px] text-ink-400" />
            </div>
          </div>

          <div className="thin-scrollbar flex-1 overflow-y-auto px-4 pt-6 lg:min-h-0 lg:px-12">
            <ChatMessages />
          </div>

          <ChatInput />
        </div>
      </div>

      <Drawer
        open={historyOpen}
        onClose={() => setHistoryOpen(false)}
        placement="left"
        size={280}
        title="会话"
        styles={{ body: { padding: 0 } }}
      >
        <SessionHistory className="min-h-full" />
      </Drawer>
    </div>
  )
}
