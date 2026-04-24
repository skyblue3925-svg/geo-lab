# Geo-Lab Beta Deployment

작성일: 2026-04-24

## 배포판 범위

이번 베타 배포판은 Streamlit 앱으로 유지한다.

- 공개: Animation Studio
- 공개: High School Geography
- 공개: Köppen Climate Graph
- 잠금/숨김: Gallery, Overview, Lab, Research, Case Mode, Higher Ed

`Animation Studio`가 중심 화면이며, 쾨펜 기후 그래프는 `apps/koppen-climate-lab` 정적 앱을 `static/koppen-climate-lab/`로 복사해 Streamlit iframe 안에서 표시한다.

## 변경된 실행 구조

- `app.py`: 베타 홈 화면과 베타 사이드바만 렌더링한다.
- `.streamlit/config.toml`: Streamlit 기본 멀티페이지 사이드바를 숨기고 정적 파일 서빙을 켠다.
- `pages/5_☁️_Climate.py`: 기존 Streamlit Climate Lab 대신 Köppen Climate Graph wrapper로 동작한다.
- `pages/8_🏫_High_School_Geography.py`: 베타 사이드바를 표시한다.
- `pages/9_Animation_Studio.py`: 베타 사이드바를 표시한다.

## 로컬 검증

```powershell
cd "C:\Users\HANSOL\OneDrive\Desktop\Geo-lab"
.\venv\Scripts\python.exe -m streamlit run app.py --server.port=8501
```

확인할 URL:

- `http://localhost:8501`
- `http://localhost:8501/Animation_Studio`
- `http://localhost:8501/High_School_Geography`
- `http://localhost:8501/Climate`

## 권장 배포 대상

이 프로젝트는 Python/Streamlit 런타임이 필요하므로 전체 Geo-Lab 베타는 Streamlit Community Cloud 또는 Hugging Face Spaces가 가장 단순하다.

Cloudflare Pages는 정적 사이트에 적합하므로 `apps/koppen-climate-lab` 단독 배포에는 맞지만, 현재 Streamlit 베타 전체를 그대로 올리는 대상은 아니다.

## Streamlit Community Cloud 설정

- Repository: 이 저장소
- Branch: 배포할 브랜치
- Main file path: `app.py`
- Python requirements: `requirements.txt`

현재 `requirements.txt`는 베타 배포용으로 PyVista/stpyvista를 제외했다. Animation Studio의 3D 화면은 Three.js HTML 컴포넌트로 실행된다.

## 프레임 속도

이미지 시퀀스 animated WebP는 12fps에서 11fps로 낮췄다. 아주 약간 느린 전환을 목표로 한 값이며, metadata의 `fps`도 11로 맞춘다.
