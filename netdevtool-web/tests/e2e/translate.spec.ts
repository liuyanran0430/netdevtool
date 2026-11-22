/**
 * 翻译页 E2E：加载、完整翻译流程、必填校验、返回上一步数据保留、接口失败重试。
 * 设备与翻译接口全部 Mock，断言以页面上的业务结果为准。
 */

import { expect, test } from '@playwright/test';
import {
  TRANSLATION_RESULT,
  fulfillJson,
  mockBaseApi,
  seedSession,
} from './support/mocks';

const SOURCE_TEXT =
  'interface GigabitEthernet0/0/1\n description uplink';

const sourceEditor = (page: import('@playwright/test').Page) =>
  page.getByPlaceholder('粘贴或导入设备配置…');

const combobox = (page: import('@playwright/test').Page, index: number) =>
  page.getByRole('combobox').nth(index);

const translateButton = (page: import('@playwright/test').Page) =>
  page.getByRole('button', { name: '翻译', exact: true });

test.describe('配置翻译', () => {
  test.beforeEach(async ({ page }) => {
    await seedSession(page);
    await mockBaseApi(page);
    await page.goto('/translate');
  });

  test('页面正常加载，展示设备选择与源配置编辑区', async ({ page }) => {
    await expect(page.getByRole('heading', { name: '配置翻译' })).toBeVisible();
    await expect(page.getByText('尚未翻译 · 选择设备后点击「翻译」')).toBeVisible();

    await expect(combobox(page, 0)).toHaveValue('switch');
    await expect(combobox(page, 1)).toHaveValue('华为');
    await expect(combobox(page, 2)).toHaveValue('S5735');
    // 默认目标厂商与源厂商一致，此时翻译按钮禁用
    await expect(translateButton(page)).toBeDisabled();

    await expect(sourceEditor(page)).toBeVisible();
  });

  test('核心流程：选择目标设备后翻译并展示结果', async ({ page }) => {
    let posted: Record<string, unknown> | null = null;
    await page.route('**/api/v1/translations**', (route) => {
      const request = route.request();
      const { pathname } = new URL(request.url());

      if (request.method() === 'POST') {
        posted = request.postDataJSON() as Record<string, unknown>;
        return fulfillJson(route, { request_id: 'req-e2e', status: 'pending' });
      }
      if (request.method() === 'GET' && /^\/api\/v1\/translations\/[^/]+$/.test(pathname)) {
        return fulfillJson(route, {
          request_id: 'req-e2e',
          status: 'succeeded',
          result: TRANSLATION_RESULT,
        });
      }
      return fulfillJson(route, []);
    });

    await sourceEditor(page).fill(SOURCE_TEXT);
    await expect(page.getByText('已自动保存')).toBeVisible();

    // 目标厂商切到 H3C，目标型号自动联动为 S6520
    await combobox(page, 3).selectOption('H3C');
    await expect(combobox(page, 4)).toHaveValue('S6520');
    await expect(translateButton(page)).toBeEnabled();

    await translateButton(page).click();

    await expect(page.getByText('翻译完成')).toBeVisible();
    await expect(page.getByText('共 2 条命令')).toBeVisible();
    await expect(
      page.getByText('interface GigabitEthernet1/0/1').first(),
    ).toBeVisible();
    // 有结果后按钮变为“重新翻译”，导出可用
    await expect(
      page.getByRole('button', { name: '重新翻译' }),
    ).toBeVisible();
    await expect(page.getByRole('button', { name: /^导出/ })).toBeEnabled();

    expect(posted).toMatchObject({
      source_text: SOURCE_TEXT,
      source_vendor: '华为',
      source_model: 'S5735',
      target_vendor: 'H3C',
      target_model: 'S6520',
    });
  });

  test('必填校验：未输入源配置时阻止翻译', async ({ page }) => {
    let createRequests = 0;
    await page.route('**/api/v1/translations**', (route) => {
      if (route.request().method() === 'POST') createRequests += 1;
      return fulfillJson(route, []);
    });

    await combobox(page, 3).selectOption('H3C');
    await translateButton(page).click();

    await expect(page.getByText('请先输入或导入源配置')).toBeVisible();
    expect(createRequests).toBe(0);
    await expect(page.getByText('尚未翻译 · 选择设备后点击「翻译」')).toBeVisible();
  });

  test('去提问后返回翻译页，源配置与设备选择保留', async ({ page }) => {
    await sourceEditor(page).fill(SOURCE_TEXT);
    await combobox(page, 3).selectOption('H3C');
    await expect(page.getByText('已自动保存')).toBeVisible();

    await page.getByRole('button', { name: '去提问' }).click();
    await expect(page).toHaveURL(/\/chat$/);

    await page.getByRole('link', { name: '翻译' }).click();
    await expect(page).toHaveURL(/\/translate$/);

    await expect(sourceEditor(page)).toHaveValue(SOURCE_TEXT);
    await expect(combobox(page, 3)).toHaveValue('H3C');
    await expect(combobox(page, 4)).toHaveValue('S6520');
    await expect(page.getByText('已自动保存')).toBeVisible();
  });

  test('翻译接口失败提示错误，重试后成功生成结果', async ({ page }) => {
    let createAttempts = 0;
    await page.route('**/api/v1/translations**', (route) => {
      const request = route.request();
      const { pathname } = new URL(request.url());

      if (request.method() === 'POST') {
        createAttempts += 1;
        if (createAttempts === 1) {
          return fulfillJson(
            route,
            { code: 500, message: '翻译服务暂不可用' },
            500,
          );
        }
        return fulfillJson(route, { request_id: 'req-retry', status: 'pending' });
      }
      if (request.method() === 'GET' && /^\/api\/v1\/translations\/[^/]+$/.test(pathname)) {
        return fulfillJson(route, {
          request_id: 'req-retry',
          status: 'succeeded',
          result: TRANSLATION_RESULT,
        });
      }
      return fulfillJson(route, []);
    });

    await sourceEditor(page).fill(SOURCE_TEXT);
    await combobox(page, 3).selectOption('H3C');

    await translateButton(page).click();
    await expect(page.getByText('翻译服务暂不可用')).toBeVisible();
    await expect(translateButton(page)).toBeEnabled();

    await translateButton(page).click();
    await expect(page.getByText('翻译完成')).toBeVisible();
    await expect(page.getByText('共 2 条命令')).toBeVisible();
    expect(createAttempts).toBe(2);
  });
});
