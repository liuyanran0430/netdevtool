export interface CodePart {
  text: string
  strong?: boolean
}

export interface CodeLine {
  no: number
  parts: CodePart[]
  state?: 'focus' | 'success' | 'warn' | 'muted'
  icon?: 'link' | 'warning'
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

export const targetLines: CodeLine[] = [
  line(1, 'system-view'),
  line(2, 'vlan 10'),
  {
    no: 3,
    parts: [{ text: '  port ' }, { text: 'access', strong: true }, { text: ' vlan 10' }],
    state: 'focus',
    icon: 'link',
  },
  line(4, '  ...', { state: 'muted' }),
  line(5, '  #', { state: 'muted' }),
  line(6, '  interface GigabitEthernet1/0/1', { state: 'warn', icon: 'warning' }),
  line(7, '  description Office-Access'),
  line(8, '  port link-type access'),
  line(9, '  port access vlan 10', { state: 'success' }),
  line(10, '  #', { state: 'muted' }),
  line(11, '  interface Vlan-interface10', { state: 'warn', icon: 'warning' }),
  line(12, '  ip address 192.168.10.1 24'),
  line(13, '  #', { state: 'muted' }),
  line(14, '  stp mode rstp'),
  line(15, '  stp global enable', { state: 'success' }),
  line(16, '  #', { state: 'muted' }),
  line(17, '  # snmp-agent: review required', { state: 'warn', icon: 'warning' }),
  line(18, '  ...', { state: 'muted' }),
]

export const auditWarnings = [
  {
    key: 'interface-name',
    title: '接口命名不一致',
    meta: 'L6 · GE0/0/1 → GE1/0/1',
    tone: 'warn' as const,
    active: false,
  },
  {
    key: 'vlan-default',
    title: 'VLAN 默认行为差异',
    meta: 'L3、L9 · 请确认 access 模式',
    tone: 'warn' as const,
    active: true,
  },
  {
    key: 'stp-scope',
    title: '生成树启用范围变化',
    meta: 'L15 · 已转换为全局启用',
    tone: 'warn' as const,
    active: false,
  },
  {
    key: 'snmp',
    title: 'SNMP 参数不支持',
    meta: 'L17 · 需在目标设备手动配置',
    tone: 'danger' as const,
    active: false,
  },
]

export const translateMeta = {
  source: { type: '交换机', vendor: '华为', model: 'CE5800' },
  target: { type: '交换机', vendor: '华三', model: 'L002' },
  total: 42,
  duration: '1.2 s',
}
