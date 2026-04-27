---
id: hyperframes-terrain-video-assessment
type: synthesis
layer: curated
status: active
created: 2026-04-27
updated: 2026-04-27
tags:
  - terrain-lab
  - video
  - hyperframes
aliases:
  - HyperFrames Terrain Video Assessment
---

# HyperFrames Terrain Video Assessment

## 확인한 내용

HyperFrames는 HTML, CSS, JavaScript로 작성한 화면을 프레임 단위로 캡처해 MP4로 렌더링하는 HTML-to-video 프레임워크다. 공식 문서 기준으로 GSAP, Lottie, CSS, Three.js 같은 웹 애니메이션 런타임을 사용할 수 있고, 같은 입력이 같은 결과를 내는 deterministic render를 목표로 한다.

## Geo-Lab 적용 가능성

Geo-Lab에는 세 가지 적용 후보가 있다.

1. GIF 갤러리의 지형 형성 설명을 MP4 영상으로 변환
2. Animation Studio의 이미지 시퀀스를 제목, 단계 설명, 화살표, 강조선과 함께 수업용 영상으로 렌더링
3. Lab의 물리모델 결과를 시간 단계별 그래프, 작용장 heatmap, 3D 표면 캡처와 합성해 연구/수업용 설명 영상으로 출력

## 장점

- HTML 기반이라 기존 Streamlit/Plotly/Three.js/Babylon.js 자산과 사고방식이 잘 맞는다.
- 영상 편집 도구보다 코드 리뷰와 버전 관리가 쉽다.
- API key 없이 로컬 렌더링 후보로 검토할 수 있다.
- GIF보다 공유용 MP4가 가볍고 재생 호환성이 좋을 수 있다.

## 리스크

- Node, Chromium, FFmpeg 계열 의존성이 늘어난다.
- 현재 Geo-Lab의 Streamlit UI 안에 바로 넣으면 런타임이 무거워질 수 있다.
- 첫 적용은 제품 페이지가 아니라 `experiments/hyperframes-terrain-video/` 같은 별도 실험 폴더가 적절하다.
- 지형 교육용 품질은 렌더러보다 스토리보드, 프레임 선별, 자막 설계가 더 중요하다.

## 제안

첫 실험은 `waterfall` 또는 `barchan` 하나만 대상으로 한다. 입력은 기존 GIF/이미지 시퀀스, 출력은 20~30초 MP4다. 화면 구성은 왼쪽 영상, 오른쪽 단계 설명, 하단 진행 바와 핵심 작용장 라벨로 제한한다. 성공하면 Animation Studio의 “수업용 MP4 내보내기”로 확장한다.
