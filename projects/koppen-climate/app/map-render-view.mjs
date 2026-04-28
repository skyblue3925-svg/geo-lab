function getCellFill({
  overlay,
  cellIndex,
  world,
  monthIndex,
  koppenColors,
  temperatureColor,
  precipitationColor,
}) {
  const isOceanCell = world.landness[cellIndex] < 0.42;
  if (overlay === "koppen") {
    const code = world.koppenCodes[cellIndex];
    return code === "Ocean" ? "rgba(33, 73, 92, 0.88)" : (koppenColors[code] ?? "#5e7483");
  }
  if (isOceanCell) {
    return "rgba(23, 48, 62, 0.96)";
  }
  if (overlay === "temperature") {
    return temperatureColor(world.monthlyTemperature[monthIndex][cellIndex]);
  }
  return precipitationColor(world.monthlyPrecipitation[monthIndex][cellIndex]);
}

export function drawMapBaseLayer({
  ctx,
  plotWidth,
  plotHeight,
  latitudes,
  longitudes,
  overlay,
  circulationLayout,
  officialKoppenCanvas,
  world,
  monthIndex,
  koppenColors,
  temperatureColor,
  precipitationColor,
  drawCirculationBands,
}) {
  const cellWidth = plotWidth / longitudes.length;
  const cellHeight = plotHeight / latitudes.length;

  if (overlay === "circulation") {
    ctx.fillStyle = "rgba(15, 33, 45, 0.98)";
    ctx.fillRect(0, 0, plotWidth, plotHeight);
    drawCirculationBands(ctx, plotWidth, plotHeight, circulationLayout);
    return;
  }

  if (overlay === "koppen" && officialKoppenCanvas) {
    ctx.drawImage(officialKoppenCanvas, 0, 0, plotWidth, plotHeight);
    return;
  }

  for (let latIndex = 0; latIndex < latitudes.length; latIndex += 1) {
    for (let lonIndex = 0; lonIndex < longitudes.length; lonIndex += 1) {
      const cellIndex = latIndex * longitudes.length + lonIndex;
      const x = lonIndex * cellWidth;
      const y = plotHeight - (latIndex + 1) * cellHeight;
      ctx.fillStyle = getCellFill({
        overlay,
        cellIndex,
        world,
        monthIndex,
        koppenColors,
        temperatureColor,
        precipitationColor,
      });
      ctx.fillRect(x, y, cellWidth + 1, cellHeight + 1);
    }
  }
}

export function drawMapOverlayAnnotations({
  ctx,
  plotWidth,
  plotHeight,
  overlay,
  circulationLayout,
  circulationStage,
  worldItczLatitude,
  mountainHeight,
  mountainLongitude,
  screenMode,
  latToY,
  lonToX,
  drawCirculationForeground,
}) {
  if (overlay === "circulation") {
    drawCirculationForeground(ctx, plotWidth, plotHeight, circulationLayout, circulationStage);
    return;
  }

  ctx.save();
  ctx.strokeStyle = "rgba(255, 208, 107, 0.95)";
  ctx.fillStyle = "rgba(255, 208, 107, 0.95)";
  ctx.lineWidth = 2.4;
  ctx.setLineDash([10, 6]);
  const itczY = latToY(worldItczLatitude, plotHeight);
  ctx.beginPath();
  ctx.moveTo(0, itczY);
  ctx.lineTo(plotWidth, itczY);
  ctx.stroke();
  ctx.setLineDash([]);
  ctx.font = '700 12px "Aptos", sans-serif';
  ctx.textAlign = "left";
  ctx.fillText("ITCZ", 10, Math.max(14, itczY - 8));

  if (mountainHeight > 0 && screenMode === "experiment") {
    const mountainX = lonToX(mountainLongitude, plotWidth);
    ctx.strokeStyle = "rgba(247, 231, 184, 0.82)";
    ctx.setLineDash([4, 5]);
    ctx.beginPath();
    ctx.moveTo(mountainX, 0);
    ctx.lineTo(mountainX, plotHeight);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = "rgba(247, 231, 184, 0.9)";
    ctx.textAlign = mountainX < plotWidth - 70 ? "left" : "right";
    ctx.fillText("산맥", mountainX + (mountainX < plotWidth - 70 ? 8 : -8), 18);
  }
  ctx.restore();
}

export function drawSelectedLocationMarker({
  ctx,
  plotWidth,
  plotHeight,
  selectedLongitude,
  selectedLatitude,
  lonToX,
  latToY,
}) {
  const selectedX = lonToX(selectedLongitude, plotWidth);
  const selectedY = latToY(selectedLatitude, plotHeight);
  ctx.save();
  ctx.strokeStyle = "#ffffff";
  ctx.fillStyle = "#ffffff";
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.arc(selectedX, selectedY, 8, 0, Math.PI * 2);
  ctx.stroke();
  ctx.beginPath();
  ctx.arc(selectedX, selectedY, 3.2, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();
}

export function drawSpotlightMarkers({
  ctx,
  plotWidth,
  plotHeight,
  spotlights,
  selectedLatitude,
  selectedLongitude,
  lonToX,
  latToY,
}) {
  ctx.save();
  ctx.font = '700 11px "Bahnschrift", sans-serif';
  ctx.textAlign = "center";
  spotlights.forEach((spot) => {
    const x = lonToX(spot.longitude, plotWidth);
    const y = latToY(spot.latitude, plotHeight);
    const active = Math.abs(spot.latitude - selectedLatitude) < 2.5 && Math.abs(spot.longitude - selectedLongitude) < 2.5;
    ctx.beginPath();
    ctx.fillStyle = active ? "#ffd06b" : "rgba(255, 255, 255, 0.88)";
    ctx.strokeStyle = "#0f2232";
    ctx.lineWidth = active ? 3 : 2;
    ctx.arc(x, y, active ? 6 : 4, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();
    ctx.fillStyle = "rgba(255,255,255,0.92)";
    ctx.fillText(spot.short, x, y - 10);
  });
  ctx.restore();
}

export function drawExamSpotMarkers({
  ctx,
  plotWidth,
  plotHeight,
  examSpotlights,
  activeExamSpot,
  lonToX,
  latToY,
  drawOverlayLabel,
}) {
  const orderedSpots = examSpotlights
    .slice()
    .sort((left, right) => {
      if (activeExamSpot?.id === left.id) {
        return 1;
      }
      if (activeExamSpot?.id === right.id) {
        return -1;
      }
      return left.examCount - right.examCount;
    });

  ctx.save();
  orderedSpots.forEach((spot) => {
    const x = lonToX(spot.longitude, plotWidth);
    const y = latToY(spot.latitude, plotHeight);
    const active = activeExamSpot?.id === spot.id;
    const radius = active ? 6.4 : 1.9 + Math.min(spot.examCount, 6) * 0.48;
    const fill = spot.examCount >= 5
      ? "rgba(239, 114, 76, 0.96)"
      : spot.examCount >= 3
        ? "rgba(255, 208, 107, 0.95)"
        : "rgba(219, 236, 245, 0.78)";

    ctx.beginPath();
    ctx.fillStyle = "rgba(8, 16, 24, 0.34)";
    ctx.arc(x, y, radius + 1.8, 0, Math.PI * 2);
    ctx.fill();

    ctx.beginPath();
    ctx.fillStyle = fill;
    ctx.strokeStyle = active ? "#fff2bf" : "rgba(10, 18, 27, 0.88)";
    ctx.lineWidth = active ? 2.6 : 1.2;
    ctx.arc(x, y, radius, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();
  });

  if (activeExamSpot) {
    const x = lonToX(activeExamSpot.longitude, plotWidth);
    const y = latToY(activeExamSpot.latitude, plotHeight);
    const align = x < plotWidth - 120 ? "left" : "right";
    const labelX = align === "left" ? x + 12 : x - 12;
    const labelY = y < 30 ? y + 18 : y - 16;
    drawOverlayLabel(
      ctx,
      labelX,
      labelY,
      activeExamSpot.name,
      `${activeExamSpot.examCode} · 평가원 ${activeExamSpot.examCount}회`,
      align,
      "rgba(255, 236, 188, 0.98)",
    );
  }
  ctx.restore();
}
