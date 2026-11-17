import {
  ArrowRightOutlined,
  CheckCircleFilled,
  CloseOutlined,
  CloudSyncOutlined,
  CodeOutlined,
  CompressOutlined,
  CopyOutlined,
  DeleteOutlined,
  DownOutlined,
  ExclamationCircleFilled,
  ExpandAltOutlined,
  ExportOutlined,
  FileTextOutlined,
  FlagOutlined,
  HistoryOutlined,
  LinkOutlined,
  LoadingOutlined,
  ReloadOutlined,
  RobotOutlined,
  SafetyCertificateOutlined,
  TranslationOutlined,
  UploadOutlined,
  WarningOutlined,
} from '@ant-design/icons'
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type Dispatch,
  type MouseEvent,
  type SetStateAction,
} from 'react'
import { Drawer, Dropdown, Input, message, Modal, Popconfirm, Tooltip } from 'antd'
import { useNavigate } from 'react-router-dom'
import { PageHeader } from '../components/PageHeader'
import { StatusTag } from '../components/StatusTag'
import { deviceTypeLabel, fetchDevices, type Device } from '../api/devices'
import {
  getTranslationSource,
  listTranslations,
  type TranslationListItem,
} from '../api/translations'
import type {
  TranslationResult,
  TranslationResultLine,
  TranslationTone,
} from '../api/translations'
import { translationSignature, useTranslationTask } from '../hooks/useTranslationTask'
import type { CodeLine } from '../data/translate'
import {
  deleteCheckpoint,
  loadCheckpoints,
  readSession,
  saveCheckpoint,
  writeSession,
  type Checkpoint,
} from './translate/storage'
import {
  buildCfgText,
  buildReviewReport,
  downloadText,
  exportStamp,
  safeFileNamePart,
  type ExportFormat,
} from './translate/exporters'
import { SOURCE_ACCEPT_EXTENSIONS, useSourceConfig } from './translate/useSourceConfig'

// ---------- 代码视图行高：行号、滚动对齐与点击定位共用 ----------

const LINE_HEIGHT = 24
const TEXTAREA_PADDING_TOP = 4
/** 设备数据未返回前的空列表占位，保持 useMemo 依赖稳定 */
const EMPTY_DEVICES: Device[] = []
/** 翻译记录抽屉最多展示的条数 */
const HISTORY_LIMIT = 10

// ---------- 源配置暂存 / 会话 / 检查点的 localStorage 读写已拆分至 ./translate/storage ----------

// ---------- 导出工具（.cfg 配置与复核报告）已拆分至 ./translate/exporters ----------

interface SelectOption {
  value: string
  label: string
}

interface OptionSelectProps {
  label: string
  value: string
  options: SelectOption[]
  onChange: (value: string) => void
  width: string
  mono?: boolean
}

function OptionSelect({ label, value, options, onChange, width, mono }: OptionSelectProps) {
  return (
    <div className="flex flex-col gap-2">
      <span className="text-[11px] leading-none text-ink-400">{label}</span>
      <div className={`relative flex h-9 items-center ${width}`}>
        <select
          value={value}
          onChange={(event) => onChange(event.target.value)}
          className={`h-9 w-full cursor-pointer appearance-none rounded-lg border border-line bg-white px-3 pr-7 text-[13px] font-medium text-ink-900 outline-none ${
            mono ? 'font-mono' : ''
          }`}
        >
          {options.length === 0 ? (
            <option value="">暂无数据</option>
          ) : (
            options.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))
          )}
        </select>
        <DownOutlined className="pointer-events-none absolute right-3 text-[10px] text-ink-400" />
      </div>
    </div>
  )
}

function TranslateToolbar({
  deviceType,
  onDeviceTypeChange,
  initialSourceVendor,
  initialSourceModel,
  initialTargetVendor,
  initialTargetModel,
  onSourceChange,
  onTargetChange,
  onDevicesLoaded,
  onTranslate,
  onExport,
  translating = false,
  hasResult = false,
  hasTask = false,
}: {
  deviceType: string
  onDeviceTypeChange: Dispatch<SetStateAction<string>>
  initialSourceVendor?: string
  initialSourceModel?: string
  initialTargetVendor?: string
  initialTargetModel?: string
  onSourceChange?: (vendor: string, model: string) => void
  onTargetChange?: (vendor: string, model: string) => void
  onDevicesLoaded?: (devices: Device[]) => void
  onTranslate?: () => void
  onExport?: (format: ExportFormat) => void
  translating?: boolean
  hasResult?: boolean
  hasTask?: boolean
}) {
  // null 表示设备数据尚未返回，此时不纠正任何已恢复的选择
  const [devices, setDevices] = useState<Device[] | null>(null)
  const [vendor, setVendor] = useState(initialSourceVendor ?? '')
  const [model, setModel] = useState(initialSourceModel ?? '')
  const [targetVendor, setTargetVendor] = useState(initialTargetVendor ?? '')
  const [targetModel, setTargetModel] = useState(initialTargetModel ?? '')
  const navigate = useNavigate()

  useEffect(() => {
    let cancelled = false
    fetchDevices()
      .then((items) => {
        if (cancelled) return
        setDevices(items)
        onDevicesLoaded?.(items)
      })
      .catch(() => {
        // 后端不可用时保留空列表
      })
    return () => {
      cancelled = true
    }
  }, [onDevicesLoaded])

  const allDevices = devices ?? EMPTY_DEVICES
  const types = useMemo(
    () => [...new Set(allDevices.map((item) => item.device_type))],
    [allDevices],
  )
  const vendors = useMemo(
    () => [
      ...new Set(
        allDevices
          .filter((item) => item.device_type === deviceType)
          .map((item) => item.vendor),
      ),
    ],
    [allDevices, deviceType],
  )
  const models = useMemo(
    () => [
      ...new Set(
        allDevices
          .filter((item) => item.device_type === deviceType && item.vendor === vendor)
          .map((item) => item.model),
      ),
    ],
    [allDevices, deviceType, vendor],
  )
  const targetModels = useMemo(
    () => [
      ...new Set(
        allDevices
          .filter(
            (item) => item.device_type === deviceType && item.vendor === targetVendor,
          )
          .map((item) => item.model),
      ),
    ],
    [allDevices, deviceType, targetVendor],
  )

  useEffect(() => {
    if (!devices) return
    onDeviceTypeChange((current) =>
      current && types.includes(current) ? current : (types[0] ?? ''),
    )
  }, [devices, types, onDeviceTypeChange])

  useEffect(() => {
    if (!devices) return
    setVendor((current) => (current && vendors.includes(current) ? current : (vendors[0] ?? '')))
    setTargetVendor((current) =>
      current && vendors.includes(current) ? current : (vendors[0] ?? ''),
    )
  }, [devices, vendors])

  useEffect(() => {
    if (!devices) return
    setModel((current) => (current && models.includes(current) ? current : (models[0] ?? '')))
  }, [devices, models])

  useEffect(() => {
    if (!devices) return
    setTargetModel((current) =>
      current && targetModels.includes(current) ? current : (targetModels[0] ?? ''),
    )
  }, [devices, targetModels])

  // 历史记录恢复等外部来源会直接改写设备选择，下拉内部状态需同步，
  // 否则旧的选择会被下面的 onSourceChange / onTargetChange 回调写回父组件
  useEffect(() => {
    if (initialSourceVendor !== undefined) setVendor(initialSourceVendor)
  }, [initialSourceVendor])
  useEffect(() => {
    if (initialSourceModel !== undefined) setModel(initialSourceModel)
  }, [initialSourceModel])
  useEffect(() => {
    if (initialTargetVendor !== undefined) setTargetVendor(initialTargetVendor)
  }, [initialTargetVendor])
  useEffect(() => {
    if (initialTargetModel !== undefined) setTargetModel(initialTargetModel)
  }, [initialTargetModel])

  useEffect(() => {
    onSourceChange?.(vendor, model)
  }, [vendor, model, onSourceChange])

  useEffect(() => {
    onTargetChange?.(targetVendor, targetModel)
  }, [targetVendor, targetModel, onTargetChange])

  const targetReady = Boolean(targetVendor && targetModel)
  const sameDevice = targetReady && vendor === targetVendor && model === targetModel
  const canTranslate = targetReady && !sameDevice
  const blockReason = !targetReady
    ? '请选择目标厂商与型号'
    : sameDevice
      ? '源设备与目标设备相同，无需转换'
      : ''
  const translateDisabled = !canTranslate || translating
  const disabledReason = translating ? '翻译任务进行中，请稍候' : blockReason

  return (
    <section className="flex flex-col gap-4 rounded-panel border border-line bg-white px-5 py-4 xl:h-[92px] xl:flex-row xl:items-center xl:justify-between xl:py-0">
      <div className="flex flex-wrap items-end gap-3">
        <OptionSelect
          label="设备类型"
          value={deviceType}
          options={types.map((type) => ({ value: type, label: deviceTypeLabel(type) }))}
          onChange={onDeviceTypeChange}
          width="w-[100px]"
        />
        <OptionSelect
          label="源厂商"
          value={deviceType ? vendor : ''}
          options={deviceType ? vendors.map((item) => ({ value: item, label: item })) : []}
          onChange={setVendor}
          width="w-[100px]"
        />
        <OptionSelect
          label="型号/版本"
          value={vendor ? model : ''}
          options={vendor ? models.map((item) => ({ value: item, label: item })) : []}
          onChange={setModel}
          width="w-[260px]"
          mono
        />
        <div className="flex h-9 w-[36px] items-center justify-center text-[16px] text-ink-400">
          <ArrowRightOutlined />
        </div>
        <OptionSelect
          label="目标厂商"
          value={deviceType ? targetVendor : ''}
          options={deviceType ? vendors.map((item) => ({ value: item, label: item })) : []}
          onChange={setTargetVendor}
          width="w-[100px]"
        />
        <OptionSelect
          label="型号/版本"
          value={targetVendor ? targetModel : ''}
          options={targetVendor ? targetModels.map((item) => ({ value: item, label: item })) : []}
          onChange={setTargetModel}
          width="w-[260px]"
          mono
        />
      </div>

      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between gap-2">
          <span className="text-[11px] leading-none text-ink-400">配置转换与验证</span>
          <span className="text-[11px] leading-none text-warn">{disabledReason}</span>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Tooltip title={translateDisabled ? disabledReason : ''}>
            <span className="inline-flex">
              <button
                type="button"
                disabled={translateDisabled}
                onClick={onTranslate}
                className="flex h-9 items-center gap-[7px] rounded-lg bg-brand px-3.5 text-[13px] font-medium text-white disabled:cursor-not-allowed disabled:opacity-45"
              >
                {translating ? (
                  <LoadingOutlined spin className="text-[15px]" />
                ) : (
                  <TranslationOutlined className="text-[15px]" />
                )}
                {translating ? '翻译中' : hasResult ? '重新翻译' : '翻译'}
              </button>
            </span>
          </Tooltip>
          <button
            type="button"
            onClick={() =>
              navigate(
                '/chat',
                hasTask
                  ? { state: { fromTranslation: true, vendor: targetVendor } }
                  : undefined,
              )
            }
            className="flex h-9 items-center gap-[7px] rounded-lg border border-line bg-white px-3.5 text-[13px] font-medium text-ink-900"
          >
            <RobotOutlined className="text-[15px] text-ink-500" />
            去提问
          </button>
          <Dropdown
            disabled={!hasResult}
            trigger={['click']}
            menu={{
              items: [
                { key: 'cfg', label: '导出配置（.cfg）' },
                { key: 'report', label: '导出复核报告（.txt）' },
              ],
              onClick: ({ key }) => onExport?.(key as ExportFormat),
            }}
          >
            <button
              type="button"
              disabled={!hasResult}
              className="flex h-9 items-center gap-[7px] rounded-lg border border-line bg-white px-3.5 text-[13px] font-medium text-ink-900 disabled:cursor-not-allowed disabled:opacity-45"
            >
              <ExportOutlined className="text-[15px] text-ink-500" />
              导出
              <DownOutlined className="text-[10px] text-ink-400" />
            </button>
          </Dropdown>
        </div>
      </div>
    </section>
  )
}

function TranslateStatusRow({
  translated,
  generating,
  stale = false,
  total,
  durationMs,
  deviceSummary,
}: {
  translated: boolean
  generating: boolean
  stale?: boolean
  total?: number
  durationMs?: number
  deviceSummary: string
}) {
  return (
    <div className="flex flex-col gap-2 py-1 xl:flex-row xl:items-center xl:justify-between">
      <div className="flex flex-wrap items-center gap-2.5">
        {translated ? (
          <>
            {stale ? (
              <WarningOutlined className="text-[16px] text-warn" />
            ) : (
              <CheckCircleFilled className="text-[16px] text-success" />
            )}
            <span className={`text-[13px] font-medium ${stale ? 'text-warn' : 'text-ink-900'}`}>
              {stale ? '结果已过期' : '翻译完成'}
            </span>
            <span className="text-xs text-ink-500">
              {stale ? '源配置已修改，结果基于修改前内容' : `${deviceSummary} · 共 ${total ?? '—'} 条命令`}
            </span>
            {stale ? (
              <span className="text-[11px] text-ink-400">共 {total ?? '—'} 条命令</span>
            ) : (
              <span className="text-[11px] text-ink-400">
                耗时 {durationMs === undefined ? '—' : `${(durationMs / 1000).toFixed(1)} s`}
              </span>
            )}
          </>
        ) : generating ? (
          <>
            <LoadingOutlined spin className="text-[16px] text-brand" />
            <span className="text-[13px] font-medium text-ink-900">翻译中</span>
            <span className="text-xs text-ink-500">任务已提交，正在生成目标配置…</span>
          </>
        ) : (
          <span className="text-[12px] text-ink-400">尚未翻译 · 选择设备后点击「翻译」</span>
        )}
      </div>
      <div className="flex flex-wrap items-center gap-4">
        {translated ? (
          <>
            <span className="flex items-center gap-1.5 text-xs text-brand-strong">
              <LinkOutlined className="text-[12px]" />
              同步滚动
            </span>
            <span className="hidden text-[11px] text-ink-400 sm:inline">
              点击高亮行，查看映射与审计详情
            </span>
          </>
        ) : (
          <span className="hidden text-[11px] text-ink-400 sm:inline">
            翻译后可查看命令映射与审计详情
          </span>
        )}
      </div>
    </div>
  )
}

function CodeRow({
  item,
  onSelect,
  blockActive = false,
  dimmed = false,
}: {
  item: CodeLine
  onSelect?: (sourceNo: number, lineNo: number) => void
  /** 当前行属于选中映射块 */
  blockActive?: boolean
  dimmed?: boolean
}) {
  const stateClass = {
    focus: 'bg-brand-soft',
    success: 'bg-white',
    warn: 'bg-warn-soft',
    error: 'bg-danger-soft',
    muted: 'bg-white',
  }[item.state ?? 'muted']
  // 结果行可点击：与源配置行联动高亮，再次点击已选中的行取消选中
  const selectable = Boolean(onSelect) && item.sourceNo != null
  // 左侧竖线标示映射块，自动补齐的命令（无源行号）用虚线区分
  const edgeClass =
    item.sourceNo == null
      ? 'border-dashed border-line'
      : blockActive
        ? 'border-brand'
        : 'border-brand-soft'

  return (
    <div
      data-row={item.no}
      data-source-no={item.sourceNo ?? ''}
      onClick={
        selectable ? () => onSelect?.(item.sourceNo as number, item.no) : undefined
      }
      className={`flex h-6 items-center border-l-2 pr-2 transition-opacity ${edgeClass} ${stateClass} ${
        dimmed ? 'opacity-50' : ''
      } ${selectable ? 'cursor-pointer' : ''}`}
    >
      <span className="w-[38px] shrink-0 select-none text-right font-mono text-[11px] leading-none text-ink-300">
        {item.no}
      </span>
      <span className="ml-3 flex-1 whitespace-pre font-mono text-[12px] leading-none text-ink-900">
        {item.parts.map((part, index) => (
          <span
            key={`${item.no}-${index}`}
            className={part.strong ? 'font-semibold text-code-blue' : undefined}
          >
            {part.text}
          </span>
        ))}
      </span>
      <span className="ml-2 flex w-4 shrink-0 items-center justify-center">
        {item.icon === 'link' ? (
          <LinkOutlined className="text-[11px] text-brand" />
        ) : null}
        {item.icon === 'warning' ? (
          <WarningOutlined className="text-[11px] text-warn" />
        ) : null}
        {item.icon === 'error' ? (
          <ExclamationCircleFilled className="text-[11px] text-danger" />
        ) : null}
      </span>
    </div>
  )
}

function SourceEditor({
  value,
  onChange,
  marks,
  focusLine,
  onSelectLine,
  onCursorChange,
}: {
  value: string
  onChange: (next: string) => void
  marks?: Map<number, 'warn' | 'error'>
  focusLine?: number | null
  onSelectLine?: (sourceNo: number, lineNo?: number) => void
  onCursorChange?: (position: { line: number; column: number }) => void
}) {
  const [scrollTop, setScrollTop] = useState(0)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const lineCount = Math.max(1, value.split('\n').length)

  const markAt = (lineNo: number) => marks?.get(lineNo)
  const bgOf = (tone?: 'warn' | 'error') =>
    tone === 'error' ? 'bg-danger-soft' : tone === 'warn' ? 'bg-warn-soft' : ''
  const rowBg = (lineNo: number) =>
    lineNo === focusLine ? 'bg-brand-soft' : bgOf(markAt(lineNo))

  // 光标位置换算为行列号，供底部状态栏展示
  const reportCursor = (element: HTMLTextAreaElement) => {
    const before = element.value.slice(0, element.selectionStart)
    const rows = before.split('\n')
    onCursorChange?.({ line: rows.length, column: rows[rows.length - 1].length + 1 })
  }

  // 按点击位置换算行号，支持点击源配置行联动高亮
  const selectAt = (event: MouseEvent<HTMLDivElement>) => {
    if (!onSelectLine) return
    const rect = event.currentTarget.getBoundingClientRect()
    const offset = event.clientY - rect.top - TEXTAREA_PADDING_TOP + scrollTop
    const lineNo = Math.floor(offset / LINE_HEIGHT) + 1
    if (lineNo >= 1 && lineNo <= lineCount) onSelectLine(lineNo)
  }

  return (
    <div className="flex min-h-[280px] flex-1 overflow-hidden" onClick={selectAt}>
      <div className="w-[38px] shrink-0 overflow-hidden pt-1">
        <div style={{ transform: `translateY(-${scrollTop}px)` }}>
          {Array.from({ length: lineCount }, (_, index) => (
            <div
              key={index}
              className={`flex h-6 select-none items-center justify-end font-mono text-[11px] leading-none text-ink-300 ${rowBg(index + 1)}`}
            >
              {index + 1}
            </div>
          ))}
        </div>
      </div>
      <div className="relative min-w-0 flex-1">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 overflow-hidden pt-1"
        >
          <div style={{ transform: `translateY(-${scrollTop}px)` }}>
            {Array.from({ length: lineCount }, (_, index) => (
              <div key={index} className={`h-6 ${rowBg(index + 1)}`} />
            ))}
          </div>
        </div>
        <textarea
          ref={textareaRef}
          data-scroll="source"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          onScroll={(event) => setScrollTop(event.currentTarget.scrollTop)}
          onSelect={(event) => reportCursor(event.currentTarget)}
          onKeyUp={(event) => reportCursor(event.currentTarget)}
          wrap="off"
          spellCheck={false}
          placeholder="粘贴或导入设备配置…"
          className="thin-scrollbar relative h-full min-h-[280px] w-full flex-1 resize-none bg-transparent py-1 pl-3 pr-6 font-mono text-[12px] leading-6 text-ink-900 outline-none placeholder:text-ink-300"
        />
        {/* 选中映射时弱化非关联行，突出当前源行 */}
        {focusLine != null ? (
          <div
            aria-hidden
            className="pointer-events-none absolute inset-0 overflow-hidden pt-1"
          >
            <div style={{ transform: `translateY(-${scrollTop}px)` }}>
              {Array.from({ length: lineCount }, (_, index) => (
                <div
                  key={index}
                  className={`h-6 ${index + 1 === focusLine ? '' : 'bg-white/60'}`}
                />
              ))}
            </div>
          </div>
        ) : null}
        <div className="pointer-events-none absolute inset-y-0 right-2 w-10 overflow-hidden pt-1">
          <div style={{ transform: `translateY(-${scrollTop}px)` }}>
            {Array.from({ length: lineCount }, (_, index) => {
              const lineNo = index + 1
              const tone = markAt(lineNo)
              const focused = lineNo === focusLine
              return (
                <div key={index} className="flex h-6 items-center justify-end gap-1">
                  {tone === 'warn' ? (
                    <WarningOutlined className="text-[11px] text-warn" />
                  ) : tone === 'error' ? (
                    <ExclamationCircleFilled className="text-[11px] text-danger" />
                  ) : focused ? (
                    <LinkOutlined className="text-[11px] text-brand" />
                  ) : null}
                </div>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}

interface PanelDetail {
  title: string
  description: string
  tag?: { tone: 'blue' | 'green' | 'warn' | 'red' | 'gray'; text: string }
}

// 结果 tone 到状态标签的映射
const TONE_TAG: Record<string, { tone: 'green' | 'warn' | 'red'; text: string }> = {
  success: { tone: 'green', text: 'high' },
  warn: { tone: 'warn', text: 'medium' },
  error: { tone: 'red', text: 'low' },
}

// 无 warnings 时按 tone 给出的兜底说明
const TONE_FALLBACK: Record<string, string> = {
  success: '高置信度，无需人工复核',
  warn: '中等置信度，建议人工复核',
  error: '低置信度，需人工处理',
  muted: '视图/退出等自动补全命令，无需复核',
  focus: '视图/退出等自动补全命令，无需复核',
}

interface ConfigPanelProps {
  variant: 'source' | 'target'
  sourceVendor?: string
  sourceModel?: string
  targetVendor?: string
  targetModel?: string
  sourceText?: string
  sourceFileName?: string
  onImportFile?: (file: File) => void
  onSourceTextChange?: (next: string) => void
  translated?: boolean
  generating?: boolean
  stale?: boolean
  resultLines?: CodeLine[]
  resultTotal?: number
  warnCount?: number
  errorCount?: number
  sourceSaveState?: 'empty' | 'saved' | 'failed'
  sourceMarks?: Map<number, 'warn' | 'error'>
  focusLine?: number | null
  onSelectLine?: (sourceNo: number, lineNo?: number) => void
  detail?: PanelDetail
  /** 本面板处于放大态（图标与 aria-label 切换） */
  expanded?: boolean
  /** 对侧面板放大时隐藏本面板（display:none，保留 DOM 与滚动位置） */
  hidden?: boolean
  onToggleExpand?: () => void
  /** 翻译结果侧复制按钮 */
  onCopy?: () => void
}

function ConfigPanel({
  variant,
  sourceVendor = '',
  sourceModel = '',
  targetVendor = '',
  targetModel = '',
  sourceText = '',
  sourceFileName,
  onImportFile,
  onSourceTextChange,
  translated = false,
  generating = false,
  stale = false,
  resultLines,
  resultTotal,
  warnCount = 0,
  errorCount = 0,
  sourceSaveState = 'empty',
  sourceMarks,
  focusLine,
  onSelectLine,
  detail,
  expanded = false,
  hidden = false,
  onToggleExpand,
  onCopy,
}: ConfigPanelProps) {
  const isSource = variant === 'source'
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [cursor, setCursor] = useState({ line: 1, column: 1 })

  const displayLines: CodeLine[] = useMemo(
    () => (isSource ? [] : resultLines ?? []),
    [isSource, resultLines],
  )

  const sourceDeviceLabel =
    sourceVendor && sourceModel ? `${sourceVendor} · ${sourceModel}` : '未选择源设备'

  const targetDeviceLabel =
    targetVendor && targetModel ? `${targetVendor} · ${targetModel}` : '未选择目标设备'

  const displayFileName = isSource ? sourceFileName || '未导入文件' : targetDeviceLabel

  const sourceLineCount = sourceText ? sourceText.split('\n').length : 0
  const sourceStatusText =
    sourceLineCount === 0
      ? '暂无内容'
      : sourceSaveState === 'failed'
        ? `未能暂存 · 共 ${sourceLineCount} 行`
        : `已暂存 · 共 ${sourceLineCount} 行`

  const targetStatusText =
    warnCount === 0 && errorCount === 0
      ? '全部高置信度'
      : `${warnCount} 处有损 · ${errorCount} 处不支持`

  const handlePickFile = () => fileInputRef.current?.click()

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file && onImportFile) onImportFile(file)
    e.target.value = '' // 允许连续选同一个文件
  }

  const importButton = (
    <button type="button" className="flex items-center gap-1.5 text-xs" onClick={sourceText ? undefined : handlePickFile}>
      <UploadOutlined className="text-[13px]" />
      导入
    </button>
  )

  return (
    <section
      className="flex min-w-0 flex-none flex-col rounded-panel border border-line bg-white xl:h-[700px] xl:flex-1"
      style={hidden ? { display: 'none' } : undefined}
    >
      <div className="flex h-[54px] shrink-0 items-center justify-between border-b border-line px-[18px]">
        <div className="flex items-center gap-2.5">
          {isSource ? (
            <CodeOutlined className="text-[16px] text-brand-strong" />
          ) : (
            <TranslationOutlined className="text-[16px] text-brand-strong" />
          )}
          <span className="text-[14px] font-bold text-ink-900">
            {isSource ? '源配置' : '翻译结果'}
          </span>
          {isSource ? (
            <StatusTag tone="blue">可编辑</StatusTag>
          ) : generating ? (
            <StatusTag tone="blue">生成中</StatusTag>
          ) : translated && stale ? (
            <StatusTag tone="warn">已过期</StatusTag>
          ) : translated ? (
            <StatusTag tone="green">已生成</StatusTag>
          ) : (
            <StatusTag tone="gray">未生成</StatusTag>
          )}
        </div>
        <div className="flex items-center gap-3 text-[14px] text-ink-500">
          {isSource ? (
            <>
              <input
                ref={fileInputRef}
                type="file"
                accept={SOURCE_ACCEPT_EXTENSIONS.join(',')}
                style={{ display: 'none' }}
                onChange={handleFileChange}
              />
              {sourceText ? (
                <Popconfirm
                  title="导入将覆盖当前内容，是否继续？"
                  okText="继续"
                  cancelText="取消"
                  onConfirm={handlePickFile}
                >
                  {importButton}
                </Popconfirm>
              ) : (
                importButton
              )}
            </>
          ) : (
            <button type="button" aria-label="复制" onClick={onCopy}>
              <CopyOutlined className="text-[15px]" />
            </button>
          )}
          <button
            type="button"
            aria-label={expanded ? '退出放大' : '放大'}
            onClick={onToggleExpand}
          >
            {expanded ? (
              <CompressOutlined className="text-[15px]" />
            ) : (
              <ExpandAltOutlined className="text-[15px]" />
            )}
          </button>
        </div>
      </div>

      <div className="mt-3 flex h-9 shrink-0 items-center justify-between gap-3 border-y border-line-soft bg-head px-[18px]">
        <span className="flex min-w-0 items-center gap-1.5 text-[11px] text-ink-500">
          <FileTextOutlined className="shrink-0 text-[13px] text-ink-400" />
          <span className={`truncate ${isSource ? 'font-mono' : ''}`}>{displayFileName}</span>
        </span>
        <span
          className="max-w-[55%] shrink-0 truncate text-[10px] text-ink-400"
          title={isSource ? sourceDeviceLabel : undefined}
        >
          {isSource
            ? `UTF-8 · ${sourceDeviceLabel}`
            : translated
              ? `${resultTotal ?? '—'} 条映射`
              : '待生成'}
        </span>
      </div>

      {isSource ? (
        <SourceEditor
          value={sourceText}
          onChange={onSourceTextChange ?? (() => {})}
          marks={sourceMarks}
          focusLine={focusLine}
          onSelectLine={onSelectLine}
          onCursorChange={setCursor}
        />
      ) : generating ? (
        <div className="flex min-h-[280px] flex-1 flex-col items-center justify-center gap-2 px-4 text-center">
          <LoadingOutlined spin className="text-[24px] text-brand" />
          <span className="text-[12px] text-ink-500">正在生成翻译结果</span>
          <span className="text-[11px] text-ink-300">后端任务执行中，完成后自动展示</span>
        </div>
      ) : translated ? (
        <div data-scroll="result" className="thin-scrollbar relative min-h-[280px] flex-1 overflow-auto py-1">
          {displayLines.map((item, index) => (
            <CodeRow
              key={`${item.no}-${index}`}
              item={item}
              onSelect={onSelectLine}
              blockActive={focusLine != null && item.sourceNo === focusLine}
              dimmed={focusLine != null && item.sourceNo !== focusLine}
            />
          ))}
        </div>
      ) : (
        <div className="flex min-h-[280px] flex-1 flex-col items-center justify-center gap-2 px-4 text-center">
          <TranslationOutlined className="text-[24px] text-ink-300" />
          <span className="text-[12px] text-ink-400">尚未生成翻译结果</span>
          <span className="text-[11px] text-ink-300">
            选择源设备与目标设备后，点击上方「翻译」
          </span>
        </div>
      )}

      {/* 未选中行时整块隐藏，不保留占位内容 */}
      {detail ? (
        <div className="m-3 shrink-0 rounded-lg border border-line bg-soft px-3 py-2.5">
          <div className="flex items-center justify-between gap-2">
            <span className="flex min-w-0 items-center gap-1.5 text-[11px] font-medium text-ink-900">
              <LinkOutlined className="shrink-0 text-[11px] text-brand" />
              <span className="truncate">{detail.title}</span>
            </span>
            {detail.tag ? <StatusTag tone={detail.tag.tone}>{detail.tag.text}</StatusTag> : null}
          </div>
          <p className="mt-1.5 truncate text-[11px] leading-[1.6] text-ink-500">
            {detail.description}
          </p>
        </div>
      ) : null}

      <div className="flex h-[26px] shrink-0 items-center justify-between border-t border-line px-3 text-[10px] text-ink-400">
        <span>
          {isSource
            ? `行 ${cursor.line}，列 ${cursor.column}`
            : translated
              ? `共 ${(resultLines ?? []).length} 行`
              : '—'}
        </span>
        <span>
          {isSource ? sourceStatusText : translated ? targetStatusText : '—'}
        </span>
      </div>
    </section>
  )
}

interface WarningGroup {
  code: string
  label: string
  severity: 'warn' | 'error'
  lines: number[]
  messages: string[]
}

// warnings 的 code 到中文标题的映射
const WARNING_LABELS: Record<string, string> = {
  unknown_command: '未识别的命令',
  intf_unmapped: '接口名未做厂商映射',
  intf_translated: '接口前缀已按厂商规则转换',
  unsupported_entity: '目标设备不支持',
  invalid_param: '参数校验失败',
  unverified_impl: '目标实现未验证',
  low_confidence: '实现置信度偏低',
}

// 翻译记录卡片中的单侧设备信息
function HistoryDeviceLine({ label, vendor, model }: { label: string; vendor: string; model: string }) {
  return (
    <div className="flex min-w-0 items-center gap-2">
      <span className="shrink-0 rounded bg-soft px-1.5 py-[1px] text-[10px] text-ink-500">{label}</span>
      <span className="shrink-0 text-[12px] font-medium text-ink-700">{vendor}</span>
      <span className="min-w-0 truncate font-mono text-[12px] text-ink-500" title={model}>
        {model}
      </span>
    </div>
  )
}

function summarizeAudit(lines: TranslationResultLine[] | undefined) {
  const stats = { total: 0, high: 0, medium: 0, low: 0 }
  for (const line of lines ?? []) {
    // muted 为视图行 / 注释 / 空行，不参与置信度统计
    if (line.tone === 'success') {
      stats.high += 1
      stats.total += 1
    } else if (line.tone === 'warn') {
      stats.medium += 1
      stats.total += 1
    } else if (line.tone === 'error') {
      stats.low += 1
      stats.total += 1
    }
  }
  return stats
}

// 选中结果行时，审计面板「检查结果」区的数据
interface AuditReview {
  /** 结果行序号，用于同步文本框草稿 */
  key: number
  /** 处理提示（warn / error 行取详情副标题） */
  hint?: string
  command: string
  tone: 'success' | 'warn' | 'error'
  /** 高置信度行的判定依据 */
  reason?: string
  onAccept?: () => void
  onAcceptEdited?: (text: string) => void
  onDefer?: () => void
}

function AuditPanel({
  result,
  lines,
  review,
  checkpoints,
  canCreateCheckpoint,
  onSelectLine,
  onCreateCheckpoint,
  onRestoreCheckpoint,
  onDeleteCheckpoint,
}: {
  result: TranslationResult | null
  lines: TranslationResultLine[]
  review?: AuditReview | null
  checkpoints: Checkpoint[]
  canCreateCheckpoint: boolean
  onSelectLine?: (lineNo: number) => void
  onCreateCheckpoint?: () => void
  onRestoreCheckpoint?: (checkpoint: Checkpoint) => void
  onDeleteCheckpoint?: (id: string) => void
}) {
  const stats = useMemo(() => summarizeAudit(lines), [lines])
  // 文本框始终可编辑，切换选中行时同步为该行命令
  const [draft, setDraft] = useState('')
  // 检查点列表折叠状态
  const [checkpointsOpen, setCheckpointsOpen] = useState(false)
  useEffect(() => {
    setDraft(review?.command ?? '')
  }, [review?.key, review?.command])

  const dirty = review != null && draft.trim() !== review.command.trim()
  const handleAccept = () => {
    if (!review) return
    // 文本被改过时直接采纳会丢失修改，提示改用「修改后采纳」
    if (dirty) {
      message.warning('配置已修改，请点击「修改后采纳」保存修改')
      return
    }
    review.onAccept?.()
  }
  const handleAcceptEdited = () => {
    if (!review) return
    const text = draft.trim()
    if (!text) return
    review.onAcceptEdited?.(text)
  }
  // 按 code 聚合行级 warnings，一类问题一条
  const groups = useMemo(() => {
    const map = new Map<string, WarningGroup>()
    for (const warning of result?.warnings ?? []) {
      const code = warning.code || 'unknown'
      const group = map.get(code) ?? {
        code,
        label: WARNING_LABELS[code] ?? '其他提示',
        severity: warning.severity === 'error' ? 'error' : 'warn',
        lines: [],
        messages: [],
      }
      if (!group.lines.includes(warning.no)) group.lines.push(warning.no)
      if (warning.severity === 'error') group.severity = 'error'
      if (!group.messages.includes(warning.message)) group.messages.push(warning.message)
      map.set(code, group)
    }
    return [...map.values()].sort((a, b) => {
      if (a.severity !== b.severity) return a.severity === 'error' ? -1 : 1
      return b.lines.length - a.lines.length
    })
  }, [result])
  const percent = (value: number) =>
    stats.total === 0 ? '0.0%' : `${((value / stats.total) * 100).toFixed(1)}%`

  return (
    <section className="flex flex-col rounded-panel border border-line bg-white xl:h-[700px] xl:w-[308px] xl:flex-none">
      <div className="flex h-[54px] shrink-0 items-center justify-between border-b border-line px-[18px]">
        <div className="flex items-center gap-2.5">
          <SafetyCertificateOutlined className="text-[16px] text-brand-strong" />
          <span className="text-[14px] font-bold text-ink-900">审计面板</span>
        </div>
        {stats.total === 0 ? (
          <StatusTag tone="gray">待生成</StatusTag>
        ) : stats.medium + stats.low > 0 ? (
          <StatusTag tone="warn">待复核 {stats.medium + stats.low}</StatusTag>
        ) : (
          <StatusTag tone="green">全部通过</StatusTag>
        )}
      </div>

      <div className="thin-scrollbar flex-1 space-y-4 overflow-y-auto px-[18px] pb-4 pt-4">
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-[13px] font-medium text-ink-900">概览</span>
            <span className="text-[11px] text-ink-400">共 {stats.total} 条</span>
          </div>

          <div className="flex h-1.5 items-stretch gap-[3px] overflow-hidden rounded-full">
            {stats.total === 0 ? (
              <span className="flex-1 rounded-full bg-line-soft" />
            ) : (
              <>
                {stats.high > 0 && (
                  <span
                    className="rounded-full bg-success"
                    style={{ flexGrow: stats.high, flexBasis: 0 }}
                  />
                )}
                {stats.medium > 0 && (
                  <span
                    className="rounded-full bg-[#D9A34E]"
                    style={{ flexGrow: stats.medium, flexBasis: 0 }}
                  />
                )}
                {stats.low > 0 && (
                  <span
                    className="rounded-full bg-danger"
                    style={{ flexGrow: stats.low, flexBasis: 0 }}
                  />
                )}
              </>
            )}
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[12px] text-success">✓ high</span>
              <span className="flex items-baseline gap-2">
                <span className="font-mono text-[13px] font-semibold text-ink-900">
                  {stats.high}
                </span>
                <span className="w-[46px] text-right font-mono text-[10px] text-ink-400">
                  {percent(stats.high)}
                </span>
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-[12px] text-warn">⚠ medium</span>
              <span className="flex items-baseline gap-2">
                <span className="font-mono text-[13px] font-semibold text-ink-900">
                  {stats.medium}
                </span>
                <span className="w-[46px] text-right font-mono text-[10px] text-ink-400">
                  {percent(stats.medium)}
                </span>
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-[12px] text-danger">✕ low</span>
              <span className="flex items-baseline gap-2">
                <span className="font-mono text-[13px] font-semibold text-ink-900">
                  {stats.low}
                </span>
                <span className="w-[46px] text-right font-mono text-[10px] text-ink-400">
                  {percent(stats.low)}
                </span>
              </span>
            </div>
          </div>

          <div className="flex h-[30px] items-center rounded-md bg-soft px-2.5 text-[11px] text-ink-500">
            {stats.total === 0
              ? '暂无翻译结果'
              : `需复核 ${stats.medium} · 需人工处理 ${stats.low}`}
          </div>
        </div>

        <div className="space-y-2.5">
          <div className="flex items-center justify-between">
            <span className="text-[13px] font-bold text-ink-900">警告 ({groups.length})</span>
            <span className="text-[11px] text-ink-400">定位到配置行</span>
          </div>
          <div className="space-y-1">
            {groups.length === 0 ? (
              <p className="rounded-md bg-soft px-2.5 py-2 text-[11px] text-ink-500">
                {stats.total === 0 ? '暂无翻译结果' : '全部高置信度，无需人工复核'}
              </p>
            ) : (
              groups.map((group) => (
                <button
                  type="button"
                  key={group.code}
                  onClick={() => onSelectLine?.(group.lines[0])}
                  className="flex w-full items-center gap-2 rounded-md border border-transparent px-2.5 py-2 text-left hover:bg-soft"
                >
                  {group.severity === 'error' ? (
                    <span className="flex h-4 w-4 shrink-0 items-center justify-center rounded-full border border-danger text-[9px] text-danger">
                      ×
                    </span>
                  ) : (
                    <WarningOutlined className="shrink-0 text-[13px] text-warn" />
                  )}
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-[11px] font-medium text-ink-900">
                      {group.label}
                    </span>
                    <span className="mt-0.5 block truncate text-[10px] text-ink-400">
                      {group.lines.map((no) => `L${no}`).join('、')} · {group.lines.length} 行
                    </span>
                  </span>
                  <span className="text-[10px] text-ink-300">›</span>
                </button>
              ))
            )}
          </div>
        </div>

        <div className="space-y-2.5">
          <span className="text-[13px] font-bold text-ink-900">检查结果</span>
          {review ? (
            review.tone === 'success' ? (
              // 高置信度行：只给通过结论与判定依据，不提供操作按钮
              <div className="space-y-2">
                <div className="flex h-8 items-center gap-1.5 rounded-md bg-success-soft px-2.5 text-[11px] font-medium text-success">
                  <CheckCircleFilled className="text-[12px]" />
                  高置信度 · 无需人工处理
                </div>
                <p className="text-[11px] leading-[1.6] text-ink-500">
                  {review.reason ?? '知识库命令模板确定，未发现参数或映射告警'}
                </p>
                <input
                  value={review.command}
                  readOnly
                  className="h-9 w-full rounded-md border border-line bg-soft px-2.5 font-mono text-[11px] text-ink-700"
                />
              </div>
            ) : (
              <div className="space-y-2">
                <p className="text-[11px] leading-[1.6] text-ink-500">
                  {review.hint || '该行建议人工确认'}
                </p>
                <input
                  value={draft}
                  onChange={(event) => setDraft(event.target.value)}
                  className="h-9 w-full rounded-md border border-brand-line bg-white px-2.5 font-mono text-[11px] text-ink-900 outline-none focus:border-brand"
                />
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={handleAccept}
                    className="flex h-8 flex-1 items-center justify-center rounded-md bg-success text-[11px] font-medium text-white transition-opacity hover:opacity-90"
                  >
                    采纳
                  </button>
                  <Popconfirm
                    title="确认按修改后的配置采纳？"
                    description="采纳后该行置信度将标记为高。"
                    okText="确认采纳"
                    cancelText="取消"
                    onConfirm={handleAcceptEdited}
                    disabled={!draft.trim()}
                  >
                    <button
                      type="button"
                      disabled={!draft.trim()}
                      className="flex h-8 flex-1 items-center justify-center rounded-md border border-success-line bg-success-soft text-[11px] font-medium text-success transition-colors hover:border-success disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      修改后采纳
                    </button>
                  </Popconfirm>
                  <button
                    type="button"
                    onClick={review.onDefer}
                    className="flex h-8 flex-1 items-center justify-center rounded-md border border-line bg-white text-[11px] text-ink-500 transition-colors hover:bg-soft"
                  >
                    暂不处理
                  </button>
                </div>
              </div>
            )
          ) : result ? (
            stats.medium + stats.low > 0 ? (
              <button
                type="button"
                onClick={() => {
                  const first = lines.find(
                    (item) =>
                      item.source_no != null && (item.tone === 'warn' || item.tone === 'error'),
                  )
                  if (first?.source_no != null) onSelectLine?.(first.source_no)
                }}
                className="flex h-8 w-full items-center justify-center rounded-md bg-warn-soft text-[11px] text-warn transition-colors hover:bg-warn-soft/70"
              >
                待处理 {stats.medium + stats.low} 行 · 已通过 {stats.high} 行
              </button>
            ) : (
              <div className="flex h-8 items-center justify-center gap-1.5 rounded-md bg-success-soft text-[11px] text-success">
                <CheckCircleFilled className="text-[12px]" />
                全部高置信度，无需复核
              </div>
            )
          ) : (
            <p className="text-[10px] leading-[1.6] text-ink-400">
              生成翻译结果后显示检查项
            </p>
          )}
        </div>
      </div>

      <div className="shrink-0 space-y-2 border-t border-line px-[18px] py-3.5">
        <Tooltip
          title={canCreateCheckpoint ? '保存当前已处理的审计结果，可随时恢复' : '暂无已处理行，无法生成检查点'}
          placement="top"
        >
          <span className="w-full">
            <button
              type="button"
              disabled={!canCreateCheckpoint}
              onClick={onCreateCheckpoint}
              className={`flex h-9 w-full items-center justify-center gap-[7px] rounded-lg border text-[13px] font-medium transition-colors ${
                canCreateCheckpoint
                  ? 'border-brand-line bg-white text-brand-strong hover:bg-brand-soft'
                  : 'cursor-not-allowed border-line bg-soft text-ink-300'
              }`}
            >
              <FlagOutlined className="text-[14px]" />
              生成检查点
            </button>
          </span>
        </Tooltip>
        <p className="text-center text-[10px] leading-[1.5] text-ink-400">
          保存当前配置、映射关系与审计结果
        </p>
        {checkpoints.length > 0 ? (
          <div className="space-y-1.5 pt-1">
            <button
              type="button"
              onClick={() => setCheckpointsOpen((v) => !v)}
              className="flex h-7 w-full items-center justify-between rounded px-1 text-[11px] text-ink-500 hover:bg-soft"
            >
              <span>检查点记录（{checkpoints.length}）</span>
              <DownOutlined
                className={`text-[10px] transition-transform ${checkpointsOpen ? 'rotate-0' : '-rotate-90'}`}
              />
            </button>
            {checkpointsOpen ? (
              <div className="thin-scrollbar max-h-44 space-y-1.5 overflow-y-auto">
                {checkpoints.map((cp) => {
                  const reviewed = Object.values(cp.reviews)
                  const edited = reviewed.filter((r) => r.text != null).length
                  const accepted = reviewed.length - edited
                  const time = new Date(cp.createdAt).toLocaleTimeString('zh-CN', {
                    hour: '2-digit',
                    minute: '2-digit',
                  })
                  return (
                    <div
                      key={cp.id}
                      className="flex items-center justify-between gap-2 rounded-md border border-line bg-white px-2.5 py-1.5"
                    >
                      <div className="min-w-0 flex-1">
                        <div className="truncate text-[11px] text-ink-700">
                          {cp.name}
                        </div>
                        <div className="text-[10px] text-ink-400">
                          {time} · 已采纳 {accepted} · 已修改 {edited}
                        </div>
                      </div>
                      <div className="flex shrink-0 items-center gap-1 text-ink-400">
                        <button
                          type="button"
                          aria-label="恢复检查点"
                          onClick={() => onRestoreCheckpoint?.(cp)}
                          className="flex h-6 w-6 items-center justify-center rounded hover:bg-brand-soft hover:text-brand"
                        >
                          <HistoryOutlined className="text-[12px]" />
                        </button>
                        <button
                          type="button"
                          aria-label="删除检查点"
                          onClick={() => onDeleteCheckpoint?.(cp.id)}
                          className="flex h-6 w-6 items-center justify-center rounded hover:bg-danger-soft hover:text-danger"
                        >
                          <DeleteOutlined className="text-[12px]" />
                        </button>
                      </div>
                    </div>
                  )
                })}
              </div>
            ) : null}
          </div>
        ) : null}
      </div>
    </section>
  )
}

export function TranslatePage() {
  const source = useSourceConfig()
  const cachedSession = useMemo(() => readSession(), [])
  const [deviceType, setDeviceType] = useState(cachedSession?.deviceType ?? '')
  const [sourceDevice, setSourceDevice] = useState({
    vendor: cachedSession?.sourceVendor ?? '',
    model: cachedSession?.sourceModel ?? '',
  })
  const [targetDevice, setTargetDevice] = useState({
    vendor: cachedSession?.targetVendor ?? '',
    model: cachedSession?.targetModel ?? '',
  })
  // 设备档案：历史恢复时按厂商 + 型号反查设备类型，保证类型与设备选择一致
  const devicesRef = useRef<Device[] | null>(null)
  // 选中的源配置行与结果行：两侧同时高亮为 focus，底部详情卡片同步更新
  const [selection, setSelection] = useState<{ sourceNo: number; lineNo: number | null } | null>(
    null,
  )
  // 选中行两侧的滚动对齐请求：sourceLine 为源行，targetRow 为结果行（为空时取该源行首行）
  const [align, setAlign] = useState<{
    sourceLine?: number
    targetRow?: number
    token: number
  } | null>(null)
  const { status, result, requestId, error, submittedSignature, start, resume, reset } =
    useTranslationTask()
  // 审计处理结果：结果行序号 → 覆盖后的 tone 与文本（采纳 / 修改后采纳）
  const [reviews, setReviews] = useState<
    Map<number, { tone: TranslationTone; text?: string }>
  >(new Map())
  // 当前翻译任务的检查点列表（本地快照）
  const [checkpoints, setCheckpoints] = useState<Checkpoint[]>([])
  // 生成检查点弹框
  const [checkpointModalOpen, setCheckpointModalOpen] = useState(false)
  const [checkpointName, setCheckpointName] = useState('')
  // 翻译历史记录抽屉
  const [historyOpen, setHistoryOpen] = useState(false)
  const [historyLoading, setHistoryLoading] = useState(false)
  const [historyItems, setHistoryItems] = useState<TranslationListItem[]>([])
  // 多取一条用于判断是否还有更早记录
  const visibleHistoryItems = historyItems.slice(0, HISTORY_LIMIT)
  // 面板放大：source / result 互斥展开，null 为默认双栏
  const [expandedPanel, setExpandedPanel] = useState<'source' | 'result' | null>(null)
  useEffect(() => {
    setCheckpoints(loadCheckpoints(requestId))
  }, [requestId])

  const toggleExpandedPanel = (panel: 'source' | 'result') =>
    setExpandedPanel((cur) => (cur === panel ? null : panel))

  // 复制翻译结果：与导出保持一致，使用人工处理后的行
  const handleCopyResult = async () => {
    const text = reviewedLines.map((line) => line.text).join('\n')
    if (!text) {
      message.warning('暂无可复制的翻译结果')
      return
    }
    try {
      await navigator.clipboard.writeText(text)
      message.success('已复制翻译结果')
    } catch {
      message.error('复制失败，请手动选择复制')
    }
  }

  const openCheckpointModal = () => {
    setCheckpointName(`检查点 ${new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}`)
    setCheckpointModalOpen(true)
  }
  const handleCreateCheckpoint = () => {
    if (!requestId) return
    setCheckpoints(saveCheckpoint(requestId, checkpointName, reviews))
    setCheckpointModalOpen(false)
    message.success('检查点已保存')
  }
  const handleRestoreCheckpoint = (cp: Checkpoint) => {
    const next = new Map<number, { tone: TranslationTone; text?: string }>()
    for (const [key, override] of Object.entries(cp.reviews)) {
      next.set(Number(key), { tone: override.tone as TranslationTone, text: override.text })
    }
    setReviews(next)
    setSelection(null)
    setAlign(null)
    message.success('已恢复检查点')
  }
  const handleDeleteCheckpoint = (id: string) => {
    if (!requestId) return
    setCheckpoints(deleteCheckpoint(requestId, id))
  }

  const loadHistory = async () => {
    setHistoryLoading(true)
    try {
      setHistoryItems(await listTranslations(HISTORY_LIMIT + 1))
    } catch {
      message.error('加载翻译记录失败')
    } finally {
      setHistoryLoading(false)
    }
  }
  const handleOpenHistory = () => {
    setHistoryOpen(true)
    void loadHistory()
  }
  const handleRestoreHistory = async (item: TranslationListItem) => {
    try {
      const src = await getTranslationSource(item.request_id)
      const matched =
        devicesRef.current?.find(
          (device) =>
            device.vendor === src.source_vendor && device.model === src.source_model,
        ) ??
        devicesRef.current?.find(
          (device) =>
            device.vendor === src.target_vendor && device.model === src.target_model,
        )
      if (matched) setDeviceType(matched.device_type)
      setSourceDevice({ vendor: src.source_vendor, model: src.source_model })
      setTargetDevice({ vendor: src.target_vendor, model: src.target_model })
      source.setText(src.source_text)
      const signature = translationSignature({
        source_text: src.source_text,
        source_vendor: src.source_vendor,
        source_model: src.source_model,
        target_vendor: src.target_vendor,
        target_model: src.target_model,
      })
      setReviews(new Map())
      setCheckpoints(loadCheckpoints(item.request_id))
      setSelection(null)
      setAlign(null)
      resume(item.request_id, signature)
      setHistoryOpen(false)
      message.success('已恢复历史翻译')
    } catch {
      message.error('恢复历史翻译失败，请重试')
    }
  }
  // 稳定的回调引用：避免每次渲染都触发下拉组件的同步 effect，把历史恢复的设备选择覆盖回去
  const handleSourceDeviceChange = useCallback((vendor: string, model: string) => {
    setSourceDevice((prev) =>
      prev.vendor === vendor && prev.model === model ? prev : { vendor, model },
    )
  }, [])
  const handleTargetDeviceChange = useCallback((vendor: string, model: string) => {
    setTargetDevice((prev) =>
      prev.vendor === vendor && prev.model === model ? prev : { vendor, model },
    )
  }, [])
  const handleDevicesLoaded = useCallback((items: Device[]) => {
    devicesRef.current = items
  }, [])

  // 合并人工处理结果后的行视图，供展示、统计与导出共用
  const reviewedLines = useMemo<TranslationResultLine[]>(() => {
    if (!result) return []
    return result.lines.map((line, index) => {
      const review = reviews.get(index)
      if (!review) return line
      return { ...line, tone: review.tone, text: review.text ?? line.text }
    })
  }, [result, reviews])

  // 回到本页时按已保存的 requestId 从后端恢复结果（避免把大结果写进 localStorage）
  useEffect(() => {
    if (!cachedSession?.requestId || !cachedSession.submittedSignature) return
    resume(cachedSession.requestId, cachedSession.submittedSignature)
  }, [cachedSession, resume])

  // 设备选择与任务信息随页面状态变化写入会话快照
  useEffect(() => {
    writeSession({
      deviceType,
      sourceVendor: sourceDevice.vendor,
      sourceModel: sourceDevice.model,
      targetVendor: targetDevice.vendor,
      targetModel: targetDevice.model,
      requestId,
      submittedSignature,
    })
  }, [deviceType, sourceDevice, targetDevice, requestId, submittedSignature])

  const generating = status === 'pending' || status === 'running'
  const translated = status === 'succeeded' && result !== null
  // 已提交过任务或已有源配置（含历史恢复）时，去提问需带上任务上下文提示
  const hasTranslationTask = Boolean(requestId) || source.text.trim().length > 0

  // 旧版本任务的结果不含 entity_id / warnings / entities，恢复后自动重译一次以加载详情
  const legacyRetriedRef = useRef(false)
  useEffect(() => {
    if (!translated || !result || legacyRetriedRef.current) return
    if (result.entities !== undefined && result.warnings !== undefined) return
    if (submittedSignature === null || !source.text.trim()) return
    if (!sourceDevice.vendor || !sourceDevice.model || !targetDevice.vendor) return
    if (!targetDevice.model) return
    const current = translationSignature({
      source_text: source.text,
      source_vendor: sourceDevice.vendor,
      source_model: sourceDevice.model,
      target_vendor: targetDevice.vendor,
      target_model: targetDevice.model,
    })
    if (current !== submittedSignature) return
    legacyRetriedRef.current = true
    void start({
      source_text: source.text,
      source_vendor: sourceDevice.vendor,
      source_model: sourceDevice.model,
      target_vendor: targetDevice.vendor,
      target_model: targetDevice.model,
    })
  }, [translated, result, submittedSignature, source.text, sourceDevice, targetDevice, start])

  const targetResultLines = useMemo<CodeLine[]>(
    () =>
      reviewedLines.map((item, index) => {
        const focused = selection !== null && item.source_no === selection.sourceNo
        // warn / error 行保持原图标，success / muted 行聚焦后换成链接图标
        const baseIcon: CodeLine['icon'] =
          item.tone === 'warn' ? 'warning' : item.tone === 'error' ? 'error' : undefined
        return {
          no: index + 1,
          parts: [{ text: item.text }],
          state: focused ? 'focus' : item.tone,
          icon: baseIcon ?? (focused ? 'link' : undefined),
          sourceNo: item.source_no,
        }
      }),
    [reviewedLines, selection],
  )

  // 新的翻译结果到达后清除选中与人工处理记录
  useEffect(() => {
    setSelection(null)
    setAlign(null)
    setReviews(new Map())
  }, [result])

  const handleSelectLine = (sourceNo: number, lineNo?: number) => {
    // 结果已过期时禁用选中高亮，避免误导为当前结果的核对状态
    if (stale) return
    const toggling =
      selection !== null &&
      selection.sourceNo === sourceNo &&
      selection.lineNo === (lineNo ?? null)
    if (toggling) {
      setSelection(null)
      setAlign(null)
      return
    }
    setSelection({ sourceNo, lineNo: lineNo ?? null })
    // 两侧滚动到同一高度，使源行与其对应的结果行水平对齐
    setAlign({ sourceLine: sourceNo, targetRow: lineNo, token: Date.now() })
  }

  // 选中行对齐：取两个面板都能达到的共同高度，再分别把目标行滚动到该位置
  useEffect(() => {
    if (align?.sourceLine == null) return
    const { sourceLine, targetRow } = align
    const frame = requestAnimationFrame(() => {
      const sourceEl = document.querySelector<HTMLTextAreaElement>('[data-scroll="source"]')
      const resultEl = document.querySelector<HTMLElement>('[data-scroll="result"]')
      if (!sourceEl || !resultEl) return
      const row =
        (targetRow != null
          ? resultEl.querySelector<HTMLElement>(`[data-row="${targetRow}"]`)
          : null) ??
        resultEl.querySelector<HTMLElement>(`[data-source-no="${sourceLine}"]`)
      if (!row) return
      // 两行在各自滚动内容中的起点（含顶部内边距，保持口径一致）
      const sourceTop = (sourceLine - 1) * LINE_HEIGHT + TEXTAREA_PADDING_TOP
      const rowTop =
        row.getBoundingClientRect().top -
        resultEl.getBoundingClientRect().top +
        resultEl.scrollTop
      const sourceMax = Math.max(0, sourceEl.scrollHeight - sourceEl.clientHeight)
      const resultMax = Math.max(0, resultEl.scrollHeight - resultEl.clientHeight)
      // 面板内容不足时无法居中，取两侧都能满足的可行高度区间，尽量靠近中线
      const low = Math.max(0, sourceTop - sourceMax, rowTop - resultMax)
      const high = Math.min(
        sourceTop,
        rowTop,
        sourceEl.clientHeight - LINE_HEIGHT,
        resultEl.clientHeight - LINE_HEIGHT,
      )
      const center =
        Math.min(sourceEl.clientHeight, resultEl.clientHeight) / 2 - LINE_HEIGHT / 2
      const anchor = high >= low ? Math.min(Math.max(center, low), high) : low
      sourceEl.scrollTop = Math.max(0, sourceTop - anchor)
      resultEl.scrollTop = Math.max(0, rowTop - anchor)
    })
    return () => cancelAnimationFrame(frame)
  }, [align])

  const sourceMarks = useMemo(() => {
    const marks = new Map<number, 'warn' | 'error'>()
    for (const item of reviewedLines) {
      if (item.source_no === null || item.source_no === undefined) continue
      if (item.tone !== 'warn' && item.tone !== 'error') continue
      // 同一源行命中多行时取更严重的级别
      if (marks.get(item.source_no) === 'error') continue
      marks.set(item.source_no, item.tone)
    }
    return marks
  }, [reviewedLines])

  const resultStats = useMemo(() => {
    let warn = 0
    let error = 0
    for (const item of reviewedLines) {
      if (item.tone === 'warn') warn += 1
      else if (item.tone === 'error') error += 1
    }
    return { warn, error }
  }, [reviewedLines])

  const stale = useMemo(() => {
    if (!translated || submittedSignature === null) return false
    const current = translationSignature({
      source_text: source.text,
      source_vendor: sourceDevice.vendor,
      source_model: sourceDevice.model,
      target_vendor: targetDevice.vendor,
      target_model: targetDevice.model,
    })
    return current !== submittedSignature
  }, [translated, submittedSignature, source.text, sourceDevice, targetDevice])

  // 结果转为过期时清空已有选中，避免残留高亮
  useEffect(() => {
    if (!stale) return
    setSelection(null)
    setAlign(null)
  }, [stale])

  const entityDescriptions = useMemo(() => {
    const map = new Map<string, string | null>()
    for (const entity of result?.entities ?? []) map.set(entity.id, entity.description)
    return map
  }, [result])

  const warningMap = useMemo(() => {
    const map = new Map<number, string[]>()
    for (const warning of result?.warnings ?? []) {
      const messages = map.get(warning.no) ?? []
      messages.push(warning.message)
      map.set(warning.no, messages)
    }
    return map
  }, [result])

  // 源侧详情：显示选中行对应的实体描述
  const sourceDetail = useMemo<PanelDetail | undefined>(() => {
    if (!selection) return undefined
    const lineNo = selection.sourceNo
    const lines = source.text ? source.text.split('\n').map((line) => line.replace(/\r$/, '')) : []
    const text = (lines[lineNo - 1] ?? '').trim()
    const mapped = reviewedLines.filter((item) => item.source_no === lineNo)
    const entityId = mapped.find((item) => item.entity_id)?.entity_id ?? null
    const legacy = result !== null && result.entities === undefined
    const description = entityId
      ? (entityDescriptions.get(entityId) ?? '暂无实体说明')
      : legacy && mapped.length > 0
        ? '结果由旧版本生成，正在重新翻译以加载实体说明'
        : text === ''
          ? '空行'
          : text.startsWith('#') || text.startsWith('!')
            ? '注释行'
            : mapped.some((item) => item.tone === 'error')
              ? '未识别的命令，已原样保留'
              : mapped.length > 0
                ? '视图行 · 不参与命令翻译'
                : '该行未参与翻译'
    const tones = mapped.map((item) => item.tone)
    const severity = tones.includes('error')
      ? 'error'
      : tones.includes('warn')
        ? 'warn'
        : tones.includes('success')
          ? 'success'
          : null
    return {
      title: `L${lineNo} · ${text || '空行'}`,
      description,
      tag: severity ? TONE_TAG[severity] : undefined,
    }
  }, [selection, source.text, result, reviewedLines, entityDescriptions])

  // 目的侧详情：显示选中结果行的行级 warnings
  const targetDetail = useMemo<PanelDetail | undefined>(() => {
    if (!selection) return undefined
    if (!result) {
      return {
        title: '暂无翻译结果',
        description: '生成翻译结果后，这里显示目标命令与复核提示。',
      }
    }
    const lines = reviewedLines
    // 后端 no 是源配置行号，可能重复；按结果行序号（界面上显示的 L 编号）定位
    const index =
      selection.lineNo != null
        ? selection.lineNo - 1
        : lines.findIndex((item) => item.source_no === selection.sourceNo)
    const line = index >= 0 ? lines[index] : undefined
    if (!line) {
      return {
        title: `L${selection.sourceNo} · 无对应结果`,
        description: '该源配置行未产出翻译结果。',
      }
    }
    const review = reviews.get(index)
    // 优先按源行号匹配；旧渲染器的视图行 warning 挂在触发命令行上，回退到结果行号
    let messages = line.source_no == null ? [] : (warningMap.get(line.source_no) ?? [])
    if (messages.length === 0) messages = warningMap.get(line.no) ?? []
    const description = review
      ? review.text != null
        ? '已人工修改并采纳，置信度标记为高'
        : '已人工采纳，置信度标记为高'
      : messages.length
        ? messages.join('；')
        : line.source_no == null
          ? '渲染器自动补齐的命令，非源配置内容'
          : (TONE_FALLBACK[line.tone] ?? '无需复核')
    return {
      title: `L${index + 1} · ${line.text.trim() || '空行'}`,
      description,
      tag: TONE_TAG[line.tone],
    }
  }, [selection, result, reviewedLines, warningMap, reviews])

  // 采纳后自动定位到下一处待处理行：先向后找，到末尾回到开头
  const advanceAfterReview = (from: number) => {
    const order = [
      ...reviewedLines.map((_, index) => index).slice(from + 1),
      ...reviewedLines.map((_, index) => index).slice(0, from),
    ]
    const next = order.find((index) => {
      const item = reviewedLines[index]
      return item.source_no != null && (item.tone === 'warn' || item.tone === 'error')
    })
    const line = next == null ? undefined : reviewedLines[next]
    if (next == null || !line || line.source_no == null) {
      setSelection(null)
      setAlign(null)
      return
    }
    setSelection({ sourceNo: line.source_no, lineNo: next + 1 })
    setAlign({ sourceLine: line.source_no, targetRow: next + 1, token: Date.now() })
  }

  // 选中 warn / error 行时，审计面板进入人工处理模式
  const reviewTarget = useMemo<AuditReview | null>(() => {
    if (!selection || !result) return null
    let index =
      selection.lineNo != null
        ? selection.lineNo - 1
        : reviewedLines.findIndex((item) => item.source_no === selection.sourceNo)
    // 点击源行时优先落到该行下最需要处理的 warn / error 结果行
    if (selection.lineNo == null) {
      const pending = reviewedLines.findIndex(
        (item) =>
          item.source_no === selection.sourceNo &&
          (item.tone === 'warn' || item.tone === 'error'),
      )
      if (pending >= 0) index = pending
    }
    const line = index >= 0 ? reviewedLines[index] : undefined
    if (!line) return null
    // 高置信度行只展示通过结论与判定依据
    if (line.tone === 'success') {
      const reviewed = reviews.get(index)
      const reason = reviewed
        ? reviewed.text != null
          ? '已人工修改并采纳，置信度标记为高'
          : '已人工采纳，置信度标记为高'
        : line.entity_id
          ? `命中实体 ${line.entity_id}，参数完整`
          : line.source_no == null
            ? '渲染器自动补齐的命令，无匹配告警'
            : '知识库命令模板确定，未发现参数或映射告警'
      return { key: index, command: line.text, tone: 'success', reason }
    }
    // muted（视图行 / quit / 自动补齐）不进入检查区
    if (line.tone !== 'warn' && line.tone !== 'error') return null
    return {
      key: index,
      hint: targetDetail?.description ?? '该行建议人工确认',
      command: line.text,
      tone: line.tone,
      onAccept: () => {
        setReviews((prev) => new Map(prev).set(index, { tone: 'success' }))
        advanceAfterReview(index)
      },
      onAcceptEdited: (text) => {
        setReviews((prev) => new Map(prev).set(index, { tone: 'success', text }))
        advanceAfterReview(index)
      },
      onDefer: () => {
        setSelection(null)
        setAlign(null)
      },
    }
  }, [selection, result, reviewedLines, targetDetail, reviews])

  useEffect(() => {
    if (status !== 'failed') return
    message.error(error ?? '翻译任务失败，请稍后重试')
    reset()
  }, [status, error, reset])

  const handleTranslate = () => {
    if (!source.text.trim()) {
      message.error('请先输入或导入源配置')
      return
    }
    if (!sourceDevice.vendor || !sourceDevice.model) {
      message.error('请选择源厂商与型号')
      return
    }
    void start({
      source_text: source.text,
      source_vendor: sourceDevice.vendor,
      source_model: sourceDevice.model,
      target_vendor: targetDevice.vendor,
      target_model: targetDevice.model,
    })
  }

  const handleExport = (format: ExportFormat) => {
    if (!result) {
      message.error('暂无可导出的翻译结果')
      return
    }
    if (stale) {
      message.warning('结果已过期，导出内容基于修改前的源配置')
    }
    const now = new Date()
    const base = `${safeFileNamePart(sourceDevice.vendor)}-${safeFileNamePart(
      sourceDevice.model,
    )}_to_${safeFileNamePart(targetDevice.vendor)}-${safeFileNamePart(
      targetDevice.model,
    )}_${exportStamp(now)}`
    if (format === 'cfg') {
      downloadText(buildCfgText(reviewedLines), `${base}.cfg`)
      message.success('配置已导出')
      return
    }
    downloadText(
      buildReviewReport(reviewedLines, {
        generatedAt: now,
        source: `${sourceDevice.vendor || '未选择'} ${sourceDevice.model || ''}`.trim(),
        target: `${targetDevice.vendor || '未选择'} ${targetDevice.model || ''}`.trim(),
        stale,
      }),
      `${base}_复核报告.txt`,
      true,
    )
    message.success('复核报告已导出')
  }

  return (
    <div className="flex min-h-full flex-col">
      <PageHeader
        title="配置翻译"
        subtitle="网络设备配置助手"
        right={
          <>
            {source.saveState !== 'empty' && (
              <span
                className={`flex items-center gap-1.5 text-[11px] ${
                  source.saveState === 'failed' ? 'text-warn' : 'text-ink-500'
                }`}
              >
                <CloudSyncOutlined
                  className={`text-[15px] ${
                    source.saveState === 'failed' ? 'text-warn' : 'text-ink-400'
                  }`}
                />
                {source.saveState === 'failed' ? '自动保存失败' : '已自动保存'}
              </span>
            )}
            <button
              type="button"
              onClick={handleOpenHistory}
              className="flex items-center gap-1.5 text-[13px] text-ink-500 hover:text-brand-strong"
            >
              <HistoryOutlined className="text-[15px]" />
              翻译记录
            </button>
          </>
        }
      />

      <div className="flex flex-col gap-4 px-4 py-4 md:px-7 md:pb-5 md:pt-6">
        <TranslateToolbar
          deviceType={deviceType}
          onDeviceTypeChange={setDeviceType}
          initialSourceVendor={sourceDevice.vendor}
          initialSourceModel={sourceDevice.model}
          initialTargetVendor={targetDevice.vendor}
          initialTargetModel={targetDevice.model}
          onSourceChange={handleSourceDeviceChange}
          onTargetChange={handleTargetDeviceChange}
          onDevicesLoaded={handleDevicesLoaded}
          onTranslate={handleTranslate}
          onExport={handleExport}
          translating={generating}
          hasResult={translated}
          hasTask={hasTranslationTask}
        />
        <TranslateStatusRow
          translated={translated}
          generating={generating}
          stale={stale}
          total={result?.summary.total}
          durationMs={result?.summary.duration_ms}
          deviceSummary={`${sourceDevice.vendor} → ${targetDevice.vendor}`}
        />

        <div className="flex flex-col gap-4 xl:gap-2 xl:flex-row">
          <ConfigPanel
            variant="source"
            sourceVendor={sourceDevice.vendor}
            sourceModel={sourceDevice.model}
            sourceText={source.text}
            sourceFileName={source.fileName}
            onImportFile={source.importFile}
            onSourceTextChange={source.setText}
            sourceSaveState={source.saveState}
            sourceMarks={sourceMarks}
            focusLine={selection?.sourceNo ?? null}
            onSelectLine={(lineNo) => handleSelectLine(lineNo)}
            detail={sourceDetail}
            expanded={expandedPanel === 'source'}
            hidden={expandedPanel === 'result'}
            onToggleExpand={() => toggleExpandedPanel('source')}
          />
          <ConfigPanel
            variant="target"
            targetVendor={targetDevice.vendor}
            targetModel={targetDevice.model}
            translated={translated}
            generating={generating}
            stale={stale}
            resultLines={targetResultLines}
            resultTotal={result?.summary.total}
            warnCount={resultStats.warn}
            errorCount={resultStats.error}
            focusLine={selection?.sourceNo ?? null}
            onSelectLine={(sourceNo, lineNo) => handleSelectLine(sourceNo, lineNo)}
            detail={targetDetail}
            expanded={expandedPanel === 'result'}
            hidden={expandedPanel === 'source'}
            onToggleExpand={() => toggleExpandedPanel('result')}
            onCopy={handleCopyResult}
          />
          <AuditPanel
            result={result}
            lines={reviewedLines}
            review={reviewTarget}
            checkpoints={checkpoints}
            canCreateCheckpoint={translated && reviews.size > 0}
            onSelectLine={(lineNo) => handleSelectLine(lineNo)}
            onCreateCheckpoint={openCheckpointModal}
            onRestoreCheckpoint={handleRestoreCheckpoint}
            onDeleteCheckpoint={handleDeleteCheckpoint}
          />
        </div>

        <footer className="flex flex-col gap-1 text-[10px] text-ink-400 sm:flex-row sm:items-center sm:justify-between">
          <span className="flex items-center gap-1.5">
            <SafetyCertificateOutlined className="text-[12px] text-ink-400" />
            配置中的账号、密钥等信息请先脱敏
          </span>
          <span>翻译结果仅供参考，请在目标设备验证后下发</span>
        </footer>
      </div>

      <Modal
        title="生成检查点"
        open={checkpointModalOpen}
        onOk={handleCreateCheckpoint}
        onCancel={() => setCheckpointModalOpen(false)}
        okText="保存"
        cancelText="取消"
        okButtonProps={{ disabled: !checkpointName.trim() }}
        destroyOnClose
      >
        <div className="py-2">
          <label className="mb-1.5 block text-[12px] text-ink-500">检查点名称</label>
          <Input
            value={checkpointName}
            onChange={(e) => setCheckpointName(e.target.value)}
            placeholder="请输入检查点名称"
            maxLength={30}
            showCount
            onPressEnter={() => checkpointName.trim() && handleCreateCheckpoint()}
            autoFocus
          />
          <p className="mt-2 text-[11px] text-ink-400">
            将保存当前已处理的审计结果，可在检查点记录中恢复
          </p>
        </div>
      </Modal>

      <Drawer
        closable={false}
        title={
          <div className="flex items-center gap-2">
            <span className="flex h-6 w-6 items-center justify-center rounded-md bg-brand-soft text-brand">
              <HistoryOutlined className="text-[13px]" />
            </span>
            <span className="text-[14px] font-medium text-ink-900">翻译记录</span>
            {visibleHistoryItems.length > 0 ? (
              <span className="rounded-full bg-soft px-1.5 py-[1px] text-[11px] text-ink-400">
                {visibleHistoryItems.length}
              </span>
            ) : null}
          </div>
        }
        extra={
          <div className="flex items-center gap-1.5">
            <button
              type="button"
              onClick={() => void loadHistory()}
              disabled={historyLoading}
              className="flex h-7 items-center gap-1 rounded-md px-2 text-[12px] text-ink-500 transition-colors hover:bg-soft hover:text-brand-strong disabled:cursor-not-allowed disabled:text-ink-300"
            >
              <ReloadOutlined spin={historyLoading} className="text-[12px]" />
              刷新
            </button>
            <span className="h-4 w-px bg-line" />
            <button
              type="button"
              aria-label="关闭"
              onClick={() => setHistoryOpen(false)}
              className="flex h-7 w-7 items-center justify-center rounded-md text-ink-400 transition-colors hover:bg-soft hover:text-ink-700"
            >
              <CloseOutlined className="text-[12px]" />
            </button>
          </div>
        }
        open={historyOpen}
        onClose={() => setHistoryOpen(false)}
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
        {historyLoading && historyItems.length === 0 ? (
          <div className="flex flex-col items-center gap-2 py-20 text-ink-400">
            <LoadingOutlined className="text-[20px]" />
            <span className="text-[12px]">正在加载翻译记录…</span>
          </div>
        ) : historyItems.length === 0 ? (
          <div className="flex flex-col items-center gap-2 py-20 text-ink-400">
            <div className="flex h-11 w-11 items-center justify-center rounded-full bg-white text-ink-300">
              <HistoryOutlined className="text-[18px]" />
            </div>
            <span className="text-[12px]">暂无翻译记录</span>
            <span className="text-[11px] text-ink-300">完成一次翻译后会自动出现在这里</span>
          </div>
        ) : (
          <div className="space-y-2.5">
            {visibleHistoryItems.map((item) => {
              const date = new Date(item.created_at)
              const time = date.toLocaleString('zh-CN', {
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
              })
              const statusText =
                item.status === 'succeeded'
                  ? '已完成'
                  : item.status === 'failed'
                    ? '失败'
                    : item.status === 'running'
                      ? '翻译中'
                      : '排队中'
              const statusClass =
                item.status === 'succeeded'
                  ? 'bg-success-soft text-success'
                  : item.status === 'failed'
                    ? 'bg-danger-soft text-danger'
                    : 'bg-brand-soft text-brand'
              const isCurrent = item.request_id === requestId
              return (
                <button
                  key={item.request_id}
                  type="button"
                  onClick={() => handleRestoreHistory(item)}
                  className="group block w-full rounded-xl border border-line bg-white p-3 text-left transition-all hover:border-brand-line hover:shadow-panel"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0 flex-1 space-y-1">
                      <HistoryDeviceLine
                        label="源"
                        vendor={item.source_vendor}
                        model={item.source_model}
                      />
                      <div className="pl-[26px] text-[10px] text-ink-300">
                        <ArrowRightOutlined className="rotate-90" />
                      </div>
                      <HistoryDeviceLine
                        label="目标"
                        vendor={item.target_vendor}
                        model={item.target_model}
                      />
                    </div>
                    <span
                      className={`shrink-0 rounded-full px-2 py-[1px] text-[10px] ${statusClass}`}
                    >
                      {statusText}
                    </span>
                  </div>
                  <div className="mt-2 flex items-center justify-between border-t border-line-soft pt-2">
                    <span className="text-[11px] text-ink-400">{time}</span>
                    {isCurrent ? (
                      <span className="text-[11px] text-brand-strong">当前任务</span>
                    ) : (
                      <span className="flex items-center gap-1 text-[11px] text-brand opacity-0 transition-opacity group-hover:opacity-100">
                        恢复此记录
                        <ArrowRightOutlined className="text-[10px]" />
                      </span>
                    )}
                  </div>
                </button>
              )
            })}
            {historyItems.length > HISTORY_LIMIT ? (
              <div className="pt-1 text-center text-[10px] text-ink-300">
                仅显示最近 {HISTORY_LIMIT} 条翻译记录
              </div>
            ) : null}
          </div>
        )}
      </Drawer>
    </div>
  )
}
