---
id: raw-snapshot-2026-04-12
type: raw_snapshot
layer: raw
status: immutable
created: 2026-04-12
updated: 2026-04-12
tags:
  - snapshot
  - git
  - working-tree
---

# 2026-04-12 Repository Snapshot

## capture scope

이 note는 2026-04-12 기준 저장소 상태를 `committed HEAD` 와 `working tree` 로 분리해 기록한 raw snapshot이다.

## committed snapshot

### HEAD

- commit date: `2026-03-20`
- full sha: `a3d9c1673099d6947288f62aa9283be730be717b`
- short sha: `a3d9c16`
- subject: `feat: increase Koppen climate data resolution`

### recent committed trend

- 2026-03-20 `a3d9c16` `feat: increase Koppen climate data resolution`
- 2026-03-20 `80632cd` `docs: refine Koppen Pages deployment guide`
- 2026-03-20 `9f1438d` `feat: add Koppen climate map app and Cloudflare Pages setup`
- 2025-12-25 `7a9f894` `feat: Geo-Lab Modern UI - clean white/slate/blue design based on approved mockup`
- 2025-12-25 `a165cc2` `feat: GeoLab Scholar theme with teacher/expert mode`
- 2025-12-25 `1155e4f` `fix: Lab page UI - hide advanced params in expander`
- 2025-12-25 `b6aff9d` `revert: Restore original style.css - UI fix`
- 2025-12-25 `070de42` `feat: Performance & UI improvements - Add 30+ camera angles, responsive CSS, dark mode, caching utils`
- 2025-12-25 `45183b7` `fix: Connect ideal_landforms to scenarios, organize UI with expanders`
- 2025-12-24 `5a7c9e5` `feat: Expand terrain scenarios with Gallery landforms (17 total)`

## working tree snapshot

### status counts

- modified tracked paths: `32`
- deleted tracked paths: `3`
- untracked paths: `94`
- staged diff stat: empty at capture time

### top-level scope summary

- tracked changed top areas: `apps(6), app(4), pages(4), engine(3), renderer.py(1), requirements.txt(1), visitor_count.json(1), terrain_processes_stages.html(1), tests(1), terrain_processes.html(1), terrain_processes_3d.html(1), pyproject.toml(1)`
- untracked top areas: `apps(33), tests(16), docs(14), app(11), pages(4), engine(1), tmp(1), playwright.config.js(1), run_geo_lab.ps1(1), knowledge(1), output(1), .obsidian(1)`

### diff stat facts

- `git diff --stat` reported `32 files changed, 8125 insertions(+), 4441 deletions(-)`
- deleted tracked files in diff stat:
  - `terrain_processes.html`
  - `terrain_processes_3d.html`
  - `terrain_processes_stages.html`

### visible working tree signals

- tracked edits include `app.py`, `README.md`, `pages/1_📖_Gallery.py`, `pages/2_🗺️_Overview.py`, `pages/3_🧪_Lab.py`, `pages/4_🔬_Research.py`, `engine/analysis.py`, `engine/simple_lem.py`, `assets/style.css`, `apps/koppen-climate-lab/*`
- untracked additions include `app/home_view.py`, `app/high_school_geography_view.py`, `app/utils/*`, `app/cases/`, `pages/7_🎓_Higher_Ed.py`, `pages/8_🏫_High_School_Geography.py`, `apps/school-neighborhood-gis/`, multiple docs, multiple tests, `knowledge/`, `.obsidian/`

## interpretation boundary

- 이 note는 command-derived facts만 적는다.
- working tree의 의미 판단, canonical current-state 해석, 위키 갱신 우선순위는 curated note인 [[Latest Repository Snapshot]] 에서 다룬다.
