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

const line = (no: number, text: string, rest: Omit<CodeLine, 'no' | 'parts'> = {}): CodeLine => ({
  no,
  parts: [{ text }],
  ...rest,
})

export const sourceLines: CodeLine[] = [
  line(1, 'system-view'),
  line(2, 'vlan 10'),
  {
    no: 3,
    parts: [{ text: '  port ' }, { text: 'default', strong: true }, { text: ' vlan 10' }],
    state: 'focus',
    icon: 'link',
  },
  line(4, '  ...', { state: 'muted' }),
  line(5, '  #', { state: 'muted' }),
  line(6, '  interface GigabitEthernet0/0/1', { state: 'warn', icon: 'warning' }),
  line(7, '  description Office-Access'),
  line(8, '  port link-type access'),
  line(9, '  port default vlan 10'),
  line(10, '  #', { state: 'muted' }),
  line(11, '  interface Vlanif10', { state: 'warn', icon: 'warning' }),
  line(12, '  ip address 192.168.10.1 24'),
  line(13, '  #', { state: 'muted' }),
  line(14, '  stp mode rstp'),
  line(15, '  stp enable'),
  line(16, '  #', { state: 'muted' }),
  line(17, '  snmp-agent', { state: 'warn', icon: 'warning' }),
  line(18, '  ...', { state: 'muted' }),
]
