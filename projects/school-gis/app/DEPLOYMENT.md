# 학생 GIS 작업공간 배포 체크리스트

이 앱은 정적 프론트엔드와 Cloudflare Pages `_worker.js` SGIS 프록시로 배포한다.

## 필수 설정

1. Kakao Developers에서 배포 도메인을 JavaScript 키 플랫폼 도메인에 등록한다.
2. Cloudflare Pages 환경변수에 SGIS 키를 저장한다.
3. 배포 전 `scripts/prepare-pages-deploy.ps1`로 배포 폴더를 만든다.

## Cloudflare Pages 환경변수

필수:

- `SGIS_CONSUMER_KEY`
- `SGIS_CONSUMER_SECRET`

선택:

- `SGIS_API_BASE_URL`

SGIS 키는 브라우저에 노출하지 않는다. `_worker.js`가 서버 프록시로 SGIS 요청을 처리한다.

## 배포 명령

```powershell
& ".\apps\school-neighborhood-gis\scripts\prepare-pages-deploy.ps1"
npx.cmd wrangler pages deploy ".\.deploy\school-neighborhood-gis-pages" --project-name geo-lab-school-gis
```

## 배포 전 확인

- 모바일 390px 화면에서 가로 스크롤이 없어야 한다.
- 카카오 SDK가 실패해도 기본 지도로 폴백되어야 한다.
- 위치 검색 후 사용자가 위치 고정을 확인해야 SGIS 가져오기가 활성화된다.
- SGIS 격자 데이터가 없으면 “값 없음” 안내가 떠야 한다.
- 지도 아래 Layer Hub에서 공공/학생 레이어를 켜기, 끄기, 보기, 삭제할 수 있어야 한다.
- Playwright 로컬 테스트가 통과해야 한다.

```powershell
npx.cmd playwright test --config=apps/school-neighborhood-gis/playwright.local.config.js --project=chromium
```
