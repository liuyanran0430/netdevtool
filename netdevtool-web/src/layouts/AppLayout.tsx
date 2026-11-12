import { useState } from 'react'
import { MenuOutlined } from '@ant-design/icons'
import { Drawer } from 'antd'
import { Outlet } from 'react-router-dom'
import { AppSidebar } from '../components/AppSidebar'

export function AppLayout() {
  const [navOpen, setNavOpen] = useState(false)

  return (
    <div className="flex min-h-screen bg-page">
      <AppSidebar />

      <div className="flex min-h-screen min-w-0 flex-1 flex-col">
        <div className="sticky top-0 z-20 flex h-14 items-center gap-3 border-b border-line bg-white px-4 md:hidden">
          <button
            type="button"
            aria-label="打开导航"
            onClick={() => setNavOpen(true)}
            className="flex h-9 w-9 items-center justify-center rounded-lg border border-line text-[16px] text-ink-700"
          >
            <MenuOutlined />
          </button>
          <span className="text-[15px] font-medium text-ink-900">网络设备配置助手</span>
        </div>

        <main className="min-w-0 flex-1">
          <Outlet />
        </main>
      </div>

      <Drawer
        open={navOpen}
        onClose={() => setNavOpen(false)}
        placement="left"
        size={232}
        closable={false}
        styles={{ body: { padding: 0 } }}
      >
        <AppSidebar variant="drawer" onNavigate={() => setNavOpen(false)} />
      </Drawer>
    </div>
  )
}
