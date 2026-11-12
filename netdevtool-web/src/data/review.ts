export interface ReviewCandidate {
  id: string
  vendor: string
  command: string
  source: string
  similarity: string
  confidence: 'low' | 'medium' | 'high'
  candidateVendor: string
  candidateCommand: string
  view: string
  reason: string
  category: string
  revision: string
  checked: boolean
}

export const reviewCandidates: ReviewCandidate[] = [
  {
    id: 'REV-0037',
    vendor: '华为',
    command: 'stp edged-port enable',
    source: 'LLM',
    similarity: '0.82',
    confidence: 'low',
    candidateVendor: '华三',
    candidateCommand: 'stp edged-port',
    view: 'interface',
    reason: '华三同名命令，视图一致（interface）',
    category: 'STP · 生成树',
    revision: 'REV-0037',
    checked: true,
  },
  {
    id: 'REV-0036',
    vendor: '华为',
    command: 'port trunk allow-pass vlan 10 20',
    source: 'LLM',
    similarity: '0.78',
    confidence: 'low',
    candidateVendor: '华三',
    candidateCommand: 'port trunk permit vlan 10 20',
    view: 'interface',
    reason: 'trunk 放行语义一致，需核对 VLAN 参数范围',
    category: 'VLAN · 二层交换',
    revision: 'REV-0036',
    checked: true,
  },
  {
    id: 'REV-0035',
    vendor: '华为',
    command: 'undo info-center enable',
    source: 'LLM',
    similarity: '0.74',
    confidence: 'low',
    candidateVendor: '华三',
    candidateCommand: 'undo info-center enable',
    view: 'system-view',
    reason: '命令名称一致，需确认目标版本的默认行为',
    category: '系统管理 · 日志',
    revision: 'REV-0035',
    checked: false,
  },
]
