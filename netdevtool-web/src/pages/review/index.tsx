import { useCallback, useEffect, useMemo, useState } from 'react'
import { Checkbox, Input, Modal, message } from 'antd'
import { PageHeader } from '../../components/PageHeader'
import { saveCheckpoint } from '../translate/storage'
import {
  createReviewDecision,
  deleteReviewDecision,
  listReviewDecisionSnapshots,
  listReviewItems,
  type ReviewCandidateDto,
  type ReviewDecisionAction,
  type ReviewItemsPageDto,
} from '../../api/review'
import { toReviewItems, type ReviewItem } from './deriveItems'
import { ReviewCard } from './components/ReviewCard'
import { ReviewBatchBar } from './components/ReviewBatchBar'
import {
  ReviewFilterBar,
  type StatusFilter,
} from './components/ReviewFilterBar'

const PAGE_SIZE = 10

const EMPTY_STATS = { pending: 0, accepted: 0, edited: 0, skipped: 0 }

function toCheckpointMap(
  reviews: Record<number, { tone: string; text?: string }>,
): Map<number, { tone: string; text?: string }> {
  return new Map(
    Object.entries(reviews).map(([index, value]) => [Number(index), value]),
  )
}

function decisionPayload(item: ReviewItem, action: ReviewDecisionAction) {
  return {
    source_vendor: item.sourceVendor,
    source_model: item.sourceModel,
    target_vendor: item.targetVendor,
    target_model: item.targetModel,
    source_text: item.sourceText,
    action,
  }
}

function defaultCheckpointName(): string {
  return `检查点 ${new Date().toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
  })}`
}

export function ReviewPage() {
  const [data, setData] = useState<ReviewItemsPageDto | null>(null)
  const [loading, setLoading] = useState(true)
  const [loadFailed, setLoadFailed] = useState(false)
  const [targetModel, setTargetModel] = useState('all')
  const [status, setStatus] = useState<StatusFilter>('all')
  const [code, setCode] = useState('all')
  const [page, setPage] = useState(1)
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [completeOpen, setCompleteOpen] = useState(false)
  const [completeName, setCompleteName] = useState('')

  const fetchPage = useCallback(
    async (silent = false) => {
      if (!silent) setLoading(true)
      setLoadFailed(false)
      const [vendor, model] = targetModel === 'all' ? [] : targetModel.split('|')
      try {
        const response = await listReviewItems({
          page,
          pageSize: PAGE_SIZE,
          status,
          targetVendor: vendor || undefined,
          targetModel: model || undefined,
          code: code === 'all' ? undefined : code,
        })
        setData(response)
        setSelected(new Set())
        // 后端会把越界页码收敛到最后一页，跟随其返回的页码
        if (response.page !== page) setPage(response.page)
      } catch (error) {
        if (!silent) setLoadFailed(true)
        message.error(error instanceof Error ? error.message : '加载待审核条目失败')
      } finally {
        if (!silent) setLoading(false)
      }
    },
    [page, status, targetModel, code],
  )

  useEffect(() => {
    void fetchPage()
  }, [fetchPage])

  const items = useMemo(() => (data ? toReviewItems(data.items) : []), [data])
  const total = data?.total ?? 0
  const currentPage = data?.page ?? page
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))
  const stats = data?.stats ?? EMPTY_STATS

  const modelOptions = useMemo(
    () =>
      (data?.target_options ?? []).map((option) => ({
        value: `${option.vendor}|${option.model}`,
        label: `${option.vendor} ${option.model}`,
      })),
    [data],
  )
  const codeOptions = data?.code_options ?? []

  const selectableOnPage = items.filter((item) => item.status === 'pending')
  const allSelected =
    selectableOnPage.length > 0 && selectableOnPage.every((item) => selected.has(item.key))
  const someSelected = selectableOnPage.some((item) => selected.has(item.key))

  const disposed = stats.accepted + stats.edited + stats.skipped
  const totalAll = stats.pending + disposed

  const submitDecision = async (
    item: ReviewItem,
    action: ReviewDecisionAction,
    extra: { decided_text?: string; candidate_id?: number } = {},
  ) => {
    try {
      await createReviewDecision({
        ...decisionPayload(item, action),
        ...extra,
      })
      if (extra.candidate_id != null) message.success('候选已写入补充知识库')
      await fetchPage(true)
    } catch (error) {
      message.error(error instanceof Error ? error.message : '提交审核处置失败')
    }
  }

  const applyAccept = (item: ReviewItem, candidateId?: number) =>
    submitDecision(
      item,
      'accept',
      candidateId == null ? {} : { candidate_id: candidateId },
    )

  const applyEdit = (item: ReviewItem, text: string) =>
    submitDecision(item, 'edit', { decided_text: text })

  const applySkip = (item: ReviewItem) => submitDecision(item, 'skip')

  const handleUndo = async (item: ReviewItem) => {
    try {
      await deleteReviewDecision(item.key)
      await fetchPage(true)
    } catch (error) {
      message.error(error instanceof Error ? error.message : '撤销审核处置失败')
    }
  }

  const handleCandidateGenerated = (itemKey: string, candidate: ReviewCandidateDto) => {
    setData((previous) =>
      previous
        ? {
            ...previous,
            items: previous.items.map((dto) =>
              dto.item_key === itemKey ? { ...dto, candidate } : dto,
            ),
          }
        : previous,
    )
  }

  const toggleSelect = (key: string, checked: boolean) => {
    setSelected((previous) => {
      const next = new Set(previous)
      if (checked) next.add(key)
      else next.delete(key)
      return next
    })
  }

  const toggleSelectAll = () => {
    setSelected((previous) => {
      const next = new Set(previous)
      if (allSelected) selectableOnPage.forEach((item) => next.delete(item.key))
      else selectableOnPage.forEach((item) => next.add(item.key))
      return next
    })
  }

  const batchApply = async (action: 'accept' | 'skip') => {
    const targets = items.filter(
      (item) => selected.has(item.key) && item.status === 'pending',
    )
    setSelected(new Set())
    if (targets.length === 0) return
    const results = await Promise.allSettled(
      targets.map((item) =>
        createReviewDecision({
          ...decisionPayload(item, action),
          // 与单条采纳保持一致：已通过校验的 AI 候选随采纳写入补充知识库
          ...(action === 'accept' && item.candidate?.passed
            ? { candidate_id: item.candidate.id }
            : {}),
        }),
      ),
    )
    const decided = new Set<string>()
    let failed = 0
    results.forEach((result, index) => {
      if (result.status === 'fulfilled') decided.add(targets[index].key)
      else failed += 1
    })
    if (failed > 0) message.error(`${failed} 条处置失败`)
    else message.success(`已${action === 'accept' ? '采纳' : '拒绝'} ${decided.size} 条`)
    if (decided.size > 0) await fetchPage(true)
  }

  const resetFilters = () => {
    setTargetModel('all')
    setStatus('all')
    setCode('all')
    setPage(1)
  }

  const openComplete = () => {
    setCompleteName(defaultCheckpointName())
    setCompleteOpen(true)
  }

  const saveComplete = async () => {
    try {
      const snapshots = await listReviewDecisionSnapshots()
      const byRequest: Record<string, Record<number, { tone: string; text?: string }>> = {}
      snapshots.forEach((snapshot) => {
        const reviews = byRequest[snapshot.request_id] ?? {}
        // 检查点与翻译页共用 reviews 覆盖层，键为结果行下标（0 开始），后端 lineIndex 从 1 开始
        reviews[snapshot.line_index - 1] = {
          tone: snapshot.action === 'skip' ? snapshot.original_tone : 'success',
          text: snapshot.decided_text ?? undefined,
        }
        byRequest[snapshot.request_id] = reviews
      })
      Object.entries(byRequest).forEach(([requestId, reviews]) => {
        saveCheckpoint(requestId, completeName, toCheckpointMap(reviews))
      })
      setCompleteOpen(false)
      message.success('检查点已生成')
    } catch (error) {
      message.error(error instanceof Error ? error.message : '生成检查点失败')
    }
  }

  const rangeStart = total === 0 ? 0 : (currentPage - 1) * PAGE_SIZE + 1
  const rangeEnd = Math.min(currentPage * PAGE_SIZE, total)

  const renderEmptyState = () => {
    if (loading) {
      return (
        <div className="flex flex-col items-center gap-2 rounded-lg border border-line bg-white px-4 py-16 text-center">
          <span className="text-[14px] text-ink-900">正在加载待审核条目…</span>
        </div>
      )
    }
    if (loadFailed) {
      return (
        <div className="flex flex-col items-center gap-2 rounded-lg border border-line bg-white px-4 py-16 text-center">
          <span className="text-[14px] text-ink-900">待审核条目加载失败</span>
          <button type="button" onClick={() => void fetchPage()} className="text-xs text-brand">
            重新加载
          </button>
        </div>
      )
    }
    if (totalAll === 0) {
      return (
        <div className="flex flex-col items-center gap-2 rounded-lg border border-line bg-white px-4 py-16 text-center">
          <span className="text-[14px] text-ink-900">暂无待审核条目</span>
          <span className="text-xs text-ink-400">
            已完成翻译任务中没有 error / warn 告警
          </span>
        </div>
      )
    }
    return (
      <div className="flex flex-col items-center gap-2 rounded-lg border border-line bg-white px-4 py-16 text-center">
        <span className="text-[14px] text-ink-900">当前筛选条件下没有条目</span>
        <button type="button" onClick={resetFilters} className="text-xs text-brand">
          重置筛选
        </button>
      </div>
    )
  }

  const showEmpty = loading || loadFailed || items.length === 0
  const selectedCount = items.filter((item) => selected.has(item.key)).length

  return (
    <div className="flex min-h-full flex-col">
      <PageHeader
        title="命令审核"
        subtitle="网络设备知识助手"
        right={
          <>
            <span className="hidden text-xs text-ink-400 lg:inline">
              人工确认后同步至命令知识库
            </span>
            {stats.pending === 0 && totalAll > 0 ? (
              <button
                type="button"
                onClick={openComplete}
                className="flex h-[34px] items-center rounded-md bg-brand px-4 text-[13px] font-medium text-white"
              >
                完成审核
              </button>
            ) : null}
            <button
              type="button"
              onClick={() => message.info('审核记录功能开发中')}
              className="flex h-[34px] items-center rounded-md border border-line bg-white px-4 text-[13px] text-ink-500"
            >
              审核记录
            </button>
          </>
        }
      />

      <div className="flex flex-1 flex-col gap-4 px-4 pb-4 pt-2 md:px-7 md:pt-2">
        <section className="flex flex-wrap items-end gap-x-4 gap-y-2">
          <div className="flex items-baseline gap-2.5">
            <span className="text-[14px] font-medium leading-5 text-ink-900">待审核</span>
            <span className="text-[24px] font-bold leading-[30px] text-brand">{stats.pending}</span>
          </div>
          <span className="mx-2 hidden h-6 w-px bg-line sm:block" />
          <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
            <span className="text-[12px] text-ink-500">已处置</span>
            <span className="text-[18px] font-medium leading-[24px] text-ink-900">
              {disposed}
            </span>
            <span className="text-[11px] text-ink-400">
              采纳 {stats.accepted} · 修改 {stats.edited} · 拒绝 {stats.skipped}
            </span>
          </div>
          <span className="ml-auto hidden text-xs text-ink-400 xl:inline">
            审核候选命令，持续完善跨厂商映射
          </span>
        </section>

        <ReviewFilterBar
          targetModel={targetModel}
          status={status}
          code={code}
          modelOptions={modelOptions}
          codeOptions={codeOptions}
          filteredCount={total}
          onTargetModelChange={(value) => {
            setTargetModel(value)
            setPage(1)
          }}
          onStatusChange={(value) => {
            setStatus(value)
            setPage(1)
          }}
          onCodeChange={(value) => {
            setCode(value)
            setPage(1)
          }}
          onReset={resetFilters}
        />

        <section className="flex flex-wrap items-center gap-x-3 gap-y-1.5">
          <Checkbox
            checked={allSelected}
            indeterminate={!allSelected && someSelected}
            disabled={selectableOnPage.length === 0}
            onChange={toggleSelectAll}
          />
          <span className="text-xs text-ink-500">全选当前页</span>
          <span className="text-xs text-brand">已选 {selectedCount} 项</span>
          <span className="ml-auto hidden text-xs text-ink-400 xl:inline">
            AI候选仅供参考，请结合源手册审核
          </span>
        </section>

        <section className="flex flex-col gap-2.5">
          {showEmpty
            ? renderEmptyState()
            : items.map((item) => (
                <ReviewCard
                  key={item.key}
                  item={item}
                  checked={selected.has(item.key)}
                  onCheck={(checked) => toggleSelect(item.key, checked)}
                  onAccept={(candidateId) => applyAccept(item, candidateId)}
                  onEditAccept={(text) => applyEdit(item, text)}
                  onSkip={() => applySkip(item)}
                  onUndo={() => handleUndo(item)}
                  onCandidateGenerated={(candidate) =>
                    handleCandidateGenerated(item.key, candidate)
                  }
                />
              ))}
        </section>

        <ReviewBatchBar
          selectedCount={selectedCount}
          page={currentPage}
          totalPages={totalPages}
          rangeText={`${rangeStart}–${rangeEnd} / ${total} 条`}
          onPage={setPage}
          onClear={() => setSelected(new Set())}
          onBatchAccept={() => batchApply('accept')}
          onBatchSkip={() => batchApply('skip')}
        />

        <footer className="flex flex-col gap-1 text-[10px] text-ink-400 sm:flex-row sm:items-center sm:justify-between">
          <span>处置结果可追溯，同步至翻译结果与检查点</span>
          <span>网络设备知识助手 · 命令审核</span>
        </footer>
      </div>

      <Modal
        open={completeOpen}
        title="生成检查点"
        okText="保存"
        cancelText="取消"
        okButtonProps={{ disabled: !completeName.trim() }}
        onOk={saveComplete}
        onCancel={() => setCompleteOpen(false)}
      >
        <Input
          autoFocus
          maxLength={30}
          showCount
          value={completeName}
          placeholder="检查点名称"
          onChange={(event) => setCompleteName(event.target.value)}
        />
      </Modal>
    </div>
  )
}
