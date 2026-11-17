import {
  CloseOutlined,
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
  ToolOutlined,
  UploadOutlined,
} from '@ant-design/icons'
import {
  Button,
  Checkbox,
  Drawer,
  Dropdown,
  Input,
  Modal,
  Select,
  Tooltip,
  Upload,
  message,
} from 'antd'
import type { UploadFile } from 'antd'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import Markdown from 'react-markdown'
import type { Components } from 'react-markdown'
import remarkGfm from 'remark-gfm'
import configGuide from '../../../knowledges/docs/知识库配置说明.md?raw'
import {
  deleteKnowledgeDocument,
  fetchKnowledgeBases,
  fetchKnowledgeDocuments,
  retryKnowledgeDocument,
  updateKnowledgeBaseConfig,
  updateKnowledgeDocumentMetadata,
  updateKnowledgeDocumentsMetadata,
  uploadKnowledgeDocument,
} from '../api/knowledge'
import type {
  KnowledgeBaseConfigPayload,
  KnowledgeBaseDto,
  KnowledgeDocumentDto,
  KnowledgeDocumentStage,
} from '../api/knowledge'
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
  retrieval: 'embedding' | 'bm25' | 'hybrid'
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

function configFromBase(base: KnowledgeBaseDto): KnowledgeConfig {
  return {
    chunking: {
      mode: base.chunking_mode,
      general: {
        delimiter:
          base.general_delimiter ?? DEFAULT_CONFIG.chunking.general.delimiter,
        maxLength:
          base.general_max_length ??
          DEFAULT_CONFIG.chunking.general.maxLength,
        overlap:
          base.general_overlap ?? DEFAULT_CONFIG.chunking.general.overlap,
      },
      parentChild: {
        parent: {
          delimiter:
            base.parent_delimiter ??
            DEFAULT_CONFIG.chunking.parentChild.parent.delimiter,
          maxLength:
            base.parent_max_length ??
            DEFAULT_CONFIG.chunking.parentChild.parent.maxLength,
        },
        child: {
          delimiter:
            base.child_delimiter ??
            DEFAULT_CONFIG.chunking.parentChild.child.delimiter,
          maxLength:
            base.child_max_length ??
            DEFAULT_CONFIG.chunking.parentChild.child.maxLength,
        },
      },
    },
    indexing: base.indexing_mode,
    retrieval: base.retrieval_mode,
    hybrid: {
      semanticWeight: base.hybrid_semantic_weight,
      topK: base.hybrid_top_k,
      scoreThreshold: Number(base.hybrid_score_threshold),
    },
  }
}

function toConfigPayload(config: KnowledgeConfig): KnowledgeBaseConfigPayload {
  return {
    chunking_mode: config.chunking.mode,
    general_delimiter: config.chunking.general.delimiter,
    general_max_length: config.chunking.general.maxLength,
    general_overlap: config.chunking.general.overlap,
    parent_delimiter: config.chunking.parentChild.parent.delimiter,
    parent_max_length: config.chunking.parentChild.parent.maxLength,
    child_delimiter: config.chunking.parentChild.child.delimiter,
    child_max_length: config.chunking.parentChild.child.maxLength,
    indexing_mode: config.indexing,
    retrieval_mode: config.retrieval,
    hybrid_semantic_weight: config.hybrid.semanticWeight,
    hybrid_top_k: config.hybrid.topK,
    hybrid_score_threshold: config.hybrid.scoreThreshold,
  }
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

export type DocStatus =
  | 'pending'
  | 'processing'
  | 'indexed'
  | 'failed'
  | 'configured'
  | 'needmanual'

export interface DocRow {
  id: string
  fileName: string
  type: 'PDF' | 'YML' | 'XLS' | 'MD'
  typeLabel: string
  dynamicChunks?: boolean
  chunks: number | null
  metadata: Record<string, string>
  status: DocStatus
  stage: KnowledgeDocumentStage | null
  progress: number
  totalChunks: number | null
  processedChunks: number
  errorMessage: string | null
  size: string
  updatedAt: string
}

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
  pending: {
    label: '排队中',
    dot: '#8A96A8',
    bg: '#F2F4F8',
    text: '#647289',
  },
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
  configured: {
    label: '已配置',
    dot: '#3268DB',
    bg: '#EAF1FF',
    text: '#3268DB',
  },
  needmanual: {
    label: '待补充',
    dot: '#B47B24',
    bg: '#FFF7E8',
    text: '#B47B24',
  },
}

/* 文件大小格式化 */
function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

/* ===================================================== */
/* Hook：集中管理配置状态                                  */
/* ===================================================== */

function useKnowledgeConfig() {
  const [config, setConfig] = useState<KnowledgeConfig>(() => DEFAULT_CONFIG)
  const [savedConfig, setSavedConfig] =
    useState<KnowledgeConfig>(() => DEFAULT_CONFIG)
  const [saving, setSaving] = useState(false)

  const isDirty = useMemo(
    () => JSON.stringify(config) !== JSON.stringify(savedConfig),
    [config, savedConfig],
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

  const load = useCallback(
    (next: KnowledgeConfig, draft?: KnowledgeConfig) => {
      setConfig(draft ?? next)
      setSavedConfig(next)
    },
    [],
  )

  const save = async (baseId: number) => {
    setSaving(true)
    let updated: KnowledgeBaseDto
    try {
      updated = await updateKnowledgeBaseConfig(
        baseId,
        toConfigPayload(config),
      )
      const next = configFromBase(updated)
      setConfig(next)
      setSavedConfig(next)
      message.success('配置已保存')
    } catch (error) {
      message.error(error instanceof Error ? error.message : '保存配置失败')
      return undefined
    } finally {
      setSaving(false)
    }

    return updated
  }

  return {
    config,
    isDirty,
    saving,
    patchChunking,
    setIndexing,
    setRetrieval,
    patchHybrid,
    load,
    save,
  }
}

/* ===================================================== */
/* Hook：文档列表状态                                      */
/* ===================================================== */

const FILE_TYPE_MAP: Record<KnowledgeDocumentDto['file_type'], DocRow['type']> = {
  pdf: 'PDF',
  yaml: 'YML',
  excel: 'XLS',
  markdown: 'MD',
}

const FILE_TYPE_LABEL: Record<DocRow['type'], string> = {
  PDF: 'PDF',
  YML: '结构化',
  XLS: 'Excel',
  MD: 'Markdown',
}

function toDocRow(dto: KnowledgeDocumentDto): DocRow {
  const metadata = dto.metadata_json ?? {}
  const metadataPairs = Object.fromEntries(
    Object.entries(metadata).map(([key, value]) => [
      key,
      typeof value === 'string' ? value : JSON.stringify(value),
    ]),
  )
  const type = FILE_TYPE_MAP[dto.file_type]
  return {
    id: String(dto.id),
    fileName: dto.file_name,
    type,
    typeLabel: FILE_TYPE_LABEL[type],
    chunks: dto.chunk_count,
    metadata: metadataPairs,
    status: dto.status,
    stage: dto.stage,
    progress: dto.progress,
    totalChunks: dto.total_chunks,
    processedChunks: dto.processed_chunks,
    errorMessage: dto.error_message,
    size: formatFileSize(dto.file_size),
    updatedAt: dto.updated_at.slice(0, 10),
  }
}

function useKnowledgeDocs(kbId: number | null) {
  const [docs, setDocs] = useState<DocRow[]>([])
  const [loading, setLoading] = useState(false)
  const [search, setSearch] = useState('')
  const [typeFilter, setTypeFilter] = useState<string | undefined>()
  const [statusFilter, setStatusFilter] = useState<string | undefined>()
  const [pageSize, setPageSize] = useState(10)
  const [page, setPage] = useState(1)
  const [selected, setSelected] = useState<string[]>([])

  const reload = useCallback(
    async (showError = true) => {
      if (kbId == null) {
        setDocs([])
        return
      }
      setLoading(true)
      try {
        const data = await fetchKnowledgeDocuments(kbId)
        setDocs(data.items.map(toDocRow))
      } catch (error) {
        if (showError) {
          message.error(
            error instanceof Error ? error.message : '加载文档列表失败',
          )
        }
      } finally {
        setLoading(false)
      }
    },
    [kbId],
  )

  useEffect(() => {
    // 异步执行，避免在 effect 内同步触发额外渲染
    void (async () => {
      setSelected([])
      setPage(1)
      await reload()
    })()
  }, [reload])

  const hasProcessing = useMemo(
    () =>
      docs.some(
        (doc) => doc.status === 'pending' || doc.status === 'processing',
      ),
    [docs],
  )

  useEffect(() => {
    if (!hasProcessing || kbId == null) return
    const timer = window.setInterval(() => {
      void reload(false)
    }, 2500)
    return () => window.clearInterval(timer)
  }, [hasProcessing, kbId, reload])

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

  const retry = async (id: string) => {
    try {
      await retryKnowledgeDocument(Number(id))
      message.success('已重新提交处理')
      await reload(false)
    } catch (error) {
      message.error(error instanceof Error ? error.message : '重试失败')
    }
  }

  const remove = async (ids: string[]) => {
    if (ids.length === 0) return
    const results = await Promise.allSettled(
      ids.map((id) => deleteKnowledgeDocument(Number(id))),
    )
    const failed = results.filter((item) => item.status === 'rejected')
    if (failed.length > 0) {
      message.error(`${failed.length} 个文档删除失败`)
    } else {
      message.success(`已删除 ${ids.length} 个文档`)
    }
    setSelected((prev) => prev.filter((id) => !ids.includes(id)))
    await reload(false)
  }

  const saveMetadata = async (
    id: string,
    metadata: Record<string, string>,
  ) => {
    const dto = await updateKnowledgeDocumentMetadata(Number(id), metadata)
    const row = toDocRow(dto)
    setDocs((prev) => prev.map((doc) => (doc.id === id ? row : doc)))
    message.success('元数据已保存')
  }

  const saveMetadataBatch = async (
    ids: string[],
    metadata: Record<string, string>,
  ) => {
    const dtos = await updateKnowledgeDocumentsMetadata(
      ids.map(Number),
      metadata,
    )
    const rows = new Map(dtos.map((dto) => [String(dto.id), toDocRow(dto)]))
    setDocs((prev) => prev.map((doc) => rows.get(doc.id) ?? doc))
    setSelected([])
    message.success(`已更新 ${dtos.length} 个文档的元数据`)
  }

  return {
    docs,
    loading,
    reload,
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
    saveMetadata,
    saveMetadataBatch,
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
const optionTitle =
  'text-[14px] font-semibold leading-[20px] text-ink-900'

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
                    <span className={`truncate ${optionTitle}`}>
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
                          <span className="text-[13px] font-semibold text-ink-700">
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
                          <span className="text-[13px] font-semibold text-ink-700">
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
                <span className={`truncate ${optionTitle}`}>
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
          { key: 'embedding' as const, title: '向量检索' },
          { key: 'bm25' as const, title: '关键词检索' },
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
              <span className={optionTitle}>
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
            <span className={optionTitle}>
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

const STAGE_LABEL: Record<KnowledgeDocumentStage, string> = {
  parsing: '解析中',
  chunking: '切分中',
  embedding: '向量化',
  indexing: '写入索引',
  verifying: '校验索引',
  done: '已完成',
}

function StatusCell({ doc }: { doc: DocRow }) {
  const active = doc.status === 'pending' || doc.status === 'processing'
  return (
    <div className="min-w-0">
      <StatusPill status={doc.status} />
      {active && doc.stage ? (
        <div className="mt-1.5 w-[138px]">
          <div className="h-1 overflow-hidden rounded-full bg-[#EEF2F8]">
            <div
              className="h-full rounded-full bg-brand transition-all"
              style={{ width: `${Math.max(2, Math.min(100, doc.progress))}%` }}
            />
          </div>
          <div className="mt-1 truncate text-[10px] leading-3 text-ink-400">
            {STAGE_LABEL[doc.stage]} {doc.progress}%
            {doc.totalChunks
              ? ` · ${doc.processedChunks}/${doc.totalChunks}`
              : ''}
          </div>
        </div>
      ) : null}
      {(doc.status === 'failed' || doc.status === 'needmanual') &&
      doc.errorMessage ? (
        <div
          className="mt-1 w-[138px] truncate text-[10px]"
          style={{ color: doc.status === 'failed' ? '#C45C60' : '#B47B24' }}
          title={doc.errorMessage}
        >
          {doc.errorMessage}
        </div>
      ) : null}
    </div>
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
    saveMetadata,
    saveMetadataBatch,
  } = docsState

  const [metadataDoc, setMetadataDoc] = useState<DocRow | null>(null)
  const [batchMetadataOpen, setBatchMetadataOpen] = useState(false)
  const [metadataPairs, setMetadataPairs] = useState<
    { key: string; value: string }[]
  >([])
  const [metadataSaving, setMetadataSaving] = useState(false)

  const allSelectedOnPage =
    paged.length > 0 && paged.every((d) => selected.includes(d.id))

  const openMetadata = (doc: DocRow) => {
    setBatchMetadataOpen(false)
    setMetadataDoc(doc)
    setMetadataPairs(
      Object.entries(doc.metadata).map(([key, value]) => ({ key, value })),
    )
  }

  const openBatchMetadata = () => {
    setMetadataDoc(null)
    setMetadataPairs([])
    setBatchMetadataOpen(true)
  }

  const closeMetadata = () => {
    if (metadataSaving) return
    setMetadataDoc(null)
    setBatchMetadataOpen(false)
    setMetadataPairs([])
  }

  const updatePair = (
    index: number,
    field: 'key' | 'value',
    value: string,
  ) => {
    setMetadataPairs((prev) =>
      prev.map((pair, i) => (i === index ? { ...pair, [field]: value } : pair)),
    )
  }

  const removePair = (index: number) => {
    setMetadataPairs((prev) => prev.filter((_, i) => i !== index))
  }

  const addPair = () => {
    setMetadataPairs((prev) => [...prev, { key: '', value: '' }])
  }

  const saveMetadataChanges = async () => {
    if (!metadataDoc && !batchMetadataOpen) return
    const payload: Record<string, string> = {}
    for (const pair of metadataPairs) {
      const key = pair.key.trim()
      if (!key) {
        message.warning('元数据键不能为空')
        return
      }
      if (key in payload) {
        message.warning(`存在重复的键：${key}`)
        return
      }
      payload[key] = pair.value
    }

    setMetadataSaving(true)
    try {
      if (batchMetadataOpen) {
        await saveMetadataBatch(selected, payload)
      } else if (metadataDoc) {
        await saveMetadata(metadataDoc.id, payload)
      }
      setMetadataDoc(null)
      setBatchMetadataOpen(false)
      setMetadataPairs([])
    } catch (error) {
      message.error(error instanceof Error ? error.message : '保存元数据失败')
    } finally {
      setMetadataSaving(false)
    }
  }

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
                { value: 'pending', label: '排队中' },
                { value: 'processing', label: '处理中' },
                { value: 'indexed', label: '已索引' },
                { value: 'failed', label: '失败' },
                { value: 'needmanual', label: '待补充' },
                { value: 'configured', label: '已配置' },
              ]}
            />
          </div>

          <div className="ml-auto flex items-center gap-2">
            <Dropdown
              menu={{
                items: [
                  {
                    key: 'metadata',
                    icon: <EditOutlined />,
                    label: '批量元数据配置',
                    disabled: selected.length === 0,
                    onClick: openBatchMetadata,
                  },
                  {
                    key: 'delete',
                    icon: <DeleteOutlined />,
                    label: '批量删除',
                    danger: true,
                    disabled: selected.length === 0,
                    onClick: () => void remove(selected),
                  },
                ],
              }}
            >
              <Button size="middle" className="!rounded-md">
                批量操作
                <DownOutlined className="ml-1 text-[10px]" />
              </Button>
            </Dropdown>
          </div>
        </div>

        {/* 表格区域：允许横向滚动 */}
        <div className="overflow-x-auto">
          <div className="min-w-[1140px]">
            {/* 表头 */}
            <div
              className="grid grid-cols-[32px_minmax(240px,2.2fr)_100px_110px_1.5fr_170px_160px] items-center gap-3 border-b border-line px-4 text-[12px] font-medium text-ink-500"
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
              <span>元数据</span>
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
                const metadataEntries = Object.entries(d.metadata)
                return (
                  <div
                    key={d.id}
                    className={`grid grid-cols-[32px_minmax(240px,2.2fr)_100px_110px_1.5fr_170px_160px] items-center gap-3 border-b border-line px-4 transition-colors last:border-b-0 ${
                      checked ? 'bg-[#F5F8FD]' : 'bg-white hover:bg-[#FAFCFF]'
                    }`}
                    style={{ minHeight: 76 }}
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

                    {/* 元数据 */}
                    <div className="min-w-0">
                      {metadataEntries.length === 0 ? (
                        <span className="text-[12px] text-ink-400">--</span>
                      ) : (
                        <span
                          className="block truncate text-[12px] text-ink-700"
                          title={metadataEntries
                            .map(([key, value]) => `${key}=${value}`)
                            .join('\n')}
                        >
                          {metadataEntries.map(([, value]) => value).join(' · ')}
                        </span>
                      )}
                    </div>

                    {/* 状态 */}
                    <StatusCell doc={d} />

                    {/* 操作 */}
                    <div className="flex shrink-0 items-center justify-end gap-3 text-[12px]">
                      {d.status === 'failed' || d.status === 'needmanual' ? (
                        <button
                          type="button"
                          onClick={() => void retry(d.id)}
                          className="flex items-center gap-1 text-brand hover:text-brand-strong"
                        >
                          <ReloadOutlined className="text-[12px]" />
                          重试
                        </button>
                      ) : null}
                      <button
                        type="button"
                        onClick={() => openMetadata(d)}
                        className="flex items-center gap-1 text-ink-500 hover:text-brand"
                      >
                        <EditOutlined className="text-[12px]" />
                        元数据
                      </button>
                      {d.status !== 'processing' ? (
                        <button
                          type="button"
                          className="flex items-center gap-1 text-ink-500 hover:text-danger"
                          onClick={() => void remove([d.id])}
                        >
                          <DeleteOutlined className="text-[12px]" />
                        </button>
                      ) : null}
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

      <Modal
        open={metadataDoc !== null || batchMetadataOpen}
        title={
          batchMetadataOpen
            ? `批量元数据配置 · 已选中 ${selected.length} 个文档`
            : `元数据 · ${metadataDoc?.fileName ?? ''}`
        }
        okText="保存"
        cancelText="取消"
        confirmLoading={metadataSaving}
        onOk={() => void saveMetadataChanges()}
        onCancel={closeMetadata}
        width={620}
      >
        {batchMetadataOpen ? (
          <div className="mb-2 rounded-md bg-brand-soft px-3 py-2 text-[12px] text-[#3863AD]">
            保存后将用下方键值对整组替换所选文档的元数据。
          </div>
        ) : null}
        <div className="flex flex-col gap-2 pt-1">
          {metadataPairs.length === 0 ? (
            <div className="rounded-md border border-dashed border-line px-4 py-6 text-center text-[12px] text-ink-400">
              {batchMetadataOpen
                ? '尚未添加元数据，点击下方「新增一项」添加'
                : '暂无元数据，点击下方「新增一项」添加'}
            </div>
          ) : (
            metadataPairs.map((pair, index) => (
              <div
                key={index}
                className="grid grid-cols-[1fr_1.4fr_28px] items-center gap-2"
              >
                <Input
                  value={pair.key}
                  placeholder="键，如 vendor"
                  maxLength={64}
                  onChange={(e) => updatePair(index, 'key', e.target.value)}
                />
                <Input
                  value={pair.value}
                  placeholder="值，如 华为"
                  onChange={(e) => updatePair(index, 'value', e.target.value)}
                />
                <button
                  type="button"
                  aria-label="删除"
                  onClick={() => removePair(index)}
                  className="flex h-8 w-8 items-center justify-center rounded-md text-ink-400 hover:bg-[#FDF1F1] hover:text-danger"
                >
                  <DeleteOutlined />
                </button>
              </div>
            ))
          )}
          <button
            type="button"
            onClick={addPair}
            className="mt-1 flex h-8 items-center justify-center gap-1 rounded-md border border-dashed border-line text-[12px] text-brand hover:border-brand hover:bg-brand-soft"
          >
            <PlusOutlined />
            新增一项
          </button>
        </div>
      </Modal>
    </div>
  )
}

/* ===================================================== */
/* 上传抽屉                                                */
/* ===================================================== */

function UploadDrawer({
  open,
  onClose,
  kbId,
  onUploaded,
}: {
  open: boolean
  onClose: () => void
  kbId: number | null
  onUploaded: () => void
}) {
  const [fileList, setFileList] = useState<UploadFile[]>([])
  const [uploading, setUploading] = useState(false)

  const handleUpload = async () => {
    if (fileList.length === 0) {
      message.warning('请先选择文件')
      return
    }
    if (kbId == null) {
      message.warning('请先选择知识库')
      return
    }

    setUploading(true)
    const failures: string[] = []
    try {
      for (const item of fileList) {
        const file = item.originFileObj as File | undefined
        if (!file) continue
        try {
          const result = await uploadKnowledgeDocument(kbId, file)
          if (result.result === 'failed') {
            failures.push(`${result.file_name}：${result.error ?? '上传失败'}`)
          }
        } catch (error) {
          failures.push(
            `${item.name}：${error instanceof Error ? error.message : '上传失败'}`,
          )
        }
      }
    } finally {
      setUploading(false)
    }

    setFileList([])
    onUploaded()
    onClose()
    if (failures.length > 0) {
      message.error(failures.join('；'))
    } else {
      message.success('文档已提交，正在后台处理')
    }
  }

  return (
    <Drawer
      closable={false}
      placement="right"
      width={480}
      open={open}
      onClose={onClose}
      title={
        <div className="flex items-center gap-2">
          <span className="flex h-6 w-6 items-center justify-center rounded-md bg-brand-soft text-brand">
            <UploadOutlined className="text-[13px]" />
          </span>
          <span className="text-[14px] font-medium text-ink-900">上传文档</span>
          {fileList.length > 0 ? (
            <span className="rounded-full bg-soft px-1.5 py-[1px] text-[11px] text-ink-400">
              {fileList.length}
            </span>
          ) : null}
        </div>
      }
      extra={
        <button
          type="button"
          aria-label="关闭"
          onClick={onClose}
          className="flex h-7 w-7 items-center justify-center rounded-md text-ink-400 transition-colors hover:bg-soft hover:text-ink-700"
        >
          <CloseOutlined className="text-[12px]" />
        </button>
      }
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
      styles={{
        wrapper: { boxShadow: 'none' },
        header: {
          padding: '14px 20px',
          borderBottom: '1px solid #E4EAF2',
          background: '#FFFFFF',
        },
        body: { padding: '16px 18px', background: '#F7F9FC' },
        footer: {
          padding: '12px 18px',
          borderTop: '1px solid #E4EAF2',
          background: '#FFFFFF',
        },
        section: {
          width: 'calc(100% - 12px)',
          height: 'calc(100% - 24px)',
          margin: '12px 12px 12px 0',
          borderRadius: 16,
          overflow: 'hidden',
          boxShadow: '0 10px 40px rgba(32, 44, 64, 0.16)',
        },
      }}
    >
      <Upload.Dragger
        multiple
        showUploadList={false}
        fileList={fileList}
        onChange={({ fileList: fl }) => setFileList(fl)}
        accept=".pdf,.yml,.yaml,.xls,.xlsx,.md,.markdown"
        beforeUpload={() => false}
        className="[&_.ant-upload-drag]:!bg-white [&_.ant-upload-drag]:!px-4 [&_.ant-upload-drag]:!py-3 [&_.ant-upload-drag]:!h-[220px]"
      >
        <p className="ant-upload-drag-icon !mb-1.5">
          <UploadOutlined className="text-[26px] text-brand" />
        </p>
        <p className="ant-upload-text !mb-0 !text-[13px]">
          点击或拖拽文件到此区域上传
        </p>
        <p className="ant-upload-hint !mt-1 !text-[12px]">
          支持 PDF、YAML、Excel、Markdown，单次最多 20 个
        </p>
      </Upload.Dragger>

      {fileList.length > 0 ? (
        <div className="mt-3">
          <div className="mb-1.5 text-[12px] text-ink-500">
            待上传文件（{fileList.length}）
          </div>
          <ul className="space-y-1.5">
            {fileList.map((file) => (
              <li
                key={file.uid}
                className="flex items-center gap-2 rounded-md border border-line bg-white px-3 py-2"
              >
                <FileTextOutlined className="shrink-0 text-[13px] text-brand" />
                <span className="min-w-0 flex-1 truncate text-[12px] text-ink-700">
                  {file.name}
                </span>
                <span className="shrink-0 text-[11px] text-ink-400">
                  {formatFileSize(file.size ?? 0)}
                </span>
                <button
                  type="button"
                  aria-label={`删除 ${file.name}`}
                  onClick={() =>
                    setFileList((prev) =>
                      prev.filter((item) => item.uid !== file.uid),
                    )
                  }
                  className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md text-ink-400 transition-colors hover:bg-soft hover:text-danger"
                >
                  <DeleteOutlined className="text-[12px]" />
                </button>
              </li>
            ))}
          </ul>
        </div>
      ) : null}

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

/* 配置说明 Markdown 样式映射 */
const guideMarkdownComponents: Components = {
  // 抽屉标题已展示文档名称，正文不再重复一级标题
  h1: () => null,
  h2: ({ children }) => (
    <h2 className="mb-3 mt-7 flex items-center gap-2 text-[16px] font-semibold leading-6 text-ink-900">
      <span className="h-4 w-[3px] shrink-0 rounded-full bg-brand" />
      {children}
    </h2>
  ),
  h3: ({ children }) => (
    <h3 className="mb-2 mt-5 border-l-2 border-brand-line pl-2.5 text-[14px] font-semibold leading-6 text-ink-900">
      {children}
    </h3>
  ),
  h4: ({ children }) => (
    <h4 className="mb-2 mt-3 text-[13px] font-semibold leading-6 text-ink-700">
      {children}
    </h4>
  ),
  p: ({ children }) => (
    <p className="my-2.5 text-[13px] leading-[26px] text-ink-700">{children}</p>
  ),
  strong: ({ children }) => (
    <strong className="font-semibold text-ink-900">{children}</strong>
  ),
  a: ({ children, href }) => (
    <a
      href={href}
      target="_blank"
      rel="noreferrer"
      className="text-brand underline decoration-brand-line underline-offset-2 hover:text-brand-strong"
    >
      {children}
    </a>
  ),
  ul: ({ children }) => (
    <ul className="my-3 list-disc space-y-1.5 pl-5 text-[13px] leading-[26px] text-ink-700 marker:text-brand">
      {children}
    </ul>
  ),
  ol: ({ children }) => (
    <ol className="my-3 list-decimal space-y-1.5 pl-5 text-[13px] leading-[26px] text-ink-700 marker:font-medium marker:text-brand">
      {children}
    </ol>
  ),
  li: ({ children }) => (
    <li className="pl-0.5 [&_p]:my-0 [&_p]:leading-[26px]">{children}</li>
  ),
  blockquote: ({ children }) => (
    <blockquote className="my-4 rounded-lg border border-brand-line bg-brand-soft/50 px-4 py-2.5 text-[13px] leading-[26px] text-ink-500 [&_p]:my-0 [&_p]:leading-[26px]">
      {children}
    </blockquote>
  ),
  code: ({ children, className }) => (
    <code
      className={
        className
          ? 'font-mono text-[12px] text-ink-700'
          : 'rounded border border-[#DCE7FB] bg-[#F2F6FE] px-1.5 py-0.5 font-mono text-[12px] text-code-blue'
      }
    >
      {children}
    </code>
  ),
  pre: ({ children }) => (
    <pre className="my-4 overflow-x-auto rounded-lg border border-line bg-soft p-4 font-mono text-[12px] leading-[22px] text-ink-700">
      {children}
    </pre>
  ),
  table: ({ children }) => (
    <div className="my-4 overflow-x-auto rounded-lg border border-line shadow-panel">
      <table className="w-full border-collapse text-[13px] text-ink-700">
        {children}
      </table>
    </div>
  ),
  thead: ({ children }) => (
    <thead className="bg-[#F4F7FE] text-ink-900">{children}</thead>
  ),
  tbody: ({ children }) => (
    <tbody className="[&>tr:hover]:bg-brand-soft/40 [&>tr:nth-child(even)]:bg-soft [&>tr:last-child>td]:border-b-0">
      {children}
    </tbody>
  ),
  th: ({ children }) => (
    <th className="whitespace-nowrap border-b border-line px-4 py-2.5 text-left text-[12px] font-semibold">
      {children}
    </th>
  ),
  td: ({ children }) => (
    <td className="border-b border-line-soft px-4 py-2.5 align-top leading-[24px]">
      {children}
    </td>
  ),
  hr: () => <hr className="my-7 h-px border-0 bg-line" />,
}

/* 页签记忆：切换页面后恢复上次停留的页签 */
const KNOWLEDGE_TAB_LS_KEY = 'knowledge:tab'

function readStoredTab(): 'doc' | 'vector' {
  try {
    return localStorage.getItem(KNOWLEDGE_TAB_LS_KEY) === 'doc'
      ? 'doc'
      : 'vector'
  } catch {
    return 'vector'
  }
}

/* 选中的知识库与未保存配置的本地暂存 */
const KNOWLEDGE_BASE_LS_KEY = 'knowledge:base'

function readStoredBaseName(): string {
  try {
    return localStorage.getItem(KNOWLEDGE_BASE_LS_KEY) ?? ''
  } catch {
    return ''
  }
}

function configDraftKey(baseId: number): string {
  return `knowledge:config-draft:${baseId}`
}

function readConfigDraft(baseId: number): KnowledgeConfig | undefined {
  try {
    const raw = localStorage.getItem(configDraftKey(baseId))
    if (!raw) return undefined
    const parsed = JSON.parse(raw) as KnowledgeConfig
    return parsed?.chunking && parsed?.hybrid ? parsed : undefined
  } catch {
    return undefined
  }
}

function writeConfigDraft(baseId: number, config: KnowledgeConfig) {
  try {
    localStorage.setItem(configDraftKey(baseId), JSON.stringify(config))
  } catch {
    // 存储不可用时忽略，不影响页面使用
  }
}

function clearConfigDraft(baseId: number) {
  try {
    localStorage.removeItem(configDraftKey(baseId))
  } catch {
    // 存储不可用时忽略，不影响页面使用
  }
}

export function KnowledgeSettingsPage() {
  const {
    config,
    isDirty,
    saving,
    patchChunking,
    setIndexing,
    setRetrieval,
    patchHybrid,
    load,
    save,
  } = useKnowledgeConfig()

  const [tab, setTab] = useState<'doc' | 'vector'>(readStoredTab)
  const [uploadOpen, setUploadOpen] = useState(false)
  const [guideOpen, setGuideOpen] = useState(false)
  const [bases, setBases] = useState<KnowledgeBaseDto[]>([])
  const [kbName, setKbName] = useState<string>(readStoredBaseName)
  const [kbOptions, setKbOptions] = useState<{ value: string; label: string }[]>([])
  const [kbLoading, setKbLoading] = useState(true)

  useEffect(() => {
    try {
      localStorage.setItem(KNOWLEDGE_TAB_LS_KEY, tab)
    } catch {
      // 存储不可用时忽略，不影响页面使用
    }
  }, [tab])

  useEffect(() => {
    if (!kbName) return
    try {
      localStorage.setItem(KNOWLEDGE_BASE_LS_KEY, kbName)
    } catch {
      // 存储不可用时忽略，不影响页面使用
    }
  }, [kbName])

  useEffect(() => {
    let cancelled = false
    fetchKnowledgeBases()
      .then((items) => {
        if (cancelled) return
        setBases(items)
        setKbOptions(items.map((base) => ({ value: base.name, label: base.name })))
        setKbName((prev) =>
          items.some((base) => base.name === prev) ? prev : (items[0]?.name ?? ''),
        )
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          message.error(
            error instanceof Error ? error.message : '加载知识库列表失败',
          )
        }
      })
      .finally(() => {
        if (!cancelled) setKbLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  const selectedBase = useMemo(
    () => bases.find((base) => base.name === kbName),
    [bases, kbName],
  )
  const docsState = useKnowledgeDocs(selectedBase?.id ?? null)
  const loadedBaseId = useRef<number | null>(null)
  const skipDraftPersist = useRef(false)

  useEffect(() => {
    if (!selectedBase || loadedBaseId.current === selectedBase.id) return
    loadedBaseId.current = selectedBase.id
    skipDraftPersist.current = true
    load(configFromBase(selectedBase), readConfigDraft(selectedBase.id))
  }, [load, selectedBase])

  // 配置改动后暂存草稿，保存或还原后清除
  useEffect(() => {
    if (skipDraftPersist.current) {
      skipDraftPersist.current = false
      return
    }
    if (!selectedBase || loadedBaseId.current !== selectedBase.id) return
    if (isDirty) {
      writeConfigDraft(selectedBase.id, config)
    } else {
      clearConfigDraft(selectedBase.id)
    }
  }, [config, isDirty, selectedBase])

  const chunkingErrors = validateChunking(config.chunking)
  const hybridErrors = validateHybrid(config)
  const hasErrors =
    Object.keys(chunkingErrors).length > 0 ||
    Object.keys(hybridErrors).length > 0

  const canSave = isDirty && !hasErrors && !saving

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
      config.retrieval === 'embedding'
        ? '向量检索'
        : config.retrieval === 'bm25'
          ? '关键词检索'
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
              value={kbName || undefined}
              onChange={(v) => {
                setKbName(v)
                message.info(`已切换到「${v}」`)
              }}
              size="small"
              variant="borderless"
              loading={kbLoading}
              placeholder={kbLoading ? '加载中' : '暂无知识库'}
              className="!min-w-[180px] !pl-2 !text-[13px] !text-brand"
              options={kbOptions}
            />
          </span>
        }
        right={
          <>
            {tab === 'doc' ? (
              <StatusTag tone="blue">
                {docsState.filtered.length} 个文档 ·{' '}
                {docsState.filtered.filter((d) => d.status === 'indexed')
                  .length}{' '}
                已索引
              </StatusTag>
            ) : (
              <StatusTag tone={isDirty ? 'warn' : 'green'}>
                {isDirty ? '有未保存修改' : '已读取配置'}
              </StatusTag>
            )}
            <button
              type="button"
              onClick={() => setGuideOpen(true)}
              className="flex h-9 items-center gap-2 rounded-md border border-line bg-white px-3 text-[13px] text-ink-500 hover:border-brand-line hover:text-brand"
            >
              <ToolOutlined className="text-[13px]" />
              配置说明
            </button>
          </>
        }
      />

      {/* 页签与右侧按钮 */}
      <div className="flex flex-col gap-4 px-4 pb-1 pt-1.5 md:flex-row md:items-center md:justify-between md:px-7 md:pb-2 md:pt-2">
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
                  <span className="absolute -bottom-[1px] h-[3px] w-full rounded-t bg-brand md:-bottom-[5px]" />
                ) : null}
              </button>
            )
          })}
        </div>

        {/* Doc tab: 只显示 上传文档；Vector tab: 保存 */}
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
            {hasErrors ? (
              <span className="mr-1 hidden text-[12px] text-danger lg:inline">
                表单存在校验错误
              </span>
            ) : (
              <div className="mr-1 hidden h-8 items-center gap-2 rounded-md px-4 text-[12px] text-[#3863AD] lg:flex">
                <span className="flex h-4 w-4 shrink-0 items-center justify-center rounded-full border border-brand bg-white text-[9px] font-bold text-brand">
                  i
                </span>
                知识库已有文档切分时，不允许修改分段模式和索引模式
              </div>
            )}
            <Button
              type="primary"
              size="middle"
              onClick={() => {
                if (!selectedBase) return
                void save(selectedBase.id).then((updated) => {
                  if (!updated) return
                  setBases((prev) =>
                    prev.map((base) =>
                      base.id === updated.id ? updated : base,
                    ),
                  )
                })
              }}
              loading={saving}
              disabled={!canSave || !selectedBase}
              className="!rounded-[5px]"
            >
              保存
            </Button>
          </div>
        )}
      </div>

      {/* 主体 */}
      <div className="flex flex-1 flex-col gap-4 px-4 pb-4 md:px-7">
        {tab === 'vector' ? (
          <>
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
          <span>知识库配置仅对「{kbName || '未选择'}」生效</span>
        </footer>
      ) : null}

      {/* 上传抽屉 */}
      <UploadDrawer
        open={uploadOpen}
        onClose={() => setUploadOpen(false)}
        kbId={selectedBase?.id ?? null}
        onUploaded={() => void docsState.reload()}
      />

      {/* 配置说明预览 */}
      <Drawer
        placement="right"
        size={820}
        open={guideOpen}
        onClose={() => setGuideOpen(false)}
        title={
          <div className="flex items-center gap-3">
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-soft text-[16px] text-brand">
              <FileTextOutlined />
            </span>
            <span className="flex flex-col gap-0.5">
              <span className="text-[15px] font-semibold leading-5 text-ink-900">
                知识库配置说明
              </span>
              <span className="text-[12px] font-normal leading-4 text-ink-400">
                分段模式、索引模式、检索设置与元数据说明
              </span>
            </span>
          </div>
        }
        styles={{
          header: {
            borderBottom: '1px solid #E4EAF2',
            padding: '14px 24px',
            marginBottom: 0,
          },
          body: { padding: '4px 32px 40px' },
        }}
      >
        <div className="mx-auto max-w-[720px]">
          <Markdown
            remarkPlugins={[remarkGfm]}
            components={guideMarkdownComponents}
          >
            {configGuide}
          </Markdown>
        </div>
      </Drawer>
    </div>
  )
}
