# wiki-ingest

이 스킬은 repo 안의 문서, 코드, 로그를 위키에 적재할 때 사용한다.

## 목표

- source를 먼저 `knowledge/raw/` 에 보존한다.
- 필요한 해석만 `knowledge/wiki/` 에 올린다.
- 중복 note를 만들지 않는다.
- baseline source와 repository snapshot은 다른 흐름으로 취급한다.

## 절차

1. [[Knowledge Index]] 를 확인해 기존 note가 있는지 찾는다.
2. source를 읽고 날짜가 있는 raw source note를 만든다.
3. 기존 entity, map, synthesis note를 우선 갱신한다.
4. 새 durable note가 생기면 [[Knowledge Index]] 와 [[Knowledge Log]] 를 함께 갱신한다.

## 가드레일

- raw note는 immutable source layer다.
- git 상태 캡처는 `wiki-snapshot` 으로 분리한다.
- prose 기본 언어는 한국어다.
- README, docs, git log, code read 결과를 한 note에 섞을 때는 source 구분을 명시한다.
