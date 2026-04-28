const EARTH_RADIUS_METERS = 6371008.8;
const EARTH_METERS_PER_DEGREE = 111320;

function toRadians(value) {
  return (Number(value) * Math.PI) / 180;
}

function formatMetric(value, digits = 0) {
  return new Intl.NumberFormat("ko-KR", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(value);
}

function formatDistance(meters) {
  if (meters >= 1000) {
    return `${formatMetric(meters / 1000, 2)} km`;
  }
  return `${formatMetric(meters, 0)} m`;
}

function formatArea(squareMeters) {
  if (squareMeters >= 1_000_000) {
    return `${formatMetric(squareMeters / 1_000_000, 2)} km²`;
  }
  if (squareMeters >= 10_000) {
    return `${formatMetric(squareMeters / 10_000, 2)} ha`;
  }
  return `${formatMetric(squareMeters, 0)} m²`;
}

function haversineDistanceMeters(start, end) {
  const lat1 = toRadians(start.lat);
  const lat2 = toRadians(end.lat);
  const deltaLat = lat2 - lat1;
  const deltaLng = toRadians(end.lng - start.lng);

  const a = Math.sin(deltaLat / 2) ** 2
    + Math.cos(lat1) * Math.cos(lat2) * Math.sin(deltaLng / 2) ** 2;
  return 2 * EARTH_RADIUS_METERS * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

function getAverageLat(points) {
  return points.reduce((total, point) => total + point.lat, 0) / points.length;
}

function projectPoint(point, averageLat) {
  const metersPerLng = EARTH_METERS_PER_DEGREE * Math.cos(toRadians(averageLat));
  return {
    x: point.lng * metersPerLng,
    y: point.lat * EARTH_METERS_PER_DEGREE,
  };
}

function calculatePolygonArea(points) {
  if (points.length < 3) {
    return 0;
  }

  const averageLat = getAverageLat(points);
  const projected = points.map((point) => projectPoint(point, averageLat));
  let area = 0;
  for (let index = 0; index < projected.length; index += 1) {
    const current = projected[index];
    const next = projected[(index + 1) % projected.length];
    area += current.x * next.y - next.x * current.y;
  }
  return Math.abs(area) / 2;
}

function toLatLngPoints(coordinates) {
  return coordinates.map(([lng, lat]) => ({
    lat: Number(lat),
    lng: Number(lng),
  }));
}

function buildGeometrySummaryFromCoordinates(geometryType, coordinates) {
  const points = toLatLngPoints(coordinates);
  if (geometryType === "line") {
    const distance = calculateDistanceMeasurement(points);
    return {
      lengthMeters: distance.raw.totalDistanceMeters,
      lengthLabel: distance.primaryValue,
    };
  }

  if (geometryType === "polygon") {
    const area = calculateAreaMeasurement(points);
    return {
      areaSquareMeters: area.raw.areaSquareMeters,
      areaLabel: area.primaryValue,
      perimeterMeters: area.raw.perimeterMeters,
      perimeterLabel: formatDistance(area.raw.perimeterMeters),
    };
  }

  return null;
}

function accumulateGeometrySummary(target, geometryType, coordinates) {
  const summary = buildGeometrySummaryFromCoordinates(geometryType, coordinates);
  if (!summary) {
    return;
  }

  if (summary.lengthMeters) {
    target.totalLengthMeters += summary.lengthMeters;
  }
  if (summary.areaSquareMeters) {
    target.totalAreaSquareMeters += summary.areaSquareMeters;
  }
  if (summary.perimeterMeters) {
    target.totalPerimeterMeters += summary.perimeterMeters;
  }
}

function accumulateGeoJsonGeometry(target, geometry) {
  if (!geometry?.type) {
    return;
  }

  switch (geometry.type) {
    case "LineString":
      accumulateGeometrySummary(target, "line", geometry.coordinates ?? []);
      break;
    case "MultiLineString":
      (geometry.coordinates ?? []).forEach((coordinates) => {
        accumulateGeometrySummary(target, "line", coordinates ?? []);
      });
      break;
    case "Polygon":
      accumulateGeometrySummary(target, "polygon", geometry.coordinates?.[0] ?? []);
      break;
    case "MultiPolygon":
      (geometry.coordinates ?? []).forEach((polygon) => {
        accumulateGeometrySummary(target, "polygon", polygon?.[0] ?? []);
      });
      break;
    default:
      break;
  }
}

export function calculateDistanceMeasurement(points) {
  const segments = [];
  let totalDistanceMeters = 0;

  for (let index = 1; index < points.length; index += 1) {
    const segmentDistance = haversineDistanceMeters(points[index - 1], points[index]);
    totalDistanceMeters += segmentDistance;
    segments.push(segmentDistance);
  }

  return {
    kind: "distance",
    title: "거리 측정",
    primaryLabel: "총 거리",
    primaryValue: formatDistance(totalDistanceMeters),
    detail: `구간 ${segments.length}개를 따라 측정했습니다.`,
    raw: {
      totalDistanceMeters,
      segments,
    },
  };
}

export function calculateAreaMeasurement(points) {
  const perimeterMeters = calculateDistanceMeasurement([...points, points[0]]).raw.totalDistanceMeters;
  const areaSquareMeters = calculatePolygonArea(points);

  return {
    kind: "area",
    title: "면적 측정",
    primaryLabel: "면적",
    primaryValue: formatArea(areaSquareMeters),
    detail: `둘레 ${formatDistance(perimeterMeters)}`,
    raw: {
      areaSquareMeters,
      perimeterMeters,
    },
  };
}

export function buildMeasurementResult(tool, draftGeometry) {
  const points = draftGeometry?.points ?? [];
  if (tool === "measure-line") {
    return calculateDistanceMeasurement(points);
  }
  if (tool === "measure-area") {
    return calculateAreaMeasurement(points);
  }
  return null;
}

export function buildFeatureMeasurementSummary(feature) {
  if (!feature?.geometryType || !Array.isArray(feature.coordinates)) {
    return null;
  }

  return buildGeometrySummaryFromCoordinates(feature.geometryType, feature.coordinates);
}

export function buildLayerMeasurementSummary(layer) {
  const summary = {
    pointCount: 0,
    lineCount: 0,
    polygonCount: 0,
    totalLengthMeters: 0,
    totalAreaSquareMeters: 0,
    totalPerimeterMeters: 0,
  };

  (layer?.features ?? []).forEach((feature) => {
    switch (feature.geometryType) {
      case "line":
        summary.lineCount += 1;
        break;
      case "polygon":
        summary.polygonCount += 1;
        break;
      case "point":
      default:
        summary.pointCount += 1;
        break;
    }

    const featureSummary = buildFeatureMeasurementSummary(feature);
    if (!featureSummary) {
      return;
    }

    if (featureSummary.lengthMeters) {
      summary.totalLengthMeters += featureSummary.lengthMeters;
    }
    if (featureSummary.areaSquareMeters) {
      summary.totalAreaSquareMeters += featureSummary.areaSquareMeters;
    }
    if (featureSummary.perimeterMeters) {
      summary.totalPerimeterMeters += featureSummary.perimeterMeters;
    }
  });

  const breakdown = [
    summary.pointCount ? `점 ${summary.pointCount}개` : null,
    summary.lineCount ? `선 ${summary.lineCount}개` : null,
    summary.polygonCount ? `면 ${summary.polygonCount}개` : null,
  ].filter(Boolean);

  return {
    ...summary,
    breakdownLabel: breakdown.join(" · "),
    totalLengthLabel: summary.totalLengthMeters > 0 ? formatDistance(summary.totalLengthMeters) : "",
    totalAreaLabel: summary.totalAreaSquareMeters > 0 ? formatArea(summary.totalAreaSquareMeters) : "",
    totalPerimeterLabel:
      summary.totalPerimeterMeters > 0 ? formatDistance(summary.totalPerimeterMeters) : "",
  };
}

export function buildFeatureCollectionMeasurementSummary(featureCollection) {
  const summary = {
    totalLengthMeters: 0,
    totalAreaSquareMeters: 0,
    totalPerimeterMeters: 0,
  };

  (featureCollection?.features ?? []).forEach((feature) => {
    accumulateGeoJsonGeometry(summary, feature?.geometry);
  });

  if (
    summary.totalLengthMeters <= 0
    && summary.totalAreaSquareMeters <= 0
    && summary.totalPerimeterMeters <= 0
  ) {
    return null;
  }

  return {
    ...summary,
    totalLengthLabel: summary.totalLengthMeters > 0 ? formatDistance(summary.totalLengthMeters) : "",
    totalAreaLabel: summary.totalAreaSquareMeters > 0 ? formatArea(summary.totalAreaSquareMeters) : "",
    totalPerimeterLabel:
      summary.totalPerimeterMeters > 0 ? formatDistance(summary.totalPerimeterMeters) : "",
  };
}
