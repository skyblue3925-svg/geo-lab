---
id: shape-terrain-engine
type: synthesis
layer: curated
status: seed
created: 2026-04-12
updated: 2026-04-12
tags:
  - synthesis
  - engine
  - current-shape
---

# Terrain Engine Current Shape

## 현재 구현 형태

- `engine/ideal_landforms.py` 는 삼각주, 선상지, 곡류, U자곡, V자곡 등 교과서형 지형을 직접 기하학적으로 생성한다.
- `engine/system.py` 의 `EarthSystem` 은 hydrology, erosion, lateral erosion, mass movement, climate, wave, glacier, wind kernel을 묶는 통합 엔진이다.
- `engine/lem/` 아래에는 `advanced_physics.py`, `climate.py`, `human.py`, `visualization.py` 같은 확장 LEM 모듈이 남아 있다.
- `engine/river/` 는 delta, meander, v_valley 등 하천 계열 모델을 별도 폴더로 둔다.
- `engine/analysis.py` 와 `engine/dem_io.py` 는 Research 계열 surface와 연결될 가능성이 높다.

## 확인 근거

- `engine/ideal_landforms.py`
- `engine/system.py`
- `engine/lem/`
- `engine/river/`
- [[Latest Repository Snapshot]]
- recent git log의 2025-12 LEM/physics 관련 커밋들

## 구조적 긴장/리스크

- 동일한 지형을 `ideal shape`, `analytical helper`, `process simulation` 세 방식으로 다룰 수 있어 경계가 겹친다.
- 엔진 breadth는 크지만, 사용자 surface별 canonical 사용 경로가 즉시 명료하지 않다.
- 레거시와 현재 helper가 병존해 테스트와 문서가 계속 따라가야 한다.

## 다음에 볼 것

- `engine/simple_lem.py`
- `engine/analysis.py`
- `app/utils/lab_model.py`
- `pages/4_🔬_Research.py`
