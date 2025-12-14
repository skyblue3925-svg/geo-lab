# 📘 [Geo-Lab AI] 개발 백서 (Development White Paper)

**Project Name:** Geo-Lab AI
**Version:** Final Release 1.0
**Module:** Coastal Landforms (해안 지형)
**Target:** High School Geography ~ Undergraduate Geomorphology
**Director:** [User Name]

---

## 0. 개발 표준 및 제약사항 (Standard Protocols)

### 🎨 1. 비주얼 스타일 가이드 (Visual Style: Schematic Education)
* **Tone:** Clean, Minimalist, Textbook-style 3D.
* **Color Palette:**
    * *Sea:* 깊이에 따른 파란색 그라데이션 (얕은 곳=하늘색, 깊은 곳=남색).
    * *Sand:* 밝은 베이지색 (이동 경로가 잘 보여야 함).
    * *Rocks:* 짙은 회색/갈색 (절벽의 질감 표현).
* **Key Feature:** 파도의 굴절과 모래의 이동 경로(Vector Arrow)를 시각적으로 표시.

### 🛠️ 2. 기술 스택 (Tech Stack)
* **Backend:** Python 3.9+ (Libraries: `NumPy`, `SciPy`, `Taichi`).
* **Frontend:** WebGL via `Three.js` or `PyVista`.
* **App Framework:** `Streamlit`.

---

## 1. 해안 지형 모듈 세부 명세 (Module Specifications)

### 🌊 Chapter 1. 곶(Headland)과 침식: 파도의 공격
**핵심 로직:** **파랑의 굴절 (Wave Refraction)**. 파도의 에너지가 튀어나온 땅(곶)으로 집중됨.

| 지형 (Feature) | 핵심 변수 (Key Parameters) | 시각화 포인트 (Visualization) | 학습용 수식 (Formula Reference) |
| :--- | :--- | :--- | :--- |
| **해식애 & 파식대** | 파랑 에너지($P$), 암석 경도 | 파도가 절벽 밑을 때려(Notch) 윗부분이 무너지고, 절벽이 후퇴하며 평평한 바닥(파식대) 노출. | Cliff Retreat Rate $\propto P$ ($P \propto H^2T$) |
| **시스택 & 아치** | 차별 침식, 시간($t$) | **[Evolution Time-lapse]** 해식동굴 → 아치(구멍) → 시스택(기둥) → 시스텀프(바위) 4단계 변화. | - |
| **해안단구** | 지반 융기($U$), 해수면 변동 | 파식대가 융기하여 계단 모양의 언덕이 되는 과정 (강의 하안단구와 비교). | Uplift Event Trigger |

### 🏖️ Chapter 2. 만(Bay)과 퇴적: 모래의 여행
**핵심 로직:** **연안류 (Longshore Drift)**. 파도가 비스듬히 칠 때 모래가 지그재그로 이동.

| 지형 (Feature) | 핵심 변수 (Key Parameters) | 시각화 포인트 (Visualization) | 학습용 수식 (Formula Reference) |
| :--- | :--- | :--- | :--- |
| **사빈 (Beach)** | 파랑 입사각($\theta$), 입자 크기 | 만(Bay) 안쪽으로 에너지가 분산되며 모래가 쌓임. 여름(퇴적) vs 겨울(침식) 해변 비교. | Sediment Transport (CERC Formula) |
| **사구 (Sand Dune)** | 풍속($V_{wind}$), 식생 밀도 | 사빈의 모래가 바람에 날려 이동. **[Windbreak Effect]** 식생 설치 시 사구 성장 시뮬레이션. | Aeolian Transport Rate |
| **사취 & 사주** | 연안류 속도, 해안선 굴곡 | 모래가 바다 쪽으로 뻗어 나가며(사취) 만의 입구를 막아버리는(사주) 과정. | - |
| **석호 (Lagoon)** | 사주 형성 여부, 유입 수량 | 사주가 바다를 막아 호수가 되고, 시간이 지나며 퇴적물로 메워져 늪이 되는 생애주기. | Water Balance Equation |

### 🦀 Chapter 3. 조류와 갯벌: 달의 인력
**핵심 로직:** **조석 주기 (Tidal Cycle)** & 미립질 퇴적.

| 지형 (Feature) | 핵심 변수 (Key Parameters) | 시각화 포인트 (Visualization) | 학습용 수식 (Formula Reference) |
| :--- | :--- | :--- | :--- |
| **갯벌 (Mudflat)** | 조차(Tidal Range), 미립질 비율 | **[Tidal Simulation]** 밀물/썰물 수위 변화와 갯골(Tidal Channel)의 프랙탈 구조 형성. | Tidal Prism / Hydrodynamics |
| **간척 사업** | 제방 건설, 시간 경과 | 갯벌에 둑을 쌓은 후(User Action), 퇴적물이 마르고 육지화되며 염분이 빠지는 과정. | Soil Desalination Model |

---

## 2. 정답지 이미지 목록 (Reference Images to Load)
*AI 학습 시 아래 파일명과 매칭되는 이미지를 함께 업로드할 것.*

1.  `sea_cliff_erosion.jpg` (해식애, 파식대, 노치 구조 단면)
2.  `sea_stack_formation.jpg` (동굴-아치-시스택 변화 과정)
3.  `sand_spit_bar_tombolo.jpg` (사취, 사주, 석호 지도형 그림)
4.  `tidal_flat_zonation.jpg` (갯벌 단면 및 조수 수위)