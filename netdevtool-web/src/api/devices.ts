const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8083'

const DEVICE_TYPE_LABELS: Record<string, string> = {
  switch: '交换机',
  firewall: '防火墙',
}

interface Device {
  id: number
  vendor: string
  model: string
  device_type: string
}

export function deviceTypeLabel(type: string): string {
  return DEVICE_TYPE_LABELS[type] ?? type
}

async function fetchDevices(query: { device_type?: string; vendor?: string }): Promise<Device[]> {
  const params = new URLSearchParams()
  if (query.device_type) params.set('device_type', query.device_type)
  if (query.vendor) params.set('vendor', query.vendor)

  const suffix = params.toString() ? `?${params.toString()}` : ''
  const resp = await fetch(`${API_BASE}/api/v1/devices${suffix}`)
  if (!resp.ok) {
    throw new Error(`加载设备失败：${resp.status}`)
  }
  return (await resp.json()) as Device[]
}

export async function fetchDeviceTypes(): Promise<string[]> {
  const resp = await fetch(`${API_BASE}/api/v1/devices/types`)
  if (!resp.ok) {
    throw new Error(`加载设备类型失败：${resp.status}`)
  }
  return (await resp.json()) as string[]
}

export async function fetchVendors(deviceType: string): Promise<string[]> {
  const devices = await fetchDevices({ device_type: deviceType })
  return [...new Set(devices.map((device) => device.vendor))]
}

export async function fetchModels(vendor: string, deviceType: string): Promise<string[]> {
  const devices = await fetchDevices({ vendor, device_type: deviceType })
  return [...new Set(devices.map((device) => device.model))]
}
