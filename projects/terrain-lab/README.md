# Terrain Lab

제작자: 한백고등학교 김한솔

Terrain Lab은 지형 애니메이션, GIF 갤러리, 고등학교 세계지리 수업 화면, 지형 물리 Lab을 담당하는 Geo-Lab의 핵심 프로젝트입니다.

## 경로

- 실제 소스: `projects/terrain-lab/src/`
- Streamlit 호환 진입점: 루트 `app.py`
- 루트 wrapper: `app/`, `engine/`, `pages/`
- 지형 이미지/GIF 자산: 루트 `assets/cinematic/`
- 지형 관련 테스트: `projects/terrain-lab/tests/`

## 로컬 실행

```powershell
cd "C:\Users\HANSOL\OneDrive\Desktop\Geo-lab"
.\run_geo_lab.ps1
```

Streamlit을 직접 실행할 때:

```powershell
.\.venv\Scripts\streamlit.exe run app.py
```

## 검증

```powershell
powershell -ExecutionPolicy Bypass -File .\projects\terrain-lab\test.ps1
```

빠른 핵심 검증:

```powershell
powershell -ExecutionPolicy Bypass -File .\projects\terrain-lab\test.ps1 -Fast
```

브라우저 E2E 검증:

```powershell
npm.cmd run test:e2e
```

## 배포

- 현재 배포 호환 진입점은 루트 `app.py`입니다.
- `.deploy/hf-space/` mirror를 갱신할 때는 루트 wrapper와 `projects/terrain-lab/src/`를 함께 반영해야 합니다.
- 완전한 프로젝트 독립 배포로 전환하기 전까지는 루트 wrapper를 제거하지 않습니다.
