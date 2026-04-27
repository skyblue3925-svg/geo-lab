import {
  getMinimumStudentGeometryPoints,
  resolveStudentGeometryType,
} from "../domain/student-layer.js";

export const DRAW_TOOL_META = {
  select: { label: "선택", geometryType: null, mode: "selection" },
  point: { label: "점", geometryType: "point", mode: "feature" },
  line: { label: "선", geometryType: "line", mode: "feature" },
  polygon: { label: "면", geometryType: "polygon", mode: "feature" },
  "measure-line": {
    label: "거리",
    geometryType: "line",
    mode: "measurement",
    measurementKind: "distance",
  },
  "measure-area": {
    label: "면적",
    geometryType: "polygon",
    mode: "measurement",
    measurementKind: "area",
  },
  delete: { label: "삭제", geometryType: null, mode: "delete" },
};

export function resolveDrawTool(value) {
  return DRAW_TOOL_META[value] ? value : "select";
}

export function getDrawToolGeometryType(tool) {
  return DRAW_TOOL_META[resolveDrawTool(tool)].geometryType;
}

export function isGeometryDrawTool(tool) {
  return Boolean(getDrawToolGeometryType(tool));
}

export function isMeasurementTool(tool) {
  return DRAW_TOOL_META[resolveDrawTool(tool)]?.mode === "measurement";
}

export function isStudentFeatureDrawTool(tool) {
  return DRAW_TOOL_META[resolveDrawTool(tool)]?.mode === "feature";
}

export function getMeasurementKind(tool) {
  return DRAW_TOOL_META[resolveDrawTool(tool)]?.measurementKind ?? null;
}

export function createDraftGeometry(geometryType) {
  return {
    geometryType: resolveStudentGeometryType(geometryType),
    points: [],
  };
}

export function appendPointToDraftGeometry(draftGeometry, latlng) {
  const nextDraft = draftGeometry
    ? {
        geometryType: resolveStudentGeometryType(draftGeometry.geometryType),
        points: [...draftGeometry.points],
      }
    : createDraftGeometry("point");

  nextDraft.points.push({
    lat: Number(latlng.lat),
    lng: Number(latlng.lng),
  });

  return nextDraft;
}

export function removeLastDraftPoint(draftGeometry) {
  if (!draftGeometry) {
    return null;
  }

  return {
    ...draftGeometry,
    points: draftGeometry.points.slice(0, -1),
  };
}

export function canCompleteDraftGeometry(draftGeometry) {
  if (!draftGeometry) {
    return false;
  }

  return draftGeometry.points.length >= getMinimumStudentGeometryPoints(draftGeometry.geometryType);
}

export function getDraftGeometryPointCount(draftGeometry) {
  return draftGeometry?.points?.length ?? 0;
}
