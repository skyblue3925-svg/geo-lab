# Cloudflare Pages 배포 가이드

`school-neighborhood-gis`는 정적 자산 + Pages advanced mode `_worker.js` 조합으로 배포합니다.

## 1. 배포 자산 준비

```powershell
& "C:\Users\HANSOL\OneDrive\Desktop\Geo-lab\apps\school-neighborhood-gis\scripts\prepare-pages-deploy.ps1"
```

기본 출력 폴더:

- `C:\Users\HANSOL\OneDrive\Desktop\Geo-lab\.deploy\school-neighborhood-gis-pages`

이 폴더 안에는:

- 정적 앱 파일
- `_worker.js`

가 함께 준비됩니다.

## 2. Cloudflare Pages 프로젝트 설정

- Framework preset: `None`
- Build command: 비워두기
- Build output directory: 배포 스크립트로 준비한 폴더

CLI 예시:

```powershell
cmd /c npx wrangler pages deploy "C:\Users\HANSOL\OneDrive\Desktop\Geo-lab\.deploy\school-neighborhood-gis-pages" --project-name geo-lab-school-gis
```

## 3. 환경변수

Pages 프로젝트에 아래 값을 넣습니다.

- `SGIS_CONSUMER_KEY`
- `SGIS_CONSUMER_SECRET`

선택:

- `SGIS_API_BASE_URL`

기본값은 공식 SGIS OpenAPI v3 주소입니다.

## 4. runtime-config.js

[runtime-config.js](C:/Users/HANSOL/OneDrive/Desktop/Geo-lab/apps/school-neighborhood-gis/runtime-config.js)에서 학교별 설정만 바꾸면 됩니다.

예시:

```js
window.__SCHOOL_GIS_RUNTIME_CONFIG__ = {
  schoolName: "예시고등학교",
  mapCenter: {
    lat: 37.5665,
    lng: 126.978,
    label: "학교 중심",
  },
  schoolRadiusMeters: 1000,
  sgis: {
    enabled: true,
    proxyPath: "/api/sgis",
    defaultMetric: "tot_ppltn",
    defaultYear: 2023,
    defaultAdmCd: "",
    defaultLowSearch: "1",
  },
};
```

## 5. 운영 팁

- 학생은 URL만 열면 됩니다.
- SGIS 키와 시크릿은 브라우저에 넣지 말고 Cloudflare 환경변수로만 관리하세요.
- 첫 운영은 `전국 시도 총인구`, `서울 시군구 평균연령` 같은 1~2개 케이스부터 시작하는 편이 안전합니다.
