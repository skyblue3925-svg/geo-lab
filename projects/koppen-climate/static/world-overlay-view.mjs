function drawFallbackWorldOverlay(ctx, width, height, overlay, worldMapRegions, lonToX, latToY, withAlpha) {
  const fillAlpha = overlay === "koppen" ? 0.18 : overlay === "circulation" ? 0.05 : 0.08;
  const strokeAlpha = overlay === "koppen" ? 0.7 : overlay === "circulation" ? 0.32 : 0.42;

  for (const region of worldMapRegions) {
    ctx.beginPath();
    region.points.forEach(([longitude, latitude], index) => {
      const x = lonToX(longitude, width);
      const y = latToY(latitude, height);
      if (index === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    });
    ctx.closePath();
    ctx.fillStyle = withAlpha(region.fill, fillAlpha);
    ctx.strokeStyle = withAlpha(region.stroke, strokeAlpha);
    ctx.lineWidth = 1.2;
    ctx.fill();
    ctx.stroke();
  }
}

function traceRing(ctx, ring, width, height, lonToX, latToY) {
  ring.forEach(([longitude, latitude], index) => {
    const x = lonToX(longitude, width);
    const y = latToY(latitude, height);
    if (index === 0) {
      ctx.moveTo(x, y);
    } else {
      ctx.lineTo(x, y);
    }
  });
  ctx.closePath();
}

function traceGeometry(ctx, geometry, width, height, lonToX, latToY) {
  if (!geometry) {
    return;
  }
  if (geometry.type === "Polygon") {
    geometry.coordinates.forEach((ring) => traceRing(ctx, ring, width, height, lonToX, latToY));
    return;
  }
  if (geometry.type === "MultiPolygon") {
    geometry.coordinates.forEach((polygon) => {
      polygon.forEach((ring) => traceRing(ctx, ring, width, height, lonToX, latToY));
    });
  }
}

function drawGeoJsonCollection(ctx, geojson, width, height, options, lonToX, latToY) {
  if (!geojson?.features?.length) {
    return false;
  }
  ctx.beginPath();
  geojson.features.forEach((feature) => traceGeometry(ctx, feature.geometry, width, height, lonToX, latToY));
  if (options.fillStyle) {
    ctx.fillStyle = options.fillStyle;
    ctx.fill();
  }
  if (options.strokeStyle) {
    ctx.strokeStyle = options.strokeStyle;
    ctx.lineWidth = options.lineWidth ?? 1;
    ctx.stroke();
  }
  return true;
}

export function drawWorldOverlay({
  ctx,
  width,
  height,
  overlay,
  worldGeometry,
  worldMapBorders,
  worldMapRegions,
  lonToX,
  latToY,
  withAlpha,
  average,
}) {
  ctx.save();
  const usedRealGeometry = drawGeoJsonCollection(ctx, worldGeometry.land, width, height, {
    fillStyle: overlay === "koppen"
      ? "rgba(237, 231, 216, 0.18)"
      : overlay === "circulation"
        ? "rgba(237, 231, 216, 0.06)"
        : "rgba(237, 231, 216, 0.1)",
    strokeStyle: overlay === "circulation" ? "rgba(247, 241, 230, 0.34)" : "rgba(247, 241, 230, 0.48)",
    lineWidth: 1.2,
  }, lonToX, latToY);

  if (usedRealGeometry) {
    drawGeoJsonCollection(ctx, worldGeometry.countries, width, height, {
      strokeStyle: overlay === "koppen" ? "rgba(255, 255, 255, 0.18)" : "rgba(255, 255, 255, 0.12)",
      lineWidth: 0.65,
    }, lonToX, latToY);
  } else {
    drawFallbackWorldOverlay(ctx, width, height, overlay, worldMapRegions, lonToX, latToY, withAlpha);
  }

  ctx.font = '700 11px "Aptos", sans-serif';
  for (const border of worldMapBorders) {
    const y = latToY(border.lat, height);
    const highlight = border.name === "Equator" || border.name === "Tropic of Cancer" || border.name === "Tropic of Capricorn";
    ctx.setLineDash(border.dash ? [6, 6] : []);
    ctx.strokeStyle = highlight ? "rgba(255, 231, 153, 0.55)" : "rgba(255,255,255,0.18)";
    ctx.lineWidth = highlight ? 1.4 : 1;
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(width, y);
    ctx.stroke();
    if (highlight) {
      const label = border.name === "Equator"
        ? "적도"
        : border.name === "Tropic of Cancer"
          ? "북회귀선"
          : "남회귀선";
      ctx.fillStyle = "rgba(255, 243, 214, 0.9)";
      ctx.textAlign = "right";
      ctx.fillText(label, width - 8, Math.max(12, y - 6));
    }
  }
  ctx.setLineDash([]);

  if (!usedRealGeometry) {
    ctx.fillStyle = "rgba(247, 244, 236, 0.68)";
    ctx.font = '600 12px "Aptos", sans-serif';
    ctx.textAlign = "center";
    for (const region of worldMapRegions.filter((item) => item.type === "continent" || item.type === "ice")) {
      const lon = average(region.points.map(([pointLon]) => pointLon));
      const lat = average(region.points.map(([, pointLat]) => pointLat));
      ctx.fillText(region.label, lonToX(lon, width), latToY(lat, height));
    }
  }
  ctx.restore();
}

export function drawMapAxes({
  ctx,
  plot,
  latToY,
  lonToX,
  formatLatitudeAxisLabel,
  formatLongitudeAxisLabel,
}) {
  const latitudeTicks = [90, 60, 30, 0, -30, -60, -90];
  const longitudeTicks = [-180, -120, -60, 0, 60, 120, 180];

  ctx.save();
  ctx.strokeStyle = "rgba(255, 255, 255, 0.16)";
  ctx.lineWidth = 1;
  ctx.strokeRect(plot.left, plot.top, plot.width, plot.height);
  ctx.font = '700 11px "Aptos", sans-serif';
  ctx.fillStyle = "rgba(247, 244, 236, 0.78)";
  ctx.textBaseline = "middle";
  ctx.textAlign = "right";

  latitudeTicks.forEach((latitude) => {
    const y = plot.top + latToY(latitude, plot.height);
    ctx.beginPath();
    ctx.moveTo(plot.left - 6, y);
    ctx.lineTo(plot.left, y);
    ctx.stroke();
    ctx.fillText(formatLatitudeAxisLabel(latitude), plot.left - 9, y);
  });

  ctx.textBaseline = "top";
  ctx.textAlign = "center";
  longitudeTicks.forEach((longitude) => {
    const x = plot.left + lonToX(longitude, plot.width);
    ctx.beginPath();
    ctx.moveTo(x, plot.bottom);
    ctx.lineTo(x, plot.bottom + 6);
    ctx.stroke();
    ctx.fillText(formatLongitudeAxisLabel(longitude), x, plot.bottom + 10);
  });
  ctx.restore();
}
