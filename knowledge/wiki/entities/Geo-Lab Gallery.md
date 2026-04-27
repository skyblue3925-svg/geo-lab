---
id: entity-geo-lab-gallery
type: entity
layer: curated
status: seed
created: 2026-04-12
updated: 2026-04-12
tags:
  - entity
  - streamlit
  - gallery
aliases:
  - Gallery
---

# Geo-Lab Gallery

## 정체성

대표 지형을 안정적으로 미리 보고, 수업용 preset을 고른 뒤 다른 surface로 넘기는 catalog surface다.

## 주요 책임

- 대표 지형 카드와 썸네일 제공
- 연속 애니메이션 / 수동 단계 보기 제공
- 세계 사례 atlas와 수업 포인트 연결
- Lab으로 preset handoff
- 고등학교 수업용 catalog와 고급 미리보기 모드 제공

## 핵심 경로

- `pages/1_📖_Gallery.py`
- `app/utils/gallery_showcase.py`
- `app/utils/world_terrain_cases.py`
- `app/components/animation_renderer.py`
- `engine/ideal_landforms.py`

## 관련 note

- [[Geo-Lab Streamlit App]]
- [[Geo-Lab Gallery Current Shape]]
- [[Geo-Lab Streamlit Surface Map]]
- [[Geo-Lab Lab]]
- [[Geo-Lab High School Geography Atlas]]

## 관찰 메모

- Gallery는 단순 showcase가 아니라 `preset selection + routing` 이 핵심 역할이다.
