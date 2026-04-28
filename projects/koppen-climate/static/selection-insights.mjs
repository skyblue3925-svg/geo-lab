function formatSigned(value, unit) {
  return `${value >= 0 ? "+" : ""}${value.toFixed(unit === "°C" ? 1 : 0)}${unit}`;
}

function getDominantDrivers(drivers, sign = "any", limit = 2) {
  return [...drivers]
    .filter((driver) => {
      if (sign === "positive") {
        return driver.value > 0;
      }
      if (sign === "negative") {
        return driver.value < 0;
      }
      return true;
    })
    .filter((driver) => Math.abs(driver.value) >= (driver.unit === "°C" ? 0.35 : 6))
    .sort((left, right) => Math.abs(right.value) - Math.abs(left.value))
    .slice(0, limit);
}

export function describeRegionalSetting({
  analysis,
  context,
  circulationPressureBand,
  circulationWindLabel,
  monthLabel,
}) {
  const coastText = analysis.profile.coastalness > 0.35
    ? "바다 영향이 큰 해안·연안 지대"
    : analysis.profile.interiorness > 0.45
      ? "바다에서 멀리 떨어진 내륙 지대"
      : "해양성과 대륙성이 함께 작용하는 전이 지대";
  const highlandText = analysis.highlandAssist
    ? ` 해발 ${analysis.highlandAssist.elevation.toFixed(0)} m라 기후그래프 해석에서는 ${analysis.highlandAssist.label}로 읽는 고산 냉각이 함께 나타납니다.`
    : analysis.profile.elevation > 250
      ? ` 해발 ${Math.round(analysis.profile.elevation)} m가 기본 온도대를 조금 낮춥니다.`
      : "";
  const reliefText = analysis.selectedMonth.orographicWet > analysis.selectedMonth.shadowDry + 6
    ? "산맥 바람받이 효과가 강수 공급을 돕습니다."
    : analysis.selectedMonth.shadowDry > 12
      ? "산맥 비그늘이 건조화를 키웁니다."
      : "산맥 장벽 효과는 이번 달에는 크지 않습니다.";
  return `${context.latitudeZone}에 있는 ${coastText}입니다.${highlandText} ${monthLabel}에는 ${circulationPressureBand}와 ${circulationWindLabel}이 기본 배경이며, ${reliefText}`;
}

export function describeKoppenClimateLink({
  analysis,
  isObservedMode,
  officialCode,
  graphCode,
  graphDisplayCode,
  details,
  metrics,
  graphCodeSource,
  comparisonNote,
}) {
  const effectiveHighlandAssist = analysis.highlandAssist?.label === graphCode ? analysis.highlandAssist : null;
  const highlandText = effectiveHighlandAssist
    ? ` 또한 해발 ${effectiveHighlandAssist.elevation.toFixed(0)} m의 고지대라, 평가원식 기후그래프 판정은 ${graphDisplayCode}로 읽습니다.`
    : "";
  const examText = comparisonNote?.examCode
    ? comparisonNote.examMismatch
      ? ` 평가원 기출 표기 ${comparisonNote.examCode}와는 차이가 있어 참고용으로만 둡니다.`
      : comparisonNote.examReferenceStatus === "compatible"
        ? ` 평가원 기출 표기 ${comparisonNote.examCode}와 계산값은 2차 구분까지 같습니다.`
      : ` 평가원 기출 표기 ${comparisonNote.examCode}와 계산값이 같습니다.`
    : "";
  const sourcePrefix = isObservedMode
    ? officialCode === graphCode
      ? `현재 공식 지도 코드는 ${officialCode}이며, 아래 임계값 해석은 같은 기간의 월별 기후자료를 평가형 기준(-3°C, 30 mm)으로 다시 읽은 기후그래프 설명입니다.${highlandText}${examText} `
      : `현재 공식 지도 코드는 ${officialCode}이고, 기후그래프 판정은 평가형 임계값(-3°C, 30 mm)과 고도 효과를 반영한 ${graphDisplayCode}입니다.${highlandText}${examText} `
    : "";
  const comparisonText = comparisonNote?.clue ? ` ${comparisonNote.clue}` : "";

  if (graphCode === "Ocean") {
    return `${sourcePrefix}이 위치는 공식 쾨펜 지도에서 해양/무자료 영역으로 처리됩니다. 기후 그래프는 육상 격자 기준 참고값만 읽습니다.`;
  }

  if (graphCode === "AH" || graphCode === "CH") {
    return `${sourcePrefix}${graphDisplayCode} ${details.label}은 해발 ${Math.round(analysis.profile.elevation)} m의 고지대라 같은 위도 저지대보다 기온이 낮아지는 고산형입니다. 월별 그래프에서는 연중 저온화와 짧은 온난기를 중심으로 읽습니다.${comparisonText}`;
  }

  if (graphCode.startsWith("A")) {
    const subtype = graphCode[1] === "f"
      ? `최건월 ${metrics.driest.toFixed(0)} mm로 60 mm 이상이라 연중 습윤성이 유지됩니다.`
      : graphCode[1] === "m"
        ? `최건월 ${metrics.driest.toFixed(0)} mm가 Af보다는 적지만 몬순 한계 ${metrics.monsoonThreshold.toFixed(0)} mm는 넘어서 몬순형으로 읽습니다.`
        : graphCode[1] === "w"
          ? "연중 고온이지만 겨울 건기가 뚜렷해 사바나형 강수 리듬이 나타납니다."
          : "연중 고온이지만 여름철 상대적 건조가 나타납니다.";
    return `${sourcePrefix}${graphDisplayCode} ${details.label}은 최한월 ${metrics.coldest.toFixed(1)}°C로 18°C 이상인 열대 기후입니다. ${subtype}${comparisonText}`;
  }

  if (graphCode.startsWith("B")) {
    const thermalText = graphCode[2] === "h"
      ? `연평균 ${metrics.annualTemp.toFixed(1)}°C로 고온 건조대 성격이 강합니다.`
      : graphCode[2] === "k"
        ? `연평균 ${metrics.annualTemp.toFixed(1)}°C로 냉량 건조대 성격이 붙습니다.`
        : `평가원식 그래프에서는 ${graphDisplayCode}처럼 건조대 묶음 코드로 우선 읽습니다.`;
    return `${sourcePrefix}${graphDisplayCode} ${details.label}은 연강수량 ${metrics.annualPrecip.toFixed(0)} mm가 건조 한계 ${metrics.drynessThreshold.toFixed(0)} mm보다 적어서 성립합니다. ${thermalText}${comparisonText}`;
  }

  if (graphCode.startsWith("E")) {
    const subtype = graphCode[1] === "F"
      ? "최난월도 0°C 미만이라 빙설 기후입니다."
      : "최난월이 0~10°C 사이여서 짧은 여름의 툰드라 기후입니다.";
    return `${sourcePrefix}${graphDisplayCode} ${details.label}은 최난월 ${metrics.warmest.toFixed(1)}°C가 10°C 미만이어서 한대 기후로 분류됩니다. ${subtype}${comparisonText}`;
  }

  const drySeasonText = graphCode[1] === "f"
    ? "뚜렷한 건기가 없고"
    : graphCode[1] === "w"
      ? "겨울 건기가 나타나고"
      : graphCode[1] === "s"
        ? "여름 건기가 나타나고"
        : "평가원식 묶음 코드로 계절 구분을 먼저 읽고";
  const summerText = graphCode[2] === "a"
    ? "가장 더운 달이 22°C 이상인 더운 여름형입니다."
    : graphCode[2] === "b"
      ? `10°C 이상 달이 ${metrics.warmMonths}개월이라 온난한 여름형입니다.`
      : graphCode[2] === "c"
        ? `10°C 이상 달이 ${metrics.warmMonths}개월로 적어 짧고 서늘한 여름형입니다.`
        : graphCode[2] === "d"
          ? "겨울 한파가 강한 하위형입니다."
          : "세부 여름형은 그래프 형태와 지역 맥락을 함께 봅니다.";
  return `${sourcePrefix}${graphDisplayCode} ${details.label}은 최한월 ${metrics.coldest.toFixed(1)}°C, 최난월 ${metrics.warmest.toFixed(1)}°C 조건을 만족하고 ${drySeasonText} ${summerText}${comparisonText}`;
}

export function describeMonthlyClimateFocus({
  analysis,
  breakdowns,
  graphCode,
  isObservedMode,
}) {
  const warmDrivers = getDominantDrivers(breakdowns.temperature, "positive", 2);
  const coolDrivers = getDominantDrivers(breakdowns.temperature, "negative", 1);
  const wetDrivers = getDominantDrivers(breakdowns.precipitation, "positive", 2);
  const dryDrivers = getDominantDrivers(breakdowns.precipitation, "negative", 2);

  const temperatureText = warmDrivers.length
    ? `기온은 ${warmDrivers.map((driver) => `${driver.label} ${formatSigned(driver.value, driver.unit)}`).join(", ")}의 영향이 큽니다.${coolDrivers[0] ? ` 반대로 ${coolDrivers[0].label} ${formatSigned(coolDrivers[0].value, coolDrivers[0].unit)}가 기온을 눌러 연교차를 만듭니다.` : ""}`
    : "이번 달 기온은 여러 요인이 비슷하게 섞여 있어 한 가지 요인으로 설명되기 어렵습니다.";
  const precipitationText = wetDrivers.length
    ? `강수는 ${wetDrivers.map((driver) => `${driver.label} ${formatSigned(driver.value, driver.unit)}`).join(", ")}이 비를 더합니다.${dryDrivers.length ? ` 반대로 ${dryDrivers.map((driver) => `${driver.label} ${formatSigned(driver.value, driver.unit)}`).join(", ")}이 건조화를 만듭니다.` : ""}`
    : "이번 달 강수는 기본 수분량보다 건조 요인이 상대적으로 우세합니다.";

  const codeLink = graphCode === "AH"
    ? "높은 해발 때문에 같은 위도 저지대보다 더 서늘하게 읽혀 저위도 고산형(AH) 판정으로 이어집니다."
    : graphCode === "CH"
      ? "높은 해발 때문에 같은 위도 저지대보다 더 서늘하게 읽혀 중위도 고산형(CH) 판정으로 이어집니다."
      : graphCode.startsWith("B")
        ? "이런 건조화 신호가 건조 기후 판정을 직접 밀어 줍니다."
        : graphCode.startsWith("A")
          ? "이런 고온·대류·계절 강수 리듬이 열대 기후의 우기/건기 차이를 만듭니다."
          : graphCode.startsWith("E")
            ? "낮은 태양고도와 한랭한 공기가 한대 기후 성격을 유지합니다."
            : "이런 기온 연교차와 계절 강수 구조가 온대·냉대 하위형을 가르는 핵심입니다.";
  const framing = isObservedMode
    ? "관측 월값을 직접 분해한 정답표가 아니라, 같은 달을 읽기 위한 설명 모델로 보면 "
    : "";

  return `${framing}${temperatureText} ${precipitationText} ${codeLink}`;
}
