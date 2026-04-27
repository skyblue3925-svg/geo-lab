import {
  buildStudentLayerFeatureCollection,
  normalizeStudentFeature,
  normalizeStudentLayer,
} from "./domain/student-layer.js";

const STUDENT_LAYER_STORAGE_KEY = "school-neighborhood-gis-student-layers-v5";
const WORKSPACE_REFLECTION_STORAGE_KEY = "school-neighborhood-gis-reflection-v1";
const WORKSPACE_PROJECT_STORAGE_KEY = "school-neighborhood-gis-projects-v1";

function getStudentLayerStorageKey(storageScope = "default") {
  return `${STUDENT_LAYER_STORAGE_KEY}:${storageScope}`;
}

function getWorkspaceReflectionStorageKey(storageScope = "default") {
  return `${WORKSPACE_REFLECTION_STORAGE_KEY}:${storageScope}`;
}

function getWorkspaceProjectStorageKey(storageScope = "default") {
  return `${WORKSPACE_PROJECT_STORAGE_KEY}:${storageScope}`;
}

export function createId(prefix = "layer") {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return `${prefix}-${crypto.randomUUID()}`;
  }
  return `${prefix}-${Date.now()}-${Math.floor(Math.random() * 1000)}`;
}

export function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

export function formatNumber(value, digits = 0) {
  return new Intl.NumberFormat("ko-KR", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(value);
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function hexToRgb(hex) {
  const normalized = hex.replace("#", "");
  const intValue = Number.parseInt(normalized, 16);
  return {
    r: (intValue >> 16) & 255,
    g: (intValue >> 8) & 255,
    b: intValue & 255,
  };
}

function rgbToHex(red, green, blue) {
  return `#${[red, green, blue]
    .map((value) => clamp(Math.round(value), 0, 255).toString(16).padStart(2, "0"))
    .join("")}`;
}

export function interpolateColor(startHex, endHex, ratio) {
  const safeRatio = clamp(ratio, 0, 1);
  const start = hexToRgb(startHex);
  const end = hexToRgb(endHex);
  return rgbToHex(
    start.r + (end.r - start.r) * safeRatio,
    start.g + (end.g - start.g) * safeRatio,
    start.b + (end.b - start.b) * safeRatio,
  );
}

function offsetPoint(center, latOffset, lngOffset) {
  return {
    lat: center.lat + latOffset,
    lng: center.lng + lngOffset,
  };
}

export function buildLocalPublicLayers(center) {
  return [
    {
      id: "bus-stops",
      label: "버스정류장",
      color: "#ff9f1c",
      defaultVisible: false,
      description: "탐색 중심 주변 버스정류장을 예시로 보여 주는 레이어입니다.",
      items: [
        { id: "bus-1", name: "정문 앞 정류장", type: "정류장", note: "통학 시간대 탑승하차가 많은 지점", ...offsetPoint(center, 0.0016, -0.0022) },
        { id: "bus-2", name: "북문 연결 정류장", type: "정류장", note: "주거지 방향 이동축과 가까운 정류장", ...offsetPoint(center, -0.0023, 0.0014) },
        { id: "bus-3", name: "체육관 앞 정류장", type: "정류장", note: "보행 흐름과 차량 흐름을 함께 보기 좋은 지점", ...offsetPoint(center, 0.0034, 0.0027) },
      ],
    },
    {
      id: "safety-observation",
      label: "보행 관찰 지점",
      color: "#d94862",
      defaultVisible: false,
      description: "교차로 코너나 시야 취약 구간을 비교하기 좋은 예시 레이어입니다.",
      items: [
        { id: "safe-1", name: "정문 앞 횡단보도", type: "보행 안전", note: "차량 시야와 보행 대기 공간을 함께 보기 쉬운 지점", ...offsetPoint(center, 0.0007, 0.0016) },
        { id: "safe-2", name: "상원가 코너", type: "보행 안전", note: "방과 후 학생 이동이 몰리는 지점", ...offsetPoint(center, -0.0015, -0.0012) },
        { id: "safe-3", name: "골목 합류부", type: "보행 안전", note: "자전거와 차량 동선이 겹치는 구간", ...offsetPoint(center, -0.0032, 0.0006) },
      ],
    },
    {
      id: "rest-spots",
      label: "쉼터와 그늘",
      color: "#1d9bf0",
      defaultVisible: false,
      description: "체류 공간이나 쉼터 관찰과 비교하기 위한 예시 레이어입니다.",
      items: [
        { id: "rest-1", name: "작은 공원 쉼터", type: "쉼터", note: "벤치와 나무 그늘이 있는 공간", ...offsetPoint(center, 0.0028, -0.0008) },
        { id: "rest-2", name: "도서관 앞 그늘막", type: "그늘", note: "대기 공간과 연결된 휴식 지점", ...offsetPoint(center, -0.0008, 0.0024) },
        { id: "rest-3", name: "문화센터 앞 쉼터", type: "쉼터", note: "방과 후 체류 지점으로 비교 가능", ...offsetPoint(center, 0.0014, 0.0031) },
      ],
    },
  ];
}

function buildInitialStudentLayers() {
  return [];
}

export function loadStudentLayers(_center, storageScope = "default") {
  const storageKey = getStudentLayerStorageKey(storageScope);
  const raw = window.localStorage.getItem(storageKey);
  if (!raw) {
    const initialLayers = buildInitialStudentLayers().map(normalizeStudentLayer);
    saveStudentLayers(initialLayers, storageScope);
    return initialLayers;
  }

  try {
    return JSON.parse(raw).map(normalizeStudentLayer);
  } catch (error) {
    console.error("Failed to parse student layers from localStorage.", error);
    const initialLayers = buildInitialStudentLayers().map(normalizeStudentLayer);
    saveStudentLayers(initialLayers, storageScope);
    return initialLayers;
  }
}

export function saveStudentLayers(layers, storageScope = "default") {
  const storageKey = getStudentLayerStorageKey(storageScope);
  window.localStorage.setItem(storageKey, JSON.stringify(layers));
}

export function loadWorkspaceReflection(storageScope = "default") {
  const storageKey = getWorkspaceReflectionStorageKey(storageScope);
  return window.localStorage.getItem(storageKey) ?? "";
}

export function saveWorkspaceReflection(note, storageScope = "default") {
  const storageKey = getWorkspaceReflectionStorageKey(storageScope);
  window.localStorage.setItem(storageKey, String(note ?? "").trim());
}

export function loadWorkspaceProjectsRaw(storageScope = "default") {
  const storageKey = getWorkspaceProjectStorageKey(storageScope);
  const raw = window.localStorage.getItem(storageKey);
  if (!raw) {
    return [];
  }

  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch (error) {
    console.error("Failed to parse workspace projects from localStorage.", error);
    return [];
  }
}

export function saveWorkspaceProjectsRaw(projects, storageScope = "default") {
  const storageKey = getWorkspaceProjectStorageKey(storageScope);
  window.localStorage.setItem(storageKey, JSON.stringify(projects));
}

export function getRandomLayerColor(index) {
  const colors = ["#d94862", "#2f9e74", "#1d9bf0", "#8f5cf7", "#ff9f1c", "#0f766e"];
  return colors[index % colors.length];
}

function parseCsvLine(line) {
  const result = [];
  let current = "";
  let inQuotes = false;

  for (let index = 0; index < line.length; index += 1) {
    const character = line[index];
    if (character === '"') {
      if (inQuotes && line[index + 1] === '"') {
        current += '"';
        index += 1;
      } else {
        inQuotes = !inQuotes;
      }
      continue;
    }
    if (character === "," && !inQuotes) {
      result.push(current.trim());
      current = "";
      continue;
    }
    current += character;
  }

  result.push(current.trim());
  return result;
}

export function parseCsvText(text) {
  const lines = text.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  if (lines.length < 2) {
    throw new Error("CSV 파일에 데이터 행이 없습니다.");
  }

  const headers = parseCsvLine(lines[0]).map((header) => header.trim().toLowerCase());
  const latitudeKey = headers.find((header) => ["lat", "latitude", "y"].includes(header));
  const longitudeKey = headers.find((header) => ["lng", "lon", "longitude", "x"].includes(header));

  if (!latitudeKey || !longitudeKey) {
    throw new Error("CSV에는 lat/lng 또는 latitude/longitude 열이 필요합니다.");
  }

  return lines.slice(1).map((line) => {
    const values = parseCsvLine(line);
    const record = Object.fromEntries(headers.map((header, index) => [header, values[index] ?? ""]));
    return {
      geometryType: "point",
      coordinates: [Number(record[longitudeKey]), Number(record[latitudeKey])],
      title: record.title || record.name || record.label || "업로드 조사 지점",
      note: record.note || record.description || "",
      properties: record,
    };
  });
}

export function parseGeoJsonText(text, fallbackName) {
  const parsed = JSON.parse(text);
  const features = parsed.type === "FeatureCollection"
    ? parsed.features
    : parsed.type === "Feature"
      ? [parsed]
      : [];

  return features
    .map((feature) =>
      normalizeStudentFeature({
        title: feature.properties?.title ?? feature.properties?.name ?? fallbackName,
        note: feature.properties?.note ?? feature.properties?.description ?? "",
        geometry: feature.geometry,
        properties: feature.properties ?? {},
      }))
    .filter(Boolean);
}

export {
  buildStudentLayerFeatureCollection,
  normalizeStudentLayer,
};
