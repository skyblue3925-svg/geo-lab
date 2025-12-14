# 📘 [Geo-Lab AI] 개발 백서 (Development White Paper)

**Project Name:** Geo-Lab AI
**Version:** Final Release 1.0
**Module:** Karst Landforms (카르스트 지형)
**Target:** High School Geography ~ Undergraduate Geology
**Director:** [User Name]

---

## 0. 개발 표준 및 제약사항 (Standard Protocols)

### 🎨 1. 비주얼 스타일 가이드 (Visual Style: Subsurface & Texture)
* **Tone:** Cross-sectional, Chemically Reactive, Hydrological.
* **Color Palette:**
    * *Limestone:* 밝은 회백색 (기반암).
    * *Soil (Terra Rossa):* 붉은 갈색 (산화철 성분 강조).
    * *Water:* 투명한 청록색 (지하수 위주).
    * *Vegetation:* 짙은 녹색 (돌리네 내부 식생).
* **Key Feature:** 지표면(Surface)과 지하(Subsurface)를 동시에 보여주는 **이중 레이어(Dual-Layer) 뷰** 지원. 용식 반응 시 거품(Reaction Bubble) 이펙트 적용.

### 🛠️ 2. 기술 스택 (Tech Stack)
* **Core Engine:** Chemical Weathering Simulator based on $pH$ & $Temperature$.
* **Rendering:** Voxel-based Terrain (동굴 형성을 위한 내부 굴착 표현).
* **Physics:** Fluid Dynamics (지하수 흐름 및 침투).

---

## 1. 카르스트 지형 모듈 세부 명세 (Module Specifications)

### 💧 Chapter 1. 지표 카르스트: 물이 조각한 대지
**핵심 로직:** **탄산칼슘 용식 작용 (Dissolution)**. 빗물이 석회암을 녹여 지표면이 함몰됨.

| 지형 (Feature) | 핵심 변수 (Key Parameters) | 시각화 포인트 (Visualization) | 학습용 수식 (Formula Reference) |
| :--- | :--- | :--- | :--- |
| **용식 메커니즘** | 빗물 산도($pH$), 탄산가스 농도 | 빗물이 닿는 즉시 암석 표면이 녹아내리는 **[Shader Effect]**. 화학식 오버레이. | $CaCO_3 + H_2O + CO_2 \leftrightarrow Ca(HCO_3)_2$ |
| **돌리네 (Doline)** | 절리 밀도, 시간($t$) | 지표면에 빗물이 고이다가 배수구처럼 빠지며 원형으로 움푹 꺼지는 애니메이션. | Sinkhole Radius $R(t)$ |
| **우발라 & 폴리에** | 돌리네 결합 확률, 기반암 깊이 | 인접한 여러 개의 돌리네가 합쳐져 거대 분지(우발라)가 되고, 평평한 들판(폴리에)이 되는 과정. | Merge Function $f(D_1, D_2)$ |
| **테라로사 (Terra Rossa)** | 불용성 잔류물 비율 | 석회암이 녹고 남은 붉은 흙이 지표면을 덮는 텍스처 매핑 변화 (White → Red). | Residue Accumulation |

### 🦇 Chapter 2. 지하 카르스트: 어둠 속의 예술
**핵심 로직:** **침전 작용 (Precipitation)**. 녹았던 석회질이 다시 굳어짐.

| 지형 (Feature) | 핵심 변수 (Key Parameters) | 시각화 포인트 (Visualization) | 학습용 수식 (Formula Reference) |
| :--- | :--- | :--- | :--- |
| **석회 동굴** | 지하수 유량, 수위 변화 | **[X-Ray Mode]** 지하수면 아래에서 석회암이 녹아 빈 공간(Cavity)이 확장되는 과정. | Cave Volume Expansion |
| **종유석 & 석순** | 낙수 속도($V_{drip}$), 증발률 | 천장에서 물방울이 떨어지며 고드름(종유석)이 자라고, 바닥에서 죽순(석순)이 솟아오름. | Growth Rate $\approx mm/year$ |
| **석주 (Column)** | 성장 속도, 동굴 높이($H$) | 위(종유석)와 아래(석순)가 만나 기둥으로 연결되는 순간 **[Highlight Effect]**. | Connection Event |

### 🏞️ Chapter 3. 탑 카르스트: 열대의 기암괴석 (Bonus)
**핵심 로직:** **고온 다습 & 차별 침식**.

| 지형 (Feature) | 핵심 변수 (Key Parameters) | 시각화 포인트 (Visualization) | 학습용 수식 (Formula Reference) |
| :--- | :--- | :--- | :--- |
| **탑 카르스트** | 강수량($P_{high}$), 기온($T_{high}$) | 평지에 탑처럼 솟은 봉우리 형성 (베트남 하롱베이, 중국 구이린 스타일). 측면 침식 강조. | Tropical Erosion Rate |

---

## 2. 정답지 이미지 목록 (Reference Images to Load)
*AI 모델 학습 및 UI 렌더링 시 매칭할 레퍼런스 데이터.*

1.  `chemical_weathering_reaction.png` (탄산칼슘 용식 화학식 및 모식도)
2.  `doline_uvala_polje_progression.jpg` (돌리네에서 폴리에로 커지는 단계별 지도)
3.  `cave_interior_structure.jpg` (종유석, 석순, 석주가 있는 동굴 내부 단면도)
4.  `tower_karst_landscape.jpg` (탑 카르스트의 지형적 특징)

---

**[Director's Note]**
카르스트 모듈은 **'화학 반응'**이 지형을 어떻게 바꾸는지 보여주는 것이 핵심입니다. $CaCO_3$ 화학식이 시뮬레이션 내에서 트리거로 작동하도록 로직을 점검하십시오.
승인하시면 다음 **'화산 지형'**으로 넘어가겠습니다.