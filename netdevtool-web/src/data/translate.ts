export interface CodePart {
  text: string
  strong?: boolean
}

export interface CodeLine {
  no: number
  parts: CodePart[]
  state?: 'focus' | 'success' | 'warn' | 'error' | 'muted'
  icon?: 'link' | 'warning' | 'error'
  /** 该行参与的全部源配置行号，用于按段联动高亮 */
  sourceNos?: number[] | null
  /** 该行归属的实体；共享视图行只保留最先进入的实体 */
  entityId?: string | null
}
