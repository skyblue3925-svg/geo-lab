# 지형물리 Lab 구현 청사진

## 제품 방향

Geo-Lab의 지형 콘텐츠는 두 층으로 나눈다.

1. 학생용 설명층: GIF 갤러리와 고등학교 세계지리 화면에서 지형 형성과정을 빠르게 이해한다.
2. 실험실층: 사용자가 시간, 유량, 파랑, 빙하, 지하수, 점성 같은 요인을 조절하며 지형 형성과정이 어떻게 달라지는지 실험한다.
3. 연구자층: 드론 사진, 영상, DEM/DSM을 넣고 현재 지형에서 가능한 형성 요인과 과거 경로를 역추정한다.

학생용 GIF는 정답을 보여주는 설명 자료이고, Lab은 조건을 바꾸며 가능한 결과 범위를 탐색하는 모델이다. 연구자층은 “과거를 확정”하는 도구가 아니라, 관측 자료와 맞는 복수의 형성과정 시나리오와 불확실성을 보여주는 도구로 설계해야 한다.

## 현재 연결된 무API 제작 흐름

추가 지형 12개는 API 키 없이도 같은 제작 단계를 재현할 수 있게 했다.

```powershell
python scripts/build_additional_landform_image_sequences.py --force
```

이 명령은 `docs/TERRAIN_ADDITIONAL_IMAGE_SEQUENCE_SPECS.json`의 카탈로그를 읽고, 로컬 절차적 지형 표면으로 5x6 필름스트립을 만든 뒤, WebP 애니메이션과 GIF 갤러리용 파일까지 다시 생성한다. `--only oxbow_lake,esker`처럼 일부 지형만 다시 만들 수도 있다.

카탈로그 연결은 세 화면이 같은 원천을 읽는 구조로 둔다.

| 연결 지점 | 역할 |
| --- | --- |
| `app/services/terrain_lab_catalog.py` | 지형별 형성 단계, 조절 요인, 기본값, SimpleLEM 배율 변환 |
| `pages/3_🧪_Lab.py` | “추가 지형” 시나리오와 요인 슬라이더 |
| `pages/9_Animation_Studio.py` | 선택 지형의 카탈로그 단계와 Lab 조절 요인 확인 |
| `assets/cinematic/image_sequence/*` | 학생용 WebP/GIF 애니메이션 자산 |

## 핵심 아키텍처

Clean Architecture 기준으로 의존 방향을 안쪽으로 고정한다.

| 층 | 역할 | 현재 연결 후보 |
| --- | --- | --- |
| Domain | 지형 상태, 과정, 요인, 시나리오, 관측 자료, 역산 결과 | 신규 `terrain_lab` 도메인 모델 |
| Application | 시나리오 실행, 요인 스윕, 관측-모델 비교, 결과 요약 | `app/utils/lab_model.py`, 신규 use case 모듈 |
| Infrastructure | SimpleLEM, DEM/영상 로더, 최적화기, 렌더러 payload 변환 | `engine/simple_lem.py`, `app/services/terrain_3d_payload.py` |
| Presentation | Streamlit Lab, 고등학교 3D 보기, 연구자용 업로드 UI | `pages/3_🧪_Lab.py`, `pages/8_🏫_High_School_Geography.py` |

렌더러는 도메인 규칙이 아니다. Three.js와 Babylon.js는 `surfaceFrames`, `waterDepthFrames`, `erosionFrames`, `depositionFrames`, `flowFrames`, `stageHistory` 같은 공통 payload를 받아 그리는 어댑터로 둔다.

## 물리 모델 토대

| 계열 | 기본 식 또는 규칙 | 조절 요인 | 교육 포인트 |
| --- | --- | --- | --- |
| 하천 | stream power erosion, 퇴적물 수지, 측방 침식 | 유량, 경사, 침식계수, 입경, 기준면 | 침식과 퇴적이 같은 하천 안에서 위치별로 다르게 나타난다. |
| 해안 | 파랑 기저부 침식, 연안류 퇴적, 해수면 변화 | 파랑 에너지, 파향, 연안류, 퇴적물 공급, 해수면 | 해안선은 앞으로만 자라지 않고 후퇴·퇴적·분리된다. |
| 빙하 | 빙하 침식, 암설 운반, 빙하 퇴적 | 빙하 두께, 유속, 융빙수, 말단 위치, 암설량 | 같은 얼음 작용도 U자곡, 모레인, 드럼린, 에스커를 다르게 만든다. |
| 화산 | 분출률, 점성, 붕괴, 지하수 접촉 | 점성, 분출률, 수분, 화산쇄설물 비율 | 쌓이는 과정과 폭발·붕괴가 함께 지형을 만든다. |
| 카르스트 | 용식, 절리 밀도, 지하수위, 배수 | 석회암 순도, 절리, 강수량, 지하수위 | 표면 침식보다 지하 배수와 용해가 형태를 좌우한다. |
| 건조·풍성 | 바람 전단, 모래 공급, 간헐 하천 | 풍향, 풍속, 모래 공급, 식생, 강우 이벤트 | 바람 방향과 공급량이 사구 이동과 형태를 결정한다. |
| 구조·사면 | 융기, 단층 변위, 확산, 임계경사 붕괴 | 융기율, 단층 변위, 마찰각, 풍화 | 내적 작용이 골격을 만들고 외적 작용이 표면을 다듬는다. |

## 구현 단계

### 0단계: 공통 지형 시나리오 카탈로그

- 38개 기존 지형과 추가 12개 지형을 같은 ID 체계로 정리한다.
- 각 지형에 `title_ko`, `group`, `process_family`, `process_factors`, `surface_generator`, `image_sequence_prompt`를 붙인다.
- 이미 추가한 12개는 `docs/TERRAIN_ADDITIONAL_IMAGE_SEQUENCE_SPECS.json`을 기준으로 관리한다.

### 1단계: 학생용 GIF 제작 확장

- 5x6, 30프레임 필름스트립 계약을 고정한다.
- 생성 결과는 `scripts/import_filmstrip_sequence.py`로 WebP/GIF를 만든다.
- 품질검사는 프레임 수, 셀 경계, 위아래 래핑, 카메라 일관성, 지형 형성 순서를 본다.

### 2단계: Lab v0 물리 샌드박스

- SimpleLEM 실행 결과에서 다음 payload를 안정적으로 만든다.
- `surfaceFrames`: 지형 높이장
- `erosionFrames`: 침식 강도
- `depositionFrames`: 퇴적 강도
- `waterDepthFrames`: 하도·호수·해안 수면
- `flowFrames`: 유동 방향
- `stageHistory`: 수업용 단계 설명

우선 하천, 해안, 빙하 세 계열을 직접 연결한다. 화산·카르스트·건조는 절차 생성기 기반 proxy로 시작하고, 물리 파라미터를 점진적으로 강화한다.

### 3단계: 렌더러 분리

Three.js와 Babylon.js를 경쟁시키기보다 같은 payload를 받는 두 렌더러로 둔다.

- Three.js: 이미 붙어 있으므로 빠른 유지보수와 현 화면 호환에 유리하다.
- Babylon.js: 카메라, 재질, GUI, 씬 상태 관리가 편해 실험실형 인터랙션에 유리하다.
- 결론: Babylon이 항상 월등한 것은 아니다. 이 프로젝트에서는 `renderer-neutral payload`를 먼저 안정화하고, Babylon은 Lab 전용 고품질 렌더러로 병렬 확장한다.

### 4단계: 연구자용 역산 prototype

입력 자료:

- DEM/DSM GeoTIFF
- 드론 정사영상
- 드론 영상 또는 다중 시점 사진
- 수치지도, 하천망, 해안선, 지질도, 강수·해수면 자료

처리 흐름:

1. 좌표계·해상도 정규화
2. 경사, 곡률, 능선·곡저선, 하천망, 해안선, 분지 경계 추출
3. 지형 계열 후보 분류
4. 관측 지표와 맞는 요인 조합을 ensemble로 탐색
5. 여러 가능한 형성과정 경로와 불확실성 표시

출력은 “가장 그럴듯한 하나의 과거”가 아니라, 관측 자료를 만족하는 후보 시나리오 묶음이어야 한다.

## 오늘 바로 가능한 구현 범위

1. 추가 12개 지형의 ID, 한글명, 분류, 제작 프롬프트, 절차 표면 alias를 등록한다.
2. 에스커처럼 기존 생성기가 없는 지형은 가벼운 절차 생성기를 추가한다.
3. `build_terrain_3d_payload()`가 추가 지형 ID를 받아 3D 표면과 overlay payload를 만들 수 있게 한다.
4. Lab은 추가 지형명을 받았을 때 적절한 SimpleLEM 계열 파라미터를 선택하도록 연결한다.
5. 실제 이미지/GIF 생성은 API 키나 별도 이미지 생성 도구가 준비되는 즉시 JSON 스펙을 입력으로 진행한다.

## 품질 기준

- 학생용 GIF는 한눈에 형성과정 순서가 읽혀야 한다.
- 3D Lab은 물리적으로 완벽하기보다 조절 요인과 결과 방향이 일관되어야 한다.
- 연구자용 도구는 정답처럼 보이는 단일 결과를 피하고 불확실성을 화면에 드러내야 한다.
- 렌더러의 화려함보다 `processFrames`와 `stageHistory`의 신뢰성이 우선이다.
