# wiki-snapshot

이 스킬은 저장소 상태를 raw snapshot으로 캡처할 때 사용한다.

## 목표

- `committed` 와 `working tree` 를 분리해 기록한다.
- raw snapshot과 curated 해석을 섞지 않는다.
- 이후 `wiki-sync` 가 바로 이어질 수 있게 최소 근거를 남긴다.

## 기본 절차

1. HEAD commit 정보와 recent git log를 읽는다.
2. `git status --short`, `git diff --stat`, 필요하면 `git diff --cached --stat` 를 읽는다.
3. 새 raw snapshot note를 `knowledge/raw/snapshots/` 에 날짜 기준으로 만든다.
4. raw note에는 command-derived facts만 적는다.
5. 해석은 `wiki-sync` 단계에서 `Latest Repository Snapshot` 에 반영한다.

## 최소 포함 항목

- capture date
- HEAD sha / subject / date
- recent committed trend
- working tree modified/deleted/untracked counts
- diff stat
- top-level changed areas

## 가드레일

- raw snapshot note는 immutable이다.
- commit history와 working tree를 섞어 하나의 현재 상태처럼 쓰지 않는다.
- staged diff가 비어 있으면 비어 있다고 그대로 적는다.
