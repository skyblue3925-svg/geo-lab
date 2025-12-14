# 🌍 [Geo-Lab AI] 통합 아키텍처 설계서 (Master Integration Plan)

**Project Name:** Geo-Lab AI: The Living Earth
**Version:** Global Build 1.0 (Integration Phase)
**Scope:** Full-stack Geomorphology Simulation (All Modules)
**Director:** [User Name]

---

## 0. 통합 개발 철학 (System Philosophy)

**"지형은 고립되어 있지 않다 (No Landform is an Island)."**
본 통합 시스템은 7개의 독립 모듈(하천, 해안, 카르스트, 화산, 빙하, 건조, 평야)을 **'가이아 엔진(Gaia Engine)'**이라는 하나의 물리 서버 위에서 유기적으로 구동한다. 사용자가 조절하는 기후와 지각 에너지가 나비 효과처럼 전 지구적 지형 변화를 일으키는 **순환 시스템(Feedback Loop)** 구현을 목표로 한다.

---

## 1. 시스템 아키텍처: 가이아 엔진 (The Gaia Engine)

모든 개별 모듈은 아래 3가지 **글로벌 변수(Global Variables)**에 종속되어 작동한다.

### 🎛️ 글로벌 컨트롤러 (Global Controllers)
1.  **지각 에너지 ($E_{tectonics}$):**
    * *Role:* 판의 이동 속도 및 마그마 활동성 제어.
    * *Impact:* $E \uparrow$ $\Rightarrow$ 신기 습곡 산지 융기, 화산 폭발 빈도 증가, 지진 발생.
2.  **기후 레벨 ($C_{climate}$):**
    * *Role:* 지구 평균 기온($T_{avg}$) 및 강수량($P_{avg}$) 제어.
    * *Impact:* $T \downarrow$ $\Rightarrow$ 빙하 확장 (빙기). $T \uparrow$ $\Rightarrow$ 빙하 후퇴 및 해수면 상승 (간빙기).
3.  **해수면 고도 ($H_{sea}$):**
    * *Role:* 침식 기준면(Base Level) 설정.
    * *Impact:* $H \downarrow$ $\Rightarrow$ 하천 하방 침식 강화(감입 곡류). $H \uparrow$ $\Rightarrow$ 하구 퇴적 강화(삼각주, 석호).

---

## 2. 모듈 간 상호작용 로직 (Cross-Module Interaction)

지형 모듈끼리 데이터를 주고받으며 새로운 지형을 생성하는 **인과관계 체인(Chain)**을 정의한다.

### 🔗 Chain A. [산지] $\leftrightarrow$ [건조]: 비그늘 효과 (Rain Shadow)
* **Logic:** 거대한 습곡 산맥이 융기하여 수증기를 막음.
* **Process:**
    1.  **[산지]** 모듈: 해발고도 $H > 3,000m$ 산맥 생성.
    2.  **[기상]** 엔진: 편서풍이 산맥에 부딪혀 비를 뿌림 (바람받이 사면).
    3.  **[건조]** 모듈 트리거: 산맥 반대편에 건조 기후 형성 $\rightarrow$ 사막/사구 생성.

### 🔗 Chain B. [빙하] $\leftrightarrow$ [평야]: 융빙수와 범람 (Meltwater Pulse)
* **Logic:** 빙하기가 끝나고 간빙기가 오면 막대한 물이 평야로 쏟아짐.
* **Process:**
    1.  **[빙하]** 모듈: 기온 상승($T \uparrow$)으로 빙하 후퇴.
    2.  **[수문]** 엔진: 융빙수 유입량($Q_{melt}$) 급증.
    3.  **[평야]** 모듈 트리거: 하천 유량 폭증 $\rightarrow$ 범람원 확대, 배후습지 형성, 하구 삼각주 성장 가속.

### 🔗 Chain C. [화산] $\leftrightarrow$ [카르스트]: 산성과 염기성 (Chemical Weathering)
* **Logic:** 화산 활동으로 인한 산성비가 석회암 용식을 가속화.
* **Process:**
    1.  **[화산]** 모듈: 화산 폭발로 대기 중 $SO_2, CO_2$ 농도 증가.
    2.  **[환경]** 엔진: 빗물의 $pH$ 농도 하락 (산성비).
    3.  **[카르스트]** 모듈 트리거: 기반암이 석회암인 지역의 용식 속도($Rate_{dissolution}$) 2배 가속 $\rightarrow$ 거대 동굴 생성.

### 🔗 Chain D. [빙하] $\leftrightarrow$ [해안]: 피오르의 탄생 (Fjord Formation)
* **Logic:** 빙하가 깎아낸 U자곡에 바닷물이 들어차 깊고 좁은 만을 형성.
* **Process:**
    1.  **[빙하]** 모듈: 빙하기에 해안까지 도달하는 거대 빙하가 U자곡을 깊게 침식.
    2.  **[기후]** 엔진: 간빙기 도래로 해수면 상승($H_{sea} \uparrow$).
    3.  **[해안]** 모듈 트리거: 바닷물이 U자곡으로 침투 $\rightarrow$ 피오르(Fjord) 형성.

### 🔗 Chain E. [화산] $\leftrightarrow$ [해안]: 현무암 해안 (Volcanic Coast)
* **Logic:** 용암이 바다에 닿으며 급격히 냉각되어 독특한 해안 지형 형성.
* **Process:**
    1.  **[화산]** 모듈: 해안 인근에서 현무암질 용암 분출.
    2.  **[냉각]** 엔진: 바닷물과 접촉하며 급랭 $\rightarrow$ 주상절리 형성.
    3.  **[해안]** 모듈 트리거: 주상절리 해안 절벽 생성 (예: 제주 중문 대포해안).

### 🔗 Chain F. [하천] $\leftrightarrow$ [해안]: 삼각주 vs 삼각강 (Delta vs Estuary)
* **Logic:** 하구에서 하천 에너지와 해양 에너지의 상대적 크기에 따라 퇴적 또는 침식 발생.
* **Process:**
    1.  **[하천]** 모듈: 하구에 퇴적물 공급 (Sediment Load).
    2.  **[해안]** 엔진: 파랑/조류의 퇴적물 재분배 능력 계산.
    3.  **결과:** 하천 우세 → 삼각주(Delta), 조류 우세 → 삼각강(Estuary).

---

## 3. 캠페인 시나리오 (Campaign Mode Missions)

학생들이 지형 형성 원리를 게임처럼 익힐 수 있는 미션 목록.

| 시나리오 (Title) | 목표 (Mission Objective) | 필요 모듈 조합 | 난이도 |
| :--- | :--- | :--- | :--- |
| **불과 얼음의 노래** | 화산 폭발로 생긴 산 정상에 만년설과 빙하를 형성하라. (아이슬란드, 킬리만자로 형) | **화산 + 빙하** | ⭐⭐⭐ |
| **사막의 기적** | 건조한 사막에 외래 하천을 흐르게 하여 하구에 거대 삼각주를 건설하라. (이집트 나일강 형) | **건조 + 평야** | ⭐⭐⭐⭐ |
| **시간의 동굴** | 융기된 산지를 침식시켜 지하수면을 낮추고, 석회동굴을 육상에 노출시켜라. (단양 고수동굴 형) | **산지 + 카르스트** | ⭐⭐ |
| **대홍수 (The Flood)** | 빙하기를 끝내고 해수면을 100m 상승시켜, U자곡을 피오르로, 하구를 석호로 만들어라. | **빙하 + 평야 + 해안** | ⭐⭐⭐⭐⭐ |

---

## 4. UI/UX: 마스터 대시보드 (Master Dashboard Design)

### 🖥️ Viewport Layout
1.  **Main Globe (Center):** 3D 지구본 뷰. 휠 스크롤로 우주(위성 사진)에서 지하(단면도)까지 심리스 줌인/아웃.
2.  **Control Deck (Bottom):** 타임라인 슬라이더. (고생대 $\leftrightarrow$ 현세). 시간을 돌리며 지형 변화 관찰.
3.  **Mini-Map (Right-Top):** 현재 지형의 형성 원리(작용)를 아이콘으로 표시 (🌊유수, 🌬️바람, 🌋마그마, ❄️빙하).

### 📊 Data Visualization
* **Cross-Section Overlay:** 지표면 아래 지질 구조(습곡, 단층, 지하수, 마그마 방)를 엑스레이처럼 투시.
* **Eco-System Status:** 현재 지형에 적합한 농업(벼농사 vs 밭농사 vs 목축) 및 거주 적합도 점수 표시.

---

## 5. 데이터 통신 규격 (JSON Data Structure)

통합 엔진이 처리할 최종 월드 상태 데이터 예시.

```json
{
  "World_State": {
    "Timestamp": "Epoch_Holocene_Early",
    "Global_Temp": 14.5,
    "Sea_Level_Base": 0
  },
  "Active_Regions": [
    {
      "Region_ID": "NE_Asia",
      "Base_Rock": "Granite",
      "Landforms": [
        {"Type": "Mountain", "Age": "Old", "Feature": "Erosion_Dome"},
        {"Type": "Plain", "Feature": "Alluvial_Fan", "Source": "Mountain_Runoff"}
      ],
      "Climate_Effect": "Monsoon"
    },
    {
      "Region_ID": "Pacific_Rim",
      "Base_Rock": "Basalt",
      "Landforms": [
        {"Type": "Volcano", "Shape": "Shield", "Status": "Active"}
      ],
      "Tectonic_Activity": "High"
    }
  ]
}