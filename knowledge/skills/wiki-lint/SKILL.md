# wiki-lint

이 스킬은 위키 구조와 note 품질을 점검할 때 사용한다.

## 체크리스트

- `knowledge/raw/` 와 `knowledge/wiki/` 역할이 섞이지 않았는가
- raw snapshot과 curated snapshot digest가 분리되어 있는가
- durable note가 [[Knowledge Index]] 에 등록되어 있는가
- durable note 생성/갱신이 [[Knowledge Log]] 에 남아 있는가
- 중복 제목이나 거의 같은 주제의 note가 생기지 않았는가
- `Current Shape` note가 entity note 없이 단독으로 늘어나지 않았는가
- home/schema/map/synthesis 링크가 깨지지 않았는가
- 최신 snapshot 이후 stale claim이 남아 있지 않은가

## 우선 수정 순서

1. 링크 오류
2. index/log 누락
3. raw/wiki 레이어 혼합
4. 중복 note
5. 오래된 current-shape note

## 가드레일

- lint 과정에서도 기존 canonical note를 우선 갱신한다.
- raw note는 formatting 수정 외에는 사실 본문을 재서술하지 않는다.
