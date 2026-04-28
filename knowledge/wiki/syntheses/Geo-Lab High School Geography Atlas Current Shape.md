---
id: shape-geo-lab-high-school-geography-atlas
type: synthesis
layer: curated
status: seed
created: 2026-04-12
updated: 2026-04-12
tags:
  - synthesis
  - streamlit
  - atlas
  - current-shape
aliases:
  - High School Geography Current Shape
---

# Geo-Lab High School Geography Atlas Current Shape

## 현재 구현 형태

- `pages/8_🏫_High_School_Geography.py` 는 매우 얇은 wrapper이고, 실제 로직은 `app/high_school_geography_view.py` 에 있다.
- `app/utils/high_school_world_geography.py` 가 group, topic, world case, teaching stage를 dataclass 기반으로 구조화한다.
- page는 단원 선택 -> 대표 지형 선택 -> 세계 사례 지도 -> 표준 시점 미리보기 -> 수업 카드 -> 4단계 형성 과정 순으로 전개된다.
- `route_to_lab()` 과 `open_gallery()` 를 통해 교사/학생 preset을 Lab과 Gallery로 넘긴다.
- student question, teacher note, overlay caption, compare hint 같은 교육용 metadata가 first-class data로 다뤄진다.

## 확인 근거

- `pages/8_🏫_High_School_Geography.py`
- `app/high_school_geography_view.py`
- `app/utils/high_school_world_geography.py`
- `app/utils/gallery_showcase.py`
- [[Latest Repository Snapshot]]

## 구조적 긴장/리스크

- page wrapper는 얇지만 실제 logic/data coupling은 `view + dataset + preset routing` 조합으로 꽤 강하다.
- Lab/Gallery preset availability에 의존하므로 target surface가 바뀌면 atlas routing도 함께 갱신해야 한다.
- 고등학교 수업에 최적화된 canonical 표현이 많아, 향후 대학용 설명과 충돌하지 않게 경계를 유지해야 한다.

## 다음에 볼 것

- [[Geo-Lab Lab]]
- [[Geo-Lab Higher Ed Portal]]
- `tests/test_high_school_geography_view.py`
- `tests/test_high_school_world_geography.py`
