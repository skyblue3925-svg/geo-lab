---
id: shape-geo-lab-case-mode
type: synthesis
layer: curated
status: seed
created: 2026-04-12
updated: 2026-04-12
tags:
  - synthesis
  - streamlit
  - cases
  - current-shape
aliases:
  - Case Mode Current Shape
---

# Geo-Lab Case Mode Current Shape

## 현재 구현 형태

- `pages/6_🧭_케이스_모드.py` 는 `CaseSpec` 라이브러리를 읽어 사례별 narrative, evidence, timeline, policy option을 보여준다.
- `app/cases/travel_cases.py` 는 evidence item, timeline, policy option, real case card를 dataclass로 구조화한다.
- baseline / intervention 시뮬레이션은 `SimpleLEM` 과 ideal landform 생성기를 사용해 A/B 비교를 만든다.
- page는 `기본 DEM을 Research Lab으로 보내기` 버튼으로 `research_elevation` 과 `research_params` 를 session state에 넣어 Research로 handoff 한다.
- `기후 프리셋을 Climate Lab으로 보내기` 버튼으로 월/모드 preset도 세션에 저장한다.
- 결과물은 차이맵 PNG, evidence table, 정책 워크시트, JSON 지표를 묶어 zip으로 내려받을 수 있다.
- 문서와 UI 모두 `수업 빠른모드` 와 근거 확보 흐름을 의식한다.

## 확인 근거

- `pages/6_🧭_케이스_모드.py`
- `app/cases/travel_cases.py`
- [docs/CASE_MODE_USAGE.md](../../../docs/CASE_MODE_USAGE.md)
- [[Latest Repository Snapshot]]

## 구조적 긴장/리스크

- 실제 지역 앵커와 synthetic simulation을 함께 쓰므로, 현실 데이터와 학습용 모델의 경계를 계속 명시해야 한다.
- Research/Climate handoff가 session state 의존이라 흐름이 암묵적이다.
- 수업 운영, 정책 비교, export가 한 page에 많이 모여 있어 유지보수 시 분리 후보가 된다.

## 다음에 볼 것

- [[Geo-Lab Research Lab]]
- `tests/test_world_terrain_cases.py`
- `tests/test_research_compare.py`
- [docs/CASE_WORKSHEET_TEMPLATES.md](../../../docs/CASE_WORKSHEET_TEMPLATES.md)
