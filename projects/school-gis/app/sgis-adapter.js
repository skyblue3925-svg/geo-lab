import {
  createId,
  formatNumber,
  interpolateColor,
} from "./layer-workspace-data.js";
import { normalizeImportedPublicLayer } from "./public-layer-imports.js";

const proj4 = window.proj4;

const SGIS_PROJECTION = "EPSG:5179";
const WGS84_PROJECTION = "EPSG:4326";

if (!proj4) {
  throw new Error("proj4 is not available on window. Check local vendor asset loading.");
}

proj4.defs(
  SGIS_PROJECTION,
  "+proj=tmerc +lat_0=38 +lon_0=127.5 +k=0.9996 +x_0=1000000 +y_0=2000000 +ellps=GRS80 +units=m +no_defs",
);

export const SGIS_SUPPORTED_YEARS = Object.freeze([
  2015,
  2016,
  2017,
  2018,
  2019,
  2020,
  2021,
  2022,
  2023,
]);

export const SGIS_POPULATION_METRICS = Object.freeze([
  { id: "tot_ppltn", label: "총인구", unit: "명", digits: 0, statsResource: "population" },
  { id: "avg_age", label: "평균연령", unit: "세", digits: 1, statsResource: "population" },
  { id: "ppltn_dnsty", label: "인구밀도", unit: "명/km²", digits: 2, statsResource: "population" },
  { id: "aged_child_idx", label: "노령화지수", unit: "", digits: 1, statsResource: "population" },
  { id: "oldage_suprt_per", label: "노년부양비", unit: "", digits: 1, statsResource: "population" },
  { id: "juv_suprt_per", label: "유소년부양비", unit: "", digits: 1, statsResource: "population" },
  { id: "tot_family", label: "총가구", unit: "가구", digits: 0, statsResource: "population" },
  { id: "avg_fmember_cnt", label: "평균가구원수", unit: "명", digits: 1, statsResource: "population" },
  { id: "tot_house", label: "총주택", unit: "호", digits: 0, statsResource: "population" },
  { id: "nongga_cnt", label: "농가 수", unit: "가구", digits: 0, statsResource: "population", fixedYear: 2020 },
  { id: "nongga_ppltn", label: "농가 인구", unit: "명", digits: 0, statsResource: "population", fixedYear: 2020 },
  { id: "imga_cnt", label: "임가 수", unit: "가구", digits: 0, statsResource: "population", fixedYear: 2020 },
  { id: "imga_ppltn", label: "임가 인구", unit: "명", digits: 0, statsResource: "population", fixedYear: 2020 },
  { id: "naesuoga_cnt", label: "내수면 어가 수", unit: "가구", digits: 0, statsResource: "population", fixedYear: 2020 },
  { id: "naesuoga_ppltn", label: "내수면 어가 인구", unit: "명", digits: 0, statsResource: "population", fixedYear: 2020 },
  { id: "haesuoga_cnt", label: "해수면 어가 수", unit: "가구", digits: 0, statsResource: "population", fixedYear: 2020 },
  { id: "haesuoga_ppltn", label: "해수면 어가 인구", unit: "명", digits: 0, statsResource: "population", fixedYear: 2020 },
  { id: "corp_cnt", label: "사업체 수", unit: "개", digits: 0, statsResource: "population" },
  { id: "employee_cnt", label: "종업원 수", unit: "명", digits: 0, statsResource: "population" },
  { id: "household_cnt", label: "가구 수", unit: "가구", digits: 0, statsResource: "household" },
  { id: "family_member_cnt", label: "가구원 수", unit: "명", digits: 0, statsResource: "household" },
  { id: "avg_family_member_cnt", label: "가구당 평균인원", unit: "명", digits: 1, statsResource: "household" },
  { id: "house_cnt", label: "주택 수", unit: "호", digits: 0, statsResource: "house" },
]);

const metricMap = new Map(SGIS_POPULATION_METRICS.map((metric) => [metric.id, metric]));

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function buildSgisProxyUrl(proxyPath, resourcePath, query) {
  const requestUrl = new URL(
    `${proxyPath.replace(/\/$/, "")}/${resourcePath.replace(/^\//, "")}`,
    window.location.origin,
  );

  Object.entries(query).forEach(([key, value]) => {
    if (value === null || value === undefined || value === "") {
      return;
    }
    requestUrl.searchParams.set(key, String(value));
  });

  return requestUrl;
}

function normalizeCoordinateTree(value) {
  if (!Array.isArray(value)) {
    return value;
  }

  if (
    value.length >= 2
    && typeof value[0] === "number"
    && typeof value[1] === "number"
  ) {
    return proj4(SGIS_PROJECTION, WGS84_PROJECTION, value);
  }

  return value.map((item) => normalizeCoordinateTree(item));
}

function transformSgisFeatureCollection(featureCollection) {
  return {
    type: "FeatureCollection",
    features: (featureCollection?.features ?? [])
      .filter((feature) => feature?.geometry)
      .map((feature) => ({
        ...feature,
        geometry: {
          ...feature.geometry,
          coordinates: normalizeCoordinateTree(feature.geometry.coordinates),
        },
      })),
  };
}

function toNumericValue(value) {
  if (value === null || value === undefined || value === "" || value === "N/A") {
    return null;
  }

  const numericValue = Number(value);
  return Number.isFinite(numericValue) ? numericValue : null;
}

function buildMetricRange(rows, metricId) {
  const values = rows
    .map((row) => toNumericValue(row?.[metricId]))
    .filter((value) => value !== null);

  if (!values.length) {
    return { min: 0, max: 1 };
  }

  return {
    min: Math.min(...values),
    max: Math.max(...values),
  };
}

function buildStatsByAdmCd(rows) {
  return new Map(rows.map((row) => [String(row.adm_cd ?? "").trim(), row]));
}

function findBestStatsRow(statsByAdmCd, admCd) {
  const normalizedAdmCd = String(admCd ?? "").trim();
  if (!normalizedAdmCd) {
    return null;
  }

  const exact = statsByAdmCd.get(normalizedAdmCd);
  if (exact) {
    return exact;
  }

  const sortedCodes = [...statsByAdmCd.keys()]
    .filter(Boolean)
    .sort((left, right) => right.length - left.length);

  return sortedCodes
    .map((code) => ({
      code,
      row: statsByAdmCd.get(code),
    }))
    .find(({ code }) =>
      normalizedAdmCd.startsWith(code) || code.startsWith(normalizedAdmCd))?.row ?? null;
}

function normalizeSpatialFilter(spatialFilter) {
  const lat = Number(spatialFilter?.center?.lat);
  const lng = Number(spatialFilter?.center?.lng);
  const radiusMeters = Number(spatialFilter?.radiusMeters);
  if (!Number.isFinite(lat) || !Number.isFinite(lng) || !Number.isFinite(radiusMeters) || radiusMeters <= 0) {
    return null;
  }

  return {
    center: { lat, lng },
    radiusMeters,
  };
}

function toRadians(value) {
  return (Number(value) * Math.PI) / 180;
}

function calculateDistanceMeters(left, right) {
  const earthRadiusMeters = 6371000;
  const dLat = toRadians(right.lat - left.lat);
  const dLng = toRadians(right.lng - left.lng);
  const lat1 = toRadians(left.lat);
  const lat2 = toRadians(right.lat);
  const a = Math.sin(dLat / 2) ** 2
    + Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLng / 2) ** 2;
  return 2 * earthRadiusMeters * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

function visitGeometryCoordinates(value, visitor) {
  if (!Array.isArray(value)) {
    return;
  }

  if (
    value.length >= 2
    && typeof value[0] === "number"
    && typeof value[1] === "number"
  ) {
    visitor({ lng: value[0], lat: value[1] });
    return;
  }

  value.forEach((item) => visitGeometryCoordinates(item, visitor));
}

function collectGeometryPoints(geometry) {
  const points = [];
  visitGeometryCoordinates(geometry?.coordinates, (point) => {
    if (Number.isFinite(point.lat) && Number.isFinite(point.lng)) {
      points.push(point);
    }
  });
  return points;
}

function getGeometryCentroid(geometry) {
  const points = collectGeometryPoints(geometry);
  if (!points.length) {
    return null;
  }

  const total = points.reduce(
    (sum, point) => ({
      lat: sum.lat + point.lat,
      lng: sum.lng + point.lng,
    }),
    { lat: 0, lng: 0 },
  );

  return {
    lat: total.lat / points.length,
    lng: total.lng / points.length,
  };
}

function pointInRing(point, ring) {
  let inside = false;
  for (let index = 0, previousIndex = ring.length - 1; index < ring.length; previousIndex = index, index += 1) {
    const current = ring[index];
    const previous = ring[previousIndex];
    const currentLng = Number(current?.[0]);
    const currentLat = Number(current?.[1]);
    const previousLng = Number(previous?.[0]);
    const previousLat = Number(previous?.[1]);
    const intersects = currentLat > point.lat !== previousLat > point.lat
      && point.lng
        < ((previousLng - currentLng) * (point.lat - currentLat)) / (previousLat - currentLat)
          + currentLng;
    if (intersects) {
      inside = !inside;
    }
  }
  return inside;
}

function polygonContainsPoint(point, polygonCoordinates) {
  const rings = Array.isArray(polygonCoordinates) ? polygonCoordinates : [];
  if (!rings.length || !pointInRing(point, rings[0])) {
    return false;
  }

  return !rings.slice(1).some((ring) => pointInRing(point, ring));
}

function geometryContainsPoint(geometry, point) {
  if (geometry?.type === "Polygon") {
    return polygonContainsPoint(point, geometry.coordinates);
  }

  if (geometry?.type === "MultiPolygon") {
    return (geometry.coordinates ?? []).some((polygonCoordinates) =>
      polygonContainsPoint(point, polygonCoordinates));
  }

  return false;
}

function getFeatureDistanceToCenter(feature, center) {
  if (geometryContainsPoint(feature.geometry, center)) {
    return 0;
  }

  const points = collectGeometryPoints(feature.geometry);
  const centroid = getGeometryCentroid(feature.geometry);
  const candidates = centroid ? [...points, centroid] : points;
  if (!candidates.length) {
    return Number.POSITIVE_INFINITY;
  }

  return Math.min(...candidates.map((point) => calculateDistanceMeters(center, point)));
}

function filterFeatureCollectionBySpatialFilter(featureCollection, spatialFilter) {
  const filter = normalizeSpatialFilter(spatialFilter);
  if (!filter) {
    return featureCollection;
  }

  const featuresWithDistance = (featureCollection.features ?? [])
    .map((feature) => ({
      feature,
      distance: getFeatureDistanceToCenter(feature, filter.center),
    }))
    .filter(({ distance }) => Number.isFinite(distance))
    .sort((left, right) => left.distance - right.distance);

  const filteredFeatures = featuresWithDistance
    .filter(({ distance }) => distance <= filter.radiusMeters)
    .map(({ feature }) => feature);

  return {
    ...featureCollection,
    features: filteredFeatures.length
      ? filteredFeatures
      : featuresWithDistance.slice(0, 1).map(({ feature }) => feature),
  };
}

function buildFeatureStyle(metricValue, range, layerColor) {
  if (metricValue === null) {
    return {
      color: "#9fb3c1",
      weight: 1.4,
      opacity: 0.85,
      fillColor: "#dce7ee",
      fillOpacity: 0.2,
    };
  }

  const denominator = Math.max(1, range.max - range.min);
  const ratio = clamp((metricValue - range.min) / denominator, 0, 1);

  return {
    color: interpolateColor("#9cb4c6", layerColor, Math.max(0.22, ratio)),
    weight: 1.5,
    opacity: 0.95,
    fillColor: interpolateColor("#edf4f8", layerColor, ratio),
    fillOpacity: 0.52,
  };
}

function buildLayerName(metric, year, scopeLabel) {
  const normalizedScopeLabel = scopeLabel || "선택한 범위";
  return `SGIS ${metric.label} ${year} · ${normalizedScopeLabel}`;
}

function buildLayerDescription(metric, year, scopeLabel) {
  const normalizedScopeLabel = scopeLabel || "선택한 범위";
  return `SGIS ${metric.statsResource} API에서 ${normalizedScopeLabel}의 ${metric.label} 통계를 ${year}년 기준으로 불러온 레이어입니다.`;
}

function buildPopupNote(metric, metricValue, range) {
  if (metricValue === null) {
    return `${metric.label} 값이 없습니다.`;
  }

  return `${metric.label} ${formatNumber(metricValue, metric.digits)}${metric.unit} · 범위 ${formatNumber(range.min, metric.digits)} ~ ${formatNumber(range.max, metric.digits)}${metric.unit}`;
}

function normalizeMetric(metricId) {
  if (metricId === "tot_worker") {
    return metricMap.get("employee_cnt") ?? SGIS_POPULATION_METRICS[0];
  }

  return metricMap.get(metricId) ?? SGIS_POPULATION_METRICS[0];
}

function buildGridLayerName(gridLevelDiv, scopeLabel) {
  const normalizedScopeLabel = scopeLabel || "선택한 범위";
  return `SGIS ${gridLevelDiv} 격자 · ${normalizedScopeLabel}`;
}

function buildGridLayerDescription(gridLevelDiv, scopeLabel) {
  const normalizedScopeLabel = scopeLabel || "선택한 범위";
  return `SGIS 격자경계 API에서 ${normalizedScopeLabel}의 ${gridLevelDiv} 격자 경계와 격자코드를 불러온 레이어입니다.`;
}

function getGridCode(properties, gridLevelDiv) {
  const levelKey = String(gridLevelDiv ?? "").toUpperCase().replace("KM", "K");
  const candidates = [
    `GRID_${levelKey}`,
    `grid_${levelKey}`,
    "grid_cd",
    "gridCode",
    "adm_cd",
    "adm_nm",
  ];

  return candidates
    .map((key) => String(properties?.[key] ?? "").trim())
    .find(Boolean) ?? "";
}

function buildGridFeatureTitle(properties, gridLevelDiv, index) {
  const gridCode = getGridCode(properties, gridLevelDiv);
  if (gridCode) {
    return `${gridLevelDiv} 격자 ${gridCode}`;
  }
  return `${gridLevelDiv} 격자 ${index + 1}`;
}

function buildGridMetricSourceLabel(statRow) {
  const admName = String(statRow?.adm_nm ?? "").trim();
  const admCode = String(statRow?.adm_cd ?? "").trim();
  if (admName || admCode) {
    return `${admName || admCode} 행정구역 통계 결합`;
  }
  return "격자 경계 정보";
}

function buildGridPopupNote(metric, metricValue, range, statRow) {
  const metricNote = buildPopupNote(metric, metricValue, range);
  if (metricValue === null) {
    return `격자 경계와 격자코드를 표시합니다. ${metricNote}`;
  }

  return `${buildGridMetricSourceLabel(statRow)} · ${metricNote}`;
}

async function readJsonResponse(response) {
  const payload = await response.json().catch(() => ({}));

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error("SGIS 프록시 경로를 찾지 못했습니다. 로컬 서버가 `/api/sgis`를 제공하는 방식으로 실행 중인지 확인해 주세요.");
    }

    throw new Error(payload?.error ?? `SGIS proxy request failed (${response.status})`);
  }

  return payload;
}

export async function fetchSgisRegionCode({ proxyPath, lat, lng }) {
  const requestUrl = buildSgisProxyUrl(proxyPath, "region-code", { lat, lng });
  return readJsonResponse(await fetch(requestUrl.toString()));
}

export async function fetchSgisPopulationLayer({
  proxyPath,
  year,
  admCd,
  lowSearch,
  metricId,
  color,
  scope = "both",
  scopeLabel = "",
  spatialFilter = null,
}) {
  const metric = normalizeMetric(metricId);
  const effectiveYear = Number(metric.fixedYear ?? year);
  const requestUrl = buildSgisProxyUrl(proxyPath, "population", {
    year: effectiveYear,
    admCd,
    lowSearch,
    statsResource: metric.statsResource ?? "population",
  });

  const payload = await readJsonResponse(await fetch(requestUrl.toString()));
  const transformedBoundary = transformSgisFeatureCollection(payload.boundary);
  const statsRows = Array.isArray(payload.statsRows) ? payload.statsRows : [];
  const range = buildMetricRange(statsRows, metric.id);
  const statsByAdmCd = buildStatsByAdmCd(statsRows);

  const featureCollection = filterFeatureCollectionBySpatialFilter({
    type: "FeatureCollection",
    features: transformedBoundary.features.map((feature) => {
      const properties = feature.properties ?? {};
      const statRow = findBestStatsRow(statsByAdmCd, properties.adm_cd) ?? null;
      const metricValue = toNumericValue(statRow?.[metric.id]);
      const style = buildFeatureStyle(metricValue, range, color);

      return {
        ...feature,
        properties: {
          ...properties,
          title: properties.adm_nm ?? properties.name ?? "SGIS 통계 구역",
          note: buildPopupNote(metric, metricValue, range),
          metricId: metric.id,
          metricLabel: metric.label,
          metricUnit: metric.unit,
          metricDigits: metric.digits,
          metricValue,
          metricYear: String(effectiveYear),
          source: "SGIS",
          __style: style,
        },
      };
    }),
  }, spatialFilter);

  return normalizeImportedPublicLayer({
    id: createId("public-layer"),
    name: buildLayerName(metric, effectiveYear, scopeLabel),
    description: buildLayerDescription(metric, effectiveYear, scopeLabel),
    color,
    visible: true,
    scope,
    sourceKind: "sgis",
    sourceLabel: `SGIS ${metric.statsResource}.json + hadmarea.geojson`,
    featureCollection,
  });
}

export async function fetchSgisGridLayer({
  proxyPath,
  admCd,
  gridLevelDiv,
  year,
  metricId,
  statsAdmCd,
  statsLowSearch,
  color,
  scope = "both",
  scopeLabel = "",
  spatialFilter = null,
}) {
  const metric = normalizeMetric(metricId);
  const effectiveYear = Number(metric.fixedYear ?? year);
  const requestUrl = buildSgisProxyUrl(proxyPath, "grid", {
    admCd,
    gridLevelDiv,
  });

  const statsRequestUrl = buildSgisProxyUrl(proxyPath, "population", {
    year: effectiveYear,
    admCd: statsAdmCd ?? admCd,
    lowSearch: statsLowSearch ?? "1",
    statsResource: metric.statsResource ?? "population",
  });

  const [payload, statsPayload] = await Promise.all([
    readJsonResponse(await fetch(requestUrl.toString())),
    readJsonResponse(await fetch(statsRequestUrl.toString())),
  ]);
  const transformedBoundary = transformSgisFeatureCollection(payload.boundary);
  const statsRows = Array.isArray(statsPayload.statsRows) ? statsPayload.statsRows : [];
  const range = buildMetricRange(statsRows, metric.id);
  const statsByAdmCd = buildStatsByAdmCd(statsRows);

  const featureCollection = filterFeatureCollectionBySpatialFilter({
    type: "FeatureCollection",
    features: transformedBoundary.features.map((feature, index) => {
      const properties = feature.properties ?? {};
      const statRow = findBestStatsRow(statsByAdmCd, properties.adm_cd);
      const metricValue = toNumericValue(statRow?.[metric.id]);
      const gridCode = getGridCode(properties, gridLevelDiv);
      const style = metricValue === null
        ? {
            color,
            weight: gridLevelDiv === "100m" ? 0.7 : 1,
            opacity: 0.5,
            fillColor: "#dce7ee",
            fillOpacity: 0.04,
          }
        : {
            ...buildFeatureStyle(metricValue, range, color),
            weight: gridLevelDiv === "100m" ? 0.7 : 1.1,
            fillOpacity: 0.42,
          };
      return {
        ...feature,
        properties: {
          ...properties,
          title: buildGridFeatureTitle(properties, gridLevelDiv, index),
          note: buildGridPopupNote(metric, metricValue, range, statRow),
          isGridFeature: true,
          gridLevelDiv,
          gridSizeLabel: gridLevelDiv,
          gridCode,
          gridIndex: index + 1,
          metricId: metric.id,
          metricLabel: metric.label,
          metricUnit: metric.unit,
          metricDigits: metric.digits,
          metricValue,
          metricYear: String(effectiveYear),
          metricSourceLabel: buildGridMetricSourceLabel(statRow),
          joinedAdmCd: statRow?.adm_cd ?? "",
          joinedAdmNm: statRow?.adm_nm ?? "",
          source: "SGIS",
          __style: style,
        },
      };
    }),
  }, spatialFilter);

  return normalizeImportedPublicLayer({
    id: createId("public-layer"),
    name: `SGIS ${metric.label} ${effectiveYear} · ${gridLevelDiv} 격자`,
    description: `${buildGridLayerDescription(gridLevelDiv, scopeLabel)} ${metric.label} 값은 격자 속성에서 확인되는 경우 함께 표시합니다.`,
    color,
    visible: true,
    scope,
    sourceKind: "sgis",
    sourceLabel: "SGIS grid/data.geojson",
    featureCollection,
  });
}
