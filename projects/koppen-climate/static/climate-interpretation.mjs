function sum(values) {
  return values.reduce((total, value) => total + value, 0);
}

function average(values) {
  return values.length ? sum(values) / values.length : 0;
}

function getReferenceClassification(analysis) {
  return analysis.referenceClassification ?? analysis.classification;
}

function classifyEvaluationClimate(analysis) {
  const temperatures = analysis.temperatures ?? [];
  const precipitations = analysis.precipitations ?? [];
  const latitude = Number(analysis.latitude ?? analysis.profile?.latitude ?? 0);
  const landness = Number(analysis.profile?.landness ?? 1);

  if (landness < 0.42) {
    return { code: "Ocean" };
  }

  const metrics = getClassificationMetrics({
    ...analysis,
    temperatures,
    precipitations,
    latitude,
  });

  if (metrics.warmest < 10) {
    return { code: metrics.warmest < 0 ? "EF" : "ET" };
  }

  if (metrics.annualPrecip < metrics.drynessThreshold) {
    const moistureCode = metrics.annualPrecip < metrics.drynessThreshold / 2 ? "BW" : "BS";
    const thermalCode = metrics.annualTemp >= 18 ? "h" : "k";
    return { code: `${moistureCode}${thermalCode}` };
  }

  if (metrics.coldest >= 18) {
    if (metrics.driest >= 60) {
      return { code: "Af" };
    }
    if (metrics.driest >= metrics.monsoonThreshold) {
      return { code: "Am" };
    }
    const summerIndices = latitude >= 0 ? [3, 4, 5, 6, 7, 8] : [9, 10, 11, 0, 1, 2];
    const winterIndices = Array.from({ length: 12 }, (_, index) => index).filter((index) => !summerIndices.includes(index));
    const summerPrecip = sum(summerIndices.map((index) => precipitations[index]));
    const winterPrecip = sum(winterIndices.map((index) => precipitations[index]));
    return { code: summerPrecip < winterPrecip ? "As" : "Aw" };
  }

  const mainCode = metrics.coldest > -3 ? "C" : "D";
  let seasonalCode = "f";
  if (metrics.driestSummer < 30 && metrics.driestSummer < metrics.wettestWinter / 3) {
    seasonalCode = "s";
  } else if (metrics.driestWinter < metrics.wettestSummer / 10) {
    seasonalCode = "w";
  }

  let thermalCode = "c";
  if (mainCode === "D" && metrics.coldest < -38) {
    thermalCode = "d";
  } else if (metrics.warmest >= 22 && metrics.warmMonths >= 4) {
    thermalCode = "a";
  } else if (metrics.warmMonths >= 4) {
    thermalCode = "b";
  }

  return { code: `${mainCode}${seasonalCode}${thermalCode}` };
}

export function normalizeClimateCode(code) {
  const normalized = String(code ?? "")
    .trim()
    .replace(/\s+/g, "")
    .replace(/\(H\)/gi, "");
  return normalized || null;
}

export function getExamClimateReference(activeExamSpot) {
  if (!activeExamSpot?.examCode) {
    return null;
  }
  const normalized = normalizeClimateCode(activeExamSpot.examCode);
  if (!normalized) {
    return null;
  }
  return {
    raw: activeExamSpot.examCode.trim(),
    normalized,
    spot: activeExamSpot,
  };
}

export function getGraphClimateCodeSource(analysis, activeExamSpot) {
  return analysis.highlandAssist?.label ? "highland" : "evaluation";
}

export function getGraphClimateCode(analysis, activeExamSpot) {
  return analysis.highlandAssist?.label
    ?? classifyEvaluationClimate(analysis).code
    ?? getReferenceClassification(analysis).code;
}

export function getGraphClimateDisplayCode(analysis, activeExamSpot) {
  return getGraphClimateCode(analysis, activeExamSpot);
}

function getExamReferenceStatus(calculatedCode, examCode) {
  const calculated = normalizeClimateCode(calculatedCode);
  const exam = normalizeClimateCode(examCode);
  if (!calculated || !exam) {
    return "none";
  }
  if (calculated === exam) {
    return "exact";
  }
  if (calculated[0] === exam[0] && calculated[1] === exam[1]) {
    return "compatible";
  }
  return "mismatch";
}

function getClimateTierDifferenceLabel(leftCode, rightCode) {
  const left = normalizeClimateCode(leftCode);
  const right = normalizeClimateCode(rightCode);
  if (!left || !right || left === right) {
    return null;
  }
  if (left === "AH" || left === "CH" || right === "AH" || right === "CH") {
    return "고산 보조 판정";
  }
  if (left[0] !== right[0]) {
    return "대분류";
  }
  if (left[1] && right[1] && left[1] !== right[1]) {
    return "2차 구분";
  }
  if (left[2] && right[2] && left[2] !== right[2]) {
    return "3차 구분";
  }
  if (left.length !== right.length) {
    return "세부 구분";
  }
  return "세부 구분";
}

function getClimateFamilyLabel(code) {
  const normalized = normalizeClimateCode(code);
  if (!normalized) {
    return null;
  }
  if (normalized === "AH" || normalized === "CH") {
    return "고산형";
  }
  return `${normalized[0]}기후`;
}

export function getClassificationMetrics(analysis) {
  const temperatures = analysis.temperatures;
  const precipitations = analysis.precipitations;
  const annualTemp = average(temperatures);
  const annualPrecip = sum(precipitations);
  const warmest = Math.max(...temperatures);
  const coldest = Math.min(...temperatures);
  const driest = Math.min(...precipitations);
  const warmMonths = temperatures.filter((value) => value >= 10).length;
  const summerIndices = analysis.latitude >= 0 ? [3, 4, 5, 6, 7, 8] : [9, 10, 11, 0, 1, 2];
  const winterIndices = Array.from({ length: 12 }, (_, index) => index).filter((index) => !summerIndices.includes(index));
  const summerPrecip = sum(summerIndices.map((index) => precipitations[index]));
  const driestSummer = Math.min(...summerIndices.map((index) => precipitations[index]));
  const wettestSummer = Math.max(...summerIndices.map((index) => precipitations[index]));
  const driestWinter = Math.min(...winterIndices.map((index) => precipitations[index]));
  const wettestWinter = Math.max(...winterIndices.map((index) => precipitations[index]));
  const summerRatio = annualPrecip > 0 ? summerPrecip / annualPrecip : 0;
  const drynessOffset = summerRatio >= 0.7 ? 280 : summerRatio >= 0.3 ? 140 : 0;
  const drynessThreshold = Math.max(0, 20 * annualTemp + drynessOffset);
  const monsoonThreshold = 100 - annualPrecip / 25;

  return {
    annualTemp,
    annualPrecip,
    warmest,
    coldest,
    driest,
    warmMonths,
    driestSummer,
    wettestSummer,
    driestWinter,
    wettestWinter,
    summerRatio,
    drynessOffset,
    drynessThreshold,
    monsoonThreshold,
  };
}

function getClimateDifferenceClue(officialCode, graphCode, displayCode, analysis, graphCodeSource) {
  const official = normalizeClimateCode(officialCode);
  const graph = normalizeClimateCode(graphCode);
  if (!official || !graph || official === graph) {
    return null;
  }
  const metrics = getClassificationMetrics(analysis);
  const tierLabel = getClimateTierDifferenceLabel(official, graph);
  if (graph === "AH" || graph === "CH") {
    return `해발 ${Math.round(analysis.profile.elevation)} m의 고도 효과가 커서 지도 코드와 별도로 ${displayCode} 고산형으로 읽습니다.`;
  }
  if (graph.startsWith("A")) {
    return `A기후 내부는 최건월 ${metrics.driest.toFixed(0)} mm와 몬순 한계 ${metrics.monsoonThreshold.toFixed(0)} mm, 우기 집중도를 함께 봅니다. 제시된 그래프에선 ${displayCode}처럼 읽을 수 있습니다.`;
  }
  if (graph.startsWith("B")) {
    return `B기후는 연강수량 ${metrics.annualPrecip.toFixed(0)} mm와 건조 한계 ${metrics.drynessThreshold.toFixed(0)} mm를 먼저 보고, 필요하면 사막/스텝과 h·k를 더 읽습니다.`;
  }
  if (graph.startsWith("C") || graph.startsWith("D")) {
    if ((official === "C" || official === "D" || official.startsWith("C") || official.startsWith("D"))
      && (graph === "C" || graph === "D" || graph.startsWith("C") || graph.startsWith("D"))
      && official[0] !== graph[0]) {
      return `공식 지도는 C·D 경계를 0°C로 보지만, 기후그래프 판정은 최한월 -3°C 경계를 더 중시해 ${displayCode}로 읽을 수 있습니다.`;
    }
    if ((official[1] === "s" || graph[1] === "s") && official[1] !== graph[1]) {
      return `여름 건기 판정은 여름 최건월 30 mm 미만과 겨울 최다우월의 1/3 미만을 함께 보므로, 그래프에서는 ${displayCode}처럼 읽힐 수 있습니다.`;
    }
    if (tierLabel === "2차 구분") {
      return `C·D기후의 2차 구분은 건기 위치(f·w·s)를 보는 단계입니다. 제시된 그래프에서는 건기 시점 단서를 더 우선해 ${displayCode}로 읽을 수 있습니다.`;
    }
    if (tierLabel === "3차 구분" || tierLabel === "세부 구분") {
      return `C·D기후의 3차 구분은 최난월 ${metrics.warmest.toFixed(1)}°C와 10°C 이상 달 수 ${metrics.warmMonths}개월을 함께 보는 단계입니다. 그래프 단서가 단순하면 ${displayCode}처럼 묶어 읽기도 합니다.`;
    }
  }
  if (graph.startsWith("E")) {
    return `E기후는 최난월 ${metrics.warmest.toFixed(1)}°C가 핵심 단서입니다. 0°C 경계면 EF·ET, 10°C 경계면 한대 여부가 갈립니다.`;
  }
  if (graphCodeSource === "evaluation") {
    return "기후그래프 판정은 평가형 임계값을 따릅니다. C·D 경계는 최한월 -3°C, Cs·Ds의 여름 건기 기준은 여름 최건월 30 mm 미만으로 읽습니다.";
  }
  return null;
}

export function getClimateComparisonNote(analysis, activeExamSpot, isObservedMode) {
  if (!isObservedMode) {
    return null;
  }
  const officialCode = analysis.classification.code;
  const graphCode = getGraphClimateCode(analysis, activeExamSpot);
  const displayCode = getGraphClimateDisplayCode(analysis, activeExamSpot);
  const graphCodeSource = getGraphClimateCodeSource(analysis, activeExamSpot);
  const examReference = getExamClimateReference(activeExamSpot);
  const examReferenceStatus = getExamReferenceStatus(graphCode, examReference?.normalized);
  const examMismatch = examReferenceStatus === "mismatch";
  const tierLabel = getClimateTierDifferenceLabel(officialCode, graphCode);
  const familyLabel = getClimateFamilyLabel(officialCode) ?? "같은 기후대";
  const clue = getClimateDifferenceClue(officialCode, graphCode, displayCode, analysis, graphCodeSource);
  let summary = null;

  if (tierLabel === "2차 구분" || tierLabel === "3차 구분" || tierLabel === "세부 구분") {
    summary = `공식 지도 ${officialCode}와 기후그래프 판정 ${displayCode}는 ${familyLabel} 내부의 ${tierLabel}에서 차이가 납니다.`;
  } else if (tierLabel === "고산 보조 판정") {
    summary = `공식 지도 ${officialCode}에 고도 효과를 함께 읽어 ${displayCode} 고산 보조 판정을 붙였습니다.`;
  } else if (officialCode !== graphCode) {
    summary = `공식 지도 ${officialCode}와 기후그래프 판정 ${displayCode}는 자료 기준이 달라 다르게 읽힐 수 있습니다.`;
  }

  const summaryParts = summary ? [summary] : [];
  if (examReference) {
    summaryParts.push(
      examReferenceStatus === "mismatch"
        ? `평가원 기출 표기는 ${examReference.raw}이지만, 앱 계산값은 ${displayCode}입니다.`
        : examReferenceStatus === "compatible"
          ? `평가원 기출 표기 ${examReference.raw}와 계산값 ${displayCode}는 2차 구분까지 같습니다.`
          : `평가원 기출도 ${examReference.raw}로 계산값과 같습니다.`,
    );
  }

  const clueParts = clue ? [clue] : [];
  if (examMismatch) {
    clueParts.push("기출 코드는 참고값으로만 두고, 현재 앱에서는 월별 기후자료와 평가형 임계값(-3°C, 30 mm)으로 다시 계산한 결과를 우선합니다.");
  }

  summary = summaryParts.join(" ").trim() || null;
  const combinedClue = clueParts.join(" ").trim() || null;

  if (!summary && !combinedClue) {
    return null;
  }

  return {
    summary,
    clue: combinedClue,
    examCode: examReference?.raw ?? null,
    examReferenceCode: examReference?.normalized ?? null,
    examReferenceStatus,
    examMismatch,
    tierLabel,
  };
}
