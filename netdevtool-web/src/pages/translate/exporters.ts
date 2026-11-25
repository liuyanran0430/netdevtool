/** 翻译结果导出：.cfg 配置与复核报告的纯文本生成与下载。 */

import type { TranslationResultLines } from '../../api/translations'

export type ExportFormat = 'cfg' | 'report'

const pad2 = (value: number) => String(value).padStart(2, '0')

function exportTimeLabel(date: Date) {
  return `${date.getFullYear()}-${pad2(date.getMonth() + 1)}-${pad2(date.getDate())} ${pad2(date.getHours())}:${pad2(date.getMinutes())}`
}

export function exportStamp(date: Date) {
  return `${date.getFullYear()}${pad2(date.getMonth() + 1)}${pad2(date.getDate())}-${pad2(date.getHours())}${pad2(date.getMinutes())}`
}

export function safeFileNamePart(value: string) {
  return value.replace(/[\\/:*?"<>|\s]+/g, '-') || '未选择'
}

export function downloadText(content: string, fileName: string, withBom = false) {
  const blob = new Blob([withBom ? `\uFEFF${content}` : content], {
    type: 'text/plain;charset=utf-8',
  })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = fileName
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

export function buildCfgText(lines: TranslationResultLines[]) {
  // 仅输出命令本身，便于直接回灌设备；Windows 习惯使用 CRLF
  return `${lines.map((line) => line.text).join('\r\n')}\r\n`
}

export function buildReviewReport(
  lines: TranslationResultLines[],
  meta: { generatedAt: Date; source: string; target: string; stale: boolean },
) {
  const warnCount = lines.filter((line) => line.tone === 'warn').length
  const errorCount = lines.filter((line) => line.tone === 'error').length
  const header = [
    '# 配置翻译复核报告',
    `# 生成时间：${exportTimeLabel(meta.generatedAt)}`,
    `# 设备：${meta.source} → ${meta.target}`,
    `# 统计：共 ${lines.length} 行，需复核 ${warnCount} 行（warn），需人工处理 ${errorCount} 行（error）`,
    ...(meta.stale ? ['# 注意：翻译结果已过期，内容基于修改前的源配置'] : []),
    '# 说明：行尾 [需复核] / [需人工处理] 标记仅用于评审，下发前请确认',
    '# --------------------------------------------------',
  ]
  const body = lines.map((line) => {
    const mark =
      line.tone === 'error' ? '[需人工处理]' : line.tone === 'warn' ? '[需复核]' : ''
    if (!mark) return line.text
    return `${line.text}  # ${mark}`
  })
  return `${[...header, ...body].join('\r\n')}\r\n`
}
