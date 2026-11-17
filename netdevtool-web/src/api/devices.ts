import { API_BASE, authHeaders, toRequestError } from './client'

const DEVICE_TYPE_LABELS: Record<string, string> = {
  switch: '交换机',
  firewall: '防火墙',
}

export interface Device {
  id: number
  vendor: string
  vendor_en: string | null
  model: string
  device_type: string
}

export function deviceTypeLabel(type: string): string {
  return DEVICE_TYPE_LABELS[type] ?? type
}

/** 一次拉取设备全量；设备表规模增大后应改回按 device_type / vendor 过滤 */
export async function fetchDevices(): Promise<Device[]> {
  const response = await fetch(`${API_BASE}/api/v1/devices`, { headers: authHeaders() })
  if (!response.ok) throw await toRequestError(response, '加载设备失败')
  return (await response.json()) as Device[]
}

/**
 * 打开设备手册：外部链接直接新开标签页，本地 PDF 以 blob 方式新开。
 * 本地文件走鉴权请求，避免把知识库目录暴露为公开静态资源。
 */
export async function openDeviceManual(vendor: string, model: string): Promise<void> {
  const params = new URLSearchParams({ vendor, model })
  const response = await fetch(`${API_BASE}/api/v1/devices/manual?${params}`, {
    headers: authHeaders(),
  })
  if (!response.ok) throw await toRequestError(response, '打开手册失败')

  const contentType = response.headers.get('content-type') ?? ''
  if (contentType.includes('application/json')) {
    const body = (await response.json()) as { kind: string; url: string }
    window.open(body.url, '_blank', 'noopener,noreferrer')
    return
  }

  const blobUrl = URL.createObjectURL(await response.blob())
  const opened = window.open(blobUrl, '_blank')
  if (!opened) {
    URL.revokeObjectURL(blobUrl)
    throw new Error('浏览器阻止了新标签页，请允许本站弹出窗口')
  }
  // 延迟释放，避免新标签页尚未读取完 blob
  window.setTimeout(() => URL.revokeObjectURL(blobUrl), 60_000)
}
