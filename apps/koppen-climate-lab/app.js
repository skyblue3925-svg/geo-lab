import {
  ACTIVE_CLIMATE_DATASET,
  CLIMATE_DATA_MODE,
  MONTH_LABELS,
  PRESETS,
  KOPPEN_COLORS,
  LATITUDES,
  LONGITUDES,
  analyzeLocation,
  buildWorld,
  createScenario,
  describeWindBand,
  getKoppenDetails,
  sampleTransect,
} from "./climate-model.mjs";
import { WORLD_MAP_BORDERS, WORLD_MAP_REGIONS } from "./world-map-data.mjs";
import { KEY_CONCEPT_PROMPTS, LESSON_MISSIONS, SCENARIO_GUIDANCE } from "./lesson-data.mjs";
import {
  OFFICIAL_KOPPEN_BINARY_URL,
  OFFICIAL_KOPPEN_BY_CODE,
  OFFICIAL_KOPPEN_BY_ID,
  OFFICIAL_KOPPEN_META,
} from "./data/koppen-geiger-1991-2020.mjs";

const TWO_PI = Math.PI * 2;
const LAND_GEOJSON_URL = "./data/world-land-110m.geojson";
const COUNTRY_GEOJSON_URL = "./data/world-countries-110m.geojson";

const MISSION_TO_CONCEPT = {
  "latitude-insolation": "insolation",
  "itcz-circulation": "itcz",
  continentality: "continentality",
  "mountain-rain-shadow": "mountain",
  "monsoon-seasonality": "monsoon",
  "koppen-reasoning": "koppen",
};

const MISSION_TO_SCENARIO = {
  "latitude-insolation": "equator-core",
  "itcz-circulation": "equator-core",
  continentality: "midlatitude-shift",
  "mountain-rain-shadow": "mountain-shadow",
  "monsoon-seasonality": "monsoon-classroom",
  "koppen-reasoning": "classification-bridge",
};

const SPOTLIGHTS = [
  { id: "equatorial-maritime", name: "적도 열대 해안", short: "EQT", latitude: 1.3, longitude: 103.8, presetId: "earthLite", note: "적도 저압대" },
  { id: "north-africa-dry", name: "북아프리카 건조대", short: "NAF", latitude: 25.0, longitude: 32.5, presetId: "earthLite", note: "아열대 건조대" },
  { id: "west-europe-coast", name: "서유럽 해안", short: "WEU", latitude: 47.5, longitude: 7.5, presetId: "earthLite", note: "편서풍 해안" },
  { id: "east-asia-coast", name: "동아시아 동안", short: "EAS", latitude: 37.5, longitude: 127.5, presetId: "earthLite", note: "동안 습윤대" },
  { id: "south-asia-monsoon", name: "남아시아 몬순대", short: "MON", latitude: 19.1, longitude: 72.9, presetId: "monsoonLab", note: "여름 몬순" },
  { id: "west-asia-steppe", name: "서아시아 스텝", short: "STP", latitude: 35.0, longitude: 45.0, presetId: "earthLite", note: "건조 초원" },
  { id: "andes-leeward", name: "안데스 비그늘", short: "LEE", latitude: -32.9, longitude: -68.8, presetId: "rainShadowLab", note: "산맥 배후" },
  { id: "arctic-tundra", name: "북극권 툰드라", short: "ARC", latitude: 78.2, longitude: 15.6, presetId: "earthLite", note: "고위도 한대" },
  { id: "antarctic-plateau", name: "남극 고원", short: "ICE", latitude: -82.0, longitude: 40.0, presetId: "earthLite", note: "빙설 고원" },
];

const mapCanvas = document.querySelector("#mapCanvas");
const climateChart = document.querySelector("#climateChart");
const circulationSvg = document.querySelector("#circulationSvg");
const transectSvg = document.querySelector("#transectSvg");
const mapLegend = document.querySelector("#mapLegend");
const selectionLabel = document.querySelector("#selectionLabel");
const selectionKoppen = document.querySelector("#selectionKoppen");
const selectionSummary = document.querySelector("#selectionSummary");
const selectionContext = document.querySelector("#selectionContext");
const koppenBreakdown = document.querySelector("#koppenBreakdown");
const annualFacts = document.querySelector("#annualFacts");
const monthlyFactors = document.querySelector("#monthlyFactors");
const driverStacks = document.querySelector("#driverStacks");
const ruleTrace = document.querySelector("#ruleTrace");
const reasonList = document.querySelector("#reasonList");
const circulationFacts = document.querySelector("#circulationFacts");
const transectCaption = document.querySelector("#transectCaption");
const presetDescription = document.querySelector("#presetDescription");
const spotlightButtons = document.querySelector("#spotlightButtons");
const missionSteps = document.querySelector("#missionSteps");
const missionCard = document.querySelector("#missionCard");
const scenarioGuidance = document.querySelector("#scenarioGuidance");
const knobBlocks = Array.from(document.querySelectorAll("[data-knob]"));
const foldPanels = Array.from(document.querySelectorAll("[data-fold-panel]"));
const controlNote = document.querySelector(".control-note");

const controls = {
  preset: document.querySelector("#presetSelect"),
  month: document.querySelector("#monthRange"),
  monthValue: document.querySelector("#monthValue"),
  tilt: document.querySelector("#tiltRange"),
  tiltValue: document.querySelector("#tiltValue"),
  landScale: document.querySelector("#landScaleRange"),
  landScaleValue: document.querySelector("#landScaleValue"),
  mountainHeight: document.querySelector("#mountainRange"),
  mountainHeightValue: document.querySelector("#mountainValue"),
  currentButtons: Array.from(document.querySelectorAll("[data-current-bias]")),
  overlayButtons: Array.from(document.querySelectorAll("[data-overlay]")),
};

const defaultPreset = PRESETS.earthLite;
const state = {
  presetId: defaultPreset.id,
  month: 7,
  tilt: defaultPreset.tilt,
  landScale: defaultPreset.landScale,
  mountainHeight: defaultPreset.mountainHeight,
  currentBias: defaultPreset.currentBias,
  overlay: "koppen",
  missionId: LESSON_MISSIONS[0].id,
  selectedLatitude: defaultPreset.probeLat,
  selectedLongitude: defaultPreset.probeLon,
};

let renderQueued = false;
let worldGeometry = {
  land: null,
  countries: null,
};
let officialKoppenLayer = {
  ready: false,
  width: OFFICIAL_KOPPEN_META.width,
  height: OFFICIAL_KOPPEN_META.height,
  codes: null,
  canvas: null,
};

const isObservedClimateMode = CLIMATE_DATA_MODE === "observed";

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function sum(values) {
  return values.reduce((total, value) => total + value, 0);
}

function average(values) {
  return values.length ? sum(values) / values.length : 0;
}

function gaussian(distance, spread) {
  if (spread <= 0) {
    return 0;
  }
  return Math.exp(-((distance * distance) / (2 * spread * spread)));
}

function degToRad(value) {
  return (value * Math.PI) / 180;
}

function wrapLongitude(value) {
  let longitude = ((Number(value) + 180) % 360 + 360) % 360 - 180;
  if (longitude === 180) {
    longitude = -180;
  }
  return longitude;
}

function buildOfficialKoppenCanvas(codes) {
  const canvas = document.createElement("canvas");
  canvas.width = OFFICIAL_KOPPEN_META.width;
  canvas.height = OFFICIAL_KOPPEN_META.height;
  const context = canvas.getContext("2d", { alpha: false });
  const imageData = context.createImageData(canvas.width, canvas.height);
  const pixels = imageData.data;

  for (let index = 0; index < codes.length; index += 1) {
    const classMeta = OFFICIAL_KOPPEN_BY_ID[codes[index]];
    const pixelOffset = index * 4;
    if (classMeta) {
      const displayColor = KOPPEN_COLORS[classMeta.code] ?? classMeta.color;
      const [red, green, blue] = hexToRgb(displayColor);
      pixels[pixelOffset] = red;
      pixels[pixelOffset + 1] = green;
      pixels[pixelOffset + 2] = blue;
      pixels[pixelOffset + 3] = 255;
    } else {
      pixels[pixelOffset] = 23;
      pixels[pixelOffset + 1] = 48;
      pixels[pixelOffset + 2] = 62;
      pixels[pixelOffset + 3] = 255;
    }
  }

  context.putImageData(imageData, 0, 0);
  return canvas;
}

function sampleOfficialKoppenId(latitude, longitude) {
  if (!officialKoppenLayer.ready || !officialKoppenLayer.codes) {
    return 0;
  }

  const safeLat = clamp(Number(latitude), -90, 90);
  const safeLon = wrapLongitude(longitude);
  const x = clamp(Math.floor(((safeLon + 180) / 360) * officialKoppenLayer.width), 0, officialKoppenLayer.width - 1);
  const y = clamp(Math.floor(((90 - safeLat) / 180) * officialKoppenLayer.height), 0, officialKoppenLayer.height - 1);
  return officialKoppenLayer.codes[y * officialKoppenLayer.width + x] ?? 0;
}

function getOfficialClassification(latitude, longitude) {
  const officialId = sampleOfficialKoppenId(latitude, longitude);
  const officialClass = OFFICIAL_KOPPEN_BY_ID[officialId];
  if (!officialClass) {
    return {
      id: 0,
      code: "Ocean",
      ...getKoppenDetails("Ocean"),
      source: "Beck et al. 2026 v2 map",
      approximate: false,
    };
  }

  return {
    id: officialId,
    code: officialClass.code,
    ...getKoppenDetails(officialClass.code),
    color: officialClass.color,
    source: "Beck et al. 2026 v2 map",
    approximate: true,
  };
}

function withOfficialClassification(analysis) {
  if (!officialKoppenLayer.ready) {
    return analysis;
  }

  const classification = getOfficialClassification(analysis.latitude, analysis.longitude);
  const reasons = classification.code === "Ocean"
    ? [
        "공식 Beck 쾨펜 지도에서 이 위치는 해양/무자료 영역입니다.",
        `${ACTIVE_CLIMATE_DATASET.dataset} ${ACTIVE_CLIMATE_DATASET.period} 차트는 육상 월평균 기후자료만 제공합니다.`,
      ]
    : [
        `지도 코드는 Beck et al. 2026 v2 1991-2020 공식 쾨펜 지도(${classification.code})를 사용합니다.`,
        `${ACTIVE_CLIMATE_DATASET.dataset} ${ACTIVE_CLIMATE_DATASET.period} 월별 기온·강수 차트로 원인을 함께 읽습니다.`,
        ...analysis.reasons.slice(0, 4),
      ];

  return {
    ...analysis,
    classification,
    reasons,
  };
}

function interpolateStops(stops, value) {
  const safeValue = clamp(value, 0, 1);
  for (let index = 0; index < stops.length - 1; index += 1) {
    const left = stops[index];
    const right = stops[index + 1];
    if (safeValue >= left[0] && safeValue <= right[0]) {
      const localT = (safeValue - left[0]) / Math.max(right[0] - left[0], 0.0001);
      return mixColor(left[1], right[1], localT);
    }
  }
  return stops[stops.length - 1][1];
}

function mixColor(left, right, t) {
  const leftRgb = hexToRgb(left);
  const rightRgb = hexToRgb(right);
  const mix = (a, b) => Math.round(a + (b - a) * t);
  return `rgb(${mix(leftRgb[0], rightRgb[0])}, ${mix(leftRgb[1], rightRgb[1])}, ${mix(leftRgb[2], rightRgb[2])})`;
}

function hexToRgb(hex) {
  const clean = hex.replace("#", "");
  const normalized = clean.length === 3 ? clean.split("").map((char) => `${char}${char}`).join("") : clean;
  const value = parseInt(normalized, 16);
  return [(value >> 16) & 255, (value >> 8) & 255, value & 255];
}

function withAlpha(hex, alpha) {
  const [red, green, blue] = hexToRgb(hex);
  return `rgba(${red}, ${green}, ${blue}, ${alpha})`;
}

function temperatureColor(value) {
  const normalized = clamp((value + 35) / 70, 0, 1);
  return interpolateStops(
    [
      [0, "#12304a"],
      [0.28, "#4d8fc4"],
      [0.5, "#eff5f8"],
      [0.68, "#f2bf61"],
      [1, "#b33c26"],
    ],
    normalized,
  );
}

function precipitationColor(value) {
  const normalized = clamp(value / 300, 0, 1);
  return interpolateStops(
    [
      [0, "#7b5438"],
      [0.25, "#c48a5a"],
      [0.45, "#dfc78b"],
      [0.7, "#7cc9cc"],
      [1, "#0e5f77"],
    ],
    normalized,
  );
}

function prepareCanvas(canvas) {
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  const width = Math.max(1, Math.round(rect.width));
  const height = Math.max(1, Math.round(rect.height));
  if (canvas.width !== width * dpr || canvas.height !== height * dpr) {
    canvas.width = width * dpr;
    canvas.height = height * dpr;
  }
  const ctx = canvas.getContext("2d");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  return { ctx, width, height };
}

function latToY(latitude, height) {
  return ((90 - latitude) / 180) * height;
}

function lonToX(longitude, width) {
  return ((longitude + 180) / 360) * width;
}

function formatCoordinate(latitude, longitude) {
  const latLabel = `${Math.abs(latitude).toFixed(1)}°${latitude >= 0 ? "N" : "S"}`;
  const lonLabel = `${Math.abs(longitude).toFixed(1)}°${longitude >= 0 ? "E" : "W"}`;
  return `${latLabel}, ${lonLabel}`;
}

function wrappedLongitudeDistance(left, right) {
  const delta = Math.abs(left - right) % 360;
  return delta > 180 ? 360 - delta : delta;
}

function getSpotlightDistance(latitude, longitude, spotlight) {
  const lonDistance = wrappedLongitudeDistance(longitude, spotlight.longitude) * Math.cos(degToRad((latitude + spotlight.latitude) / 2));
  return Math.hypot(latitude - spotlight.latitude, lonDistance);
}

function getNearestSpotlight(latitude, longitude) {
  return SPOTLIGHTS
    .map((spotlight) => ({ spotlight, distance: getSpotlightDistance(latitude, longitude, spotlight) }))
    .sort((left, right) => left.distance - right.distance)[0];
}

function getMacroRegionLabel(latitude, longitude) {
  if (latitude <= -70) {
    return "남극권";
  }
  if (latitude >= 72 && longitude >= -75 && longitude <= -10) {
    return "그린란드 내륙";
  }
  if (longitude >= -170 && longitude < -30) {
    if (latitude >= 55) {
      return "북아메리카 북부";
    }
    if (latitude >= 15) {
      return "북아메리카";
    }
    if (latitude >= -15) {
      return "중앙아메리카";
    }
    return "남아메리카";
  }
  if (longitude >= -30 && longitude < 60) {
    if (latitude >= 35) {
      return "유럽";
    }
    if (latitude >= 5) {
      return "북아프리카·서아시아";
    }
    if (latitude >= -35) {
      return "사하라 이남 아프리카";
    }
    return "남아프리카";
  }
  if (longitude >= 60 && longitude < 150) {
    if (latitude >= 45) {
      return "북아시아";
    }
    if (latitude >= 15) {
      return "동아시아·내륙 아시아";
    }
    if (latitude >= -10) {
      return "남아시아·동남아시아";
    }
    return "인도양·오세아니아";
  }
  if (latitude < -10) {
    return "오스트레일리아·남태평양";
  }
  return "태평양 해역";
}

function getLatitudeZoneLabel(latitude) {
  const absLat = Math.abs(latitude);
  if (absLat < 12) {
    return "적도 저압대";
  }
  if (absLat < 25) {
    return "열대 순환대";
  }
  if (absLat < 38) {
    return "아열대 전이대";
  }
  if (absLat < 60) {
    return "중위도 편서풍대";
  }
  return "극전선·한대";
}

function getSurfaceContextLabel(analysis) {
  if (analysis.profile.landness < 0.18) {
    return "대양성 해양 셀";
  }
  if (analysis.selectedMonth.shadowDry > 18 && analysis.selectedMonth.foehnWarm > 1) {
    return "산맥 비그늘";
  }
  if (analysis.selectedMonth.orographicWet > 24) {
    return "산맥 바람받이";
  }
  if (analysis.profile.interiorness > 0.5) {
    return "대륙 내부";
  }
  if (analysis.profile.coastalness > 0.35) {
    if (analysis.profile.currentZone > 0.2) {
      return "따뜻한 해류 해안";
    }
    if (analysis.profile.currentZone < -0.2) {
      return "찬 해류 해안";
    }
    return "해양성 해안";
  }
  return "육해 전이지대";
}

function resolveSelectionContext(analysis) {
  const nearest = getNearestSpotlight(analysis.latitude, analysis.longitude);
  const macroRegion = getMacroRegionLabel(analysis.latitude, analysis.longitude);
  const latitudeZone = getLatitudeZoneLabel(analysis.latitude);
  const surfaceContext = getSurfaceContextLabel(analysis);
  const useSpotlight = nearest && nearest.distance < 7;
  const title = useSpotlight ? nearest.spotlight.name : macroRegion;
  const subtitle = useSpotlight ? nearest.spotlight.note : `${latitudeZone} 대표 지점`;
  const note = useSpotlight
    ? `${macroRegion}의 대표 사례입니다. ${latitudeZone}와 ${surfaceContext}이 겹치며 ${analysis.classification.code}가 만들어집니다.`
    : `${macroRegion}의 ${surfaceContext} 지대입니다. ${latitudeZone}와 지형·해양 효과를 함께 읽기 좋은 위치입니다.`;
  return {
    title,
    subtitle,
    macroRegion,
    latitudeZone,
    surfaceContext,
    note,
  };
}

function getCurrentMission() {
  return LESSON_MISSIONS.find((mission) => mission.id === state.missionId) ?? LESSON_MISSIONS[0];
}

function updateControlUI() {
  const mission = getCurrentMission();
  controls.preset.value = state.presetId;
  controls.month.value = String(state.month);
  controls.monthValue.textContent = MONTH_LABELS[state.month - 1];
  controls.tilt.value = String(state.tilt);
  controls.tiltValue.textContent = `${Number(state.tilt).toFixed(1)}°`;
  controls.landScale.value = String(state.landScale);
  controls.landScaleValue.textContent = `${Math.round(state.landScale * 100)}%`;
  controls.mountainHeight.value = String(state.mountainHeight);
  controls.mountainHeightValue.textContent = `${Math.round(state.mountainHeight).toLocaleString()} m`;

  for (const button of controls.currentButtons) {
    button.classList.toggle("is-active", Number(button.dataset.currentBias) === Number(state.currentBias));
  }
  for (const button of controls.overlayButtons) {
    button.classList.toggle("is-active", button.dataset.overlay === state.overlay);
  }
  controls.preset.disabled = isObservedClimateMode;
  controls.tilt.disabled = isObservedClimateMode;
  controls.landScale.disabled = isObservedClimateMode;
  controls.mountainHeight.disabled = isObservedClimateMode;
  for (const button of controls.currentButtons) {
    button.disabled = isObservedClimateMode;
  }
  for (const block of knobBlocks) {
    const isMonthKnob = block.dataset.knob === "월";
    block.classList.toggle("is-guided", isObservedClimateMode ? isMonthKnob : mission.knobTargets.includes(block.dataset.knob));
    block.classList.toggle("is-disabled", isObservedClimateMode && !isMonthKnob);
  }

  presetDescription.textContent = isObservedClimateMode
    ? `지도는 Beck 2026 v2 1991-2020 공식 쾨펜 레이어를, 차트는 ${ACTIVE_CLIMATE_DATASET.dataset} ${ACTIVE_CLIMATE_DATASET.period} 월별 자료를 사용합니다.`
    : PRESETS[state.presetId].description;
  if (controlNote && isObservedClimateMode) {
    controlNote.textContent = `쾨펜 지도는 Beck et al. 2026 v2 1991-2020 공식 분류 레이어이고, 월별 차트는 ${ACTIVE_CLIMATE_DATASET.dataset} ${ACTIVE_CLIMATE_DATASET.period} ${ACTIVE_CLIMATE_DATASET.resolution} 자료입니다. 학생용으로 월과 오버레이만 남기고 나머지 손잡이는 잠갔습니다.`;
  }
}

function buildScenarioFromState() {
  if (isObservedClimateMode) {
    return createScenario({
      presetId: PRESETS.earthLite.id,
      month: state.month,
      tilt: PRESETS.earthLite.tilt,
      landScale: PRESETS.earthLite.landScale,
      mountainHeight: 0,
      currentBias: 0,
      monsoonStrength: PRESETS.earthLite.monsoonStrength,
    });
  }

  return createScenario({
    presetId: state.presetId,
    month: state.month,
    tilt: state.tilt,
    landScale: state.landScale,
    mountainHeight: state.mountainHeight,
    currentBias: state.currentBias,
  });
}

function applyPreset(presetId) {
  const preset = PRESETS[presetId] ?? PRESETS.earthLite;
  state.presetId = preset.id;
  state.tilt = preset.tilt;
  state.landScale = preset.landScale;
  state.mountainHeight = preset.mountainHeight;
  state.currentBias = preset.currentBias;
  state.selectedLatitude = preset.probeLat;
  state.selectedLongitude = preset.probeLon;
  updateControlUI();
  queueRender();
}

function jumpToSpotlight(spotlightId) {
  const spotlight = SPOTLIGHTS.find((item) => item.id === spotlightId);
  if (!spotlight) {
    return;
  }
  const preset = PRESETS[spotlight.presetId] ?? PRESETS.earthLite;
  state.presetId = preset.id;
  state.tilt = preset.tilt;
  state.landScale = preset.landScale;
  state.mountainHeight = preset.mountainHeight;
  state.currentBias = preset.currentBias;
  state.selectedLatitude = spotlight.latitude;
  state.selectedLongitude = spotlight.longitude;
  updateControlUI();
  queueRender();
}

function queueRender() {
  if (renderQueued) {
    return;
  }
  renderQueued = true;
  window.requestAnimationFrame(() => {
    renderQueued = false;
    render();
  });
}

function populatePresetSelect() {
  controls.preset.innerHTML = Object.values(PRESETS)
    .map((preset) => `<option value="${preset.id}">${preset.name}</option>`)
    .join("");
}

function renderLegend() {
  if (state.overlay === "koppen") {
    mapLegend.innerHTML = [
      ["A", KOPPEN_COLORS.Am, "열대"],
      ["B", KOPPEN_COLORS.BWh, "건조"],
      ["C", KOPPEN_COLORS.Cfb, "온대"],
      ["D", KOPPEN_COLORS.Dfb, "냉대"],
      ["E", KOPPEN_COLORS.ET, "한대"],
    ]
      .map(([code, color, label]) => `<span class="legend-chip"><span class="legend-dot" style="background:${color}"></span>${code} ${label}</span>`)
      .join("")
      + '<p class="legend-note">공식 Beck 2026 v2 1991-2020 쾨펜 지도입니다. 바다는 해양/무자료 영역으로 처리합니다.</p>';
    return;
  }

  const gradient = state.overlay === "temperature"
    ? "linear-gradient(90deg, #12304a 0%, #4d8fc4 28%, #eff5f8 50%, #f2bf61 70%, #b33c26 100%)"
    : "linear-gradient(90deg, #7b5438 0%, #c48a5a 25%, #dfc78b 45%, #7cc9cc 70%, #0e5f77 100%)";
  const labels = state.overlay === "temperature" ? ["-35°C", "0°C", "35°C"] : ["0 mm", "150 mm", "300+ mm"];
  mapLegend.innerHTML = `
    <div class="legend-bar" style="background:${gradient}"></div>
    <div class="legend-scale"><span>${labels[0]}</span><span>${labels[1]}</span><span>${labels[2]}</span></div>
  `;
}

function drawFallbackWorldOverlay(ctx, width, height) {
  const fillAlpha = state.overlay === "koppen" ? 0.18 : 0.08;
  const strokeAlpha = state.overlay === "koppen" ? 0.7 : 0.42;

  for (const region of WORLD_MAP_REGIONS) {
    ctx.beginPath();
    region.points.forEach(([longitude, latitude], index) => {
      const x = lonToX(longitude, width);
      const y = latToY(latitude, height);
      if (index === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    });
    ctx.closePath();
    ctx.fillStyle = withAlpha(region.fill, fillAlpha);
    ctx.strokeStyle = withAlpha(region.stroke, strokeAlpha);
    ctx.lineWidth = 1.2;
    ctx.fill();
    ctx.stroke();
  }
}

function traceRing(ctx, ring, width, height) {
  ring.forEach(([longitude, latitude], index) => {
    const x = lonToX(longitude, width);
    const y = latToY(latitude, height);
    if (index === 0) {
      ctx.moveTo(x, y);
    } else {
      ctx.lineTo(x, y);
    }
  });
  ctx.closePath();
}

function traceGeometry(ctx, geometry, width, height) {
  if (!geometry) {
    return;
  }

  if (geometry.type === "Polygon") {
    geometry.coordinates.forEach((ring) => traceRing(ctx, ring, width, height));
    return;
  }

  if (geometry.type === "MultiPolygon") {
    geometry.coordinates.forEach((polygon) => {
      polygon.forEach((ring) => traceRing(ctx, ring, width, height));
    });
  }
}

function drawGeoJsonCollection(ctx, geojson, width, height, options) {
  if (!geojson?.features?.length) {
    return false;
  }

  ctx.beginPath();
  geojson.features.forEach((feature) => traceGeometry(ctx, feature.geometry, width, height));

  if (options.fillStyle) {
    ctx.fillStyle = options.fillStyle;
    ctx.fill();
  }

  if (options.strokeStyle) {
    ctx.strokeStyle = options.strokeStyle;
    ctx.lineWidth = options.lineWidth ?? 1;
    ctx.stroke();
  }

  return true;
}

function drawWorldOverlay(ctx, width, height) {
  ctx.save();

  const usedRealGeometry = drawGeoJsonCollection(ctx, worldGeometry.land, width, height, {
    fillStyle: state.overlay === "koppen" ? "rgba(237, 231, 216, 0.18)" : "rgba(237, 231, 216, 0.1)",
    strokeStyle: "rgba(247, 241, 230, 0.48)",
    lineWidth: 1.2,
  });

  if (usedRealGeometry) {
    drawGeoJsonCollection(ctx, worldGeometry.countries, width, height, {
      strokeStyle: state.overlay === "koppen" ? "rgba(255, 255, 255, 0.18)" : "rgba(255, 255, 255, 0.12)",
      lineWidth: 0.65,
    });
  } else {
    drawFallbackWorldOverlay(ctx, width, height);
  }

  ctx.setLineDash([6, 6]);
  ctx.strokeStyle = "rgba(255,255,255,0.22)";
  for (const border of WORLD_MAP_BORDERS) {
    const y = latToY(border.lat, height);
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(width, y);
    ctx.stroke();
  }
  ctx.setLineDash([]);

  if (!usedRealGeometry) {
    ctx.fillStyle = "rgba(247, 244, 236, 0.68)";
    ctx.font = '600 12px "Aptos", sans-serif';
    ctx.textAlign = "center";
    for (const region of WORLD_MAP_REGIONS.filter((item) => item.type === "continent" || item.type === "ice")) {
      const lon = average(region.points.map(([pointLon]) => pointLon));
      const lat = average(region.points.map(([, pointLat]) => pointLat));
      ctx.fillText(region.label, lonToX(lon, width), latToY(lat, height));
    }
  }

  ctx.restore();
}

function drawSpotlights(ctx, width, height) {
  ctx.save();
  ctx.font = '700 11px "Bahnschrift", sans-serif';
  ctx.textAlign = "center";
  SPOTLIGHTS.forEach((spot) => {
    const x = lonToX(spot.longitude, width);
    const y = latToY(spot.latitude, height);
    const active = Math.abs(spot.latitude - state.selectedLatitude) < 2.5 && Math.abs(spot.longitude - state.selectedLongitude) < 2.5;
    ctx.beginPath();
    ctx.fillStyle = active ? "#ffd06b" : "rgba(255, 255, 255, 0.88)";
    ctx.strokeStyle = "#0f2232";
    ctx.lineWidth = active ? 3 : 2;
    ctx.arc(x, y, active ? 6 : 4, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();
    ctx.fillStyle = "rgba(255,255,255,0.92)";
    ctx.fillText(spot.short, x, y - 10);
  });
  ctx.restore();
}

function renderMap(world, scenario) {
  const { ctx, width, height } = prepareCanvas(mapCanvas);
  const cellWidth = width / LONGITUDES.length;
  const cellHeight = height / LATITUDES.length;
  const monthIndex = clamp(state.month - 1, 0, 11);

  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = "#17303e";
  ctx.fillRect(0, 0, width, height);

  if (state.overlay === "koppen" && officialKoppenLayer.ready && officialKoppenLayer.canvas) {
    ctx.drawImage(officialKoppenLayer.canvas, 0, 0, width, height);
  } else {
    for (let latIndex = 0; latIndex < LATITUDES.length; latIndex += 1) {
      for (let lonIndex = 0; lonIndex < LONGITUDES.length; lonIndex += 1) {
        const cellIndex = latIndex * LONGITUDES.length + lonIndex;
        const x = lonIndex * cellWidth;
        const y = latIndex * cellHeight;
        let fill = "#17303e";
        const isOceanCell = world.landness[cellIndex] < 0.42;

        if (state.overlay === "koppen") {
          const code = world.koppenCodes[cellIndex];
          fill = code === "Ocean" ? "rgba(33, 73, 92, 0.88)" : (KOPPEN_COLORS[code] ?? "#5e7483");
        } else if (isOceanCell) {
          fill = "rgba(23, 48, 62, 0.96)";
        } else if (state.overlay === "temperature") {
          fill = temperatureColor(world.monthlyTemperature[monthIndex][cellIndex]);
        } else {
          fill = precipitationColor(world.monthlyPrecipitation[monthIndex][cellIndex]);
        }

        ctx.fillStyle = fill;
        ctx.fillRect(x, y, cellWidth + 1, cellHeight + 1);
      }
    }
  }

  drawWorldOverlay(ctx, width, height);

  ctx.save();
  ctx.strokeStyle = "rgba(255, 208, 107, 0.95)";
  ctx.fillStyle = "rgba(255, 208, 107, 0.95)";
  ctx.lineWidth = 2.4;
  ctx.setLineDash([10, 6]);
  const itczY = latToY(world.itczLatitude, height);
  ctx.beginPath();
  ctx.moveTo(0, itczY);
  ctx.lineTo(width, itczY);
  ctx.stroke();
  ctx.setLineDash([]);
  ctx.font = '700 12px "Aptos", sans-serif';
  ctx.textAlign = "left";
  ctx.fillText("ITCZ", 10, Math.max(14, itczY - 8));

  if (scenario.mountainHeight > 0) {
    const mountainX = lonToX(scenario.mountainLon, width);
    ctx.strokeStyle = "rgba(247, 231, 184, 0.82)";
    ctx.setLineDash([4, 5]);
    ctx.beginPath();
    ctx.moveTo(mountainX, 0);
    ctx.lineTo(mountainX, height);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = "rgba(247, 231, 184, 0.9)";
    ctx.textAlign = mountainX < width - 70 ? "left" : "right";
    ctx.fillText("산맥", mountainX + (mountainX < width - 70 ? 8 : -8), 18);
  }
  ctx.restore();

  drawSpotlights(ctx, width, height);

  const selectedX = lonToX(state.selectedLongitude, width);
  const selectedY = latToY(state.selectedLatitude, height);
  ctx.save();
  ctx.strokeStyle = "#ffffff";
  ctx.fillStyle = "#ffffff";
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.arc(selectedX, selectedY, 8, 0, TWO_PI);
  ctx.stroke();
  ctx.beginPath();
  ctx.arc(selectedX, selectedY, 3.2, 0, TWO_PI);
  ctx.fill();
  ctx.restore();
}

function getBreakdowns(analysis, scenario) {
  const absLat = Math.abs(analysis.latitude);
  const hemisphere = analysis.latitude === 0 ? 0 : Math.sign(analysis.latitude);
  const heatingSign = hemisphere === 0 ? 1 : hemisphere;
  const seasonWave = Math.sin((scenario.month - 4) / 12 * TWO_PI);
  const currentTemp = scenario.currentBias * analysis.profile.coastalness * analysis.profile.currentZone * 3.4;
  const seasonAmplitude = clamp(
    (1.8 + absLat * 0.18) * (scenario.tilt / 23.4) + analysis.profile.interiorness * 9 - analysis.profile.coastalness * 4.5,
    0.8,
    26,
  );
  const latitudeBase = 29 - 0.39 * absLat - 0.0014 * absLat * absLat;
  const elevationCooling = -0.0057 * analysis.profile.elevation;
  const oceanLandAdjustment = analysis.profile.landness * 0.9 - analysis.profile.interiorness * 1.8 + currentTemp * 0.6;
  const solarPulse = (Math.cos(degToRad(analysis.latitude - analysis.selectedMonth.declination)) - Math.cos(degToRad(analysis.latitude))) * 9;
  const seasonalOffset = seasonAmplitude * seasonWave * heatingSign * (hemisphere === 0 ? 0.2 : 1);

  const summerHeating = Math.max(0, seasonWave * heatingSign);
  const winterCooling = Math.max(0, -seasonWave * heatingSign);
  const baselineMoisture = 18 + 32 * (1 - analysis.profile.landness) + 24 * analysis.profile.coastalness;
  const itczRain = 145 * gaussian(analysis.latitude - analysis.selectedMonth.itczLat, 11) * (0.75 + analysis.profile.oceanFetch * 0.35);
  const stormTrack = 62 * gaussian(absLat - 50, 10) * (0.5 + analysis.profile.oceanFetch * 0.5);
  const subtropicalDry = -78 * gaussian(absLat - 28, 8) * (0.65 + analysis.profile.interiorness);
  const interiorDry = -50 * analysis.profile.interiorness;
  const monsoonBand = clamp((absLat - 8) / 12, 0, 1) * clamp((38 - absLat) / 12, 0, 1);
  const monsoonWet = scenario.monsoonStrength * analysis.profile.landness * analysis.profile.oceanFetch * monsoonBand * summerHeating * 150;
  const monsoonDry = -scenario.monsoonStrength * analysis.profile.landness * monsoonBand * winterCooling * 34;
  const currentWet = scenario.currentBias * analysis.profile.coastalness * analysis.profile.currentZone * 24;
  const polarDry = -(absLat > 65 ? (absLat - 65) * 1.4 : 0);

  return {
    temperature: [
      { label: "위도 기본값", value: latitudeBase, unit: "°C" },
      { label: "해양/대륙 조정", value: oceanLandAdjustment, unit: "°C" },
      { label: "지형 냉각", value: elevationCooling, unit: "°C" },
      { label: "계절 이동", value: solarPulse + seasonalOffset, unit: "°C" },
      { label: "푄 가열", value: analysis.selectedMonth.foehnWarm, unit: "°C" },
    ],
    precipitation: [
      { label: "기본 수분", value: baselineMoisture, unit: "mm" },
      { label: "ITCZ", value: itczRain, unit: "mm" },
      { label: "중위도 저기압", value: stormTrack, unit: "mm" },
      { label: "몬순", value: monsoonWet + monsoonDry, unit: "mm" },
      { label: "해류/해안", value: currentWet, unit: "mm" },
      { label: "산맥 상승", value: analysis.selectedMonth.orographicWet, unit: "mm" },
      { label: "비그늘", value: -analysis.selectedMonth.shadowDry, unit: "mm" },
      { label: "아열대 건조대", value: subtropicalDry, unit: "mm" },
      { label: "내륙 건조", value: interiorDry, unit: "mm" },
      { label: "극지 건조", value: polarDry, unit: "mm" },
    ],
  };
}

function formatSigned(value, unit) {
  return `${value >= 0 ? "+" : ""}${value.toFixed(1)} ${unit}`;
}

function renderDriverSection(title, drivers) {
  const maxAbs = Math.max(...drivers.map((item) => Math.abs(item.value)), 1);
  return `
    <section class="driver-section">
      <h3>${title}</h3>
      ${drivers
        .map((driver) => {
          const width = (Math.abs(driver.value) / maxAbs) * 100;
          const toneClass = driver.value >= 0 ? "positive" : "negative";
          return `
            <div class="driver-row ${toneClass}">
              <span>${driver.label}</span>
              <div class="driver-meter"><i style="width:${width}%"></i></div>
              <strong>${formatSigned(driver.value, driver.unit)}</strong>
            </div>
          `;
        })
        .join("")}
    </section>
  `;
}

function getClassificationMetrics(analysis) {
  const temperatures = analysis.temperatures;
  const precipitations = analysis.precipitations;
  const annualTemp = average(temperatures);
  const annualPrecip = sum(precipitations);
  const warmest = Math.max(...temperatures);
  const coldest = Math.min(...temperatures);
  const driest = Math.min(...precipitations);
  const warmMonths = temperatures.filter((value) => value >= 10).length;
  const summerIndices = analysis.latitude >= 0 ? [3, 4, 5, 6, 7, 8] : [9, 10, 11, 0, 1, 2];
  const winterIndices = Array.from({ length: 12 }, (_, index) => index).filter((index) => !summerIndices.includes(index));
  const summerPrecip = sum(summerIndices.map((index) => precipitations[index]));
  const driestSummer = Math.min(...summerIndices.map((index) => precipitations[index]));
  const wettestSummer = Math.max(...summerIndices.map((index) => precipitations[index]));
  const driestWinter = Math.min(...winterIndices.map((index) => precipitations[index]));
  const wettestWinter = Math.max(...winterIndices.map((index) => precipitations[index]));
  const summerRatio = annualPrecip > 0 ? summerPrecip / annualPrecip : 0;
  const drynessOffset = summerRatio >= 0.7 ? 280 : summerRatio >= 0.3 ? 140 : 0;
  const drynessThreshold = Math.max(0, 20 * annualTemp + drynessOffset);
  const monsoonThreshold = 100 - annualPrecip / 25;

  return {
    annualTemp,
    annualPrecip,
    warmest,
    coldest,
    driest,
    warmMonths,
    driestSummer,
    wettestSummer,
    driestWinter,
    wettestWinter,
    summerRatio,
    drynessOffset,
    drynessThreshold,
    monsoonThreshold,
  };
}

function getRuleTraceRows(analysis) {
  const metrics = getClassificationMetrics(analysis);

  if (analysis.classification.code === "Ocean") {
    return [{ label: "육지 비율", value: `${(analysis.profile.landness * 100).toFixed(0)}%`, detail: "육상이 부족해 해양 셀로 처리", state: "neutral" }];
  }

  if (analysis.classification.code.startsWith("A")) {
    return [
      { label: "최한월 ≥ 18°C", value: `${metrics.coldest.toFixed(1)}°C`, detail: metrics.coldest >= 18 ? "충족" : "미충족", state: metrics.coldest >= 18 ? "pass" : "warn" },
      { label: "최건월", value: `${metrics.driest.toFixed(0)} mm`, detail: `Af 기준 60 mm, Am 기준 ${metrics.monsoonThreshold.toFixed(0)} mm`, state: "pass" },
      { label: "연강수량", value: `${metrics.annualPrecip.toFixed(0)} mm`, detail: "열대 내 건기/우기 해석에 사용", state: "neutral" },
    ];
  }

  if (analysis.classification.code.startsWith("B")) {
    return [
      { label: "연강수량", value: `${metrics.annualPrecip.toFixed(0)} mm`, detail: `건조 한계 ${metrics.drynessThreshold.toFixed(0)} mm`, state: metrics.annualPrecip < metrics.drynessThreshold ? "pass" : "warn" },
      { label: "여름 강수 비율", value: `${(metrics.summerRatio * 100).toFixed(0)}%`, detail: `보정값 ${metrics.drynessOffset.toFixed(0)} mm`, state: "neutral" },
      { label: "연평균 기온", value: `${metrics.annualTemp.toFixed(1)}°C`, detail: metrics.annualTemp >= 18 ? "h 분기" : "k 분기", state: "pass" },
    ];
  }

  if (analysis.classification.code.startsWith("E")) {
    return [
      { label: "최난월", value: `${metrics.warmest.toFixed(1)}°C`, detail: "10°C 미만이면 E기후", state: metrics.warmest < 10 ? "pass" : "warn" },
      { label: "빙설 경계", value: `${metrics.warmest.toFixed(1)}°C`, detail: metrics.warmest < 0 ? "EF" : "ET", state: "neutral" },
      { label: "연강수량", value: `${metrics.annualPrecip.toFixed(0)} mm`, detail: "한대 내부에서도 건조 정도를 읽는 참고값", state: "neutral" },
    ];
  }

  return [
    { label: "최난월", value: `${metrics.warmest.toFixed(1)}°C`, detail: "10°C 이상이어야 C/D 가능", state: metrics.warmest >= 10 ? "pass" : "warn" },
    { label: "최한월", value: `${metrics.coldest.toFixed(1)}°C`, detail: metrics.coldest >= 0 ? "C 경계" : "D 경계", state: "pass" },
    {
      label: "건기 판정",
      value: `여름 ${metrics.driestSummer.toFixed(0)} / 겨울 ${metrics.driestWinter.toFixed(0)} mm`,
      detail: metrics.driestSummer < 40 && metrics.driestSummer < metrics.wettestWinter / 3 ? "s" : metrics.driestWinter < metrics.wettestSummer / 10 ? "w" : "f",
      state: "neutral",
    },
    { label: "10°C 이상 월 수", value: `${metrics.warmMonths}개월`, detail: metrics.warmest >= 22 && metrics.warmMonths >= 4 ? "a" : metrics.warmMonths >= 4 ? "b" : "c/d", state: "neutral" },
  ];
}

function getKoppenLetterBreakdown(analysis) {
  const code = analysis.classification.code;
  const metrics = getClassificationMetrics(analysis);

  if (code === "Ocean") {
    return [
      {
        letter: "Ocean",
        label: "해양 셀",
        detail: `육지 비율 ${(analysis.profile.landness * 100).toFixed(0)}%로 낮아 쾨펜 분류보다 배경 참고층으로 봅니다.`,
      },
    ];
  }

  const chips = [];
  const firstLetter = code[0];
  const secondLetter = code[1];
  const thirdLetter = code[2];

  const firstMeta = {
    A: { label: "열대", detail: `최한월 ${metrics.coldest.toFixed(1)}°C로 18°C 이상입니다.` },
    B: { label: "건조", detail: `연강수량 ${metrics.annualPrecip.toFixed(0)} mm가 건조 한계 ${metrics.drynessThreshold.toFixed(0)} mm보다 적습니다.` },
    C: { label: "온대", detail: `최한월 ${metrics.coldest.toFixed(1)}°C로 0°C 이상, 최난월 ${metrics.warmest.toFixed(1)}°C로 10°C 이상입니다.` },
    D: { label: "냉대", detail: `최한월 ${metrics.coldest.toFixed(1)}°C로 0°C 미만이며 최난월은 10°C 이상입니다.` },
    E: { label: "한대", detail: `최난월 ${metrics.warmest.toFixed(1)}°C로 10°C 미만입니다.` },
  };
  chips.push({ letter: firstLetter, ...firstMeta[firstLetter] });

  if (firstLetter === "A") {
    const secondMeta = {
      f: { label: "건기 없음", detail: `최건월 ${metrics.driest.toFixed(0)} mm로 60 mm 이상입니다.` },
      m: { label: "몬순", detail: `최건월 ${metrics.driest.toFixed(0)} mm로 Af보다 건조하지만 몬순 한계 ${metrics.monsoonThreshold.toFixed(0)} mm는 넘습니다.` },
      w: { label: "겨울 건기", detail: `연중 고온이지만 겨울철 건기가 뚜렷합니다.` },
      s: { label: "여름 건기", detail: `연중 고온이지만 여름철이 상대적으로 더 건조합니다.` },
    };
    chips.push({ letter: secondLetter, ...secondMeta[secondLetter] });
    return chips;
  }

  if (firstLetter === "B") {
    const secondMeta = {
      W: { label: "사막", detail: `강수가 건조 한계의 절반 이하라 사막 단계입니다.` },
      S: { label: "스텝", detail: `강수가 건조 한계 이하지만 사막보다는 많아 초원 단계입니다.` },
    };
    const thirdMeta = {
      h: { label: "고온", detail: `연평균 기온 ${metrics.annualTemp.toFixed(1)}°C로 18°C 이상입니다.` },
      k: { label: "냉량", detail: `연평균 기온 ${metrics.annualTemp.toFixed(1)}°C로 18°C 미만입니다.` },
    };
    chips.push({ letter: secondLetter, ...secondMeta[secondLetter] });
    chips.push({ letter: thirdLetter, ...thirdMeta[thirdLetter] });
    return chips;
  }

  if (firstLetter === "E") {
    const secondMeta = {
      T: { label: "툰드라", detail: `최난월 ${metrics.warmest.toFixed(1)}°C가 0~10°C 사이입니다.` },
      F: { label: "빙설", detail: `최난월 ${metrics.warmest.toFixed(1)}°C도 0°C 미만입니다.` },
    };
    chips.push({ letter: secondLetter, ...secondMeta[secondLetter] });
    return chips;
  }

  const secondMeta = {
    f: { label: "사계절 습윤", detail: "뚜렷한 건기가 없어 연중 강수가 비교적 고릅니다." },
    w: { label: "겨울 건기", detail: `겨울 최건월 ${metrics.driestWinter.toFixed(0)} mm로 겨울이 뚜렷하게 건조합니다.` },
    s: { label: "여름 건기", detail: `여름 최건월 ${metrics.driestSummer.toFixed(0)} mm로 여름이 뚜렷하게 건조합니다.` },
  };
  const thirdMeta = {
    a: { label: "더운 여름", detail: `최난월 ${metrics.warmest.toFixed(1)}°C로 22°C 이상입니다.` },
    b: { label: "온난한 여름", detail: `10°C 이상 달이 ${metrics.warmMonths}개월이며 최난월은 22°C 미만입니다.` },
    c: { label: "짧고 서늘한 여름", detail: `10°C 이상 달이 ${metrics.warmMonths}개월로 적어 여름이 짧습니다.` },
    d: { label: "혹한 겨울", detail: `매우 추운 겨울이 나타나는 냉대 하위형입니다.` },
  };

  chips.push({ letter: secondLetter, ...secondMeta[secondLetter] });
  chips.push({ letter: thirdLetter, ...thirdMeta[thirdLetter] });
  return chips;
}

function renderSpotlightButtons() {
  spotlightButtons.innerHTML = SPOTLIGHTS
    .map((spot) => {
      const active = Math.abs(spot.latitude - state.selectedLatitude) < 2.5 && Math.abs(spot.longitude - state.selectedLongitude) < 2.5;
      const spotlightScenario = createScenario({
        presetId: spot.presetId,
        month: state.month,
        tilt: state.tilt,
        landScale: state.landScale,
        mountainHeight: state.mountainHeight,
        currentBias: state.currentBias,
      });
      const analysis = withOfficialClassification(analyzeLocation(spot.latitude, spot.longitude, spotlightScenario));
      const details = getKoppenDetails(analysis.classification.code);
      return `
        <button type="button" class="spotlight-button ${active ? "is-active" : ""}" data-spotlight="${spot.id}">
          <strong>${spot.name}</strong>
          <span>${analysis.classification.code} · ${details.label}</span>
        </button>
      `;
    })
    .join("");
}

function renderMissionPanel(scenario) {
  const mission = getCurrentMission();
  const concept = KEY_CONCEPT_PROMPTS[MISSION_TO_CONCEPT[mission.id]];
  const guidance = SCENARIO_GUIDANCE.find((item) => item.id === MISSION_TO_SCENARIO[mission.id])
    ?? SCENARIO_GUIDANCE.find((item) => item.recommendedPreset === scenario.presetId)
    ?? SCENARIO_GUIDANCE[0];

  missionSteps.innerHTML = LESSON_MISSIONS
    .map((item) => `
      <button type="button" class="mission-step ${item.id === mission.id ? "is-active" : ""}" data-mission-id="${item.id}">
        <span>${item.order}</span>
        <strong>${item.title}</strong>
      </button>
    `)
    .join("");

  missionCard.innerHTML = `
    <div class="mission-focus">
      <strong>${mission.title}</strong>
      <p>${mission.focus}</p>
    </div>
    <div class="inline-chips">
      ${mission.knobTargets.map((target) => `<span class="mini-chip">${target}</span>`).join("")}
    </div>
    <div class="mission-grid">
      <section>
        <span>학생 과제</span>
        <p>${mission.studentTask}</p>
      </section>
      <section>
        <span>관찰 포인트</span>
        <p>${mission.observation}</p>
      </section>
      <section>
        <span>질문</span>
        <p>${mission.guidingQuestion}</p>
      </section>
      <section>
        <span>성공 기준</span>
        <p>${mission.successCheck}</p>
      </section>
    </div>
    ${concept ? `
      <div class="concept-card">
        <strong>${concept.title}</strong>
        <p>${concept.prompt}</p>
        <ul>
          ${concept.cues.map((cue) => `<li>${cue}</li>`).join("")}
        </ul>
      </div>
    ` : ""}
  `;

  scenarioGuidance.innerHTML = `
    <div class="guidance-card">
      <div>
        <span class="eyebrow">Teacher Tip</span>
        <strong>${guidance.title}</strong>
      </div>
      <p>${guidance.useWhen}</p>
      <div class="inline-chips">
        <span class="mini-chip">추천 프리셋: ${PRESETS[guidance.recommendedPreset]?.name ?? guidance.recommendedPreset}</span>
      </div>
      <ul>
        ${guidance.suggestedMoves.map((step) => `<li>${step}</li>`).join("")}
      </ul>
      <p class="guidance-note">${guidance.teacherNote}</p>
      <button type="button" class="guidance-button" data-guidance-preset="${guidance.recommendedPreset}">추천 프리셋 적용</button>
    </div>
  `;
}
function renderSelectionCard(analysis, scenario) {
  const details = getKoppenDetails(analysis.classification.code);
  const breakdowns = getBreakdowns(analysis, scenario);
  const traceRows = getRuleTraceRows(analysis);
  const context = resolveSelectionContext(analysis);
  const letterRows = getKoppenLetterBreakdown(analysis);
  const isOceanCell = analysis.classification.code === "Ocean";

  selectionLabel.textContent = `${context.title} · ${formatCoordinate(analysis.latitude, analysis.longitude)}`;
  selectionKoppen.innerHTML = `
    <span class="koppen-badge" style="background:${KOPPEN_COLORS[analysis.classification.code] ?? "#5e7483"}">${analysis.classification.code}</span>
    <div>
      <strong>${details.group} ${details.label}</strong>
      <p>${details.summary}</p>
    </div>
  `;
  selectionSummary.textContent = isOceanCell
    ? `선택 위치는 해양 셀입니다. 공식 Beck 쾨펜 지도에서도 해양/무자료 영역이며, 월별 차트는 육상 ${ACTIVE_CLIMATE_DATASET.resolution} WorldClim 자료만 제공합니다.`
    : `${MONTH_LABELS[state.month - 1]} 기준 설명 차트는 ${analysis.selectedMonth.pressureBand}와 ${analysis.profile.wind.label}의 영향을 보여 주고, 지도 코드는 Beck 2026 v2 1991-2020 공식 쾨펜 지도를 따릅니다.`;
  selectionContext.innerHTML = `
    <div class="context-title">
      <strong>${context.subtitle}</strong>
      <span>${context.macroRegion}</span>
    </div>
    <div class="inline-chips">
      <span class="mini-chip">${context.latitudeZone}</span>
      <span class="mini-chip">${context.surfaceContext}</span>
      <span class="mini-chip">현재 코드 ${analysis.classification.code}</span>
    </div>
    <p>${context.note}</p>
  `;
  koppenBreakdown.innerHTML = letterRows
    .map((item) => `
      <article class="letter-chip">
        <span class="letter-symbol">${item.letter}</span>
        <strong>${item.label}</strong>
        <p>${item.detail}</p>
      </article>
    `)
    .join("");

  annualFacts.innerHTML = isOceanCell
    ? `<div class="fact-pill"><span>자료 범위</span><strong>육상 ${ACTIVE_CLIMATE_DATASET.resolution} 월평균 기후 자료만 제공</strong></div>`
    : [
        ["연평균 기온", `${analysis.annual.meanTemp.toFixed(1)}°C`],
        ["연강수량", `${analysis.annual.annualPrecip.toFixed(0)} mm`],
        ["가장 더운 달", `${analysis.annual.warmestTemp.toFixed(1)}°C`],
        ["가장 추운 달", `${analysis.annual.coldestTemp.toFixed(1)}°C`],
        ["지도 코드", analysis.classification.source ?? "WorldClim 기반 계산"],
      ]
        .map(([label, value]) => `<div class="fact-pill"><span>${label}</span><strong>${value}</strong></div>`)
        .join("");

  monthlyFactors.innerHTML = [
    ["기압대", analysis.selectedMonth.pressureBand],
    ["바람", `${analysis.profile.wind.label} (${analysis.profile.wind.shortArrow})`],
    ["바다 영향", analysis.profile.coastalness > 0.35 ? "강함" : analysis.profile.coastalness > 0.15 ? "보통" : "약함"],
    ["대륙 내부", analysis.profile.interiorness > 0.45 ? "강함" : analysis.profile.interiorness > 0.2 ? "보통" : "약함"],
    ["산맥 효과", analysis.selectedMonth.orographicWet > analysis.selectedMonth.shadowDry ? "바람받이 우세" : analysis.selectedMonth.shadowDry > 10 ? "비그늘 우세" : "약함"],
    ["푄", analysis.selectedMonth.foehnWarm > 1.2 ? `+${analysis.selectedMonth.foehnWarm.toFixed(1)}°C` : "거의 없음"],
  ]
    .map(([label, value]) => `<div class="factor-chip"><span>${label}</span><strong>${value}</strong></div>`)
    .join("");

  driverStacks.innerHTML = `
    ${renderDriverSection("이번 달 기온 기여", breakdowns.temperature)}
    ${renderDriverSection("이번 달 강수 기여", breakdowns.precipitation)}
  `;

  ruleTrace.innerHTML = traceRows
    .map((row) => `
      <div class="trace-card ${row.state}">
        <span>${row.label}</span>
        <strong>${row.value}</strong>
        <p>${row.detail}</p>
      </div>
    `)
    .join("");

  reasonList.innerHTML = analysis.reasons.map((reason) => `<li>${reason}</li>`).join("");
}

function renderClimateChart(analysis) {
  if (analysis.classification.code === "Ocean") {
    climateChart.innerHTML = `
      <div class="chart-empty">
        <strong>해양 셀</strong>
        <p>현재 월별 실측 자료는 육상 ${ACTIVE_CLIMATE_DATASET.resolution} WorldClim 격자를 사용합니다. 바다는 쾨펜 차트 대신 안내만 표시합니다.</p>
      </div>
    `;
    return;
  }

  const width = 560;
  const height = 250;
  const margin = { top: 18, right: 26, bottom: 34, left: 38 };
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;
  const maxPrecip = Math.max(160, ...analysis.precipitations) * 1.1;
  const minTemp = Math.min(...analysis.temperatures) - 4;
  const maxTemp = Math.max(...analysis.temperatures) + 4;
  const xStep = innerWidth / 12;

  const bars = analysis.precipitations
    .map((value, index) => {
      const x = margin.left + index * xStep + 8;
      const barHeight = (value / maxPrecip) * innerHeight;
      const y = margin.top + innerHeight - barHeight;
      return `<rect x="${x.toFixed(1)}" y="${y.toFixed(1)}" width="${(xStep - 16).toFixed(1)}" height="${barHeight.toFixed(1)}" rx="6" fill="rgba(79, 191, 198, ${index + 1 === state.month ? 0.95 : 0.55})" />`;
    })
    .join("");

  const tempPath = analysis.temperatures
    .map((value, index) => {
      const x = margin.left + index * xStep + xStep / 2;
      const normalized = (value - minTemp) / Math.max(maxTemp - minTemp, 1);
      const y = margin.top + innerHeight - normalized * innerHeight;
      return `${index === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");

  const monthLabels = MONTH_LABELS.map((label, index) => {
    const x = margin.left + index * xStep + xStep / 2;
    return `<text x="${x.toFixed(1)}" y="${height - 10}" class="axis-label">${label.replace("월", "")}</text>`;
  }).join("");

  climateChart.innerHTML = `
    <svg viewBox="0 0 ${width} ${height}" role="img" aria-label="월별 기온과 강수량 차트">
      <defs>
        <linearGradient id="tempLineGradient" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stop-color="#ffd06b" />
          <stop offset="100%" stop-color="#f16b45" />
        </linearGradient>
      </defs>
      <rect x="0" y="0" width="${width}" height="${height}" fill="transparent" />
      <line x1="${margin.left}" y1="${margin.top + innerHeight}" x2="${width - margin.right}" y2="${margin.top + innerHeight}" class="chart-axis" />
      <line x1="${margin.left}" y1="${margin.top}" x2="${margin.left}" y2="${margin.top + innerHeight}" class="chart-axis" />
      ${bars}
      <path d="${tempPath}" fill="none" stroke="url(#tempLineGradient)" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" />
      ${analysis.temperatures
        .map((value, index) => {
          const x = margin.left + index * xStep + xStep / 2;
          const normalized = (value - minTemp) / Math.max(maxTemp - minTemp, 1);
          const y = margin.top + innerHeight - normalized * innerHeight;
          return `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${index + 1 === state.month ? 5 : 3.5}" fill="#fff3d6" stroke="#f16b45" stroke-width="2" />`;
        })
        .join("")}
      <text x="${margin.left}" y="${margin.top - 2}" class="axis-title">강수량 (mm)</text>
      <text x="${width - margin.right}" y="${margin.top - 2}" text-anchor="end" class="axis-title">기온 (°C)</text>
      ${monthLabels}
    </svg>
  `;
}

function renderCirculation(analysis, scenario) {
  const width = 360;
  const height = 320;
  const toY = (latitude) => ((90 - latitude) / 180) * (height - 40) + 20;
  const itczY = toY(analysis.selectedMonth.itczLat);
  const bandDefs = [
    { top: 90, bottom: 60, label: "극고압대 / 극동풍", color: "rgba(154, 194, 219, 0.22)" },
    { top: 60, bottom: 25, label: "아극 저압대 / 편서풍", color: "rgba(99, 169, 211, 0.24)" },
    { top: 25, bottom: 0, label: "아열대 고압대 / 무역풍", color: "rgba(241, 184, 83, 0.18)" },
    { top: 0, bottom: -25, label: "아열대 고압대 / 무역풍", color: "rgba(241, 184, 83, 0.18)" },
    { top: -25, bottom: -60, label: "아극 저압대 / 편서풍", color: "rgba(99, 169, 211, 0.24)" },
    { top: -60, bottom: -90, label: "극고압대 / 극동풍", color: "rgba(154, 194, 219, 0.22)" },
  ];

  const bands = bandDefs
    .map((band) => {
      const y = toY(band.top);
      const nextY = toY(band.bottom);
      return `
        <rect x="52" y="${y}" width="256" height="${nextY - y}" rx="18" fill="${band.color}" />
        <text x="180" y="${y + (nextY - y) / 2 + 4}" class="band-label" text-anchor="middle">${band.label}</text>
      `;
    })
    .join("");

  const latitudeTicks = [60, 30, 0, -30, -60]
    .map((latitude) => {
      const y = toY(latitude);
      return `
        <line x1="36" y1="${y}" x2="320" y2="${y}" class="grid-line" />
        <text x="22" y="${y + 4}" class="axis-label" text-anchor="end">${latitude}°</text>
      `;
    })
    .join("");

  circulationSvg.innerHTML = `
    <svg viewBox="0 0 ${width} ${height}" role="img" aria-label="위도대별 대기대순환 도식">
      ${bands}
      ${latitudeTicks}
      <line x1="52" y1="${itczY}" x2="308" y2="${itczY}" class="itcz-line" />
      <text x="314" y="${itczY + 4}" class="itcz-label">ITCZ</text>
      <line x1="52" y1="${toY(state.selectedLatitude)}" x2="308" y2="${toY(state.selectedLatitude)}" class="probe-line" />
      <circle cx="180" cy="${toY(state.selectedLatitude)}" r="6" class="probe-dot" />
    </svg>
  `;

  const wind = describeWindBand(state.selectedLatitude);
  circulationFacts.innerHTML = [
    ["선택 달 ITCZ", `${analysis.selectedMonth.itczLat.toFixed(1)}°`],
    ["선택 위치 기압대", analysis.selectedMonth.pressureBand],
    ["선택 위치 바람", `${wind.label} · ${wind.shortArrow}`],
    ["자전축 기울기", `${scenario.tilt.toFixed(1)}°`],
  ]
    .map(([label, value]) => `<div class="fact-pill compact"><span>${label}</span><strong>${value}</strong></div>`)
    .join("");
}
function renderTransect(scenario) {
  const data = sampleTransect(state.selectedLatitude, scenario.month, scenario);
  const width = 560;
  const height = 250;
  const margin = { top: 22, right: 20, bottom: 28, left: 28 };
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;
  const maxElevation = Math.max(1500, ...data.map((item) => item.elevation)) * 1.05;
  const maxPrecip = Math.max(120, ...data.map((item) => item.precipitation)) * 1.05;
  const lonSpan = LONGITUDES.length - 1;

  const xForIndex = (index) => margin.left + (index / lonSpan) * innerWidth;
  const elevationY = (value) => margin.top + innerHeight - (value / maxElevation) * innerHeight * 0.52;
  const precipY = (value) => margin.top + innerHeight - (value / maxPrecip) * innerHeight;

  const terrainPath = data
    .map((item, index) => `${index === 0 ? "M" : "L"}${xForIndex(index).toFixed(1)},${elevationY(item.elevation).toFixed(1)}`)
    .join(" ");
  const terrainClosed = `${terrainPath} L ${xForIndex(lonSpan).toFixed(1)},${(margin.top + innerHeight).toFixed(1)} L ${xForIndex(0).toFixed(1)},${(margin.top + innerHeight).toFixed(1)} Z`;
  const precipPath = data
    .map((item, index) => `${index === 0 ? "M" : "L"}${xForIndex(index).toFixed(1)},${precipY(item.precipitation).toFixed(1)}`)
    .join(" ");
  const selectedIndex = data.findIndex((item) => Math.abs(item.longitude - state.selectedLongitude) < 2.6);
  const selectedX = xForIndex(Math.max(0, selectedIndex));
  const mountainX = margin.left + ((scenario.mountainLon + 180) / 360) * innerWidth;

  transectSvg.innerHTML = `
    <svg viewBox="0 0 ${width} ${height}" role="img" aria-label="선택 위도의 지형과 강수 단면도">
      <defs>
        <linearGradient id="terrainGradient" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#f8d77a" />
          <stop offset="100%" stop-color="#7b5438" />
        </linearGradient>
      </defs>
      <rect x="0" y="0" width="${width}" height="${height}" fill="transparent" />
      <line x1="${margin.left}" y1="${margin.top + innerHeight}" x2="${width - margin.right}" y2="${margin.top + innerHeight}" class="chart-axis" />
      <path d="${terrainClosed}" fill="url(#terrainGradient)" opacity="0.88" />
      <path d="${precipPath}" fill="none" stroke="#61d6dc" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" />
      <line x1="${mountainX.toFixed(1)}" y1="${margin.top}" x2="${mountainX.toFixed(1)}" y2="${margin.top + innerHeight}" class="mountain-line" />
      <line x1="${selectedX.toFixed(1)}" y1="${margin.top}" x2="${selectedX.toFixed(1)}" y2="${margin.top + innerHeight}" class="probe-line" />
      <text x="${mountainX.toFixed(1)}" y="${margin.top - 4}" text-anchor="middle" class="axis-label">산맥</text>
      <text x="${selectedX.toFixed(1)}" y="${height - 8}" text-anchor="middle" class="axis-label">선택 위치</text>
    </svg>
  `;

  transectCaption.textContent = `${formatCoordinate(state.selectedLatitude, state.selectedLongitude)}와 같은 위도대를 따라 잘라 본 단면입니다. 편서풍/무역풍이 산맥을 넘을 때 강수와 푄이 어떻게 달라지는지 비교하세요.`;
}

function renderSpotlightButtonsSection() {
  renderSpotlightButtons();
}

function renderMapAndPanels() {
  const scenario = buildScenarioFromState();
  const world = buildWorld(scenario);
  const analysis = withOfficialClassification(analyzeLocation(state.selectedLatitude, state.selectedLongitude, scenario));

  updateControlUI();
  renderLegend();
  renderMap(world, scenario);
  renderSpotlightButtonsSection();
  renderMissionPanel(scenario);
  renderSelectionCard(analysis, scenario);
  renderClimateChart(analysis);
  renderCirculation(analysis, scenario);
  renderTransect(scenario);
}

function handleMapSelection(event) {
  const rect = mapCanvas.getBoundingClientRect();
  const x = clamp((event.clientX - rect.left) / Math.max(rect.width, 1), 0, 1);
  const y = clamp((event.clientY - rect.top) / Math.max(rect.height, 1), 0, 1);
  state.selectedLongitude = x * 360 - 180;
  state.selectedLatitude = 90 - y * 180;
  queueRender();
}

function bindEvents() {
  controls.preset.addEventListener("change", (event) => applyPreset(event.target.value));
  controls.month.addEventListener("input", (event) => {
    state.month = Number(event.target.value);
    updateControlUI();
    queueRender();
  });
  controls.tilt.addEventListener("input", (event) => {
    state.tilt = Number(event.target.value);
    updateControlUI();
    queueRender();
  });
  controls.landScale.addEventListener("input", (event) => {
    state.landScale = Number(event.target.value);
    updateControlUI();
    queueRender();
  });
  controls.mountainHeight.addEventListener("input", (event) => {
    state.mountainHeight = Number(event.target.value);
    updateControlUI();
    queueRender();
  });

  controls.currentButtons.forEach((button) => {
    button.addEventListener("click", () => {
      state.currentBias = Number(button.dataset.currentBias);
      updateControlUI();
      queueRender();
    });
  });

  controls.overlayButtons.forEach((button) => {
    button.addEventListener("click", () => {
      state.overlay = button.dataset.overlay;
      updateControlUI();
      queueRender();
    });
  });

  missionSteps.addEventListener("click", (event) => {
    const button = event.target.closest("[data-mission-id]");
    if (!button) {
      return;
    }
    state.missionId = button.dataset.missionId;
    updateControlUI();
    queueRender();
  });

  scenarioGuidance.addEventListener("click", (event) => {
    const button = event.target.closest("[data-guidance-preset]");
    if (!button) {
      return;
    }
    applyPreset(button.dataset.guidancePreset);
  });

  spotlightButtons.addEventListener("click", (event) => {
    const button = event.target.closest("[data-spotlight]");
    if (!button) {
      return;
    }
    jumpToSpotlight(button.dataset.spotlight);
  });

  mapCanvas.addEventListener("click", handleMapSelection);
  window.addEventListener("resize", queueRender);

  foldPanels.forEach((panel) => {
    panel.addEventListener("toggle", () => {
      if (panel.open) {
        queueRender();
      }
    });
  });
}

function initializeFoldPanels() {
  const isCompactViewport = window.matchMedia("(max-width: 760px)").matches;
  if (!isCompactViewport) {
    return;
  }

  foldPanels.forEach((panel) => {
    if (panel.dataset.mobileCollapsed === "true") {
      panel.open = false;
    }
  });
}

async function loadOfficialKoppenLayer() {
  try {
    const response = await fetch(OFFICIAL_KOPPEN_BINARY_URL);
    if (!response.ok) {
      throw new Error(`Official Koppen fetch failed: ${response.status}`);
    }

    const buffer = await response.arrayBuffer();
    const codes = new Uint8Array(buffer);
    officialKoppenLayer = {
      ready: true,
      width: OFFICIAL_KOPPEN_META.width,
      height: OFFICIAL_KOPPEN_META.height,
      codes,
      canvas: buildOfficialKoppenCanvas(codes),
    };
  } catch (error) {
    console.warn("Using coarse Koppen fallback.", error);
  }
}

async function loadWorldGeometry() {
  try {
    const [landResponse, countriesResponse] = await Promise.all([
      fetch(LAND_GEOJSON_URL),
      fetch(COUNTRY_GEOJSON_URL),
    ]);

    if (!landResponse.ok || !countriesResponse.ok) {
      throw new Error(`World map fetch failed: ${landResponse.status}/${countriesResponse.status}`);
    }

    const [land, countries] = await Promise.all([landResponse.json(), countriesResponse.json()]);
    worldGeometry = { land, countries };
  } catch (error) {
    console.warn("Using fallback world overlay.", error);
  }
}

function render() {
  renderMapAndPanels();
}

async function init() {
  populatePresetSelect();
  initializeFoldPanels();
  bindEvents();
  updateControlUI();
  await Promise.all([loadWorldGeometry(), loadOfficialKoppenLayer()]);
  render();
}

void init();
