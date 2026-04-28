---
id: raw-repo-baseline-2026-04-12
type: raw_source
layer: raw
status: immutable
created: 2026-04-12
updated: 2026-04-12
tags:
  - baseline
  - repo
  - source
---

# 2026-04-12 Repo Baseline Source Note

## 읽은 source 범위

### 1. primary README

- [README.md](../../README.md)

### 2. docs

- [docs/QUICK_START_LOCAL_SERVER.md](../../docs/QUICK_START_LOCAL_SERVER.md)
- [docs/HIGH_SCHOOL_TERRAIN_ANIMATION_GUIDE.md](../../docs/HIGH_SCHOOL_TERRAIN_ANIMATION_GUIDE.md)
- [docs/TERRAIN_REFERENCE_NOTES.md](../../docs/TERRAIN_REFERENCE_NOTES.md)
- [docs/CASE_MODE_USAGE.md](../../docs/CASE_MODE_USAGE.md)
- [docs/CLOUDFLARE_PAGES_SCHOOL_GIS.md](../../docs/CLOUDFLARE_PAGES_SCHOOL_GIS.md)
- [docs/SUPABASE_SCHOOL_GIS_SETUP.md](../../docs/SUPABASE_SCHOOL_GIS_SETUP.md)
- [docs/subagents/README.md](../../docs/subagents/README.md)

### 3. supplementary README

- [apps/koppen-climate-lab/README.md](../../apps/koppen-climate-lab/README.md)
- [apps/school-neighborhood-gis/README.md](../../apps/school-neighborhood-gis/README.md)

### 4. recent git log

명령:

```powershell
git log --pretty=format:"%ad %h %s" --date=short -n 20
```

## 관찰 사실

- root README는 Geo-Lab을 `교사를 위한 지형·기후·여행지리 수업용 Streamlit 앱` 으로 정의한다.
- README 기준 핵심 구조는 `app.py`, `pages/`, `engine/`, `app/cases/`, `docs/` 다.
- 로컬 실행 기준 경로는 `.\run_geo_lab.ps1` 이며, 테스트 기준은 `.\.venv\Scripts\python.exe -m pytest -q` 다.
- `docs/QUICK_START_LOCAL_SERVER.md` 는 `run_geo_lab.ps1 -KillPortOwner` 와 `-BootstrapVenv` 를 운영용 표준 실행 절차로 둔다.
- `docs/HIGH_SCHOOL_TERRAIN_ANIMATION_GUIDE.md` 는 고등학생용 지형 애니메이션을 `4단계 이내`, `과정 중심`, `교사용 설명 포인트 포함` 으로 설계하도록 요구한다.
- `docs/TERRAIN_REFERENCE_NOTES.md` 는 선상지, 삼각주, 곡류 하천, V자곡, U자곡/피오르, 카르스트, 해안 지형 등 설명 카드 보강용 참고 노트를 제공한다.
- `docs/CASE_MODE_USAGE.md` 는 여행지리 수업용 Case Mode를 별도 수업 흐름으로 운영하며, Research Lab과 Climate Lab을 함께 쓰는 학습 시퀀스를 제시한다.
- `docs/CLOUDFLARE_PAGES_SCHOOL_GIS.md` 와 `docs/SUPABASE_SCHOOL_GIS_SETUP.md` 는 `apps/school-neighborhood-gis` 가 별도 배포·운영 가능한 제품임을 보여준다.
- `apps/school-neighborhood-gis/README.md` 는 학생용 GIS MVP, SGIS 프록시, Cloudflare Pages 배포, Supabase 확장 계획을 설명한다.
- `apps/koppen-climate-lab/README.md` 는 정적 교실용 웹 앱, precomputed dataset, Cloudflare Pages 배포 구조를 설명한다.
- `docs/subagents/README.md` 는 현재 저장소가 dirty worktree 이며, 같은 workspace 안에서 파일 ownership을 나눠 병렬 작업하는 runbook을 포함한다.

## recent git log signal

- 2026-03-20 `a3d9c16` `feat: increase Koppen climate data resolution`
- 2026-03-20 `80632cd` `docs: refine Koppen Pages deployment guide`
- 2026-03-20 `9f1438d` `feat: add Koppen climate map app and Cloudflare Pages setup`
- 2025-12-25 `7a9f894` `feat: Geo-Lab Modern UI - clean white/slate/blue design based on approved mockup`
- 2025-12-25 `a165cc2` `feat: GeoLab Scholar theme with teacher/expert mode`
- 2025-12-25 `1155e4f` `fix: Lab page UI - hide advanced params in expander`
- 2025-12-25 `070de42` `feat: Performance & UI improvements - Add 30+ camera angles, responsive CSS, dark mode, caching utils`
- 2025-12-24 `4f86c77` `refactor: Restructure Lab tabs - merge climate/human into terrain simulation`
- 2025-12-24 `5e899f0` `feat: Integrate advanced physics models to LEM simulation`
- 2025-12-23 `1c6005a` `feat: Add structured advanced Landlab physics`
- 2025-12-23 `ef17b08` `feat: LEM modular restructuring - climate, human, visualization modules`

## source-derived interpretation

- committed history상 2025-12에는 Lab, UI, LEM 고도화가 중심축이었다.
- 2026-03에는 `Koppen Climate Lab` 과 Cloudflare Pages 배포 문서가 새 축으로 추가되었다.
- docs 기준 현재 repo는 단일 Streamlit 앱만이 아니라 `수업용 Streamlit + 정적 웹 앱 + 배포/운영 문서 + 병렬 작업 runbook` 을 포함하는 교육 플랫폼 workspace에 가깝다.
- 고등학교 수업 적합성, 교사용 설명, 학생 탐구 흐름이 문서 전반의 우선순위다.

## 한계와 빈칸

- recent git log의 최신 커밋은 2026-03-20까지이며, 현재 working tree의 최신 파일 상태 전체를 대표하지 않을 수 있다.
- README와 docs는 제품 의도를 잘 설명하지만, 실제 활성 진입점과 모듈 간 결합 상태는 코드 읽기 기반 current-shape note에서 보완해야 한다.
