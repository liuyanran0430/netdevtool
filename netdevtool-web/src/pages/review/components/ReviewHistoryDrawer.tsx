import { useCallback, useEffect, useState } from 'react'
import { Drawer, Input, message } from 'antd'
import {
  ArrowLeftOutlined,
  ArrowRightOutlined,
  CloseOutlined,
  HistoryOutlined,
  LoadingOutlined,
  ReloadOutlined,
} from '@ant-design/icons'
import {
  deleteReviewDecision,
  listReviewHistory,
  type ReviewDecisionAction,
  type ReviewHistoryPageDto,
} from '../../../api/review'

const PAGE_SIZE = 10

const ACTION_OPTIONS: { value: 'all' | ReviewDecisionAction; label: string }[] = [
  { value: 'all', label: '全部' },
  { value: 'accept', label: '已采纳' },
  { value: 'edit', label: '修改后采纳' },
  { value: 'skip', label: '已拒绝' },
]

const ACTION_LABELS: Record<ReviewDecisionAction, string> = {
  accept: '已采纳',
  edit: '修改后采纳',
  skip: '已拒绝',
}

const ACTION_CLASSES: Record<ReviewDecisionAction, string> = {
  accept: 'bg-success-soft text-success',
  edit: 'bg-brand-soft text-brand',
  skip: 'bg-danger-soft text-danger',
}

interface ReviewHistoryDrawerProps {
  open: boolean
  onClose: () => void
  /** 撤销处置后通知审核列表刷新，被撤销的命令重新回到待审核 */
  onChanged: () => void
}

function formatTime(value: string): string {
  return new Date(value).toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function ReviewHistoryDrawer({ open, onClose, onChanged }: ReviewHistoryDrawerProps) {
  const [data, setData] = useState<ReviewHistoryPageDto | null>(null)
  const [loading, setLoading] = useState(false)
  const [failed, setFailed] = useState(false)
  const [action, setAction] = useState<'all' | ReviewDecisionAction>('all')
  const [keyword, setKeyword] = useState('')
  const [appliedKeyword, setAppliedKeyword] = useState('')
  const [revoking, setRevoking] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setFailed(false)
    try {
      const response = await listReviewHistory({
        page: 1,
        pageSize: PAGE_SIZE,
        action,
        keyword: appliedKeyword || undefined,
      })
      setData(response)
    } catch {
      setFailed(true)
    } finally {
      setLoading(false)
    }
  }, [action, appliedKeyword])

  useEffect(() => {
    if (open) void load()
  }, [open, load])

  // 关键词防抖，避免每次输入都请求
  useEffect(() => {
    if (!open) return
    const timer = window.setTimeout(() => setAppliedKeyword(keyword.trim()), 300)
    return () => window.clearTimeout(timer)
  }, [keyword, open])

  const items = data?.items ?? []
  const total = data?.total ?? 0

  const handleRevoke = async (itemKey: string) => {
    setRevoking(itemKey)
    try {
      await deleteReviewDecision(itemKey)
      message.success('已撤销，命令回到待审核列表')
      await load()
      onChanged()
    } catch (error) {
      message.error(error instanceof Error ? error.message : '撤销审核处置失败')
    } finally {
      setRevoking(null)
    }
  }

  const renderBody = () => {
    if (loading && !data) {
      return (
        <div className="flex flex-col items-center gap-2 py-20 text-ink-400">
          <LoadingOutlined className="text-[20px]" />
          <span className="text-[12px]">正在加载审核记录…</span>
        </div>
      )
    }
    if (failed) {
      return (
        <div className="flex flex-col items-center gap-2 py-20 text-ink-400">
          <span className="text-[12px]">审核记录加载失败</span>
          <button type="button" onClick={() => void load()} className="text-[11px] text-brand">
            重新加载
          </button>
        </div>
      )
    }
    if (items.length === 0) {
      return (
        <div className="flex flex-col items-center gap-2 py-20 text-ink-400">
          <div className="flex h-11 w-11 items-center justify-center rounded-full bg-white text-ink-300">
            <HistoryOutlined className="text-[18px]" />
          </div>
          <span className="text-[12px]">暂无审核记录</span>
          <span className="text-[11px] text-ink-300">
            {action === 'all' && !appliedKeyword
              ? '完成一次审核处置后会自动出现在这里'
              : '当前筛选条件下没有记录'}
          </span>
        </div>
      )
    }
    return (
      <div className="space-y-2.5">
        {items.map((item) => {
          const targetLine =
            item.action === 'skip'
              ? null
              : item.decided_text || item.candidate?.command || item.target_text
          return (
            <div
              key={item.item_key}
              className="group rounded-xl border border-line bg-white p-3 transition-colors hover:border-brand-line"
            >
              <div className="flex items-center justify-between gap-2">
                <div className="flex min-w-0 items-center gap-1.5">
                  <span
                    className={`shrink-0 rounded-full px-2 py-[1px] text-[10px] ${ACTION_CLASSES[item.action]}`}
                  >
                    {ACTION_LABELS[item.action]}
                  </span>
                  {item.candidate ? (
                    <span className="shrink-0 rounded-full bg-brand-soft px-2 py-[1px] text-[10px] text-brand">
                      AI 候选
                    </span>
                  ) : null}
                  <span className="truncate text-[10px] text-ink-300">{item.view}</span>
                </div>
                <span className="shrink-0 text-[11px] text-ink-400">
                  {formatTime(item.updated_at)}
                </span>
              </div>

              <div className="mt-2 space-y-1">
                <div className="break-all rounded-md bg-soft px-2 py-1 font-mono text-[11px] text-ink-900">
                  {item.source_text || '（空行）'}
                </div>
                {targetLine ? (
                  <>
                    <div className="pl-2 text-[10px] text-ink-300">
                      <ArrowRightOutlined className="rotate-90" />
                    </div>
                    <div className="break-all rounded-md border border-line-soft px-2 py-1 font-mono text-[11px] text-ink-900">
                      {targetLine}
                    </div>
                  </>
                ) : (
                  <div className="text-[10px] text-ink-300">已拒绝，不写入知识库</div>
                )}
              </div>

              <div className="mt-2 flex items-center justify-between gap-2 border-t border-line-soft pt-2 text-[10px] text-ink-400">
                <span className="truncate">
                  {item.source_vendor} {item.source_model} → {item.target_vendor}{' '}
                  {item.target_model}
                </span>
                <button
                  type="button"
                  disabled={revoking === item.item_key}
                  onClick={() => void handleRevoke(item.item_key)}
                  className={`flex shrink-0 items-center gap-1 text-[11px] text-brand transition-opacity group-hover:opacity-100 disabled:cursor-not-allowed disabled:text-ink-300 ${
                    revoking === item.item_key ? 'opacity-100' : 'opacity-0'
                  }`}
                >
                  {revoking === item.item_key ? '撤销中…' : '撤销此审核'}
                  <ArrowLeftOutlined className="text-[10px]" />
                </button>
              </div>
            </div>
          )
        })}

        {total > PAGE_SIZE ? (
          <div className="pt-1 text-center text-[10px] text-ink-300">
            仅显示最近 {PAGE_SIZE} 条审核记录（共 {total} 条），可用关键词检索更早的记录
          </div>
        ) : null}
      </div>
    )
  }

  return (
    <Drawer
      closable={false}
      title={
        <div className="flex items-center gap-2">
          <span className="flex h-6 w-6 items-center justify-center rounded-md bg-brand-soft text-brand">
            <HistoryOutlined className="text-[13px]" />
          </span>
          <span className="text-[14px] font-medium text-ink-900">审核记录</span>
          {total > 0 ? (
            <span className="rounded-full bg-soft px-1.5 py-[1px] text-[11px] text-ink-400">
              {total}
            </span>
          ) : null}
        </div>
      }
      extra={
        <div className="flex items-center gap-1.5">
          <button
            type="button"
            onClick={() => void load()}
            disabled={loading}
            className="flex h-7 items-center gap-1 rounded-md px-2 text-[12px] text-ink-500 transition-colors hover:bg-soft hover:text-brand-strong disabled:cursor-not-allowed disabled:text-ink-300"
          >
            <ReloadOutlined spin={loading} className="text-[12px]" />
            刷新
          </button>
          <span className="h-4 w-px bg-line" />
          <button
            type="button"
            aria-label="关闭"
            onClick={onClose}
            className="flex h-7 w-7 items-center justify-center rounded-md text-ink-400 transition-colors hover:bg-soft hover:text-ink-700"
          >
            <CloseOutlined className="text-[12px]" />
          </button>
        </div>
      }
      open={open}
      onClose={onClose}
      width={440}
      styles={{
        wrapper: { boxShadow: 'none' },
        header: {
          padding: '14px 20px',
          borderBottom: '1px solid #E4EAF2',
          background: '#FFFFFF',
        },
        body: { padding: '16px 18px', background: '#F7F9FC' },
        section: {
          width: 'calc(100% - 12px)',
          height: 'calc(100% - 24px)',
          margin: '12px 12px 12px 0',
          borderRadius: 16,
          overflow: 'hidden',
          boxShadow: '0 10px 40px rgba(32, 44, 64, 0.16)',
        },
      }}
      destroyOnClose
    >
      <div className="mb-3 flex items-center gap-2">
        <select
          className="h-[30px] rounded-md border border-line bg-white px-2 text-[12px] text-ink-500 outline-none focus:border-brand-line"
          value={action}
          onChange={(event) =>
            setAction(event.target.value as 'all' | ReviewDecisionAction)
          }
        >
          {ACTION_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              动作：{option.label}
            </option>
          ))}
        </select>
        <Input
          size="small"
          allowClear
          placeholder="搜索源命令"
          value={keyword}
          onChange={(event) => setKeyword(event.target.value)}
        />
      </div>
      {renderBody()}
    </Drawer>
  )
}
