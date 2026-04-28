const EARTH_RADIUS_METERS = 6371008.8;

export const SUITABILITY_TEMPLATES = Object.freeze([
  {
    id: "access",
    label: "접근성 좋은 곳",
    description: "선택한 학생 레이어와 가까운 격자를 높게 평가합니다.",
    publicDirection: "high",
    nearWeight: 45,
    farWeight: 0,
    publicWeight: 55,
  },
  {
    id: "crowded",
    label: "사람이 많은 곳",
    description: "SGIS 통계값이 높은 격자를 중심으로 후보지를 찾습니다.",
    publicDirection: "high",
    nearWeight: 20,
    farWeight: 0,
    publicWeight: 80,
  },
  {
    id: "quiet",
    label: "조용한 곳",
    description: "통계값이 낮고 조사 지점과 멀리 떨어진 격자를 높게 평가합니다.",
    publicDirection: "low",
    nearWeight: 0,
    farWeight: 45,
    publicWeight: 55,
  },
  {
    id: "facility-gap",
    label: "시설이 부족한 곳",
    description: "통계값이 낮고 기존 시설 또는 조사 지점에서 먼 격자를 찾습니다.",
    publicDirection: "low",
    nearWeight: 0,
    farWeight: 55,
    publicWeight: 45,
  },
  {
    id: "custom",
    label: "내가 직접 정하기",
    description: "조건 가중치를 직접 조절해 입지점수를 계산합니다.",
    publicDirection: "high",
    nearWeight: 30,
    farWeight: 0,
    publicWeight: 70,
  },
]);

const templateMap = new Map(SUITABILITY_TEMPLATES.map((template) => [template.id, template]));

function toRadians(value) {
  return (Number(value) * Math.PI) / 180;
}

function formatNumber(value, digits = 0) {
  return Number(value).toLocaleString("ko-KR", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

function distanceMeters(left, right) {
  const lat1 = toRadians(left.lat);
  const lat2 = toRadians(right.lat);
  const deltaLat = lat2 - lat1;
  const deltaLng = toRadians(right.lng - left.lng);
  const a = Math.sin(deltaLat / 2) ** 2
    + Math.cos(lat1) * Math.cos(lat2) * Math.sin(deltaLng / 2) ** 2;
  return 2 * EARTH_RADIUS_METERS * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

function clamp(value, min, max) {
  const numericValue = Number(value);
  if (!Number.isFinite(numericValue)) {
    return min;
  }
  return Math.min(max, Math.max(min, numericValue));
}

function flattenCoordinates(coordinates, output = []) {
  if (!Array.isArray(coordinates)) {
    return output;
  }

  if (
    coordinates.length >= 2
    && Number.isFinite(Number(coordinates[0]))
    && Number.isFinite(Number(coordinates[1]))
  ) {
    output.push({
      lng: Number(coordinates[0]),
      lat: Number(coordinates[1]),
    });
    return output;
  }

  coordinates.forEach((item) => flattenCoordinates(item, output));
  return output;
}

function getGeometryCenter(geometry) {
  const points = flattenCoordinates(geometry?.coordinates);
  if (!points.length) {
    return null;
  }

  return {
    lat: points.reduce((total, point) => total + point.lat, 0) / points.length,
    lng: points.reduce((total, point) => total + point.lng, 0) / points.length,
  };
}

function getStudentFeaturePoints(feature) {
  return (feature?.coordinates ?? [])
    .filter((coordinate) =>
      Array.isArray(coordinate)
      && coordinate.length >= 2
      && Number.isFinite(Number(coordinate[0]))
      && Number.isFinite(Number(coordinate[1])))
    .map(([lng, lat]) => ({
      lng: Number(lng),
      lat: Number(lat),
    }));
}

function getNearestDistanceMeters(center, studentLayer) {
  const points = (studentLayer?.features ?? []).flatMap(getStudentFeaturePoints);
  if (!center || !points.length) {
    return null;
  }

  return Math.min(...points.map((point) => distanceMeters(center, point)));
}

function isGridFeature(feature) {
  const properties = feature?.properties ?? {};
  return Boolean(properties.isGridFeature || properties.gridLevelDiv || properties.gridCode);
}

function getGridFeatures(layer) {
  return (layer?.featureCollection?.features ?? []).filter((feature) => feature?.geometry && isGridFeature(feature));
}

function isGridLayer(layer) {
  return getGridFeatures(layer).length > 0;
}

function getMetricLabel(layer) {
  const feature = (layer?.featureCollection?.features ?? []).find((item) =>
    item?.properties?.metricLabel);
  return String(feature?.properties?.metricLabel ?? "통계값");
}

function getMetricYear(layer) {
  const feature = (layer?.featureCollection?.features ?? []).find((item) =>
    item?.properties?.metricYear);
  return String(feature?.properties?.metricYear ?? "");
}

function getMetricUnit(layer) {
  const feature = (layer?.featureCollection?.features ?? []).find((item) =>
    item?.properties?.metricUnit !== undefined);
  return String(feature?.properties?.metricUnit ?? "");
}

function normalizeScore(value, values, direction) {
  if (!Number.isFinite(value) || !values.length) {
    return null;
  }

  const min = Math.min(...values);
  const max = Math.max(...values);
  if (max === min) {
    return 50;
  }

  const ratio = (value - min) / (max - min);
  const directedRatio = direction === "low" ? 1 - ratio : ratio;
  return Math.round(clamp(directedRatio * 100, 0, 100));
}

function normalizeWeights(weights, template) {
  return {
    publicWeight: clamp(weights?.publicWeight ?? template.publicWeight, 0, 100),
    nearWeight: clamp(weights?.nearWeight ?? template.nearWeight, 0, 100),
    farWeight: clamp(weights?.farWeight ?? template.farWeight, 0, 100),
  };
}

function scoreColor(score) {
  const safeScore = clamp(score, 0, 100);
  if (safeScore >= 80) {
    return "#1f8f63";
  }
  if (safeScore >= 60) {
    return "#66a85a";
  }
  if (safeScore >= 40) {
    return "#f0c25a";
  }
  if (safeScore >= 20) {
    return "#df8f45";
  }
  return "#c8514f";
}

function buildCriteria(records, {
  template,
  weights,
  metricLabel,
  studentLayer,
}) {
  const metricValues = records
    .map((record) => record.baseMetricValue)
    .filter(Number.isFinite);
  const distanceValues = records
    .map((record) => record.nearestDistanceMeters)
    .filter(Number.isFinite);

  return records.map((record) => {
    const criteria = [];

    const publicScore = normalizeScore(record.baseMetricValue, metricValues, template.publicDirection);
    if (publicScore !== null && weights.publicWeight > 0) {
      criteria.push({
        id: "public-metric",
        label: `${metricLabel} ${template.publicDirection === "low" ? "낮을수록" : "높을수록"}`,
        score: publicScore,
        weight: weights.publicWeight,
        rawLabel: `${formatNumber(record.baseMetricValue, 0)}`,
      });
    }

    const nearScore = normalizeScore(record.nearestDistanceMeters, distanceValues, "low");
    if (nearScore !== null && weights.nearWeight > 0 && studentLayer) {
      criteria.push({
        id: "near-student-layer",
        label: `${studentLayer.name} 가까울수록`,
        score: nearScore,
        weight: weights.nearWeight,
        rawLabel: `${formatNumber(record.nearestDistanceMeters, 0)}m`,
      });
    }

    const farScore = normalizeScore(record.nearestDistanceMeters, distanceValues, "high");
    if (farScore !== null && weights.farWeight > 0 && studentLayer) {
      criteria.push({
        id: "far-student-layer",
        label: `${studentLayer.name} 멀수록`,
        score: farScore,
        weight: weights.farWeight,
        rawLabel: `${formatNumber(record.nearestDistanceMeters, 0)}m`,
      });
    }

    return {
      ...record,
      criteria,
    };
  });
}

function calculateWeightedScore(criteria) {
  const weightTotal = criteria.reduce((total, criterion) => total + criterion.weight, 0);
  if (weightTotal <= 0) {
    return null;
  }

  const score = criteria.reduce((total, criterion) => total + criterion.score * criterion.weight, 0) / weightTotal;
  return Math.round(clamp(score, 0, 100));
}

function buildContributionText(criteria) {
  return criteria
    .slice()
    .sort((left, right) => (right.score * right.weight) - (left.score * left.weight))
    .slice(0, 2)
    .map((criterion) => `${criterion.label} ${criterion.score}점`)
    .join(" · ");
}

function copyFeatureWithScore(record, rank, {
  template,
  metricLabel,
  metricUnit,
  metricYear,
}) {
  const score = record.score ?? 0;
  const contributionText = buildContributionText(record.criteria);
  const originalProperties = record.feature.properties ?? {};

  return {
    ...record.feature,
    properties: {
      ...originalProperties,
      title: `${originalProperties.title ?? originalProperties.gridCode ?? "격자"} · 입지점수 ${score}점`,
      note: contributionText
        ? `입지점수 ${score}점. 주요 조건: ${contributionText}`
        : `입지점수 ${score}점`,
      analysisType: "suitability",
      isSuitabilityFeature: true,
      suitabilityTemplateId: template.id,
      suitabilityTemplateLabel: template.label,
      suitabilityScore: score,
      suitabilityRank: rank,
      suitabilityContributionText: contributionText,
      baseMetricLabel: metricLabel,
      baseMetricValue: record.baseMetricValue ?? null,
      nearestStudentDistanceMeters: record.nearestDistanceMeters ?? null,
      criteriaScores: record.criteria,
      metricId: "suitability_score",
      metricLabel: "입지점수",
      metricValue: score,
      metricUnit: "점",
      metricDigits: 0,
      metricYear,
      metricSourceLabel: `${metricLabel}${metricUnit ? ` (${metricUnit})` : ""} + 학생 레이어 중첩`,
      __style: {
        color: "#12382f",
        weight: originalProperties.gridLevelDiv === "100m" ? 0.7 : 1.1,
        opacity: 0.88,
        fillColor: scoreColor(score),
        fillOpacity: 0.58,
      },
    },
  };
}

function buildTopCandidates(scoredRecords) {
  return scoredRecords
    .filter((record) => Number.isFinite(record.score))
    .slice()
    .sort((left, right) => right.score - left.score)
    .slice(0, 3)
    .map((record, index) => ({
      rank: index + 1,
      title: String(record.feature.properties?.gridCode || record.feature.properties?.title || `후보 격자 ${index + 1}`),
      score: record.score,
      reason: buildContributionText(record.criteria) || "조건 점수 합산",
    }));
}

export function getSuitabilityTemplate(templateId) {
  return templateMap.get(templateId) ?? SUITABILITY_TEMPLATES[0];
}

export function getSuitabilityGridLayers(importedPublicLayers) {
  return (importedPublicLayers ?? []).filter(isGridLayer);
}

export function buildSuitabilityPanelViewModel({
  importedPublicLayers,
  studentLayers,
  selectedTemplateId,
  selectedGridLayerId,
  selectedStudentLayerId,
  weights,
  latestSuitabilityLayer,
}) {
  const gridLayers = getSuitabilityGridLayers(importedPublicLayers);
  const template = getSuitabilityTemplate(selectedTemplateId);
  const normalizedWeights = normalizeWeights(weights, template);
  const selectedGridLayer = gridLayers.find((layer) => layer.id === selectedGridLayerId)
    ?? gridLayers[0]
    ?? null;
  const selectableStudentLayers = (studentLayers ?? []).filter((layer) => layer.features?.length);
  const selectedStudentLayer = selectableStudentLayers.find((layer) => layer.id === selectedStudentLayerId)
    ?? selectableStudentLayers[0]
    ?? null;

  return {
    templates: SUITABILITY_TEMPLATES,
    selectedTemplateId: template.id,
    selectedTemplateDescription: template.description,
    weights: normalizedWeights,
    gridLayers: gridLayers.map((layer) => ({
      id: layer.id,
      name: layer.name,
      featureCount: getGridFeatures(layer).length,
      metricLabel: getMetricLabel(layer),
    })),
    selectedGridLayerId: selectedGridLayer?.id ?? "",
    studentLayers: selectableStudentLayers.map((layer) => ({
      id: layer.id,
      name: layer.name,
      featureCount: layer.features.length,
    })),
    selectedStudentLayerId: selectedStudentLayer?.id ?? "",
    canCreate: Boolean(selectedGridLayer),
    emptyReason: selectedGridLayer
      ? ""
      : "먼저 SGIS 격자 레이어를 추가해야 입지점수를 계산할 수 있습니다.",
    latestResult: latestSuitabilityLayer
      ? {
          name: latestSuitabilityLayer.name,
          topCandidates: latestSuitabilityLayer.topCandidates ?? [],
        }
      : null,
  };
}

export function createSuitabilityAnalysisLayer({
  idFactory,
  gridLayer,
  studentLayer = null,
  templateId,
  weights,
  color = "#238b68",
  scope = "both",
}) {
  const template = getSuitabilityTemplate(templateId);
  const gridFeatures = getGridFeatures(gridLayer);
  if (!gridFeatures.length) {
    throw new Error("입지점수를 계산할 SGIS 격자 레이어가 없습니다.");
  }

  const metricLabel = getMetricLabel(gridLayer);
  const metricYear = getMetricYear(gridLayer);
  const metricUnit = getMetricUnit(gridLayer);
  const normalizedWeights = normalizeWeights(weights, template);
  const records = gridFeatures.map((feature, index) => {
    const center = getGeometryCenter(feature.geometry);
    return {
      feature,
      index,
      center,
      baseMetricValue: Number(feature.properties?.metricValue),
      nearestDistanceMeters: getNearestDistanceMeters(center, studentLayer),
    };
  });
  const recordsWithCriteria = buildCriteria(records, {
    template,
    weights: normalizedWeights,
    metricLabel,
    studentLayer,
  }).map((record) => ({
    ...record,
    score: calculateWeightedScore(record.criteria),
  }));

  const scoredRecords = recordsWithCriteria.filter((record) => Number.isFinite(record.score));
  if (!scoredRecords.length) {
    throw new Error("계산에 사용할 통계값이나 학생 레이어 거리가 없습니다. 다른 격자 레이어나 조건을 선택해 주세요.");
  }

  const rankedRecords = recordsWithCriteria
    .slice()
    .sort((left, right) => (right.score ?? -1) - (left.score ?? -1));
  const topCandidates = buildTopCandidates(rankedRecords);
  const rankedFeatureByOriginalIndex = new Map(
    rankedRecords.map((record, rankIndex) => [record.index, { record, rank: rankIndex + 1 }]),
  );

  return {
    id: idFactory("analysis-suitability"),
    name: `${template.label} 입지점수`,
    description: `${gridLayer.name} 격자를 기준으로 ${template.label} 조건을 0~100점으로 계산한 분석 레이어입니다.`,
    color,
    opacity: 0.82,
    visible: true,
    scope,
    sourceKind: "analysis",
    sourceLabel: "격자 입지점수",
    analysisType: "suitability",
    createdAt: new Date().toISOString(),
    suitabilityAnalysis: {
      templateId: template.id,
      templateLabel: template.label,
      baseGridLayerId: gridLayer.id,
      baseGridLayerName: gridLayer.name,
      studentLayerId: studentLayer?.id ?? "",
      studentLayerName: studentLayer?.name ?? "",
      metricLabel,
      metricYear,
      weights: normalizedWeights,
    },
    topCandidates,
    featureCollection: {
      type: "FeatureCollection",
      features: gridFeatures.map((feature, index) => {
        const ranked = rankedFeatureByOriginalIndex.get(index);
        return copyFeatureWithScore(ranked?.record ?? recordsWithCriteria[index], ranked?.rank ?? index + 1, {
          template,
          metricLabel,
          metricUnit,
          metricYear,
        });
      }),
    },
  };
}
