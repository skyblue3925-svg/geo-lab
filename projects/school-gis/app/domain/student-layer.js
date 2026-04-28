export const STUDENT_GEOMETRY_META = {
  point: {
    label: "점",
    minimumPoints: 1,
  },
  line: {
    label: "선",
    minimumPoints: 2,
  },
  polygon: {
    label: "면",
    minimumPoints: 3,
  },
};

const STUDENT_LAYER_GEOMETRY_LABEL = {
  ...Object.fromEntries(
    Object.entries(STUDENT_GEOMETRY_META).map(([key, value]) => [key, value.label]),
  ),
  mixed: "혼합",
};

function roundCoordinate(value) {
  return Number(Number(value).toFixed(6));
}

function isValidCoordinatePair(pair) {
  return Array.isArray(pair) && pair.length >= 2 && Number.isFinite(pair[0]) && Number.isFinite(pair[1]);
}

function normalizeCoordinatePair(value) {
  if (!Array.isArray(value) || value.length < 2) {
    return null;
  }

  const lng = Number(value[0]);
  const lat = Number(value[1]);
  if (!Number.isFinite(lat) || !Number.isFinite(lng)) {
    return null;
  }

  return [roundCoordinate(lng), roundCoordinate(lat)];
}

function stripClosedPolygonRing(coordinates) {
  if (!coordinates.length) {
    return [];
  }

  const first = coordinates[0];
  const last = coordinates.at(-1);
  if (first[0] === last[0] && first[1] === last[1]) {
    return coordinates.slice(0, -1);
  }

  return coordinates;
}

function inferGeometryTypeFromFeature(feature) {
  const geometryType = feature?.geometry?.type;
  switch (geometryType) {
    case "Point":
    case "MultiPoint":
      return "point";
    case "LineString":
    case "MultiLineString":
      return "line";
    case "Polygon":
    case "MultiPolygon":
      return "polygon";
    default:
      return resolveStudentGeometryType(feature?.geometryType);
  }
}

function normalizePointCoordinates(feature) {
  if (Array.isArray(feature.coordinates)) {
    if (Array.isArray(feature.coordinates[0])) {
      return feature.coordinates.map(normalizeCoordinatePair).filter(Boolean).slice(0, 1);
    }

    const coordinates = normalizeCoordinatePair(feature.coordinates);
    return coordinates ? [coordinates] : [];
  }

  if (feature?.geometry?.type === "Point") {
    const coordinates = normalizeCoordinatePair(feature.geometry.coordinates);
    return coordinates ? [coordinates] : [];
  }

  if (feature?.geometry?.type === "MultiPoint") {
    return feature.geometry.coordinates.map(normalizeCoordinatePair).filter(Boolean).slice(0, 1);
  }

  const lat = Number(feature.lat ?? feature.latitude);
  const lng = Number(feature.lng ?? feature.longitude);
  if (!Number.isFinite(lat) || !Number.isFinite(lng)) {
    return [];
  }

  return [[roundCoordinate(lng), roundCoordinate(lat)]];
}

function normalizeLineCoordinates(feature) {
  const rawCoordinates = Array.isArray(feature.coordinates)
    ? feature.coordinates
    : feature?.geometry?.type === "LineString"
      ? feature.geometry.coordinates
      : feature?.geometry?.type === "MultiLineString"
        ? feature.geometry.coordinates[0]
        : [];

  return rawCoordinates.map(normalizeCoordinatePair).filter(Boolean);
}

function normalizePolygonCoordinates(feature) {
  const rawCoordinates = Array.isArray(feature.coordinates)
    ? feature.coordinates
    : feature?.geometry?.type === "Polygon"
      ? feature.geometry.coordinates[0]
      : feature?.geometry?.type === "MultiPolygon"
        ? feature.geometry.coordinates[0]?.[0] ?? []
        : [];

  return stripClosedPolygonRing(rawCoordinates.map(normalizeCoordinatePair).filter(Boolean));
}

function normalizeFeatureCoordinates(feature, geometryType) {
  switch (geometryType) {
    case "line":
      return normalizeLineCoordinates(feature);
    case "polygon":
      return normalizePolygonCoordinates(feature);
    case "point":
    default:
      return normalizePointCoordinates(feature);
  }
}

export function resolveStudentGeometryType(value) {
  return STUDENT_GEOMETRY_META[value] ? value : "point";
}

export function isStudentGeometryType(value) {
  return Boolean(STUDENT_GEOMETRY_META[value]);
}

export function getStudentGeometryMeta(value) {
  return STUDENT_GEOMETRY_META[resolveStudentGeometryType(value)];
}

export function getStudentGeometryLabel(value) {
  return getStudentGeometryMeta(value).label;
}

export function getMinimumStudentGeometryPoints(value) {
  return getStudentGeometryMeta(value).minimumPoints;
}

export function normalizeStudentFeature(feature, fallbackGeometryType = "point") {
  const geometryType = resolveStudentGeometryType(
    feature?.geometryType ?? inferGeometryTypeFromFeature(feature) ?? fallbackGeometryType,
  );
  const coordinates = normalizeFeatureCoordinates(feature ?? {}, geometryType);
  if (coordinates.length < getMinimumStudentGeometryPoints(geometryType)) {
    return null;
  }

  return {
    id: feature.id ?? null,
    title: feature.title ?? feature.name ?? "조사 객체",
    note: feature.note ?? feature.description ?? "",
    geometryType,
    coordinates,
    createdAt: feature.createdAt ?? new Date().toISOString(),
    properties: feature.properties ?? {},
  };
}

export function getStudentLayerGeometryType(layer) {
  const featureGeometryTypes = new Set(
    (layer?.features ?? [])
      .map((feature) => feature?.geometryType)
      .filter(Boolean),
  );

  if (featureGeometryTypes.size === 1) {
    return [...featureGeometryTypes][0];
  }

  if (featureGeometryTypes.size > 1) {
    return "mixed";
  }

  return layer?.geometryType && STUDENT_LAYER_GEOMETRY_LABEL[layer.geometryType]
    ? layer.geometryType
    : "mixed";
}

export function getStudentLayerGeometryLabel(layer) {
  return STUDENT_LAYER_GEOMETRY_LABEL[getStudentLayerGeometryType(layer)] ?? "혼합";
}

export function normalizeStudentLayer(layer) {
  const normalizedFeatures = Array.isArray(layer.features)
    ? layer.features
        .map((feature, index) => {
          const normalizedFeature = normalizeStudentFeature(
            feature,
            inferGeometryTypeFromFeature(feature) ?? "point",
          );
          if (!normalizedFeature) {
            return null;
          }

          return {
            ...normalizedFeature,
            id: feature.id ?? `${layer.id ?? "student-layer"}-feature-${index + 1}`,
          };
        })
        .filter(Boolean)
    : [];

  const normalizedLayer = {
    id: layer.id ?? "student-layer",
    name: layer.name ?? "학생 레이어",
    geometryType: layer.geometryType ?? "mixed",
    color: layer.color ?? "#d94862",
    opacity: Number.isFinite(Number(layer.opacity)) ? Number(layer.opacity) : 1,
    description: layer.description ?? "",
    visible: layer.visible !== false,
    source: layer.source ?? "manual",
    createdAt: layer.createdAt ?? new Date().toISOString(),
    features: normalizedFeatures,
  };

  return {
    ...normalizedLayer,
    geometryType: getStudentLayerGeometryType(normalizedLayer),
  };
}

export function buildStudentFeatureGeometry(feature) {
  if (!feature) {
    return null;
  }

  switch (resolveStudentGeometryType(feature.geometryType)) {
    case "line":
      return {
        type: "LineString",
        coordinates: feature.coordinates,
      };
    case "polygon": {
      const closedRing = [...feature.coordinates];
      if (closedRing.length) {
        closedRing.push(closedRing[0]);
      }
      return {
        type: "Polygon",
        coordinates: [closedRing],
      };
    }
    case "point":
    default:
      return {
        type: "Point",
        coordinates: feature.coordinates[0],
      };
  }
}

export function buildStudentLayerFeatureCollection(layer) {
  return {
    type: "FeatureCollection",
    features: layer.features.map((feature) => ({
      type: "Feature",
      geometry: buildStudentFeatureGeometry(feature),
      properties: {
        featureId: feature.id,
        featureGeometryType: feature.geometryType,
        layerId: layer.id,
        layerName: layer.name,
        layerDescription: layer.description,
        layerGeometryType: getStudentLayerGeometryType(layer),
        title: feature.title,
        note: feature.note,
        source: layer.source,
        ...feature.properties,
      },
    })),
  };
}

export function getStudentFeatureCoordinates(feature) {
  if (!feature) {
    return [];
  }

  switch (resolveStudentGeometryType(feature.geometryType)) {
    case "line":
    case "polygon":
      return feature.coordinates
        .filter(isValidCoordinatePair)
        .map(([lng, lat]) => [lat, lng]);
    case "point":
    default:
      return feature.coordinates
        .slice(0, 1)
        .filter(isValidCoordinatePair)
        .map(([lng, lat]) => [lat, lng]);
  }
}

export function getStudentLayerCoordinates(layer) {
  return layer.features.flatMap(getStudentFeatureCoordinates);
}
