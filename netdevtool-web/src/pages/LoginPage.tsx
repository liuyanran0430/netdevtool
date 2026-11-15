import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { login } from '../api/auth'
import { readSession, saveSession } from '../auth/session'

const TOPOLOGY_BG =
  "url(\"data:image/svg+xml,%3Csvg width='100%25' height='100%25' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' stroke='%232563eb' stroke-opacity='0.06' stroke-width='1'%3E%3Ccircle cx='10%25' cy='20%25' r='3' fill='%232563eb' fill-opacity='0.08'/%3E%3Ccircle cx='30%25' cy='15%25' r='2' fill='%232563eb' fill-opacity='0.06'/%3E%3Ccircle cx='50%25' cy='10%25' r='4' fill='%232563eb' fill-opacity='0.1'/%3E%3Ccircle cx='70%25' cy='25%25' r='2.5' fill='%232563eb' fill-opacity='0.07'/%3E%3Ccircle cx='90%25' cy='18%25' r='3' fill='%232563eb' fill-opacity='0.08'/%3E%3Ccircle cx='15%25' cy='50%25' r='2' fill='%232563eb' fill-opacity='0.06'/%3E%3Ccircle cx='35%25' cy='60%25' r='3.5' fill='%232563eb' fill-opacity='0.09'/%3E%3Ccircle cx='55%25' cy='45%25' r='2' fill='%232563eb' fill-opacity='0.06'/%3E%3Ccircle cx='75%25' cy='70%25' r='4' fill='%232563eb' fill-opacity='0.1'/%3E%3Ccircle cx='95%25' cy='55%25' r='2.5' fill='%232563eb' fill-opacity='0.07'/%3E%3Ccircle cx='5%25' cy='80%25' r='3' fill='%232563eb' fill-opacity='0.08'/%3E%3Ccircle cx='25%25' cy='85%25' r='2' fill='%232563eb' fill-opacity='0.06'/%3E%3Ccircle cx='45%25' cy='90%25' r='3.5' fill='%232563eb' fill-opacity='0.09'/%3E%3Ccircle cx='65%25' cy='80%25' r='2' fill='%232563eb' fill-opacity='0.06'/%3E%3Ccircle cx='85%25' cy='88%25' r='4' fill='%232563eb' fill-opacity='0.1'/%3E%3Ccircle cx='20%25' cy='35%25' r='2.5' fill='%232563eb' fill-opacity='0.07'/%3E%3Ccircle cx='80%25' cy='40%25' r='3' fill='%232563eb' fill-opacity='0.08'/%3E%3Cline x1='10%25' y1='20%25' x2='30%25' y2='15%25' /%3E%3Cline x1='30%25' y1='15%25' x2='50%25' y2='10%25' /%3E%3Cline x1='50%25' y1='10%25' x2='70%25' y2='25%25' /%3E%3Cline x1='70%25' y1='25%25' x2='90%25' y2='18%25' /%3E%3Cline x1='10%25' y1='20%25' x2='15%25' y2='50%25' /%3E%3Cline x1='30%25' y1='15%25' x2='35%25' y2='60%25' /%3E%3Cline x1='50%25' y1='10%25' x2='55%25' y2='45%25' /%3E%3Cline x1='70%25' y1='25%25' x2='75%25' y2='70%25' /%3E%3Cline x1='90%25' y1='18%25' x2='95%25' y2='55%25' /%3E%3Cline x1='15%25' y1='50%25' x2='35%25' y2='60%25' /%3E%3Cline x1='35%25' y1='60%25' x2='55%25' y2='45%25' /%3E%3Cline x1='55%25' y1='45%25' x2='75%25' y2='70%25' /%3E%3Cline x1='75%25' y1='70%25' x2='95%25' y2='55%25' /%3E%3Cline x1='15%25' y1='50%25' x2='5%25' y2='80%25' /%3E%3Cline x1='35%25' y1='60%25' x2='25%25' y2='85%25' /%3E%3Cline x1='55%25' y1='45%25' x2='45%25' y2='90%25' /%3E%3Cline x1='75%25' y1='70%25' x2='65%25' y2='80%25' /%3E%3Cline x1='95%25' y1='55%25' x2='85%25' y2='88%25' /%3E%3Cline x1='5%25' y1='80%25' x2='25%25' y2='85%25' /%3E%3Cline x1='25%25' y1='85%25' x2='45%25' y2='90%25' /%3E%3Cline x1='45%25' y1='90%25' x2='65%25' y2='80%25' /%3E%3Cline x1='65%25' y1='80%25' x2='85%25' y2='88%25' /%3E%3Cline x1='20%25' y1='35%25' x2='10%25' y2='20%25' /%3E%3Cline x1='20%25' y1='35%25' x2='35%25' y2='60%25' /%3E%3Cline x1='80%25' y1='40%25' x2='70%25' y2='25%25' /%3E%3Cline x1='80%25' y1='40%25' x2='75%25' y2='70%25' /%3E%3C/g%3E%3C/svg%3E\")"

const FEATURES = [
  { title: '跨厂商配置翻译', desc: '支持华为、华三等数据中心交换机和防火墙设备' },
  { title: '网络知识问答', desc: '网络设备命令检索、常见故障排查与网络知识问答' },
  { title: '审计与知识沉淀', desc: '知识库制作，支持配置命令修订并沉淀经验' },
]

/** 登录页：左侧品牌介绍，右侧账号密码表单 */
export function LoginPage() {
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (readSession()) navigate('/translate', { replace: true })
  }, [navigate])

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (submitting) return
    if (!username.trim() || !password) {
      setError('请输入用户名和密码')
      return
    }

    setSubmitting(true)
    setError(null)
    try {
      const session = await login(username.trim(), password)
      saveSession(session)
      navigate('/translate', { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : '登录失败，请稍后重试')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="relative min-h-screen overflow-x-hidden bg-gradient-to-br from-[#EFF5FF] via-white to-slate-50 text-ink-900">
      <style>{`
        @keyframes loginFadeIn { from { opacity: .95; transform: translateY(12px) } to { opacity: 1; transform: translateY(0) } }
        @keyframes loginFloat { 0%, 100% { transform: translateY(0) } 50% { transform: translateY(-8px) } }
        .login-fade-in { animation: loginFadeIn .6s cubic-bezier(.2,.8,.2,1) both }
        .login-float { animation: loginFloat 8s ease-in-out infinite }
      `}</style>

      <div
        aria-hidden
        className="pointer-events-none fixed inset-0 z-0 bg-[length:100%_100%] opacity-80"
        style={{ backgroundImage: TOPOLOGY_BG }}
      />
      <div
        aria-hidden
        className="login-float pointer-events-none fixed left-1/5 top-1/5 z-0 h-72 w-72 rounded-full bg-blue-200/20 blur-3xl"
      />
      <div
        aria-hidden
        className="login-float pointer-events-none fixed bottom-1/5 right-1/5 z-0 h-96 w-96 rounded-full bg-indigo-200/20 blur-3xl"
        style={{ animationDelay: '3s' }}
      />

      <main className="relative z-10 flex min-h-screen items-center justify-center p-4 md:p-8">
        <div className="login-fade-in grid w-full max-w-5xl overflow-hidden rounded-2xl bg-white/85 shadow-2xl backdrop-blur-xl md:grid-cols-2">
          <div className="relative flex flex-col justify-center overflow-hidden bg-gradient-to-br from-blue-50/80 to-indigo-50/80 p-8 md:p-12">
            <div aria-hidden className="absolute right-0 top-0 h-48 w-48 opacity-10">
              <svg viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="20" cy="20" r="3" fill="#2563eb" />
                <circle cx="80" cy="30" r="4" fill="#2563eb" />
                <circle cx="40" cy="70" r="2" fill="#2563eb" />
                <circle cx="70" cy="80" r="3" fill="#2563eb" />
                <circle cx="50" cy="50" r="5" fill="#2563eb" />
                <line x1="20" y1="20" x2="80" y2="30" stroke="#2563eb" strokeWidth="1" />
                <line x1="80" y1="30" x2="70" y2="80" stroke="#2563eb" strokeWidth="1" />
                <line x1="20" y1="20" x2="40" y2="70" stroke="#2563eb" strokeWidth="1" />
                <line x1="40" y1="70" x2="70" y2="80" stroke="#2563eb" strokeWidth="1" />
                <line x1="20" y1="20" x2="50" y2="50" stroke="#2563eb" strokeWidth="1" />
                <line x1="80" y1="30" x2="50" y2="50" stroke="#2563eb" strokeWidth="1" />
                <line x1="40" y1="70" x2="50" y2="50" stroke="#2563eb" strokeWidth="1" />
                <line x1="70" y1="80" x2="50" y2="50" stroke="#2563eb" strokeWidth="1" />
              </svg>
            </div>

            <div className="mb-8">
              <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-xl bg-brand/10">
                <svg
                  className="h-8 w-8 text-brand"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"
                  />
                </svg>
              </div>
              <h1 className="mb-3 text-[clamp(1.75rem,3vw,2.5rem)] font-bold leading-tight text-ink-900">
                网络设备配置助手
              </h1>
              <p className="max-w-sm text-[15px] leading-relaxed text-ink-500 md:text-base">
                智能转换多厂商网络设备配置，统一语法规范，大幅降低运维复杂度与出错率
              </p>
            </div>

            <ul className="space-y-4">
              {FEATURES.map((feature) => (
                <li key={feature.title} className="flex items-start gap-3">
                  <div className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-brand/10">
                    <svg
                      className="h-3.5 w-3.5 text-brand"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                      xmlns="http://www.w3.org/2000/svg"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <div>
                    <p className="font-medium text-ink-900">{feature.title}</p>
                    <p className="mt-0.5 text-sm text-ink-400">{feature.desc}</p>
                  </div>
                </li>
              ))}
            </ul>
          </div>

          <div className="flex flex-col justify-center p-8 md:p-12">
            <div className="mb-8">
              <h2 className="mb-2 text-2xl font-bold text-ink-900">欢迎回来</h2>
              <p className="text-[15px] text-ink-500">请登录您的账户以继续使用</p>
            </div>

            <form className="space-y-5" onSubmit={handleSubmit}>
              <div className="space-y-2">
                <label htmlFor="username" className="block text-sm font-medium text-ink-700">
                  用户名
                </label>
                <div className="relative">
                  <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                    <svg
                      className="h-[18px] w-[18px] text-ink-300"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                      xmlns="http://www.w3.org/2000/svg"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth="2"
                        d="M16 12a4 4 0 10-8 0 4 4 0 008 0zm0 0v1.5a2.5 2.5 0 005 0V12a9 9 0 10-9 9m4.5-1.206a8.959 8.959 0 01-4.5 1.207"
                      />
                    </svg>
                  </div>
                  <input
                    id="username"
                    name="username"
                    type="text"
                    autoFocus
                    autoComplete="username"
                    placeholder="请输入用户名"
                    value={username}
                    onChange={(event) => setUsername(event.target.value)}
                    className="w-full rounded-lg border border-line py-3 pl-10 pr-4 text-[15px] text-ink-900 transition-all duration-200 placeholder:text-ink-300 focus:border-brand focus:outline-none focus:ring-2 focus:ring-brand/20"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label htmlFor="password" className="block text-sm font-medium text-ink-700">
                  密码
                </label>
                <div className="relative">
                  <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                    <svg
                      className="h-[18px] w-[18px] text-ink-300"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                      xmlns="http://www.w3.org/2000/svg"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth="2"
                        d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
                      />
                    </svg>
                  </div>
                  <input
                    id="password"
                    name="password"
                    type={showPassword ? 'text' : 'password'}
                    autoComplete="current-password"
                    placeholder="请输入密码"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    className="w-full rounded-lg border border-line py-3 pl-10 pr-12 text-[15px] text-ink-900 transition-all duration-200 placeholder:text-ink-300 focus:border-brand focus:outline-none focus:ring-2 focus:ring-brand/20"
                  />
                  <button
                    type="button"
                    aria-label={showPassword ? '隐藏密码' : '显示密码'}
                    onClick={() => setShowPassword((visible) => !visible)}
                    className="absolute inset-y-0 right-0 flex items-center pr-3 text-ink-300 transition-colors hover:text-ink-500"
                  >
                    {showPassword ? (
                      <svg
                        className="h-[18px] w-[18px]"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                        xmlns="http://www.w3.org/2000/svg"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth="2"
                          d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"
                        />
                      </svg>
                    ) : (
                      <svg
                        className="h-[18px] w-[18px]"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                        xmlns="http://www.w3.org/2000/svg"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth="2"
                          d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                        />
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth="2"
                          d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                        />
                      </svg>
                    )}
                  </button>
                </div>
              </div>

              {error ? (
                <p className="rounded-lg bg-danger-soft px-3 py-2 text-[13px] text-danger">{error}</p>
              ) : null}

              <button
                type="submit"
                disabled={submitting}
                className="w-full rounded-lg bg-brand py-3 text-[15px] font-medium text-white transition-all duration-300 hover:-translate-y-0.5 hover:bg-brand-strong hover:shadow-lg active:translate-y-0 active:shadow-md disabled:cursor-not-allowed disabled:opacity-60"
              >
                {submitting ? '登录中…' : '登 录'}
              </button>
            </form>
          </div>
        </div>
      </main>
    </div>
  )
}
