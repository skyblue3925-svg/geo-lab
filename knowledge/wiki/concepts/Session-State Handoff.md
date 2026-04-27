---
id: concept-session-state-handoff
type: concept
layer: curated
status: seed
created: 2026-04-12
updated: 2026-04-12
tags:
  - concept
  - streamlit
  - handoff
aliases:
  - session-state handoff
---

# Session-State Handoff

## 핵심 개념

Geo-Lab Streamlit app의 여러 surface는 명시적 URL routing보다 `st.session_state` 를 이용한 handoff를 자주 사용한다.

## 확인된 handoff 예

- `Gallery -> Lab`
  - `gallery_lab_preset`
- `Case Mode -> Research Lab`
  - `research_elevation`
  - `research_params`
- `Case Mode -> Climate Lab`
  - `case_climate_month`
  - `case_climate_mode`
  - `case_climate_pending`

## 장점

- 사용자가 같은 세션 안에서 바로 이어서 탐구할 수 있다.
- preset 기반 수업 시연 흐름을 빠르게 만든다.

## 리스크

- 상태 이름이 암묵적이라 흐름을 코드만 보고 파악하기 어렵다.
- rerun 타이밍과 초기화 규칙에 따라 회귀가 생기기 쉽다.
- 위키 current-shape note에서 handoff를 명시하지 않으면 surface 간 연결이 잘 안 보인다.

## 관련 note

- [[Geo-Lab Streamlit Surface Map]]
- [[Geo-Lab Gallery Current Shape]]
- [[Geo-Lab Case Mode Current Shape]]
- [[Geo-Lab Research Lab Current Shape]]
- [[Geo-Lab Climate Lab Current Shape]]
