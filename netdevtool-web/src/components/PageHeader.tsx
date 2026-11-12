import type { ReactNode } from 'react'

interface PageHeaderProps {
  title: string
  subtitle: ReactNode
  right?: ReactNode
}

/** 页面标题栏：白底 80px，底部 1px 分隔线 */
export function PageHeader({ title, subtitle, right }: PageHeaderProps) {
  return (
    <header className="flex min-h-[64px] w-full flex-wrap items-center justify-between gap-4 border-b border-line bg-white px-4 py-4 md:h-20 md:flex-nowrap md:px-7 md:py-0">
      <div className="flex min-w-0 items-center gap-4">
        <h1 className="whitespace-nowrap text-[20px] leading-7 text-ink-900">{title}</h1>
        <span className="hidden h-[18px] w-px bg-line sm:block" />
        <span className="hidden whitespace-nowrap text-xs text-ink-400 sm:block">
          {subtitle}
        </span>
      </div>
      {right ? (
        <div className="ml-auto flex max-w-full flex-wrap items-center justify-end gap-2 md:flex-nowrap md:gap-5">
          {right}
        </div>
      ) : null}
    </header>
  )
}
