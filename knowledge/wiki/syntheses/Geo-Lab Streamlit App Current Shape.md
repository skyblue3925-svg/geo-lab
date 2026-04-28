---
id: shape-geo-lab-streamlit-app
type: synthesis
layer: curated
status: active
created: 2026-04-12
updated: 2026-04-12
tags:
  - synthesis
  - streamlit
  - current-shape
---

# Geo-Lab Streamlit App Current Shape

## 현재 구현 상태

- `app.py` 는 page config를 설정하고 `render_home_page()` 를 호출하는 현재 canonical entrypoint다.
- `app/home_view.py` 는 메인 홈을 `교사용 시작`, `학생 탐구 시작`, `고등교육/연구 포털` 로 나누고, 방문자 카운트는 Supabase 또는 로컬 JSON fallback으로 처리한다.
- `pages/` 는 현재 최소 8개의 surface를 가진다.
  - Overview
  - Gallery
  - Lab
  - Research
  - Climate
  - Case Mode
  - Higher Ed
  - High School Geography
- `pages/2_🗺️_Overview.py` 는 교실 상황에서 어디로 들어가야 하는지 설명하는 안내 surface다.
- `pages/1_📖_Gallery.py` 는 showcase 카드, preset queue, world terrain case atlas를 제공하는 catalog surface다.
- `pages/5_☁️_Climate.py` 는 student / teacher mode와 2D / 3D 선택지를 가진 Streamlit climate surface다.
- `pages/3_🧪_Lab.py` 는 학생/교사 모드, session-state preset, animation preview, SimpleLEM helper와 결합된 핵심 실험 surface다.
- `app/high_school_geography_view.py` 는 topic spec, 세계 사례, 단계 카드, 수업 서사를 묶어 고등학교 atlas를 구성한다.

## 현재 분해된 2차 surface

- [[Geo-Lab Overview Guide]]
- [[Geo-Lab Gallery]]
- [[Geo-Lab Lab]]
- [[Geo-Lab Research Lab]]
- [[Geo-Lab Climate Lab]]
- [[Geo-Lab Case Mode]]
- [[Geo-Lab High School Geography Atlas]]
- [[Geo-Lab Higher Ed Portal]]

## 확인 근거

- [README.md](C:/Users/HANSOL/OneDrive/Desktop/Geo-lab/README.md)
- [docs/HIGH_SCHOOL_TERRAIN_ANIMATION_GUIDE.md](C:/Users/HANSOL/OneDrive/Desktop/Geo-lab/docs/HIGH_SCHOOL_TERRAIN_ANIMATION_GUIDE.md)
- [[Latest Repository Snapshot]]
- `app.py`
- `app/home_view.py`
- `app/high_school_geography_view.py`
- `pages/1_📖_Gallery.py`
- `pages/2_🗺️_Overview.py`
- `pages/3_🧪_Lab.py`
- `pages/5_☁️_Climate.py`

## 구조적 긴장과 리스크

- `app/main.py` 같은 과거 simulator 축이 남아 있어 현재 shell과 과거 구현이 공존한다.
- 여러 page와 utility가 [[Session-State Handoff]] 로 결합되어 있어 추론은 유연하지만 경계가 흐려지기 쉽다.
- Gallery, Case Mode, Climate, Research가 모두 [[합성 DEM과 관측 DEM]] 및 provenance 설명을 요구하는데, 사용자 메시지로는 그 경계가 항상 충분히 드러나지 않을 수 있다.
- README의 상위 서사보다 실제 working tree의 표면적이 더 넓어 문서와 runtime shape 사이 간격이 있다.

## 다음에 볼 note

- [[Geo-Lab Streamlit Surface Map]]
- [[Geo-Lab Overview Guide Current Shape]]
- [[Geo-Lab Gallery Current Shape]]
- [[Geo-Lab Lab Current Shape]]
- [[Geo-Lab Research Lab Current Shape]]
- [[Geo-Lab Climate Lab Current Shape]]
- [[Geo-Lab Case Mode Current Shape]]
- [[Geo-Lab High School Geography Atlas Current Shape]]
- [[Geo-Lab Higher Ed Portal Current Shape]]
