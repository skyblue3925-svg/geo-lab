# Student GIS Layer Lab

학생이 일반 지도 위에 공공 레이어와 자기 조사 레이어를 겹쳐 보면서 GIS를 체험하는 교육용 webGIS MVP입니다.

## 현재 구현 범위

- `학교 주변` / `대한민국 통계` 화면 전환
- 학교 주변 기본 공개 레이어
- 대한민국 샘플 통계 + 시설 레이어
- 학생 레이어 생성
- 지도 클릭으로 직접 포인트 추가
- CSV / GeoJSON 포인트 업로드
- 외부 GeoJSON / CSV URL 가져오기
- `runtime-config.js` 기반 프리셋 공공 레이어 가져오기
- 기본 실습용 프리셋 레이어 3종 내장
- SGIS 실데이터 레이어 가져오기
  - `hadmarea.geojson` 경계
  - `population.json` 통계값
  - 프론트에서 choropleth 스타일 적용
- 모바일 / 태블릿 대응
- 현재 보이는 레이어 GeoJSON 내보내기

## 로컬 실행

```powershell
cd "C:\Users\HANSOL\OneDrive\Desktop\Geo-lab\apps\school-neighborhood-gis"
python -m http.server 8787
```

브라우저에서 `http://127.0.0.1:8787`를 열면 됩니다.

## 라이브 주소

- 기본: [https://geo-lab-school-gis.pages.dev/](https://geo-lab-school-gis.pages.dev/)
- 대한민국 통계 바로가기: [https://geo-lab-school-gis.pages.dev/?view=korea](https://geo-lab-school-gis.pages.dev/?view=korea)

## SGIS 실데이터 연결 방식

브라우저에서 SGIS 시크릿을 직접 들고 호출하면 안 되므로, Cloudflare Pages Functions를 프록시로 둡니다.

- 프론트엔드: [app.js](C:/Users/HANSOL/OneDrive/Desktop/Geo-lab/apps/school-neighborhood-gis/app.js)
- SGIS 어댑터: [sgis-adapter.js](C:/Users/HANSOL/OneDrive/Desktop/Geo-lab/apps/school-neighborhood-gis/sgis-adapter.js)
- Cloudflare 워커: [_worker.js](C:/Users/HANSOL/OneDrive/Desktop/Geo-lab/apps/school-neighborhood-gis/_worker.js)

Cloudflare 환경변수:

- `SGIS_CONSUMER_KEY`
- `SGIS_CONSUMER_SECRET`
- 선택: `SGIS_API_BASE_URL`

기본 프록시 경로:

- `/api/sgis/population`

## 배포 준비

배포용 정적 파일과 Functions는 아래 스크립트로 묶습니다.

- [prepare-pages-deploy.ps1](C:/Users/HANSOL/OneDrive/Desktop/Geo-lab/apps/school-neighborhood-gis/scripts/prepare-pages-deploy.ps1)

실행 예시:

```powershell
& "C:\Users\HANSOL\OneDrive\Desktop\Geo-lab\apps\school-neighborhood-gis\scripts\prepare-pages-deploy.ps1"
```

그 다음 `wrangler pages deploy`로 그대로 배포하면 `_worker.js`가 함께 올라갑니다.

## 다음 단계

1. SGIS 실계정 값을 Cloudflare 환경변수로 넣기
2. 실제 배포 후 SGIS 레이어 호출 확인
3. KOSIS 지표 1개를 SGIS 경계와 조인해 추가하기
4. 학생 레이어를 반/팀 단위 공유 저장소로 확장하기
