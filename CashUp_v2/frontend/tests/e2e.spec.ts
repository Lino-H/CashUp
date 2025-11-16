import { test, expect } from '@playwright/test'

test('首页加载与菜单导航', async ({ page }) => {
  await page.goto('/')
  await expect(page).toHaveTitle(/CashUp/)
  // 侧边菜单进入配置中心
  await page.getByText('配置中心').click()
  await expect(page.locator('text=系统配置')).toBeVisible()
})

test('配置中心保存并提示重载', async ({ page }) => {
  await page.goto('/config-center')
  await page.getByRole('button', { name: '新增/更新配置' }).click()
  await page.getByLabel('键').fill('trading.sync.interval')
  await page.getByLabel('值').fill('120')
  await page.getByRole('button', { name: '保存' }).click()
  await expect(page.locator('text=需要重载模块')).toBeVisible()
})

test('密钥管理加载交易所选项', async ({ page }) => {
  await page.goto('/keys-management')
  await expect(page.locator('.ant-table')).toBeVisible()
  await page.getByRole('button', { name: '新增/更新密钥' }).click()
  await expect(page.getByRole('combobox')).toBeVisible()
})