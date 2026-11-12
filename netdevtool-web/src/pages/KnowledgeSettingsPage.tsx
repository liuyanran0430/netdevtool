import {
  DatabaseOutlined,
  DeleteOutlined,
  DownOutlined,
  EditOutlined,
  ExclamationCircleOutlined,
  FileTextOutlined,
  InfoCircleOutlined,
  PlusOutlined,
  ReloadOutlined,
  SearchOutlined,
  SettingOutlined,
  TagsOutlined,
  ToolOutlined,
  UploadOutlined,
} from '@ant-design/icons'
import {
  Button,
  Checkbox,
  Drawer,
  Dropdown,
  Input,
  Progress,
  Select,
  Tag,
  Tooltip,
  Upload,
  message,
} from 'antd'
import type { UploadFile } from 'antd'
import { useMemo, useState } from 'react'
import { PageHeader } from '../components/PageHeader'
import { StatusTag } from '../components/StatusTag'

/* ===================================================== */
/* 类型 & 默认配置                                        */
/* ===================================================== */

export interface KnowledgeConfig {
  chunking: {
    mode: 'general' | 'parent-child' | 'qa'
    general: { delimiter: string; maxLength: number; overlap: number }
    parentChild: {
      parent: { delimiter: string; maxLength: number }
      child: { delimiter: string; maxLength: number }
    }
  }
  indexing: 'high' | 'economical'
  retrieval: 'vector' | 'fulltext' | 'hybrid'
  hybrid: { semanticWeight: number; topK: number; scoreThreshold: number }
}

const DEFAULT_CONFIG: KnowledgeConfig = {
  chunking: {
    mode: 'general',
    general: { delimiter: '\\n\\n', maxLength: 500, overlap: 50 },
    parentChild: {
      parent: { delimiter: '\\n\\n', maxLength: 1000 },
      child: { delimiter: '\\n', maxLength: 200 },
    },
  },
  indexing: 'high',
  retrieval: 'hybrid',
  hybrid: { semanticWeight: 50, topK: 3, scoreThreshold: 0.6 },
}

const chunkingOptions: {
  value: KnowledgeConfig['chunking']['mode']
  title: string
  desc: string
  tag: string | null
}[] = [
  {
    value: 'general',
    title: 'General 通用文本分段',
    desc: '按分隔符切分文本，适用于命令说明、FAQ 等通用文档。',
    tag: null,
  },
  {
    value: 'parent-child',
    title: 'Parent-Child 父子分段',
    desc: '子块用于精准检索，父块作为完整上下文返回给大模型。',
    tag: '推荐',
  },
  {
    value: 'qa',
    title: 'Q&A 问答对',
    desc: '识别 Markdown 或 Excel 中的 Q&A 结构，按问答对切片入库。',
    tag: null,
  },
]

/* ===================================================== */
/* 文档管理类型 & 数据                                    */
/* ===================================================== */

export type DocStatus = 'indexed' | 'processing' | 'failed' | 'unconfigured'

export interface DocRow {
  id: string
  fileName: string
  type: 'PDF' | 'YML' | 'XLS' | 'MD'
  typeLabel: string
  dynamicChunks?: boolean
  chunks: number | null
  vendor: string
  functionTag: string
  status: DocStatus
  size: string
  updatedAt: string
}

const DOC_ROWS_INIT: DocRow[] = [
  {
    id: 'd1',
    fileName: 'huawei_s5735.pdf',
    type: 'PDF',
    typeLabel: 'PDF',
    chunks: 142,
    vendor: '华为',
    functionTag: 'VLAN / 路由',
    status: 'indexed',
    size: '2.4 MB',
    updatedAt: '2025-01-18',
  },
  {
    id: 'd2',
    fileName: 'h3c_映射表.yaml',
    type: 'YML',
    typeLabel: '结构化',
    dynamicChunks: true,
    chunks: null,
    vendor: '华三',
    functionTag: '交换机全局',
    status: 'processing',
    size: '8 KB',
    updatedAt: '2025-01-17',
  },
  {
    id: 'd3',
    fileName: 'dptech_fw.xlsx',
    type: 'XLS',
    typeLabel: 'Excel',
    chunks: null,
    vendor: '迪普',
    functionTag: '未配置',
    status: 'failed',
    size: '44 KB',
    updatedAt: '2025-01-16',
  },
  {
    id: 'd4',
    fileName: '故障排查手册.md',
    type: 'MD',
    typeLabel: 'Markdown',
    chunks: 210,
    vendor: '全局',
    functionTag: '故障排查',
    status: 'indexed',
    size: '12 KB',
    updatedAt: '2025-01-15',
  },
]

/* 文件类型徽标配色 */
const TYPE_BADGE: Record<
  DocRow['type'],
  { bg: string; text: string; label: string }
> = {
  PDF: { bg: '#EAF1FF', text: '#3268DB', label: 'PDF' },
  YML: { bg: '#EEEAFB', text: '#7460AD', label: 'YML' },
  XLS: { bg: '#EDF7F3', text: '#29826D', label: 'XLS' },
  MD: { bg: '#EDF2F8', text: '#3268DB', label: 'MD' },
}

/* 状态元数据 */
const STATUS_META: Record<
  DocStatus,
  { label: string; dot: string; bg: string; text: string }
> = {
  indexed: {
    label: '已索引',
    dot: '#29826D',
    bg: '#EDF7F3',
    text: '#29826D',
  },
  processing: {
    label: '处理中',
    dot: '#B47B24',
    bg: '#FFF7E8',
    text: '#B47B24',
  },
  failed: {
    label: '失败',
    dot: '#C45C60',
    bg: '#FDF1F1',
    text: '#C45C60',
  },
  unconfigured: {
    label: '未配置',
    dot: '#8A96A8',
    bg: '#F2F4F8',
    text: '#647289',
  },
}

/* ===================================================== */
/* Hook：集中管理配置状态                                  */
/* ===================================================== */

function useKnowledgeConfig() {
  const [config, setConfig] = useState<KnowledgeConfig>(() => DEFAULT_CONFIG)
  const [saving, setSaving] = useState(false)
  const [rebuilding, setRebuilding] = useState(false)
  const [rebuildProgress, setRebuildProgress] = useState(0)

  const isDirty = useMemo(
    () => JSON.stringify(config) !== JSON.stringify(DEFAULT_CONFIG),
    [config],
  )

  const patchChunking = (
    updater: (c: KnowledgeConfig['chunking']) => KnowledgeConfig['chunking'],
  ) =>
    setConfig((prev) => ({ ...prev, chunking: updater(prev.chunking) }))

  const setIndexing = (mode: KnowledgeConfig['indexing']) =>
    setConfig((prev) => ({ ...prev, indexing: mode }))

  const setRetrieval = (mode: KnowledgeConfig['retrieval']) =>
    setConfig((prev) => ({ ...prev, retrieval: mode }))

  const patchHybrid = (
    updater: (h: KnowledgeConfig['hybrid']) => KnowledgeConfig['hybrid'],
  ) =>
    setConfig((prev) => ({ ...prev, hybrid: updater(prev.hybrid) }))

  const reset = () => {
    setConfig(DEFAULT_CONFIG)
    message.info('已恢复默认配置')
  }

  const save = async () => {
    setSaving(true)
    await new Promise((r) => setTimeout(r, 500))
    setSaving(false)

    setRebuilding(true)
    setRebuildProgress(0)

    let progress = 0
    const timer = window.setInterval(() => {
      progress = Math.min(
        100,
        progress + Math.max(3, Math.round((100 - progress) * 0.15)),
      )
      setRebuildProgress(progress)
      if (progress >= 100) {
        window.clearInterval(timer)
        window.setTimeout(() => setRebuilding(false), 600)
      }
    }, 350)

    message.success('配置已保存，索引重建已开始')
  }

  return {
    config,
    isDirty,
    saving,
    rebuilding,
    rebuildProgress,
    patchChunking,
    setIndexing,
    setRetrieval,
    patchHybrid,
    reset,
    save,
  }
}

/* ===================================================== */
/* Hook：文档列表状态                                      */
/* ===================================================== */

function useKnowledgeDocs() {
  const [docs, setDocs] = useState<DocRow[]>(DOC_ROWS_INIT)
  const [search, setSearch] = useState('')
  const [typeFilter, setTypeFilter] = useState<string | undefined>()
  const [statusFilter, setStatusFilter] = useState<string | undefined>()
  const [pageSize, setPageSize] = useState(10)
  const [page, setPage] = useState(1)
  const [selected, setSelected] = useState<string[]>([])

  const filtered = useMemo(() => {
    return docs.filter((d) => {
      if (search && !d.fileName.toLowerCase().includes(search.toLowerCase()))
        return false
      if (typeFilter && d.type !== typeFilter) return false
      if (statusFilter && d.status !== statusFilter) return false
      return true
    })
  }, [docs, search, typeFilter, statusFilter])

  const paged = useMemo(() => {
    const start = (page - 1) * pageSize
    return filtered.slice(start, start + pageSize)
  }, [filtered, page, pageSize])

  const toggleRow = (id: string) => {
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    )
  }

  const toggleAll = () => {
    const allIds = paged.map((d) => d.id)
    const allSelected = allIds.every((id) => selected.includes(id))
    if (allSelected) {
      setSelected((prev) => prev.filter((id) => !allIds.includes(id)))
    } else {
      setSelected((prev) => Array.from(new Set([...prev, ...allIds])))
    }
  }

  const retry = (id: string) => {
    setDocs((prev) =>
      prev.map((d) =>
        d.id === id ? { ...d, status: 'processing' as DocStatus } : d,
      ),
    )
    message.info('已重新开始处理')
    // 模拟处理 → 索引
    window.setTimeout(() => {
      setDocs((prev) =>
        prev.map((d) =>
          d.id === id
            ? { ...d, status: 'indexed' as DocStatus, chunks: 96 }
            : d,
        ),
      )
      message.success('文档索引完成')
    }, 1800)
  }

  const remove = (ids: string[]) => {
    setDocs((prev) => prev.filter((d) => !ids.includes(d.id)))
    setSelected((prev) => prev.filter((id) => !ids.includes(id)))
    message.success(`已删除 ${ids.length} 个文档`)
  }

  const addDoc = (file: {
    name: string
    size: number
    ext: DocRow['type']
  }) => {
    const id = `d_${Date.now()}`
    const sizeKB =
      file.size < 1024
        ? `${file.size} B`
        : file.size < 1024 * 1024
          ? `${(file.size / 1024).toFixed(1)} KB`
          : `${(file.size / 1024 / 1024).toFixed(1)} MB`

    const newDoc: DocRow = {
      id,
      fileName: file.name,
      type: file.ext,
      typeLabel:
        file.ext === 'PDF'
          ? 'PDF'
          : file.ext === 'YML'
            ? '结构化'
            : file.ext === 'XLS'
              ? 'Excel'
              : 'Markdown',
      chunks: null,
      vendor: '全局',
      functionTag: '自动识别',
      status: 'processing',
      size: sizeKB,
      updatedAt: new Date().toISOString().slice(0, 10),
    }
    setDocs((prev) => [newDoc, ...prev])
    // 模拟处理
    window.setTimeout(() => {
      setDocs((prev) =>
        prev.map((d) =>
          d.id === id
            ? { ...d, status: 'indexed' as DocStatus, chunks: Math.floor(Math.random() * 200) + 40 }
            : d,
        ),
      )
      message.success(`${file.name} 索引完成`)
    }, 2200)
  }

  return {
    docs,
    search,
    setSearch,
    typeFilter,
    setTypeFilter,
    statusFilter,
    setStatusFilter,
    page,
    setPage,
    pageSize,
    setPageSize,
    selected,
    setSelected,
    filtered,
    paged,
    toggleRow,
    toggleAll,
    retry,
    remove,
    addDoc,
  }
}

/* ===================================================== */
/* 校验                                                   */
/* ===================================================== */

interface ChunkingErrors {
  delimiter?: string
  maxLength?: string
  overlap?: string
  parentDelimiter?: string
  parentMaxLength?: string
  childDelimiter?: string
  childMaxLength?: string
}

function validateChunking(
  cfg: KnowledgeConfig['chunking'],
): ChunkingErrors {
  const e: ChunkingErrors = {}
  if (cfg.mode === 'general') {
    if (!cfg.general.delimiter.trim()) e.delimiter = '分隔符不能为空'
    if (
      !Number.isFinite(cfg.general.maxLength) ||
      cfg.general.maxLength < 20 ||
      cfg.general.maxLength > 5000
    ) {
      e.maxLength = '应在 20-5000 之间'
    }
    if (
      !Number.isFinite(cfg.general.overlap) ||
      cfg.general.overlap < 0 ||
      cfg.general.overlap >= cfg.general.maxLength
    ) {
      e.overlap = '应 ≥ 0 且小于最大分段长度'
    }
  } else if (cfg.mode === 'parent-child') {
    const pc = cfg.parentChild
    if (!pc.parent.delimiter.trim())
      e.parentDelimiter = '父分段分隔符不能为空'
    if (
      !Number.isFinite(pc.parent.maxLength) ||
      pc.parent.maxLength < 20 ||
      pc.parent.maxLength > 5000
    ) {
      e.parentMaxLength = '应在 20-5000 之间'
    }
    if (!pc.child.delimiter.trim())
      e.childDelimiter = '子分段分隔符不能为空'
    if (
      !Number.isFinite(pc.child.maxLength) ||
      pc.child.maxLength < 20 ||
      pc.child.maxLength > 5000
    ) {
      e.childMaxLength = '应在 20-5000 之间'
    }
  }
  return e
}

interface HybridErrors {
  topK?: string
  scoreThreshold?: string
}

function validateHybrid(cfg: KnowledgeConfig): HybridErrors {
  if (cfg.retrieval !== 'hybrid') return {}
  const e: HybridErrors = {}
  if (
    !Number.isFinite(cfg.hybrid.topK) ||
    cfg.hybrid.topK < 1 ||
    cfg.hybrid.topK > 50
  ) {
    e.topK = '应在 1-50 之间'
  }
  if (
    !Number.isFinite(cfg.hybrid.scoreThreshold) ||
    cfg.hybrid.scoreThreshold < 0 ||
    cfg.hybrid.scoreThreshold > 1
  ) {
    e.scoreThreshold = '应在 0-1 之间'
  }
  return e
}

/* ===================================================== */
/* 通用外壳                                                */
/* ===================================================== */

const sectionTitle =
  'mb-1 text-[15px] font-medium leading-[22px] text-ink-900'
const sectionSub = 'text-[11px] text-ink-500'

function SectionCard({
  title,
  sub,
  children,
  className = '',
}: {
  title: string
  sub?: string
  children: React.ReactNode
  className?: string
}) {
  return (
    <section
      className={`rounded-[8px] border border-line bg-white px-4 py-3 ${className}`}
    >
      <header className="mb-2.5 flex items-center gap-2">
        <h3 className={sectionTitle}>{title}</h3>
        {sub ? <span className={sectionSub}>{sub}</span> : null}
      </header>
      {children}
    </section>
  )
}

/* ===================================================== */
/* Chunking 分段模式                                       */
/* ===================================================== */

function ChunkingSection({
  chunking,
  patchChunking,
  errors,
}: {
  chunking: KnowledgeConfig['chunking']
  patchChunking: (
    u: (c: KnowledgeConfig['chunking']) => KnowledgeConfig['chunking'],
  ) => void
  errors: ChunkingErrors
}) {
  const selected = chunking.mode
  const expanded = selected

  const select = (mode: KnowledgeConfig['chunking']['mode']) =>
    patchChunking(() => ({ ...chunking, mode }))

  return (
    <SectionCard title="分段模式" sub="Chunking Strategy">
      <p className="mb-3 text-[12px] text-ink-500">
        选择文档的切分方式，平衡检索精度与上下文完整性
      </p>

      <div className="flex flex-col gap-2">
        {chunkingOptions.map((o) => {
          const isSelected = selected === o.value
          return (
            <div
              key={o.value}
              className={`rounded-lg border bg-white transition-colors ${
                isSelected
                  ? 'border-brand-line bg-white'
                  : 'border-line hover:border-brand-line'
              }`}
            >
              <button
                type="button"
                onClick={() => select(o.value)}
                className="flex w-full items-center gap-3 px-4 py-3 text-left"
              >
                <span
                  className={`flex h-4 w-4 shrink-0 items-center justify-center rounded-full border ${
                    isSelected ? 'border-brand' : 'border-line'
                  }`}
                >
                  {isSelected ? (
                    <span className="h-2 w-2 rounded-full bg-brand" />
                  ) : null}
                </span>
                <div className="flex min-w-0 flex-1 items-center justify-between">
                  <div className="flex min-w-0 items-center gap-2">
                    <span className="truncate text-[15px] font-semibold text-ink-900">
                      {o.title}
                    </span>
                    {o.tag ? (
                      <span className="rounded bg-brand-soft px-1.5 py-0.5 text-[10px] font-medium text-brand-strong">
                        {o.tag}
                      </span>
                    ) : null}
                  </div>
                  {isSelected ? (
                    <span className="rounded bg-brand-soft px-2 py-0.5 text-[10px] font-medium text-brand-strong">
                      已选择
                    </span>
                  ) : (
                    <span className="text-[12px] text-ink-400">›</span>
                  )}
                </div>
              </button>

              {isSelected && expanded ? (
                <div className="border-t border-line px-4 py-4">
                  <p className="mb-3 pl-7 text-[12px] text-ink-500">
                    {o.desc}
                  </p>

                  {o.value === 'general' ? (
                    <div className="grid gap-3 pl-7 md:grid-cols-3">
                      <div className="flex flex-col gap-2">
                        <label className="flex items-center gap-1 text-[12px] text-ink-500">
                          分隔符 (Delimiter)
                          <Tooltip title="支持 \\n、\\n\\n、#、--- 等">
                            <InfoCircleOutlined className="text-[12px]" />
                          </Tooltip>
                        </label>
                        <Input
                          size="middle"
                          value={chunking.general.delimiter}
                          onChange={(e) =>
                            patchChunking((c) => ({
                              ...c,
                              general: {
                                ...c.general,
                                delimiter: e.target.value,
                              },
                            }))
                          }
                          status={errors.delimiter ? 'error' : undefined}
                          className="!rounded-md"
                        />
                        {errors.delimiter ? (
                          <span className="text-[11px] text-danger">
                            {errors.delimiter}
                          </span>
                        ) : (
                          <span className="text-[11px] text-ink-400">
                            提示：例如输入 \n 或 # 进行段落切分。
                          </span>
                        )}
                      </div>

                      <div className="flex flex-col gap-2">
                        <label className="text-[12px] text-ink-500">
                          最大分段长度 (Max Length)
                        </label>
                        <div className="flex items-center gap-2">
                          <Input
                            size="middle"
                            type="number"
                            min={20}
                            max={5000}
                            value={chunking.general.maxLength}
                            onChange={(e) =>
                              patchChunking((c) => ({
                                ...c,
                                general: {
                                  ...c.general,
                                  maxLength: Number(e.target.value) || 0,
                                },
                              }))
                            }
                            status={errors.maxLength ? 'error' : undefined}
                            className="!w-24 !rounded-md"
                          />
                          <span className="text-[11px] text-ink-400">
                            tokens
                          </span>
                        </div>
                        {errors.maxLength ? (
                          <span className="text-[11px] text-danger">
                            {errors.maxLength}
                          </span>
                        ) : null}
                      </div>

                      <div className="flex flex-col gap-2">
                        <label className="flex items-center gap-1 text-[12px] text-ink-500">
                          分段重叠 (Chunk Overlap)
                          <Tooltip title="相邻分段之间的重叠 token 数，用于保持上下文">
                            <InfoCircleOutlined className="text-[12px]" />
                          </Tooltip>
                        </label>
                        <div className="flex items-center gap-2">
                          <Input
                            size="middle"
                            type="number"
                            min={0}
                            value={chunking.general.overlap}
                            onChange={(e) =>
                              patchChunking((c) => ({
                                ...c,
                                general: {
                                  ...c.general,
                                  overlap: Number(e.target.value) || 0,
                                },
                              }))
                            }
                            status={errors.overlap ? 'error' : undefined}
                            className="!w-24 !rounded-md"
                          />
                          <span className="text-[11px] text-ink-400">
                            tokens
                          </span>
                        </div>
                        {errors.overlap ? (
                          <span className="text-[11px] text-danger">
                            {errors.overlap}
                          </span>
                        ) : (
                          <span className="text-[11px] text-ink-400">
                            适合命令说明、FAQ 等结构清晰的短文本。
                          </span>
                        )}
                      </div>
                    </div>
                  ) : o.value === 'parent-child' ? (
                    <div className="flex flex-col gap-4 pl-7">
                      {/* Parent-chunk group */}
                      <div className="rounded-md border border-line bg-[#F7F9FC] px-4 py-3">
                        <div className="mb-2.5 flex items-center gap-2">
                          <span className="text-[12px] font-semibold text-ink-700">
                            Parent-chunk
                          </span>
                          <span className="text-[11px] text-ink-400">
                            （父分段 · 返回给大模型的完整上下文）
                          </span>
                        </div>
                        <div className="grid gap-3 md:grid-cols-2">
                          <div className="flex flex-col gap-1.5">
                            <label className="flex items-center gap-1 text-[12px] text-ink-500">
                              分隔符 (Delimiter)
                              <Tooltip title="父分段切分边界，建议使用 \\n\\n 或章节号">
                                <InfoCircleOutlined className="text-[12px]" />
                              </Tooltip>
                            </label>
                            <Input
                              size="middle"
                              value={chunking.parentChild.parent.delimiter}
                              onChange={(e) =>
                                patchChunking((c) => ({
                                  ...c,
                                  parentChild: {
                                    ...c.parentChild,
                                    parent: {
                                      ...c.parentChild.parent,
                                      delimiter: e.target.value,
                                    },
                                  },
                                }))
                              }
                              status={
                                errors.parentDelimiter ? 'error' : undefined
                              }
                              className="!rounded-md"
                            />
                            {errors.parentDelimiter ? (
                              <span className="text-[11px] text-danger">
                                {errors.parentDelimiter}
                              </span>
                            ) : null}
                          </div>

                          <div className="flex flex-col gap-1.5">
                            <label className="text-[12px] text-ink-500">
                              最大分段长度 (Max Length)
                            </label>
                            <div className="flex items-center gap-2">
                              <Input
                                size="middle"
                                type="number"
                                min={20}
                                max={5000}
                                value={chunking.parentChild.parent.maxLength}
                                onChange={(e) =>
                                  patchChunking((c) => ({
                                    ...c,
                                    parentChild: {
                                      ...c.parentChild,
                                      parent: {
                                        ...c.parentChild.parent,
                                        maxLength: Number(e.target.value) || 0,
                                      },
                                    },
                                  }))
                                }
                                status={
                                  errors.parentMaxLength ? 'error' : undefined
                                }
                                className="!w-28 !rounded-md"
                              />
                              <span className="text-[11px] text-ink-400">
                                tokens
                              </span>
                            </div>
                            {errors.parentMaxLength ? (
                              <span className="text-[11px] text-danger">
                                {errors.parentMaxLength}
                              </span>
                            ) : (
                              <span className="text-[11px] text-ink-400">
                                建议 ≥ 子分段长度，容纳完整段落。
                              </span>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Child-chunk group */}
                      <div className="rounded-md border border-line bg-[#F7F9FC] px-4 py-3">
                        <div className="mb-2.5 flex items-center gap-2">
                          <span className="text-[12px] font-semibold text-ink-700">
                            Child-chunk for Retrieval
                          </span>
                          <span className="text-[11px] text-ink-400">
                            （子分段 · 用于向量检索的精准切片）
                          </span>
                        </div>
                        <div className="grid gap-3 md:grid-cols-2">
                          <div className="flex flex-col gap-1.5">
                            <label className="flex items-center gap-1 text-[12px] text-ink-500">
                              分隔符 (Delimiter)
                              <Tooltip title="子分段切分边界，通常更细粒度如 \\n">
                                <InfoCircleOutlined className="text-[12px]" />
                              </Tooltip>
                            </label>
                            <Input
                              size="middle"
                              value={chunking.parentChild.child.delimiter}
                              onChange={(e) =>
                                patchChunking((c) => ({
                                  ...c,
                                  parentChild: {
                                    ...c.parentChild,
                                    child: {
                                      ...c.parentChild.child,
                                      delimiter: e.target.value,
                                    },
                                  },
                                }))
                              }
                              status={
                                errors.childDelimiter ? 'error' : undefined
                              }
                              className="!rounded-md"
                            />
                            {errors.childDelimiter ? (
                              <span className="text-[11px] text-danger">
                                {errors.childDelimiter}
                              </span>
                            ) : null}
                          </div>

                          <div className="flex flex-col gap-1.5">
                            <label className="text-[12px] text-ink-500">
                              最大分段长度 (Max Length)
                            </label>
                            <div className="flex items-center gap-2">
                              <Input
                                size="middle"
                                type="number"
                                min={20}
                                max={5000}
                                value={chunking.parentChild.child.maxLength}
                                onChange={(e) =>
                                  patchChunking((c) => ({
                                    ...c,
                                    parentChild: {
                                      ...c.parentChild,
                                      child: {
                                        ...c.parentChild.child,
                                        maxLength: Number(e.target.value) || 0,
                                      },
                                    },
                                  }))
                                }
                                status={
                                  errors.childMaxLength ? 'error' : undefined
                                }
                                className="!w-28 !rounded-md"
                              />
                              <span className="text-[11px] text-ink-400">
                                tokens
                              </span>
                            </div>
                            {errors.childMaxLength ? (
                              <span className="text-[11px] text-danger">
                                {errors.childMaxLength}
                              </span>
                            ) : (
                              <span className="text-[11px] text-ink-400">
                                建议 200-500，检索精度更高。
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  ) : o.value === 'qa' ? (
                    <div className="pl-7 text-[12px] text-ink-500">
                      系统将自动识别 Markdown / Excel 中的 Q&amp;A 结构，按问答对切片入库。
                      暂无需额外配置。
                    </div>
                  ) : null}
                </div>
              ) : null}
            </div>
          )
        })}
      </div>
    </SectionCard>
  )
}

/* ===================================================== */
/* Indexing 索引模式                                       */
/* ===================================================== */

function IndexingSection({
  mode,
  setMode,
}: {
  mode: KnowledgeConfig['indexing']
  setMode: (m: KnowledgeConfig['indexing']) => void
}) {
  return (
    <SectionCard title="索引模式" sub="Indexing Mode">
      <div className="flex flex-col gap-2.5 md:flex-row">
        {[
          {
            key: 'high' as const,
            title: '高质量',
            desc: '调用多模态嵌入模型处理文本/图片，精度高。',
          },
          {
            key: 'economical' as const,
            title: '经济',
            desc: '仅提取关键词，不耗 Token。',
          },
        ].map((o) => {
          const active = mode === o.key
          return (
            <button
              type="button"
              key={o.key}
              onClick={() => setMode(o.key)}
              className={`flex h-[64px] flex-1 items-center gap-3 rounded-lg border px-4 text-left transition-colors ${
                active
                  ? 'border-brand-line bg-[#F0F4FA]'
                  : 'border-line bg-white hover:border-brand-line'
              }`}
            >
              <span
                className={`flex h-4 w-4 shrink-0 items-center justify-center rounded-full border ${
                  active ? 'border-brand' : 'border-line'
                }`}
              >
                {active ? (
                  <span className="h-2 w-2 rounded-full bg-brand" />
                ) : null}
              </span>
              <div className="flex min-w-0 flex-col gap-1">
                <span className="truncate text-[14px] font-semibold text-ink-900">
                  {o.title}
                </span>
                <span className="truncate text-[12px] text-ink-500">
                  {o.desc}
                </span>
              </div>
            </button>
          )
        })}
      </div>
    </SectionCard>
  )
}

/* ===================================================== */
/* Retrieval 检索设置                                     */
/* ===================================================== */

function SliderBar({
  value,
  onChange,
  disabled,
}: {
  value: number
  onChange: (v: number) => void
  disabled?: boolean
}) {
  return (
    <input
      type="range"
      min={0}
      max={100}
      value={value}
      disabled={disabled}
      onChange={(e) => onChange(Number(e.target.value))}
      className="h-[3px] w-full cursor-pointer appearance-none rounded-full bg-[#CDD7E6] disabled:opacity-60
                 [&::-webkit-slider-thumb]:h-3 [&::-webkit-slider-thumb]:w-3
                 [&::-webkit-slider-thumb]:appearance-none
                 [&::-webkit-slider-thumb]:rounded-full
                 [&::-webkit-slider-thumb]:border-2
                 [&::-webkit-slider-thumb]:border-brand
                 [&::-webkit-slider-thumb]:bg-white"
      style={{
        background: `linear-gradient(to right, #3268DB 0%, #3268DB ${value}%, #CDD7E6 ${value}%, #CDD7E6 100%)`,
      }}
    />
  )
}

function RetrievalSection({
  retrieval,
  setRetrieval,
  hybrid,
  patchHybrid,
  errors,
}: {
  retrieval: KnowledgeConfig['retrieval']
  setRetrieval: (m: KnowledgeConfig['retrieval']) => void
  hybrid: KnowledgeConfig['hybrid']
  patchHybrid: (
    u: (h: KnowledgeConfig['hybrid']) => KnowledgeConfig['hybrid'],
  ) => void
  errors: HybridErrors
}) {
  const hybridActive = retrieval === 'hybrid'

  return (
    <SectionCard title="检索设置" sub="Retrieval Settings">
      <div className="mb-2 grid gap-2.5 md:grid-cols-2">
        {[
          { key: 'vector' as const, title: '向量检索' },
          { key: 'fulltext' as const, title: '全文检索' },
        ].map((o) => {
          const active = retrieval === o.key
          return (
            <button
              type="button"
              key={o.key}
              onClick={() => setRetrieval(o.key)}
              className={`flex h-10 items-center gap-2.5 rounded-lg border px-4 text-left transition-colors ${
                active
                  ? 'border-brand-line bg-[#F0F4FA]'
                  : 'border-line bg-white hover:border-brand-line'
              }`}
            >
              <span
                className={`flex h-4 w-4 shrink-0 items-center justify-center rounded-full border ${
                  active ? 'border-brand' : 'border-line'
                }`}
              >
                {active ? (
                  <span className="h-2 w-2 rounded-full bg-brand" />
                ) : null}
              </span>
              <span className="text-[13px] font-medium text-ink-900">
                {o.title}
              </span>
            </button>
          )
        })}
      </div>

      <button
        type="button"
        onClick={() => setRetrieval('hybrid')}
        className={`w-full rounded-lg border px-4 py-3 text-left transition-colors ${
          hybridActive
            ? 'border-brand-line bg-[#F0F4FA]'
            : 'border-line bg-white hover:border-brand-line'
        }`}
      >
        <div className="flex items-center gap-2.5">
          <span
            className={`flex h-4 w-4 shrink-0 items-center justify-center rounded-full border ${
              hybridActive ? 'border-brand' : 'border-line'
            }`}
          >
            {hybridActive ? (
              <span className="h-2 w-2 rounded-full bg-brand" />
            ) : null}
          </span>
          <div className="flex min-w-0 items-center gap-2">
            <span className="text-[14px] font-semibold text-ink-900">
              混合检索
            </span>
            <span className="rounded bg-brand-soft px-1.5 py-0.5 text-[10px] font-medium text-brand-strong">
              推荐
            </span>
          </div>
        </div>
        {hybridActive ? (
          <>
            <p className="ml-6 mt-1 text-[12px] text-ink-500">
              同时执行向量与全文检索，并应用重排序步骤。
            </p>

            <div className="mt-2.5 ml-6 rounded-md bg-[#F0F4FA] px-3 py-2">
              <div className="flex flex-wrap items-center gap-x-5 gap-y-2 text-[12px]">
                <label className="flex items-center gap-2">
                  <span className="text-ink-500">语义权重</span>
                  <span className="font-mono text-brand-strong">
                    {hybrid.semanticWeight}%
                  </span>
                </label>
                <div className="flex flex-1 min-w-[200px] items-center">
                  <SliderBar
                    value={hybrid.semanticWeight}
                    onChange={(v) =>
                      patchHybrid((h) => ({
                        ...h,
                        semanticWeight: v,
                      }))
                    }
                  />
                </div>
                <label className="flex items-center gap-2">
                  <span className="text-ink-500">关键词权重</span>
                  <span className="font-mono text-brand-strong">
                    {100 - hybrid.semanticWeight}%
                  </span>
                </label>
              </div>

              <div className="mt-2.5 flex flex-wrap items-center gap-x-5 gap-y-2 text-[12px]">
                <label className="flex items-center gap-2">
                  <span className="text-ink-500">Top K 召回数量</span>
                  <Input
                    size="middle"
                    type="number"
                    min={1}
                    max={50}
                    value={hybrid.topK}
                    onChange={(e) =>
                      patchHybrid((h) => ({
                        ...h,
                        topK: Number(e.target.value) || 0,
                      }))
                    }
                    status={errors.topK ? 'error' : undefined}
                    className="!w-24 !rounded-md"
                  />
                </label>
                {errors.topK ? (
                  <span className="text-[11px] text-danger">{errors.topK}</span>
                ) : null}

                <label className="flex items-center gap-2">
                  <span className="text-ink-500">Score 匹配阈值</span>
                  <Input
                    size="middle"
                    type="number"
                    step={0.1}
                    min={0}
                    max={1}
                    value={hybrid.scoreThreshold}
                    onChange={(e) =>
                      patchHybrid((h) => ({
                        ...h,
                        scoreThreshold: Number(e.target.value) || 0,
                      }))
                    }
                    status={errors.scoreThreshold ? 'error' : undefined}
                    className="!w-24 !rounded-md"
                  />
                </label>
                {errors.scoreThreshold ? (
                  <span className="text-[11px] text-danger">
                    {errors.scoreThreshold}
                  </span>
                ) : null}
              </div>
            </div>
          </>
        ) : null}
      </button>
    </SectionCard>
  )
}

/* ===================================================== */
/* 文档列表主体                                            */
/* ===================================================== */

function FileTypeBadge({ type }: { type: DocRow['type'] }) {
  const meta = TYPE_BADGE[type]
  return (
    <span
      className="flex h-7 w-[52px] shrink-0 items-center justify-center rounded-md text-[11px] font-semibold"
      style={{ backgroundColor: meta.bg, color: meta.text }}
    >
      {meta.label}
    </span>
  )
}

function StatusPill({ status }: { status: DocStatus }) {
  const m = STATUS_META[status]
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[11px] font-medium"
      style={{ backgroundColor: m.bg, color: m.text }}
    >
      <span
        className="inline-block h-[6px] w-[6px] rounded-full"
        style={{ backgroundColor: m.dot }}
      />
      {m.label}
    </span>
  )
}

function DocListSection({
  docsState,
  kbName,
}: {
  docsState: ReturnType<typeof useKnowledgeDocs>
  kbName: string
}) {
  const {
    filtered,
    paged,
    page,
    setPage,
    pageSize,
    setPageSize,
    selected,
    toggleAll,
    toggleRow,
    search,
    setSearch,
    typeFilter,
    setTypeFilter,
    statusFilter,
    setStatusFilter,
    retry,
    remove,
  } = docsState

  const allSelectedOnPage =
    paged.length > 0 && paged.every((d) => selected.includes(d.id))

  return (
    <div className="flex flex-col gap-4">
      {/* 列表容器 */}
      <div className="overflow-hidden rounded-lg border border-line bg-white shadow-panel">
        {/* 过滤器 */}
        <div className="flex flex-wrap items-center gap-2 border-b border-line px-4 py-3">
          <div className="relative">
            <SearchOutlined className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[12px] text-ink-400" />
            <Input
              size="middle"
              placeholder="搜索文件名…"
              prefix={null}
              value={search}
              onChange={(e) => {
                setSearch(e.target.value)
                setPage(1)
              }}
              className=" !w-[320px] !pl-8 !rounded-md"
            />
          </div>

          <div className="flex items-center gap-1.5">
            <span className="text-[12px] text-ink-500">类型</span>
            <Select
              value={typeFilter}
              placeholder="全部"
              allowClear
              size="middle"
              style={{ width: 120 }}
              onChange={(v) => {
                setTypeFilter(v)
                setPage(1)
              }}
              options={[
                { value: 'PDF', label: 'PDF' },
                { value: 'YML', label: '结构化' },
                { value: 'XLS', label: 'Excel' },
                { value: 'MD', label: 'Markdown' },
              ]}
            />
          </div>

          <div className="flex items-center gap-1.5">
            <span className="text-[12px] text-ink-500">状态</span>
            <Select
              value={statusFilter}
              placeholder="全部"
              allowClear
              size="middle"
              style={{ width: 120 }}
              onChange={(v) => {
                setStatusFilter(v)
                setPage(1)
              }}
              options={[
                { value: 'indexed', label: '已索引' },
                { value: 'processing', label: '处理中' },
                { value: 'failed', label: '失败' },
                { value: 'unconfigured', label: '未配置' },
              ]}
            />
          </div>

          <div className="ml-auto flex items-center gap-2">
            <Dropdown
              menu={{
                items: [
                  {
                    key: 'delete',
                    icon: <DeleteOutlined />,
                    label: '批量删除',
                    danger: true,
                    disabled: selected.length === 0,
                    onClick: () => remove(selected),
                  },
                ],
              }}
            >
              <Button size="middle" className="!rounded-md">
                批量操作
                <DownOutlined className="ml-1 text-[10px]" />
              </Button>
            </Dropdown>
            <Button
              type="primary"
              size="middle"
              icon={<TagsOutlined />}
              onClick={() => message.info('元数据管理功能待实现')}
              className=" !rounded-[5px]"
              style={{ width: 132 }}
            >
              元数据管理
            </Button>
          </div>
        </div>

        {/* 表格区域：允许横向滚动 */}
        <div className="overflow-x-auto">
          <div className="min-w-[1100px]">
            {/* 表头 */}
            <div
              className="grid grid-cols-[32px_minmax(240px,2.2fr)_100px_110px_1.5fr_130px_160px] items-center gap-3 border-b border-line px-4 text-[12px] font-medium text-ink-500"
              style={{ height: 56, backgroundColor: '#F7F9FC' }}
            >
              <Checkbox
                checked={allSelectedOnPage}
                indeterminate={selected.length > 0 && !allSelectedOnPage}
                onChange={toggleAll}
              />
              <span>文件名</span>
              <span>类型</span>
              <span>分块数</span>
              <span>厂商 / 功能元数据</span>
              <span>状态</span>
              <span className="text-right">操作</span>
            </div>

            {/* 行 */}
            {paged.length === 0 ? (
              <div className="flex h-[200px] flex-col items-center justify-center gap-2 text-[13px] text-ink-400">
                <ExclamationCircleOutlined className="text-[20px]" />
                暂无匹配的文档
              </div>
            ) : (
              paged.map((d) => {
                const checked = selected.includes(d.id)
                return (
                  <div
                    key={d.id}
                    className={`grid grid-cols-[32px_minmax(240px,2.2fr)_100px_110px_1.5fr_130px_160px] items-center gap-3 border-b border-line px-4 transition-colors last:border-b-0 ${
                      checked ? 'bg-[#F5F8FD]' : 'bg-white hover:bg-[#FAFCFF]'
                    }`}
                    style={{ minHeight: 112 }}
                  >
                    {/* checkbox */}
                    <Checkbox
                      checked={checked}
                      onChange={() => toggleRow(d.id)}
                    />

                    {/* 文件名 */}
                    <div className="flex min-w-0 items-center gap-3">
                      <FileTypeBadge type={d.type} />
                      <div className="min-w-0 flex-1">
                        <div className="truncate text-[14px] font-semibold text-ink-900">
                          {d.fileName}
                        </div>
                        <div className="mt-0.5 truncate text-[11px] text-ink-400">
                          {d.typeLabel} · {d.size} · 更新于 {d.updatedAt}
                        </div>
                      </div>
                    </div>

                    {/* 类型 */}
                    <span className="text-[12px] text-ink-700">
                      {d.typeLabel}
                    </span>

                    {/* 分块数 */}
                    <span
                      className={`text-[13px] font-medium ${
                        d.dynamicChunks
                          ? 'text-brand'
                          : d.chunks == null
                            ? 'text-ink-400'
                            : 'text-ink-900'
                      }`}
                    >
                      {d.dynamicChunks
                        ? '动态'
                        : d.chunks == null
                          ? '—'
                          : d.chunks}
                    </span>

                    {/* 厂商 / 功能 */}
                    <div className="flex min-w-0 items-center gap-1.5">
                      <span className="shrink-0 rounded bg-[#F2F4F8] px-2 py-0.5 text-[11px] text-ink-700">
                        {d.vendor}
                      </span>
                      <span className="truncate text-[12px] text-ink-500">
                        / {d.functionTag}
                      </span>
                    </div>

                    {/* 状态 */}
                    <div>
                      <StatusPill status={d.status} />
                    </div>

                    {/* 操作 */}
                    <div className="flex shrink-0 items-center justify-end gap-3 text-[12px]">
                      {d.status === 'failed' ? (
                        <button
                          type="button"
                          onClick={() => retry(d.id)}
                          className="flex items-center gap-1 text-brand hover:text-brand-strong"
                        >
                          <ReloadOutlined className="text-[12px]" />
                          重试
                        </button>
                      ) : null}
                      <button
                        type="button"
                        className="flex items-center gap-1 text-ink-500 hover:text-brand"
                      >
                        <EditOutlined className="text-[12px]" />
                        元数据
                      </button>
                      <button
                        type="button"
                        className="flex items-center gap-1 text-ink-500 hover:text-danger"
                        onClick={() => remove([d.id])}
                      >
                        <DeleteOutlined className="text-[12px]" />
                      </button>
                    </div>
                  </div>
                )
              })
            )}
          </div>
        </div>

        {/* 分页 + banner */}
        <div className="border-t border-line px-4 py-4">
          <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
            <span className="text-[12px] text-ink-500">
              共 {filtered.length} 条文档
            </span>
            <div className="flex items-center gap-1">
              <Button
                size="middle"
                disabled={page === 1}
                onClick={() => setPage(page - 1)}
                className="!rounded-md"
              >
                ‹
              </Button>
              <button
                type="button"
                onClick={() => setPage(1)}
                className="flex h-7 min-w-[28px] items-center justify-center rounded-md bg-brand-soft px-2 text-[12px] font-medium text-brand"
              >
                1
              </button>
              <Button
                size="middle"
                disabled={paged.length < pageSize}
                onClick={() => setPage(page + 1)}
                className="!rounded-md"
              >
                ›
              </Button>
              <Select
                value={pageSize}
                onChange={(v) => {
                  setPageSize(v)
                  setPage(1)
                }}
                size="small"
                style={{ width: 96 }}
                className="ml-2"
                options={[
                  { value: 10, label: '10 条 / 页' },
                  { value: 20, label: '20 条 / 页' },
                  { value: 50, label: '50 条 / 页' },
                ]}
              />
            </div>
          </div>

          {/* 提示 banner */}
          <div className="flex h-12 items-center gap-2 rounded-md bg-brand-soft px-4 text-[12px] text-[#3863AD]">
            <InfoCircleOutlined className="text-[14px]" />
            提示：上传后将自动进行分块与索引；结构化文档的分块数动态生成。失败文档可点击「重试」。
          </div>

          {/* 底部说明 */}
          <div className="mt-3 flex flex-wrap items-center justify-between gap-2 border-t border-line pt-3 text-[11px] text-ink-400">
            <span>支持 PDF、YAML、Excel、Markdown 等格式</span>
            <span>当前知识库：{kbName}</span>
          </div>
        </div>
      </div>
    </div>
  )
}

/* ===================================================== */
/* 上传抽屉                                                */
/* ===================================================== */

function UploadDrawer({
  open,
  onClose,
  onAdd,
}: {
  open: boolean
  onClose: () => void
  onAdd: (file: {
    name: string
    size: number
    ext: DocRow['type']
  }) => void
}) {
  const [fileList, setFileList] = useState<UploadFile[]>([])
  const [uploading, setUploading] = useState(false)

  const extMap: Record<string, DocRow['type']> = {
    pdf: 'PDF',
    yml: 'YML',
    yaml: 'YML',
    xls: 'XLS',
    xlsx: 'XLS',
    md: 'MD',
    markdown: 'MD',
  }

  const handleUpload = async () => {
    if (fileList.length === 0) {
      message.warning('请先选择文件')
      return
    }
    setUploading(true)
    for (const f of fileList) {
      const name = f.name.toLowerCase()
      const ext =
        extMap[name.split('.').pop() ?? ''] ?? 'MD'
      onAdd({ name: f.name, size: f.size ?? 0, ext })
      await new Promise((r) => setTimeout(r, 300))
    }
    setUploading(false)
    setFileList([])
    onClose()
  }

  return (
    <Drawer
      title="上传文档"
      placement="right"
      size={480}
      open={open}
      onClose={onClose}
      footer={
        <div className="flex items-center justify-end gap-2">
          <Button onClick={onClose} disabled={uploading}>
            取消
          </Button>
          <Button
            type="primary"
            icon={<UploadOutlined />}
            loading={uploading}
            onClick={handleUpload}
          >
            {uploading ? '上传中…' : '确认上传'}
          </Button>
        </div>
      }
    >
      <Upload.Dragger
        multiple
        fileList={fileList}
        onChange={({ fileList: fl }) => setFileList(fl)}
        accept=".pdf,.yml,.yaml,.xls,.xlsx,.md,.markdown"
        beforeUpload={() => false}
      >
        <p className="ant-upload-drag-icon">
          <UploadOutlined />
        </p>
        <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
        <p className="ant-upload-hint">
          支持 PDF、YAML、Excel、Markdown，单次最多 20 个
        </p>
      </Upload.Dragger>

      <div className="mt-4 rounded-md bg-brand-soft px-3 py-2 text-[12px] text-[#3863AD]">
        上传完成后，文档将自动进入分块与索引流程。结构化文档会动态计算分块数。
      </div>
    </Drawer>
  )
}

/* ===================================================== */
/* 主页面                                                 */
/* ===================================================== */

const tabs = [
  { key: 'doc', label: '文档管理', icon: <FileTextOutlined /> },
  {
    key: 'vector',
    label: '向量与检索配置',
    icon: <DatabaseOutlined />,
    count: 3,
  },
]

export function KnowledgeSettingsPage() {
  const {
    config,
    isDirty,
    saving,
    rebuilding,
    rebuildProgress,
    patchChunking,
    setIndexing,
    setRetrieval,
    patchHybrid,
    reset,
    save,
  } = useKnowledgeConfig()

  const docsState = useKnowledgeDocs()
  const [tab, setTab] = useState<'doc' | 'vector'>('vector')
  const [uploadOpen, setUploadOpen] = useState(false)
  const [kbName, setKbName] = useState('网络配置核心库')

  const chunkingErrors = validateChunking(config.chunking)
  const hybridErrors = validateHybrid(config)
  const hasErrors =
    Object.keys(chunkingErrors).length > 0 ||
    Object.keys(hybridErrors).length > 0

  const canSave = isDirty && !hasErrors && !saving && !rebuilding

  const footerText = useMemo(() => {
    const parts: string[] = []
    parts.push(
      config.chunking.mode === 'general'
        ? 'General'
        : config.chunking.mode === 'parent-child'
          ? 'Parent-Child'
          : 'Q&A',
    )
    if (config.chunking.mode === 'general') {
      parts.push(`${config.chunking.general.maxLength} tokens`)
      parts.push(`重叠 ${config.chunking.general.overlap} tokens`)
    } else if (config.chunking.mode === 'parent-child') {
      parts.push(
        `父 ${config.chunking.parentChild.parent.maxLength} / 子 ${config.chunking.parentChild.child.maxLength} tokens`,
      )
    }
    parts.push(config.indexing === 'high' ? '高质量' : '经济')
    parts.push(
      config.retrieval === 'vector'
        ? '向量检索'
        : config.retrieval === 'fulltext'
          ? '全文检索'
          : `混合检索 · 语义 ${config.hybrid.semanticWeight}%`,
    )
    return parts.join(' · ')
  }, [config])

  return (
    <div className="flex min-h-full flex-col">
      {/* 标题栏 */}
      <PageHeader
        title="知识库配置"
        subtitle={
          <span className="flex items-center gap-1.5 text-xs text-ink-400">
            <span>知识库：</span>
            <Select
              value={kbName}
              onChange={(v) => {
                setKbName(v)
                message.info(`已切换到「${v}」`)
              }}
              size="small"
              variant="borderless"
              className="!min-w-[140px] !text-[13px] !text-brand"
              style={{ paddingInline: 0 }}
              options={[
                { value: '网络配置核心库', label: '网络配置核心库' },
                { value: '安全策略库', label: '安全策略库' },
                { value: '故障排查手册库', label: '故障排查手册库' },
                { value: '全厂商命令参考库', label: '全厂商命令参考库' },
              ]}
            />
          </span>
        }
        right={
          <>
            {rebuilding ? (
              <StatusTag tone="warn">
                索引重建中… {rebuildProgress}%
              </StatusTag>
            ) : tab === 'doc' ? (
              <StatusTag tone="blue">
                {docsState.filtered.length} 个文档 ·{' '}
                {docsState.filtered.filter((d) => d.status === 'indexed')
                  .length}{' '}
                已索引
              </StatusTag>
            ) : (
              <StatusTag tone="green">当前索引可用</StatusTag>
            )}
            <button
              type="button"
              className="flex h-9 items-center gap-2 rounded-md border border-line bg-white px-3 text-[13px] text-ink-500"
            >
              <ToolOutlined className="text-[13px]" />
              配置说明
            </button>
          </>
        }
      />

      {/* 页签与右侧按钮 */}
      <div className="flex flex-col gap-4 px-4 py-4 md:flex-row md:items-center md:justify-between md:px-7 md:py-5">
        <div className="flex items-end gap-6">
          {tabs.map((t) => {
            const active = tab === t.key
            return (
              <button
                type="button"
                key={t.key}
                onClick={() => setTab(t.key as 'doc' | 'vector')}
                className="relative flex flex-col items-start gap-1"
              >
                <span
                  className={`flex items-center gap-1.5 pb-2 text-[14px] ${
                    active ? 'font-semibold text-brand' : 'text-ink-500'
                  }`}
                >
                  <span className="text-[16px]">{t.icon}</span>
                  {t.label}
                  {t.count && tab === 'vector' && active ? (
                    <StatusTag tone="blue">{t.count}</StatusTag>
                  ) : null}
                </span>
                {active ? (
                  <span className="absolute -bottom-[17px] h-[3px] w-full rounded-t bg-brand" />
                ) : null}
              </button>
            )
          })}
        </div>

        {/* Doc tab: 只显示 上传文档；Vector tab: 恢复默认 + 保存并重建 */}
        {tab === 'doc' ? (
          <Button
            type="primary"
            size="middle"
            icon={<PlusOutlined />}
            onClick={() => setUploadOpen(true)}
            className="!rounded-[5px]"
          >
            上传文档
          </Button>
        ) : (
          <div className="flex flex-wrap items-center gap-2.5">
            <span className="mr-1 hidden text-[12px] text-ink-500 lg:inline">
              {hasErrors ? (
                <span className="text-danger">表单存在校验错误</span>
              ) : (
                '修改后需重建索引生效'
              )}
            </span>
            <Tooltip
              title={
                !isDirty
                  ? '当前已是默认配置'
                  : '将所有设置恢复到默认值'
              }
            >
              <Button onClick={reset} disabled={!isDirty || saving}>
                恢复默认
              </Button>
            </Tooltip>
            <Button
              type="primary"
              size="middle"
              onClick={save}
              loading={saving}
              disabled={!canSave}
              className="!rounded-[5px]"
            >
              保存并重建索引
            </Button>
          </div>
        )}
      </div>

      {/* 主体 */}
      <div className="flex flex-1 flex-col gap-4 px-4 pb-4 md:px-7">
        {tab === 'vector' ? (
          <>
            {rebuilding ? (
              <div className="rounded-lg border border-line bg-white px-5 py-4">
                <div className="mb-1.5 flex items-center gap-2 text-[13px] font-medium text-ink-900">
                  <SettingOutlined className="animate-spin text-brand" />
                  索引重建中… 重建完成前继续使用现有索引
                </div>
                <Progress
                  percent={rebuildProgress}
                  status="active"
                  showInfo={false}
                />
              </div>
            ) : null}

            <ChunkingSection
              chunking={config.chunking}
              patchChunking={patchChunking}
              errors={chunkingErrors}
            />
            <IndexingSection
              mode={config.indexing}
              setMode={setIndexing}
            />
            <RetrievalSection
              retrieval={config.retrieval}
              setRetrieval={setRetrieval}
              hybrid={config.hybrid}
              patchHybrid={patchHybrid}
              errors={hybridErrors}
            />

            <div className="flex h-8 items-center gap-2 rounded-md bg-brand-soft px-4 text-[12px] text-[#3863AD]">
              <span className="flex h-4 w-4 shrink-0 items-center justify-center rounded-full border border-brand bg-white text-[9px] font-bold text-brand">
                i
              </span>
              保存后将按新配置重新切分文档并重建索引。重建完成前，检索继续使用现有索引。
            </div>

            {isDirty && !hasErrors ? (
              <Tag color="blue">有未保存修改</Tag>
            ) : null}
          </>
        ) : (
          <DocListSection
            docsState={docsState}
            kbName={kbName}
          />
        )}
      </div>

      {/* 页脚 */}
      {tab === 'vector' ? (
        <footer className="flex h-[54px] shrink-0 flex-col items-start justify-center gap-0.5 border-t border-line bg-white px-4 text-[11px] text-ink-500 md:flex-row md:items-center md:justify-between md:px-7">
          <span>当前配置：{footerText}</span>
          <span>知识库配置仅对「{kbName}」生效</span>
        </footer>
      ) : null}

      {/* 上传抽屉 */}
      <UploadDrawer
        open={uploadOpen}
        onClose={() => setUploadOpen(false)}
        onAdd={docsState.addDoc}
      />
    </div>
  )
}
