import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { readSession } from './auth/session'
import { AppLayout } from './layouts/AppLayout'
import { TranslatePage } from './pages/TranslatePage'
import { ChatPage } from './pages/ChatPage'
import { ReviewPage } from './pages/review'
import { KnowledgeSettingsPage } from './pages/KnowledgeSettingsPage'
import { LoginPage } from './pages/LoginPage'

/** 未登录时跳转登录页，已登录才渲染主框架 */
function RequireAuth() {
  return readSession() ? <AppLayout /> : <Navigate to="/login" replace />
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
