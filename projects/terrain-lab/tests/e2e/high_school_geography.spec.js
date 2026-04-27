const { test, expect } = require('@playwright/test');

async function openSidebarIfCollapsed(page) {
  const toggle = page.getByRole('button', { name: 'keyboard_double_arrow_right' });
  if (await toggle.isVisible().catch(() => false)) {
    await toggle.click();
  }
}

test('High school geography atlas routes a topic into Lab preset flow', async ({ page }) => {
  await page.goto('/High_School_Geography');

  await expect(page.getByText(/고등학교 세계지리 지형 형성 아틀라스/i)).toBeVisible({ timeout: 20000 });
  await expect(page.getByText(/1\. 단원 선택/i)).toBeVisible();
  await expect(page.getByText(/하천 침식과 퇴적 지형/i)).toBeVisible();

  const studentButton = page.getByRole('button', { name: /Lab 학생 탐구로 열기/i });
  await studentButton.scrollIntoViewIfNeeded();
  await studentButton.click();

  await expect(page).toHaveURL(/\/Lab$/);
  await openSidebarIfCollapsed(page);
  await expect(page.locator('[data-testid="stSidebar"]').getByText(/preset/i)).toBeVisible({ timeout: 20000 });
});
