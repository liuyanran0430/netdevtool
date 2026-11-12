import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AppLayout } from './layouts/AppLayout'
import { TranslatePage } from './pages/TranslatePage'
import { ChatPage } from './pages/ChatPage'
import { ReviewPage } from './pages/ReviewPage'
import { KnowledgeSettingsPage } from './pages/KnowledgeSettingsPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
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
