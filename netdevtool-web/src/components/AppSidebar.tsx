import { useState } from 'react'
import type { ReactNode } from 'react'
import {
  AuditOutlined,
  BookOutlined,
  DeploymentUnitOutlined,
  LogoutOutlined,
  MessageOutlined,
  TranslationOutlined,
} from '@ant-design/icons'
import { Popover } from 'antd'
import { NavLink, useNavigate } from 'react-router-dom'
import { logout } from '../api/auth'
import { clearSession, readSession } from '../auth/session'

interface NavItem {
  to: string
  label: string
  icon: ReactNode
}

const workNav: NavItem[] = [
  { to: '/translate', label: '翻译', icon: <TranslationOutlined /> },
  { to: '/chat', label: '问答', icon: <MessageOutlined /> },
  { to: '/knowledge', label: '知识', icon: <BookOutlined /> },
  { to: '/review', label: '审核', icon: <AuditOutlined /> },
]

function BrandMark() {
  return (
    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand text-[20px] text-white">
      <DeploymentUnitOutlined />
    </div>
  )
}

interface SidebarProps {
  variant?: 'desktop' | 'drawer'
  onNavigate?: () => void
}

/** 全局导航：桌面端 84px 竖栏，移动端以抽屉形式折叠 */
export function AppSidebar({ variant = 'desktop', onNavigate }: SidebarProps) {
  const navigate = useNavigate()
  const [loggingOut, setLoggingOut] = useState(false)
  const displayName = readSession()?.user.name ?? '未登录'
  const username = readSession()?.user.username ?? ''
  const initial = Array.from(displayName)[0] ?? '?'

  async function handleLogout() {
    if (loggingOut) return
    setLoggingOut(true)
    const token = readSession()?.token
    try {
      if (token) await logout(token)
    } catch {
      // 后端不可用时也要允许本地退出
    }
    clearSession()
    navigate('/login', { replace: true })
  }

  const userMenu = (
    <div className="w-[184px] overflow-hidden">
      <div className="flex items-center gap-2.5 px-3 py-3">
        <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-brand-soft text-[13px] font-bold text-brand">
          {initial}
        </span>
        <div className="min-w-0">
          <p className="truncate text-[13px] font-medium leading-tight text-ink-900">
            {displayName}
          </p>
          {username ? (
            <p className="mt-0.5 truncate text-[11px] leading-none text-ink-400">@{username}</p>
          ) : null}
        </div>
      </div>
      <div className="h-px bg-line" />
      <button
        type="button"
        disabled={loggingOut}
        onClick={() => {
          void handleLogout()
        }}
        className="flex w-full items-center gap-2 px-3 py-2.5 text-[12px] text-ink-700 transition-colors hover:bg-danger-soft hover:text-danger disabled:cursor-not-allowed disabled:opacity-60"
      >
        <LogoutOutlined />
        {loggingOut ? '正在退出…' : '退出登录'}
      </button>
    </div>
  )

  const userMenuProps = {
    trigger: 'click' as const,
    arrow: false,
    content: userMenu,
    styles: {
      container: {
        padding: 0,
        borderRadius: 12,
        overflow: 'hidden',
        boxShadow: '0 10px 30px rgba(32, 44, 64, 0.12)',
      },
    },
  }

  if (variant === 'drawer') {
    return (
      <div className="flex h-full flex-col bg-white px-3 py-5">
        <div className="flex items-center gap-3 px-2 pb-5">
          <BrandMark />
          <div className="leading-tight">
            <p className="text-[14px] font-bold text-ink-900">网络设备配置助手</p>
            <p className="mt-1 text-[11px] text-ink-400">NetDev Tool</p>
          </div>
        </div>
        <nav className="flex flex-col gap-1">
          {workNav.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={onNavigate}
              className={({ isActive }) =>
                `flex h-11 items-center gap-3 rounded-lg px-3 text-[13px] ${
                  isActive
                    ? 'bg-brand-soft font-bold text-brand'
                    : 'text-ink-500 hover:bg-soft'
                }`
              }
            >
              <span className="text-[18px]">{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>
        <Popover {...userMenuProps} placement="topLeft">
          <button
            type="button"
            title={displayName}
            className="mt-auto flex w-full items-center gap-3 rounded-lg border-t border-line px-1 pt-4 pb-1 text-left hover:bg-soft"
          >
            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#DDE6F4] text-[13px] font-bold text-[#526B93]">
              {initial}
            </span>
            <span className="truncate text-[13px] text-ink-700">{displayName}</span>
          </button>
        </Popover>
      </div>
    )
  }

  return (
    <aside className="sticky top-0 hidden h-screen w-[84px] shrink-0 flex-col items-center gap-[26px] border-r border-line bg-nav px-3 py-[22px] md:flex">
      <BrandMark />

      <nav className="flex flex-col items-center gap-[10px]">
        {workNav.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `relative flex h-16 w-[60px] flex-col items-center justify-center gap-[5px] rounded-xl text-[12px] transition-colors ${
                isActive
                  ? 'bg-brand-soft font-bold text-brand'
                  : 'text-ink-500 hover:bg-white'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <span className="text-[22px] leading-none">{item.icon}</span>
                <span className="leading-none">{item.label}</span>
                {isActive ? (
                  <span className="absolute left-0 top-[24px] h-[18px] w-[3px] rounded-r bg-brand" />
                ) : null}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="flex-1" />

      <Popover {...userMenuProps} placement="top">
        <button
          type="button"
          title={displayName}
          aria-label="用户菜单"
          className="rounded-full transition-shadow hover:ring-2 hover:ring-brand-line"
        >
          <span className="flex h-[40px] w-[40px] items-center justify-center rounded-full bg-[#DDE6F4] text-[15px] font-bold text-[#526B93]">
            {initial}
          </span>
        </button>
      </Popover>
    </aside>
  )
}
