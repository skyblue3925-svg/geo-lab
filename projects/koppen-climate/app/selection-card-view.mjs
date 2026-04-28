export function buildSelectionKoppenMarkup({
  officialCode,
  graphCode,
  graphDisplayCode,
  details,
  graphDetails,
  comparisonNote,
  observedMode,
  graphDiffers,
  activeExamSpot,
  koppenColors,
}) {
  const basisNote = observedMode
    ? activeExamSpot
      ? "공식 지도 코드는 Beck 기준이고, 앱 계산값을 기후그래프 판정의 우선 기준으로 씁니다. 평가원 기출 코드는 비교용 참고값이며, 다르면 주의 표시를 붙입니다. C·D 경계는 최한월 -3°C를 씁니다."
      : "공식 지도 코드는 Beck 기준이고, 기후그래프 판정과 문자 해설의 C·D 경계는 최한월 -3°C로 읽습니다. 두 결과는 서로 다를 수 있습니다."
    : "";
  return `
    <div class="koppen-badge-stack">
      <span class="koppen-badge" style="background:${koppenColors[officialCode] ?? "#5e7483"}">${officialCode}</span>
      ${graphDiffers ? `<span class="koppen-badge koppen-badge-secondary" style="background:${koppenColors[graphCode] ?? "#9b8c54"}">${graphDisplayCode}</span>` : ""}
    </div>
    <div>
      <strong>${graphDiffers ? `공식 ${officialCode} · 기후그래프 ${graphDisplayCode}` : `${details.group} ${details.label}`}</strong>
      <p>${graphDiffers ? `공식 지도는 ${details.label}이지만, 기후그래프 판정은 ${graphDetails.label}으로 읽습니다.${comparisonNote?.summary ? ` ${comparisonNote.summary}` : ""}` : `${details.summary}${comparisonNote?.summary ? ` ${comparisonNote.summary}` : ""}`}</p>
      <div class="inline-chips">
        <span class="mini-chip">공식 Beck 코드 ${officialCode}</span>
        ${observedMode ? `<span class="mini-chip">기후그래프 ${graphDisplayCode}</span>` : ""}
        ${activeExamSpot ? `<span class="mini-chip">평가원 기출 코드 ${activeExamSpot.examCode}</span>` : ""}
        ${comparisonNote?.examMismatch ? `<span class="mini-chip mini-chip-warning">주의: 기출 코드와 불일치</span>` : ""}
      </div>
      ${basisNote ? `<p class="selection-basis-note">${basisNote}</p>` : ""}
    </div>
  `;
}

export function buildSelectionSummaryText({
  isObservedOceanCell,
  climateResolution,
  observedMode,
  graphDiffers,
  officialCode,
  graphDisplayCode,
  comparisonNote,
  activeClimateDataset,
  monthLabel,
  circulationPressureBand,
  circulationWindLabel,
  highlandSummary,
  examSpotSummary,
  experimentalClassificationCode,
}) {
  if (isObservedOceanCell) {
    return `선택 위치는 해양 셀입니다. 공식 Beck 쾨펜 지도에서도 해양/무자료 영역이며, 월별 차트는 육상 ${climateResolution} 월별 기후자료만 제공합니다.`;
  }
  if (observedMode) {
    return `${graphDiffers ? `공식 지도 코드는 ${officialCode}이지만 기후그래프 판정은 ${graphDisplayCode}로 읽습니다. ` : `지도 코드와 기후그래프 판정은 모두 ${officialCode}입니다. `}${comparisonNote?.summary ? `${comparisonNote.summary} ` : ""}기후그래프 해석은 ${activeClimateDataset.dataset} ${activeClimateDataset.period} 월별 수치와 평가원식 임계값을 함께 기준으로 읽습니다. ${monthLabel}에는 ${circulationPressureBand}와 ${circulationWindLabel}의 배경을 함께 봅니다.${highlandSummary}${comparisonNote?.clue ? ` 단서: ${comparisonNote.clue}` : ""}${examSpotSummary}`;
  }
  return `${monthLabel} 기준 현재 레버 조건에서 ${circulationPressureBand}와 ${circulationWindLabel}의 영향을 받아 ${experimentalClassificationCode} 기후로 계산됩니다.${examSpotSummary}`;
}

export function buildSelectionContextMarkup({
  observedMode,
  context,
  officialCode,
  elevation,
  graphDisplayCode,
  activeExamSpot,
  comparisonNote,
}) {
  return `
    <div class="context-title">
      <strong>${context.subtitle}</strong>
      <span>${context.macroRegion}</span>
    </div>
    <div class="inline-chips">
      <span class="mini-chip">${observedMode ? "관측 모드" : "실험 모드"}</span>
      <span class="mini-chip">${context.latitudeZone}</span>
      <span class="mini-chip">${context.surfaceContext}</span>
      <span class="mini-chip">공식 코드 ${officialCode}</span>
      ${elevation > 50 ? `<span class="mini-chip">해발 ${Math.round(elevation)} m</span>` : ""}
      ${observedMode ? `<span class="mini-chip">기후그래프 ${graphDisplayCode}</span>` : ""}
      ${activeExamSpot ? `<span class="mini-chip">평가원 ${activeExamSpot.examCount}회 기출</span>` : ""}
      ${comparisonNote?.examMismatch ? `<span class="mini-chip mini-chip-warning">기출 코드 재검토 필요</span>` : ""}
    </div>
    <p>${context.note}</p>
  `;
}

export function buildKoppenBreakdownMarkup(letterRows) {
  return letterRows
    .map((item) => `
      <article class="letter-chip">
        <span class="letter-symbol">${item.letter}</span>
        <strong>${item.label}</strong>
        <p>${item.detail}</p>
      </article>
    `)
    .join("");
}

export function buildAnnualFactRows({
  analysis,
  observedMode,
  officialCode,
  graphDisplayCode,
  highlandAssist,
  activeExamSpot,
  comparisonNote,
}) {
  return [
    ["연평균 기온", `${analysis.annual.meanTemp.toFixed(1)}°C`],
    ["연강수량", `${analysis.annual.annualPrecip.toFixed(0)} mm`],
    ["가장 더운 달", `${analysis.annual.warmestTemp.toFixed(1)}°C`],
    ["가장 추운 달", `${analysis.annual.coldestTemp.toFixed(1)}°C`],
    ["해발고도", `${Math.round(analysis.profile.elevation)} m`],
    [observedMode ? "공식 Beck 코드" : "계산 코드", officialCode],
    ...(observedMode ? [["기후그래프 판정", `${graphDisplayCode}${highlandAssist ? ` (${highlandAssist.strength})` : ""}`]] : []),
    ...(activeExamSpot ? [["평가원 기출 코드", activeExamSpot.examCode]] : []),
    ...(activeExamSpot && comparisonNote?.examMismatch ? [["기출-계산 비교", `주의: 기출 ${activeExamSpot.examCode} / 계산 ${graphDisplayCode}`]] : []),
  ];
}

export function buildAnnualFactsMarkup({ isObservedOceanCell, climateResolution, rows }) {
  if (isObservedOceanCell) {
    return `<div class="fact-pill"><span>자료 범위</span><strong>육상 ${climateResolution} 월평균 기후 자료만 제공</strong></div>`;
  }
  return rows
    .map(([label, value]) => `<div class="fact-pill"><span>${label}</span><strong>${value}</strong></div>`)
    .join("");
}

export function buildMonthlyFactorRows({
  analysis,
  observedMode,
  graphDisplayCode,
  highlandAssist,
  activeExamSpot,
  circulationPressureBand,
  circulationWind,
  showUpperCirculation,
  jetPresence,
  geostrophicContext,
}) {
  const factorRows = [
    ["기압대", circulationPressureBand],
    ["바람", `${circulationWind.label} (${circulationWind.shortArrow})`],
    ["해발고도", `${Math.round(analysis.profile.elevation)} m`],
    ...(observedMode ? [["기후그래프 판정", `${graphDisplayCode}${highlandAssist ? ` (${highlandAssist.strength})` : ""}`]] : []),
    ...(activeExamSpot ? [["평가원 기출 코드", activeExamSpot.examCode]] : []),
    ["바다 영향", analysis.profile.coastalness > 0.35 ? "강함" : analysis.profile.coastalness > 0.15 ? "보통" : "약함"],
    ["대륙 내부", analysis.profile.interiorness > 0.45 ? "강함" : analysis.profile.interiorness > 0.2 ? "보통" : "약함"],
    ["산맥 효과", analysis.selectedMonth.orographicWet > analysis.selectedMonth.shadowDry ? "바람받이 우세" : analysis.selectedMonth.shadowDry > 10 ? "비그늘 우세" : "약함"],
    ["푄", analysis.selectedMonth.foehnWarm > 1.2 ? `+${analysis.selectedMonth.foehnWarm.toFixed(1)}°C` : "거의 없음"],
  ];
  if (showUpperCirculation) {
    factorRows.splice(2, 0, ["상층 제트", jetPresence], ["지균풍", geostrophicContext]);
  }
  return factorRows;
}

export function buildMonthlyFactorsMarkup(factorRows) {
  return factorRows
    .map(([label, value]) => `<div class="factor-chip"><span>${label}</span><strong>${value}</strong></div>`)
    .join("");
}

export function buildRuleTraceMarkup(traceRows) {
  return traceRows
    .map((row) => `
      <div class="trace-card ${row.state}">
        <span>${row.label}</span>
        <strong>${row.value}</strong>
        <p>${row.detail}</p>
      </div>
    `)
    .join("");
}

export function buildReasonListMarkup(reasons) {
  return reasons.map((reason) => `<li>${reason}</li>`).join("");
}
