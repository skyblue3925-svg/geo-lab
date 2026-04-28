const { test, expect } = require("@playwright/test");

async function waitForWorkspace(page) {
  await page.addInitScript(() => {
    window.localStorage.clear();
  });

  await page.goto("/?r=playwright-student-workspace", {
    waitUntil: "domcontentloaded",
  });

  await expect(page.locator("#map")).toBeVisible();
  await expect(page.locator("#locationSearchField")).toBeVisible();
  await page.waitForFunction(() => window.__SCHOOL_GIS_READY === true);
  await page.waitForTimeout(500);
}

test("student gis workspace starts with one layer-add entry", async ({ page }) => {
  const pageErrors = [];

  page.on("pageerror", (error) => {
    pageErrors.push(error.message);
  });

  await waitForWorkspace(page);

  await expect(page.locator("#layerAddButton")).toBeVisible();
  await expect(page.locator("#layerAddSheet")).toBeHidden();
  await expect(page.locator("#drawToolbar")).toBeHidden();
  await expect(page.locator("#publicCard")).toBeVisible();
  await expect(page.locator("#studentCard")).toBeHidden();
  await expect(page.locator("#layerStackCard")).toBeHidden();
  await expect(page.locator("#adminScaleField")).toBeVisible();
  await expect(page.locator("#adminScaleField")).toHaveValue("grid-sgg-500m");
  await expect(page.locator("#sgisProfileField")).toBeVisible();
  await expect(page.locator("#sgisProfileField")).toHaveValue("grid-sgg-500m");
  await page.selectOption("#adminScaleField", "region-sgg-children");
  await expect(page.locator("#sgisProfileField")).toHaveValue("region-sgg-children");
  await expect(page.locator("#schoolSgisQuickActions .quick-action-card")).toHaveCount(1);

  await page.click("#layerAddButton");
  await expect(page.locator("#layerAddSheet")).toBeVisible();
  await expect(page.locator("#layerAddSheet [data-layer-add-choice='public']")).toBeVisible();
  await expect(page.locator("#layerAddSheet [data-layer-add-choice='draw']")).toBeVisible();
  await expect(page.locator("#layerAddSheet [data-layer-add-choice]")).toHaveCount(2);

  await expect(page.locator("#mapTitle")).toContainText("GIS");
  await expect(page.locator("#mapLayerHub")).toContainText("Layer Hub");
  await expect(page.locator("#mapLayerHub [data-layer-hub-action='open-layer-tools']")).toBeVisible();
  expect(pageErrors).toEqual([]);
});

test("drawing choice creates a student layer and reveals drawing tools", async ({ page }) => {
  await waitForWorkspace(page);

  await page.click("#layerAddButton");
  await page.click("#layerAddSheet [data-layer-add-choice='draw']");

  await expect(page.locator("#drawToolbar")).toBeVisible();
  await expect(page.locator("#studentLayerCount")).toContainText("1");
  await expect(page.locator("#activeLayerField")).not.toHaveValue("");
  await expect(page.locator("#drawToolbar [data-draw-tool='point']")).toBeEnabled();
  await expect(page.locator("#drawToolbar [data-draw-tool='line']")).toBeEnabled();
  await expect(page.locator("#drawToolbar [data-draw-tool='polygon']")).toBeEnabled();
  await expect(page.locator("#mapLayerHub")).toContainText("1");
});

test("public choice opens student-language statistics choices", async ({ page }) => {
  await waitForWorkspace(page);

  await page.click("#layerAddButton");
  await page.click("#layerAddSheet [data-layer-add-choice='public']");

  await expect(page.locator("#publicCard")).toBeVisible();
  await expect(page.locator("#publicSimpleFlow")).toBeVisible();
  await expect(page.locator("#publicSimpleFlow [data-public-topic='population']")).toBeVisible();
  await expect(page.locator("#publicSimpleFlow [data-public-topic='age']")).toBeVisible();
  await expect(page.locator("#publicSimpleFlow [data-public-topic='business']")).toBeVisible();
  await expect(page.locator("#publicSimpleFlow [data-public-shape='grid']")).toBeVisible();
  await expect(page.locator("#publicSimpleFlow [data-public-scope='current']")).toBeVisible();
  await expect(page.locator("#simplePublicSubmitButton")).toBeVisible();
  await expect(page.locator("#simplePublicSubmitButton")).toBeDisabled();
});

test("layer cards keep destructive and export actions behind more details", async ({ page }) => {
  await waitForWorkspace(page);

  await page.click("#layerAddButton");
  await page.click("#layerAddSheet [data-layer-add-choice='draw']");
  await page.click("#sidebarPanelTabs [data-sidebar-panel='layers']");

  const studentCard = page.locator("#studentLayerList .layer-card").first();
  await expect(studentCard).toBeVisible();
  await expect(studentCard.locator("[data-action='toggle-student-layer']")).toBeVisible();
  await expect(studentCard.locator("[data-action='set-student-layer-opacity']")).toBeVisible();
  await expect(studentCard.locator("[data-action='delete-student-layer']")).toBeHidden();
  await studentCard.locator("summary", { hasText: "더보기" }).click();
  await expect(studentCard.locator("[data-action='delete-student-layer']")).toBeVisible();
});

test("desktop layout is map-first with GIS task tabs", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await waitForWorkspace(page);

  const layout = await page.evaluate(() => {
    const mapColumn = document.querySelector(".content-stack").getBoundingClientRect();
    const toolsPanel = document.querySelector("#sidebar").getBoundingClientRect();
    const hero = document.querySelector(".hero-panel").getBoundingClientRect();
    return {
      mapX: Math.round(mapColumn.x),
      toolsX: Math.round(toolsPanel.x),
      mapWidth: Math.round(mapColumn.width),
      toolsWidth: Math.round(toolsPanel.width),
      heroHeight: Math.round(hero.height),
    };
  });

  expect(layout.mapX).toBeLessThan(layout.toolsX);
  expect(layout.mapWidth).toBeGreaterThan(layout.toolsWidth * 2);
  expect(layout.heroHeight).toBeLessThanOrEqual(86);
  await expect(page.locator("#sidebarPanelTabs [data-sidebar-panel='public']")).toHaveText("공공데이터");
  await expect(page.locator("#sidebarPanelTabs [data-sidebar-panel='student']")).toHaveText("내 레이어");
  await expect(page.locator("#sidebarPanelTabs [data-sidebar-panel='analysis']")).toHaveText("분석");
  await expect(page.locator("#sidebarPanelTabs [data-sidebar-panel='layers']")).toHaveText("레이어");
});

test("map view overlay chips give visible applied feedback", async ({ page }) => {
  await waitForWorkspace(page);

  const trafficChip = page.locator("#mapOverlayFilterList [data-overlay-id='traffic']");
  await expect(trafficChip).toBeVisible();
  await expect(trafficChip).not.toHaveClass(/is-active/);

  await trafficChip.click();
  await expect(trafficChip).toHaveClass(/is-active/);
  await expect(page.locator("#statusNotice")).toContainText("교통");
  await expect(page.locator("#statusNotice")).toContainText("켰습니다");

  await trafficChip.click();
  await expect(trafficChip).not.toHaveClass(/is-active/);
  await expect(page.locator("#statusNotice")).toContainText("껐습니다");
});

test("location must be confirmed before SGIS actions unlock", async ({ page }) => {
  await waitForWorkspace(page);

  await expect(page.locator("#scopePill")).toContainText("위치 미고정");
  const sgisActions = page.locator("#schoolSgisQuickActions [data-action]");
  await expect(sgisActions.first()).toBeDisabled();
  await expect(page.locator("#sgisProfileSubmitButton")).toBeDisabled();

  page.once("dialog", async (dialog) => {
    expect(dialog.message()).toContain("지금 이 화면의 GIS 기준 위치");
    await dialog.dismiss();
  });
  await page.locator("#useMapCenterButton").dispatchEvent("click");
  await expect(sgisActions.first()).toBeDisabled();

  page.once("dialog", async (dialog) => {
    expect(dialog.message()).toContain("지금 이 화면의 GIS 기준 위치");
    await dialog.accept();
  });
  await page.locator("#useMapCenterButton").dispatchEvent("click");
  await expect(sgisActions.first()).toBeEnabled();
  await expect(page.locator("#sgisProfileSubmitButton")).toBeEnabled();
  await expect(page.locator("#scopePill")).toContainText("위치 고정됨");
});

test("search fallback offers current map center when providers fail", async ({ page }) => {
  await page.route("https://nominatim.openstreetmap.org/**", (route) => route.abort());
  await waitForWorkspace(page);

  await page.fill("#locationSearchField", "CodexNoResultSchool");
  await page.click("#locationSearchButton");
  await expect(page.locator("#locationSearchResults")).toContainText("현재 지도 중심");
  await expect(page.locator("#scopePill")).toContainText("위치 미고정");
});

test("mobile keeps map sticky and scrolls layer tools inside the sheet", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await waitForWorkspace(page);

  await expect
    .poll(() =>
      page.evaluate(() => ({
        viewportWidth: window.innerWidth,
        pageWidth: document.documentElement.scrollWidth,
      })),
    )
    .toEqual({ viewportWidth: 390, pageWidth: 390 });
  await expect(page.locator(".content-stack")).toHaveCSS("position", "sticky");
  await expect(page.locator("#mobileToolsButton")).toBeVisible();

  await page.click("#mobileToolsButton");
  await expect(page.locator("#sidebar")).toBeVisible();
  await expect(page.locator("#sidebar")).toHaveCSS("position", "fixed");
  await expect(page.locator("#sidebar")).toHaveCSS("overflow-y", "auto");
});

test("imported SGIS grid layers expose cell information", async ({ page }) => {
  await page.addInitScript(() => {
    const storageScope = `${"탐색 중심"}-${Number(37.5665).toFixed(4)}-${Number(126.978).toFixed(4)}-${1200}`
      .replace(/[^\w.-]+/g, "-")
      .toLowerCase();
    const storageKey = `school-neighborhood-gis-public-layers-v1:${storageScope}`;
    window.localStorage.clear();
    window.localStorage.setItem(
      storageKey,
      JSON.stringify([
        {
          id: "grid-layer-test",
          name: "SGIS 총인구 2023 · 100m 격자",
          description: "테스트 격자 레이어",
          color: "#1d78c8",
          opacity: 1,
          visible: true,
          scope: "both",
          sourceKind: "sgis",
          sourceLabel: "SGIS grid/data.geojson",
          featureCollection: {
            type: "FeatureCollection",
            features: [
              {
                type: "Feature",
                geometry: {
                  type: "Polygon",
                  coordinates: [[
                    [126.976, 37.565],
                    [126.98, 37.565],
                    [126.98, 37.568],
                    [126.976, 37.568],
                    [126.976, 37.565],
                  ]],
                },
                properties: {
                  title: "100m 격자 다마89",
                  isGridFeature: true,
                  gridLevelDiv: "100m",
                  gridSizeLabel: "100m",
                  gridCode: "다마89",
                  gridIndex: 1,
                  metricLabel: "총인구",
                  metricValue: 42,
                  metricUnit: "명",
                  metricDigits: 0,
                  metricYear: "2023",
                  metricSourceLabel: "테스트 행정구역 통계 결합",
                  note: "테스트 격자 정보",
                },
              },
            ],
          },
        },
      ]),
    );
  });

  await page.goto("/?r=playwright-grid-info", {
    waitUntil: "domcontentloaded",
  });

  await expect(page.locator("#map")).toBeVisible();
  await expect(page.locator("#importedPublicLayerList")).toContainText("100m 격자 셀 정보");
  await expect(page.locator("#importedPublicLayerList")).toContainText("100m 격자 다마89");
  await expect(page.locator("#importedPublicLayerList")).toContainText("42명");
});

test("SGIS grid import clips cells to the fixed reference radius", async ({ page }) => {
  await waitForWorkspace(page);

  const featureCount = await page.evaluate(async () => {
    const sgis = await import("/sgis-adapter.js");
    const toSgis = (lng, lat) => window.proj4("EPSG:4326", "EPSG:5179", [lng, lat]);
    const makeSquare = (centerLng, centerLat, size = 0.002) => [[
      toSgis(centerLng - size, centerLat - size),
      toSgis(centerLng + size, centerLat - size),
      toSgis(centerLng + size, centerLat + size),
      toSgis(centerLng - size, centerLat + size),
      toSgis(centerLng - size, centerLat - size),
    ]];
    const originalFetch = window.fetch;
    window.fetch = async (url) => {
      const requestUrl = String(url);
      if (requestUrl.includes("/grid")) {
        return new Response(JSON.stringify({
          boundary: {
            type: "FeatureCollection",
            features: [
              {
                type: "Feature",
                geometry: { type: "Polygon", coordinates: makeSquare(126.978, 37.5665) },
                properties: { adm_cd: "near-grid", adm_nm: "near-grid" },
              },
              {
                type: "Feature",
                geometry: { type: "Polygon", coordinates: makeSquare(127.3, 37.8) },
                properties: { adm_cd: "far-grid", adm_nm: "far-grid" },
              },
            ],
          },
        }), { status: 200 });
      }

      if (requestUrl.includes("/population")) {
        return new Response(JSON.stringify({
          statsRows: [
            { adm_cd: "near-grid", adm_nm: "near-grid", tot_ppltn: 42 },
            { adm_cd: "far-grid", adm_nm: "far-grid", tot_ppltn: 100 },
          ],
        }), { status: 200 });
      }

      return originalFetch(url);
    };

    try {
      const layer = await sgis.fetchSgisGridLayer({
        proxyPath: "/api/sgis",
        admCd: "11",
        gridLevelDiv: "500m",
        year: 2023,
        metricId: "tot_ppltn",
        color: "#1d78c8",
        scope: "school",
        scopeLabel: "현재 주변 500m 격자",
        spatialFilter: {
          center: { lat: 37.5665, lng: 126.978 },
          radiusMeters: 1200,
        },
      });
      return layer.featureCollection.features.length;
    } finally {
      window.fetch = originalFetch;
    }
  });

  expect(featureCount).toBe(1);
});

test("student can draw geometries, save project, and restore buffer state", async ({ page }) => {
  page.on("dialog", (dialog) => dialog.accept());

  await waitForWorkspace(page);
  await page.click("#sidebarPanelTabs [data-sidebar-panel='layers']");
  await expect(page.locator("#layerStackCard")).toBeVisible();

  const map = page.locator("#map");

  await page.fill("#studentLayerNameField", "Field Survey");
  await page.fill("#studentLayerDescriptionField", "Student collected vector features");
  await page.click("#studentLayerForm button[type='submit']");
  await page.click("#layerAddButton");
  await page.click("#layerAddSheet [data-layer-add-choice='draw']");

  const layerCard = page.locator("#studentLayerList .layer-card").first();
  await expect(layerCard).toContainText("Field Survey");
  await expect(layerCard).toContainText("0개");
  await expect(page.locator("#mapLayerHub")).toContainText("Field Survey");
  await expect(page.locator("#drawToolbar [data-draw-tool='point']")).toBeEnabled();
  await expect(page.locator("#drawToolbar [data-draw-tool='line']")).toBeEnabled();
  await expect(page.locator("#drawToolbar [data-draw-tool='polygon']")).toBeEnabled();

  await page.click("#drawToolbar [data-draw-tool='point']");
  await map.click({ position: { x: 220, y: 220 } });
  await expect(layerCard).toContainText("1개");

  await map.click({ position: { x: 245, y: 220 } });
  await expect(layerCard).toContainText("2개");
  await page.click("#sidebarPanelTabs [data-sidebar-panel='layers']");
  await layerCard.locator("summary", { hasText: "더보기" }).click();
  await expect(layerCard.locator("[data-action='delete-student-feature']")).toHaveCount(2);
  await layerCard.locator("[data-action='delete-student-feature']").last().click();
  await expect(layerCard).toContainText("1개");

  await map.click({ position: { x: 245, y: 220 } });
  await expect(layerCard).toContainText("2개");
  await expect(page.locator("#legend [data-legend-action='delete-student-feature']")).toHaveCount(2);
  await page.locator("#legend [data-legend-action='delete-student-feature']").last().click();
  await expect(layerCard).toContainText("1개");

  await page.click("#drawToolbar [data-draw-tool='line']");
  await map.click({ position: { x: 280, y: 220 } });
  await map.click({ position: { x: 360, y: 280 } });
  await page.click("#completeDraftButton");
  await expect(layerCard).toContainText("2개");
  await expect(layerCard).toContainText("총 길이");

  await page.click("#drawToolbar [data-draw-tool='polygon']");
  await map.click({ position: { x: 260, y: 330 } });
  await map.click({ position: { x: 340, y: 330 } });
  await map.click({ position: { x: 300, y: 410 } });
  await page.click("#completeDraftButton");
  await expect(layerCard).toContainText("3개");
  await expect(layerCard).toContainText("총 면적");

  await page.click("#sidebarPanelTabs [data-sidebar-panel='student']");
  await page.click("#drawToolbar [data-draw-tool='select']");
  await map.click({ position: { x: 320, y: 250 } });
  await expect(page.locator("#selectedFeatureMeasurement")).toContainText("길이");

  await map.click({ position: { x: 300, y: 360 } });
  await expect(page.locator("#selectedFeatureMeasurement")).toContainText("면적");

  await map.click({ position: { x: 220, y: 220 } });
  await page.fill("#pointTitleField", "Gate hazard");
  await page.fill("#pointNoteField", "Vehicle and pedestrian paths intersect.");
  await page.fill("#featureValueLabelField", "Traffic count");
  await page.fill("#featureValueField", "35");
  await page.fill("#featureValueUnitField", "cars/10min");
  await page.selectOption("#featureSeverityField", "3");
  await page.click("#saveSelectedFeatureButton");
  await expect(layerCard).toContainText("Traffic count: 35 cars/10min");
  await expect(page.locator("#mapLayerHub")).toContainText("Traffic count: 35 cars/10min");

  await page.fill("#featureBufferRadiusField", "120");
  await page.click("#createFeatureBufferButton");

  await page.click("#drawToolbar [data-draw-tool='measure-line']");
  await map.click({ position: { x: 420, y: 220 } });
  await map.click({ position: { x: 520, y: 220 } });
  await page.click("#completeDraftButton");
  await expect(page.locator("#measurementTitle")).toContainText("거리");
  await expect(page.locator("#measurementValue")).toContainText("총 거리");

  await page.click("#drawToolbar [data-draw-tool='measure-area']");
  await map.click({ position: { x: 430, y: 320 } });
  await map.click({ position: { x: 520, y: 320 } });
  await map.click({ position: { x: 480, y: 390 } });
  await page.click("#completeDraftButton");
  await expect(page.locator("#measurementTitle")).toContainText("면적");
  await expect(page.locator("#measurementValue")).toContainText("면적");
  await expect(page.locator("#summaryInsightList")).toContainText("버퍼");
  await expect(page.locator("#summaryInsightList")).toContainText("최근 면적 측정 결과");
  await expect(page.locator("#presentationSummaryField")).toHaveValue(/면적/);

  await page.fill("#projectNameField", "GIS Test Project");
  await page.click("#saveProjectButton");
  await expect(page.locator("#savedProjectSelectField option")).toHaveCount(1);
  await expect(page.locator("#savedProjectHint")).toContainText("GIS Test Project");

  await page.click("#sidebarPanelTabs [data-sidebar-panel='layers']");
  await expect(page.locator("#importedPublicLayerList")).toContainText("Gate hazard 120m");
  await expect(page.locator("#importedPublicLayerList")).toContainText("면적");
  await expect(page.locator("#legend")).toContainText("Gate hazard 120m");

  await page.click("#sidebarPanelTabs [data-sidebar-panel='student']");
  await page.click("#drawToolbar [data-draw-tool='delete']");
  await map.click({ position: { x: 220, y: 220 } });
  await page.click("#sidebarPanelTabs [data-sidebar-panel='layers']");
  await expect(layerCard).toContainText("2개");

  await page.click("#sidebarPanelTabs [data-sidebar-panel='student']");
  await page.click("#loadSavedProjectButton");
  await page.click("#sidebarPanelTabs [data-sidebar-panel='layers']");
  await expect(layerCard).toContainText("3개");

  await page.click("#sidebarPanelTabs [data-sidebar-panel='student']");
  await expect(page.locator("#pointTitleField")).toBeDisabled();

  await page.click("#sidebarPanelTabs [data-sidebar-panel='layers']");
  await expect(page.locator("#importedPublicLayerList")).toContainText("Gate hazard 120m");
  await expect(page.locator("#importedPublicLayerList")).toContainText("면적");
});

test("measurement result can be saved back as a student layer", async ({ page }) => {
  await waitForWorkspace(page);
  const map = page.locator("#map");

  await page.click("#layerAddButton");
  await page.click("#layerAddSheet [data-layer-add-choice='draw']");
  await page.click("#drawToolbar [data-draw-tool='measure-line']");
  await map.click({ position: { x: 300, y: 240 } });
  await map.click({ position: { x: 410, y: 240 } });
  await expect(page.locator("#undoDraftPointButton")).toBeEnabled();
  await page.click("#completeDraftButton");
  await expect(page.locator("#measurementTitle")).toContainText("거리");
  await expect(page.locator("#saveMeasurementLayerButton")).toBeEnabled();

  await page.click("#saveMeasurementLayerButton");
  await expect(page.locator("#mapLayerHub")).toContainText("거리 측정");
  await page.click("#sidebarPanelTabs [data-sidebar-panel='layers']");
  await expect(page.locator("#studentLayerList")).toContainText("거리 측정");
  await expect(page.locator("#studentLayerList")).toContainText("총 길이");
});

test("student can create a grid-based suitability score layer", async ({ page }) => {
  await page.addInitScript(() => {
    const storageScope = `${"탐색 중심"}-${Number(37.5665).toFixed(4)}-${Number(126.978).toFixed(4)}-${1200}`
      .replace(/[^\w.-]+/g, "-")
      .toLowerCase();
    window.localStorage.clear();
    window.localStorage.setItem(
      `school-neighborhood-gis-public-layers-v1:${storageScope}`,
      JSON.stringify([
        {
          id: "grid-suitability-test",
          name: "SGIS 총인구 2023 · 500m 격자",
          description: "테스트용 격자 레이어",
          color: "#1d78c8",
          opacity: 1,
          visible: true,
          scope: "both",
          sourceKind: "sgis",
          sourceLabel: "SGIS grid/data.geojson",
          featureCollection: {
            type: "FeatureCollection",
            features: [
              {
                type: "Feature",
                geometry: {
                  type: "Polygon",
                  coordinates: [[
                    [126.976, 37.565],
                    [126.98, 37.565],
                    [126.98, 37.568],
                    [126.976, 37.568],
                    [126.976, 37.565],
                  ]],
                },
                properties: {
                  title: "500m 격자 A",
                  isGridFeature: true,
                  gridLevelDiv: "500m",
                  gridSizeLabel: "500m",
                  gridCode: "A",
                  gridIndex: 1,
                  metricLabel: "총인구",
                  metricValue: 80,
                  metricUnit: "명",
                  metricDigits: 0,
                  metricYear: "2023",
                  metricSourceLabel: "테스트 통계",
                },
              },
              {
                type: "Feature",
                geometry: {
                  type: "Polygon",
                  coordinates: [[
                    [126.99, 37.575],
                    [126.994, 37.575],
                    [126.994, 37.578],
                    [126.99, 37.578],
                    [126.99, 37.575],
                  ]],
                },
                properties: {
                  title: "500m 격자 B",
                  isGridFeature: true,
                  gridLevelDiv: "500m",
                  gridSizeLabel: "500m",
                  gridCode: "B",
                  gridIndex: 2,
                  metricLabel: "총인구",
                  metricValue: 20,
                  metricUnit: "명",
                  metricDigits: 0,
                  metricYear: "2023",
                  metricSourceLabel: "테스트 통계",
                },
              },
            ],
          },
        },
      ]),
    );
    window.localStorage.setItem(
      `school-neighborhood-gis-student-layers-v5:${storageScope}`,
      JSON.stringify([
        {
          id: "student-access-test",
          name: "학생 접근성 지점",
          geometryType: "point",
          color: "#d94862",
          opacity: 1,
          visible: true,
          description: "테스트용 학생 지점",
          source: "manual",
          features: [
            {
              id: "student-access-feature-1",
              title: "버스정류장",
              note: "접근성 기준 지점",
              geometryType: "point",
              coordinates: [[126.978, 37.5665]],
              properties: { severity: "2", severityLabel: "보통" },
            },
          ],
        },
      ]),
    );
  });

  await page.goto("/?r=playwright-suitability", {
    waitUntil: "domcontentloaded",
  });
  await expect(page.locator("#map")).toBeVisible();
  await page.waitForTimeout(2500);

  await page.click("#sidebarPanelTabs [data-sidebar-panel='analysis']");
  await expect(page.locator("#analysisCard")).toBeVisible();
  await expect(page.locator("#suitabilityGridLayerField")).toHaveValue("grid-suitability-test");
  await expect(page.locator("#suitabilityStudentLayerField")).toHaveValue("student-access-test");
  await page.selectOption("#suitabilityTemplateField", "access");
  await page.click("#createSuitabilityButton");

  await expect(page.locator("#suitabilityResult")).toContainText("접근성 좋은 곳 입지점수");
  await expect(page.locator("#suitabilityResult")).toContainText("1위");
  await expect(page.locator("#mapLayerHub")).toContainText("입지점수 분석");

  await page.click("#sidebarPanelTabs [data-sidebar-panel='layers']");
  await expect(page.locator("#importedPublicLayerList")).toContainText("접근성 좋은 곳 입지점수");
  await expect(page.locator("#importedPublicLayerList")).toContainText("입지점수");
  await expect(page.locator("#importedPublicLayerList")).toContainText("상위 후보");
});
