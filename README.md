# Geo-Lab

제작자: 한백고등학교 김한솔

Geo-Lab은 지형 교육, 쾨펜 기후 그래프, 학교 주변 GIS를 한 저장소에서 관리하는 교육용 지리 프로젝트 모음입니다.

## 프로젝트 구조

| 프로젝트 | 경로 | 역할 |
| --- | --- | --- |
| Terrain Lab | `projects/terrain-lab/` | 지형 애니메이션, GIF 갤러리, 고등학교 세계지리, 지형 물리 Lab |
| Koppen Climate | `projects/koppen-climate/` | 쾨펜 기후 그래프와 기후 자료 시각화 |
| School GIS | `projects/school-gis/` | 학교 주변 공공데이터/GIS 수업 앱 |

루트의 `app/`, `engine/`, `pages/` 일부는 현재 배포 호환성을 위한 얇은 wrapper입니다. 실제 Terrain Lab 소스는 `projects/terrain-lab/src/` 아래에 있습니다.

## 실행 명령

### Terrain Lab

```powershell
cd "C:\Users\HANSOL\OneDrive\Desktop\Geo-lab"
.\run_geo_lab.ps1
```

가상환경을 새로 맞춰야 할 때:

```powershell
.\run_geo_lab.ps1 -BootstrapVenv
```

Streamlit을 직접 실행할 때:

```powershell
.\.venv\Scripts\streamlit.exe run app.py
```

### Koppen Climate

```powershell
cd "C:\Users\HANSOL\OneDrive\Desktop\Geo-lab\projects\koppen-climate\app"
python -m http.server 8765
```

브라우저에서 `http://127.0.0.1:8765`를 엽니다.

### School GIS

```powershell
cd "C:\Users\HANSOL\OneDrive\Desktop\Geo-lab\projects\school-gis\app"
python -m http.server 8787
```

브라우저에서 `http://127.0.0.1:8787`를 엽니다.

## 검증 명령

### Terrain Lab

```powershell
.\.venv\Scripts\python.exe -m pytest projects\terrain-lab\tests\test_geomorphic_engine_presets.py projects\terrain-lab\tests\test_geomorphic_engine_force_fields.py projects\terrain-lab\tests\test_physics_lab_metadata.py projects\terrain-lab\tests\test_geomorphic_engine.py projects\terrain-lab\tests\test_morphometric_metrics.py projects\terrain-lab\tests\test_geomorphic_process_kernels.py projects\terrain-lab\tests\test_river_morphology_kernel.py projects\terrain-lab\tests\test_terrain_lab_catalog.py projects\terrain-lab\tests\test_page_syntax.py -q
```

프로젝트 스크립트로 실행할 때:

```powershell
powershell -ExecutionPolicy Bypass -File .\projects\terrain-lab\test.ps1
```

### Koppen Climate

```powershell
npm.cmd run test:koppen
```

### School GIS

```powershell
npm.cmd run test:gis:syntax
```

## 배포 경로

### Terrain Lab

- 현재 Streamlit/Hugging Face Space 호환 진입점: 루트 `app.py`
- 실제 앱 소스: `projects/terrain-lab/src/`
- 배포 mirror: `.deploy/hf-space/`
- 다음 배포 전 확인할 것: `.deploy/hf-space/`에 루트 wrapper와 `projects/terrain-lab/src/` 구조가 함께 반영되어야 합니다.

### Koppen Climate

- 앱 소스: `projects/koppen-climate/app/`
- 정적 배포 사본: `projects/koppen-climate/static/`
- Cloudflare Pages 권장 root directory: `projects/koppen-climate/static`
- Build command: 비움
- Build output directory: `.`

### School GIS

- 앱 소스 및 Cloudflare Pages root directory: `projects/school-gis/app/`
- Build command: 비움
- Build output directory: `.`
- SGIS 프록시: `projects/school-gis/app/_worker.js`

## 남은 일

1. `.deploy/` 아래 실제 배포 mirror를 새 프로젝트 구조에 맞게 갱신합니다.
2. Koppen 원자료 대용량 폴더는 Git에 넣지 않고 다운로드/재생성 스크립트로 관리하는 방향을 확정합니다.
3. Terrain Lab의 `assets/`, `scripts/`, `tests/`를 루트에 둘지, 프로젝트 내부로 더 옮길지 결정합니다.
4. wrapper 기반 호환 구조를 유지할지, 프로젝트별 완전 독립 실행 구조로 갈지 결정합니다.
5. 각 프로젝트별 CI와 배포 문서를 분리합니다.
