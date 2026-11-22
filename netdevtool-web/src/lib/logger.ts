type LogLevel = 'debug' | 'info' | 'warn' | 'error'
type LogField = string | number | boolean | null | undefined
type LogFields = Record<string, LogField>

const MAX_FIELD_LENGTH = 300

function write(level: LogLevel, event: string, fields: LogFields): void {
  const parts = [`event=${event}`]
  for (const [key, value] of Object.entries(fields)) {
    if (value === null || value === undefined) continue
    const text = String(value).replace(/\s+/g, ' ').trim().slice(0, MAX_FIELD_LENGTH)
    parts.push(`${key}=${text}`)
  }
  console[level](parts.join(' '))
}

export const logger = {
  debug(event: string, fields: LogFields = {}): void {
    if (import.meta.env.DEV) write('debug', event, fields)
  },
  info(event: string, fields: LogFields = {}): void {
    if (import.meta.env.DEV) write('info', event, fields)
  },
  warn(event: string, fields: LogFields = {}): void {
    write('warn', event, fields)
  },
  error(event: string, fields: LogFields = {}): void {
    write('error', event, fields)
  },
}

function errorDetails(error: unknown): string {
  if (error instanceof Error) return `${error.name}: ${error.message}`
  return String(error)
}

/** 仅记录未被业务代码处理的异常；页面已处理的错误仍由页面负责提示。 */
export function installGlobalErrorLogging(): void {
  window.addEventListener('error', (event) => {
    logger.error('frontend.unhandled_error', {
      route: window.location.pathname,
      error: errorDetails(event.error ?? event.message),
    })
  })
  window.addEventListener('unhandledrejection', (event) => {
    logger.error('frontend.unhandled_rejection', {
      route: window.location.pathname,
      error: errorDetails(event.reason),
    })
  })
}
