export interface CodePart {
  text: string
  strong?: boolean
}

export interface CodeLine {
  no: number
  parts: CodePart[]
  state?: 'focus' | 'success' | 'warn' | 'error' | 'muted'
  icon?: 'link' | 'warning' | 'error'
  /** 对应的源配置行号，供点击选中时双向定位 */
  sourceNo?: number | null
}
