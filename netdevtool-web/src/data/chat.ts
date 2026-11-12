export const chatSessions = [
  { id: 'vlan', title: 'VLAN 间不通', time: '昨天', active: true, tag: '故障排查' },
  { id: 'trunk', title: 'trunk 放行', time: '昨天', active: false, tag: '配置问答' },
  { id: 'port', title: 'port default vlan 命令', time: '3天前', active: false, tag: '命令检索' },
]

export const probableCauses = [
  { percent: '80%', width: 59, text: '三层接口未配置 / 未 up' },
  { percent: '60%', width: 44, text: 'trunk 未放行 VLAN' },
]

export const diagnosticSteps = [
  { id: 1, text: '确认 VLAN 已创建，接入口归属正确', command: 'display vlan', done: true },
  { id: 2, text: '检查 Vlanif 接口 IP 与 up 状态', command: 'display ip interface brief', done: false },
  { id: 3, text: '检查 trunk 链路是否放行目标 VLAN', command: 'display port vlan', done: false },
  { id: 4, text: '核对终端网关，并测试跨 VLAN 连通性', command: 'ping -a <源IP> <目的IP>', done: false },
]

export const questionModes = [
  { id: 'command', label: '命令检索' },
  { id: 'troubleshoot', label: '故障排查' },
  { id: 'knowledge', label: '知识提问' },
]
