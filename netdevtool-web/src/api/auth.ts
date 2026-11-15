import type { AuthSession, AuthUser } from '../auth/session'
import { API_BASE, toRequestError } from './client'

export async function login(username: string, password: string): Promise<AuthSession> {
  const response = await fetch(`${API_BASE}/api/v1/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })
  if (!response.ok) throw await toRequestError(response, '登录失败')
  return (await response.json()) as AuthSession
}

export async function fetchMe(token: string): Promise<AuthUser> {
  const response = await fetch(`${API_BASE}/api/v1/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!response.ok) throw await toRequestError(response, '获取登录用户失败')
  return (await response.json()) as AuthUser
}

export async function logout(token: string): Promise<void> {
  await fetch(`${API_BASE}/api/v1/auth/logout`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  })
}
