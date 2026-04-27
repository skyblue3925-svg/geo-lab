import {
  createId,
  getRandomLayerColor,
  parseCsvText,
} from "./layer-workspace-data.js";

const PUBLIC_LAYER_STORAGE_KEY = "school-neighborhood-gis-public-layers-v1";

function getPublicLayerStorageKey(storageScope = "default") {
  return `${PUBLIC_LAYER_STORAGE_KEY}:${storageScope}`;
}

function normalizeFeatureCollection(featureCollection) {
  if (
    !featureCollection
    || featureCollection.type !== "FeatureCollection"
    || !Array.isArray(featureCollection.features)
  ) {
    return { type: "FeatureCollection", features: [] };
  }

  return {
    type: "FeatureCollection",
    features: featureCollection.features.filter((feature) => feature?.geometry),
  };
}

export function normalizeImportedPublicLayer(layer) {
  return {
    id: layer.id ?? createId("public-layer"),
    name: layer.name ?? "공공 레이어",
    description: layer.description ?? "",
    color: layer.color ?? "#1d9bf0",
    opacity: Number.isFinite(Number(layer.opacity)) ? Number(layer.opacity) : 1,
    visible: layer.visible !== false,
    scope: layer.scope ?? "both",
    sourceKind: layer.sourceKind ?? "url",
    sourceLabel: layer.sourceLabel ?? "",
    analysisType: layer.analysisType ?? "",
    createdAt: layer.createdAt ?? new Date().toISOString(),
    measurementSummary: layer.measurementSummary ?? null,
    suitabilityAnalysis: layer.suitabilityAnalysis ?? null,
    topCandidates: Array.isArray(layer.topCandidates) ? layer.topCandidates : [],
    featureCollection: normalizeFeatureCollection(layer.featureCollection),
  };
}

export function loadImportedPublicLayers(storageScope = "default") {
  const raw = window.localStorage.getItem(getPublicLayerStorageKey(storageScope));
  if (!raw) {
    return [];
  }

  try {
    return JSON.parse(raw).map(normalizeImportedPublicLayer);
  } catch (error) {
    console.error("Failed to parse imported public layers.", error);
    return [];
  }
}

export function saveImportedPublicLayers(layers, storageScope = "default") {
  window.localStorage.setItem(
    getPublicLayerStorageKey(storageScope),
    JSON.stringify(layers),
  );
}

export function buildFeatureCollectionFromCsvRows(rows) {
  return {
    type: "FeatureCollection",
    features: rows
      .filter((row) => Number.isFinite(row.lat) && Number.isFinite(row.lng))
      .map((row) => ({
        type: "Feature",
        geometry: {
          type: "Point",
          coordinates: [row.lng, row.lat],
        },
        properties: {
          title: row.title,
          note: row.note,
          ...row.properties,
        },
      })),
  };
}

export function detectUrlLayerType(url, explicitType = "") {
  if (explicitType) {
    return explicitType;
  }

  const normalized = url.toLowerCase();
  if (normalized.endsWith(".csv")) {
    return "csv-url";
  }

  return "geojson-url";
}

function buildFeatureCollectionFromText(text, type, fallbackName) {
  if (type === "csv-url") {
    return buildFeatureCollectionFromCsvRows(parseCsvText(text));
  }

  const parsed = JSON.parse(text);
  if (parsed.type === "FeatureCollection") {
    return normalizeFeatureCollection(parsed);
  }

  if (parsed.type === "Feature") {
    return normalizeFeatureCollection({
      type: "FeatureCollection",
      features: [parsed],
    });
  }

  throw new Error(`${fallbackName} 레이어를 GeoJSON으로 해석하지 못했습니다.`);
}

export async function importPublicLayerFromUrl({
  name,
  description,
  color,
  scope,
  url,
  sourceKind = "url",
  type = "",
}) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`레이어 URL 응답이 실패했습니다 (${response.status}).`);
  }

  const text = await response.text();
  const resolvedType = detectUrlLayerType(url, type);
  const featureCollection = buildFeatureCollectionFromText(text, resolvedType, name);
  if (!featureCollection.features.length) {
    throw new Error("가져온 레이어에 표시 가능한 객체가 없습니다.");
  }

  return normalizeImportedPublicLayer({
    id: createId("public-layer"),
    name,
    description,
    color,
    visible: true,
    scope,
    sourceKind,
    sourceLabel: url,
    featureCollection,
  });
}

export async function importPublicLayerFromPreset(preset, colorIndex) {
  return importPublicLayerFromUrl({
    name: preset.label,
    description: preset.description ?? "",
    color: preset.color ?? getRandomLayerColor(colorIndex),
    scope: preset.scope ?? "both",
    url: preset.url,
    type: preset.type ?? "",
    sourceKind: "preset",
  });
}

function extractCoordinatesFromGeometry(geometry, target) {
  if (!geometry) {
    return;
  }

  const { type, coordinates } = geometry;
  if (!coordinates) {
    return;
  }

  if (type === "Point") {
    target.push([coordinates[1], coordinates[0]]);
    return;
  }

  if (type === "MultiPoint" || type === "LineString") {
    coordinates.forEach((coordinate) => target.push([coordinate[1], coordinate[0]]));
    return;
  }

  if (type === "MultiLineString" || type === "Polygon") {
    coordinates.flat().forEach((coordinate) => target.push([coordinate[1], coordinate[0]]));
    return;
  }

  if (type === "MultiPolygon") {
    coordinates.flat(2).forEach((coordinate) => target.push([coordinate[1], coordinate[0]]));
  }
}

export function collectFeatureCollectionCoordinates(featureCollection) {
  const coordinates = [];
  normalizeFeatureCollection(featureCollection).features.forEach((feature) =>
    extractCoordinatesFromGeometry(feature.geometry, coordinates),
  );
  return coordinates;
}
