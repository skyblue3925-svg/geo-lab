function buildLegendChipsMarkup(rows) {
  return rows
    .map(([code, color, label]) => `<span class="legend-chip"><span class="legend-dot" style="background:${color}"></span>${code} ${label}</span>`)
    .join("");
}

export function buildLegendMarkup({
  overlay,
  observedMode,
  koppenColors,
  circulationStage,
  activeClimateDataset,
}) {
  if (overlay === "koppen") {
    return buildLegendChipsMarkup([
      ["A", koppenColors.Am, "열대"],
      ["B", koppenColors.BWh, "건조"],
      ["C", koppenColors.Cfb, "온대"],
      ["D", koppenColors.Dfb, "냉대"],
      ["E", koppenColors.ET, "한대"],
    ]) + `<p class="legend-note">${observedMode ? "공식 Beck 2026 v2 1991-2020 쾨펜 지도입니다. 바다는 해양/무자료 영역으로 처리합니다." : "실험 모드에서 현재 레버 조건으로 다시 계산한 쾨펜 지도입니다."}</p>`;
  }

  if (overlay === "circulation") {
    return buildLegendChipsMarkup([
      ["Hadley", "#f1b853", "무역풍 · 아열대 고압대"],
      ["Ferrel", "#63a9d3", "편서풍 · 아극 저압대"],
      ["Polar", "#9ac2db", "극동풍 · 극고압대"],
      ["Jet", "#f7e39f", "상층 제트 · 지균풍 접근"],
    ]) + `<p class="legend-note">현재 단계: ${circulationStage.label}. ${circulationStage.note}</p>`;
  }

  const gradient = overlay === "temperature"
    ? "linear-gradient(90deg, #12304a 0%, #4d8fc4 28%, #eff5f8 50%, #f2bf61 70%, #b33c26 100%)"
    : "linear-gradient(90deg, #7b5438 0%, #c48a5a 25%, #dfc78b 45%, #7cc9cc 70%, #0e5f77 100%)";
  const labels = overlay === "temperature" ? ["-35°C", "0°C", "35°C"] : ["0 mm", "150 mm", "300+ mm"];

  return `
    <div class="legend-bar" style="background:${gradient}"></div>
    <div class="legend-scale"><span>${labels[0]}</span><span>${labels[1]}</span><span>${labels[2]}</span></div>
    <p class="legend-note">${observedMode ? `${activeClimateDataset.dataset} ${activeClimateDataset.period} ${activeClimateDataset.resolution} 월별 관측값입니다.` : "실험 모드에서 현재 레버 조건으로 다시 계산한 월별 값입니다."}</p>
  `;
}
