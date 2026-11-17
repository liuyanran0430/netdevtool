import { useState } from 'react'
import { Checkbox, Modal, message } from 'antd'
import { EditOutlined, CloseOutlined, ThunderboltOutlined } from '@ant-design/icons'
import { StatusTag } from '../../../components/StatusTag'
import { generateCandidate } from '../../../api/knowledge'
import { openDeviceManual } from '../../../api/devices'
import type { ReviewCandidateDto } from '../../../api/review'
import type { ReviewItem } from '../deriveItems'
import { WARNING_LABELS } from '../deriveItems'

interface ReviewCardProps {
  item: ReviewItem
  checked: boolean
  onCheck: (checked: boolean) => void
  onAccept: (candidateId?: number) => Promise<void>
  onEditAccept: (text: string) => Promise<void>
  onSkip: () => Promise<void>
  /** 生成成功后回写条目候选，保证批量采纳与单条采纳使用同一份数据 */
  onCandidateGenerated: (candidate: ReviewCandidateDto) => void
}

export function ReviewCard({
  item,
  checked,
  onCheck,
  onAccept,
  onEditAccept,
  onSkip,
  onCandidateGenerated,
}: ReviewCardProps) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState('')
  const [generating, setGenerating] = useState(false)
  const [manualLoading, setManualLoading] = useState(false)
  // 是否本次会话内触发过生成：失败后允许重试，页面恢复的历史失败候选不允许
  const [generatedHere, setGeneratedHere] = useState(false)
  const [accepting, setAccepting] = useState(false)
  const [aiCandidate, setAiCandidate] = useState<{
    id: number
    command: string
    views: string[]
    reasoning: string
    passed: boolean
  } | null>(() =>
    item.candidate
      ? {
          id: item.candidate.id,
          command: item.candidate.command ?? '',
          views: item.candidate.views ?? [],
          reasoning: item.candidate.reasoning ?? '',
          passed: item.candidate.passed,
        }
      : null,
  )

  const borderClass = checked ? 'border-brand-line' : 'border-line'

  const startEdit = () => {
    setDraft(
      aiCandidate?.passed && aiCandidate.command
        ? aiCandidate.command
        : item.targetText || item.sourceText,
    )
    setEditing(true)
  }

  const confirmEdit = () => {
    const text = draft.trim()
    if (!text) return
    Modal.confirm({
      title: '确认修改后采纳？',
      content: (
        <div className="flex flex-col gap-2 pt-1 text-xs text-ink-700">
          <span>采纳内容将写入数据库，该条目移入审核记录，可在审核记录中撤销。</span>
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
    const withCandidate = Boolean(aiCandidate?.passed)
    Modal.confirm({
      title: '确认采纳该命令？',
      content: withCandidate
        ? '采纳后该映射将写入补充知识库，审核结果同步落库，可在审核记录中撤销。'
        : '采纳结果将写入数据库，该条目移入审核记录，可在审核记录中撤销。',
      okText: '确认采纳',
      cancelText: '取消',
      onOk: async () => {
        setAccepting(true)
        try {
          await onAccept(withCandidate ? aiCandidate?.id : undefined)
        } finally {
          setAccepting(false)
        }
      },
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

  const handleGenerate = async () => {
    if (item.gapId == null) return
    setGenerating(true)
    try {
      const candidate = await generateCandidate(
        item.gapId,
        item.targetVendor,
        item.targetModel,
      )
      const errors = candidate.validation?.errors ?? []
      setGeneratedHere(true)
      setAiCandidate({
        id: candidate.id,
        command: candidate.response?.target_command ?? '',
        views: candidate.response?.target_view_path ?? [],
        reasoning: candidate.response?.reasoning ?? '',
        passed: candidate.validation?.passed ?? false,
      })
      onCandidateGenerated({
        id: candidate.id,
        status: candidate.status,
        command: candidate.response?.target_command ?? null,
        views: candidate.response?.target_view_path ?? [],
        reasoning: candidate.response?.reasoning ?? null,
        passed: candidate.validation?.passed ?? false,
        llm_model: candidate.llm_model,
        created_at: candidate.created_at,
      })
      if (candidate.status === 'passed') {
        message.success('候选已生成，自动校验通过')
      } else {
        message.warning('候选已生成，自动校验未通过')
        Modal.info({
          title: 'AI 候选结果',
          okText: '知道了',
          content: (
            <div className="flex flex-col gap-1.5 pt-1 text-xs text-ink-700">
              <div className="break-all font-mono text-[13px] text-ink-900">
                {candidate.response?.target_command ?? '模型选择弃权'}
              </div>
              <div>视图：{candidate.response?.target_view_path?.join(' > ') || '-'}</div>
              <div>
                状态：{candidate.status}（{candidate.validation?.passed ? '校验通过' : '校验未通过'}）
              </div>
              {errors.length ? (
                <ul className="list-disc pl-4 text-danger">
                  {errors.map((error) => (
                    <li key={error}>{error}</li>
                  ))}
                </ul>
              ) : null}
            </div>
          ),
        })
      }
    } catch (error) {
      message.error(error instanceof Error ? error.message : '生成候选失败')
    } finally {
      setGenerating(false)
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
              <span className="break-all font-mono text-[15px] leading-[23px] text-ink-900">
                {item.sourceText || '（空行）'}
              </span>
              {item.codes.map((code) => (
                <StatusTag key={code} tone={item.severity === 'error' ? 'red' : item.severity === 'warn' ? 'warn' : 'gray'}>
                  {WARNING_LABELS[code] ?? code}
                </StatusTag>
              ))}
              {aiCandidate?.passed ? (
                <StatusTag tone="green">候选由AI生成</StatusTag>
              ) : aiCandidate ? (
                <StatusTag tone="red">候选AI生成失败</StatusTag>
              ) : null}
            </div>
          </div>
        </div>
      </div>

      <div className="mt-2.5 flex flex-col gap-1.5 rounded bg-soft px-4 py-2.5">
        <div className="flex min-w-0 flex-wrap items-baseline gap-2">
          <span className="shrink-0 text-xs text-ink-400">候选：</span>
          <StatusTag tone="blue">
            {item.targetVendor} {item.targetModel}
          </StatusTag>
          <span className="break-all font-mono text-[13px] leading-[22px] text-brand">
            {(aiCandidate?.passed && aiCandidate.command) || item.targetText}
          </span>
          <span className="ml-auto shrink-0 text-[11px] text-ink-400">
            视图：
            {aiCandidate?.passed && aiCandidate.views.length
              ? aiCandidate.views.join(' > ')
              : item.view}
          </span>
        </div>
      </div>

      <p className="mt-2.5 text-xs text-ink-500">
        说明：
        {aiCandidate?.passed
          ? aiCandidate.reasoning || 'AI 已生成候选命令并通过自动校验，采纳后写入补充知识库'
          : item.message}
      </p>

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
            disabled={accepting}
            onClick={handleAccept}
            className="flex h-[30px] items-center rounded-md bg-brand px-4 text-xs font-medium text-white disabled:cursor-not-allowed disabled:opacity-50"
          >
            {accepting ? '采纳中…' : '采纳'}
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
          {item.gapId != null && !aiCandidate?.passed && (!aiCandidate || generatedHere) ? (
            <button
              type="button"
              disabled={generating}
              onClick={handleGenerate}
              className="flex h-[30px] items-center gap-1.5 rounded-md border border-brand-line bg-white px-4 text-xs text-brand-strong disabled:cursor-not-allowed disabled:opacity-50"
            >
              <ThunderboltOutlined className="text-[12px]" />
              {generating ? '生成中…' : '生成候选'}
            </button>
          ) : null}
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
