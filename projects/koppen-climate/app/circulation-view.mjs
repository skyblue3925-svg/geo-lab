function formatBandLat(latitude) {
  return `${Math.abs(latitude).toFixed(1)}°${latitude >= 0 ? "N" : "S"}`;
}

function buildCompactFactPillsMarkup(rows) {
  return rows
    .map(([label, value]) => `<div class="fact-pill compact"><span>${label}</span><strong>${value}</strong></div>`)
    .join("");
}

export function buildCirculationSvgMarkup({
  width,
  height,
  stage,
  layout,
  jetLayout,
  selectedLatitude,
  tradeCrossEquatorThreshold,
}) {
  const toY = (latitude) => ((90 - latitude) / 180) * (height - 40) + 20;
  const showVertical = stage.id !== "surface";
  const showUpper = stage.id === "upper";
  const itczY = toY(layout.itcz);
  const polarBandLabel = stage.id === "surface" ? "표층 바람대 / 극동풍" : "극고압대 / 극동풍";
  const ferrelBandLabel = stage.id === "surface" ? "표층 바람대 / 편서풍" : "아극 저압대 / 편서풍";
  const northHadleyLabel = layout.itcz < -tradeCrossEquatorThreshold
    ? `${stage.id === "surface" ? "표층 바람대" : "아열대 고압대"} / 북동 무역풍·북서 기류`
    : `${stage.id === "surface" ? "표층 바람대" : "아열대 고압대"} / 북동 무역풍`;
  const southHadleyLabel = layout.itcz > tradeCrossEquatorThreshold
    ? `${stage.id === "surface" ? "표층 바람대" : "아열대 고압대"} / 남동 무역풍·남서 기류`
    : `${stage.id === "surface" ? "표층 바람대" : "아열대 고압대"} / 남동 무역풍`;
  const bandDefs = [
    { top: 90, bottom: layout.northSubpolar, label: polarBandLabel, color: "rgba(154, 194, 219, 0.22)" },
    { top: layout.northSubpolar, bottom: layout.northSubtropical, label: ferrelBandLabel, color: "rgba(99, 169, 211, 0.24)" },
    { top: layout.northSubtropical, bottom: layout.itcz, label: northHadleyLabel, color: "rgba(241, 184, 83, 0.18)" },
    { top: layout.itcz, bottom: layout.southSubtropical, label: southHadleyLabel, color: "rgba(241, 184, 83, 0.18)" },
    { top: layout.southSubtropical, bottom: layout.southSubpolar, label: ferrelBandLabel, color: "rgba(99, 169, 211, 0.24)" },
    { top: layout.southSubpolar, bottom: -90, label: polarBandLabel, color: "rgba(154, 194, 219, 0.22)" },
  ];
  const pressureLines = [
    { lat: layout.northSubpolar, color: "rgba(126, 203, 242, 0.45)" },
    { lat: layout.northSubtropical, color: "rgba(255, 204, 120, 0.45)" },
    { lat: layout.southSubtropical, color: "rgba(255, 204, 120, 0.45)" },
    { lat: layout.southSubpolar, color: "rgba(126, 203, 242, 0.45)" },
  ]
    .map((line) => {
      const y = toY(line.lat);
      return `<line x1="52" y1="${y}" x2="308" y2="${y}" stroke="${line.color}" stroke-width="1.3" stroke-dasharray="6 7" />`;
    })
    .join("");
  const jetLines = [
    { lat: jetLayout.northPolarJet, color: "rgba(219, 236, 245, 0.9)", label: "한대전선 제트", anchor: "end", x: 314 },
    { lat: jetLayout.northSubtropicalJet, color: "rgba(255, 235, 171, 0.94)", label: "아열대 제트", anchor: "end", x: 314 },
    { lat: jetLayout.southSubtropicalJet, color: "rgba(255, 235, 171, 0.94)", label: "아열대 제트", anchor: "start", x: 46 },
    { lat: jetLayout.southPolarJet, color: "rgba(219, 236, 245, 0.9)", label: "한대전선 제트", anchor: "start", x: 46 },
  ]
    .map((jet) => {
      const y = toY(jet.lat);
      return `
        <line x1="52" y1="${y}" x2="308" y2="${y}" stroke="${jet.color}" stroke-width="2" stroke-dasharray="10 7" />
        <text x="${jet.x}" y="${y + 4}" text-anchor="${jet.anchor}" font-size="11" font-weight="700" fill="${jet.color}">${jet.label}</text>
      `;
    })
    .join("");
  const verticalMotion = [
    { lat: layout.northSubpolar, label: "상승", direction: "up", x: 74, color: "rgba(199, 232, 246, 0.92)" },
    { lat: layout.northSubtropical, label: "하강", direction: "down", x: 286, color: "rgba(255, 220, 157, 0.92)" },
    { lat: layout.itcz, label: "상승", direction: "up", x: 180, color: "rgba(255, 217, 123, 0.96)" },
    { lat: layout.southSubtropical, label: "하강", direction: "down", x: 74, color: "rgba(255, 220, 157, 0.92)" },
    { lat: layout.southSubpolar, label: "상승", direction: "up", x: 286, color: "rgba(199, 232, 246, 0.92)" },
  ]
    .map((motion) => {
      const y = toY(motion.lat);
      const startY = motion.direction === "up" ? y + 14 : y - 14;
      const endY = motion.direction === "up" ? y - 14 : y + 14;
      const arrowHead = motion.direction === "up"
        ? `${motion.x - 4},${endY + 7} ${motion.x + 4},${endY + 7} ${motion.x},${endY}`
        : `${motion.x - 4},${endY - 7} ${motion.x + 4},${endY - 7} ${motion.x},${endY}`;
      const labelY = motion.direction === "up" ? y - 20 : y + 26;
      return `
        <line x1="${motion.x}" y1="${startY}" x2="${motion.x}" y2="${endY}" stroke="${motion.color}" stroke-width="2.2" />
        <polygon points="${arrowHead}" fill="${motion.color}" />
        <text x="${motion.x}" y="${labelY}" text-anchor="middle" font-size="11" font-weight="700" fill="${motion.color}">${motion.label}</text>
      `;
    })
    .join("");

  const bands = bandDefs
    .map((band) => {
      const y = toY(band.top);
      const nextY = toY(band.bottom);
      const radius = Math.max(6, Math.min(18, (nextY - y) / 2 - 1));
      return `
        <rect x="52" y="${y}" width="256" height="${nextY - y}" rx="${radius.toFixed(1)}" fill="${band.color}" />
        <text x="180" y="${y + (nextY - y) / 2 + 4}" class="band-label" text-anchor="middle">${band.label}</text>
      `;
    })
    .join("");

  const latitudeTicks = [60, 30, 0, -30, -60]
    .map((latitude) => {
      const y = toY(latitude);
      return `
        <line x1="36" y1="${y}" x2="320" y2="${y}" class="grid-line" />
        <text x="22" y="${y + 4}" class="axis-label" text-anchor="end">${latitude}°</text>
      `;
    })
    .join("");

  return `
    <svg viewBox="0 0 ${width} ${height}" role="img" aria-label="위도대별 대기대순환 도식">
      ${bands}
      ${latitudeTicks}
      ${pressureLines}
      ${showUpper ? jetLines : ""}
      ${showVertical ? verticalMotion : ""}
      <line x1="52" y1="${itczY}" x2="308" y2="${itczY}" class="itcz-line" />
      <text x="314" y="${itczY + 4}" class="itcz-label">ITCZ</text>
      <line x1="52" y1="${toY(selectedLatitude)}" x2="308" y2="${toY(selectedLatitude)}" class="probe-line" />
      <circle cx="180" cy="${toY(selectedLatitude)}" r="6" class="probe-dot" />
    </svg>
  `;
}

export function buildCirculationFactsMarkup({
  stageLabel,
  layout,
  jetLayout,
  showUpper,
  pressureBand,
  wind,
  jetPresence,
  geostrophicContext,
  tilt,
}) {
  const factRows = [
    ["현재 보기", stageLabel],
    ["선택 달 ITCZ", formatBandLat(layout.itcz)],
    ["아열대 고압대", `${formatBandLat(layout.northSubtropical)} / ${formatBandLat(layout.southSubtropical)}`],
    ["아극 저압대", `${formatBandLat(layout.northSubpolar)} / ${formatBandLat(layout.southSubpolar)}`],
    ["선택 위치 기압대", pressureBand],
    ["선택 위치 바람", `${wind.label} · ${wind.shortArrow}`],
    ["자전축 기울기", `${tilt.toFixed(1)}°`],
  ];
  if (showUpper) {
    factRows.splice(4, 0,
      ["아열대 제트", `${formatBandLat(jetLayout.northSubtropicalJet)} / ${formatBandLat(jetLayout.southSubtropicalJet)}`],
      ["한대전선 제트", `${formatBandLat(jetLayout.northPolarJet)} / ${formatBandLat(jetLayout.southPolarJet)}`],
    );
    factRows.splice(factRows.length - 1, 0,
      ["선택 위치 제트", jetPresence],
      ["지균풍 해석", geostrophicContext],
    );
  }
  return buildCompactFactPillsMarkup(factRows);
}
