---
id: shape-geo-lab-overview-guide
type: synthesis
layer: curated
status: seed
created: 2026-04-12
updated: 2026-04-12
tags:
  - synthesis
  - streamlit
  - overview
  - current-shape
aliases:
  - Overview Current Shape
---

# Geo-Lab Overview Guide Current Shape

## 현재 구현 형태

- `pages/2_🗺️_Overview.py` 는 classroom routing 설명용 lightweight page다.
- `10분 시연`, `20분 탐구`, `심화·후속 활동` 세 가지 시작 경로를 CTA 카드로 제시한다.
- 메인 홈이 우선하는 사용자와 자주 쓰는 지형 묶음을 별도로 정리한다.
- Research/Higher Ed를 메인 홈과 같은 레벨의 기본 CTA가 아니라 별도 포털로 보내는 이유를 설명한다.

## 확인 근거

- `pages/2_🗺️_Overview.py`
- [[Latest Repository Snapshot]]

## 구조적 긴장/리스크

- Home과 역할이 겹칠 수 있어 둘의 차이를 유지해야 한다.
- 제품 copy가 바뀌면 stale routing 설명이 남기 쉽다.

## 다음에 볼 것

- [[Geo-Lab Higher Ed Portal]]
- [[Geo-Lab Streamlit Surface Map]]
