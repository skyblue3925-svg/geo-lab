---
id: shape-koppen-climate-lab
type: synthesis
layer: curated
status: seed
created: 2026-04-12
updated: 2026-04-12
tags:
  - synthesis
  - climate
  - current-shape
---

# Koppen Climate Lab Current Shape

## 현재 구현 형태

- 정적 HTML/CSS/ES module 기반 classroom app이다.
- root runtime 파일 외에 `app-state.mjs`, `dashboard-scene.mjs`, `map-render-view.mjs`, `selection-card-view.mjs`, `driver-insights-view.mjs` 등 UI 모듈이 세분화되어 있다.
- `data/` 아래에는 Koppen-Geiger, WorldClim, ETOPO 계열 precomputed asset과 geojson이 들어 있다.
- `scripts/` 아래에는 climate grid와 elevation grid를 빌드하는 도구가 있다.

## 확인 근거

- [apps/koppen-climate-lab/README.md](../../../apps/koppen-climate-lab/README.md)
- [docs/CLOUDFLARE_PAGES_KOPPEN.md](../../../docs/CLOUDFLARE_PAGES_KOPPEN.md)
- [[Latest Repository Snapshot]]
- recent git log의 2026-03-20 Koppen 관련 커밋 3건
- `apps/koppen-climate-lab/` 폴더 구조

## 구조적 긴장/리스크

- large static dataset과 runtime module이 함께 진화하므로 배포 산출물과 원천 데이터의 경계를 계속 관리해야 한다.
- 교실용 정적 앱이지만 데이터 빌드 파이프라인이 있어 완전한 단순 정적 사이트는 아니다.
- root repo의 Streamlit 중심 narrative와는 별도 cadence로 발전할 수 있다.

## 다음에 볼 것

- `apps/koppen-climate-lab/climate-model.mjs`
- `apps/koppen-climate-lab/lesson-data.mjs`
- `apps/koppen-climate-lab/data/`
- `apps/koppen-climate-lab/scripts/`
