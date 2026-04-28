# wiki-query

이 스킬은 위키를 기반으로 빠르게 질문에 답할 때 사용한다.

## 목표

- curated note를 우선 읽고,
- 필요한 경우 raw source note로 근거를 되짚고,
- 확실한 것과 추정인 것을 분리해 말한다.

## 절차

1. [[LLM Wiki Home]] 와 [[Knowledge Index]] 에서 관련 canonical note를 찾는다.
2. [[Current State Synthesis]] 와 [[Latest Repository Snapshot]] 을 먼저 읽는다.
3. entity note와 current-shape note를 우선 읽는다.
4. 근거가 필요하면 `knowledge/raw/` source note 또는 snapshot note를 확인한다.
5. 답변에는 `확인된 사실`, `현재 판단`, `추가로 읽을 note` 를 구분한다.

## 가드레일

- raw note에 없는 내용을 source 사실처럼 단정하지 않는다.
- current-shape note가 없으면 즉석 추정보다 먼저 note 보강 필요 여부를 판단한다.
