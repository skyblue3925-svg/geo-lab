---
id: map-geo-lab-streamlit-surface
type: map
layer: curated
status: active
created: 2026-04-12
updated: 2026-04-12
tags:
  - map
  - streamlit
  - surfaces
aliases:
  - streamlit-surface-map
---

# Geo-Lab Streamlit Surface Map

## 목적

이 map은 [[Geo-Lab Streamlit App]] 안에서 2차 surface가 어떻게 갈라지고 다시 합류하는지 보여준다.

## 핵심 surface

- [[Geo-Lab Overview Guide]]
- [[Geo-Lab Gallery]]
- [[Geo-Lab Lab]]
- [[Geo-Lab Research Lab]]
- [[Geo-Lab Climate Lab]]
- [[Geo-Lab Case Mode]]
- [[Geo-Lab High School Geography Atlas]]
- [[Geo-Lab Higher Ed Portal]]

## 연결 구조

### Home 및 진입선

- `Home -> Overview`
- `Home -> Gallery`
- `Home -> Lab`
- `Home -> Higher Ed`

### 교실 안내 흐름

- `Overview -> High School Geography Atlas`
- `Overview -> Lab`
- `Overview -> Higher Ed`
- `High School Geography Atlas -> Gallery`
- `High School Geography Atlas -> Lab`

### Gallery 기반 preset 흐름

- `Gallery -> Lab` via preset queue
- `Gallery -> Research Lab` via showcase / atlas reference
- `Gallery -> High School Geography Atlas` via 수업 사례 링크

### 대학 및 연구 흐름

- `Higher Ed Portal -> Research Lab`
- `Higher Ed Portal -> Case Mode`
- `Higher Ed Portal -> Gallery`

### Case Mode handoff

- `Case Mode -> Research Lab` via [[Session-State Handoff]]
- `Case Mode -> Climate Lab` via climate preset handoff

### 분석 및 provenance 흐름

- `Research Lab <- uploaded DEM`
- `Research Lab <- synthetic DEM`
- `Research Lab <- case-mode DEM`
- `Lab <- synthetic terrain preset`
- `Climate Lab <- case preset climate state`

## 경계와 역할

- [[Geo-Lab Overview Guide]] 는 교실용 안내와 진입 경로 정렬을 맡는다.
- [[Geo-Lab Gallery]] 는 showcase, preset, atlas 라우팅을 맡는다.
- [[Geo-Lab Lab]] 은 학생 및 교사용 실험 surface다.
- [[Geo-Lab Research Lab]] 은 분석과 비교 surface다.
- [[Geo-Lab Climate Lab]] 은 기후 시뮬레이션과 교육용 시각화를 맡는다.
- [[Geo-Lab Case Mode]] 는 narrative / policy activity surface다.
- [[Geo-Lab High School Geography Atlas]] 는 고등학교 수업용 canonical teaching gateway다.
- [[Geo-Lab Higher Ed Portal]] 은 대학 및 연구용 routing gateway다.

## 관련 개념

- [[합성 DEM과 관측 DEM]]
- [[Provenance와 해석 경계]]
- [[Session-State Handoff]]
