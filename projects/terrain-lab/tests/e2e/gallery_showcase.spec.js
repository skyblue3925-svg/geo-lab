const { test, expect } = require('@playwright/test');

async function openSidebarIfCollapsed(page) {
  const toggle = page.getByRole('button', { name: 'keyboard_double_arrow_right' });
  if (await toggle.isVisible().catch(() => false)) {
    await toggle.click();
  }
}

test('Gallery showcase card opens a Lab preset', async ({ page }) => {
  await page.goto('/Gallery');
  await openSidebarIfCollapsed(page);

  await expect(page.getByText(/수업용 예시|예시 카탈로그/i)).toBeVisible({ timeout: 20000 });
  await expect(page.getByText(/세계 위치/i)).toBeVisible({ timeout: 20000 });
  const labStartButton = page.getByRole('button', { name: /Lab 수업으로 열기|Lab에서 수업 시작/i }).first();
  await labStartButton.scrollIntoViewIfNeeded();
  await labStartButton.click();

  await expect(page).toHaveURL(/\/Lab$/);

  await openSidebarIfCollapsed(page);
  const sidebar = page.locator('[data-testid="stSidebar"]');
  await expect(sidebar.getByText(/preset/i)).toBeVisible({ timeout: 20000 });
});
