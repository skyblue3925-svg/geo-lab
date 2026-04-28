import {
  getMinimumStudentGeometryPoints,
  getStudentGeometryLabel,
  normalizeStudentFeature,
  normalizeStudentLayer,
  resolveStudentGeometryType,
} from "../domain/student-layer.js";
import { buildFeatureMeasurementSummary } from "./measurement-use-cases.js";

export function createStudentLayer({
  idFactory,
  name,
  color,
  description,
  geometryType = "mixed",
  source = "manual",
}) {
  return normalizeStudentLayer({
    id: idFactory("student-layer"),
    name,
    color,
    description,
    geometryType,
    source,
    visible: true,
    features: [],
  });
}

function buildDraftCoordinates(geometryType, draftPoints) {
  return geometryType === "point"
    ? [draftPoints[0].lng, draftPoints[0].lat]
    : draftPoints.map((point) => [point.lng, point.lat]);
}

export function canFinalizeStudentDraftGeometry(geometryType, draftPoints) {
  const resolvedGeometryType = resolveStudentGeometryType(geometryType);
  if (draftPoints.length < getMinimumStudentGeometryPoints(resolvedGeometryType)) {
    return false;
  }

  return Boolean(
    normalizeStudentFeature(
      {
        geometryType: resolvedGeometryType,
        coordinates: buildDraftCoordinates(resolvedGeometryType, draftPoints),
      },
      resolvedGeometryType,
    ),
  );
}

export function buildStudentFeatureFromDraft({
  idFactory,
  layer,
  geometryType,
  draftPoints,
  title,
  note,
  properties = {},
}) {
  const resolvedGeometryType = resolveStudentGeometryType(geometryType);
  if (!canFinalizeStudentDraftGeometry(resolvedGeometryType, draftPoints)) {
    throw new Error(`${getStudentGeometryLabel(resolvedGeometryType)} 도형을 완성하기 위한 점이 부족합니다.`);
  }

  const autoTitle = `${layer.name} ${layer.features.length + 1}`;
  const coordinates = buildDraftCoordinates(resolvedGeometryType, draftPoints);
  const feature = normalizeStudentFeature(
    {
      id: idFactory("student-feature"),
      title: title || autoTitle,
      note,
      geometryType: resolvedGeometryType,
      coordinates,
      properties: {
        ...properties,
      },
    },
    resolvedGeometryType,
  );

  if (!feature) {
    throw new Error(`${getStudentGeometryLabel(resolvedGeometryType)} 도형을 만들 수 없습니다. 점을 다시 확인해 주세요.`);
  }

  const measurementSummary = buildFeatureMeasurementSummary(feature);
  if (measurementSummary) {
    feature.properties = {
      ...feature.properties,
      ...measurementSummary,
    };
  }

  return feature;
}

export function getStudentDraftStatus(geometryType, draftPoints) {
  const resolvedGeometryType = resolveStudentGeometryType(geometryType);
  const count = draftPoints.length;
  const minimumPoints = getMinimumStudentGeometryPoints(resolvedGeometryType);

  if (resolvedGeometryType === "point") {
    return "지도에서 한 번 누르면 점 객체가 바로 추가됩니다.";
  }

  if (!count) {
    return `${getStudentGeometryLabel(resolvedGeometryType)} 도형을 시작하려면 지도에 점을 먼저 찍어 주세요.`;
  }

  if (count < minimumPoints) {
    return `현재 ${count}개의 점을 기록했습니다. 최소 ${minimumPoints}개가 필요합니다.`;
  }

  if (!canFinalizeStudentDraftGeometry(resolvedGeometryType, draftPoints)) {
    return `현재 ${count}개의 점을 기록했습니다. 서로 다른 점을 더 추가해 도형을 완성해 주세요.`;
  }

  return `현재 ${count}개의 점을 기록했습니다. 완료를 누르면 ${getStudentGeometryLabel(resolvedGeometryType)} 객체가 저장됩니다.`;
}
