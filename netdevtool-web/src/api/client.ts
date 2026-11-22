import { clearSession, readSession } from '../auth/session'
import { logger } from '../lib/logger'

export const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8083'

/** 已登录时返回鉴权头，未登录返回空对象 */
export function authHeaders(): Record<string, string> {
  const token = readSession()?.token
  return token ? { Authorization: `Bearer ${token}` } : {}
}

/** 解析后端统一错误响应 `{ code, message, detail }`，无响应体时退回状态码文案。 */
export async function toRequestError(response: Response, action: string): Promise<Error> {
  if (response.status === 401) {
    clearSession()
    if (!window.location.pathname.startsWith('/login')) {
      window.location.assign('/login')
    }
  }
  if (response.status >= 500) {
    logger.error('api.http_error', {
      action,
      status: response.status,
      path: new URL(response.url).pathname,
    })
  }
  const body = (await response.json().catch(() => null)) as { message?: string } | null
  return new Error(body?.message ?? `${action}：${response.status}`)
}
