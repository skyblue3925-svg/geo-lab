---
id: entity-terrain-engine
type: entity
layer: curated
status: seed
created: 2026-04-12
updated: 2026-04-12
tags:
  - entity
  - engine
  - terrain
---

# Terrain Engine

## 정체성

Geo-lab 전체의 지형 생성, 분석, 시뮬레이션, 시각화 기반을 제공하는 엔진 계층이다.

## 주요 책임

- 이상적 지형 기하 생성
- 교육용 LEM 및 process simulation
- hydrology, erosion, deposition, climate, glacier, wind 등 kernel 제공
- DEM 분석과 비교를 위한 분석 함수 제공

## 핵심 경로

- `engine/ideal_landforms.py`
- `engine/simple_lem.py`
- `engine/system.py`
- `engine/analysis.py`
- `engine/lem/`
- `engine/river/`

## 관련 note

- [[Terrain Engine Current Shape]]
- [[Geo-Lab Streamlit App]]
- [[Project Map]]
- [[Current State Synthesis]]

## 관찰 메모

- 단일 canonical engine 하나만 있는 형태가 아니라, `ideal geometry`, `LEM`, `unified EarthSystem` 축이 병존한다.
