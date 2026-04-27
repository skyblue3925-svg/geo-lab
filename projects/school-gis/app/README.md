# School GIS

제작자: 한백고등학교 김한솔

학생이 학교 주변 공개데이터와 직접 만든 조사 데이터를 지도 위에 겹쳐 보며 GIS를 체험하는 교육용 webGIS MVP입니다.

## 앱 경로

- 앱 소스: `projects/school-gis/app/`
- 테스트 스크립트: 루트 `package.json`의 `test:gis:syntax`
- 배포 문서: `docs/CLOUDFLARE_PAGES_SCHOOL_GIS.md`, `docs/SGIS_LOCAL_SETUP.md`, `docs/SUPABASE_SCHOOL_GIS_SETUP.md`

## 현재 구현 범위

- 학교 주변 / 대한민국 통계 화면 전환
- 기본 공개 레이어와 샘플 통계 레이어
- 학생 데이터 생성
- 지도 클릭으로 직접 포인트 추가
- CSV / GeoJSON 업로드
- 외부 GeoJSON / CSV URL 불러오기
- `runtime-config.js` 기반 프리셋 공개 데이터 불러오기
- SGIS 경계 및 인구 통계 프록시
- 모바일 / 태블릿 대응

## 로컬 실행

```powershell
cd "C:\Users\HANSOL\OneDrive\Desktop\Geo-lab\projects\school-gis\app"
python -m http.server 8787
```

브라우저에서 `http://127.0.0.1:8787`를 엽니다.

## 검증

```powershell
cd "C:\Users\HANSOL\OneDrive\Desktop\Geo-lab"
npm.cmd run test:gis:syntax
```

## Cloudflare Pages

권장 설정:

- Framework preset: `None`
- Root directory: `projects/school-gis/app`
- Build command: 비움
- Build output directory: `.`
- Functions/Worker: `projects/school-gis/app/_worker.js`

필요한 Cloudflare 환경변수:

- `SGIS_CONSUMER_KEY`
- `SGIS_CONSUMER_SECRET`
- 선택: `SGIS_API_BASE_URL`

기본 프록시 경로:

- `/api/sgis/population`

## 공개 주소

- 기본: [https://geo-lab-school-gis.pages.dev/](https://geo-lab-school-gis.pages.dev/)
- 대한민국 통계: [https://geo-lab-school-gis.pages.dev/?view=korea](https://geo-lab-school-gis.pages.dev/?view=korea)
