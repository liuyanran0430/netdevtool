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

        const deadline = Date.now() + POLL_TIMEOUT_MS
        const poll = async () => {
          if (run !== runRef.current) return
          try {
            const current = await getTranslation(created.request_id)
            if (run !== runRef.current) return

            if (current.status === 'succeeded') {
              if (!current.result) throw new Error('后端未返回翻译结果')
              setState({
                status: 'succeeded',
                requestId: created.request_id,
                result: current.result,
                error: null,
              })
              return
            }
            if (current.status === 'failed') {
              setState({
                status: 'failed',
                requestId: created.request_id,
                result: null,
                error: current.error ?? '翻译任务执行失败',
              })
              return
            }

            setState({
              status: current.status,
              requestId: created.request_id,
              result: null,
              error: null,
            })
            if (Date.now() >= deadline) {
              setState({
                status: 'failed',
                requestId: created.request_id,
                result: null,
                error: '翻译超时，请稍后重试',
              })
              return
            }
            timerRef.current = window.setTimeout(() => void poll(), POLL_INTERVAL_MS)
          } catch (error) {
            if (run !== runRef.current) return
            setState({
              status: 'failed',
              requestId: created.request_id,
              result: null,
              error: getErrorMessage(error),
            })
          }
        }

        timerRef.current = window.setTimeout(() => void poll(), POLL_INTERVAL_MS)
      } catch (error) {
        if (run !== runRef.current) return
        setState({ ...INITIAL_STATE, status: 'failed', error: getErrorMessage(error) })
      }
    },
    [clearTimer],
  )

  useEffect(
    () => () => {
      runRef.current += 1
      clearTimer()
    },
    [clearTimer],
  )

  return { ...state, submittedSignature, start, reset }
}
