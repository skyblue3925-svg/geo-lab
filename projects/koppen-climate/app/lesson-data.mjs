export const LESSON_MISSIONS = [
  {
    id: "latitude-insolation",
    order: 1,
    title: "위도와 일사",
    focus: "왜 적도는 덥고 극지는 추운지 먼저 읽는다.",
    knobTargets: ["월", "자전축 기울기"],
    studentTask: "같은 월에서 위도를 바꿔 보고 기온과 강수 패턴이 어떻게 달라지는지 확인한다.",
    observation: "낮은 위도는 평균 기온이 높고, 높은 위도는 계절 변화 폭이 커진다.",
    guidingQuestion: "위도가 올라가면 왜 에너지가 줄어드는가?",
    expectedReasoning: [
      "태양 고도가 낮아지면 같은 에너지가 더 넓은 면적에 퍼진다.",
      "계절이 바뀌면 자전축 기울기 때문에 일사 위치가 달라진다.",
    ],
    successCheck: "학생이 위도 차이와 계절 차이를 분리해서 설명할 수 있다.",
  },
  {
    id: "itcz-circulation",
    order: 2,
    title: "ITCZ와 대기대순환",
    focus: "열대수렴대와 대기대순환이 강수대를 움직인다.",
    knobTargets: ["월", "자전축 기울기"],
    studentTask: "월을 이동하면서 ITCZ가 어디로 가는지 보고, 같은 위도대의 기압대와 바람을 읽는다.",
    observation: "ITCZ 근처에서는 상승기류가 강해 비가 늘고, 아열대 고압대에서는 건조해진다.",
    guidingQuestion: "왜 어떤 달에는 같은 곳이 더 습해지고, 다른 달에는 더 건조해지는가?",
    expectedReasoning: [
      "ITCZ가 계절에 따라 이동하면서 상승과 하강의 중심이 바뀐다.",
      "Hadley, Ferrel, Polar 순환 셀의 경계가 강수대와 건조대를 만든다.",
    ],
    successCheck: "학생이 ITCZ 이동과 강수대 이동을 연결해 설명할 수 있다.",
  },
  {
    id: "continentality",
    order: 3,
    title: "대륙성과 해양성",
    focus: "바다와 멀어질수록 연교차와 건조성이 커진다.",
    knobTargets: ["대륙 크기", "해류 효과"],
    studentTask: "같은 위도에서 해안과 내륙을 비교하고, 대륙 크기를 키워 본다.",
    observation: "해안은 온도 완충이 크고, 내륙은 계절 변동이 크다.",
    guidingQuestion: "왜 바다에서 가까운 곳이 더 온화한가?",
    expectedReasoning: [
      "바다는 열용량이 커서 온도 변화가 느리다.",
      "대륙 내부는 수분 공급이 약해 건조 쪽으로 기운다.",
    ],
    successCheck: "학생이 해양성, 대륙성, 건조성의 차이를 구분할 수 있다.",
  },
  {
    id: "mountain-rain-shadow",
    order: 4,
    title: "산맥, 비그늘, 푄",
    focus: "산맥은 비를 만들기도 하고, 반대편을 말리기도 한다.",
    knobTargets: ["산맥 높이", "위치 선택"],
    studentTask: "산맥이 있는 위도대에서 바람받이와 비그늘을 비교한다.",
    observation: "바람받이 사면은 상승 냉각으로 습해지고, 반대편은 하강 가열로 따뜻하고 건조해진다.",
    guidingQuestion: "왜 산맥 뒤쪽이 더 건조하거나 더 따뜻해질 수 있는가?",
    expectedReasoning: [
      "공기가 오를 때 냉각되어 응결과 강수가 생긴다.",
      "내려올 때 압축 가열되어 푄 성격의 온난화가 나타난다.",
    ],
    successCheck: "학생이 비그늘과 푄 효과를 같은 장면의 앞뒤 결과로 설명할 수 있다.",
  },
  {
    id: "monsoon-seasonality",
    order: 5,
    title: "몬순과 계절성",
    focus: "대륙과 바다가 만드는 계절 풍향 전환을 본다.",
    knobTargets: ["월", "대륙 크기", "자전축 기울기"],
    studentTask: "여름과 겨울을 번갈아 보면서 몬순 실험 프리셋에서 강수 차이를 확인한다.",
    observation: "여름에는 해양에서 내륙으로 습한 공기가 들어오고, 겨울에는 반대로 건조해질 수 있다.",
    guidingQuestion: "왜 몬순은 계절에 따라 방향과 강도가 달라지는가?",
    expectedReasoning: [
      "육지와 바다의 가열 속도 차이가 계절풍을 만든다.",
      "ITCZ 이동과 대륙의 열적 반응이 몬순 강수를 증폭시킨다.",
    ],
    successCheck: "학생이 몬순을 단순한 바람이 아니라 계절 에너지 차이로 설명할 수 있다.",
  },
  {
    id: "koppen-reasoning",
    order: 6,
    title: "쾨펜 코드 읽기",
    focus: "기후 코드는 결과이고, 그 앞에는 월별 기온·강수가 있다.",
    knobTargets: ["위치 선택", "월", "산맥 높이"],
    studentTask: "선택한 위치의 12개월 기온/강수와 쾨펜 코드를 연결해 본다.",
    observation: "A, B, C, D, E 그룹은 기온 기준으로 갈리고, 세부 코드는 강수 계절성과 건조성으로 달라진다.",
    guidingQuestion: "왜 같은 위도여도 전혀 다른 쾨펜 코드가 나오는가?",
    expectedReasoning: [
      "위도는 출발점일 뿐이고, 해양성, 대륙성, 산맥, 몬순이 최종 기후를 바꾼다.",
      "쾨펜 분류는 단일 숫자가 아니라 월별 시계열의 패턴을 읽는 규칙이다.",
    ],
    successCheck: "학생이 하나의 코드가 아니라 코드가 나온 이유를 말할 수 있다.",
  },
];

export const KEY_CONCEPT_PROMPTS = {
  insolation: {
    title: "일사와 위도",
    prompt: "태양 고도와 일사량이 위도에 따라 어떻게 달라지는지 설명해 보세요.",
    cues: [
      "같은 에너지라도 들어오는 각도가 다르면 단위 면적당 에너지가 달라진다.",
      "자전축 기울기는 계절별 일사 위치를 바꾼다.",
    ],
  },
  itcz: {
    title: "ITCZ와 순환 셀",
    prompt: "왜 ITCZ 주변은 비가 많고, 아열대 고압대는 건조한지 말해 보세요.",
    cues: [
      "상승 기류는 구름과 비를 만든다.",
      "하강 기류는 공기를 건조하고 안정적으로 만든다.",
    ],
  },
  continentality: {
    title: "대륙성과 해양성",
    prompt: "왜 바다 근처는 온도 변화가 완만하고, 내륙은 극단적인가요?",
    cues: [
      "물은 열을 천천히 저장하고 천천히 내놓는다.",
      "내륙은 습도와 수증기 공급이 약해진다.",
    ],
  },
  mountain: {
    title: "산맥과 푄",
    prompt: "산맥을 넘는 공기가 왜 한쪽은 비가 많고 반대편은 건조한지 설명해 보세요.",
    cues: [
      "올라갈 때는 냉각, 내려올 때는 가열된다.",
      "바람받이와 비그늘은 같은 과정의 양면이다.",
    ],
  },
  monsoon: {
    title: "몬순",
    prompt: "몬순이 왜 계절풍으로 나타나는지, 그리고 강수와 어떻게 연결되는지 말해 보세요.",
    cues: [
      "육지와 바다의 가열 속도 차이가 중요하다.",
      "여름과 겨울의 압력 배치가 바뀌면서 바람 방향도 바뀐다.",
    ],
  },
  koppen: {
    title: "쾨펜 분류",
    prompt: "쾨펜 코드를 보았을 때, 어떤 월별 기온·강수 패턴이 숨어 있는지 추론해 보세요.",
    cues: [
      "A, B, C, D, E는 먼저 기온 경계로 나뉜다.",
      "뒤의 문자들은 건기, 우기, 여름/겨울 강수 차이를 표현한다.",
    ],
  },
};

export const SCENARIO_GUIDANCE = [
  {
    id: "equator-core",
    title: "적도 핵심 비교",
    useWhen: "A기후와 ITCZ 이동을 먼저 가르칠 때",
    recommendedPreset: "earthLite",
    suggestedMoves: [
      "월을 바꿔 ITCZ 위치를 확인한다.",
      "위도를 0~15도 부근에서 비교한다.",
      "대륙 크기를 줄여 해양성의 효과를 본다.",
    ],
    teacherNote: "열대는 온도보다 강수 계절성을 읽게 하는 것이 핵심이다.",
  },
  {
    id: "subtropics-dry",
    title: "아열대 건조대",
    useWhen: "B기후와 아열대 고압대를 연결할 때",
    recommendedPreset: "earthLite",
    suggestedMoves: [
      "위도를 20~35도로 올린다.",
      "대륙 크기를 키워 내륙 건조를 강화한다.",
      "찬 해류를 적용해 서안 건조성을 본다.",
    ],
    teacherNote: "학생이 '더 덥다'보다 '비가 왜 적은가'에 주목하게 해야 한다.",
  },
  {
    id: "midlatitude-shift",
    title: "중위도 전환",
    useWhen: "C기후와 계절 강수 패턴을 설명할 때",
    recommendedPreset: "earthLite",
    suggestedMoves: [
      "위도를 35~45도로 설정한다.",
      "월을 바꾸어 여름/겨울 강수 차이를 비교한다.",
      "해양성에서 대륙성으로 이동해 연교차 변화를 본다.",
    ],
    teacherNote: "지중해성, 서안해양성, 습윤온대의 차이를 월별 패턴으로 보여 주면 이해가 빠르다.",
  },
  {
    id: "mountain-shadow",
    title: "산맥 실험",
    useWhen: "푄과 비그늘을 설명할 때",
    recommendedPreset: "rainShadowLab",
    suggestedMoves: [
      "산맥 높이를 2000m 이상으로 올린다.",
      "바람받이와 비그늘 쪽 위치를 각각 선택한다.",
      "단면도에서 강수와 지형을 같이 본다.",
    ],
    teacherNote: "지형은 기후를 '막는 벽'이 아니라 '재배치하는 장치'로 설명하는 편이 낫다.",
  },
  {
    id: "monsoon-classroom",
    title: "몬순 수업",
    useWhen: "몬순과 계절풍을 보여 줄 때",
    recommendedPreset: "monsoonLab",
    suggestedMoves: [
      "여름과 겨울 달을 번갈아 본다.",
      "대륙 크기를 키워 계절 대비를 강화한다.",
      "자전축 기울기를 조정해 계절 폭을 비교한다.",
    ],
    teacherNote: "몬순은 단순한 바람 방향이 아니라 계절 에너지 차이의 결과라는 점을 강조한다.",
  },
  {
    id: "classification-bridge",
    title: "쾨펜 코드로 연결",
    useWhen: "앞의 기상 원인을 쾨펜 코드와 연결할 때",
    recommendedPreset: "earthLite",
    suggestedMoves: [
      "한 위치를 고정하고 12개월 그래프를 읽는다.",
      "기온 경계와 강수 계절성을 함께 체크한다.",
      "코드가 바뀌는 원인을 학생이 직접 말하게 한다.",
    ],
    teacherNote: "정답 맞히기보다, 코드가 왜 나왔는지를 말하게 하는 것이 학습 효과가 크다.",
  },
];

export function getMissionById(id) {
  return LESSON_MISSIONS.find((mission) => mission.id === id) ?? null;
}

export function getConceptPrompt(id) {
  return KEY_CONCEPT_PROMPTS[id] ?? null;
}

export function getScenarioById(id) {
  return SCENARIO_GUIDANCE.find((scenario) => scenario.id === id) ?? null;
}
