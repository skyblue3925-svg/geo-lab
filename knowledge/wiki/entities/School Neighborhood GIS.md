---
id: entity-school-neighborhood-gis
type: entity
layer: curated
status: seed
created: 2026-04-12
updated: 2026-04-12
tags:
  - entity
  - gis
  - webapp
---

# School Neighborhood GIS

## 정체성

학생이 공개 레이어와 자기 조사 레이어를 겹쳐 보며 GIS를 체험하는 교육용 webGIS MVP다.

## 주요 책임

- 학교 주변 레이어 탐색
- 대한민국 통계/시설 레이어 탐색
- 학생 레이어 생성, 업로드, 내보내기
- SGIS 실데이터 프록시 연결
- Cloudflare Pages 기반 배포

## 핵심 경로

- `apps/school-neighborhood-gis/index.html`
- `apps/school-neighborhood-gis/app.js`
- `apps/school-neighborhood-gis/runtime-config.js`
- `apps/school-neighborhood-gis/_worker.js`
- `apps/school-neighborhood-gis/application/`
- `apps/school-neighborhood-gis/domain/`
- `apps/school-neighborhood-gis/presentation/`
- `apps/school-neighborhood-gis/infrastructure/`

## 관련 note

- [[School Neighborhood GIS Current Shape]]
- [[Project Map]]
- [[Current State Synthesis]]

## 관찰 메모

- 이 surface는 더 이상 보조 실험이 아니라 별도 배포 가이드와 운영 절차를 가진 독립 제품에 가깝다.
