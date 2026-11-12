import type { ReactNode } from 'react'

type Tone = 'blue' | 'green' | 'warn' | 'red' | 'gray'

const toneClass: Record<Tone, string> = {
  blue: 'bg-brand-soft text-brand-strong',
  green: 'bg-success-soft text-success',
  warn: 'bg-warn-soft text-warn',
  red: 'bg-danger-soft text-danger',
  gray: 'bg-[#F1F4F9] text-ink-500',
}

interface StatusTagProps {
  tone?: Tone
  children: ReactNode
  className?: string
}

/** 面板标题右侧的状态标签，规格来自设计稿：10px / 20px 高 / 4px 圆角 */
export function StatusTag({ tone = 'blue', children, className = '' }: StatusTagProps) {
  return (
    <span
      className={`inline-flex h-5 items-center rounded px-1.5 text-[10px] font-normal leading-none ${toneClass[tone]} ${className}`}
    >
      {children}
    </span>
  )
}
