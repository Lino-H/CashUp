import { test, expect } from '@playwright/test'

test('核心服务与前端健康', async ({ request }) => {
  const respCore = await request.get('http://localhost:8001/health')
  expect(respCore.status()).toBe(200)
  const respFront = await request.get('http://localhost/health')
  expect(respFront.status()).toBe(200)
})

test('配置中心列表接口返回', async ({ request }) => {
  const resp = await request.get('http://localhost:8001/api/v1/configs')
  expect([200, 404]).toContain(resp.status())
})

test('交易所列表接口返回', async ({ request }) => {
  const resp = await request.get('http://localhost:8001/api/v1/exchanges')
  expect(resp.status()).toBe(200)
})

test('调度状态与调整间隔', async ({ request }) => {
  const seed = await request.post('http://localhost:8001/api/v1/seed/system_configs')
  expect(seed.status()).toBe(200)
  const put = await request.put('http://localhost:8001/api/v1/configs/trading.sync.interval', { data: { value: '120' } })
  expect(put.status()).toBe(200)
  const status = await request.get('http://localhost:8001/api/v1/scheduler/status?granularity=hour')
  expect(status.status()).toBe(200)
})

test('调度手动触发接口', async ({ request }) => {
  const resp1 = await request.post('http://localhost:8001/api/v1/scheduler/trigger', { data: { task: 'trading.sync' } })
  expect(resp1.status()).toBe(200)
  const resp2 = await request.post('http://localhost:8001/api/v1/scheduler/trigger', { data: { task: 'rss.fetch' } })
  expect(resp2.status()).toBe(200)
  const status = await request.get('http://localhost:8001/api/v1/scheduler/status')
  expect(status.status()).toBe(200)
})

test('设置备用RSS并查看状态', async ({ request }) => {
  const put = await request.put('http://localhost:8001/api/v1/configs/rss.fallback.feeds', { data: { value: ["https://news.google.com/rss?hl=zh-CN&gl=CN&ceid=CN:zh-Hans"] } })
  expect(put.status()).toBe(200)
  const status = await request.get('http://localhost:8001/api/v1/scheduler/status?granularity=day&task=rss.fetch')
  expect(status.status()).toBe(200)
})