# 📘 [Geo-Lab AI] 개발 백서 (Development White Paper)

**Project Name:** Geo-Lab AI
**Version:** Final Release 1.0
**Module:** Arid Landforms (건조 지형)
**Target:** High School Geography ~ Undergraduate Geomorphology
**Director:** [User Name]

---

## 0. 개발 표준 및 제약사항 (Standard Protocols)

### 🎨 1. 비주얼 스타일 가이드 (Visual Style: Desert & Erosion)
* **Tone:** High Contrast, Dusty, Heat-haze.
* **Color Palette:**
    * *Sand/Dust:* 오커(Ochre), 번트 시에나(Burnt Sienna) 등 황토색 계열.
    * *Sky:* 짙은 코발트 블루(건조해서 대기가 깨끗함) 또는 모래폭풍 시 뿌연 황색.
    * *Salt Lake (Playa):* 눈부신 흰색 (소금 결정 반사).
* **Key Feature:** 지표면의 아지랑이(Heat Haze) 효과와 바람의 방향을 보여주는 **입자 흐름(Particle Flow)** 시각화.

### 🛠️ 2. 기술 스택 (Tech Stack)
* **Physics Engine:** Granular Physics (모래 입자 간 마찰 및 안식각 시뮬레이션).
* **Rendering:** PBR Materials (암석의 거친 질감 vs 소금 사막의 매끄러운 질감).
* **Algorithm:** Cellular Automata (사구의 이동 및 성장 패턴 계산).

---

## 1. 건조 지형 모듈 세부 명세 (Module Specifications)

### 🌪️ Chapter 1. 바람의 조각: 침식과 퇴적 (Aeolian Process)
**핵심 로직:** **도약 운동(Saltation)**. 무거운 모래는 지면 가까이서 튀며 이동한다.

| 지형 (Feature) | 핵심 변수 (Key Parameters) | 시각화 포인트 (Visualization) | 학습용 수식 (Formula Reference) |
| :--- | :--- | :--- | :--- |
| **버섯바위 (Mushroom Rock)** | 모래 비산 높이($H_{max} \approx 1m$), 암석 경도 | 바람에 날린 모래알이 바위의 **밑부분만 집중 공격**하여 깎아내는 과정. (윗부분은 침식 안 됨). | Erosion Rate $E(z)$ |
| **사구 (Sand Dune)** | 풍향 벡터($\vec{V}$), 모래 공급량 | **[Dune Morphing]** 풍향에 따라 바르한(초승달형, 단일풍) $\leftrightarrow$ 성사구(긴 칼형, 양방향풍) 변환. | Bagnold Formula |
| **삼릉석 (Ventifact)** | 주풍향의 개수 | 자갈이 바람을 받아 깎이면서 3개의 면과 모서리가 생기는 과정. | Facet Formation |
| **사막 포장 (Desert Pavement)** | 입자 크기별 무게 | 바람이 고운 모래만 날려 보내고(Deflation), 무거운 자갈만 바닥에 남는 **[Sorting Filter]** 효과. | Threshold Friction Velocity |

### 🌧️ Chapter 2. 물의 역설: 유수 지형 (Fluvial in Desert)
**핵심 로직:** **포상 홍수(Flash Flood)**. 식생이 없어 비가 오면 물이 급격히 불어남.

| 지형 (Feature) | 핵심 변수 (Key Parameters) | 시각화 포인트 (Visualization) | 학습용 수식 (Formula Reference) |
| :--- | :--- | :--- | :--- |
| **선상지 (Alluvial Fan)** | 경사 급변점, 유속 감소율 | 산지에서 평지로 나올 때 유속이 느려지며 부채꼴로 퇴적물이 퍼지는 시뮬레이션. (선정-선앙-선단 구분). | Stream Power Law |
| **바하다 (Bajada)** | 선상지 결합 수($N$) | 여러 개의 선상지가 옆으로 합쳐져 산기슭을 감싸는 복합 선상지 형성. | Coalescence Factor |
| **와디 (Wadi)** | 강수 빈도, 침투율 | 평소엔 마른 골짜기(교통로)였다가, 비가 오면 급류가 흐르는 강으로 변하는 **[Event Trigger]**. | Infiltration Capacity |
| **플라야 (Playa)** | 증발량 >> 강수량 | 물이 고였다가 증발하고 **소금(Salt)**만 하얗게 남는 염호의 형성 과정. | Evaporation Rate |

### 🧱 Chapter 3. 구조 지형: 강한 놈이 살아남는다 (Structural)
**핵심 로직:** **차별 침식(Differential Erosion)** & 수평 지층.

| 지형 (Feature) | 핵심 변수 (Key Parameters) | 시각화 포인트 (Visualization) | 학습용 수식 (Formula Reference) |
| :--- | :--- | :--- | :--- |
| **메사 (Mesa)** | 상부 암석 강도($S_{hard}$), 하부($S_{soft}$) | 윗부분의 단단한 암석(Cap rock)이 뚜껑처럼 보호해줘서 생긴 탁자 모양의 지형. | Resistance Ratio |
| **뷰트 (Butte)** | 침식 진행률 | 메사가 깎여서 작아진 탑 모양의 지형. (메사 $\rightarrow$ 뷰트 크기 비교). | Width/Height Ratio |

---

## 2. 정답지 이미지 목록 (Reference Images to Load)
*AI 모델 학습 및 UI 렌더링 시 매칭할 레퍼런스 데이터.*

1.  `barchan_dune_wind_direction.jpg` (바르한 사구의 형태와 바람 방향 화살표)
2.  `alluvial_fan_structure.png` (선상지의 선정, 선앙, 선단 단면도 및 입자 크기 분포)
3.  `mesa_butte_evolution.jpg` (고원 -> 메사 -> 뷰트 -> 스파이어 침식 단계)
4.  `mushroom_rock_formation.gif` (모래바람에 의한 하단부 침식 애니메이션)

---

**[Director's Note]**
건조 지형은 **"바람"**이 만든 것 같지만, 실제 거대 지형은 **"일시적인 폭우(물)"**가 만들었다는 오개념을 바로잡는 것이 교육적 목표입니다. 와디(Wadi) 시뮬레이션에서 비가 올 때 급격히 물이 차오르는 속도를 극적으로 표현해 주십시오.

승인하시면 마지막 대단원, 가장 평온하지만 가장 중요한 **'평야 지형'**으로 넘어가겠습니다.