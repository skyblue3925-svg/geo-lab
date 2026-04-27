function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function buildChartTheme(theme) {
  if (theme === "print") {
    return {
      background: "#ffffff",
      axisLabel: "#111111",
      axisTitle: "#111111",
      axisLine: "rgba(17, 17, 17, 0.78)",
      gridLine: "rgba(17, 17, 17, 0.18)",
      tempLine: "#111111",
      pointFill: "#ffffff",
      pointStroke: "#111111",
      barFill: "#ffffff",
      barStroke: "#111111",
      barStrokeWidth: 1.5,
      interactive: false,
      highlightMonth: false,
      showGradient: false,
    };
  }

  return {
    background: "transparent",
    axisLabel: "rgba(247, 241, 230, 0.78)",
    axisTitle: "rgba(247, 241, 230, 0.86)",
    axisLine: "rgba(247, 241, 230, 0.18)",
    gridLine: "rgba(247, 241, 230, 0.18)",
    tempLine: "url(#tempLineGradient)",
    pointFill: "#fff3d6",
    pointStroke: "#f16b45",
    barFill: null,
    barStroke: null,
    barStrokeWidth: 0,
    interactive: true,
    highlightMonth: true,
    showGradient: true,
  };
}

function getActivePoint(chartPoints, selectedMonth) {
  return chartPoints.find((point) => point.monthIndex + 1 === selectedMonth) ?? chartPoints[0];
}

function buildClimateChartSvgInternal({
  analysis,
  selectedMonth,
  monthLabels,
  observedOceanCell,
  climateResolution,
  theme = "screen",
  width = 560,
  height = 264,
  interactive = true,
  chartTitle = "",
}) {
  const palette = buildChartTheme(theme);
  const resolvedInteractive = palette.interactive && interactive;
  const titleHeight = chartTitle ? 24 : 0;

  if (observedOceanCell) {
    return `
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" role="img" aria-label="월별 기후 그래프">
        <rect x="0" y="0" width="${width}" height="${height}" fill="${palette.background}" />
        <text x="${width / 2}" y="${height / 2 - 12}" text-anchor="middle" fill="${palette.axisTitle}" font-size="18" font-weight="700">해양 셀</text>
        <text x="${width / 2}" y="${height / 2 + 18}" text-anchor="middle" fill="${palette.axisLabel}" font-size="12">
          현재 월별 기후자료는 육상 ${escapeHtml(climateResolution)} 격자를 사용해 바다는 안내만 제공합니다.
        </text>
      </svg>
    `;
  }

  const margin = { top: 24 + titleHeight, right: 44, bottom: 34, left: 38 };
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;
  const minTemp = -30;
  const maxTemp = 40;
  const maxPrecip = 500;
  const xStep = innerWidth / 12;
  const tempToY = (value) => {
    const normalized = clamp((value - minTemp) / Math.max(maxTemp - minTemp, 1), 0, 1);
    return margin.top + innerHeight - normalized * innerHeight;
  };
  const precipToY = (value) => {
    const normalized = clamp(value / Math.max(maxPrecip, 1), 0, 1);
    return margin.top + innerHeight - normalized * innerHeight;
  };
  const tempTicks = Array.from({ length: 8 }, (_, index) => {
    const value = minTemp + index * 10;
    return { value, y: tempToY(value) };
  });
  const precipTicks = Array.from({ length: 6 }, (_, index) => {
    const value = index * 100;
    return { value, y: precipToY(value) };
  });

  const chartPoints = analysis.temperatures.map((value, index) => {
    const x = margin.left + index * xStep + xStep / 2;
    return {
      x,
      y: tempToY(value),
      temperature: value,
      precipitation: analysis.precipitations[index],
      monthIndex: index,
    };
  });

  const bars = chartPoints.map((point) => {
    const x = point.x - (xStep - 16) / 2;
    const y = precipToY(point.precipitation);
    const barHeight = margin.top + innerHeight - y;
    const isActive = point.monthIndex + 1 === selectedMonth;
    const fill = palette.barFill
      ?? `rgba(79, 191, 198, ${palette.highlightMonth && isActive ? 0.95 : 0.55})`;
    const strokeAttr = palette.barStroke
      ? ` stroke="${palette.barStroke}" stroke-width="${palette.barStrokeWidth}"`
      : "";
    return `<rect x="${x.toFixed(1)}" y="${y.toFixed(1)}" width="${(xStep - 16).toFixed(1)}" height="${barHeight.toFixed(1)}" rx="6" fill="${fill}"${strokeAttr} />`;
  }).join("");

  const tempPath = chartPoints
    .map((point, index) => `${index === 0 ? "M" : "L"}${point.x.toFixed(1)},${point.y.toFixed(1)}`)
    .join(" ");

  const monthLabelMarkup = monthLabels.map((label, index) => {
    const x = margin.left + index * xStep + xStep / 2;
    const isActive = palette.highlightMonth && index + 1 === selectedMonth;
    return `<text x="${x.toFixed(1)}" y="${height - 10}" text-anchor="middle" class="axis-label chart-month-label${isActive ? " is-active" : ""}" fill="${palette.axisLabel}">${escapeHtml(label)}</text>`;
  }).join("");

  const monthHitTargets = resolvedInteractive
    ? chartPoints.map((point) => {
      const x = margin.left + point.monthIndex * xStep;
      const isActive = point.monthIndex + 1 === selectedMonth;
      return `
        <rect
          x="${x.toFixed(1)}"
          y="${(margin.top - 6).toFixed(1)}"
          width="${xStep.toFixed(1)}"
          height="${(innerHeight + 28).toFixed(1)}"
          rx="10"
          class="chart-hit-target${isActive ? " is-active" : ""}"
          data-chart-month="${point.monthIndex + 1}"
        />
      `;
    }).join("")
    : "";

  const yGridLines = tempTicks
    .map((tick) => `<line x1="${margin.left}" y1="${tick.y.toFixed(1)}" x2="${width - margin.right}" y2="${tick.y.toFixed(1)}" stroke="${palette.gridLine}" class="grid-line chart-grid-line" />`)
    .join("");

  const precipTickLabels = precipTicks
    .map((tick) => `
      <text
        x="${(width - 8).toFixed(1)}"
        y="${(tick.y + 4).toFixed(1)}"
        text-anchor="end"
        class="axis-label chart-tick chart-tick-right"
        fill="${palette.axisLabel}"
      >${Math.round(tick.value)}</text>
    `)
    .join("");

  const tempTickLabels = tempTicks
    .map((tick) => `
      <text
        x="${(margin.left - 8).toFixed(1)}"
        y="${(tick.y + 4).toFixed(1)}"
        text-anchor="end"
        class="axis-label chart-tick chart-tick-left"
        fill="${palette.axisLabel}"
      >${tick.value.toFixed(0)}</text>
    `)
    .join("");

  const titleMarkup = chartTitle
    ? `<text x="${(width / 2).toFixed(1)}" y="24" text-anchor="middle" fill="${palette.axisTitle}" font-size="16" font-weight="700">${escapeHtml(chartTitle)}</text>`
    : "";

  const defsMarkup = palette.showGradient
    ? `
      <defs>
        <linearGradient id="tempLineGradient" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stop-color="#ffd06b" />
          <stop offset="100%" stop-color="#f16b45" />
        </linearGradient>
      </defs>
    `
    : "";

  return `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" role="img" aria-label="월별 기온과 강수량 그래프">
      ${defsMarkup}
      <rect x="0" y="0" width="${width}" height="${height}" fill="${palette.background}" />
      ${titleMarkup}
      ${yGridLines}
      <line x1="${margin.left}" y1="${margin.top + innerHeight}" x2="${width - margin.right}" y2="${margin.top + innerHeight}" stroke="${palette.axisLine}" class="chart-axis" />
      <line x1="${margin.left}" y1="${margin.top}" x2="${margin.left}" y2="${margin.top + innerHeight}" stroke="${palette.axisLine}" class="chart-axis" />
      <line x1="${width - margin.right}" y1="${margin.top}" x2="${width - margin.right}" y2="${margin.top + innerHeight}" stroke="${palette.axisLine}" class="chart-axis chart-axis-right" />
      ${precipTickLabels}
      ${tempTickLabels}
      ${bars}
      <path d="${tempPath}" fill="none" stroke="${palette.tempLine}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" />
      ${chartPoints.map((point) => {
        const isActive = palette.highlightMonth && point.monthIndex + 1 === selectedMonth;
        const radius = isActive ? 5 : 3.5;
        return `<circle cx="${point.x.toFixed(1)}" cy="${point.y.toFixed(1)}" r="${radius}" fill="${palette.pointFill}" stroke="${palette.pointStroke}" stroke-width="2" />`;
      }).join("")}
      ${monthHitTargets}
      <text x="${margin.left}" y="${margin.top - 2}" class="axis-title" fill="${palette.axisTitle}">기온 (°C)</text>
      <text x="${width - margin.right}" y="${margin.top - 2}" text-anchor="end" class="axis-title" fill="${palette.axisTitle}">강수량 (mm)</text>
      ${monthLabelMarkup}
    </svg>
  `;
}

export function buildClimateChartSvgMarkup(options) {
  return buildClimateChartSvgInternal(options);
}

export function buildClimateChartMarkup({
  analysis,
  selectedMonth,
  monthLabels,
  observedOceanCell,
  climateResolution,
  theme = "screen",
  exportKey = "",
  chartTitle = "",
  showReadout = true,
  interactive = true,
}) {
  if (observedOceanCell) {
    return `
      <div class="chart-empty">
        <strong>해양 셀</strong>
        <p>현재 월별 기후자료는 육상 ${escapeHtml(climateResolution)} 격자를 사용해 바다는 안내만 제공합니다.</p>
      </div>
    `;
  }

  const chartPoints = analysis.temperatures.map((temperature, monthIndex) => ({
    temperature,
    precipitation: analysis.precipitations[monthIndex],
    monthIndex,
  }));
  const activePoint = getActivePoint(chartPoints, selectedMonth);
  const activeMonthLabel = monthLabels[activePoint.monthIndex];

  const actionsMarkup = exportKey
    ? `
      <div class="chart-actions">
        <button type="button" class="chart-export-button" data-chart-export="png" data-chart-key="${escapeHtml(exportKey)}">PNG 저장</button>
        <button type="button" class="chart-export-button" data-chart-export="jpg" data-chart-key="${escapeHtml(exportKey)}">JPG 저장</button>
      </div>
    `
    : "";

  const readoutMarkup = showReadout
    ? `
      <div class="chart-readout">
        <div class="chart-readout-item chart-readout-month">
          <span>선택 월</span>
          <strong>${escapeHtml(activeMonthLabel)}</strong>
        </div>
        <div class="chart-readout-item chart-readout-temp">
          <span>기온</span>
          <strong>${activePoint.temperature.toFixed(1)}°C</strong>
        </div>
        <div class="chart-readout-item chart-readout-precip">
          <span>강수량</span>
          <strong>${Math.round(activePoint.precipitation)} mm</strong>
        </div>
        <p class="chart-readout-hint">그래프의 월을 누르면 해당 달 수치로 바로 바뀝니다.</p>
      </div>
    `
    : "";

  return `
    ${actionsMarkup}
    ${readoutMarkup}
    ${buildClimateChartSvgInternal({
      analysis,
      selectedMonth,
      monthLabels,
      observedOceanCell,
      climateResolution,
      theme,
      interactive,
      chartTitle,
    })}
  `;
}
