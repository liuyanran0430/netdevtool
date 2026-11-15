/** 登录会话：本地保存令牌与当前用户，供路由守卫和侧边栏读取。 */

export interface AuthUser {
  id: number
  username: string
  name: string
  status: string
}

export interface AuthSession {
  token: string
  user: AuthUser
}

const SESSION_KEY = 'netdevtool:session'

export function readSession(): AuthSession | null {
  try {
    const raw = window.localStorage.getItem(SESSION_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw) as AuthSession
    return parsed?.token && parsed?.user ? parsed : null
  } catch {
    return null
  }
}

export function saveSession(session: AuthSession): void {
  window.localStorage.setItem(SESSION_KEY, JSON.stringify(session))
}

export function clearSession(): void {
  window.localStorage.removeItem(SESSION_KEY)
}
