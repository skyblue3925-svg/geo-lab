import { buildFeatureCollectionMeasurementSummary } from "./measurement-use-cases.js";

const EARTH_METERS_PER_DEGREE = 111320;

function toRadians(value) {
  return (value * Math.PI) / 180;
}

function createProjectionContext(coordinates) {
  const validCoordinates = coordinates.filter(
    (coordinate) =>
      Array.isArray(coordinate)
      && coordinate.length >= 2
      && Number.isFinite(Number(coordinate[0]))
      && Number.isFinite(Number(coordinate[1])),
  );

  if (!validCoordinates.length) {
    throw new Error("버퍼를 만들 좌표가 없습니다.");
  }

  const averageLat =
    validCoordinates.reduce((total, [, lat]) => total + Number(lat), 0) / validCoordinates.length;
  const averageLng =
    validCoordinates.reduce((total, [lng]) => total + Number(lng), 0) / validCoordinates.length;
  const metersPerLng = EARTH_METERS_PER_DEGREE * Math.cos(toRadians(averageLat));

  return {
    originLng: averageLng,
    originLat: averageLat,
    metersPerLng: Math.max(metersPerLng, 1),
    metersPerLat: EARTH_METERS_PER_DEGREE,
  };
}

function projectCoordinate([lng, lat], context) {
  return {
    x: (Number(lng) - context.originLng) * context.metersPerLng,
    y: (Number(lat) - context.originLat) * context.metersPerLat,
  };
}

function unprojectPoint(point, context) {
  return [
    Number((context.originLng + point.x / context.metersPerLng).toFixed(6)),
    Number((context.originLat + point.y / context.metersPerLat).toFixed(6)),
  ];
}

function getBoundaryCoordinates(feature) {
  if (!feature?.coordinates?.length) {
    return [];
  }

  if (feature.geometryType === "point") {
    return feature.coordinates.slice(0, 1);
  }

  return feature.coordinates;
}

function interpolatePoint(start, end, ratio) {
  return {
    x: start.x + (end.x - start.x) * ratio,
    y: start.y + (end.y - start.y) * ratio,
  };
}

function sampleSegmentPoints(start, end, stepMeters) {
  const dx = end.x - start.x;
  const dy = end.y - start.y;
  const distance = Math.hypot(dx, dy);

  if (!distance) {
    return [start];
  }

  const segments = Math.max(1, Math.ceil(distance / stepMeters));
  const sampled = [];
  for (let index = 0; index <= segments; index += 1) {
    sampled.push(interpolatePoint(start, end, index / segments));
  }
  return sampled;
}

function buildSamplePoints(projectedCoordinates, geometryType, radiusMeters) {
  if (geometryType === "point") {
    return projectedCoordinates.slice(0, 1);
  }

  const sampled = [];
  const stepMeters = Math.max(12, radiusMeters / 3);
  const lastIndex = projectedCoordinates.length - 1;
  const segmentCount = geometryType === "polygon" ? projectedCoordinates.length : lastIndex;

  for (let index = 0; index < segmentCount; index += 1) {
    const start = projectedCoordinates[index];
    const end = projectedCoordinates[(index + 1) % projectedCoordinates.length];
    sampleSegmentPoints(start, end, stepMeters).forEach((point) => {
      sampled.push(point);
    });
  }

  return sampled;
}

function buildCirclePoints(center, radiusMeters, pointCount = 24) {
  const points = [];
  for (let index = 0; index < pointCount; index += 1) {
    const angle = (Math.PI * 2 * index) / pointCount;
    points.push({
      x: center.x + Math.cos(angle) * radiusMeters,
      y: center.y + Math.sin(angle) * radiusMeters,
    });
  }
  return points;
}

function cross(origin, left, right) {
  return (left.x - origin.x) * (right.y - origin.y) - (left.y - origin.y) * (right.x - origin.x);
}

function computeConvexHull(points) {
  if (points.length <= 1) {
    return points.slice();
  }

  const sorted = [...points].sort((left, right) =>
    left.x === right.x ? left.y - right.y : left.x - right.x);

  const lower = [];
  sorted.forEach((point) => {
    while (lower.length >= 2 && cross(lower[lower.length - 2], lower[lower.length - 1], point) <= 0) {
      lower.pop();
    }
    lower.push(point);
  });

  const upper = [];
  sorted
    .slice()
    .reverse()
    .forEach((point) => {
      while (upper.length >= 2 && cross(upper[upper.length - 2], upper[upper.length - 1], point) <= 0) {
        upper.pop();
      }
      upper.push(point);
    });

  lower.pop();
  upper.pop();
  return [...lower, ...upper];
}

function closeRing(coordinates) {
  if (!coordinates.length) {
    return [];
  }

  const ring = [...coordinates];
  const [firstLng, firstLat] = ring[0];
  const [lastLng, lastLat] = ring[ring.length - 1];

  if (firstLng !== lastLng || firstLat !== lastLat) {
    ring.push([firstLng, firstLat]);
  }

  return ring;
}

export function buildBufferedFeatureCollection({ feature, radiusMeters }) {
  const boundaryCoordinates = getBoundaryCoordinates(feature);
  const context = createProjectionContext(boundaryCoordinates);
  const projectedCoordinates = boundaryCoordinates.map((coordinate) => projectCoordinate(coordinate, context));
  const sampledPoints = buildSamplePoints(projectedCoordinates, feature.geometryType, radiusMeters);
  const expandedPoints = sampledPoints.flatMap((point) => buildCirclePoints(point, radiusMeters));
  const hull = computeConvexHull(expandedPoints);

  if (hull.length < 3) {
    throw new Error("버퍼를 만들 만큼 충분한 좌표가 없습니다.");
  }

  const ring = closeRing(hull.map((point) => unprojectPoint(point, context)));

  return {
    type: "FeatureCollection",
    features: [
      {
        type: "Feature",
        geometry: {
          type: "Polygon",
          coordinates: [ring],
        },
        properties: {
          analysisType: "buffer",
          radiusMeters,
          bufferPrecision: "approximate",
        },
      },
    ],
  };
}

export function createBufferLayer({
  idFactory,
  selectedFeatureRecord,
  radiusMeters,
  color = "#0d9f6f",
  scope = "school",
}) {
  const { layer, feature } = selectedFeatureRecord;
  const featureCollection = buildBufferedFeatureCollection({
    feature,
    radiusMeters,
  });
  const bufferMeasurement = buildFeatureCollectionMeasurementSummary(featureCollection);
  const baseTitle = String(feature.title || layer.name || "선택 객체").trim();

  featureCollection.features[0].properties = {
    ...featureCollection.features[0].properties,
    title: `${baseTitle} ${radiusMeters}m 버퍼`,
    note: `${layer.name} 레이어의 ${baseTitle} 주변 ${radiusMeters}m 근사 버퍼`,
    sourceLayerId: layer.id,
    sourceFeatureId: feature.id,
    sourceGeometryType: feature.geometryType,
    areaSquareMeters: bufferMeasurement?.totalAreaSquareMeters ?? null,
    areaLabel: bufferMeasurement?.totalAreaLabel ?? "",
    perimeterMeters: bufferMeasurement?.totalPerimeterMeters ?? null,
    perimeterLabel: bufferMeasurement?.totalPerimeterLabel ?? "",
  };

  return {
    id: idFactory("analysis-buffer"),
    name: `${baseTitle} ${radiusMeters}m 버퍼`,
    description: `${layer.name} 레이어에서 만든 ${radiusMeters}m 분석 버퍼`,
    color,
    visible: true,
    scope,
    sourceKind: "analysis",
    sourceLabel: `근사 버퍼 ${radiusMeters}m`,
    createdAt: new Date().toISOString(),
    measurementSummary: bufferMeasurement,
    featureCollection,
  };
}
