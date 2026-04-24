function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

export function findNearestMapSpot({
  mapX,
  mapY,
  plotWidth,
  plotHeight,
  spotlights,
  examSpotlights,
  lonToX,
  latToY,
}) {
  let closest = null;

  const checkCandidate = (candidate) => {
    const x = lonToX(candidate.longitude, plotWidth);
    const y = latToY(candidate.latitude, plotHeight);
    const distance = Math.hypot(mapX - x, mapY - y);
    if (distance > candidate.hitRadius) {
      return;
    }
    if (!closest || distance < closest.distance) {
      closest = { ...candidate, distance };
    }
  };

  spotlights.forEach((spot) => {
    checkCandidate({
      kind: "spotlight",
      id: spot.id,
      latitude: spot.latitude,
      longitude: spot.longitude,
      hitRadius: 13,
    });
  });

  examSpotlights.forEach((spot) => {
    checkCandidate({
      kind: "exam",
      id: spot.id,
      latitude: spot.latitude,
      longitude: spot.longitude,
      hitRadius: 8 + Math.min(spot.examCount, 6) * 0.65,
    });
  });

  return closest;
}

export function resolveMapClickSelection({
  clientX,
  clientY,
  rect,
  plot,
  spotlights,
  examSpotlights,
  lonToX,
  latToY,
}) {
  const localX = clientX - rect.left;
  const localY = clientY - rect.top;
  if (localX < plot.left || localX > plot.right || localY < plot.top || localY > plot.bottom) {
    return null;
  }

  const mapX = localX - plot.left;
  const mapY = localY - plot.top;
  const nearestSpot = findNearestMapSpot({
    mapX,
    mapY,
    plotWidth: plot.width,
    plotHeight: plot.height,
    spotlights,
    examSpotlights,
    lonToX,
    latToY,
  });
  if (nearestSpot) {
    return nearestSpot;
  }

  const x = clamp((localX - plot.left) / Math.max(plot.width, 1), 0, 1);
  const y = clamp((localY - plot.top) / Math.max(plot.height, 1), 0, 1);
  return {
    kind: "coordinate",
    latitude: 90 - y * 180,
    longitude: x * 360 - 180,
  };
}
