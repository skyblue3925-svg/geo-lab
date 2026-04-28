const { test, expect } = require('@playwright/test');

async function openSidebarIfCollapsed(page) {
  const toggle = page.getByRole('button', { name: 'keyboard_double_arrow_right' });
  if (await toggle.isVisible().catch(() => false)) {
    await toggle.click();
  }
}

test('Home and Overview expose product-shell entry points', async ({ page }) => {
  await page.goto('/');
  await openSidebarIfCollapsed(page);

  await expect(page.locator('.classroom-hero-title')).toBeVisible({ timeout: 60000 });
  await expect(page.getByText(/고등학교 지형 수업을 바로 시작하는 메인 홈/)).toBeVisible();
  await expect(page.getByTestId('stSidebarNavItems').getByRole('link', { name: 'Overview' })).toBeVisible();
  await page.getByTestId('stSidebarNavItems').getByRole('link', { name: 'Overview' }).click();
  await expect(page).toHaveURL(/\/Overview$/);
  await expect(page.getByTestId('stSidebarNavItems').getByRole('link', { name: 'Lab' })).toBeVisible();
  await expect(page.getByText('별도 포털 열기')).toBeVisible();
});
