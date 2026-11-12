import {
  ArrowRightOutlined,
  CheckCircleFilled,
  CloudSyncOutlined,
  CodeOutlined,
  CopyOutlined,
  DownOutlined,
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
import { useEffect, useMemo, useRef, useState } from 'react'
import { message, Popconfirm, Tooltip } from 'antd'
import { PageHeader } from '../components/PageHeader'
import { StatusTag } from '../components/StatusTag'
import { deviceTypeLabel, fetchDeviceTypes, fetchModels, fetchVendors } from '../api/devices'
import { translationSignature, useTranslationTask } from '../hooks/useTranslationTask'
import { auditWarnings, sourceLines, translateMeta, type CodeLine } from '../data/translate'

// ---------- 源配置：导入约束 + localStorage 暂存 ----------

const SOURCE_ACCEPT_EXTENSIONS = ['.txt', '.cfg', '.log']
const SOURCE_MAX_BYTES = 2 * 1024 * 1024 // 2MB
const SOURCE_LS_KEY_TEXT = 'translate:source:text'
const SOURCE_LS_KEY_NAME = 'translate:source:fileName'
const SOURCE_LS_KEY_TIME = 'translate:source:savedAt'
const SOURCE_LS_TTL_MS = 24 * 60 * 60 * 1000 // 24h 过期

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

function writeSourceCache(text: string, fileName: string) {
  try {
    if (!text) {
      localStorage.removeItem(SOURCE_LS_KEY_TEXT)
      localStorage.removeItem(SOURCE_LS_KEY_NAME)
      localStorage.removeItem(SOURCE_LS_KEY_TIME)
      return
    }
    localStorage.setItem(SOURCE_LS_KEY_TEXT, text)
    localStorage.setItem(SOURCE_LS_KEY_NAME, fileName)
    localStorage.setItem(SOURCE_LS_KEY_TIME, String(Date.now()))
  } catch {
    // 隐私模式 / 配额满等场景下静默跳过
  }
}

function useSourceConfig() {
  const cached = useMemo(() => readSourceCache(), [])
  const [text, setText] = useState<string>(cached?.text ?? SAMPLE_SOURCE_TEXT)
  const [fileName, setFileName] = useState<string>(cached?.fileName ?? 'campus-access.cfg')

  useEffect(() => {
    writeSourceCache(text, fileName)
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

  return { text, fileName, setText, importFile, clear }
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
  onSourceChange,
  onTargetChange,
  onTranslate,
  translating = false,
  hasResult = false,
}: {
  onSourceChange?: (vendor: string, model: string) => void
  onTargetChange?: (vendor: string, model: string) => void
  onTranslate?: () => void
  translating?: boolean
  hasResult?: boolean
}) {
  const [types, setTypes] = useState<string[]>([])
  const [deviceType, setDeviceType] = useState('')
  const [vendors, setVendors] = useState<string[]>([])
  const [vendor, setVendor] = useState('')
  const [models, setModels] = useState<string[]>([])
  const [model, setModel] = useState('')
  const [targetVendor, setTargetVendor] = useState('')
  const [targetModels, setTargetModels] = useState<string[]>([])
  const [targetModel, setTargetModel] = useState('')

  useEffect(() => {
    let cancelled = false
    fetchDeviceTypes()
      .then((items) => {
        if (cancelled) return
        setTypes(items)
        setDeviceType((current) => (current && items.includes(current) ? current : (items[0] ?? '')))
      })
      .catch(() => {
        // 后端不可用时保留空列表
      })
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    if (!deviceType) return
    let cancelled = false
    fetchVendors(deviceType)
      .then((items) => {
        if (cancelled) return
        setVendors(items)
        setVendor((current) => (current && items.includes(current) ? current : (items[0] ?? '')))
        setTargetVendor((current) => (current && items.includes(current) ? current : (items[0] ?? '')))
      })
      .catch(() => {
        // 后端不可用时保留空列表
      })
    return () => {
      cancelled = true
    }
  }, [deviceType])

  useEffect(() => {
    if (!vendor) return
    let cancelled = false
    fetchModels(vendor, deviceType)
      .then((items) => {
        if (cancelled) return
        setModels(items)
        setModel((current) => (current && items.includes(current) ? current : (items[0] ?? '')))
      })
      .catch(() => {
        // 后端不可用时保留空列表
      })
    return () => {
      cancelled = true
    }
  }, [vendor, deviceType])

  useEffect(() => {
    if (!targetVendor) return
    let cancelled = false
    fetchModels(targetVendor, deviceType)
      .then((items) => {
        if (cancelled) return
        setTargetModels(items)
        setTargetModel((current) => (current && items.includes(current) ? current : (items[0] ?? '')))
      })
      .catch(() => {
        // 后端不可用时保留空列表
      })
    return () => {
      cancelled = true
    }
  }, [targetVendor, deviceType])

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
          onChange={setDeviceType}
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
          <button
            type="button"
            className="flex h-9 items-center gap-[7px] rounded-lg border border-line bg-white px-3.5 text-[13px] font-medium text-ink-900"
          >
            <ExportOutlined className="text-[15px] text-ink-500" />
            导出
            <DownOutlined className="text-[10px] text-ink-400" />
          </button>
        </div>
      </div>
    </section>
  )
}

function TranslateStatusRow({
  viewMode,
  onViewModeChange,
  translated,
  generating,
  stale = false,
  total = translateMeta.total,
  durationMs,
  deviceSummary,
}: {
  viewMode: 'text' | 'compare'
  onViewModeChange: (mode: 'text' | 'compare') => void
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
        <div className="flex h-[30px] items-center gap-1 rounded-md bg-[#F1F4F9] p-0.5 text-[12px]">
          <button
            type="button"
            onClick={() => onViewModeChange('text')}
            className={`flex h-[26px] items-center rounded px-3 font-medium transition-colors ${
              viewMode === 'text'
                ? 'border border-line bg-white text-brand-strong'
                : 'text-ink-500 hover:text-ink-900'
            }`}
          >
            文本模式
          </button>
          <Tooltip title="对照模式开发中">
            <span>
              <button
                type="button"
                disabled
                className="flex h-[26px] cursor-not-allowed items-center rounded px-3 text-ink-300"
              >
                对照模式
              </button>
            </span>
          </Tooltip>
        </div>
        <span className="hidden h-4 w-px bg-line sm:block" />
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
              {stale ? '源配置已修改，结果基于修改前内容' : `${deviceSummary} · 共 ${total} 条命令`}
            </span>
            {stale ? (
              <span className="text-[11px] text-ink-400">共 {total} 条命令</span>
            ) : (
              <span className="text-[11px] text-ink-400">
                耗时 {durationMs === undefined ? translateMeta.duration : `${(durationMs / 1000).toFixed(1)} s`}
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

function CodeRow({ item }: { item: CodeLine }) {
  const stateClass = {
    focus: 'bg-brand-soft',
    success: 'bg-success-soft',
    warn: 'bg-warn-soft',
    muted: 'bg-white',
  }[item.state ?? 'muted']

  const textClass = item.state === 'muted' ? 'text-ink-400' : 'text-ink-900'

  return (
    <div className={`flex h-6 items-center pr-2 ${stateClass}`}>
      <span className="w-[38px] shrink-0 select-none text-right font-mono text-[11px] leading-none text-ink-300">
        {item.no}
      </span>
      <span className={`ml-3 flex-1 whitespace-pre font-mono text-[12px] leading-none ${textClass}`}>
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
      </span>
    </div>
  )
}

function SourceEditor({ value, onChange }: { value: string; onChange: (next: string) => void }) {
  const [scrollTop, setScrollTop] = useState(0)
  const lineCount = Math.max(1, value.split('\n').length)

  return (
    <div className="flex min-h-[280px] flex-1 overflow-hidden">
      <div className="w-[46px] shrink-0 overflow-hidden border-r border-line-soft bg-soft pt-1">
        <div style={{ transform: `translateY(-${scrollTop}px)` }}>
          {Array.from({ length: lineCount }, (_, index) => (
            <div
              key={index}
              className="flex h-6 select-none items-center justify-end pr-2 font-mono text-[11px] leading-none text-ink-300"
            >
              {index + 1}
            </div>
          ))}
        </div>
      </div>
      <textarea
        value={value}
        onChange={(event) => onChange(event.target.value)}
        onScroll={(event) => setScrollTop(event.currentTarget.scrollTop)}
        wrap="off"
        spellCheck={false}
        placeholder="粘贴或导入设备配置…"
        className="thin-scrollbar h-full min-h-[280px] w-full flex-1 resize-none bg-white px-3 py-1 font-mono text-[12px] leading-6 text-ink-900 outline-none placeholder:text-ink-300"
      />
    </div>
  )
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
}: ConfigPanelProps) {
  const isSource = variant === 'source'
  const fileInputRef = useRef<HTMLInputElement>(null)

  const displayLines: CodeLine[] = useMemo(() => {
    if (!isSource) return resultLines ?? []
    if (!sourceText) return sourceLines
    return sourceText.split('\n').map((text, idx) => ({
      no: idx + 1,
      parts: [{ text: text.replace(/\r$/, '') }],
    }))
  }, [isSource, sourceText, resultLines])

  const sourceDeviceLabel =
    sourceVendor && sourceModel ? `${sourceVendor} · ${sourceModel}` : '未选择源设备'

  const targetDeviceLabel =
    targetVendor && targetModel ? `${targetVendor} · ${targetModel}` : '未选择目标设备'

  const displayFileName = isSource
    ? sourceFileName ?? 'campus-access.cfg'
    : targetDeviceLabel

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
              ? `${resultTotal ?? translateMeta.total} 条映射`
              : '待生成'}
        </span>
      </div>

      {isSource ? (
        <SourceEditor value={sourceText} onChange={onSourceTextChange ?? (() => {})} />
      ) : generating ? (
        <div className="flex min-h-[280px] flex-1 flex-col items-center justify-center gap-2 px-4 text-center">
          <LoadingOutlined spin className="text-[24px] text-brand" />
          <span className="text-[12px] text-ink-500">正在生成翻译结果</span>
          <span className="text-[11px] text-ink-300">后端任务执行中，完成后自动展示</span>
        </div>
      ) : translated ? (
        <div className="thin-scrollbar min-h-[280px] flex-1 overflow-auto py-1">
          {displayLines.map((item, index) => (
            <CodeRow key={`${item.no}-${index}`} item={item} />
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
            <span className="truncate">
              {isSource ? 'L3 → L3 · VLAN 接入口映射' : 'L3 → L3 · VLAN 接入口映射'}
            </span>
          </span>
          <StatusTag tone="green">high</StatusTag>
        </div>
        <p className="mt-1.5 text-[11px] leading-[1.6] text-ink-500">
          {isSource
            ? '已识别默认 VLAN 归属命令，与右侧目标命令一一对应。'
            : 'default → access，保留 VLAN 10；请核对目标端口的链路类型。'}
        </p>
      </div>

      <div className="flex h-[26px] shrink-0 items-center justify-between border-t border-line px-3 text-[10px] text-ink-400">
        <span>{isSource ? '行 3，列 2' : '行 3，列 2'}</span>
        <span>
          {isSource
            ? sourceText === SAMPLE_SOURCE_TEXT
              ? '示例配置 · 可直接编辑'
              : `已暂存本地 · 共 ${displayLines.length} 行`
            : translated
              ? '3 处有损 · 1 处不支持'
              : '—'}
        </span>
      </div>
    </section>
  )
}

function AuditPanel() {
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
            <span className="text-[11px] text-ink-400">共 {translateMeta.total} 条</span>
          </div>

          <div className="flex h-1.5 items-stretch gap-[3px] overflow-hidden rounded-full">
            <span className="flex-[31] rounded-full bg-success" />
            <span className="flex-[9] rounded-full bg-[#D9A34E]" />
            <span className="flex-[2] rounded-full bg-danger" />
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[12px] text-success">✓ high</span>
              <span className="flex items-baseline gap-2">
                <span className="font-mono text-[13px] font-semibold text-ink-900">31</span>
                <span className="w-[46px] text-right font-mono text-[10px] text-ink-400">73.8%</span>
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-[12px] text-warn">⚠ medium</span>
              <span className="flex items-baseline gap-2">
                <span className="font-mono text-[13px] font-semibold text-ink-900">9</span>
                <span className="w-[46px] text-right font-mono text-[10px] text-ink-400">21.4%</span>
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-[12px] text-danger">✕ low</span>
              <span className="flex items-baseline gap-2">
                <span className="font-mono text-[13px] font-semibold text-ink-900">2</span>
                <span className="w-[46px] text-right font-mono text-[10px] text-ink-400">4.8%</span>
              </span>
            </div>
          </div>

          <div className="flex h-[30px] items-center rounded-md bg-soft px-2.5 text-[11px] text-ink-500">
            有损 3 · 不支持 1
          </div>
        </div>

        <div className="space-y-2.5">
          <div className="flex items-center justify-between">
            <span className="text-[13px] font-bold text-ink-900">警告 (4)</span>
            <span className="text-[11px] text-ink-400">定位到配置行</span>
          </div>
          <div className="space-y-1">
            {auditWarnings.map((item) => (
              <button
                type="button"
                key={item.key}
                className={`flex w-full items-center gap-2 rounded-md border px-2.5 py-2 text-left ${
                  item.active
                    ? 'border-brand-line bg-brand-soft'
                    : 'border-transparent hover:bg-soft'
                }`}
              >
                {item.tone === 'danger' ? (
                  <span className="flex h-4 w-4 shrink-0 items-center justify-center rounded-full border border-danger text-[9px] text-danger">
                    ×
                  </span>
                ) : (
                  <WarningOutlined className="shrink-0 text-[13px] text-warn" />
                )}
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-[11px] font-medium text-ink-900">
                    {item.title}
                  </span>
                  <span className="mt-0.5 block truncate text-[10px] text-ink-400">
                    {item.meta}
                  </span>
                </span>
                <span className="text-[10px] text-ink-300">›</span>
              </button>
            ))}
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
  const [sourceDevice, setSourceDevice] = useState({ vendor: '', model: '' })
  const [targetDevice, setTargetDevice] = useState({ vendor: '', model: '' })
  const [viewMode, setViewMode] = useState<'text' | 'compare'>('text')
  const { status, result, error, submittedSignature, start, reset } = useTranslationTask()

  const generating = status === 'pending' || status === 'running'
  const translated = status === 'succeeded' && result !== null
  const targetResultLines = useMemo<CodeLine[]>(
    () =>
      result?.lines.map((item, index) => ({
        no: index + 1,
        parts: [{ text: item.text }],
        state: item.tone,
      })) ?? [],
    [result],
  )

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

  return (
    <div className="flex min-h-full flex-col">
      <PageHeader
        title="配置翻译"
        subtitle="网络设备配置助手"
        right={
          <>
            <span className="flex items-center gap-1.5 text-[11px] text-ink-500">
              <CloudSyncOutlined className="text-[15px] text-ink-400" />
              已自动保存
            </span>
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
          translating={generating}
          hasResult={translated}
        />
        <TranslateStatusRow
          viewMode={viewMode}
          onViewModeChange={setViewMode}
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
          />
          <AuditPanel />
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
