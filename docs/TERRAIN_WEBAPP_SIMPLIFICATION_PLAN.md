# Geo-Lab 웹앱 구조 단순화 계획

## 문제

현재 `Gallery`가 학생용 카탈로그, 시네마틱 영상, 3D 실험, 텍스처 업로드, 세계 사례 연결을 동시에 담당한다. 그 결과 같은 지형 자산을 여러 위치에서 다시 찾고, 화면 목적도 섞여 있다.

## 목표 구조

1. `Learn`
   - 학생용 지형 형성 학습 화면.
   - 완성 애니메이션, 4단계 핵심 이미지, 간단한 프롬프트 확인만 제공한다.

2. `Animation Studio`
   - 제작자용 이미지·프롬프트·애니메이션 검수 화면.
   - 지형별 산출물 상태를 확인하고, 선택 지형의 고프레임 WebP 또는 GIF preview를 다시 빌드한다.

3. `Lab`
   - 기존 3D 시뮬레이션과 카메라 전환 실험 화면.
   - `생성 이미지 단계` 텍스처와 지형별 카메라 프리셋을 연결한다.

4. `Gallery`
   - 과도기 레거시 복합 화면.
   - 기능을 `Learn`, `Animation Studio`, `Lab`로 옮긴 뒤 축소하거나 제거한다.

## 1차 구현

- `app/services/animation_assets.py` 추가.
  - 생성 이미지, 프롬프트, 고프레임 WebP, GIF, 시네마틱 메타데이터의 경로 처리를 한 곳으로 모았다.
- `pages/0_Learn.py` 추가.
  - 학생용 단순 화면을 새로 만들었다.
- `pages/9_Animation_Studio.py` 추가.
  - 제작/검수용 화면을 새로 만들었다.
- `pages/1_📖_Gallery.py` 수정.
  - Gallery 내부의 시네마틱 메타데이터 병합과 생성 이미지 텍스처 로딩을 서비스로 위임했다.
  - Gallery가 단순 화면과 제작 화면으로 분리 중임을 표시했다.

## 2차 구현

- `scripts/build_storyboard_cinematic_animations.py` 추가.
  - 4개 핵심 이미지를 24fps, 136프레임, 약 5.7초 animated WebP로 변환한다.
  - 지형 묶음과 지형 ID에 따라 카메라 이동 방향을 다르게 적용한다.
- `assets/cinematic/storyboard_cinematic/` 생성.
  - 38개 지형의 `*_storyboard_cinematic.webp`를 생성했다.
  - `metadata.json`에 고프레임 자산의 fps, frame count, duration, source를 기록했다.
- `Learn`과 `Animation Studio` 수정.
  - 고프레임 WebP를 우선 표시하고, 없으면 기존 GIF preview를 fallback으로 표시한다.
  - `Animation Studio`에서 선택 지형의 고프레임 WebP와 GIF preview를 각각 재빌드할 수 있게 했다.
- `Gallery` 수정.
  - animated WebP도 시네마틱 영상 목록에서 이미지 애니메이션으로 표시한다.

## 다음 단계

1. Gallery의 `시네마틱 영상` 탭을 `Learn`으로 완전히 이동한다.
2. Gallery의 `인터랙티브 시네마틱` 실험을 `Lab` 또는 별도 `3D Studio`로 이동한다.
3. `Gallery`는 지형 검색/연결 허브만 남기거나 제거한다.
4. animated WebP 파이프라인을 기준으로, `ffmpeg` 사용 가능 환경에서는 같은 프레임을 MP4/WebM으로도 내보낸다.
5. 지형별 카메라 전환 규칙을 `app/services/camera_presets.py`로 분리한다.
