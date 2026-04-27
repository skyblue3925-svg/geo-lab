---
id: llm-wiki-schema
type: schema
layer: curated
status: seed
created: 2026-04-12
updated: 2026-04-12
tags:
  - wiki
  - schema
aliases:
  - wiki-schema
---

# LLM Wiki Schema

## 1. 레이어 모델

### `knowledge/raw/`

- 성격: immutable source layer
- 내용: README, docs, git log, code read, command output를 날짜 기준으로 보존한 source note
- 규칙: 기존 raw note의 사실 본문을 덮어쓰지 않는다. 소스가 바뀌면 새 raw note를 만든다.

### `knowledge/raw/snapshots/`

- 성격: immutable repository snapshot layer
- 내용: git HEAD, recent commit trend, working tree status, diff stat
- 규칙: `committed` 와 `working tree` 를 같은 note 안에서 명시적으로 분리한다.

### `knowledge/wiki/`

- 성격: curated layer
- 내용: entity, concept, source digest, synthesis, map
- 규칙: 해석, 요약, 연결, 현재 구조 판단은 여기서 관리한다.

## 2. note 타입

| type | 위치 | 목적 |
| --- | --- | --- |
| `home` | `knowledge/` | vault 진입점 |
| `schema` | `knowledge/` | 위키 운영 규칙 |
| `raw_source` | `knowledge/raw/` | 원천 관찰 기록 |
| `raw_snapshot` | `knowledge/raw/snapshots/` | 저장소 상태 스냅샷 |
| `source_digest` | `knowledge/wiki/sources/` | raw source의 해석된 요약 |
| `snapshot_digest` | `knowledge/wiki/sources/` | 최신 raw snapshot의 curated 요약 |
| `map` | `knowledge/wiki/maps/` | 구조/경로/폴더 지형도 |
| `entity` | `knowledge/wiki/entities/` | 모듈·서브시스템 정체성 |
| `synthesis` | `knowledge/wiki/syntheses/` | 현재 상태, current shape, 교차 해석 |

## 3. 최소 메타데이터

모든 durable note는 아래 frontmatter를 권장한다.

```yaml
id: stable-id
type: entity
layer: curated
status: seed
created: 2026-04-12
updated: 2026-04-12
```

## 4. 권장 본문 구조

### entity note

1. 정체성
2. 주요 책임
3. 핵심 경로
4. 관련 note
5. 관찰 메모

### current-shape synthesis

1. 현재 구현 형태
2. 확인 근거
3. 구조적 긴장/리스크
4. 다음에 볼 것

### raw source note

1. 읽은 source 범위
2. 관찰 사실
3. source-derived interpretation
4. 한계와 빈칸

### raw snapshot note

1. capture scope
2. committed snapshot
3. working tree snapshot
4. command-derived counts
5. interpretation boundary

### snapshot digest

1. latest raw snapshot link
2. committed baseline
3. working tree delta
4. wiki sync implications
5. next notes to refresh

## 5. 생성/갱신 규칙

1. 먼저 [[Knowledge Index]] 와 대상 폴더를 확인한다.
2. 같은 주제 note가 있으면 기존 note를 갱신한다.
3. source read가 새로 필요하면 `knowledge/raw/` 에 먼저 적재한다.
4. curated note를 갱신한다.
5. durable note가 생기거나 바뀌면 [[Knowledge Index]] 와 [[Knowledge Log]] 를 함께 갱신한다.

snapshot/sync 작업은 아래 순서를 권장한다.

1. raw snapshot 생성
2. `Latest Repository Snapshot` 갱신
3. 영향 받은 map/entity/current-shape/current-state note 갱신
4. index/log 갱신

## 6. 네이밍 규칙

- raw note: `YYYY-MM-DD <Subject>.md`
- current shape note: `<Entity> Current Shape.md`
- synthesis note: 핵심 판단을 바로 읽을 수 있는 명사형 제목
- entity note: 코드/제품 명칭 그대로 사용

## 7. 충돌 해결 규칙

- 중복 note를 새로 만들지 않는다.
- 제목이 비슷하면 기존 note를 canonical note로 승격하고 나머지는 만들지 않는다.
- raw와 wiki의 역할이 섞이면 raw는 사실 보존, wiki는 해석으로 다시 분리한다.
