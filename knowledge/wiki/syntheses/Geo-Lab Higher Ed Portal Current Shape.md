---
id: shape-geo-lab-higher-ed-portal
type: synthesis
layer: curated
status: seed
created: 2026-04-12
updated: 2026-04-12
tags:
  - synthesis
  - streamlit
  - higher-ed
  - current-shape
aliases:
  - Higher Ed Current Shape
---

# Geo-Lab Higher Ed Portal Current Shape

## 현재 구현 형태

- `pages/7_🎓_Higher_Ed.py` 는 lightweight portal page다.
- audience card 3종, quick link section 3종, featured world cases, 운영 원칙 텍스트로 구성된다.
- direct target은 `Research Lab`, `Gallery Atlas`, `케이스 모드` 다.
- featured world case 데이터는 `app/utils/world_terrain_cases.py` 에서 온다.
- page 본문은 메인 홈이 `고등학교 수업 우선` 이고, 이 포털은 `대학·연구 확장 흐름` 이라는 분리를 명시한다.

## 확인 근거

- `pages/7_🎓_Higher_Ed.py`
- `app/utils/world_terrain_cases.py`
- [[Latest Repository Snapshot]]

## 구조적 긴장/리스크

- 이 page 자체는 얇지만, 어떤 surface를 canonical higher-ed entry로 볼지에 대한 제품 판단이 계속 반영된다.
- Home과 역할이 겹치지 않도록 메시지 경계를 유지해야 한다.
- target page명이나 handoff 구조가 바뀌면 portal copy도 바로 stale 될 수 있다.

## 다음에 볼 것

- [[Geo-Lab Research Lab]]
- [[Geo-Lab High School Geography Atlas]]
- [[Geo-Lab Streamlit Surface Map]]
