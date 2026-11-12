import type { ReactNode } from 'react'
import {
  AuditOutlined,
  BookOutlined,
  DeploymentUnitOutlined,
  MessageOutlined,
  TranslationOutlined,
} from '@ant-design/icons'
import { NavLink } from 'react-router-dom'

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
        <div className="mt-auto flex items-center gap-3 border-t border-line pt-4">
          <span className="flex h-8 w-8 items-center justify-center rounded-full bg-[#DDE6F4] text-[12px] font-bold text-[#526B93]">
            运维
          </span>
          <span className="text-[13px] text-ink-500">运维账号</span>
        </div>
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

      <div className="flex h-[34px] w-[34px] items-center justify-center rounded-full bg-[#DDE6F4] text-[12px] font-bold text-[#526B93]">
        运维
      </div>
    </aside>
  )
}
