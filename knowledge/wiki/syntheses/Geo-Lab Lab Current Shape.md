---
id: shape-geo-lab-lab
type: synthesis
layer: curated
status: seed
created: 2026-04-12
updated: 2026-04-12
tags:
  - synthesis
  - streamlit
  - lab
  - current-shape
aliases:
  - Lab Current Shape
---

# Geo-Lab Lab Current Shape

## 현재 구현 형태

- `pages/3_🧪_Lab.py` 하나가 큰 page shell 역할을 한다.
- sidebar에서 `학생 단순모드` 와 `교사 상세모드` 를 나누고, 시나리오 범주를 `산지/하천`, `빙하/해안`, `건조/특수` 로 분류한다.
- `gallery_lab_preset` 을 session state로 받아 Gallery에서 고른 모범 사례를 바로 Lab으로 이어 받는다.
- `app.utils.lab_model` 이 scenario config, teaching note, playback guidance, stage history를 제공한다.
- `app.components.animation_renderer` 와 `render_terrain_plotly` 를 통해 animation embed, GIF, 정지 프레임 비교를 수행한다.
- page 상단에는 provenance panel이 붙어 있어 이 화면이 교육용 단순화 모델인지, 실험 비교용인지 계속 노출한다.
- page 내부에서 Higher Ed 쪽으로 넘어가야 하는 상황을 안내하는 hint도 포함한다.

## 확인 근거

- `pages/3_🧪_Lab.py`
- `app/utils/lab_model.py`
- `app/utils/mode_helpers.py`
- `app/components/animation_renderer.py`
- [[Latest Repository Snapshot]]

## 구조적 긴장/리스크

- page 파일 하나에 UI, session state, scenario routing, export, animation logic가 많이 모여 있다.
- 학생용 단순화와 교사용 상세 비교가 같은 surface 안에 있어 상태 분기가 계속 늘어날 수 있다.
- Large session state coupling이 있어 preset handoff나 rerun 타이밍 회귀에 민감할 가능성이 높다.

## 다음에 볼 것

- [[Geo-Lab Research Lab]]
- [[Geo-Lab High School Geography Atlas]]
- `app/utils/gallery_showcase.py`
- `tests/test_lab_model.py`
- `tests/test_lab_stage_history.py`
