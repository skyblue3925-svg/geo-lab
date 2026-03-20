# Cloudflare Pages Deploy

이 문서는 `apps/koppen-climate-lab` 앱을 `Cloudflare Pages + Git 연동`으로 배포할 때 사용하는 기준 설정입니다.

## Recommended Setup

- Git provider: `GitHub`
- Repository: `skyblue3925-svg/geo-lab`
- Production branch: `master`
- Framework preset: `None`
- Root directory: `apps/koppen-climate-lab`
- Build command: `exit 0`
- Build output directory: `.`

## Why This Works

- 이 앱은 정적 웹앱입니다.
- 서버 코드, 데이터베이스, 비밀키가 없습니다.
- `index.html`, `app.js`, `styles.css`, `data/*` 파일만 그대로 서빙하면 됩니다.

## Before First Deploy

반드시 포함되어야 하는 파일:

- `apps/koppen-climate-lab/index.html`
- `apps/koppen-climate-lab/app.js`
- `apps/koppen-climate-lab/styles.css`
- `apps/koppen-climate-lab/climate-model.mjs`
- `apps/koppen-climate-lab/lesson-data.mjs`
- `apps/koppen-climate-lab/world-map-data.mjs`
- `apps/koppen-climate-lab/data/koppen-geiger-1991-2020.mjs`
- `apps/koppen-climate-lab/data/koppen-geiger-1991-2020-0p1.bin`
- `apps/koppen-climate-lab/data/real-climate-data.mjs`
- `apps/koppen-climate-lab/data/world-land-110m.geojson`
- `apps/koppen-climate-lab/data/world-countries-110m.geojson`

올리지 않아도 되는 원본 전처리 파일:

- `apps/koppen-climate-lab/data/worldclim/raw/`
- `apps/koppen-climate-lab/data/koppen-official/`

## Dashboard Steps

1. GitHub에 변경사항을 push합니다.
2. Cloudflare Dashboard에서 `Workers & Pages` 로 이동합니다.
3. `Create application` 을 누릅니다.
4. `Pages` 를 선택합니다.
5. `Connect to Git` 를 선택합니다.
6. `skyblue3925-svg/geo-lab` 저장소를 연결합니다.
7. 아래 설정값을 입력합니다.

```text
Framework preset: None
Root directory: apps/koppen-climate-lab
Build command: exit 0
Build output directory: .
```

8. `Save and Deploy` 를 누릅니다.

## After Deploy

- 기본 주소는 `*.pages.dev` 로 생성됩니다.
- 이후 `Custom domains` 에서 학교용 도메인을 연결할 수 있습니다.
- `master` 브랜치에 push할 때마다 자동 배포됩니다.
- 브랜치/PR 단위 미리보기 URL도 사용할 수 있습니다.

## Local Verification

배포 전 로컬 확인:

```powershell
cd "C:\Users\HANSOL\OneDrive\Desktop\Geo-lab\apps\koppen-climate-lab"
python -m http.server 8765
```

브라우저에서 `http://127.0.0.1:8765` 확인

## Notes

- 이 앱은 `fetch("./data/...")` 를 사용하므로 파일 더블클릭 실행이 아니라 HTTP 서빙이 필요합니다.
- Cloudflare Pages Git 연동형은 운영과 수정 이력 관리에 가장 적합합니다.
- 배포 후 색상, 문구, 데이터 파일만 바꿔도 다시 빌드 없이 정적 재배포가 가능합니다.
