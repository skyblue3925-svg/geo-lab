---
id: shape-geo-lab-research-lab
type: synthesis
layer: curated
status: seed
created: 2026-04-12
updated: 2026-04-12
tags:
  - synthesis
  - streamlit
  - research
  - current-shape
aliases:
  - Research Lab Current Shape
---

# Geo-Lab Research Lab Current Shape

## 현재 구현 형태

- `pages/4_🔬_Research.py` 는 `시뮬레이션 생성` 과 `DEM 업로드` 두 데이터 진입 방식을 지원한다.
- main tab은 `3D View`, `Profile`, `Hypsometric`, `Slope`, `DEM Compare`, `Export` 의 6개다.
- `engine.analysis` 와 `engine.dem_io` 가 프로파일 추출, 경사/곡률/HI 계산, DEM 로드/내보내기를 담당한다.
- `app.utils.research_compare` 가 reference DEM 정렬, RMSE/MAE/상관성/HI 차이 요약, comparison report export를 담당한다.
- `params["source"]` 에 따라 업로드 DEM, simulation DEM, case_mode DEM을 구분하고 provenance panel 문구를 달리한다.
- export 쪽은 DEM 자체 export 외에도 comparison report의 JSON/Markdown/CSV를 별도 산출한다.

## 확인 근거

- `pages/4_🔬_Research.py`
- `engine/analysis.py`
- `engine/dem_io.py`
- `app/utils/research_compare.py`
- `app/utils/mode_helpers.py`
- [[Latest Repository Snapshot]]

## 구조적 긴장/리스크

- 관측 DEM, 이상화 DEM, Case Mode 결과를 한 surface에서 다루므로 사용자가 데이터 출처 차이를 놓치기 쉽다.
- comparison은 shape 정렬과 bilinear resampling을 쓰므로, 실제 extent/CRS reconciliation 없이 과잉 해석하면 위험하다.
- 기능이 많아졌지만 여전히 page 단일 파일 중심이라 세부 workflow 분리가 덜 된 상태다.

## 다음에 볼 것

- [[Geo-Lab Case Mode]]
- [[Geo-Lab Higher Ed Portal]]
- `tests/test_research_compare.py`
- `engine/dem_io.py`
