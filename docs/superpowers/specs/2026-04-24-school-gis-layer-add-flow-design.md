# School GIS Layer Add Flow Design

## Summary

The selected direction is Option A: one mobile-first "레이어 추가" entry point.

The School Neighborhood GIS app should feel like a map-first classroom WebGIS, not a panel-heavy GIS tool gallery. The first visible action should be adding a layer. The user should then choose between two plain-language paths:

- 통계자료 가져오기
- 직접 조사해서 그리기

Everything else is secondary and should appear only after it helps the current task.

## Product Goal

Students and teachers use Kakao Map with SGIS statistics and student-made vector layers to investigate local neighborhood questions. The core journey is:

1. Find or confirm the local area.
2. Add a public statistics layer.
3. Add a student-created layer.
4. Compare the overlap.
5. Write a short interpretation.

This is not a safety reporting app and not a full GIS workbench.

## Current Problem

The existing implementation already has the required features, but the entry points are scattered across separate panels:

- 공공데이터
- 내 레이어
- 분석
- 레이어

On mobile, this still feels like navigating a tool inventory. The map is visible, but students must understand the app's internal feature categories before they can simply add and compare layers.

## Chosen UX Direction

### Primary Entry

Expose one dominant action near the map:

- 레이어 추가

When opened, it shows a bottom sheet with exactly two primary choices:

- 통계자료 가져오기
- 직접 조사해서 그리기

The previous panel categories remain available as internal organization, but they should not be the default user-facing model.

### Public Statistics Flow

The public data path should use student-facing choices in this order:

1. 무엇을 볼까
   - 인구
   - 나이
   - 사업체
   - 가구
   - 기타
2. 어떻게 볼까
   - 격자
   - 행정구역
3. 어디까지 볼까
   - 현재 화면
   - 시군구
   - 읍면동

The existing SGIS controls can remain underneath this flow, but the default path should not expose raw SGIS terminology, administrative codes, URL import, or advanced color/year settings first.

### Student Drawing Flow

The drawing toolbar should be hidden by default.

When the user chooses 직접 조사해서 그리기:

1. If no student layer exists, create 학생 레이어 1 automatically.
2. Open drawing mode.
3. Show point, line, and polygon tools on the map.
4. Keep select, measurement, delete, complete, cancel, and active layer controls available only while drawing or editing.

This keeps the default surface quiet and makes drawing feel like the active task rather than a permanent toolbar.

### Layer Management

Layer cards should default to a compact form:

- name
- visible on/off
- opacity
- edit

Secondary operations should move behind a "더보기" disclosure:

- delete
- export
- object list
- move up/down
- advanced metadata

The map layer hub should summarize active layers and offer:

- 공공 추가
- 그리기
- 전체 관리

### Analysis

Analysis should appear as the next step after at least one public layer and one student layer exist. It should be presented as 겹쳐 보기 / 분석, not as a permanent first-level tab.

Before prerequisites are met, analysis can be hinted but not compete with layer creation.

## Mobile Layout

The mobile first viewport should show:

1. compact header/status
2. map
3. one layer-add action
4. small active-layer summary or legend/status feedback

Tool panels should open as bottom sheets. The bottom sheet should be task-specific:

- layer choice sheet
- statistics choice sheet
- drawing tool sheet
- compact layer management sheet

## Desktop Layout

Desktop can keep a side panel, but the side panel should mirror the task model instead of exposing four equal tabs. The default side panel should be the same layer-add flow, with advanced management lower or collapsed.

The map remains the dominant area.

## Feedback Rules

Every meaningful action should create at least one immediate visible response:

- map changes
- legend changes
- active layer summary changes
- status notice changes

Kakao-only map overlay controls should clearly report when the current provider cannot apply them. In Leaflet fallback, the UI should avoid implying that Kakao overlay layers were applied.

## Files Expected To Change

Keep implementation scoped to:

- `apps/school-neighborhood-gis/index.html`
- `apps/school-neighborhood-gis/styles.css`
- `apps/school-neighborhood-gis/app.js`
- `apps/school-neighborhood-gis/presentation/public-panel.js`
- `apps/school-neighborhood-gis/presentation/student-panel.js`
- `apps/school-neighborhood-gis/presentation/draw-toolbar.js`
- `apps/school-neighborhood-gis/presentation/student-workspace-controller.js`
- `apps/school-neighborhood-gis/tests/student-geometry.spec.js`

Other repository changes are unrelated and should not be mixed into this work.

## Testing Expectations

Use narrow verification first:

- `node --check` for touched JavaScript files
- `npx playwright test --config=apps/school-neighborhood-gis/playwright.local.config.js --project=chromium`

Add or update Playwright coverage for:

- the default draw toolbar is not shown as a permanent first-screen toolbar
- clicking layer add exposes only the two primary choices
- choosing drawing creates or activates a student layer and shows drawing tools
- choosing public statistics opens the simplified public-data choice flow
- compact layer cards hide destructive/export/object-list controls behind disclosure

## Non-Goals

- Do not add new GIS analysis algorithms.
- Do not redesign the whole visual brand.
- Do not change SGIS proxy behavior unless required by the simplified flow.
- Do not touch unrelated Geo-Lab, Koppen, Streamlit, terrain, or wiki files.
- Do not present the app as a school safety reporting workflow.
