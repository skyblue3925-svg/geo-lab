function buildLinePath(data, xForIndex, yForValue, valueKey) {
  return data
    .map((item, index) => `${index === 0 ? "M" : "L"}${xForIndex(index).toFixed(1)},${yForValue(item[valueKey]).toFixed(1)}`)
    .join(" ");
}

export function buildTransectSvgMarkup({
  data,
  width,
  height,
  margin,
  longitudeCount,
  selectedLongitude,
  mountainLongitude,
}) {
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;
  const maxElevation = Math.max(1500, ...data.map((item) => item.elevation)) * 1.05;
  const maxPrecip = Math.max(120, ...data.map((item) => item.precipitation)) * 1.05;
  const lonSpan = longitudeCount - 1;

  const xForIndex = (index) => margin.left + (index / lonSpan) * innerWidth;
  const elevationY = (value) => margin.top + innerHeight - (value / maxElevation) * innerHeight * 0.52;
  const precipY = (value) => margin.top + innerHeight - (value / maxPrecip) * innerHeight;

  const terrainPath = buildLinePath(data, xForIndex, elevationY, "elevation");
  const terrainClosed = `${terrainPath} L ${xForIndex(lonSpan).toFixed(1)},${(margin.top + innerHeight).toFixed(1)} L ${xForIndex(0).toFixed(1)},${(margin.top + innerHeight).toFixed(1)} Z`;
  const precipPath = buildLinePath(data, xForIndex, precipY, "precipitation");
  const selectedIndex = data.findIndex((item) => Math.abs(item.longitude - selectedLongitude) < 2.6);
  const selectedX = xForIndex(Math.max(0, selectedIndex));
  const mountainX = margin.left + ((mountainLongitude + 180) / 360) * innerWidth;

  return `
    <svg viewBox="0 0 ${width} ${height}" role="img" aria-label="선택 위도의 지형과 강수 단면도">
      <defs>
        <linearGradient id="terrainGradient" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#f8d77a" />
          <stop offset="100%" stop-color="#7b5438" />
        </linearGradient>
      </defs>
      <rect x="0" y="0" width="${width}" height="${height}" fill="transparent" />
      <line x1="${margin.left}" y1="${margin.top + innerHeight}" x2="${width - margin.right}" y2="${margin.top + innerHeight}" class="chart-axis" />
      <path d="${terrainClosed}" fill="url(#terrainGradient)" opacity="0.88" />
      <path d="${precipPath}" fill="none" stroke="#61d6dc" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" />
      <line x1="${mountainX.toFixed(1)}" y1="${margin.top}" x2="${mountainX.toFixed(1)}" y2="${margin.top + innerHeight}" class="mountain-line" />
      <line x1="${selectedX.toFixed(1)}" y1="${margin.top}" x2="${selectedX.toFixed(1)}" y2="${margin.top + innerHeight}" class="probe-line" />
      <text x="${mountainX.toFixed(1)}" y="${margin.top - 4}" text-anchor="middle" class="axis-label">산맥</text>
      <text x="${selectedX.toFixed(1)}" y="${height - 8}" text-anchor="middle" class="axis-label">선택 위치</text>
    </svg>
  `;
}

export function buildTransectCaptionText(coordinateLabel) {
  return `${coordinateLabel}와 같은 위도대를 따라 잘라 본 단면입니다. 편서풍/무역풍이 산맥을 넘을 때 강수와 푄이 어떻게 달라지는지 비교하세요.`;
}
