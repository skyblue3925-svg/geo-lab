# Geo-Lab Projects

Geo-Lab은 현재 세 개의 프로젝트로 분리되어 있습니다.

## 1. Terrain Lab

Path: `projects/terrain-lab/`

지형 애니메이션, GIF 갤러리, 고등학교 세계지리, 지형 물리 Lab을 담당합니다.

- Source: `projects/terrain-lab/src/`
- Root compatibility wrappers: `app/`, `engine/`, `pages/`, `app.py`
- Run: `.\run_geo_lab.ps1`
- Verify: terrain pytest suite in root `tests/`

## 2. Koppen Climate

Path: `projects/koppen-climate/`

쾨펜 기후 그래프 정적 웹앱입니다.

- Source: `projects/koppen-climate/app/`
- Static deploy copy: `projects/koppen-climate/static/`
- Run: `cd projects\koppen-climate\app; python -m http.server 8765`
- Verify: `npm.cmd run test:koppen`
- Deploy root: `projects/koppen-climate/static`

## 3. School GIS

Path: `projects/school-gis/`

학교 주변 GIS 수업용 정적 웹앱입니다.

- Source: `projects/school-gis/app/`
- Run: `cd projects\school-gis\app; python -m http.server 8787`
- Verify: `npm.cmd run test:gis:syntax`
- Deploy root: `projects/school-gis/app`

## Shared Repository Areas

- `knowledge/`: Obsidian/LLM wiki layer
- `docs/`: cross-project planning and deployment documents
- `.deploy/`: local deployment mirrors
- `assets/`, `scripts/`, `tests/`: still partially shared, especially for Terrain Lab

## Migration Status

The primary project boundaries are in place. The remaining migration work is deployment mirror cleanup, optional movement of terrain assets/scripts/tests, and project-specific CI/deploy documentation.

