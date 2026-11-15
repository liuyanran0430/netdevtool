/** 翻译页本地存储：源配置暂存、会话状态、检查点快照三组 localStorage 读写。 */

// ---------- 源配置暂存 ----------

const SOURCE_LS_KEY_TEXT = 'translate:source:text'
const SOURCE_LS_KEY_NAME = 'translate:source:fileName'
const SOURCE_LS_KEY_TIME = 'translate:source:savedAt'
const SOURCE_LS_TTL_MS = 24 * 60 * 60 * 1000 // 24h 过期

// ---------- 翻译页会话：设备选择 + 任务 requestId 暂存 ----------

const SESSION_LS_KEY = 'translate:session'
/** 开发环境不恢复上次会话与源配置，刷新页面即为干净状态 */
const RESTORE_PERSISTED_STATE = !import.meta.env.DEV

export interface TranslateSession {
  deviceType: string
  sourceVendor: string
  sourceModel: string
  targetVendor: string
  targetModel: string
  requestId: string | null
  submittedSignature: string | null
}

/** 开发环境的内存副本：同一次页面生命周期内切换路由不丢，刷新后重新初始化 */
let sessionMemo: TranslateSession | null = null
let sourceMemo: { text: string; fileName: string } | null = null

export function readSession(): TranslateSession | null {
  if (!RESTORE_PERSISTED_STATE) return sessionMemo
  try {
    const raw = localStorage.getItem(SESSION_LS_KEY)
    if (!raw) return null
    return JSON.parse(raw) as TranslateSession
  } catch {
    return null
  }
}

export function writeSession(session: TranslateSession) {
  if (!RESTORE_PERSISTED_STATE) {
    sessionMemo = session
    return
  }
  try {
    localStorage.setItem(SESSION_LS_KEY, JSON.stringify(session))
  } catch {
    // 隐私模式 / 配额满等场景下静默跳过
  }
}

export function readSourceCache(): { text: string; fileName: string } | null {
  if (!RESTORE_PERSISTED_STATE) return sourceMemo
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

export function writeSourceCache(text: string, fileName: string): boolean {
  if (!RESTORE_PERSISTED_STATE) {
    // 开发环境仍写 localStorage（用于“已自动保存”提示），但不作为刷新后的恢复来源
    sourceMemo = text ? { text, fileName } : null
  }
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

// ---------- 检查点：审计处理结果的本地快照，按 requestId 分组 ----------

const CHECKPOINTS_LS_KEY = 'translate:checkpoints'
const MAX_CHECKPOINTS = 20

export interface Checkpoint {
  id: string
  name: string
  createdAt: number
  reviews: Record<string, { tone: string; text?: string }>
}

// 开发环境用内存副本，刷新即清空，与会话恢复约定保持一致
let checkpointsMemo: Record<string, Checkpoint[]> | null = null

function readAllCheckpoints(): Record<string, Checkpoint[]> {
  if (!RESTORE_PERSISTED_STATE) return checkpointsMemo ?? {}
  try {
    const raw = localStorage.getItem(CHECKPOINTS_LS_KEY)
    return raw ? (JSON.parse(raw) as Record<string, Checkpoint[]>) : {}
  } catch {
    return {}
  }
}

function writeAllCheckpoints(all: Record<string, Checkpoint[]>) {
  if (!RESTORE_PERSISTED_STATE) {
    checkpointsMemo = all
    return
  }
  try {
    localStorage.setItem(CHECKPOINTS_LS_KEY, JSON.stringify(all))
  } catch {
    // 隐私模式 / 配额满等场景下静默跳过
  }
}

export function loadCheckpoints(requestId: string | null | undefined): Checkpoint[] {
  if (!requestId) return []
  return readAllCheckpoints()[requestId] ?? []
}

export function saveCheckpoint(
  requestId: string,
  name: string,
  reviews: Map<number, { tone: string; text?: string }>,
): Checkpoint[] {
  const record: Checkpoint['reviews'] = {}
  for (const [index, override] of reviews) record[String(index)] = override
  const checkpoint: Checkpoint = {
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
    name:
      name.trim() ||
      `检查点 ${new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}`,
    createdAt: Date.now(),
    reviews: record,
  }
  const all = readAllCheckpoints()
  const next = [checkpoint, ...(all[requestId] ?? [])].slice(0, MAX_CHECKPOINTS)
  all[requestId] = next
  writeAllCheckpoints(all)
  return next
}

export function deleteCheckpoint(requestId: string, id: string): Checkpoint[] {
  const all = readAllCheckpoints()
  const next = (all[requestId] ?? []).filter((item) => item.id !== id)
  all[requestId] = next
  writeAllCheckpoints(all)
  return next
}
