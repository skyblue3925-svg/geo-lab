const { test, expect } = require('@playwright/test');

async function openSidebarIfCollapsed(page) {
  const toggle = page.getByRole('button', { name: 'keyboard_double_arrow_right' });
  if (await toggle.isVisible().catch(() => false)) {
    await toggle.click();
  }
}

async function getSidebarButton(page, namePattern) {
  const button = page.locator('[data-testid="stSidebar"]').getByRole('button', { name: namePattern }).first();
  await expect(button).toBeVisible();
  return button;
}

test('Lab teacher mode preview and gif debug', async ({ page }) => {
  page.on('console', (msg) => console.log('BROWSER:', msg.type(), msg.text()));

  await page.goto('/Lab');
  await openSidebarIfCollapsed(page);

  await page.locator('[data-testid="stSidebar"]').getByText('교사 상세모드', { exact: true }).click();
  await expect(page.getByText('교사용 상세 모드', { exact: false })).toBeVisible({ timeout: 20000 });

  await (await getSidebarButton(page, /실행/)).click();
  await expect(page.getByRole('slider', { name: '프레임' })).toHaveCount(1, { timeout: 120000 });

  await expect(page.getByText('지형 애니메이션 미리보기')).toBeVisible({ timeout: 120000 });
  await expect(page.locator('iframe[title="st.iframe"]').last()).toBeVisible({ timeout: 120000 });

  await page.getByText('수업 자료 저장 (선택)').click();
  const gifButton = page.getByRole('button', { name: 'GIF 저장' });
  await gifButton.click();
  await page.waitForTimeout(1500);

  const downloadButton = page.getByRole('button', { name: 'GIF 다운로드' });
  await expect(downloadButton).toBeVisible();

  await page.screenshot({ path: 'output/playwright/lab-teacher-debug.png', fullPage: true });
});
