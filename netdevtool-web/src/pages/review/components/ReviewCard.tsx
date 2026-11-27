import { useState } from 'react'
import { Checkbox, Modal, message } from 'antd'
import { EditOutlined, CloseOutlined } from '@ant-design/icons'
import { StatusTag } from '../../../components/StatusTag'
import { openDeviceManual } from '../../../api/devices'
import type { ReviewItem } from '../deriveItems'
import { WARNING_LABELS } from '../deriveItems'

interface ReviewCardProps {
  item: ReviewItem
  checked: boolean
  onCheck: (checked: boolean) => void
  onAccept: () => Promise<void>
  onEditAccept: (text: string) => Promise<void>
  onSkip: () => Promise<void>
}

export function ReviewCard({
  item,
  checked,
  onCheck,
  onAccept,
  onEditAccept,
  onSkip,
}: ReviewCardProps) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState('')
  const [manualLoading, setManualLoading] = useState(false)

  const borderClass = checked ? 'border-brand-line' : 'border-line'

  const startEdit = () => {
    setDraft(item.sourceText)
    setEditing(true)
  }

  const confirmEdit = () => {
    const text = draft.trim()
    if (!text) return
    Modal.confirm({
      title: '确认修改后采纳？',
      content: (
        <div className="flex flex-col gap-2 pt-1 text-xs text-ink-700">
          <span className="break-all rounded bg-soft px-2 py-1.5 font-mono text-[13px] text-ink-900">
            {text}
          </span>
        </div>
      ),
      okText: '确认采纳',
      cancelText: '取消',
      onOk: () => {
        setEditing(false)
        return onEditAccept(text)
      },
    })
  }

  const handleAccept = () => {
    Modal.confirm({
      title: '确认采纳该命令？',
      content: '采纳结果将写入数据库，该条目移入审核记录。',
      okText: '确认采纳',
      cancelText: '取消',
      onOk: () => onAccept(),
    })
  }

  const handleOpenManual = async () => {
    setManualLoading(true)
    try {
      await openDeviceManual(item.targetVendor, item.targetModel)
    } catch (error) {
      message.error(error instanceof Error ? error.message : '打开手册失败')
    } finally {
      setManualLoading(false)
    }
  }

  return (
    <article className={`rounded-lg border bg-white p-4 md:px-5 md:py-3.5 ${borderClass}`}>
      <div className="flex flex-wrap items-start justify-between gap-x-4 gap-y-2">
        <div className="flex min-w-0 flex-1 items-start gap-3">
          <Checkbox
            className="mt-0.5 shrink-0"
            checked={checked}
            onChange={(event) => onCheck(event.target.checked)}
          />
          <div className="flex min-w-0 flex-1 flex-col gap-2">
            <div className="flex min-w-0 flex-wrap items-center gap-x-1.5 gap-y-1.5">
              <span className="font-mono text-[15px] leading-[23px] text-ink-700">
                {item.sourceVendor} {item.sourceModel}:
              </span>
              <span className="whitespace-pre-wrap break-all font-mono text-[15px] leading-[23px] text-ink-900">
                {item.sourceText || '（空行）'}
              </span>
              {item.codes.map((code) => (
                <StatusTag key={code} tone={item.severity === 'error' ? 'red' : item.severity === 'warn' ? 'warn' : 'gray'}>
                  {WARNING_LABELS[code] ?? code}
                </StatusTag>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="mt-2.5 flex flex-col gap-1.5 rounded bg-soft px-4 py-2.5">
        <div className="flex min-w-0 flex-wrap items-baseline gap-2">
          <span className="shrink-0 text-xs text-ink-400">目标：</span>
          <StatusTag tone="blue">
            {item.targetVendor} {item.targetModel}
          </StatusTag>
          <span className="ml-auto shrink-0 text-[11px] text-ink-400">视图：无</span>
        </div>
      </div>

      <p className="mt-2.5 text-xs text-ink-500">说明：{item.message}</p>

      {editing ? (
        <div className="mt-3 flex flex-col gap-2">
          <textarea
            className="w-full rounded-md border border-line px-3 py-2 font-mono text-[13px] leading-[22px] text-ink-900 outline-none focus:border-brand-line"
            rows={2}
            autoFocus
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
          />
          <div className="flex items-center gap-2.5">
            <button
              type="button"
              disabled={!draft.trim()}
              onClick={confirmEdit}
              className="flex h-[30px] items-center rounded-md bg-brand px-4 text-xs font-medium text-white disabled:cursor-not-allowed disabled:opacity-40"
            >
              确认采纳
            </button>
            <button
              type="button"
              onClick={() => setEditing(false)}
              className="flex h-[30px] items-center rounded-md border border-line bg-white px-4 text-xs text-ink-700"
            >
              取消
            </button>
          </div>
        </div>
      ) : (
        <div className="mt-3 flex flex-wrap items-center gap-2.5">
          <button
            type="button"
            onClick={handleAccept}
            className="flex h-[30px] items-center rounded-md bg-brand px-4 text-xs font-medium text-white disabled:cursor-not-allowed disabled:opacity-50"
          >
            采纳
          </button>
          <button
            type="button"
            onClick={startEdit}
            className="flex h-[30px] items-center gap-1.5 rounded-md border border-line bg-white px-4 text-xs text-ink-700"
          >
            <EditOutlined className="text-[13px]" />
            修改后采纳
          </button>
          <button
            type="button"
            onClick={onSkip}
            className="flex h-[30px] items-center gap-1.5 rounded-md border border-danger-line bg-white px-4 text-xs text-danger"
          >
            <CloseOutlined className="text-[12px]" />
            拒绝
          </button>
          <button
            type="button"
            disabled={manualLoading}
            onClick={() => void handleOpenManual()}
            className="ml-auto flex items-center gap-1 text-[11px] text-brand-strong disabled:cursor-not-allowed disabled:text-ink-300"
          >
            {manualLoading ? '打开中…' : '查看设备手册'}
            <span className="text-[10px]">↗</span>
          </button>
        </div>
      )}
    </article>
  )
}
