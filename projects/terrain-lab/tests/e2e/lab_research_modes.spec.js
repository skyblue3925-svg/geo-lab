const { test, expect } = require('@playwright/test');

async function openSidebarIfCollapsed(page) {
  const toggle = page.getByRole('button', { name: 'keyboard_double_arrow_right' });
  if (await toggle.isVisible().catch(() => false)) {
    await toggle.click();
  }
}

async function getSidebarButton(page, namePattern) {
  const button = page.locator('[data-testid="stSidebar"]').getByRole('button', { name: namePattern }).first();
  await button.scrollIntoViewIfNeeded();
  return button;
}

test.describe('Geo-Lab mode smoke', () => {
  test('Lab student mode shows captioned playback after running a simulation', async ({ page }) => {
    await page.goto('/Lab');
    await openSidebarIfCollapsed(page);

    await expect(await getSidebarButton(page, /실행/)).toBeVisible();
    await expect(page.getByText('학생 모드에서는 실행 후 부드러운 재생과 단계별 설명 캡션이 함께 제공됩니다.')).toBeVisible({ timeout: 20000 });
    await expect(page.getByText('내 연구 데이터 (Research Tab)')).toHaveCount(0);

    await (await getSidebarButton(page, /실행/)).click();

    await expect(page.getByText('부드러운 형성 애니메이션')).toBeVisible({ timeout: 120000 });
    await expect(page.getByRole('slider', { name: '핵심 장면' })).toBeVisible();
    await expect(page.getByText('직전 장면 대비 평균 절대 변화')).toBeVisible();
  });

  test('Lab routes advanced users to the Higher Ed portal', async ({ page }) => {
    await page.goto('/Lab');
    await openSidebarIfCollapsed(page);

    await page.getByText('🎓 Higher Ed / 연구·심화 흐름').click();
    await expect(page.getByText('대학·연구 포털로 이동')).toBeVisible({ timeout: 20000 });
    await page.getByText('대학·연구 포털로 이동').click();

    await expect(page).toHaveURL(/\/Higher_Ed$/);
    await expect(page.getByText('대학·연구·교수 사용자는 이 페이지에서 시작합니다')).toBeVisible({ timeout: 20000 });
  });

  test('Research DEM compare tab exposes comparison controls after generating DEM', async ({ page }) => {
    await page.goto('/Research');
    await openSidebarIfCollapsed(page);

    await expect(page.getByText('Research Lab').first()).toBeVisible({ timeout: 60000 });
    await expect(page.getByRole('button', { name: /생성/ }).first()).toBeVisible({ timeout: 60000 });
    await page.getByRole('button', { name: /생성/ }).first().click();

    await expect(page.getByRole('tab', { name: 'DEM Compare' })).toBeVisible({ timeout: 120000 });
    await page.getByRole('tab', { name: 'DEM Compare' }).click();

    await expect(page.getByText('횡단면 비교 행')).toBeVisible();
    await expect(page.getByText('종단면 비교 열')).toBeVisible();
    await expect(page.getByText('비교할 기준 DEM 업로드')).toBeVisible();
  });
});
