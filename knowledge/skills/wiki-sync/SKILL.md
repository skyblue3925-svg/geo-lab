# wiki-sync

이 스킬은 코드나 문서가 변한 뒤 위키를 현재 상태에 다시 맞출 때 사용한다.

## 목표

- 기존 note를 canonical source of synthesis로 유지한다.
- 변경된 부분만 갱신하고, 중복 note를 만들지 않는다.
- 최신 raw snapshot과 curated snapshot digest를 기준으로 current-shape를 재해석한다.

## 절차

1. 최신 raw snapshot note를 읽는다. 없으면 먼저 `wiki-snapshot` 을 수행한다.
2. [[Latest Repository Snapshot]] 을 갱신한다.
3. 관련 코드와 docs를 읽어 어떤 entity가 바뀌었는지 식별한다.
4. 기존 `Current Shape` note와 `Current State Synthesis` 를 갱신한다.
5. 필요하면 `Project Map` 과 source digest도 갱신한다.
6. durable note가 바뀌었으면 index/log를 반영한다.

## 가드레일

- raw history를 덮어쓰지 않는다.
- entity note보다 current-shape note를 먼저 새로 만들지 않는다.
- 변경 범위가 국소적이어도 `Project Map` 에 영향이 있으면 함께 갱신한다.
- commit history만으로 current state를 단정하지 않는다.
