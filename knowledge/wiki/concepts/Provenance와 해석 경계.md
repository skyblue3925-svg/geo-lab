---
id: concept-provenance-boundary
type: concept
layer: curated
status: seed
created: 2026-04-12
updated: 2026-04-12
tags:
  - concept
  - provenance
  - interpretation
aliases:
  - Provenance Boundary
---

# Provenance와 해석 경계

## 핵심 개념

같은 시각화라도 `무엇에서 나온 결과인가` 를 먼저 밝히지 않으면, 사용자가 결과를 과신하게 된다.

## 현재 코드에서의 구현

- `app/utils/mode_helpers.py` 의 provenance panel helper
- `Lab` 에서 교육 모드 / 실험 모드 구분
- `Research Lab` 에서 upload / simulation / case_mode source 구분
- `Case Mode` 에서 실제 사례와 simulation 결과를 함께 쓰되, 완전한 현실 재현으로 단정하지 않도록 유도

## 위키에서 중요하게 보는 이유

- 이 저장소는 교육용 단순화 모델과 관측 자료를 함께 사용한다.
- 따라서 note를 읽을 때도 `확인된 사실`, `단순화 모델`, `현실 근사`, `working tree 추정` 을 분리해야 한다.

## 관련 note

- [[Geo-Lab Lab Current Shape]]
- [[Geo-Lab Research Lab Current Shape]]
- [[Latest Repository Snapshot]]
- [[합성 DEM과 관측 DEM]]
