import Markdown from 'react-markdown'
import type { Components } from 'react-markdown'
import remarkGfm from 'remark-gfm'

/** 问答回答：紧凑排版，避免标题与代码块撑高消息气泡 */
const answerComponents: Components = {
  h1: ({ children }) => (
    <p className="mb-1.5 mt-3 text-[14px] font-bold text-ink-900">{children}</p>
  ),
  h2: ({ children }) => (
    <p className="mb-1.5 mt-3 text-[14px] font-bold text-ink-900">{children}</p>
  ),
  h3: ({ children }) => (
    <p className="mb-1 mt-2.5 text-[13px] font-bold text-ink-900">{children}</p>
  ),
  h4: ({ children }) => (
    <p className="mb-1 mt-2 text-[13px] font-semibold text-ink-900">{children}</p>
  ),
  p: ({ children }) => (
    <p className="my-1.5 text-[14px] leading-[1.7] text-ink-900">{children}</p>
  ),
  ul: ({ children }) => (
    <ul className="my-1.5 list-disc space-y-1 pl-5">{children}</ul>
  ),
  ol: ({ children }) => (
    <ol className="my-1.5 list-decimal space-y-1 pl-5">{children}</ol>
  ),
  li: ({ children }) => (
    <li className="text-[13.5px] leading-[1.65] text-ink-900">{children}</li>
  ),
  pre: ({ children }) => (
    <pre className="thin-scrollbar my-2 overflow-x-auto rounded-lg border border-line bg-[#F7F9FC] px-3 py-2 font-mono text-[12px] leading-[1.6] text-ink-900">
      {children}
    </pre>
  ),
  code: ({ className, children }) => {
    const text = String(children ?? '')
    const block = Boolean(className?.includes('language-')) || text.includes('\n')
    if (block) return <code className="font-mono">{children}</code>
    return (
      <code className="rounded bg-[#F5F6F8] px-1 py-0.5 font-mono text-[12px] text-brand-strong">
        {children}
      </code>
    )
  },
  table: ({ children }) => (
    <div className="thin-scrollbar my-2 overflow-x-auto">
      <table className="w-full border-collapse text-[12px]">{children}</table>
    </div>
  ),
  th: ({ children }) => (
    <th className="border border-line bg-[#F7F9FC] px-2 py-1 text-left font-semibold text-ink-700">
      {children}
    </th>
  ),
  td: ({ children }) => (
    <td className="border border-line px-2 py-1 align-top leading-[1.6] text-ink-700">
      {children}
    </td>
  ),
  blockquote: ({ children }) => (
    <blockquote className="my-2 border-l-2 border-brand-line pl-3 text-ink-500">
      {children}
    </blockquote>
  ),
  strong: ({ children }) => (
    <strong className="font-semibold text-ink-900">{children}</strong>
  ),
  hr: () => <hr className="my-3 border-line" />,
}

/** 配置说明：阅读型排版，带锚点色与表格斑马纹 */
const guideComponents: Components = {
  // 抽屉标题已展示文档名称，正文不再重复一级标题
  h1: () => null,
  h2: ({ children }) => (
    <h2 className="mb-3 mt-7 flex items-center gap-2 text-[16px] font-semibold leading-6 text-ink-900">
      <span className="h-4 w-[3px] shrink-0 rounded-full bg-brand" />
      {children}
    </h2>
  ),
  h3: ({ children }) => (
    <h3 className="mb-2 mt-5 border-l-2 border-brand-line pl-2.5 text-[14px] font-semibold leading-6 text-ink-900">
      {children}
    </h3>
  ),
  h4: ({ children }) => (
    <h4 className="mb-2 mt-3 text-[13px] font-semibold leading-6 text-ink-700">
      {children}
    </h4>
  ),
  p: ({ children }) => (
    <p className="my-2.5 text-[13px] leading-[26px] text-ink-700">{children}</p>
  ),
  strong: ({ children }) => (
    <strong className="font-semibold text-ink-900">{children}</strong>
  ),
  a: ({ children, href }) => (
    <a
      href={href}
      target="_blank"
      rel="noreferrer"
      className="text-brand underline decoration-brand-line underline-offset-2 hover:text-brand-strong"
    >
      {children}
    </a>
  ),
  ul: ({ children }) => (
    <ul className="my-3 list-disc space-y-1.5 pl-5 text-[13px] leading-[26px] text-ink-700 marker:text-brand">
      {children}
    </ul>
  ),
  ol: ({ children }) => (
    <ol className="my-3 list-decimal space-y-1.5 pl-5 text-[13px] leading-[26px] text-ink-700 marker:font-medium marker:text-brand">
      {children}
    </ol>
  ),
  li: ({ children }) => (
    <li className="pl-0.5 [&_p]:my-0 [&_p]:leading-[26px]">{children}</li>
  ),
  blockquote: ({ children }) => (
    <blockquote className="my-4 rounded-lg border border-brand-line bg-brand-soft/50 px-4 py-2.5 text-[13px] leading-[26px] text-ink-500 [&_p]:my-0 [&_p]:leading-[26px]">
      {children}
    </blockquote>
  ),
  code: ({ children, className }) => (
    <code
      className={
        className
          ? 'font-mono text-[12px] text-ink-700'
          : 'rounded border border-[#DCE7FB] bg-[#F2F6FE] px-1.5 py-0.5 font-mono text-[12px] text-code-blue'
      }
    >
      {children}
    </code>
  ),
  pre: ({ children }) => (
    <pre className="my-4 overflow-x-auto rounded-lg border border-line bg-soft p-4 font-mono text-[12px] leading-[22px] text-ink-700">
      {children}
    </pre>
  ),
  table: ({ children }) => (
    <div className="my-4 overflow-x-auto rounded-lg border border-line shadow-panel">
      <table className="w-full border-collapse text-[13px] text-ink-700">
        {children}
      </table>
    </div>
  ),
  thead: ({ children }) => (
    <thead className="bg-[#F4F7FE] text-ink-900">{children}</thead>
  ),
  tbody: ({ children }) => (
    <tbody className="[&>tr:hover]:bg-brand-soft/40 [&>tr:nth-child(even)]:bg-soft [&>tr:last-child>td]:border-b-0">
      {children}
    </tbody>
  ),
  th: ({ children }) => (
    <th className="whitespace-nowrap border-b border-line px-4 py-2.5 text-left text-[12px] font-semibold">
      {children}
    </th>
  ),
  td: ({ children }) => (
    <td className="border-b border-line-soft px-4 py-2.5 align-top leading-[24px]">
      {children}
    </td>
  ),
  hr: () => <hr className="my-7 h-px border-0 bg-line" />,
}

const variants: Record<MarkdownVariant, { components: Components; className: string }> = {
  answer: {
    components: answerComponents,
    className:
      'text-[14px] leading-[1.7] text-ink-900 [&>*:first-child]:mt-0 [&>*:last-child]:mb-0',
  },
  guide: { components: guideComponents, className: '' },
}

export type MarkdownVariant = 'answer' | 'guide'

export function MarkdownContent({
  content,
  variant = 'answer',
}: {
  content: string
  variant?: MarkdownVariant
}) {
  const config = variants[variant]
  return (
    <div className={config.className}>
      <Markdown remarkPlugins={[remarkGfm]} components={config.components}>
        {content}
      </Markdown>
    </div>
  )
}
