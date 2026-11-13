import { API_BASE, toRequestError } from './client'

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
  const response = await fetch(`${API_BASE}/api/v1/devices`)
  if (!response.ok) throw await toRequestError(response, '加载设备失败')
  return (await response.json()) as Device[]
}
