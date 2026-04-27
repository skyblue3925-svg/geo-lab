---
id: shape-geo-lab-climate-lab
type: synthesis
layer: curated
status: seed
created: 2026-04-12
updated: 2026-04-12
tags:
  - synthesis
  - streamlit
  - climate
  - current-shape
aliases:
  - Climate Lab Current Shape
---

# Geo-Lab Climate Lab Current Shape

## 현재 구현 형태

- `pages/5_☁️_Climate.py` 는 Streamlit climate surface shell이다.
- `engine.climate_global.GlobalClimateEngine` 이 월, 위도, ITCZ, 기압, 바람, 강수, 단순화된 쾨펜 구분을 계산한다.
- page는 `학생 단순모드` 와 `교사 상세모드` 를 분리하고, 레이어 토글과 animation control은 주로 교사 모드에서 열어 둔다.
- simulation mode는 `이론 모델` 과 `현실 근사 모델` 두 가지다.
- `case_climate_pending`, `case_climate_month`, `case_climate_mode` 를 통해 Case Mode에서 climate preset을 1회 적용한다.

## 확인 근거

- `pages/5_☁️_Climate.py`
- `engine/climate_global.py`
- [[Latest Repository Snapshot]]

## 구조적 긴장/리스크

- [[Koppen Climate Lab]] 이라는 별도 정적 앱과 이름/주제가 겹치므로 역할 경계를 명확히 해야 한다.
- `현실 근사 모델` 도 여전히 교육용 simplified model이며, 실제 climatology로 과해석하면 안 된다.
- 애니메이션, 2D/3D, teaching mode가 한 page에 모여 있어 옵션 폭이 커질 수 있다.

## 다음에 볼 것

- [[Koppen Climate Lab]]
- [[Geo-Lab Case Mode]]
- `engine/climate_global.py`
