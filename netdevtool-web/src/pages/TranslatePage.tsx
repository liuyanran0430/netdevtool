import {
  ArrowRightOutlined,
  CheckCircleFilled,
  CloudSyncOutlined,
  CodeOutlined,
  CopyOutlined,
  DownOutlined,
  ExclamationCircleFilled,
  ExpandAltOutlined,
  ExportOutlined,
  FileTextOutlined,
  FlagOutlined,
  HistoryOutlined,
  LinkOutlined,
  LoadingOutlined,
  PlayCircleOutlined,
  SafetyCertificateOutlined,
  TranslationOutlined,
  UploadOutlined,
  WarningOutlined,
} from '@ant-design/icons'
import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type Dispatch,
  type MouseEvent,
  type SetStateAction,
} from 'react'
import { Dropdown, message, Popconfirm, Tooltip } from 'antd'
import { PageHeader } from '../components/PageHeader'
import { StatusTag } from '../components/StatusTag'
import { deviceTypeLabel, fetchDevices, type Device } from '../api/devices'
import type { TranslationResult, TranslationResultLine } from '../api/translations'
import { translationSignature, useTranslationTask } from '../hooks/useTranslationTask'
import { sourceLines, type CodeLine } from '../data/translate'

// ---------- 代码视图行高：行号、滚动对齐与点击定位共用 ----------

const LINE_HEIGHT = 24
const TEXTAREA_PADDING_TOP = 4
/** 设备数据未返回前的空列表占位，保持 useMemo 依赖稳定 */
const EMPTY_DEVICES: Device[] = []

// ---------- 源配置：导入约束 + localStorage 暂存 ----------

const SOURCE_ACCEPT_EXTENSIONS = ['.txt', '.cfg', '.log']
const SOURCE_MAX_BYTES = 2 * 1024 * 1024 // 2MB
const SOURCE_LS_KEY_TEXT = 'translate:source:text'
const SOURCE_LS_KEY_NAME = 'translate:source:fileName'
const SOURCE_LS_KEY_TIME = 'translate:source:savedAt'
const SOURCE_LS_TTL_MS = 24 * 60 * 60 * 1000 // 24h 过期

// ---------- 翻译页会话：设备选择 + 任务 requestId 暂存 ----------

const SESSION_LS_KEY = 'translate:session'

interface TranslateSession {
  deviceType: string
  sourceVendor: string
  sourceModel: string
  targetVendor: string
  targetModel: string
  requestId: string | null
  submittedSignature: string | null
}

function readSession(): TranslateSession | null {
  try {
    const raw = localStorage.getItem(SESSION_LS_KEY)
    if (!raw) return null
    return JSON.parse(raw) as TranslateSession
  } catch {
    return null
  }
}

function writeSession(session: TranslateSession) {
  try {
    localStorage.setItem(SESSION_LS_KEY, JSON.stringify(session))
  } catch {
    // 隐私模式 / 配额满等场景下静默跳过
  }
}

const SAMPLE_SOURCE_TEXT = sourceLines
  .map((item) => item.parts.map((part) => part.text).join(''))
  .join('\n')

function readSourceCache(): { text: string; fileName: string } | null {
  try {
    const savedAt = Number(localStorage.getItem(SOURCE_LS_KEY_TIME) ?? 0)
    if (!savedAt || Date.now() - savedAt > SOURCE_LS_TTL_MS) return null
    const text = localStorage.getItem(SOURCE_LS_KEY_TEXT) ?? ''
    const fileName = localStorage.getItem(SOURCE_LS_KEY_NAME) ?? ''
    if (!text) return null
    return { text, fileName }
  } catch {
    return null
  }
}

function writeSourceCache(text: string, fileName: string): boolean {
  try {
    if (!text) {
      localStorage.removeItem(SOURCE_LS_KEY_TEXT)
      localStorage.removeItem(SOURCE_LS_KEY_NAME)
      localStorage.removeItem(SOURCE_LS_KEY_TIME)
      return true
    }
    localStorage.setItem(SOURCE_LS_KEY_TEXT, text)
    localStorage.setItem(SOURCE_LS_KEY_NAME, fileName)
    localStorage.setItem(SOURCE_LS_KEY_TIME, String(Date.now()))
    return true
  } catch {
    // 隐私模式 / 配额满等场景下保存失败
    return false
  }
}

function useSourceConfig() {
  const cached = useMemo(() => readSourceCache(), [])
  const [text, setText] = useState<string>(cached?.text ?? SAMPLE_SOURCE_TEXT)
  const [fileName, setFileName] = useState<string>(cached?.fileName ?? 'campus-access.cfg')
  // 源配置暂存状态：空内容 / 已保存 / 保存失败
  const [saveState, setSaveState] = useState<'empty' | 'saved' | 'failed'>('empty')

  useEffect(() => {
    const saved = writeSourceCache(text, fileName)
    if (!text.trim()) setSaveState('empty')
    else setSaveState(saved ? 'saved' : 'failed')
  }, [text, fileName])

  const importFile = (file: File) => {
    const lower = file.name.toLowerCase()
    if (!SOURCE_ACCEPT_EXTENSIONS.some((ext) => lower.endsWith(ext))) {
      message.error(`仅支持 ${SOURCE_ACCEPT_EXTENSIONS.join(' / ')} 格式`)
      return
    }
    if (file.size > SOURCE_MAX_BYTES) {
      message.error('文件超过 2MB 上限')
      return
    }
    const reader = new FileReader()
    reader.onload = () => {
      const content = typeof reader.result === 'string' ? reader.result : ''
      if (!content.trim()) {
        message.error('文件内容为空')
        return
      }
      setText(content)
      setFileName(file.name)
      message.success(`已导入 ${file.name}`)
    }
    reader.onerror = () => {
      message.error('文件读取失败，请重试')
    }
    reader.readAsText(file, 'utf-8')
  }

  const clear = () => {
    setText('')
    setFileName('campus-access.cfg')
  }

  return { text, fileName, setText, importFile, clear, saveState }
}

// ---------- 导出：.cfg 配置与复核报告 ----------

type ExportFormat = 'cfg' | 'report'

const pad2 = (value: number) => String(value).padStart(2, '0')

function exportStamp(date: Date) {
  return `${date.getFullYear()}${pad2(date.getMonth() + 1)}${pad2(date.getDate())}-${pad2(date.getHours())}${pad2(date.getMinutes())}`
}

function exportTimeLabel(date: Date) {
  return `${date.getFullYear()}-${pad2(date.getMonth() + 1)}-${pad2(date.getDate())} ${pad2(date.getHours())}:${pad2(date.getMinutes())}`
}

function safeFileNamePart(value: string) {
  return value.replace(/[\\/:*?"<>|\s]+/g, '-') || '未选择'
}

function downloadText(content: string, fileName: string, withBom = false) {
  const blob = new Blob([withBom ? `\uFEFF${content}` : content], {
    type: 'text/plain;charset=utf-8',
  })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = fileName
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

function buildCfgText(lines: TranslationResultLine[]) {
  // 仅输出命令本身，便于直接回灌设备；Windows 习惯使用 CRLF
  return `${lines.map((line) => line.text).join('\r\n')}\r\n`
}

function buildReviewReport(
  lines: TranslationResultLine[],
  meta: { generatedAt: Date; source: string; target: string; stale: boolean },
) {
  const warnCount = lines.filter((line) => line.tone === 'warn').length
  const errorCount = lines.filter((line) => line.tone === 'error').length
  const header = [
    '# 配置翻译复核报告',
    `# 生成时间：${exportTimeLabel(meta.generatedAt)}`,
    `# 设备：${meta.source} → ${meta.target}`,
    `# 统计：共 ${lines.length} 行，需复核 ${warnCount} 行（warn），需人工处理 ${errorCount} 行（error）`,
    ...(meta.stale ? ['# 注意：翻译结果已过期，内容基于修改前的源配置'] : []),
    '# 说明：行尾 [需复核] / [需人工处理] 标记仅用于评审，下发前请确认',
    '# --------------------------------------------------',
  ]
  const body = lines.map((line) => {
    const mark =
      line.tone === 'error' ? '[需人工处理]' : line.tone === 'warn' ? '[需复核]' : ''
    if (!mark) return line.text
    const source = line.source_no == null ? '' : ` 源行 ${line.source_no}`
    return `${line.text}  # ${mark}${source}`
  })
  return `${[...header, ...body].join('\r\n')}\r\n`
}

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
  onTranslate,
  onExport,
  translating = false,
  hasResult = false,
}: {
  deviceType: string
  onDeviceTypeChange: Dispatch<SetStateAction<string>>
  initialSourceVendor?: string
  initialSourceModel?: string
  initialTargetVendor?: string
  initialTargetModel?: string
  onSourceChange?: (vendor: string, model: string) => void
  onTargetChange?: (vendor: string, model: string) => void
  onTranslate?: () => void
  onExport?: (format: ExportFormat) => void
  translating?: boolean
  hasResult?: boolean
}) {
  // null 表示设备数据尚未返回，此时不纠正任何已恢复的选择
  const [devices, setDevices] = useState<Device[] | null>(null)
  const [vendor, setVendor] = useState(initialSourceVendor ?? '')
  const [model, setModel] = useState(initialSourceModel ?? '')
  const [targetVendor, setTargetVendor] = useState(initialTargetVendor ?? '')
  const [targetModel, setTargetModel] = useState(initialTargetModel ?? '')

  useEffect(() => {
    let cancelled = false
    fetchDevices()
      .then((items) => {
        if (!cancelled) setDevices(items)
      })
      .catch(() => {
        // 后端不可用时保留空列表
      })
    return () => {
      cancelled = true
    }
  }, [])

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
            className="flex h-9 items-center gap-[7px] rounded-lg border border-line bg-white px-3.5 text-[13px] font-medium text-ink-900"
          >
            <PlayCircleOutlined className="text-[15px] text-ink-500" />
            dry-run
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
}: {
  item: CodeLine
  onSelect?: (sourceNo: number, lineNo: number) => void
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

  return (
    <div
      data-row={item.no}
      data-source-no={item.sourceNo ?? ''}
      onClick={
        selectable ? () => onSelect?.(item.sourceNo as number, item.no) : undefined
      }
      className={`flex h-6 items-center pr-2 ${stateClass} ${selectable ? 'cursor-pointer' : ''}`}
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
  scrollTo,
}: {
  value: string
  onChange: (next: string) => void
  marks?: Map<number, 'warn' | 'error'>
  focusLine?: number | null
  onSelectLine?: (sourceNo: number, lineNo?: number) => void
  onCursorChange?: (position: { line: number; column: number }) => void
  /** 由结果侧选中触发，把指定源行滚动到可视区中央 */
  scrollTo?: { line: number; token: number } | null
}) {
  const [scrollTop, setScrollTop] = useState(0)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const lineCount = Math.max(1, value.split('\n').length)

  useEffect(() => {
    const area = textareaRef.current
    if (!scrollTo || !area) return
    const line = Math.min(Math.max(1, scrollTo.line), lineCount)
    // 目标行居中：行高与顶部内边距需与行号列保持一致
    const top = (line - 1) * LINE_HEIGHT + TEXTAREA_PADDING_TOP - area.clientHeight / 2 + 12
    area.scrollTop = Math.max(0, top)
    setScrollTop(area.scrollTop)
    // 仅在新的滚动请求（token 变化）时执行，避免输入时反复跳动
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scrollTo?.token])

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
        <div
          aria-hidden
          className="pointer-events-none absolute inset-y-0 right-2 w-4 overflow-hidden pt-1"
        >
          <div style={{ transform: `translateY(-${scrollTop}px)` }}>
            {Array.from({ length: lineCount }, (_, index) => {
              const lineNo = index + 1
              const tone = markAt(lineNo)
              const focused = lineNo === focusLine
              return (
                <div key={index} className="flex h-6 items-center justify-center">
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
        <textarea
          ref={textareaRef}
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
  /** 滚动对齐请求：source 面板按源行滚动，target 面板按源行或结果行滚动 */
  scrollTo?: { line: number; token: number } | null
  detail?: PanelDetail
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
  scrollTo,
  detail,
}: ConfigPanelProps) {
  const isSource = variant === 'source'
  const fileInputRef = useRef<HTMLInputElement>(null)
  const resultListRef = useRef<HTMLDivElement>(null)
  const [cursor, setCursor] = useState({ line: 1, column: 1 })

  const displayLines: CodeLine[] = useMemo(() => {
    if (!isSource) return resultLines ?? []
    if (!sourceText) return sourceLines
    return sourceText.split('\n').map((text, idx) => ({
      no: idx + 1,
      parts: [{ text: text.replace(/\r$/, '') }],
    }))
  }, [isSource, sourceText, resultLines])

  // 结果面板：把命中的源行（或指定结果行）滚动到可视区中央
  useEffect(() => {
    const container = resultListRef.current
    if (isSource || !scrollTo || !container) return
    const rows = Array.from(container.querySelectorAll<HTMLElement>('[data-row]'))
    const target =
      rows.find((row) => row.dataset.sourceNo === String(scrollTo.line)) ??
      rows.find((row) => row.dataset.row === String(scrollTo.line))
    if (!target) return
    container.scrollTop = Math.max(
      0,
      target.offsetTop - container.clientHeight / 2 + target.clientHeight / 2,
    )
    // 仅在新的滚动请求（token 变化）时执行
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isSource, scrollTo?.token])

  const sourceDeviceLabel =
    sourceVendor && sourceModel ? `${sourceVendor} · ${sourceModel}` : '未选择源设备'

  const targetDeviceLabel =
    targetVendor && targetModel ? `${targetVendor} · ${targetModel}` : '未选择目标设备'

  const displayFileName = isSource
    ? sourceFileName ?? 'campus-access.cfg'
    : targetDeviceLabel

  const sourceLineCount = sourceText ? sourceText.split('\n').length : 0
  const sourceStatusText =
    sourceLineCount === 0
      ? '暂无内容'
      : sourceText === SAMPLE_SOURCE_TEXT
        ? `示例配置 · 共 ${sourceLineCount} 行`
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
    <section className="flex min-w-0 flex-none flex-col rounded-panel border border-line bg-white xl:h-[700px] xl:flex-1">
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
            <button type="button" aria-label="复制">
              <CopyOutlined className="text-[15px]" />
            </button>
          )}
          <button type="button" aria-label="全屏">
            <ExpandAltOutlined className="text-[15px]" />
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
          scrollTo={scrollTo}
        />
      ) : generating ? (
        <div className="flex min-h-[280px] flex-1 flex-col items-center justify-center gap-2 px-4 text-center">
          <LoadingOutlined spin className="text-[24px] text-brand" />
          <span className="text-[12px] text-ink-500">正在生成翻译结果</span>
          <span className="text-[11px] text-ink-300">后端任务执行中，完成后自动展示</span>
        </div>
      ) : translated ? (
        <div ref={resultListRef} className="thin-scrollbar relative min-h-[280px] flex-1 overflow-auto py-1">
          {displayLines.map((item, index) => (
            <CodeRow key={`${item.no}-${index}`} item={item} onSelect={onSelectLine} />
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

      <div className="m-3 shrink-0 rounded-lg border border-line bg-soft px-3 py-2.5">
        <div className="flex items-center justify-between gap-2">
          <span className="flex min-w-0 items-center gap-1.5 text-[11px] font-medium text-ink-900">
            <LinkOutlined className="shrink-0 text-[11px] text-brand" />
            <span className="truncate">{detail?.title ?? '点击任意行查看映射详情'}</span>
          </span>
          {detail?.tag ? (
            <StatusTag tone={detail.tag.tone}>{detail.tag.text}</StatusTag>
          ) : null}
        </div>
        <p className="mt-1.5 truncate text-[11px] leading-[1.6] text-ink-500">
          {detail?.description ?? '选中行后，这里显示该行的映射说明。'}
        </p>
      </div>

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
  unsupported_entity: '目标设备不支持',
  invalid_param: '参数校验失败',
  unverified_impl: '目标实现未验证',
  low_confidence: '实现置信度偏低',
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

function AuditPanel({
  result,
  onSelectLine,
}: {
  result: TranslationResult | null
  onSelectLine?: (lineNo: number) => void
}) {
  const stats = useMemo(() => summarizeAudit(result?.lines), [result])
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
        <StatusTag tone="warn">待复核</StatusTag>
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
          <div className="flex gap-2.5">
            <span className="flex h-8 flex-1 items-center justify-center rounded-md bg-success-soft text-[11px] text-success">
              语法 ✓
            </span>
            <span className="flex h-8 flex-1 items-center justify-center rounded-md bg-success-soft text-[11px] text-success">
              视图 ✓
            </span>
          </div>
        </div>
      </div>

      <div className="shrink-0 space-y-2 border-t border-line px-[18px] py-3.5">
        <button
          type="button"
          className="flex h-9 w-full items-center justify-center gap-[7px] rounded-lg border border-brand-line bg-white text-[13px] font-medium text-brand-strong"
        >
          <FlagOutlined className="text-[14px]" />
          生成检查点
        </button>
        <p className="text-center text-[10px] leading-[1.5] text-ink-400">
          保存当前配置、映射关系与审计结果
        </p>
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
  // 选中的源配置行与结果行：两侧同时高亮为 focus，底部详情卡片同步更新
  const [selection, setSelection] = useState<{ sourceNo: number; lineNo: number | null } | null>(
    null,
  )
  // 选中来源对应的滚动对齐请求，token 保证重复选中同一行也能重新滚动
  const [align, setAlign] = useState<{
    source?: number
    result?: number
    token: number
  } | null>(null)
  const { status, result, requestId, error, submittedSignature, start, resume, reset } =
    useTranslationTask()

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
      result?.lines.map((item, index) => {
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
      }) ?? [],
    [result, selection],
  )

  // 新的翻译结果到达后清除选中
  useEffect(() => {
    setSelection(null)
    setAlign(null)
  }, [result])

  const handleSelectLine = (
    sourceNo: number,
    lineNo?: number,
    origin: 'source' | 'result' | 'audit' = 'result',
  ) => {
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
    // 点击源行本身不滚动源面板，避免光标定位时页面跳动；其余来源对侧滚动到可视区中央
    setAlign({
      source: origin === 'source' ? undefined : sourceNo,
      result: origin === 'result' ? undefined : (lineNo ?? sourceNo),
      token: Date.now(),
    })
  }

  // 滚动目标保持引用稳定，避免每次渲染都重新滚动
  const sourceScroll = useMemo(
    () => (align?.result != null ? { line: align.result, token: align.token } : null),
    [align],
  )
  const targetScroll = useMemo(
    () => (align?.source != null ? { line: align.source, token: align.token } : null),
    [align],
  )

  const sourceMarks = useMemo(() => {
    const marks = new Map<number, 'warn' | 'error'>()
    for (const item of result?.lines ?? []) {
      if (item.source_no === null || item.source_no === undefined) continue
      if (item.tone !== 'warn' && item.tone !== 'error') continue
      // 同一源行命中多行时取更严重的级别
      if (marks.get(item.source_no) === 'error') continue
      marks.set(item.source_no, item.tone)
    }
    return marks
  }, [result])

  const resultStats = useMemo(() => {
    let warn = 0
    let error = 0
    for (const item of result?.lines ?? []) {
      if (item.tone === 'warn') warn += 1
      else if (item.tone === 'error') error += 1
    }
    return { warn, error }
  }, [result])

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
    const mapped = (result?.lines ?? []).filter((item) => item.source_no === lineNo)
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
  }, [selection, source.text, result, entityDescriptions])

  // 目的侧详情：显示选中结果行的行级 warnings
  const targetDetail = useMemo<PanelDetail | undefined>(() => {
    if (!selection) return undefined
    if (!result) {
      return {
        title: '暂无翻译结果',
        description: '生成翻译结果后，这里显示目标命令与复核提示。',
      }
    }
    const lines = result.lines
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
    // 优先按源行号匹配；旧渲染器的视图行 warning 挂在触发命令行上，回退到结果行号
    let messages = line.source_no == null ? [] : (warningMap.get(line.source_no) ?? [])
    if (messages.length === 0) messages = warningMap.get(line.no) ?? []
    const description = messages.length
      ? messages.join('；')
      : line.source_no == null
        ? '渲染器自动补齐的命令，非源配置内容'
        : (TONE_FALLBACK[line.tone] ?? '无需复核')
    return {
      title: `L${index + 1} · ${line.text.trim() || '空行'}`,
      description,
      tag: TONE_TAG[line.tone],
    }
  }, [selection, result, warningMap])

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
      downloadText(buildCfgText(result.lines), `${base}.cfg`)
      message.success('配置已导出')
      return
    }
    downloadText(
      buildReviewReport(result.lines, {
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
              className="flex items-center gap-1.5 text-[13px] text-ink-500"
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
          onSourceChange={(vendor, model) =>
            setSourceDevice((prev) =>
              prev.vendor === vendor && prev.model === model ? prev : { vendor, model },
            )
          }
          onTargetChange={(vendor, model) =>
            setTargetDevice((prev) =>
              prev.vendor === vendor && prev.model === model ? prev : { vendor, model },
            )
          }
          onTranslate={handleTranslate}
          onExport={handleExport}
          translating={generating}
          hasResult={translated}
        />
        <TranslateStatusRow
          translated={translated}
          generating={generating}
          stale={stale}
          total={result?.summary.total}
          durationMs={result?.summary.duration_ms}
          deviceSummary={`${sourceDevice.vendor} → ${targetDevice.vendor}`}
        />

        <div className="flex flex-col gap-4 xl:flex-row">
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
            onSelectLine={(lineNo) => handleSelectLine(lineNo, undefined, 'source')}
            scrollTo={sourceScroll}
            detail={sourceDetail}
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
            onSelectLine={(sourceNo, lineNo) =>
              handleSelectLine(sourceNo, lineNo, 'result')
            }
            scrollTo={targetScroll}
            detail={targetDetail}
          />
          <AuditPanel
            result={result}
            onSelectLine={(lineNo) => handleSelectLine(lineNo, undefined, 'audit')}
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
    </div>
  )
}
