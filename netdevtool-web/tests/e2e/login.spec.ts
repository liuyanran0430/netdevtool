/**
 * 登录页 E2E：加载、必填校验、接口失败提示与重试。
 * 所有请求由 page.route 提供确定性响应，不依赖真实后端。
 */

import { expect, test } from '@playwright/test';
import { DEVICES, SESSION, fulfillJson } from './support/mocks';

const LOGIN_BUTTON = /登\s*录/;

test.describe('登录页', () => {
  test('页面正常加载，展示品牌信息与登录表单', async ({ page }) => {
    await page.goto('/login');

    await expect(
      page.getByRole('heading', { name: '网络设备配置助手' }),
    ).toBeVisible();
    await expect(page.getByRole('heading', { name: '欢迎回来' })).toBeVisible();
    await expect(page.getByLabel('用户名', { exact: true })).toBeVisible();
    await expect(page.getByLabel('密码', { exact: true })).toBeVisible();
    await expect(page.getByRole('button', { name: LOGIN_BUTTON })).toBeEnabled();
  });

  test('必填校验：空账号密码不发请求并提示', async ({ page }) => {
    let loginRequests = 0;
    await page.route('**/api/v1/auth/login', (route) => {
      loginRequests += 1;
      return fulfillJson(route, { message: '不应被调用' }, 500);
    });

    await page.goto('/login');

    await page.getByRole('button', { name: LOGIN_BUTTON }).click();
    await expect(page.getByText('请输入用户名和密码')).toBeVisible();

    await page.getByLabel('用户名', { exact: true }).fill('alice');
    await page.getByRole('button', { name: LOGIN_BUTTON }).click();
    await expect(page.getByText('请输入用户名和密码')).toBeVisible();

    expect(loginRequests).toBe(0);
    await expect(page).toHaveURL(/\/login$/);
  });

  test('登录接口失败给出提示，重试成功后进入翻译页', async ({ page }) => {
    let attempts = 0;
    await page.route('**/api/v1/auth/login', (route) => {
      attempts += 1;
      if (attempts === 1) {
        return fulfillJson(route, { code: 500, message: '用户名或密码错误' }, 500);
      }
      return fulfillJson(route, SESSION);
    });
    await page.route('**/api/v1/auth/me', (route) => fulfillJson(route, SESSION.user));
    await page.route('**/api/v1/devices', (route) => fulfillJson(route, DEVICES));

    await page.goto('/login');
    await page.getByLabel('用户名', { exact: true }).fill('alice');
    await page.getByLabel('密码', { exact: true }).fill('secret');

    await page.getByRole('button', { name: LOGIN_BUTTON }).click();
    await expect(page.getByText('用户名或密码错误')).toBeVisible();
    await expect(page).toHaveURL(/\/login$/);

    await page.getByRole('button', { name: LOGIN_BUTTON }).click();

    await expect(page).toHaveURL(/\/translate$/);
    await expect(page.getByRole('heading', { name: '配置翻译' })).toBeVisible();
    expect(attempts).toBe(2);

    const stored = await page.evaluate(() =>
      window.localStorage.getItem('netdevtool:session'),
    );
    expect(stored).toContain(SESSION.token);
  });
});
