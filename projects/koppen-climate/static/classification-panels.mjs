export function getRuleTraceRows({
  analysis,
  metrics,
  explanationCode,
  displayCode,
}) {
  if (analysis.classification.code === "Ocean") {
    return [{ label: "육지 비율", value: `${(analysis.profile.landness * 100).toFixed(0)}%`, detail: "육상이 부족해 해양 셀로 처리", state: "neutral" }];
  }

  if (explanationCode === "AH" || explanationCode === "CH") {
    return [
      { label: "해발고도", value: `${Math.round(analysis.profile.elevation)} m`, detail: "고지대 냉각이 크면 고산형으로 읽음", state: analysis.profile.elevation >= 1200 ? "pass" : "warn" },
      { label: "연평균 기온", value: `${metrics.annualTemp.toFixed(1)}°C`, detail: "같은 위도 저지대보다 낮은지 함께 확인", state: "neutral" },
      { label: "그래프 판정", value: displayCode, detail: explanationCode === "AH" ? "저위도 고산형" : "중위도 고산형", state: "pass" },
    ];
  }

  if (explanationCode.startsWith("A")) {
    return [
      { label: "최한월 ≥ 18°C", value: `${metrics.coldest.toFixed(1)}°C`, detail: metrics.coldest >= 18 ? "충족" : "미충족", state: metrics.coldest >= 18 ? "pass" : "warn" },
      { label: "최건월", value: `${metrics.driest.toFixed(0)} mm`, detail: `Af 기준 60 mm, Am 기준 ${metrics.monsoonThreshold.toFixed(0)} mm`, state: "pass" },
      { label: "연강수량", value: `${metrics.annualPrecip.toFixed(0)} mm`, detail: "열대 내 건기/우기 해석에 사용", state: "neutral" },
    ];
  }

  if (explanationCode.startsWith("B")) {
    return [
      { label: "연강수량", value: `${metrics.annualPrecip.toFixed(0)} mm`, detail: `건조 한계 ${metrics.drynessThreshold.toFixed(0)} mm`, state: metrics.annualPrecip < metrics.drynessThreshold ? "pass" : "warn" },
      { label: "여름 강수 비율", value: `${(metrics.summerRatio * 100).toFixed(0)}%`, detail: `보정값 ${metrics.drynessOffset.toFixed(0)} mm`, state: "neutral" },
      { label: "연평균 기온", value: `${metrics.annualTemp.toFixed(1)}°C`, detail: metrics.annualTemp >= 18 ? "h 분기" : "k 분기", state: "pass" },
    ];
  }

  if (explanationCode.startsWith("E")) {
    return [
      { label: "최난월", value: `${metrics.warmest.toFixed(1)}°C`, detail: "10°C 미만이면 E기후", state: metrics.warmest < 10 ? "pass" : "warn" },
      { label: "빙설 경계", value: `${metrics.warmest.toFixed(1)}°C`, detail: metrics.warmest < 0 ? "EF" : "ET", state: "neutral" },
      { label: "연강수량", value: `${metrics.annualPrecip.toFixed(0)} mm`, detail: "한대 내부에서도 건조 정도를 읽는 참고값", state: "neutral" },
    ];
  }

  return [
    { label: "최난월", value: `${metrics.warmest.toFixed(1)}°C`, detail: "10°C 이상이어야 C/D 가능", state: metrics.warmest >= 10 ? "pass" : "warn" },
    { label: "최한월", value: `${metrics.coldest.toFixed(1)}°C`, detail: metrics.coldest > -3 ? "C 경계(-3°C 초과)" : "D 경계(-3°C 이하)", state: "pass" },
    {
      label: "건기 판정",
      value: `여름 ${metrics.driestSummer.toFixed(0)} / 겨울 ${metrics.driestWinter.toFixed(0)} mm`,
      detail: metrics.driestSummer < 40 && metrics.driestSummer < metrics.wettestWinter / 3 ? "s" : metrics.driestWinter < metrics.wettestSummer / 10 ? "w" : "f",
      state: "neutral",
    },
    { label: "10°C 이상 월 수", value: `${metrics.warmMonths}개월`, detail: metrics.warmest >= 22 && metrics.warmMonths >= 4 ? "a" : metrics.warmMonths >= 4 ? "b" : "c/d", state: "neutral" },
  ];
}

export function getKoppenLetterBreakdown({
  analysis,
  code,
  metrics,
}) {
  if (analysis.classification.code === "Ocean") {
    return [
      {
        letter: "Ocean",
        label: "해양 셀",
        detail: `육지 비율 ${(analysis.profile.landness * 100).toFixed(0)}%로 낮아 쾨펜 분류보다 배경 참고층으로 봅니다.`,
      },
    ];
  }

  if (code === "AH" || code === "CH") {
    return [
      {
        letter: code[0],
        label: "고산",
        detail: `해발 ${Math.round(analysis.profile.elevation)} m의 고지대라 같은 위도 저지대보다 기온이 뚜렷하게 낮습니다.`,
      },
      {
        letter: code[1],
        label: code === "AH" ? "저위도형" : "중위도형",
        detail: code === "AH"
          ? "적도·아열대 고지대에서 평가원식 기후그래프 해석에 자주 쓰는 고산형입니다."
          : "중위도 고지대에서 쓰는 고산형 판정입니다.",
      },
    ];
  }

  const chips = [];
  const firstLetter = code[0];
  const secondLetter = code[1];
  const thirdLetter = code[2];

  const firstMeta = {
    A: { label: "열대", detail: `최한월 ${metrics.coldest.toFixed(1)}°C로 18°C 이상입니다.` },
    B: { label: "건조", detail: `연강수량 ${metrics.annualPrecip.toFixed(0)} mm가 건조 한계 ${metrics.drynessThreshold.toFixed(0)} mm보다 적습니다.` },
    C: { label: "온대", detail: `최한월 ${metrics.coldest.toFixed(1)}°C로 -3°C 초과, 최난월 ${metrics.warmest.toFixed(1)}°C로 10°C 이상입니다.` },
    D: { label: "냉대", detail: `최한월 ${metrics.coldest.toFixed(1)}°C로 -3°C 이하이며 최난월은 10°C 이상입니다.` },
    E: { label: "한대", detail: `최난월 ${metrics.warmest.toFixed(1)}°C로 10°C 미만입니다.` },
  };
  chips.push({ letter: firstLetter, ...firstMeta[firstLetter] });

  if (firstLetter === "A") {
    const secondMeta = {
      f: { label: "건기 없음", detail: `최건월 ${metrics.driest.toFixed(0)} mm로 60 mm 이상입니다.` },
      m: { label: "몬순", detail: `최건월 ${metrics.driest.toFixed(0)} mm로 Af보다 건조하지만 몬순 한계 ${metrics.monsoonThreshold.toFixed(0)} mm는 넘습니다.` },
      w: { label: "겨울 건기", detail: "연중 고온이지만 겨울철 건기가 뚜렷합니다." },
      s: { label: "여름 건기", detail: "연중 고온이지만 여름철이 상대적으로 더 건조합니다." },
    };
    if (secondMeta[secondLetter]) {
      chips.push({ letter: secondLetter, ...secondMeta[secondLetter] });
    }
    return chips;
  }

  if (firstLetter === "B") {
    const secondMeta = {
      W: { label: "사막", detail: "강수가 건조 한계의 절반 이하라 사막 단계입니다." },
      S: { label: "스텝", detail: "강수가 건조 한계 이하지만 사막보다는 많아 초원 단계입니다." },
    };
    const thirdMeta = {
      h: { label: "고온", detail: `연평균 기온 ${metrics.annualTemp.toFixed(1)}°C로 18°C 이상입니다.` },
      k: { label: "냉량", detail: `연평균 기온 ${metrics.annualTemp.toFixed(1)}°C로 18°C 미만입니다.` },
    };
    if (secondMeta[secondLetter]) {
      chips.push({ letter: secondLetter, ...secondMeta[secondLetter] });
    }
    if (thirdMeta[thirdLetter]) {
      chips.push({ letter: thirdLetter, ...thirdMeta[thirdLetter] });
    }
    return chips;
  }

  if (firstLetter === "E") {
    const secondMeta = {
      T: { label: "툰드라", detail: `최난월 ${metrics.warmest.toFixed(1)}°C가 0~10°C 사이입니다.` },
      F: { label: "빙설", detail: `최난월 ${metrics.warmest.toFixed(1)}°C도 0°C 미만입니다.` },
    };
    if (secondMeta[secondLetter]) {
      chips.push({ letter: secondLetter, ...secondMeta[secondLetter] });
    }
    return chips;
  }

  const secondMeta = {
    f: { label: "사계절 습윤", detail: "뚜렷한 건기가 없어 연중 강수가 비교적 고릅니다." },
    w: { label: "겨울 건기", detail: `겨울 최건월 ${metrics.driestWinter.toFixed(0)} mm로 겨울이 뚜렷하게 건조합니다.` },
    s: { label: "여름 건기", detail: `여름 최건월 ${metrics.driestSummer.toFixed(0)} mm로 여름이 뚜렷하게 건조합니다.` },
  };
  const thirdMeta = {
    a: { label: "더운 여름", detail: `최난월 ${metrics.warmest.toFixed(1)}°C로 22°C 이상입니다.` },
    b: { label: "온난한 여름", detail: `10°C 이상 달이 ${metrics.warmMonths}개월이며 최난월은 22°C 미만입니다.` },
    c: { label: "짧고 서늘한 여름", detail: `10°C 이상 달이 ${metrics.warmMonths}개월로 적어 여름이 짧습니다.` },
    d: { label: "혹한 겨울", detail: "매우 추운 겨울이 나타나는 냉대 하위형입니다." },
  };

  if (secondMeta[secondLetter]) {
    chips.push({ letter: secondLetter, ...secondMeta[secondLetter] });
  }
  if (thirdMeta[thirdLetter]) {
    chips.push({ letter: thirdLetter, ...thirdMeta[thirdLetter] });
  }
  return chips;
}
