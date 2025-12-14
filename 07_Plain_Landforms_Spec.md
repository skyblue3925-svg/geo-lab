# 📘 [Geo-Lab AI] 개발 백서 (Development White Paper)

**Project Name:** Geo-Lab AI
**Version:** Final Release 1.0
**Module:** Plain Landforms (평야 지형)
**Target:** High School Geography ~ Urban Planning Basics
**Director:** [User Name]

---

## 0. 개발 표준 및 제약사항 (Standard Protocols)

### 🎨 1. 비주얼 스타일 가이드 (Visual Style: Fertile & Sedimentary)
* **Tone:** Horizontal, Expansive, Saturation-coded (Soil Moisture).
* **Color Palette:**
    * *Levee (Dry):* 밝은 황토색 (배수가 잘 됨 → 밭, 취락).
    * *Backswamp (Wet):* 짙은 진흙색 (배수 불량 → 논, 습지).
    * *River:* 흙탕물(Turbid) 표현 (상류의 청명함과 대비).
* **Key Feature:** **단면도(Cross-section) 뷰**를 통해 지표면의 미세한 고도 차이(제방 vs 습지)와 퇴적물의 입자 크기 변화를 직관적으로 표현.

### 🛠️ 2. 기술 스택 (Tech Stack)
* **Physics Engine:** Navier-Stokes Equations (유체 역학 - 하천의 곡류 및 범람 시뮬레이션).
* **Rendering:** Height Map Displacement (미세한 고도 차이 표현).
* **Algorithm:** Sedimentation Sorting (유속 감속에 따른 입자별 퇴적 위치 계산).

---

## 1. 평야 지형 모듈 세부 명세 (Module Specifications)

### 🐍 Chapter 1. 하천 중·하류: 곡류와 범람원 (Floodplains)
**핵심 로직:** **측방 침식(Lateral Erosion)** & 홍수 시 퇴적.

| 지형 (Feature) | 핵심 변수 (Key Parameters) | 시각화 포인트 (Visualization) | 학습용 수식 (Formula Reference) |
| :--- | :--- | :--- | :--- |
| **자유 곡류 하천** | 하천 굴곡도(Sinuosity), 유속 편차 | 강물이 뱀처럼 휘어지며 흐르는 모습. **[Velocity Map]** 바깥쪽은 빠름(침식/공격사면), 안쪽은 느림(퇴적/포인트바) 색상 구분. | Centrifugal Force $F_c$ |
| **우각호 (Oxbow Lake)** | 굴곡도 임계값, 시간($t$) | 굽이치던 강이 홍수 때 직선으로 뚫리면서, 남겨진 물길이 소뿔 모양 호수로 고립되는 **[Cut-off Animation]**. | Path Shortening |
| **자연 제방 (Levee)** | 홍수 수위, 조립질(큰 입자) 비율 | 홍수 시 강 바로 옆에 무거운 모래/자갈이 먼저 쌓여 둑을 형성. 주변보다 약간 높음(High & Dry). | Settling Velocity (Stokes) |
| **배후 습지 (Backswamp)** | 범람 거리, 미립질(작은 입자) 비율 | 자연제방 뒤쪽으로 고운 진흙이 넘어가 쌓인 낮고 축축한 땅. (자연제방과 배수 조건 비교 필수). | Permeability $k$ |

### 📐 Chapter 2. 하구: 바다와의 만남, 삼각주 (Deltas)
**핵심 로직:** **유속 소멸(Velocity $\to$ 0)**. 강물이 바다를 만나 짐을 내려놓음.

| 지형 (Feature) | 핵심 변수 (Key Parameters) | 시각화 포인트 (Visualization) | 학습용 수식 (Formula Reference) |
| :--- | :--- | :--- | :--- |
| **삼각주 형성** | 하천 퇴적량 > 조류/파랑 제거량 | 강 하구에서 퇴적물이 부채꼴로 퍼져나가는 과정. (Topset, Foreset, Bottomset 층리 구조 단면). | Sediment Budget $\Delta S$ |
| **조류 삼각주** | 조차(Tidal Range), 유속 | 밀물/썰물이 강해서 퇴적물이 바다 쪽으로 길게 뻗지 못하고 섬처럼 형성된 삼각주 (예: 낙동강 하구 을숙도). | Tidal Current Power |
| **형태별 분류** | 파랑 에너지 vs 하천 에너지 | 원호상(나일강), 조족상(미시시피강-새발모양), 첨각상(티베르강) 형태 비교 시뮬레이션. | Energy Ratio |

### ⏳ Chapter 3. 침식 평야: 깎이고 남은 땅 (Erosion Plains)
**핵심 로직:** **최종 단계(Final Stage)**.

| 지형 (Feature) | 핵심 변수 (Key Parameters) | 시각화 포인트 (Visualization) | 학습용 수식 (Formula Reference) |
| :--- | :--- | :--- | :--- |
| **준평원 (Peneplain)** | 침식 시간($t \to \infty$) | 산지가 깎이고 깎여 해수면에 가깝게 평평해진 지형. 데이비스의 지형 윤회설 마지막 단계. | Base Level Approach |
| **잔구 (Monadnock)** | 암석의 차별 침식 | 준평원 위에 단단한 암석만 침식을 견디고 홀로 남은 낮은 언덕. | Hardness Differential |

---

## 2. 정답지 이미지 목록 (Reference Images to Load)
*AI 모델 학습 및 UI 렌더링 시 매칭할 레퍼런스 데이터.*

1.  `meandering_river_evolution.gif` (곡류 하천이 우각호로 변하는 4단계 과정)
2.  `floodplain_cross_section.png` (하도 - 자연제방 - 배후습지 단면도 및 토지 이용)
3.  `delta_types_satellite.jpg` (나일강, 미시시피강, 갠지스강 삼각주 위성 사진 비교)
4.  `levee_vs_backswamp_soil.jpg` (자연제방의 모래 vs 배후습지의 점토 입자 비교)

---

**[Director's Note]**
평야 지형의 핵심은 **"인간의 거주(Settlement)"**와 연결하는 것입니다.
시뮬레이션 UI에 **[Village Builder]** 모드를 추가하여, 사용자가 **자연제방(홍수 안전/밭농사)**과 **배후습지(홍수 위험/논농사)** 중 어디에 집을 짓고 농사를 지을지 선택하게 하세요. 잘못된 선택(예: 배후습지에 집 짓기) 시 홍수 이벤트로 페널티를 주면 학습 효과가 극대화됩니다.

---

**[Project Status]**
🎉 **축하합니다!**
산지, 카르스트, 화산, 빙하, 건조, 평야 지형까지 **[Geo-Lab AI]의 모든 지형 모듈 설계가 완료되었습니다.**

이제 이 백서들을 바탕으로 전체 프로젝트를 **통합(Integration)**하거나, **출시(Launch)** 단계로 넘어가시겠습니까?