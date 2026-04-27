---
id: shape-school-neighborhood-gis
type: synthesis
layer: curated
status: seed
created: 2026-04-12
updated: 2026-04-12
tags:
  - synthesis
  - gis
  - current-shape
---

# School Neighborhood GIS Current Shape

## 현재 구현 형태

- 정적 프런트엔드 + `_worker.js` 프록시를 조합한 Cloudflare Pages 배포형 앱이다.
- root에는 `app.js`, `config.js`, `runtime-config.js`, `sgis-adapter.js`, `store.js` 같은 실행 파일이 있고,
  하위에는 `application`, `domain`, `presentation`, `infrastructure` 폴더가 함께 존재한다.
- README와 docs는 `학교 주변`, `대한민국 통계`, `학생 레이어`, `SGIS 실데이터`, `GeoJSON export`, `모바일 대응` 을 현재 구현 범위로 제시한다.
- Supabase는 필수는 아니지만 학교 서비스 전환용 저장/승인 확장으로 준비되어 있다.

## 확인 근거

- [apps/school-neighborhood-gis/README.md](../../../apps/school-neighborhood-gis/README.md)
- [docs/CLOUDFLARE_PAGES_SCHOOL_GIS.md](../../../docs/CLOUDFLARE_PAGES_SCHOOL_GIS.md)
- [docs/SUPABASE_SCHOOL_GIS_SETUP.md](../../../docs/SUPABASE_SCHOOL_GIS_SETUP.md)
- [[Latest Repository Snapshot]]
- `apps/school-neighborhood-gis/` 폴더 구조

## 구조적 긴장/리스크

- clean-architecture 성격의 폴더와 flat runtime 파일이 함께 있어 경계가 완전히 정리된 상태는 아니다.
- 배포형 `_worker.js` 프록시와 로컬 정적 실행 흐름을 함께 유지해야 한다.
- 실서비스 전환 시 환경변수, SGIS secret, 학교별 runtime config 관리가 운영 핵심이 된다.

## 다음에 볼 것

- `apps/school-neighborhood-gis/functions/`
- `apps/school-neighborhood-gis/tests/`
- `apps/school-neighborhood-gis/scripts/prepare-pages-deploy.ps1`
- `apps/school-neighborhood-gis/supabase-schema.sql`
