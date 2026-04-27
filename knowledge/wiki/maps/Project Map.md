---
id: project-map
type: map
layer: curated
status: active
created: 2026-04-12
updated: 2026-04-12
tags:
  - map
  - repo
aliases:
  - project-map
---

# Project Map

## 한눈에 보기

Geo-lab은 하나의 Streamlit 앱만 있는 저장소라기보다, 교육용 지형 및 기후 워크스페이스와 별도 side app이 공존하는 mono-repo 성격에 가깝다.

## 최상위 구조

- `app.py`
  - 현재 canonical Streamlit entrypoint
- `pages/`
  - Overview, Gallery, Lab, Research, Climate, Case Mode, Higher Ed, High School Geography
- `app/`
  - shared view, component, utility, theory, atlas helper
- `engine/`
  - 지형 생성, ideal landforms, LEM, hydrology, analysis, climate, river physics
- `apps/koppen-climate-lab/`
  - 정적 기후 교육 앱
- `apps/school-neighborhood-gis/`
  - 생활권 GIS 웹앱
- `docs/`
  - 수업 운영, 배포, runbook, subagent 문서
- `tests/`
  - Python test와 Playwright / E2E
- `knowledge/`
  - Obsidian / LLM wiki layer

## 제품 축

### 1. Classroom Core

- [[Geo-Lab Streamlit App]]
- [[Terrain Engine]]
- 세부 surface map: [[Geo-Lab Streamlit Surface Map]]

주요 흐름:

- Home / Overview
- Gallery / Atlas / Preset routing
- Lab / Research / Climate
- Case Mode / Higher Ed / High School Geography

### 2. Static Side Apps

- [[Koppen Climate Lab]]
- [[School Neighborhood GIS]]

이 둘은 별도 앱 성격이 강하고, 배포 문서와 운영 축도 Streamlit core와 부분적으로 분리되어 있다.

### 3. Knowledge and Operations

- `docs/` 는 수업 및 운영 문서를 유지한다.
- `knowledge/` 는 durable note와 synthesis를 유지한다.
- `docs/subagents/` 는 dirty worktree와 병렬 작업 규칙을 제공한다.

## 읽기 포인트

- `app/home_view.py`
  - 메인 홈과 사용자 진입 분기
- `app/high_school_geography_view.py`
  - 고등학교 atlas와 topic routing
- `pages/1_📖_Gallery.py`
  - showcase, preset, atlas routing
- `pages/2_🗺️_Overview.py`
  - 교실용 안내 surface
- `pages/3_🧪_Lab.py`
  - 학생 및 교사용 실험 surface
- `pages/5_☁️_Climate.py`
  - Streamlit climate surface
- `engine/ideal_landforms.py`
  - 이상적 지형 생성
- `engine/system.py`
  - Project Genesis 통합 엔진
- `apps/school-neighborhood-gis/`
  - SGIS 기반 생활권 GIS
- `apps/koppen-climate-lab/`
  - precomputed climate layer 기반 학습 앱

## 추천 읽기 경로

1. [[Current State Synthesis]]
2. [[Geo-Lab Streamlit App Current Shape]]
3. [[Geo-Lab Streamlit Surface Map]]
4. [[Terrain Engine Current Shape]]
5. [[School Neighborhood GIS Current Shape]]
6. [[Koppen Climate Lab Current Shape]]
