# 📘 [Geo-Lab AI] 개발 백서 (Development White Paper)

**Project Name:** Geo-Lab AI
**Version:** Final Release 1.0
**Module:** Glacial Landforms (빙하 지형)
**Target:** High School Geography ~ Undergraduate Glaciology
**Director:** [User Name]

---

## 0. 개발 표준 및 제약사항 (Standard Protocols)

### 🎨 1. 비주얼 스타일 가이드 (Visual Style: Cryosphere)
* **Tone:** Majestic, Cold, High-Contrast.
* **Color Palette:**
    * *Ice:* 반투명한 아이스 블루(Ice Blue) ~ 압축된 짙은 파랑 (Deep Azure).
    * *Bedrock:* 깎여 나간 거친 회색 화강암 질감 (Exposed Granite).
    * *Water (Fjord):* 깊고 어두운 남색 (Deep Navy).
* **Key Feature:** 빙하가 흐를 때 바닥을 긁어내는(Scouring) 효과와 녹을 때 흙더미를 쏟아놓는(Dumping) 효과를 물리 엔진으로 구현. **"분급(Sorting) 없음"** 시각화 필수.

### 🛠️ 2. 기술 스택 (Tech Stack)
* **Physics Engine:** Non-Newtonian Fluid Dynamics (비뉴턴 유체 역학 - 얼음의 느린 흐름 구현).
* **Rendering:** Subsurface Scattering (얼음 내부의 빛 투과 효과).
* **Algorithm:** Voxel Carving (빙하 이동 경로에 따른 지형 깎기).

---

## 1. 빙하 지형 모듈 세부 명세 (Module Specifications)

### 🧊 Chapter 1. 빙하 침식: 거대한 불도저 (Erosion)
**핵심 로직:** **U자형 침식 (U-shaped Profile)** & 굴식 작용(Plucking).

| 지형 (Feature) | 핵심 변수 (Key Parameters) | 시각화 포인트 (Visualization) | 학습용 수식 (Formula Reference) |
| :--- | :--- | :--- | :--- |
| **U자곡 (U-shaped Valley)** | 빙하 두께($H_{ice}$), 마찰력 | 좁고 깊은 V자곡(하천)이 거대한 빙하에 의해 넓고 둥근 U자 형태로 깎여나가는 **[Cross-section Transition]**. | Erosion Rate $E \propto U_{sliding}^2$ |
| **권곡 (Cirque)** | 설선 고도(ELA), 굴식 강도 | 산 정상부 오목한 곳에 눈이 쌓여 얼음이 되고, 암석을 뜯어내며(Plucking) 반원형 의자 모양을 만드는 과정. | - |
| **호른 (Horn)** | 권곡의 개수($N \ge 3$) | 3개 이상의 권곡이 뒤로 후퇴하며 정상을 깎아 만들어진 피라미드형 뾰족 봉우리 (예: 마터호른). | Peak Sharpness Index |
| **피오르 (Fjord)** | 해수면 상승($\Delta SeaLevel$), 침식 깊이 | 빙기가 끝나고 해수면이 상승하여 U자곡에 바닷물이 들어차는 **[Flooding Animation]**. 내륙 깊숙이 좁고 긴 바다 형성. | Depth Profile $D(x)$ |
| **현곡 (Hanging Valley)** | 본류 빙하 vs 지류 빙하 깊이 차이 | 본류가 깊게 깎고 지나간 뒤, 얕은 지류 골짜기가 절벽 위에 걸려 폭포가 되는 지형. | Drop Height $H_{drop}$ |

### 🪨 Chapter 2. 빙하 퇴적: 무질서의 미학 (Deposition)
**핵심 로직:** **분급 불량 (Poor Sorting)**. 크고 작은 자갈과 흙이 뒤섞임.

| 지형 (Feature) | 핵심 변수 (Key Parameters) | 시각화 포인트 (Visualization) | 학습용 수식 (Formula Reference) |
| :--- | :--- | :--- | :--- |
| **빙퇴석 (Moraine)** | 빙하 후퇴 속도, 퇴적량 | 빙하가 녹는 끝부분(Terminus)에서 컨베이어 벨트처럼 암석 부스러기를 쏟아놓아 언덕을 만드는 과정. | Sediment Flux $Q_s$ |
| **드럼린 (Drumlin)** | 빙하 이동 방향, 기저 하중 | 숟가락을 엎어놓은 듯한 유선형 언덕. **[Direction Indicator]** 완만한 쪽이 빙하가 흘러간 방향임을 화살표로 표시. | Shape Factor (Elongation) |
| **에스커 (Esker)** | 융빙수 유량($Q_{water}$), 터널 크기 | 빙하 밑을 흐르는 물(융빙수) 터널에 퇴적물이 쌓여, 빙하가 녹은 뒤 구불구불한 제방 모양이 드러남. | Sinuosity Index |

### ❄️ Chapter 3. 주빙하 지형: 얼었다 녹았다 (Periglacial - Bonus)
**핵심 로직:** **동결 융해 (Freeze-Thaw Cycle)**.

| 지형 (Feature) | 핵심 변수 (Key Parameters) | 시각화 포인트 (Visualization) | 학습용 수식 (Formula Reference) |
| :--- | :--- | :--- | :--- |
| **구조토 (Patterned Ground)** | 토양 입자 크기, 동결 횟수 | 자갈들이 얼음의 쐐기 작용으로 밀려나와 다각형(Polygon) 무늬를 만드는 **[Time-lapse]**. | Convection Cell Model |
| **솔리플럭션 (Solifluction)** | 경사도, 활동층 융해 | 영구동토층 위 녹은 흙이 흘러내리는 현상. | Creep Velocity |

---

## 2. 정답지 이미지 목록 (Reference Images to Load)
*AI 모델 학습 및 UI 렌더링 시 매칭할 레퍼런스 데이터.*

1.  `valley_transformation_V_to_U.gif` (V자곡에서 U자곡으로 변형되는 3D 모델)
2.  `fjord_cross_section.jpg` (바닷물에 잠긴 U자곡 단면도)
3.  `glacial_till_unsorted.png` (빙퇴석의 뒤섞인 자갈 단면 - 분급 불량 예시)
4.  `drumlin_ice_flow.jpg` (드럼린의 형태와 빙하 이동 방향 관계도)

---

**[Director's Note]**
빙하 지형의 킬러 문항 포인트는 **"강물(유수)에 의한 퇴적(분급 양호)"**과 **"빙하에 의한 퇴적(분급 불량)"**을 구분하는 것입니다. 시뮬레이션 내에서 입자 크기 필터(Sorting Filter)가 빙하 모드에서는 작동하지 않는 것을 시각적으로 강조해주세요.

승인하시면 다음은 가장 척박하지만 아름다운 **'건조 지형'**으로 넘어가겠습니다.