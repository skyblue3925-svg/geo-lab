---
id: shape-geo-lab-gallery
type: synthesis
layer: curated
status: seed
created: 2026-04-12
updated: 2026-04-12
tags:
  - synthesis
  - streamlit
  - gallery
  - current-shape
aliases:
  - Gallery Current Shape
---

# Geo-Lab Gallery Current Shape

## 현재 구현 형태

- `pages/1_📖_Gallery.py` 는 stable gallery shell 역할을 한다.
- `app.utils.gallery_showcase` 가 category default, landform override, world case 연결, Lab preset 생성 규칙을 데이터처럼 관리한다.
- page는 showcase card, hero, lesson panel, world case atlas, animated terrain preview를 함께 제공한다.
- `consume_gallery_showcase_preset()` 과 `queue_gallery_showcase_preset()` 으로 Gallery 선택을 Lab 세션으로 넘긴다.
- `app.utils.world_terrain_cases` 와 결합해 지형 카드가 실제 세계 사례와 수업 질문을 같이 보여줄 수 있다.

## 확인 근거

- `pages/1_📖_Gallery.py`
- `app/utils/gallery_showcase.py`
- `app/utils/world_terrain_cases.py`
- [[Latest Repository Snapshot]]

## 구조적 긴장/리스크

- showcase preset, atlas, animation, routing이 같이 있어 page가 UI catalog 이상의 책임을 갖는다.
- preset 규칙이 data file에 많이 숨어 있어 target surface명이 바뀌면 stale preset 위험이 있다.
- Gallery는 안정적인 surface를 지향하지만, 수업 metadata가 커질수록 data-driven 복잡도가 늘 수 있다.

## 다음에 볼 것

- [[Geo-Lab Lab]]
- [[Geo-Lab High School Geography Atlas]]
- `tests/test_gallery_showcase.py`
