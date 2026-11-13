import { useCallback, useEffect, useRef, useState } from 'react'
import {
  createTranslation,
  getTranslation,
  type TranslationCreateInput,
  type TranslationResult,
  type TranslationStatus,
} from '../api/translations'

const POLL_INTERVAL_MS = 1000
const POLL_TIMEOUT_MS = 60_000

export type TranslationUiStatus = 'idle' | TranslationStatus

interface TranslationTaskState {
  status: TranslationUiStatus
  requestId: string | null
  result: TranslationResult | null
  error: string | null
}

const INITIAL_STATE: TranslationTaskState = {
  status: 'idle',
  requestId: null,
  result: null,
  error: null,
}

function getErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : '翻译任务提交失败，请稍后重试'
}

/** 用于判断当前输入是否与提交翻译时的快照一致。 */
export function translationSignature(input: TranslationCreateInput): string {
  return [
    input.source_text,
    input.source_vendor,
    input.source_model,
    input.target_vendor,
    input.target_model,
  ].join('\u0000')
}

export function useTranslationTask() {
  const [state, setState] = useState<TranslationTaskState>(INITIAL_STATE)
  const [submittedSignature, setSubmittedSignature] = useState<string | null>(null)
  const timerRef = useRef<number | null>(null)
  const runRef = useRef(0)

  const clearTimer = useCallback(() => {
    if (timerRef.current !== null) {
      window.clearTimeout(timerRef.current)
      timerRef.current = null
    }
  }, [])

  const reset = useCallback(() => {
    runRef.current += 1
    clearTimer()
    setSubmittedSignature(null)
    setState(INITIAL_STATE)
  }, [clearTimer])

  /** 轮询任务状态；`silentFailure` 用于恢复历史任务时避免误报错误。 */
  const poll = useCallback(
    (requestId: string, run: number, immediate: boolean, silentFailure: boolean) => {
      const deadline = Date.now() + POLL_TIMEOUT_MS
      let firstAttempt = true

      const tick = async () => {
        if (run !== runRef.current) return
        try {
          const current = await getTranslation(requestId)
          if (run !== runRef.current) return

          if (current.status === 'succeeded') {
            if (!current.result) throw new Error('后端未返回翻译结果')
            setState({
              status: 'succeeded',
              requestId,
              result: current.result,
              error: null,
            })
            return
          }
          if (current.status === 'failed') {
            setState({
              status: 'failed',
              requestId,
              result: null,
              error: current.error ?? '翻译任务执行失败',
            })
            return
          }

          setState({
            status: current.status,
            requestId,
            result: null,
            error: null,
          })
          if (Date.now() >= deadline) {
            setState({
              status: 'failed',
              requestId,
              result: null,
              error: '翻译超时，请稍后重试',
            })
            return
          }
          firstAttempt = false
          timerRef.current = window.setTimeout(() => void tick(), POLL_INTERVAL_MS)
        } catch (error) {
          if (run !== runRef.current) return
          if (silentFailure && firstAttempt) {
            // 恢复的历史任务已被清理：静默回到未生成状态
            setSubmittedSignature(null)
            setState(INITIAL_STATE)
            return
          }
          setState({
            status: 'failed',
            requestId,
            result: null,
            error: getErrorMessage(error),
          })
        }
      }

      if (immediate) void tick()
      else timerRef.current = window.setTimeout(() => void tick(), POLL_INTERVAL_MS)
    },
    [],
  )

  const start = useCallback(
    async (input: TranslationCreateInput) => {
      runRef.current += 1
      const run = runRef.current
      clearTimer()
      setSubmittedSignature(translationSignature(input))
      setState({ ...INITIAL_STATE, status: 'pending' })

      try {
        const created = await createTranslation(input)
        if (run !== runRef.current) return
        setState({
          status: created.status,
          requestId: created.request_id,
          result: null,
          error: null,
        })
        poll(created.request_id, run, false, false)
      } catch (error) {
        if (run !== runRef.current) return
        setState({ ...INITIAL_STATE, status: 'failed', error: getErrorMessage(error) })
      }
    },
    [clearTimer, poll],
  )

  /** 页面重新挂载时，按已保存的 requestId 继续拉取结果。 */
  const resume = useCallback(
    (requestId: string, signature: string) => {
      runRef.current += 1
      const run = runRef.current
      clearTimer()
      setSubmittedSignature(signature)
      setState({ status: 'running', requestId, result: null, error: null })
      poll(requestId, run, true, true)
    },
    [clearTimer, poll],
  )

  useEffect(
    () => () => {
      runRef.current += 1
      clearTimer()
    },
    [clearTimer],
  )

  return { ...state, submittedSignature, start, resume, reset }
}
