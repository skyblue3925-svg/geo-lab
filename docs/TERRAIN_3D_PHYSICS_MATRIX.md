# Terrain 3D Physics Matrix

작성일: 2026-04-24

## 1. 목적과 정확도 단계

이 문서는 38개 지형 3D 시뮬레이션을 빠르게 구현하기 위한 지형학/지질학 이론 기반 매트릭스이다. 목표는 연구용 수치모델이 아니라, 고등학교 지리 수업에서 “왜 이런 지형이 만들어지는가”를 일관되게 보여주는 것이다.

정확도 단계는 다음처럼 둔다.

| 단계 | 목표 | 허용 범위 | 검증 방식 |
| --- | --- | --- | --- |
| v1 교육용 시각 정확도 | 지형의 대표 형태와 지배 작용을 한눈에 이해 | 단순화된 높이장, 정규화된 침식/퇴적 overlay, 과장된 시간 스케일 | 교사/학생이 핵심 단서로 지형을 구분할 수 있는지 확인 |
| v2 모델 일관성 | 같은 process family 안에서 입력/출력 필드와 설명 문구를 통일 | SimpleLEM 및 procedural generator 혼합 사용 | `process_history`와 payload 필드가 누락 없이 이어지는지 확인 |
| v3 검증 확장 | 대표 사례 DEM, 사진, 문헌 설명과 비교 | 지형별 파라미터 보정, 일부 지형은 별도 모델 필요 | 기준 이미지/DEM과 형태 지표 비교 |

따라서 모든 지형에 대해 연구급 정확도를 약속하지 않는다. v1에서는 “지배 작용 -> 관찰 가능한 형태 -> 수업용 설명”의 연결을 우선한다.

## 2. 공통 3D payload 계약

Three.js 또는 다른 3D viewer는 지형별 구현 차이를 직접 알 필요가 없다. 모든 simulation adapter는 아래 payload를 반환한다.

| 필드 | 타입 | 의미 | v1 규칙 |
| --- | --- | --- | --- |
| `elevationFrames` | `number[][][]` | 시간별 표고 격자 | 모든 지형 필수. 0-1 정규화 또는 미터 단위 메타데이터 포함 |
| `waterDepthFrames` | `number[][][]` | 하천, 바다, 호수, 빙하 융빙수 등 물 깊이 | 물이 핵심이 아닌 지형은 0 배열 허용 |
| `erosionFrames` | `number[][][]` | 침식 강도 overlay | 하천, 해안, 빙하, 카르스트, 바람 침식에서 필수 |
| `depositionFrames` | `number[][][]` | 퇴적 강도 overlay | 선상지, 삼각주, 사구, 빙퇴적, 해안 퇴적에서 필수 |
| `flowFrames` | `{x:number[][], y:number[][]}[]` | 물, 얼음, 바람, 용암 이동 방향 | 방향성이 있는 지형은 필수. 정적 지형은 주요 축 벡터만 제공 가능 |
| `processLabels` | `string[]` | 프레임 또는 구간별 작용 라벨 | 예: `하방 침식`, `분류`, `파식`, `용식`, `분출` |
| `cameraProfile` | `object` | 기본 시점과 카메라 이동 방식 | `fixed`, `plan`, `low_oblique`, `valley_follow`, `coast_parallel`, `orbit_slow` 중 선택 |
| `teachingAnnotations` | `object[]` | 수업용 표식, 질문, 오개념 경고 | 관찰 단서와 “이 프레임에서 볼 것”을 짧게 제공 |

SimpleLEM와 연결할 때의 기본 매핑은 다음과 같다.

- `stream_power_erosion` -> `erosionFrames`, 하천 계열의 절단부 강조
- `sediment_transport` -> `depositionFrames`, 하류/하구/완사면 퇴적 강조
- `marine_erosion` -> `erosionFrames`, 해안 절벽, 해식 아치, 리아/피오르드 해수면 처리
- `glacial_erosion` -> `erosionFrames`, U자곡, 권곡, 아레트, 호른의 과굴식 강조
- `glacial_deposition` -> `depositionFrames`, 빙퇴석 또는 후퇴 단계 퇴적 강조
- `karst_dissolution` -> `erosionFrames`, 돌리네/우발라/카렌/탑카르스트의 용식 강조
- `aeolian_erosion` -> `erosionFrames`와 `depositionFrames`, 사구 이동과 풍식/퇴적 분리
- `volcanic_activity` -> `depositionFrames` 또는 `upliftFrames`에 준하는 표고 증가, 화산체 성장 강조
- `tectonic_faulting`, `tectonic_folding` -> `elevationFrames`의 구조적 초기 조건 및 `processLabels`
- `process_history` -> payload 생성 시 프레임별 overlay 원천

## 3. Process families

### River / Delta

하천 계열은 유량, 경사, 운반력, 퇴적 가능 공간을 단순화해 보여준다. 핵심은 “빠른 물은 깎고, 느려진 물은 내려놓는다”이다. `flowFrames`, `erosionFrames`, `depositionFrames`, `waterDepthFrames`가 모두 중요하다.

### Coastal / Marine

해안 계열은 파랑 에너지, 연안류, 조석/해수면, 하천 퇴적물 공급의 균형으로 설명한다. v1에서는 파식은 붉은 침식 overlay, 사주/사취/퇴적은 밝은 퇴적 overlay, 해수면 변화는 `waterDepthFrames`로 분리한다.

### Glacial

빙하 계열은 얼음 흐름, 권곡/곡빙하 과굴식, 능선 절단, 해수 침수 단계를 보여준다. v1에서는 얼음 두께 자체를 별도 필드로 만들지 않고 `waterDepthFrames` 또는 `flowFrames`에 빙하 흐름 라벨을 붙일 수 있다.

### Volcanic

화산 계열은 분출 양식, 화구 위치, 용암 점성, 붕괴/함몰을 단순화한다. `volcanic_activity`는 표고 증가로, 칼데라와 화구호는 성장 후 중앙부 함몰 및 물 채움으로 표현한다.

### Karst

카르스트 계열은 석회암 용식, 지하 배수, 함몰, 잔류 봉우리를 보여준다. v1에서는 지하 동굴을 실제 3D volume으로 만들기보다 표면의 sink, fissure, residual hill을 `erosionFrames`와 annotation으로 설명한다.

### Aeolian / Arid

건조/풍성 계열은 바람 방향, 모래 공급량, 식생 부족, 일시 하천을 핵심 변수로 둔다. 사구는 `flowFrames`의 바람 벡터와 `depositionFrames`의 사면 이동이 중요하고, 와디/플라야/페디먼트는 드문 홍수와 건조 퇴적을 함께 보여준다.

### Structural / Differential Erosion

구조/차별 침식 계열은 암석 경도, 층리, 절리, 단층/습곡이 먼저 지형의 골격을 만들고 이후 침식이 약한 부분을 더 깎는다는 점을 강조한다. v1에서는 구조 초기 조건과 `rockHardness` 유사 mask를 payload 내부 메타데이터로 보관한다.

## 4. 38개 지형 매트릭스

| landform_id | 한국어 이름 | family | dominant processes | required fields | v1 visual target | validation cue |
| --- | --- | --- | --- | --- | --- | --- |
| `alluvial_fan` | 선상지 | river/delta | 산지 출구 감속, 운반력 감소, 부채꼴 퇴적, 분류 | elevation, waterDepth, deposition, flow, labels | 협곡 출구에서 부채꼴 퇴적면이 하류로 넓어짐 | 꼭짓점은 산지 출구, 퇴적 전면은 평야 쪽으로 확산 |
| `arcuate_delta` | 원호상 삼각주 | river/delta | 하천 퇴적, 파랑 재분배, 하구 전진 | elevation, waterDepth, deposition, flow, labels | 해안선 밖으로 둥근 삼각주 전면 발달 | 하구 퇴적체가 둥근 호 형태이고 파랑 정리가 보임 |
| `arete` | 아레트 | glacial | 양쪽 권곡/빙하 침식, 능선 예각화 | elevation, erosion, flow, labels, camera | 두 빙하곡 사이 칼날 능선 | 양쪽 사면이 깎여 좁고 날카로운 능선이 남음 |
| `barchan` | 바르한 사구 | aeolian/arid | 단일 우세 풍향, 제한된 모래 공급, 사구 이동 | elevation, deposition, erosion, flow, labels | 초승달 모양 사구와 바람 아래쪽 뿔 | 뿔이 바람이 불어가는 방향으로 뻗음 |
| `bird_foot_delta` | 조족상 삼각주 | river/delta | 강한 하천 공급, 약한 파랑, 자연제방성 분류 | elevation, waterDepth, deposition, flow, labels | 손가락처럼 바다로 뻗는 분류 하도 | 하도 주변 퇴적 돌출부가 여러 갈래로 길게 전진 |
| `braided_river` | 망류 하천 | river/delta | 변동 유량, 높은 퇴적물 공급, 하중도 형성 | elevation, waterDepth, deposition, erosion, flow | 여러 얕은 물길과 모래톱이 계속 갈라짐 | 단일 하도보다 분류/합류가 반복되고 퇴적 bar가 많음 |
| `caldera` | 칼데라 | volcanic | 대규모 분출, 마그마방 비움, 중앙 함몰 | elevation, deposition, erosion, labels, camera | 큰 원형 함몰지와 가장자리 화산벽 | 단순 분화구보다 훨씬 넓고 붕괴 경계가 뚜렷 |
| `cirque` | 권곡 | glacial | 상류부 빙하 과굴식, 동결 융해, 후빙기 호수 | elevation, waterDepth, erosion, flow, labels | 산지 머리 부분의 그릇형 오목 지형 | 반원형 벽과 과굴식 바닥이 함께 보임 |
| `coastal_cliff` | 해식 절벽 | coastal/marine | 파식, notch, 절벽 후퇴, 파식대 | elevation, waterDepth, erosion, labels, camera | 해수면 부근 notch와 가파른 절벽 | 침식이 파랑 접촉부에 집중되고 절벽이 육지로 후퇴 |
| `coastal_dune` | 해안 사구 | aeolian/arid | 해빈 모래 공급, 육풍/해풍, 식생 고정 | elevation, deposition, flow, labels | 해안선 뒤편 평행 사구열 | 모래 공급원은 해빈이고 사구는 해안 뒤에 배열 |
| `crater_lake` | 화구호 | volcanic | 분화구 형성, 분출 중지, 물 채움 | elevation, waterDepth, deposition, labels | 원형 화구 내부에 물이 고임 | 호수는 화산 정상 또는 화구 내부에 위치 |
| `cuspate_delta` | 첨상 삼각주 | river/delta | 하천 퇴적, 양방향 파랑 재분배 | elevation, waterDepth, deposition, flow, labels | 바다 쪽으로 뾰족한 삼각주 | 해안 양쪽으로 퇴적물이 균형 있게 퍼짐 |
| `delta` | 삼각주 | river/delta | 하구 감속, 퇴적, 분류, 전면 성장 | elevation, waterDepth, deposition, flow, labels | 하구 앞 퇴적 평야와 분류 하도 | 하천에서 바다/호수로 들어가는 지점에 퇴적 집중 |
| `estuary` | 하구/에스추어리 | coastal/marine | 침수 하곡, 조석 혼합, 하천-해수 상호작용 | elevation, waterDepth, erosion, deposition, flow | 넓은 깔때기형 하구와 조석 수로 | 바다 쪽으로 넓어지고 퇴적보다 침수/혼합이 우세 |
| `fjord` | 피오르 | glacial | U자곡 과굴식, 해수 침수, 급경사 벽 | elevation, waterDepth, erosion, flow, labels | 깊고 좁은 바닷물 U자곡 | 해안인데 단면은 빙하 U자곡이고 벽이 급함 |
| `free_meander` | 자유 곡류 하천 | river/delta | 외측 침식, 내측 퇴적, 하도 측방 이동 | elevation, waterDepth, erosion, deposition, flow | 넓은 범람원 위 곡류 하도 | 외측 cut bank와 내측 point bar가 짝을 이룸 |
| `horn` | 호른 | glacial | 여러 권곡의 두부 침식, 산정 예각화 | elevation, erosion, flow, labels, camera | 피라미드형 날카로운 봉우리 | 세 방향 이상 빙하 침식이 산정을 깎음 |
| `karst_doline` | 돌리네 | karst | 석회암 용식, 지하 배수, 국지 함몰 | elevation, erosion, waterDepth, labels | 원형/타원형 와지와 배수점 | 물길이 표면 하천보다 움푹한 함몰부로 사라짐 |
| `karren` | 카렌 | karst | 빗물 용식, 절리 확대, 홈/골 형성 | elevation, erosion, flow, labels, camera | 석회암 표면의 작은 홈과 날카로운 릿지 | 미세한 선형 홈이 절리/경사 방향과 연결 |
| `lava_plateau` | 용암 대지 | volcanic | 유동성 큰 용암 반복 분출, 넓은 피복 | elevation, deposition, flow, labels | 넓고 평탄한 계단식 현무암 대지 | 중앙 원뿔보다 광역 판상 용암층이 우세 |
| `mesa_butte` | 메사와 뷰트 | structural/differential erosion | 수평층, 경암 caprock, 차별 침식 | elevation, erosion, labels, camera | 평평한 꼭대기와 급사면, 고립 언덕 | 단단한 상부층 아래 약한 층이 더 깎임 |
| `pedestal_rock` | 버섯바위/받침바위 | structural/differential erosion | 하부 집중 풍식/마식, 암석 경도 차 | elevation, erosion, flow, labels, camera | 좁은 목과 넓은 상부 암괴 | 침식이 하부에 집중되어 받침 모양 형성 |
| `pediment` | 페디먼트 | aeolian/arid | 산록 후퇴, sheetwash, 완사면 절단 | elevation, erosion, deposition, flow, labels | 산지 앞 완만한 암석 침식면 | 산록에서 평야로 이어지는 낮은 경사면 |
| `playa` | 플라야 | aeolian/arid | 폐쇄 분지, 일시 호수, 증발, 점토/염류 퇴적 | elevation, waterDepth, deposition, labels | 평탄한 건호 바닥과 계절성 물막 | 물은 빠져나가지 않고 증발 후 평탄 퇴적면이 남음 |
| `ria_coast` | 리아스식 해안 | coastal/marine | 하천곡 침수, 해수면 상승, 복잡한 만 | elevation, waterDepth, erosion, labels | 나뭇가지형 만과 반도 | 침수된 V자 하곡 패턴이 해안선에 남음 |
| `sea_arch` | 해식 아치 | coastal/marine | 절리대 파식, 동굴 확장, 관통 | elevation, waterDepth, erosion, labels, camera | 곶의 약한 부분이 뚫린 아치 | 파식 집중부가 양쪽에서 연결되어 구멍 형성 |
| `shield_volcano` | 순상 화산 | volcanic | 저점성 용암, 완경사 반복 분출 | elevation, deposition, flow, labels, camera | 넓고 완만한 방패형 화산체 | 높이보다 폭이 크고 사면 경사가 낮음 |
| `spit_lagoon` | 사취와 석호 | coastal/marine | 연안류, 모래 이동, 만 입구 차단 | elevation, waterDepth, deposition, flow, labels | 해안에서 길게 자란 사취와 뒤쪽 석호 | 사취는 연안류 방향으로 자라고 뒤쪽 물이 갇힘 |
| `star_dune` | 별사구 | aeolian/arid | 다방향 바람, 풍부한 모래, 수직 성장 | elevation, deposition, erosion, flow, labels | 여러 능선이 별 모양으로 모이는 높은 사구 | 한 방향 이동보다 방사형 사구릉과 높은 중심부가 보임 |
| `stratovolcano` | 성층 화산 | volcanic | 고점성 용암, 화산쇄설물, 반복 분출 | elevation, deposition, flow, erosion, labels | 가파른 원뿔형 화산과 화구 | 순상 화산보다 경사가 급하고 층상 성장 느낌 |
| `tombolo` | 육계사주 | coastal/marine | 파랑 굴절, 퇴적물 수렴, 섬-육지 연결 | elevation, waterDepth, deposition, flow, labels | 섬과 육지를 잇는 모래톱 | 퇴적체가 섬 뒤 파랑 그림자 영역에 모임 |
| `tower_karst` | 탑카르스트 | karst | 열대 카르스트 용식, 잔류 봉우리, 지하 배수 | elevation, erosion, waterDepth, labels, camera | 평지 위 급경사 석회암 탑 | 주변은 낮아지고 고립된 잔류 봉우리가 남음 |
| `transverse_dune` | 횡사구 | aeolian/arid | 단일 우세 풍향, 풍부한 모래 공급 | elevation, deposition, erosion, flow, labels | 바람 방향에 직각인 긴 사구릉 | 사구 능선이 바람 방향과 거의 직각 |
| `u_valley` | U자곡 | glacial | 곡빙하 과굴식, 측벽 절단, 바닥 평탄화 | elevation, erosion, flow, waterDepth, labels | 넓고 평평한 바닥과 급한 벽 | V자곡보다 바닥이 넓고 양쪽 벽이 가파름 |
| `uvala` | 우발라 | karst | 여러 돌리네 결합, 용식 확대, 지하 배수 | elevation, erosion, waterDepth, labels | 불규칙하게 연결된 큰 카르스트 와지 | 단일 원형 돌리네보다 크고 복합적인 함몰지 |
| `v_valley` | V자곡 | river/delta | 하방 침식, 사면 이동, 두부 침식 | elevation, waterDepth, erosion, flow, labels | 좁은 하천과 V자 단면 | 하천 바닥 절단이 먼저 보이고 사면이 따라 조정 |
| `wadi` | 와디 | aeolian/arid | 간헐 홍수, 건조 하상, 급류 침식/퇴적 | elevation, waterDepth, erosion, deposition, flow | 평소 건조한 하천골과 홍수 흔적 | 지속 하천이 아니라 드문 홍수 때만 물길이 활성화 |
| `waterfall` | 폭포 | river/delta | 경암/연암 차별 침식, 낙차, 후퇴 | elevation, waterDepth, erosion, flow, labels | 단차, 낙수, plunge pool, 폭포 후퇴 | 폭포 밑 소와 상류 방향 후퇴 흔적이 보임 |

## 5. Implementation priority batches

### Batch 1: payload와 overlay 검증이 쉬운 하천/퇴적 지형

대상: `alluvial_fan`, `delta`, `braided_river`, `free_meander`, `v_valley`, `waterfall`

이 배치는 `stream_power_erosion`, `sediment_transport`, `waterDepthFrames`, `flowFrames`를 가장 직접적으로 검증할 수 있다. v1 목표는 “깎는 곳과 쌓이는 곳이 색으로 분리된다”이다.

### Batch 2: 해안/하구 지형

대상: `coastal_cliff`, `sea_arch`, `spit_lagoon`, `tombolo`, `estuary`, `ria_coast`, `arcuate_delta`, `cuspate_delta`, `bird_foot_delta`

해안 지형은 `marine_erosion`과 연안류성 `depositionFrames`를 분리해야 한다. 삼각주 세부형은 같은 delta adapter에서 파랑/하천 우세 정도를 바꾸는 방식으로 빠르게 확장한다.

### Batch 3: 빙하 지형

대상: `u_valley`, `fjord`, `cirque`, `arete`, `horn`

빙하 지형은 같은 빙하 침식 mask를 공유하되, 카메라와 초기 지형을 다르게 둔다. 피오르는 U자곡 결과에 해수 침수 단계를 추가한다.

### Batch 4: 화산 지형

대상: `shield_volcano`, `stratovolcano`, `caldera`, `crater_lake`, `lava_plateau`

화산 지형은 `volcanic_activity` 기반의 표고 증가가 핵심이다. 칼데라와 화구호는 “성장 -> 함몰 -> 물 채움”의 staged payload를 우선 구현한다.

### Batch 5: 카르스트 지형

대상: `karst_doline`, `uvala`, `karren`, `tower_karst`

카르스트는 `karst_dissolution` overlay와 지하 배수 annotation이 중요하다. v1에서는 지하 동굴을 만들지 않고 표면 함몰, 홈, 잔류 봉우리로 설명한다.

### Batch 6: 건조/풍성 및 차별 침식 지형

대상: `barchan`, `transverse_dune`, `star_dune`, `coastal_dune`, `wadi`, `playa`, `pediment`, `mesa_butte`, `pedestal_rock`

이 배치는 시각적으로 매력적이지만 지형별 규칙이 다양하다. 사구류는 공통 aeolian adapter로 묶고, 메사/버섯바위/페디먼트는 구조 또는 암석 경도 mask를 단순화해 구현한다.

## v1 개발 원칙

- 각 지형은 한 문장 수업 목표와 하나의 대표 validation cue를 가져야 한다.
- payload 필드가 비어 있어도 타입은 유지한다. 예를 들어 물이 없는 사구도 `waterDepthFrames`는 0 배열로 둔다.
- 카메라는 지형 인식에 필요한 시점을 우선한다. 자동 orbit가 지형 변화 관찰을 방해하면 기본값은 `fixed` 또는 `plan`으로 둔다.
- 생성 이미지 asset은 정답 preview와 texture 참고로 사용하고, 3D 높이장은 procedural generator 또는 SimpleLEM 계열이 담당한다.
- 모델 한계는 UI와 교사용 annotation에서 명시한다. “연구급 재현”이 아니라 “형성 원리의 고등학교 수업용 시각화”가 v1 목표이다.
