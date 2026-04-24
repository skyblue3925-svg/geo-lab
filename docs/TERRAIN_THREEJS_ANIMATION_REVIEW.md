# Terrain Three.js Animation Review

작성일: 2026-04-24

## 현재 상태

- 이미지 기반 애니메이션 자산은 `assets/cinematic/image_sequence/` 아래에서 관리한다.
- 각 지형은 `filmstrip/{landform}_filmstrip.png`, `frames/frame_000.png`부터 `frame_029.png`, `{landform}_image_sequence.webp`를 가진다.
- `pages/9_Animation_Studio.py`는 원본 스토리보드, 이미지 시퀀스 WebP, 키프레임 preview, 실험용 Three.js 뷰어를 한 화면에 묶는다.
- `app/components/threejs_renderer.py`는 필름스트립 PNG를 Three.js 텍스처로 읽고, `app/services/animation_assets.py`의 `sample_landform_surface_sequence()`가 만든 절차적 높이장을 함께 재생한다.

## 확인된 문제

1. 이미지와 3D 지형의 의미가 아직 분리되어 있다.
   - 현재 Three.js 뷰어는 필름스트립의 현재 셀을 지형 메쉬 텍스처로 입힌다.
   - 높이장은 `landform_id` 기반 절차적 표면이고, 생성 이미지의 실제 지형 형태를 복원한 것은 아니다.
   - 따라서 화면은 "이미지 시퀀스 + 비슷한 3D 표면"이지, 이미지에서 추출한 3D 애니메이션은 아니다.

2. 물리 과정장이 Three.js payload로 넘어가지 않는다.
   - `engine/simple_lem.py`는 `last_process_fields`와 `process_history`에 `erosion`, `deposition`, `marine`, `glacial`, `karst`, `aeolian`, `tectonic` 등을 저장한다.
   - `app/utils/lab_model.py`의 `build_lab_stage_history()`는 이 process field를 이용해 단계와 overlay type을 분류한다.
   - `app/components/animation_renderer.py`에는 overlay 추출과 Plotly overlay 렌더링이 이미 있다.
   - 하지만 `app/components/threejs_renderer.py` payload에는 `processFrames`, `waterDepthFrames`, `stageHistory` 같은 물리/교육 레이어가 없다.

3. 카메라 움직임이 지형 과정 설명보다 강하다.
   - Three.js 뷰어는 자동 카메라 이동을 계속 수행한다.
   - 필름스트립 자체도 30프레임 과정 변화를 담고 있으므로, 카메라 이동이 강하면 학생은 지형 변화와 시점 변화를 혼동할 수 있다.
   - 특히 사구, 삼각주, 해안 지형처럼 평면 형태가 중요한 지형은 고정 또는 매우 약한 카메라가 더 적합하다.

4. 물과 퇴적 표현이 정적이다.
   - 현재 Three.js water mesh는 원형 반투명 평면 하나에 가깝다.
   - 해안, 삼각주, 에스추어리, 리아스식 해안, 플라야, 피오르처럼 수면 변화가 핵심인 지형에서 실제 수심/범람/침수 진행을 표현하지 못한다.

5. 자산 품질 검수 루프가 시각적으로만 끝난다.
   - `import_filmstrip_sequence.py`는 30프레임 분할과 WebP 생성은 안정적으로 수행한다.
   - 그러나 지형별로 "과정이 맞는가", "카메라가 고정됐는가", "텍스트/라벨이 없는가" 같은 QA 결과를 metadata에 남기지는 않는다.

## 권장 해결 방향

### 1단계: 이미지 기반 애니메이션을 canonical preview로 둔다

- Animation Studio와 Learn에서 `*_image_sequence.webp`를 최우선 애니메이션으로 표시한다.
- 기존 4단계 storyboard 기반 preview는 fallback 또는 비교용으로 낮춘다.
- metadata에는 `source_filmstrip`, `frame_count`, `fps`, `status` 외에 `qa_status`, `qa_notes`를 추가할 수 있다.

### 2단계: Three.js를 "이미지 기반 3D 보조 뷰어"로 정리한다

- `threejs_renderer.py` payload를 아래처럼 확장한다.
  - `textureFrames`: 현재는 filmstrip offset으로 처리 중이므로 유지 가능.
  - `surfaceFrames`: 현재 절차적 높이장.
  - `stageHistory`: `build_lab_stage_history()` 결과의 축약본.
  - `processFrames`: erosion/deposition/tectonic 등 normalized field.
  - `waterDepthFrames`: 수면/침수/범람 표현이 필요한 지형 전용.
- UI에는 "실험용 3D 보조 뷰어"라고 명확히 두고, 이미지 원본과 물리 overlay가 같은 원천이 아니라는 점을 내부적으로 구분한다.

### 3단계: 첫 프로토타입은 하천/삼각주 계열로 좁힌다

우선순위는 `alluvial_fan`, `delta`, `braided_river`, `estuary`가 좋다.

- 이유:
  - `SimpleLEM`의 `sediment_transport`, `stream_power_erosion`, `deposition` 필드와 연결하기 쉽다.
  - 학생이 색상 overlay로 침식/운반/퇴적을 읽기 쉽다.
  - 이번에 생성한 30프레임 이미지가 평면 과정 변화를 잘 담고 있다.

구현 흐름:

1. `SimpleLEM.run()`으로 저장된 `history`, `stats_history`, `process_history`를 확보한다.
2. `build_lab_stage_history()`로 stage와 overlay type을 만든다.
3. `threejs_renderer.py`에서 process field를 다운샘플링하고 0-1 정규화해 payload에 넣는다.
4. Three.js에서 process overlay plane 또는 vertex color layer를 추가한다.
5. 카메라는 기본 고정으로 두고, 사용자가 `fixed`, `slow orbit`, `plan view`를 선택하게 한다.

### 4단계: 이미지에서 직접 3D를 만드는 것은 별도 연구 트랙으로 둔다

현재 생성 filmstrip은 교육용 contact sheet이며, 각 셀은 단일 2D 렌더다. 여기서 안정적인 3D 메쉬를 바로 복원하려면 depth estimation이나 multi-view 일관성이 필요하다. 지금 바로 구현할 현실적인 경로는 다음 순서다.

1. 단기: 생성 이미지는 텍스처/배경/정답 preview로 사용하고, 지형 높이장은 기존 generator 또는 SimpleLEM이 담당한다.
2. 중기: 지형별 procedural surface를 생성 이미지의 형태와 더 비슷하게 보정한다.
3. 장기: depth map 추정 또는 별도 이미지 생성 프롬프트로 `height map`, `albedo`, `process mask`를 함께 생산한다.

## 바로 실행할 작업 목록

1. `threejs_renderer.py` payload에 `stageHistory`와 `processFrames`를 추가한다.
2. `animation_assets.py`에 process field를 작은 배열로 직렬화하는 helper를 둔다.
3. `pages/9_Animation_Studio.py`에 Three.js 표시 모드를 추가한다.
   - `텍스처만`
   - `높이장`
   - `과정 overlay`
4. 하천/삼각주 지형 1개로 프로토타입을 만들고, `tests/test_simple_lem_process_history.py`와 `tests/test_lab_stage_history.py`를 기준으로 회귀 테스트를 붙인다.
5. 검증 후 coastal/glacial/karst/aeolian로 확장한다.

## 판단

현재 가장 안전한 제품 방향은 30프레임 이미지 시퀀스를 수업용 canonical animation으로 쓰고, Three.js는 물리 과정장을 겹쳐 보여주는 보조 해설 레이어로 키우는 것이다. 이미지에서 바로 3D를 복원하는 방향은 매력적이지만, 지금 단계에서는 품질과 일관성 리스크가 크다.
