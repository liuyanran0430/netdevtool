/**
 * E2E 共享 Mock：后端未启动时提供确定性的接口响应。
 * 所有请求经 page.route 拦截，不依赖真实 8083 服务。
 */

import type { Page, Route } from '@playwright/test';

export const API_PREFIX = '**/api/v1';

export const SESSION = {
  token: 'e2e-token',
  user: { id: 1, username: 'alice', name: 'Alice', status: 'enabled' },
};

export const DEVICES = [
  { id: 1, vendor: '华为', vendor_en: 'huawei', model: 'S5735', device_type: 'switch' },
  { id: 2, vendor: 'H3C', vendor_en: 'h3c', model: 'S6520', device_type: 'switch' },
  { id: 3, vendor: '华为', vendor_en: 'huawei', model: 'USG6000', device_type: 'firewall' },
];

/** 翻译成功后的固定结果，供业务断言使用 */
export const TRANSLATION_RESULT = {
  lines: [
    {
      no: 1,
      text: 'interface GigabitEthernet1/0/1',
      tone: 'success',
      source_no: 1,
      entity_id: 'interface',
    },
    {
      no: 2,
      text: 'description uplink',
      tone: 'success',
      source_no: 2,
      entity_id: 'description',
    },
  ],
  warnings: [],
  entities: [],
  summary: { total: 2, duration_ms: 1200 },
};

export function fulfillJson(route: Route, body: unknown, status = 200) {
  return route.fulfill({
    status,
    contentType: 'application/json',
    body: JSON.stringify(body),
  });
}

/** 写入登录会话，避免 RequireAuth 跳转到 /login */
export async function seedSession(page: Page) {
  await page.addInitScript((session) => {
    window.localStorage.setItem('netdevtool:session', JSON.stringify(session));
  }, SESSION);
}

/** 登录后各页面通用的基础接口：当前用户、设备列表、会话列表 */
export async function mockBaseApi(page: Page) {
  await page.route(`${API_PREFIX}/auth/me`, (route) =>
    fulfillJson(route, SESSION.user),
  );
  await page.route(`${API_PREFIX}/devices`, (route) =>
    fulfillJson(route, DEVICES),
  );
  await page.route(`${API_PREFIX}/chat/sessions**`, (route) =>
    fulfillJson(route, []),
  );
}
