import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { clearSession, readSession } from './auth/session'
import { API_BASE, authHeaders } from './api/client'
import { AppLayout } from './layouts/AppLayout'
import { TranslatePage } from './pages/TranslatePage'
import { ChatPage } from './pages/ChatPage'
import { ReviewPage } from './pages/review'
import { KnowledgeSettingsPage } from './pages/KnowledgeSettingsPage'
import { LoginPage } from './pages/LoginPage'

type AuthState = 'checking' | 'authenticated' | 'unauthenticated'

/** 启动时异步验证 token 有效性，避免先渲染工具页再跳登录页的闪烁。 */
function RequireAuth() {
  const [state, setState] = useState<AuthState>('checking')

  useEffect(() => {
    const session = readSession()
    if (!session) {
      setState('unauthenticated')
      return
    }
    let cancelled = false
    fetch(`${API_BASE}/api/v1/auth/me`, { headers: authHeaders() })
      .then((response) => {
        if (cancelled) return
        if (response.ok) {
          setState('authenticated')
        } else if (response.status === 401) {
          clearSession()
          setState('unauthenticated')
        } else {
          // 网络错误等：仍尝试进入，由业务接口处理 401
          setState('authenticated')
        }
      })
      .catch(() => {
        if (!cancelled) setState('authenticated')
      })
    return () => {
      cancelled = true
    }
  }, [])

  if (state === 'checking') {
    return (
      <div className="flex h-screen items-center justify-center bg-[#f6f8fa]">
        <div className="text-[13px] text-[#999]">正在验证登录状态…</div>
      </div>
    )
  }
  if (state === 'unauthenticated') {
    return <Navigate to="/login" replace />
  }
  return <AppLayout />
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route element={<RequireAuth />}>
          <Route index element={<Navigate to="/translate" replace />} />
          <Route path="/translate" element={<TranslatePage />} />
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/knowledge" element={<KnowledgeSettingsPage />} />
          <Route path="/review" element={<ReviewPage />} />
          <Route path="*" element={<Navigate to="/translate" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
