import { defineConfig, devices } from '@playwright/test';

const BASE_URL = 'http://127.0.0.1:5175';
// 仅把 GitHub Actions 视为 CI；IDE 终端可能注入 CI=true，不能据此禁用服务复用
const IS_CI = !!process.env.GITHUB_ACTIONS;

/**
 * E2E 配置：与 vite dev server（端口 5175，strictPort）保持一致。
 * 失败时保留截图、视频与 trace，统一输出到 test-results / playwright-report。
 */
export default defineConfig({
  testDir: './tests/e2e',
  /* Run tests in files in parallel */
  fullyParallel: true,
  /* Fail the build on CI if you accidentally left test.only in the source code. */
  forbidOnly: IS_CI,
  /* Retry on CI only */
  retries: IS_CI ? 2 : 0,
  /* Opt out of parallel tests on CI. */
  workers: IS_CI ? 1 : undefined,
  timeout: 45_000,
  expect: { timeout: 10_000 },
  /* Reporter to use. See https://playwright.dev/docs/test-reporters */
  reporter: [['list'], ['html', { outputFolder: 'playwright-report', open: 'never' }]],

  /* Shared settings for all the projects below. See https://playwright.dev/docs/api/class-testoptions. */
  use: {
    baseURL: BASE_URL,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },

  /* 测试前自动拉起 dev server；本地已有服务时直接复用 */
  webServer: {
    command: 'npm run dev',
    url: BASE_URL,
    reuseExistingServer: !IS_CI,
    timeout: 120_000,
    stdout: 'pipe',
    stderr: 'pipe',
  },

  /*
   * 仅跑 Chromium：Firefox / WebKit 二进制体积大、国内下载慢，
   * 且本项目 UI 以 Chromium 内核为基线，多内核回归收益低。
   */
  projects: [
    {
      name: 'chromium',
      // 复用本机已安装的 Chrome，避免下载 Playwright 内置 Chromium
      use: { ...devices['Desktop Chrome'], channel: 'chrome' },
    },
  ],
});
