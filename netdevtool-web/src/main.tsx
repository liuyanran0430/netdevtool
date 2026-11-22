import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import './index.css'
import App from './App'
import { installGlobalErrorLogging } from './lib/logger'
import { appTheme } from './theme'

installGlobalErrorLogging()

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ConfigProvider theme={appTheme} locale={zhCN}>
      <App />
    </ConfigProvider>
  </StrictMode>,
)
