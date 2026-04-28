---
id: latest-repository-snapshot
type: snapshot_digest
layer: curated
status: active
created: 2026-04-12
updated: 2026-04-12
tags:
  - snapshot
  - git
  - current
aliases:
  - latest-snapshot
---

# Latest Repository Snapshot

## latest raw snapshot

- source: [[2026-04-12 Repository Snapshot]]

## committed baseline

- 현재 HEAD는 `2026-03-20 a3d9c16 feat: increase Koppen climate data resolution` 이다.
- committed history 기준 마지막 뚜렷한 축은 `Koppen Climate Lab` 과 Pages 배포 문서다.

## working tree delta

- 현재 working tree는 HEAD 대비 매우 크게 앞서 있다.
- tracked change만 봐도 `32 modified/deleted`, untracked가 `94` 이다.
- 변화 집중 구역은 `apps`, `app`, `pages`, `docs`, `tests`, `engine` 이다.
- 따라서 `current-state` 나 `current-shape` 설명은 commit history보다 working tree를 더 우선해서 읽어야 한다.

## wiki sync implications

- 현재 위키는 `committed baseline` 과 `working tree current shape` 를 분리해 읽어야 한다.
- baseline note는 commit/document 의도 설명에 유효하다.
- 현재 구조 note는 working tree 기반 관찰을 canonical source로 삼아야 한다.
- 앞으로 `snapshot 하고 wiki sync 해줘` 요청이 오면 이 note를 갱신한 뒤, 영향 받은 syntheses를 업데이트하는 것이 기본 흐름이다.

## next notes to refresh when changes continue

- [[Current State Synthesis]]
- [[Project Map]]
- [[Geo-Lab Streamlit App Current Shape]]
- [[Terrain Engine Current Shape]]
- [[School Neighborhood GIS Current Shape]]
- [[Koppen Climate Lab Current Shape]]
