---
id: repo-baseline-source-digest
type: source_digest
layer: curated
status: seed
created: 2026-04-12
updated: 2026-04-12
tags:
  - source
  - baseline
aliases:
  - repository-baseline
---

# Repo Baseline Source Digest

이 note는 [[2026-04-12 Repo Baseline Source Note]] 의 curated 요약본이다.

## baseline 요약

- Geo-lab의 canonical 설명은 여전히 `교사용 Streamlit 수업 앱` 이다.
- 그러나 docs와 subapp README까지 합치면 실제 저장소는 `주력 Streamlit 앱 + 별도 정적 교육 웹 앱 + 배포/운영 문서` 의 다중 제품 workspace다.
- 문서 우선순위는 `고등학교 수업 적합성`, `교사용 설명`, `학생 탐구 흐름`, `배포 가능한 부가 앱` 으로 읽힌다.

## source 우선순위

1. root `README.md`
2. 현재 운영용 `docs/`
3. 서브앱 README
4. recent git log
5. 코드 기반 current-shape note

## 이 baseline이 말하는 것

- `pages/` 와 `engine/` 가 core다.
- `Case Mode`, `Research Lab`, `Climate Lab` 은 수업 시퀀스 안에서 연결된다.
- `School Neighborhood GIS` 와 `Koppen Climate Lab` 은 repo 내부의 side product가 아니라 이미 배포/운영 문서가 있는 독립적 surface다.
- 최신 commit 흐름만 보면 Koppen 쪽이 마지막 committed focus다.

## 다음에 함께 읽을 note

- [[Project Map]]
- [[Current State Synthesis]]
- [[Geo-Lab Streamlit App Current Shape]]
- [[School Neighborhood GIS Current Shape]]
- [[Koppen Climate Lab Current Shape]]
