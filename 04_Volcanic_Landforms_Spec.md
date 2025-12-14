# 📘 [Geo-Lab AI] 개발 백서 (Development White Paper)

**Project Name:** Geo-Lab AI
**Version:** Final Release 1.0
**Module:** Volcanic Landforms (화산 지형)
**Target:** High School Geography ~ Undergraduate Volcanology
**Director:** [User Name]

---

## 0. 개발 표준 및 제약사항 (Standard Protocols)

### 🎨 1. 비주얼 스타일 가이드 (Visual Style: Magmatic & Explosive)
* **Tone:** Dynamic, Thermal-coded, Catastrophic.
* **Color Palette:**
    * *Magma/Lava:* 온도에 따른 Black Body Radiation 색상 (White Hot → Yellow → Red → Dark Crust).
    * *Ash/Rock:* 현무암(검은색) vs 조면암/안산암(회백색) 구분.
    * *Terrain:* 굳은 용암 위 1차 천이 식생(이끼, 덤불)의 듬성듬성한 녹색.
* **Key Feature:** 마그마의 **$SiO_2$ 함량(이산화규소)**에 따른 점성 변화를 슬라이더(Slider)로 조절하면 화산의 모양이 실시간으로 변형되는 **[Morphing Terrain]** 구현.

### 🛠️ 2. 기술 스택 (Tech Stack)
* **Physics Engine:** SPH (Smoothed-Particle Hydrodynamics) for Lava Flow Simulation.
* **Rendering:** Volumetric Fog (화산재 및 연기 표현).
* **Algorithm:** Cooling Crystallization Model (용암 냉각 속도에 따른 절리 형성 계산).

---

## 1. 화산 지형 모듈 세부 명세 (Module Specifications)

### 🌋 Chapter 1. 마그마의 성격: 점성(Viscosity)과 화산체
**핵심 로직:** **$SiO_2$ 함량 $\propto$ 점성 $\propto$ 화산 경사도**.

| 지형 (Feature) | 핵심 변수 (Key Parameters) | 시각화 포인트 (Visualization) | 학습용 수식 (Formula Reference) |
| :--- | :--- | :--- | :--- |
| **순상 화산 (Shield)** | 점성($\mu_{low}$), 온도($T_{high}$), 유동성(High) | 꿀처럼 묽은 용암이 넓게 퍼져나가며 완만한 경사(방패 모양) 형성. (예: 하와이, 제주도 한라산 산록) | Slope Angle $\theta \approx 2^{\circ} \sim 10^{\circ}$ |
| **종상 화산 (Lava Dome)** | 점성($\mu_{high}$), 온도($T_{low}$), 유동성(Low) | 치약처럼 된 용암이 분화구 위로 솟구쳐 종 모양 형성. (예: 제주도 산방산, 울릉도 나리분지 내 알봉) | Slope Angle $\theta > 30^{\circ}$ |
| **성층 화산 (Stratovolcano)** | 분출 주기, 폭발성 | 용암 분출(Flow)과 화산재 폭발(Explosion)이 교대로 일어나 층층이 쌓인 원뿔형 구조. (예: 후지산, 필리핀 마욘) | Layering Index |
| **용암 대지 (Lava Plateau)** | 열하 분출(Fissure), $SiO_2$ < 52% | 지각의 틈에서 묽은 용암이 대량으로 흘러나와 기존 계곡을 메우고 평탄면 형성. (예: 철원, 개마고원) | Area Coverage Rate |

### 💥 Chapter 2. 분화구의 변형: 함몰과 확장
**핵심 로직:** **질량 결손(Mass Deficit)에 의한 붕괴**.

| 지형 (Feature) | 핵심 변수 (Key Parameters) | 시각화 포인트 (Visualization) | 학습용 수식 (Formula Reference) |
| :--- | :--- | :--- | :--- |
| **화구 (Crater)** | 폭발 에너지($E_{exp}$) | 마그마가 분출된 단순한 구멍. | Diameter $D < 1km$ |
| **칼데라 (Caldera)** | 마그마 방 공동화 비율, 지반 하중 | **[Collapse Event]** 대폭발 후 지하 마그마 방이 비면서 산정부가 와르르 무너져 내리는 시네마틱 컷. 물이 차면 칼데라 호. (예: 백두산 천지, 나리분지) | Collapse Volume $V_c$ |
| **이중 화산** | 1차 분출 후 휴지기, 2차 분출 | 칼데라(큰 그릇) 안에 새로운 화산(작은 컵)이 생기는 구조. (예: 울릉도 성인봉-나리분지-알봉) | Nested Structure |

### ❄️ Chapter 3. 냉각의 기하학: 1차 지형
**핵심 로직:** **수축(Contraction)과 균열**.

| 지형 (Feature) | 핵심 변수 (Key Parameters) | 시각화 포인트 (Visualization) | 학습용 수식 (Formula Reference) |
| :--- | :--- | :--- | :--- |
| **주상절리 (Columnar Jointing)** | 냉각 속도($dT/dt$), 수축 중심점 | 용암이 급격히 식으며 부피가 줄어들 때 형성되는 **육각형(Hexagonal) 기둥** 패턴 생성 알고리즘. | Fracture Spacing $S \propto (dT/dt)^{-1/2}$ |
| **용암 동굴 (Lava Tube)** | 표면 냉각율 vs 내부 유속 | 용암의 겉부분은 굳고(지붕), 속은 계속 흘러(터널) 빠져나간 뒤 남은 빈 공간. | Tube Formation Logic |

---

## 2. 정답지 이미지 목록 (Reference Images to Load)
*AI 모델 학습 및 UI 렌더링 시 매칭할 레퍼런스 데이터.*

1.  `volcano_shape_viscosity.png` (순상 vs 성층 vs 종상 화산의 단면 비교도)
2.  `caldera_formation_steps.gif` (마그마 방 비움 → 붕괴 → 호수 형성 3단계)
3.  `columnar_jointing_hex.jpg` (주상절리의 육각형 단면 및 측면 기둥 구조)
4.  `korea_volcanic_map.png` (백두산, 제주도, 울릉도, 철원 용암대지 위치 지도)

---

**[Director's Note]**
화산 모듈은 **'점성($\mu$)'** 변수 하나가 지형의 모양(순상/종상)을 결정짓는다는 인과관계를 명확히 보여줘야 합니다. 특히 한국 지리 수험생을 타겟으로 한다면 **철원 용암대지**와 **제주도**의 형성 과정 차이를 시뮬레이션으로 비교하는 기능을 반드시 포함하십시오.

승인하시면 다음은 가장 다이내믹한 **'빙하 지형'**으로 이동하겠습니다.