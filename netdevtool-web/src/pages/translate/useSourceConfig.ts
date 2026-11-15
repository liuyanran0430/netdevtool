/** 源配置编辑状态：导入校验、暂存持久化与保存状态提示。 */

import { useEffect, useMemo, useState } from 'react'
import { message } from 'antd'
import { readSourceCache, writeSourceCache } from './storage'

export const SOURCE_ACCEPT_EXTENSIONS = ['.txt', '.cfg', '.log']
const SOURCE_MAX_BYTES = 2 * 1024 * 1024 // 2MB

export function useSourceConfig() {
  const cached = useMemo(() => readSourceCache(), [])
  const [text, setText] = useState<string>(cached?.text ?? '')
  const [fileName, setFileName] = useState<string>(cached?.fileName ?? '')
  // 源配置暂存状态：空内容 / 已保存 / 保存失败
  const [saveState, setSaveState] = useState<'empty' | 'saved' | 'failed'>('empty')

  useEffect(() => {
    const saved = writeSourceCache(text, fileName)
    if (!text.trim()) setSaveState('empty')
    else setSaveState(saved ? 'saved' : 'failed')
  }, [text, fileName])

  const importFile = (file: File) => {
    const lower = file.name.toLowerCase()
    if (!SOURCE_ACCEPT_EXTENSIONS.some((ext) => lower.endsWith(ext))) {
      message.error(`仅支持 ${SOURCE_ACCEPT_EXTENSIONS.join(' / ')} 格式`)
      return
    }
    if (file.size > SOURCE_MAX_BYTES) {
      message.error('文件超过 2MB 上限')
      return
    }
    const reader = new FileReader()
    reader.onload = () => {
      const content = typeof reader.result === 'string' ? reader.result : ''
      if (!content.trim()) {
        message.error('文件内容为空')
        return
      }
      setText(content)
      setFileName(file.name)
      message.success(`已导入 ${file.name}`)
    }
    reader.onerror = () => {
      message.error('文件读取失败，请重试')
    }
    reader.readAsText(file, 'utf-8')
  }

  const clear = () => {
    setText('')
    setFileName('')
  }

  return { text, fileName, setText, importFile, clear, saveState }
}
