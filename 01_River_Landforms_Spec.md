# 📘 [Geo-Lab AI] 개발 백서 (Development White Paper)

**Project Name:** Geo-Lab AI
**Version:** Final Release 1.0
**Module:** Fluvial Landforms (하천 지형)
**Target:** High School Geography ~ Undergraduate Geomorphology
**Director:** [User Name]

---

## 0. 개발 표준 및 제약사항 (Standard Protocols)

### 🎨 1. 비주얼 스타일 가이드 (Visual Style: Schematic Education)
* **Tone:** Clean, Minimalist, Textbook-style 3D. (군더더기 없는 깔끔한 교과서 삽화 스타일)
* **Color Palette:**
    * *Water:* 반투명한 밝은 파랑 (내부 유속 흐름 가시화).
    * *Sediment:* 입자 크기별 색상 구분 (자갈=회색, 모래=노랑, 점토=갈색).
    * *Bedrock:* 층리(Layer)가 명확히 보이는 단면 텍스처.
* **Key Feature:** 모든 지형은 '케이크 자르듯' 단면을 보여주는 **Cutaway View**가 기본 지원되어야 함.

### 🛠️ 2. 기술 스택 (Tech Stack)
* **Backend:** Python 3.9+ (Libraries: `NumPy`, `SciPy`, `Taichi` for Physics).
* **Frontend:** WebGL via `Three.js` or `PyVista`.
* **App Framework:** `Streamlit` (Web-based Interface).

---

## 1. 하천 지형 모듈 세부 명세 (Module Specifications)

### 🌊 Chapter 1. 상류 (Upper Course): 파괴와 개척
**핵심 로직:** 하방 침식(Vertical Erosion), 두부 침식(Headward Erosion), 사면 붕괴.

| 지형 (Feature) | 핵심 변수 (Key Parameters) | 시각화 포인트 (Visualization) | 학습용 수식 (Formula Reference) |
| :--- | :--- | :--- | :--- |
| **V자곡** | 침식력($E$), 암석 강도($K$), 경사($S$) | 바닥 하방 침식 후 **양옆 사면이 붕괴(Mass Wasting)**되어 V자가 완성되는 과정 강조. | $E = K \cdot A^m \cdot S^n$ (Stream Power Law) |
| **폭포 & 협곡** | 유량($Q$), 낙차 높이($h$) | 하단부 굴착(Undercutting) → 상단 붕괴 → 폭포가 뒤로 물러나며 **협곡(Gorge)** 형성. | Crosby's Knickpoint Retreat Model |
| **하천 쟁탈** | 침식 속도 차이($\Delta E$), 거리 | 한쪽 강이 두부 침식으로 다른 강의 옆구리를 터트려 물을 뺏어오고, 뺏긴 강이 말라가는 과정. | Stream Capture Ratio |
| **돌개구멍** | 와류 강도(Vortex), 자갈 경도 | **[X-ray View]** 강바닥 투시. 자갈이 소용돌이치며 암반을 드릴처럼 뚫는 내부 모습. | Abrasion Rate $\propto$ Kinetic Energy |
| **감입 곡류 (상류형)** | 암석 저항성, 최단 경로 | 단단한 암반을 피해 굽이치며 흐르는 물길과 깍지 낀 능선(Interlocking Spurs). | - |

### ➰ Chapter 2. 중류 (Middle Course): 운반과 곡류
**핵심 로직:** 측방 침식(Lateral Erosion), 분급(Sorting), 유속 차이에 의한 퇴적.

| 지형 (Feature) | 핵심 변수 (Key Parameters) | 시각화 포인트 (Visualization) | 학습용 수식 (Formula Reference) |
| :--- | :--- | :--- | :--- |
| **선상지** | 입자 크기($d$), 유속 감소율($-\Delta v$) | 선정(자갈)-선앙(모래)-선단(점토) 분급 및 **복류천(지하수 흐름)** 단면도. | Stokes' Law (Settling Velocity) |
| **곡류 & 우각호** | 원심력($F_c$), 유로 굴곡도 | 공격사면(절벽) vs 퇴적사면(백사장). 홍수 시 유로 절단(Cutoff) 및 우각호 고립 애니메이션. | Helical Flow Model |
| **감입 곡류 (융기형)** | 융기 속도($U$), 기존 굴곡도 | **[Comparison Mode]** 자유 곡류(접시형 단면) vs 감입 곡류(밥그릇형 깊은 단면) 비교. | Incision Rate = Erosion - Uplift |
| **하안단구** | 지반 융기($U$), 기저면 변동 | 융기 이벤트 발생 시 강바닥이 깊어지며 범람원이 계단 모양 언덕(Terrace)으로 남음. | - |
| **범람원** | 홍수 빈도, 부유 하중 | 홍수 시 제방(두꺼움/모래)과 배후습지(얇음/점토)의 거리별 퇴적 차이. | Overbank Sedimentation |

### ⚓ Chapter 3. 하류 (Lower Course): 바다와의 균형
**핵심 로직:** 유속 소멸, 파랑/조류 에너지 상호작용.

| 지형 (Feature) | 핵심 변수 (Key Parameters) | 시각화 포인트 (Visualization) | 학습용 수식 (Formula Reference) |
| :--- | :--- | :--- | :--- |
| **삼각주** | 강 에너지 vs 파랑 vs 조류 | **[Triangle Mixer UI]** 3가지 힘 조절 → 조족상(미시시피) ↔ 원호상(나일) 모양 변환. | Galloway's Classification |
| **삼각강 (Estuary)** | 조차(Tidal Range), 조류 속도 | 강한 조류가 퇴적물을 쓸어가며 하구가 나팔 모양으로 확장되는 과정. | Tidal Scour Equation |
| **하중도** | 유속 사각지대, 식생 밀도 | 강폭이 넓은 곳에 모래섬 형성 후 식생이 자라며 고정되는 과정. | Vegetation Stabilization |

---

## 2. 정답지 이미지 목록 (Reference Images to Load)
*AI 학습 시 아래 파일명과 매칭되는 이미지를 함께 업로드할 것.*

1.  `v_shaped_valley_diagram.jpg` (V자곡 및 사면 붕괴 단면)
2.  `alluvial_fan_structure.jpg` (선상지 평면 및 지하 단면)
3.  `meander_cross_section.jpg` (공격사면/퇴적사면 비대칭 단면)
4.  `river_terrace_formation.jpg` (하안단구 형성 단계)
5.  `delta_classification.jpg` (삼각주 3가지 유형 비교)