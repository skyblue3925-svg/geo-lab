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
  getKoppenDetails,
  sampleTransect,
} from "./climate-model.mjs";
import { KEY_CONCEPT_PROMPTS, LESSON_MISSIONS, SCENARIO_GUIDANCE } from "./lesson-data.mjs";
import { EXAM_CLIMATE_SPOTS } from "./data/exam-climate-spots.mjs";
import { EXAM_CLIMATE_COORDINATES } from "./data/exam-climate-spot-coordinates.mjs";
import {
  OFFICIAL_KOPPEN_BINARY_URL,
  OFFICIAL_KOPPEN_BY_CODE,
  OFFICIAL_KOPPEN_BY_ID,
  OFFICIAL_KOPPEN_META,
} from "./data/koppen-geiger-1991-2020.mjs";
import {
  getClassificationMetrics,
  getClimateComparisonNote,
  getGraphClimateCode,
  getGraphClimateDisplayCode,
} from "./climate-interpretation.mjs";
import {
  getKoppenLetterBreakdown,
  getRuleTraceRows,
} from "./classification-panels.mjs";
import {
  buildControlPanelViewModel,
  getLeverGuideItems as getLeverGuideViewItems,
} from "./control-view-models.mjs";
import {
  buildClimateChartMarkup,
  buildClimateChartSvgMarkup,
} from "./climate-chart-view.mjs";
import { buildSelectionCardRenderModel } from "./selection-card-models.mjs";
import {
  buildExamSpotButtonsMarkup,
  buildMissionCardMarkup,
  buildMissionStepsMarkup,
  buildScenarioGuidanceMarkup,
  buildSpotlightButtonsMarkup,
} from "./aux-panels-view.mjs";
import {
  WORLD_MAP_BORDERS,
  WORLD_MAP_REGIONS,
} from "./world-map-data.mjs";
import {
  buildCirculationFactsMarkup,
  buildCirculationSvgMarkup,
} from "./circulation-view.mjs";
import {
  drawMapBaseLayer,
  drawExamSpotMarkers,
  drawMapOverlayAnnotations,
  drawSelectedLocationMarker,
  drawSpotlightMarkers,
} from "./map-render-view.mjs";
import { drawMapAxes, drawWorldOverlay } from "./world-overlay-view.mjs";
import {
  buildDriverInsightCardsMarkup,
  buildDriverSectionMarkup,
  getClimateDriverBreakdowns,
} from "./driver-insights-view.mjs";
import { buildDashboardScene } from "./dashboard-scene.mjs";
import { resolveMapClickSelection } from "./map-selection-models.mjs";
import {
  applyCompareSelection,
  applyCirculationStageChange,
  applyClimateModeChange,
  applyCurrentBiasChange,
  clearCompareSelection,
  applyLandScaleChange,
  applyMissionChange,
  applyMonthChange,
  applyMountainHeightChange,
  applyOverlayChange,
  applyScreenModeChange,
  applySelectionCoordinates,
  applyTiltChange,
} from "./ui-state-actions.mjs";
import { buildLegendMarkup } from "./legend-view.mjs";
import {
  buildTransectCaptionText,
  buildTransectSvgMarkup,
} from "./transect-view.mjs";
import {
  CLIMATE_VIEW_MODES,
  SCREEN_MODES,
  applyPresetSelection,
  buildScenarioFromState as buildScenarioFromAppState,
  createInitialAppState,
  getCurrentClimateModeMeta as getCurrentClimateModeMetaForState,
  getCurrentScreenModeMeta as getCurrentScreenModeMetaForState,
  isObservedAppMode as isObservedStateMode,
  syncScreenMode as syncScreenModeForState,
} from "./app-state.mjs";

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

const CIRCULATION_STAGES = [
  { id: "surface", label: "표층", note: "표층 바람과 기압대 위치를 먼저 읽습니다." },
  { id: "vertical", label: "상승·하강", note: "표층 바람에 상승·하강과 3-cell 셸을 더해 순환 구조를 읽습니다." },
  { id: "upper", label: "상층·제트", note: "상층 흐름, 아열대 제트, 한대전선 제트까지 함께 봅니다." },
];
const EXAM_SPOT_BUTTON_LIMIT = 24;

const mapCanvas = document.querySelector("#mapCanvas");
const dashboard = document.querySelector(".dashboard");
const heroCard = document.querySelector(".hero");
const mapCard = document.querySelector(".map-card");
const mapStage = document.querySelector(".map-stage");
const mapFrame = document.querySelector(".map-frame");
const experimentLeverStrip = document.querySelector("#experimentLeverStrip");
const utilityGrid = document.querySelector(".utility-grid");
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
const compareStatus = document.querySelector("#compareStatus");
const compareSection = document.querySelector("#compareSection");
const setCompareAnchorButton = document.querySelector("#setCompareAnchorButton");
const clearCompareButton = document.querySelector("#clearCompareButton");
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
const experimentControlsCard = utilityGrid?.querySelector("[data-fold-panel]");
const experimentMonthBlock = experimentControlsCard?.querySelector("#monthRange")?.closest(".control-block");
const controlGrid = document.querySelector(".control-stack.control-grid");
let experimentLeverToggle = null;

if (experimentMonthBlock) {
  experimentMonthBlock.remove();
}

if (experimentControlsCard) {
  experimentControlsCard.classList.add("experiment-controls-card");
}

if (experimentLeverStrip && controlGrid && mapFrame) {
  const header = document.createElement("div");
  header.className = "experiment-lever-strip-header";
  header.innerHTML = `
    <div class="experiment-lever-strip-title">
      <span class="eyebrow">Experiment Levers</span>
      <strong>실험 레버</strong>
    </div>
    <button type="button" class="experiment-lever-toggle" aria-expanded="true">접기</button>
  `;
  experimentLeverToggle = header.querySelector(".experiment-lever-toggle");
  experimentLeverStrip.replaceChildren(header, controlGrid);
  mapFrame.append(experimentLeverStrip);
}

function syncExperimentLeverToggle() {
  if (!experimentLeverStrip || !experimentLeverToggle) {
    return;
  }
  const collapsed = experimentLeverStrip.classList.contains("is-collapsed");
  experimentLeverToggle.textContent = collapsed ? "열기" : "접기";
  experimentLeverToggle.setAttribute("aria-expanded", String(!collapsed));
}

experimentLeverToggle?.addEventListener("click", () => {
  experimentLeverStrip?.classList.toggle("is-collapsed");
  syncExperimentLeverToggle();
});

syncExperimentLeverToggle();

const knobBlocks = Array.from(document.querySelectorAll("[data-knob]"));
const foldPanels = Array.from(document.querySelectorAll("[data-fold-panel]"));
const controlNote = document.querySelector(".control-note");
const overlaySegmented = document.querySelector(".map-tools .segmented.small");
const TRADE_CROSS_EQUATOR_THRESHOLD = 4;
const chartExportRegistry = new Map();

const examSpotButtonsSection = (() => {
  if (!spotlightButtons?.parentElement) {
    return null;
  }
  const existing = spotlightButtons.parentElement.querySelector(".exam-spotlight-section");
  if (existing) {
    return existing;
  }
  const section = document.createElement("div");
  section.className = "exam-spotlight-section";
  section.innerHTML = `
    <div class="spotlight-mini-head">
      <div>
        <p class="eyebrow">Exam Hotspots</p>
        <h4>평가원 빈출 기후 지점</h4>
      </div>
      <span class="spotlight-meta">상위 ${EXAM_SPOT_BUTTON_LIMIT}개</span>
    </div>
    <p class="card-copy">평가원 기출 지점 정리는 광성고 김성빈 선생님 자료를 참고하여 구성했습니다.</p>
    <div id="examSpotButtons" class="spotlight-grid"></div>
  `;
  spotlightButtons.parentElement.append(section);
  return section;
})();
const examSpotButtons = examSpotButtonsSection?.querySelector("#examSpotButtons") ?? null;

const EXAM_SPOTLIGHTS = EXAM_CLIMATE_SPOTS
  .map((record) => {
    const coordinates = EXAM_CLIMATE_COORDINATES[record.displayName] ?? EXAM_CLIMATE_COORDINATES[record.rawName];
    if (!coordinates) {
      return null;
    }
    return {
      id: record.id,
      name: record.displayName,
      rawName: record.rawName,
      examCode: record.examCode,
      examDates: record.examDates,
      examCount: record.examCount,
      latitude: coordinates.latitude,
      longitude: coordinates.longitude,
      note: coordinates.note ?? `${record.examCount}회 출제`,
      confidence: coordinates.confidence ?? "high",
      presetId: "earthLite",
    };
  })
  .filter(Boolean)
  .sort((left, right) => right.examCount - left.examCount || left.name.localeCompare(right.name, "ko"));

if (overlaySegmented && !overlaySegmented.querySelector('[data-overlay="circulation"]')) {
  const button = document.createElement("button");
  button.type = "button";
  button.dataset.overlay = "circulation";
  button.textContent = "대기순환";
  overlaySegmented.append(button);
}

const circulationStageToggle = (() => {
  if (!overlaySegmented?.parentElement) {
    return null;
  }
  const existing = overlaySegmented.parentElement.querySelector(".circulation-stage-toggle");
  if (existing) {
    return existing;
  }
  const wrapper = document.createElement("div");
  wrapper.className = "segmented small circulation-stage-toggle";
  CIRCULATION_STAGES.forEach((stage) => {
    const button = document.createElement("button");
    button.type = "button";
    button.dataset.circulationStage = stage.id;
    button.textContent = stage.label;
    wrapper.append(button);
  });
  overlaySegmented.parentElement.append(wrapper);
  return wrapper;
})();

const climateModeToggle = (() => {
  if (!controlGrid) {
    return null;
  }
  const existing = controlGrid.querySelector(".climate-mode-block");
  if (existing) {
    return existing.querySelector(".segmented");
  }
  const block = document.createElement("div");
  block.className = "control-block control-span-2 climate-mode-block";
  block.innerHTML = `
    <span class="control-row">
      <span class="control-label">보기 모드</span>
      <strong>월은 두 모드 모두 유지</strong>
    </span>
    <div class="segmented" data-climate-mode-toggle>
      ${CLIMATE_VIEW_MODES.map((mode) => `<button type="button" data-climate-mode="${mode.id}">${mode.shortLabel}</button>`).join("")}
    </div>
    <p class="control-copy">관측 모드는 공식 지도와 실측 월별 수치를 유지하고, 실험 모드는 레버를 지도와 그래프에 직접 반영합니다.</p>
  `;
  controlGrid.prepend(block);
  return block.querySelector("[data-climate-mode-toggle]");
})();
const climateModeBlock = climateModeToggle?.closest(".control-block") ?? null;

const screenModeToggle = (() => {
  if (!heroCard) {
    return null;
  }
  const existing = heroCard.querySelector(".screen-mode-toggle");
  if (existing) {
    return existing;
  }
  const wrapper = document.createElement("div");
  wrapper.className = "screen-mode-toggle";
  wrapper.innerHTML = `
    <div class="segmented small screen-mode-buttons">
      ${SCREEN_MODES.map((mode) => `<button type="button" data-screen-mode="${mode.id}">${mode.label}</button>`).join("")}
    </div>
    <p class="screen-mode-note"></p>
  `;
  heroCard.append(wrapper);
  return wrapper;
})();

const leverGuide = (() => {
  if (!controlNote?.parentElement) {
    return null;
  }
  const existing = controlNote.parentElement.querySelector(".lever-guide");
  if (existing) {
    return existing;
  }
  const section = document.createElement("section");
  section.className = "guidance-card lever-guide";
  controlNote.insertAdjacentElement("afterend", section);
  return section;
})();

const controls = {
  screenModeToggle,
  screenModeButtons: Array.from(document.querySelectorAll("[data-screen-mode]")),
  climateModeToggle,
  climateModeButtons: Array.from(document.querySelectorAll("[data-climate-mode]")),
  preset: document.querySelector("#presetSelect"),
  monthRanges: Array.from(document.querySelectorAll("[data-month-range]")),
  monthValues: Array.from(document.querySelectorAll("[data-month-value]")),
  tilt: document.querySelector("#tiltRange"),
  tiltValue: document.querySelector("#tiltValue"),
  landScale: document.querySelector("#landScaleRange"),
  landScaleValue: document.querySelector("#landScaleValue"),
  mountainHeight: document.querySelector("#mountainRange"),
  mountainHeightValue: document.querySelector("#mountainValue"),
  currentButtons: Array.from(document.querySelectorAll("[data-current-bias]")),
  overlayButtons: Array.from(document.querySelectorAll("[data-overlay]")),
  circulationStageToggle,
  circulationStageButtons: Array.from(document.querySelectorAll("[data-circulation-stage]")),
};

const defaultPreset = PRESETS.earthLite;
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
let lastCompactViewportState = null;

const hasObservedClimateDataset = CLIMATE_DATA_MODE === "observed";
const state = createInitialAppState({
  defaultPreset,
  firstCirculationStageId: CIRCULATION_STAGES[0].id,
  firstMissionId: LESSON_MISSIONS[0].id,
  hasObservedClimateDataset,
});
const experimentalControlBlocks = [
  controls.preset?.closest(".control-block"),
  controls.tilt?.closest(".control-block"),
  controls.landScale?.closest(".control-block"),
  controls.mountainHeight?.closest(".control-block"),
  controls.currentButtons[0]?.closest(".control-block"),
].filter(Boolean);

function isObservedAppMode() {
  return isObservedStateMode(state, hasObservedClimateDataset);
}

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
  const referenceClassification = analysis.classification;
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
    referenceClassification,
    reasons,
  };
}

function getCurrentClimateModeMeta() {
  return getCurrentClimateModeMetaForState(state, CLIMATE_VIEW_MODES);
}

function getCurrentScreenModeMeta() {
  return getCurrentScreenModeMetaForState(state, SCREEN_MODES);
}

function syncScreenMode() {
  return syncScreenModeForState(state, { hasObservedClimateDataset, screenModes: SCREEN_MODES });
}

function finalizeAnalysisForMode(analysis) {
  if (isObservedAppMode()) {
    return withOfficialClassification(analysis);
  }

  return {
    ...analysis,
    classification: {
      ...analysis.classification,
      source: "실험 모드 계산",
      approximate: false,
    },
    referenceClassification: analysis.classification,
    reasons: [
      `실험 모드에서는 현재 레버 조건으로 계산한 기후 코드(${analysis.classification.code})를 사용합니다.`,
      ...analysis.reasons.slice(0, 5),
    ],
    observed: false,
    dataSource: {
      mode: "experimental",
      dataset: "Synthetic classroom model",
      period: "current lever state",
      resolution: "1°",
    },
  };
}

function getLeverGuideItems() {
  return getLeverGuideViewItems({
    observedMode: isObservedAppMode(),
  });
}

function renderLeverGuide() {
  if (!leverGuide) {
    return;
  }
  const observedMode = isObservedAppMode();
  const modeMeta = getCurrentClimateModeMeta();
  const items = getLeverGuideItems();
  leverGuide.innerHTML = `
    <div>
      <span class="eyebrow">Lever Guide</span>
      <strong>실험 레버가 바꾸는 것</strong>
    </div>
    <p>${observedMode
      ? `${modeMeta.label}에서는 월만 직접 반영되고, 나머지 레버는 설명 비교용으로 잠겨 있습니다.`
      : `${modeMeta.label}에서는 아래 레버가 지도, 그래프, 기후 코드 계산에 직접 반영됩니다.`}</p>
    <div class="lever-guide-grid">
      ${items.map((item) => `
        <article class="lever-guide-item">
          <strong>${item.name}</strong>
          <p>${item.effect}</p>
          <p class="lever-guide-note">${item.detail}</p>
        </article>
      `).join("")}
    </div>
  `;
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

function getMapPlotBounds(width, height) {
  const shellMode = state.overlay === "circulation";
  const left = Math.round(width * (shellMode ? 0.17 : 0.055));
  const right = Math.round(width * (shellMode ? 0.17 : 0.022));
  const top = Math.round(height * 0.04);
  const bottom = Math.round(height * 0.075);
  return {
    left,
    top,
    width: Math.max(1, width - left - right),
    height: Math.max(1, height - top - bottom),
    right: Math.max(left + 1, width - right),
    bottom: Math.max(top + 1, height - bottom),
  };
}

function formatCoordinate(latitude, longitude) {
  const latLabel = `${Math.abs(latitude).toFixed(1)}°${latitude >= 0 ? "N" : "S"}`;
  const lonLabel = `${Math.abs(longitude).toFixed(1)}°${longitude >= 0 ? "E" : "W"}`;
  return `${latLabel}, ${lonLabel}`;
}

function formatLatitudeAxisLabel(latitude) {
  if (latitude === 0) {
    return "0°";
  }
  return `${Math.abs(latitude)}°${latitude > 0 ? "N" : "S"}`;
}

function formatLongitudeAxisLabel(longitude) {
  if (Math.abs(longitude) === 180) {
    return "180°";
  }
  if (longitude === 0) {
    return "0°";
  }
  return `${Math.abs(longitude)}°${longitude > 0 ? "E" : "W"}`;
}

function wrappedLongitudeDistance(left, right) {
  const delta = Math.abs(left - right) % 360;
  return delta > 180 ? 360 - delta : delta;
}

function getSpotlightDistance(latitude, longitude, spotlight) {
  const lonDistance = wrappedLongitudeDistance(longitude, spotlight.longitude) * Math.cos(degToRad((latitude + spotlight.latitude) / 2));
  return Math.hypot(latitude - spotlight.latitude, lonDistance);
}

function isCoordinateNear(latitude, longitude, targetLatitude, targetLongitude, tolerance = 2.4) {
  return Math.abs(latitude - targetLatitude) < tolerance
    && wrappedLongitudeDistance(longitude, targetLongitude) < tolerance;
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

function getActiveExamSpotAt(latitude, longitude) {
  return EXAM_SPOTLIGHTS.find((spot) => isCoordinateNear(latitude, longitude, spot.latitude, spot.longitude, 1.8)) ?? null;
}

function resolveSelectionContext(analysis, activeExamSpot = getActiveExamSpotAt(analysis.latitude, analysis.longitude)) {
  const nearest = getNearestSpotlight(analysis.latitude, analysis.longitude);
  const macroRegion = getMacroRegionLabel(analysis.latitude, analysis.longitude);
  const latitudeZone = getLatitudeZoneLabel(analysis.latitude);
  const surfaceContext = getSurfaceContextLabel(analysis);
  const comparisonNote = activeExamSpot ? getClimateComparisonNote(analysis, activeExamSpot, isObservedAppMode()) : null;
  const graphCode = comparisonNote?.graphDisplayCode ?? getGraphClimateDisplayCode(analysis, activeExamSpot);
  const examMismatch = Boolean(comparisonNote?.examMismatch);
  if (activeExamSpot) {
    const examSpotTitle = activeExamSpot.name ?? activeExamSpot.displayName ?? activeExamSpot.rawName ?? macroRegion;
    return {
      title: examSpotTitle,
      subtitle: `평가원 기출 지점 · 기출 ${activeExamSpot.examCode}`,
      macroRegion,
      latitudeZone,
      surfaceContext,
      note: `${macroRegion}의 평가원 기출 지점입니다. ${latitudeZone}와 ${surfaceContext} 맥락에서 ${graphCode} 판정으로 읽습니다.${examMismatch ? ` 다만 기출 표기 ${comparisonNote?.examCode}와 앱 계산 ${graphCode}가 달라 주의가 필요합니다.` : ""}`,
    };
  }
  const useSpotlight = nearest && nearest.distance < 7;
  const title = useSpotlight ? nearest.spotlight.name : macroRegion;
  const subtitle = useSpotlight ? nearest.spotlight.note : `${latitudeZone} 대표 지점`;
  const note = useSpotlight
    ? `${macroRegion}의 대표 사례입니다. ${latitudeZone}와 ${surfaceContext}이 겹치며 ${graphCode} 판정으로 읽힙니다.`
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

function applyActiveButtonState(buttons, predicate) {
  buttons.forEach((button) => {
    button.classList.toggle("is-active", predicate(button));
  });
}

function applyDisabledState(buttons, disabled) {
  buttons.forEach((button) => {
    button.disabled = disabled;
  });
}

function updateControlUI() {
  const screenMeta = syncScreenMode();
  const mission = getCurrentMission();
  const circulationStage = CIRCULATION_STAGES.find((stage) => stage.id === state.circulationStage) ?? CIRCULATION_STAGES[0];
  const observedMode = isObservedAppMode();
  const modeMeta = getCurrentClimateModeMeta();
  const viewModel = buildControlPanelViewModel({
    state,
    screenMeta,
    mission,
    circulationStage,
    observedMode,
    modeMeta,
    monthLabels: MONTH_LABELS,
    presets: PRESETS,
    activeClimateDataset: ACTIVE_CLIMATE_DATASET,
  });
  document.body.dataset.screenMode = viewModel.screenModeId;
  dashboard?.classList.toggle("is-overview", viewModel.screenModeId === "overview");
  dashboard?.classList.toggle("is-experiment", viewModel.screenModeId === "experiment");
  climateModeBlock?.setAttribute("hidden", "hidden");
  applyActiveButtonState(controls.screenModeButtons, (button) => button.dataset.screenMode === state.screenMode);
  const screenModeNote = controls.screenModeToggle?.querySelector(".screen-mode-note");
  if (screenModeNote) {
    screenModeNote.textContent = viewModel.screenModeNote;
  }
  controls.preset.value = state.presetId;
  controls.monthRanges.forEach((input) => {
    input.value = String(state.month);
  });
  controls.monthValues.forEach((label) => {
    label.textContent = viewModel.monthLabel;
  });
  controls.tilt.value = String(state.tilt);
  controls.tiltValue.textContent = viewModel.tiltLabel;
  controls.landScale.value = String(state.landScale);
  controls.landScaleValue.textContent = viewModel.landScaleLabel;
  controls.mountainHeight.value = String(state.mountainHeight);
  controls.mountainHeightValue.textContent = viewModel.mountainHeightLabel;

  applyActiveButtonState(controls.currentButtons, (button) => Number(button.dataset.currentBias) === viewModel.currentBias);
  applyActiveButtonState(controls.overlayButtons, (button) => button.dataset.overlay === viewModel.overlay);
  controls.climateModeButtons.forEach((button) => {
    button.classList.toggle("is-active", button.dataset.climateMode === viewModel.climateMode);
    button.disabled = button.dataset.climateMode === "observed" && !hasObservedClimateDataset;
  });
  controls.circulationStageToggle?.classList.toggle("is-visible", viewModel.circulationStageVisible);
  applyActiveButtonState(controls.circulationStageButtons, (button) => button.dataset.circulationStage === viewModel.circulationStageId);
  controls.preset.disabled = viewModel.observedMode;
  controls.tilt.disabled = viewModel.observedMode;
  controls.landScale.disabled = viewModel.observedMode;
  controls.mountainHeight.disabled = viewModel.observedMode;
  applyDisabledState(controls.currentButtons, viewModel.observedMode);
  for (const block of knobBlocks) {
    block.classList.toggle("is-guided", viewModel.guidedKnobs.has(block.dataset.knob));
    block.classList.remove("is-disabled");
  }
  experimentalControlBlocks.forEach((block) => {
    block.classList.toggle("is-disabled", viewModel.observedMode);
  });

  presetDescription.textContent = viewModel.presetDescription;
  if (controlNote) {
    controlNote.textContent = viewModel.controlNote;
  }
  renderLeverGuide();
}

function buildScenarioFromState() {
  syncScreenMode();
  return buildScenarioFromAppState(state, {
    hasObservedClimateDataset,
    observedPresetId: PRESETS.earthLite.id,
    createScenario,
  });
}

function applyPreset(presetId) {
  const preset = PRESETS[presetId] ?? PRESETS.earthLite;
  applyUiStateChange(() => {
    applyPresetSelection(state, preset);
    return true;
  });
}

function jumpToSpotlight(spotlightId) {
  const spotlight = SPOTLIGHTS.find((item) => item.id === spotlightId);
  if (!spotlight) {
    return;
  }
  const preset = PRESETS[spotlight.presetId] ?? PRESETS.earthLite;
  applyUiStateChange(() => {
    applyPresetSelection(state, preset, {
      latitude: spotlight.latitude,
      longitude: spotlight.longitude,
    });
    return true;
  });
}

function isSelectionNear(latitude, longitude, tolerance = 2.4) {
  return isCoordinateNear(latitude, longitude, state.selectedLatitude, state.selectedLongitude, tolerance);
}

function getActiveExamSpot() {
  return getActiveExamSpotAt(state.selectedLatitude, state.selectedLongitude);
}

function jumpToExamSpot(examSpotId) {
  const examSpot = EXAM_SPOTLIGHTS.find((item) => item.id === examSpotId);
  if (!examSpot) {
    return;
  }
  const preset = PRESETS[examSpot.presetId] ?? PRESETS.earthLite;
  applyUiStateChange(() => {
    applyPresetSelection(state, preset, {
      latitude: examSpot.latitude,
      longitude: examSpot.longitude,
    });
    return true;
  });
}

function renderExamSpotButtons() {
  if (!examSpotButtons) {
    return;
  }
  const activeExamSpot = getActiveExamSpot();
  const ranked = EXAM_SPOTLIGHTS.slice(0, EXAM_SPOT_BUTTON_LIMIT);
  const visibleSpots = activeExamSpot && !ranked.some((spot) => spot.id === activeExamSpot.id)
    ? [activeExamSpot, ...ranked.slice(0, Math.max(EXAM_SPOT_BUTTON_LIMIT - 1, 0))]
    : ranked;

  examSpotButtons.innerHTML = buildExamSpotButtonsMarkup(visibleSpots, activeExamSpot?.id ?? null);
}

function hasCompareSelection() {
  return Number.isFinite(state.compareLatitude) && Number.isFinite(state.compareLongitude);
}

function getCompareSelection() {
  if (!hasCompareSelection()) {
    return null;
  }
  return {
    latitude: state.compareLatitude,
    longitude: state.compareLongitude,
  };
}

function isSameCoordinateSelection(left, right, tolerance = 0.1) {
  if (!left || !right) {
    return false;
  }
  return isCoordinateNear(left.latitude, left.longitude, right.latitude, right.longitude, tolerance);
}

function analyzeCoordinateSelection(latitude, longitude, scenario) {
  return finalizeAnalysisForMode(analyzeLocation(latitude, longitude, scenario));
}

function buildChartExportFileBase(label) {
  return String(label)
    .replace(/[\\/:*?"<>|]/g, "")
    .replace(/\s+/g, "-")
    .replace(/-+/g, "-")
    .replace(/^-|-$/g, "")
    || "climate-graph";
}

function registerChartExport(key, payload) {
  chartExportRegistry.set(key, payload);
}

function triggerBlobDownload(blob, filename) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function buildPrintableChartSvg(key) {
  const entry = chartExportRegistry.get(key);
  if (!entry) {
    return null;
  }
  return buildClimateChartSvgMarkup({
    analysis: entry.analysis,
    selectedMonth: entry.selectedMonth,
    monthLabels: MONTH_LABELS,
    observedOceanCell: entry.observedOceanCell,
    climateResolution: ACTIVE_CLIMATE_DATASET.resolution,
    theme: "print",
    width: 900,
    height: 460,
    interactive: false,
    chartTitle: entry.chartTitle ?? "",
  });
}

function exportChartRaster(key, type = "image/png", extension = "png", quality = 0.96) {
  const entry = chartExportRegistry.get(key);
  const svgMarkup = buildPrintableChartSvg(key);
  if (!entry || !svgMarkup) {
    return;
  }
  const blob = new Blob([svgMarkup], { type: "image/svg+xml;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const image = new Image();
  image.onload = () => {
    const canvas = document.createElement("canvas");
    canvas.width = 1800;
    canvas.height = 920;
    const context = canvas.getContext("2d");
    if (!context) {
      URL.revokeObjectURL(url);
      return;
    }
    context.fillStyle = "#ffffff";
    context.fillRect(0, 0, canvas.width, canvas.height);
    context.drawImage(image, 0, 0, canvas.width, canvas.height);
    canvas.toBlob((rasterBlob) => {
      if (rasterBlob) {
        triggerBlobDownload(rasterBlob, `${entry.fileBase}.${extension}`);
      }
      URL.revokeObjectURL(url);
    }, type, quality);
  };
  image.onerror = () => {
    URL.revokeObjectURL(url);
  };
  image.src = url;
}

function buildCompareCardMarkup({
  slotLabel,
  analysis,
  activeExamSpot,
  exportKey,
}) {
  const context = resolveSelectionContext(analysis, activeExamSpot);
  const officialCode = analysis.classification.code;
  const graphCode = getGraphClimateCode(analysis, activeExamSpot);
  const graphDisplayCode = getGraphClimateDisplayCode(analysis, activeExamSpot);
  const comparisonNote = activeExamSpot ? getClimateComparisonNote(analysis, activeExamSpot, isObservedAppMode()) : null;
  const observedOceanCell = isObservedAppMode() && officialCode === "Ocean";
  const chips = [
    `<span class="mini-chip">${formatCoordinate(analysis.latitude, analysis.longitude)}</span>`,
    `<span class="mini-chip">공식 ${officialCode}</span>`,
    `<span class="mini-chip">그래프 ${graphDisplayCode}</span>`,
  ];
  if (activeExamSpot) {
    chips.push(`<span class="mini-chip">평가원 ${activeExamSpot.examCode}</span>`);
    if (comparisonNote?.examMismatch) {
      chips.push(`<span class="mini-chip mini-chip-warning">기출 코드와 불일치</span>`);
    }
  }
  return `
    <article class="compare-card">
      <div class="compare-card-head">
        <span class="compare-slot">${slotLabel}</span>
        <strong>${context.title}</strong>
        <p>${context.subtitle}</p>
        <div class="inline-chips">${chips.join("")}</div>
      </div>
      <div class="chart-host">
        ${buildClimateChartMarkup({
          analysis,
          selectedMonth: state.month,
          monthLabels: MONTH_LABELS,
          observedOceanCell,
          climateResolution: ACTIVE_CLIMATE_DATASET.resolution,
          exportKey,
          chartTitle: context.title,
        })}
      </div>
    </article>
  `;
}

function renderCompareSection(primaryAnalysis, scenario) {
  if (!compareStatus || !compareSection || !setCompareAnchorButton || !clearCompareButton) {
    return;
  }

  registerChartExport("primary", {
    analysis: primaryAnalysis,
    selectedMonth: state.month,
    observedOceanCell: isObservedAppMode() && primaryAnalysis.classification.code === "Ocean",
    fileBase: buildChartExportFileBase(`${resolveSelectionContext(primaryAnalysis, getActiveExamSpot()).title}-climate-graph`),
    chartTitle: resolveSelectionContext(primaryAnalysis, getActiveExamSpot()).title,
  });

  const compareSelection = getCompareSelection();
  if (!compareSelection) {
    compareStatus.textContent = "현재 지점을 비교 기준으로 저장한 뒤, 다른 지점을 선택하면 두 기후 그래프를 나란히 비교할 수 있습니다.";
    setCompareAnchorButton.textContent = "현재 지점을 비교 기준으로 저장";
    clearCompareButton.hidden = true;
    compareSection.hidden = true;
    compareSection.innerHTML = "";
    chartExportRegistry.delete("compare-anchor");
    chartExportRegistry.delete("compare-current");
    return;
  }

  const currentSelection = {
    latitude: primaryAnalysis.latitude,
    longitude: primaryAnalysis.longitude,
  };
  const comparePinnedToCurrent = isSameCoordinateSelection(compareSelection, currentSelection);
  setCompareAnchorButton.textContent = comparePinnedToCurrent
    ? "비교 기준 저장됨"
    : "현재 지점을 비교 기준으로 교체";
  clearCompareButton.hidden = false;

  if (comparePinnedToCurrent) {
    compareStatus.textContent = "비교 기준이 저장되었습니다. 이제 다른 지점을 클릭하면 두 기후 그래프가 동시에 나타납니다.";
    compareSection.hidden = true;
    compareSection.innerHTML = "";
    chartExportRegistry.delete("compare-anchor");
    chartExportRegistry.delete("compare-current");
    return;
  }

  const compareAnalysis = analyzeCoordinateSelection(compareSelection.latitude, compareSelection.longitude, scenario);
  const compareExamSpot = getActiveExamSpotAt(compareAnalysis.latitude, compareAnalysis.longitude);
  const currentExamSpot = getActiveExamSpotAt(primaryAnalysis.latitude, primaryAnalysis.longitude);
  const compareContext = resolveSelectionContext(compareAnalysis, compareExamSpot);
  const currentContext = resolveSelectionContext(primaryAnalysis, currentExamSpot);

  registerChartExport("compare-anchor", {
    analysis: compareAnalysis,
    selectedMonth: state.month,
    observedOceanCell: isObservedAppMode() && compareAnalysis.classification.code === "Ocean",
    fileBase: buildChartExportFileBase(`${compareContext.title}-climate-graph`),
    chartTitle: compareContext.title,
  });
  registerChartExport("compare-current", {
    analysis: primaryAnalysis,
    selectedMonth: state.month,
    observedOceanCell: isObservedAppMode() && primaryAnalysis.classification.code === "Ocean",
    fileBase: buildChartExportFileBase(`${currentContext.title}-climate-graph`),
    chartTitle: currentContext.title,
  });

  compareStatus.textContent = "비교 기준 지점과 현재 선택 지점을 같은 월 기준으로 동시에 비교 중입니다. 두 그래프는 서로 겹치지 않고 따로 표시됩니다.";
  compareSection.hidden = false;
  compareSection.innerHTML = `
    <div class="subsection-head">
      <p class="eyebrow">Compare</p>
      <h3>두 지점 기후 그래프 비교</h3>
    </div>
    <div class="compare-grid">
      ${buildCompareCardMarkup({
        slotLabel: "비교 기준",
        analysis: compareAnalysis,
        activeExamSpot: compareExamSpot,
        exportKey: "compare-anchor",
      })}
      ${buildCompareCardMarkup({
        slotLabel: "현재 선택",
        analysis: primaryAnalysis,
        activeExamSpot: currentExamSpot,
        exportKey: "compare-current",
      })}
    </div>
  `;
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
  const observedMode = isObservedAppMode();
  const circulationStage = CIRCULATION_STAGES.find((item) => item.id === state.circulationStage) ?? CIRCULATION_STAGES[0];
  mapLegend.innerHTML = buildLegendMarkup({
    overlay: state.overlay,
    observedMode,
    koppenColors: KOPPEN_COLORS,
    circulationStage,
    activeClimateDataset: ACTIVE_CLIMATE_DATASET,
  });
}

function drawOverlayLabel(ctx, x, y, title, subtitle, align = "center", color = "rgba(255,255,255,0.92)") {
  ctx.save();
  ctx.textAlign = align;
  ctx.textBaseline = "middle";
  ctx.lineJoin = "round";
  ctx.strokeStyle = "rgba(11, 20, 29, 0.6)";
  ctx.fillStyle = color;
  ctx.lineWidth = 4;
  ctx.font = '700 12px "Aptos", sans-serif';
  ctx.strokeText(title, x, y - 8);
  ctx.fillText(title, x, y - 8);
  ctx.font = '700 10px "Aptos", sans-serif';
  ctx.strokeText(subtitle, x, y + 8);
  ctx.fillText(subtitle, x, y + 8);
  ctx.restore();
}

function traceRoundedRect(ctx, x, y, width, height, radius = 10) {
  const r = Math.min(radius, width / 2, height / 2);
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.lineTo(x + width - r, y);
  ctx.quadraticCurveTo(x + width, y, x + width, y + r);
  ctx.lineTo(x + width, y + height - r);
  ctx.quadraticCurveTo(x + width, y + height, x + width - r, y + height);
  ctx.lineTo(x + r, y + height);
  ctx.quadraticCurveTo(x, y + height, x, y + height - r);
  ctx.lineTo(x, y + r);
  ctx.quadraticCurveTo(x, y, x + r, y);
  ctx.closePath();
}

function drawShellTextLabel(ctx, x, y, title, subtitle = "", align = "center", color = "rgba(255,255,255,0.92)") {
  const paddingX = 10;
  const titleY = subtitle ? y - 8 : y;
  const subtitleY = y + 8;
  const boxHeight = subtitle ? 34 : 22;

  ctx.save();
  ctx.font = '700 12px "Aptos", sans-serif';
  const titleWidth = ctx.measureText(title).width;
  let subtitleWidth = 0;
  if (subtitle) {
    ctx.font = '700 10px "Aptos", sans-serif';
    subtitleWidth = ctx.measureText(subtitle).width;
  }
  const boxWidth = Math.max(titleWidth, subtitleWidth) + paddingX * 2;
  const boxX = align === "right" ? x - boxWidth : align === "left" ? x : x - boxWidth / 2;
  const textX = align === "right" ? x - paddingX : align === "left" ? x + paddingX : x;

  ctx.globalAlpha = 0.88;
  ctx.fillStyle = "rgba(7, 16, 26, 0.78)";
  traceRoundedRect(ctx, boxX, y - boxHeight / 2, boxWidth, boxHeight, 11);
  ctx.fill();
  ctx.globalAlpha = 0.24;
  ctx.strokeStyle = color;
  ctx.lineWidth = 1.2;
  traceRoundedRect(ctx, boxX, y - boxHeight / 2, boxWidth, boxHeight, 11);
  ctx.stroke();
  ctx.globalAlpha = 1;
  ctx.textAlign = align;
  ctx.textBaseline = "middle";
  ctx.lineJoin = "round";
  ctx.strokeStyle = "rgba(11, 20, 29, 0.78)";
  ctx.fillStyle = color;
  ctx.lineWidth = 4;
  ctx.font = '700 12px "Aptos", sans-serif';
  ctx.strokeText(title, textX, titleY);
  ctx.fillText(title, textX, titleY);
  if (subtitle) {
    ctx.font = '700 10px "Aptos", sans-serif';
    ctx.strokeText(subtitle, textX, subtitleY);
    ctx.fillText(subtitle, textX, subtitleY);
  }
  ctx.restore();
}

function drawFlowArrow(ctx, x1, y1, x2, y2, color, options = {}) {
  const { lineWidth = 2.2, headSize = 7 } = options;
  const angle = Math.atan2(y2 - y1, x2 - x1);

  ctx.save();
  ctx.strokeStyle = color;
  ctx.fillStyle = color;
  ctx.lineWidth = lineWidth;
  ctx.lineCap = "round";
  ctx.beginPath();
  ctx.moveTo(x1, y1);
  ctx.lineTo(x2, y2);
  ctx.stroke();
  ctx.beginPath();
  ctx.moveTo(x2, y2);
  ctx.lineTo(x2 - Math.cos(angle - Math.PI / 6) * headSize, y2 - Math.sin(angle - Math.PI / 6) * headSize);
  ctx.lineTo(x2 - Math.cos(angle + Math.PI / 6) * headSize, y2 - Math.sin(angle + Math.PI / 6) * headSize);
  ctx.closePath();
  ctx.fill();
  ctx.restore();
}

function drawCurvedArrow(ctx, startX, startY, cp1x, cp1y, cp2x, cp2y, endX, endY, color, lineWidth = 2.4) {
  const angle = Math.atan2(endY - cp2y, endX - cp2x);
  const headSize = 7;

  ctx.save();
  ctx.strokeStyle = color;
  ctx.fillStyle = color;
  ctx.lineWidth = lineWidth;
  ctx.lineCap = "round";
  ctx.beginPath();
  ctx.moveTo(startX, startY);
  ctx.bezierCurveTo(cp1x, cp1y, cp2x, cp2y, endX, endY);
  ctx.stroke();
  ctx.beginPath();
  ctx.moveTo(endX, endY);
  ctx.lineTo(endX - Math.cos(angle - Math.PI / 6) * headSize, endY - Math.sin(angle - Math.PI / 6) * headSize);
  ctx.lineTo(endX - Math.cos(angle + Math.PI / 6) * headSize, endY - Math.sin(angle + Math.PI / 6) * headSize);
  ctx.closePath();
  ctx.fill();
  ctx.restore();
}

function drawFlowStream(ctx, width, height, latitude, dx, dy, color) {
  const centers = [0.14, 0.32, 0.5, 0.68, 0.86];
  const y = latToY(latitude, height);
  centers.forEach((ratio) => {
    const x = width * ratio;
    drawFlowArrow(ctx, x - dx / 2, y - dy / 2, x + dx / 2, y + dy / 2, color);
  });
}

function drawJetStream(ctx, width, height, latitude, label, align, color) {
  const y = latToY(latitude, height);
  const textY = latitude >= 0 ? y - 10 : y + 18;
  const labelX = align === "left" ? 18 : width - 18;

  ctx.save();
  ctx.strokeStyle = "rgba(6, 13, 20, 0.78)";
  ctx.lineWidth = 7;
  ctx.setLineDash([18, 9]);
  ctx.beginPath();
  ctx.moveTo(16, y);
  ctx.lineTo(width - 16, y);
  ctx.stroke();
  ctx.strokeStyle = color;
  ctx.shadowColor = color;
  ctx.shadowBlur = 10;
  ctx.lineWidth = 3.2;
  ctx.beginPath();
  ctx.moveTo(16, y);
  ctx.lineTo(width - 16, y);
  ctx.stroke();
  ctx.shadowBlur = 0;
  ctx.setLineDash([]);
  [0.18, 0.38, 0.58, 0.78].forEach((ratio) => {
    const x = width * ratio;
    drawFlowArrow(ctx, x - 18, y, x + 18, y, "rgba(6, 13, 20, 0.84)", { lineWidth: 5, headSize: 10 });
    drawFlowArrow(ctx, x - 18, y, x + 18, y, color, { lineWidth: 2.8, headSize: 8 });
  });
  ctx.font = '700 10px "Aptos", sans-serif';
  const labelWidth = ctx.measureText(label).width + 18;
  const badgeX = align === "left" ? labelX : labelX - labelWidth;
  const badgeY = textY - 10;
  ctx.fillStyle = "rgba(7, 16, 26, 0.88)";
  traceRoundedRect(ctx, badgeX, badgeY, labelWidth, 20, 10);
  ctx.fill();
  ctx.globalAlpha = 0.34;
  ctx.strokeStyle = color;
  ctx.lineWidth = 1.1;
  traceRoundedRect(ctx, badgeX, badgeY, labelWidth, 20, 10);
  ctx.stroke();
  ctx.globalAlpha = 1;
  ctx.fillStyle = color;
  ctx.textAlign = align;
  ctx.fillText(label, align === "left" ? labelX + 9 : labelX - 9, textY + 0.5);
  ctx.restore();
}

function drawVerticalMotionMarker(ctx, x, y, direction, color, emphasis = false) {
  const span = emphasis ? 30 : 22;
  const offsets = emphasis ? [-4, 0, 4] : [-3, 3];
  const startY = direction === "up" ? y + span / 2 : y - span / 2;
  const endY = direction === "up" ? y - span / 2 : y + span / 2;

  ctx.save();
  ctx.fillStyle = color.replace("0.92", "0.16").replace("0.96", "0.18").replace("0.84", "0.14");
  ctx.beginPath();
  ctx.arc(x, y, emphasis ? 13 : 10, 0, TWO_PI);
  ctx.fill();
  ctx.restore();

  offsets.forEach((offset) => {
    drawFlowArrow(ctx, x + offset, startY, x + offset, endY, color);
  });
}

function drawVerticalMotionBadge(ctx, x, y, direction, label, color, emphasis = false) {
  const text = `${direction === "up" ? "↑" : "↓"} ${label}`;

  ctx.save();
  ctx.font = `700 ${emphasis ? 11 : 10}px "Aptos", sans-serif`;
  const badgeWidth = ctx.measureText(text).width + (emphasis ? 18 : 16);
  const badgeHeight = emphasis ? 24 : 21;
  const badgeX = x - badgeWidth / 2;
  const badgeY = y - badgeHeight / 2;
  ctx.fillStyle = "rgba(7, 16, 26, 0.84)";
  traceRoundedRect(ctx, badgeX, badgeY, badgeWidth, badgeHeight, 11);
  ctx.fill();
  ctx.globalAlpha = 0.36;
  ctx.strokeStyle = color;
  ctx.lineWidth = emphasis ? 1.5 : 1.2;
  traceRoundedRect(ctx, badgeX, badgeY, badgeWidth, badgeHeight, 11);
  ctx.stroke();
  ctx.globalAlpha = 1;
  ctx.fillStyle = color;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(text, x, y + 0.5);
  ctx.restore();
}

function drawMapSideVerticalMotions(ctx, width, height, layout) {
  const leftX = 28;
  const rightX = width - 28;
  const motions = [
    { lat: 82, direction: "down", color: "rgba(214, 228, 237, 0.84)" },
    { lat: layout.northSubpolar, direction: "up", color: "rgba(199, 232, 246, 0.92)" },
    { lat: layout.northSubtropical, direction: "down", color: "rgba(255, 220, 157, 0.92)" },
    { lat: layout.itcz, direction: "up", color: "rgba(255, 217, 123, 0.96)", emphasis: true },
    { lat: layout.southSubtropical, direction: "down", color: "rgba(255, 220, 157, 0.92)" },
    { lat: layout.southSubpolar, direction: "up", color: "rgba(199, 232, 246, 0.92)" },
    { lat: -82, direction: "down", color: "rgba(214, 228, 237, 0.84)" },
  ];

  motions.forEach((motion) => {
    const y = latToY(motion.lat, height);
    drawVerticalMotionMarker(ctx, leftX, y, motion.direction, motion.color, motion.emphasis);
    drawVerticalMotionMarker(ctx, rightX, y, motion.direction, motion.color, motion.emphasis);
  });
}

function drawCirculationShell(ctx, plot, layout, stage = CIRCULATION_STAGES[0].id) {
  const shellDepth = Math.max(34, Math.min(54, plot.width * 0.075));
  const shellInset = 6;
  const leftLabelX = plot.left - shellDepth - 14;
  const rightLabelX = plot.right + shellDepth + 14;
  const showLoops = stage !== "surface";
  const showVerticalBadges = stage !== "surface";
  const northTradeLabel = layout.itcz < -TRADE_CROSS_EQUATOR_THRESHOLD ? "북동 무역풍·북서 기류" : "북동 무역풍";
  const southTradeLabel = layout.itcz > TRADE_CROSS_EQUATOR_THRESHOLD ? "남동 무역풍·남서 기류" : "남동 무역풍";
  const cells = [
    { top: 90, bottom: layout.northSubpolar, type: "polar", color: "rgba(154, 194, 219, 0.17)" },
    { top: layout.northSubpolar, bottom: layout.northSubtropical, type: "ferrel", color: "rgba(99, 169, 211, 0.15)" },
    { top: layout.northSubtropical, bottom: layout.itcz, type: "hadley", color: "rgba(241, 184, 83, 0.14)" },
    { top: layout.itcz, bottom: layout.southSubtropical, type: "hadley", color: "rgba(241, 184, 83, 0.14)" },
    { top: layout.southSubtropical, bottom: layout.southSubpolar, type: "ferrel", color: "rgba(99, 169, 211, 0.15)" },
    { top: layout.southSubpolar, bottom: -90, type: "polar", color: "rgba(154, 194, 219, 0.17)" },
  ];

  const drawSide = (side) => {
    const edgeX = side === "left" ? plot.left : plot.right;
    const innerX = edgeX + (side === "left" ? -shellInset : shellInset);
    const outerX = edgeX + (side === "left" ? -shellDepth : shellDepth);

    cells.forEach((cell) => {
      const topY = plot.top + latToY(cell.top, plot.height);
      const bottomY = plot.top + latToY(cell.bottom, plot.height);
      const midY = (topY + bottomY) / 2;
      const cellHeight = Math.max(bottomY - topY, 1);
      const equatorwardLat = Math.abs(cell.top) < Math.abs(cell.bottom) ? cell.top : cell.bottom;
      const polewardLat = equatorwardLat === cell.top ? cell.bottom : cell.top;
      const ascendLat = cell.type === "ferrel" ? polewardLat : equatorwardLat;
      const descendLat = cell.type === "ferrel" ? equatorwardLat : polewardLat;
      const ascendY = plot.top + latToY(ascendLat, plot.height);
      const descendY = plot.top + latToY(descendLat, plot.height);
      const controlOuter = edgeX + (side === "left" ? -shellDepth * 0.86 : shellDepth * 0.86);
      const controlInner = edgeX + (side === "left" ? -shellDepth * 0.36 : shellDepth * 0.36);

      ctx.save();
      ctx.fillStyle = cell.color;
      ctx.strokeStyle = "rgba(255, 255, 255, 0.16)";
      ctx.lineWidth = 1.2;
      ctx.beginPath();
      ctx.moveTo(edgeX, topY);
      ctx.bezierCurveTo(controlInner, topY + cellHeight * 0.08, outerX, midY - cellHeight * 0.18, outerX, midY);
      ctx.bezierCurveTo(outerX, midY + cellHeight * 0.18, controlInner, bottomY - cellHeight * 0.08, edgeX, bottomY);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
      ctx.restore();

      if (showLoops) {
        drawCurvedArrow(
          ctx,
          innerX,
          descendY,
          controlOuter,
          descendY,
          controlOuter,
          ascendY,
          innerX,
          ascendY,
          "rgba(239, 114, 76, 0.94)",
        );
        drawCurvedArrow(
          ctx,
          innerX,
          ascendY,
          controlInner,
          ascendY,
          controlInner,
          descendY,
          innerX,
          descendY,
          "rgba(119, 192, 234, 0.94)",
        );
      }
    });
  };

  drawSide("left");
  drawSide("right");

  if (showVerticalBadges) {
    const badgeXLeft = plot.left - shellDepth * 0.58;
    const badgeXRight = plot.right + shellDepth * 0.58;
    [
      { lat: 82, direction: "down", label: "하강", color: "rgba(220, 232, 240, 0.94)" },
      { lat: layout.northSubpolar, direction: "up", label: "상승", color: "rgba(199, 232, 246, 0.96)" },
      { lat: layout.northSubtropical, direction: "down", label: "하강", color: "rgba(255, 220, 157, 0.96)" },
      { lat: layout.itcz, direction: "up", label: "강한 상승", color: "rgba(255, 217, 123, 0.98)", emphasis: true },
      { lat: layout.southSubtropical, direction: "down", label: "하강", color: "rgba(255, 220, 157, 0.96)" },
      { lat: layout.southSubpolar, direction: "up", label: "상승", color: "rgba(199, 232, 246, 0.96)" },
      { lat: -82, direction: "down", label: "하강", color: "rgba(220, 232, 240, 0.94)" },
    ].forEach((motion) => {
      const motionY = plot.top + latToY(motion.lat, plot.height);
      drawVerticalMotionBadge(ctx, badgeXLeft, motionY, motion.direction, motion.label, motion.color, motion.emphasis);
      drawVerticalMotionBadge(ctx, badgeXRight, motionY, motion.direction, motion.label, motion.color, motion.emphasis);
    });
  }

  [
    { lat: 82, title: "극고압대", subtitle: "찬 공기·하강", color: "rgba(220, 232, 240, 0.92)" },
    { lat: layout.northSubpolar, title: "아극 저압대", subtitle: "전선대·상승", color: "rgba(199, 232, 246, 0.92)" },
    { lat: layout.northSubtropical, title: "아열대 고압대", subtitle: "건조·하강", color: "rgba(255, 220, 157, 0.92)" },
    { lat: layout.itcz, title: "적도 저압대", subtitle: "수렴·강한 상승", color: "rgba(255, 217, 123, 0.96)" },
    { lat: layout.southSubtropical, title: "아열대 고압대", subtitle: "건조·하강", color: "rgba(255, 220, 157, 0.92)" },
    { lat: layout.southSubpolar, title: "아극 저압대", subtitle: "전선대·상승", color: "rgba(199, 232, 246, 0.92)" },
    { lat: -82, title: "극고압대", subtitle: "찬 공기·하강", color: "rgba(220, 232, 240, 0.92)" },
  ].forEach((label) => {
    drawShellTextLabel(ctx, leftLabelX, plot.top + latToY(label.lat, plot.height), label.title, label.subtitle ?? "", "right", label.color);
  });

  [
    { lat: (90 + layout.northSubpolar) / 2, title: stage === "surface" ? "표층 바람대" : "극순환", subtitle: "극동풍", color: "rgba(221, 236, 245, 0.95)" },
    { lat: (layout.northSubpolar + layout.northSubtropical) / 2, title: stage === "surface" ? "표층 바람대" : "페렐 순환", subtitle: "편서풍", color: "rgba(197, 231, 247, 0.95)" },
    { lat: (layout.northSubtropical + layout.itcz) / 2, title: stage === "surface" ? "표층 바람대" : "헤들리 순환", subtitle: northTradeLabel, color: "rgba(255, 227, 171, 0.96)" },
    { lat: (layout.itcz + layout.southSubtropical) / 2, title: stage === "surface" ? "표층 바람대" : "헤들리 순환", subtitle: southTradeLabel, color: "rgba(255, 227, 171, 0.96)" },
    { lat: (layout.southSubtropical + layout.southSubpolar) / 2, title: stage === "surface" ? "표층 바람대" : "페렐 순환", subtitle: "편서풍", color: "rgba(197, 231, 247, 0.95)" },
    { lat: (-90 + layout.southSubpolar) / 2, title: stage === "surface" ? "표층 바람대" : "극순환", subtitle: "극동풍", color: "rgba(221, 236, 245, 0.95)" },
  ].forEach((label) => {
    drawShellTextLabel(ctx, rightLabelX, plot.top + latToY(label.lat, plot.height), label.title, label.subtitle, "left", label.color);
  });
}

function getCirculationLayout(itczLat) {
  const seasonalShift = clamp(itczLat * 0.42, -7, 7);
  const northExpansion = Math.max(itczLat, 0) * 0.34;
  const southExpansion = Math.min(itczLat, 0) * 0.34;

  return {
    itcz: itczLat,
    northSubtropical: clamp(28 + seasonalShift + northExpansion, 20, 42),
    southSubtropical: clamp(-28 + seasonalShift + southExpansion, -42, -20),
    northSubpolar: clamp(60 + seasonalShift + northExpansion * 0.45, 50, 74),
    southSubpolar: clamp(-60 + seasonalShift + southExpansion * 0.45, -74, -50),
  };
}

function getJetStreamLayout(layout) {
  return {
    northSubtropicalJet: clamp(layout.northSubtropical + 3.5, 24, 44),
    southSubtropicalJet: clamp(layout.southSubtropical - 3.5, -44, -24),
    northPolarJet: clamp(layout.northSubpolar - 4.5, 42, 68),
    southPolarJet: clamp(layout.southSubpolar + 4.5, -68, -42),
  };
}

function getClosestJet(latitude, jets) {
  return [
    { lat: jets.northSubtropicalJet, label: "북반구 아열대 제트" },
    { lat: jets.southSubtropicalJet, label: "남반구 아열대 제트" },
    { lat: jets.northPolarJet, label: "북반구 한대전선 제트" },
    { lat: jets.southPolarJet, label: "남반구 한대전선 제트" },
  ].reduce((closest, candidate) => (
    Math.abs(latitude - candidate.lat) < Math.abs(latitude - closest.lat) ? candidate : closest
  ));
}

function describeJetStreamPresence(latitude, jets) {
  const closest = getClosestJet(latitude, jets);
  const distance = Math.abs(latitude - closest.lat);

  if (distance < 6) {
    return `${closest.label} 축 인근`;
  }

  if (distance < 12) {
    return `${closest.label} 주변`;
  }

  return "뚜렷한 제트대 밖";
}

function describeGeostrophicContext(latitude, layout, jets) {
  const closestJet = getClosestJet(latitude, jets);
  const jetDistance = Math.abs(latitude - closestJet.lat);

  if (Math.abs(latitude - layout.itcz) < 8) {
    return "적도 수렴대 부근, 지균풍 약함";
  }

  if (jetDistance < 6) {
    return `${closestJet.label} 상층, 지균풍에 가장 가까움`;
  }

  if (Math.abs(latitude) >= 25 && Math.abs(latitude) <= 65) {
    return "중위도, 상층으로 갈수록 지균풍 접근";
  }

  if (Math.abs(latitude) < 25) {
    return "저위도 표층, 수렴·마찰 영향 큼";
  }

  return "고위도, 코리올리·마찰 영향 함께 큼";
}

function describeCirculationPressureBand(latitude, layout) {
  return [
    { lat: layout.itcz, label: "적도 저압대" },
    { lat: layout.northSubtropical, label: "아열대 고압대" },
    { lat: layout.southSubtropical, label: "아열대 고압대" },
    { lat: layout.northSubpolar, label: "아극 저압대" },
    { lat: layout.southSubpolar, label: "아극 저압대" },
    { lat: 90, label: "극고압대" },
    { lat: -90, label: "극고압대" },
  ].reduce((closest, candidate) => (
    Math.abs(latitude - candidate.lat) < Math.abs(latitude - closest.lat) ? candidate : closest
  )).label;
}

function describeCirculationWindBand(latitude, layout) {
  if (latitude >= layout.northSubpolar || latitude <= layout.southSubpolar) {
    return { label: "극동풍대", shortArrow: "동 → 서" };
  }

  if (
    (latitude < layout.northSubpolar && latitude >= layout.northSubtropical)
    || (latitude > layout.southSubpolar && latitude <= layout.southSubtropical)
  ) {
    return { label: "편서풍대", shortArrow: "서 → 동" };
  }

  if (layout.itcz > TRADE_CROSS_EQUATOR_THRESHOLD && latitude >= 0 && latitude < layout.itcz) {
    return { label: "남서 기류", shortArrow: "남서 → 북동" };
  }

  if (layout.itcz < -TRADE_CROSS_EQUATOR_THRESHOLD && latitude <= 0 && latitude > layout.itcz) {
    return { label: "북서 기류", shortArrow: "북서 → 남동" };
  }

  if (latitude >= 0) {
    return { label: "북동 무역풍", shortArrow: "북동 → 남서" };
  }

  return { label: "남동 무역풍", shortArrow: "남동 → 북서" };
}

function drawCirculationBands(ctx, width, height, layout) {
  [
    { top: 90, bottom: layout.northSubpolar, color: "rgba(154, 194, 219, 0.2)" },
    { top: layout.northSubpolar, bottom: layout.northSubtropical, color: "rgba(99, 169, 211, 0.18)" },
    { top: layout.northSubtropical, bottom: layout.itcz, color: "rgba(241, 184, 83, 0.18)" },
    { top: layout.itcz, bottom: layout.southSubtropical, color: "rgba(241, 184, 83, 0.18)" },
    { top: layout.southSubtropical, bottom: layout.southSubpolar, color: "rgba(99, 169, 211, 0.18)" },
    { top: layout.southSubpolar, bottom: -90, color: "rgba(154, 194, 219, 0.2)" },
  ].forEach((band) => {
    const topY = latToY(band.top, height);
    const bottomY = latToY(band.bottom, height);
    ctx.fillStyle = band.color;
    ctx.fillRect(0, topY, width, bottomY - topY);
  });
}

function drawCirculationForeground(ctx, width, height, layout, stage = CIRCULATION_STAGES[0].id) {
  const jets = getJetStreamLayout(layout);
  const showUpper = stage === "upper";
  const pressureLines = [
    { lat: layout.northSubpolar, label: "아극 저압대", color: "rgba(126, 203, 242, 0.42)", dash: [4, 8], align: "left" },
    { lat: layout.northSubtropical, label: "아열대 고압대", color: "rgba(255, 204, 120, 0.42)", dash: [4, 8], align: "left" },
    { lat: layout.itcz, label: "ITCZ · 적도 저압대", color: "rgba(255, 208, 107, 0.95)", dash: [10, 6], align: "left", emphasis: true },
    { lat: layout.southSubtropical, label: "아열대 고압대", color: "rgba(255, 204, 120, 0.42)", dash: [4, 8], align: "right" },
    { lat: layout.southSubpolar, label: "아극 저압대", color: "rgba(126, 203, 242, 0.42)", dash: [4, 8], align: "right" },
  ];

  const northPolarMid = (90 + layout.northSubpolar) / 2;
  const northFerrelMid = (layout.northSubpolar + layout.northSubtropical) / 2;
  const southFerrelMid = (layout.southSubtropical + layout.southSubpolar) / 2;
  const southPolarMid = (-90 + layout.southSubpolar) / 2;
  const hadleySegments = [];

  if (layout.itcz < -TRADE_CROSS_EQUATOR_THRESHOLD) {
    hadleySegments.push(
      { lat: (layout.northSubtropical + 0) / 2, dx: -78, dy: 18, align: "right", subtitle: "북동 무역풍" },
      { lat: (0 + layout.itcz) / 2, dx: 78, dy: 18, align: "right", subtitle: "북서 기류" },
    );
  } else {
    hadleySegments.push({ lat: (layout.northSubtropical + layout.itcz) / 2, dx: -78, dy: 18, align: "right", subtitle: "북동 무역풍" });
  }

  if (layout.itcz > TRADE_CROSS_EQUATOR_THRESHOLD) {
    hadleySegments.push(
      { lat: (0 + layout.itcz) / 2, dx: 78, dy: -18, align: "left", subtitle: "남서 기류" },
      { lat: (layout.southSubtropical + 0) / 2, dx: -78, dy: -18, align: "left", subtitle: "남동 무역풍" },
    );
  } else {
    hadleySegments.push({ lat: (layout.itcz + layout.southSubtropical) / 2, dx: -78, dy: -18, align: "left", subtitle: "남동 무역풍" });
  }

  ctx.save();
  ctx.font = '700 11px "Aptos", sans-serif';
  pressureLines.forEach((line) => {
    const y = latToY(line.lat, height);
    ctx.setLineDash(line.dash);
    ctx.strokeStyle = line.color;
    ctx.lineWidth = line.emphasis ? 2.5 : 1.3;
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(width, y);
    ctx.stroke();
    ctx.setLineDash([]);
  });
  ctx.restore();

  if (showUpper) {
    drawJetStream(ctx, width, height, jets.northPolarJet, "한대전선 제트", "right", "rgba(63, 223, 255, 0.98)");
    drawJetStream(ctx, width, height, jets.northSubtropicalJet, "아열대 제트", "right", "rgba(255, 120, 88, 0.98)");
    drawJetStream(ctx, width, height, jets.southSubtropicalJet, "아열대 제트", "left", "rgba(255, 120, 88, 0.98)");
    drawJetStream(ctx, width, height, jets.southPolarJet, "한대전선 제트", "left", "rgba(63, 223, 255, 0.98)");
  }

  drawFlowStream(ctx, width, height, northPolarMid, -62, 18, "rgba(219, 235, 245, 0.88)");
  drawFlowStream(ctx, width, height, northFerrelMid, 76, -18, "rgba(177, 221, 242, 0.88)");
  drawFlowStream(ctx, width, height, southFerrelMid, 76, 18, "rgba(177, 221, 242, 0.88)");
  drawFlowStream(ctx, width, height, southPolarMid, -62, -18, "rgba(219, 235, 245, 0.88)");
  hadleySegments.forEach((segment) => {
    drawFlowStream(ctx, width, height, segment.lat, segment.dx, segment.dy, "rgba(255, 223, 160, 0.92)");
  });

}

function renderMap(world, scenario) {
  const { ctx, width, height } = prepareCanvas(mapCanvas);
  const plot = getMapPlotBounds(width, height);
  const monthIndex = clamp(state.month - 1, 0, 11);
  const circulationLayout = state.overlay === "circulation" ? getCirculationLayout(world.itczLatitude) : null;
  const observedMode = isObservedAppMode();

  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = "#17303e";
  ctx.fillRect(0, 0, width, height);

  ctx.save();
  ctx.translate(plot.left, plot.top);
  ctx.beginPath();
  ctx.rect(0, 0, plot.width, plot.height);
  ctx.clip();

  drawMapBaseLayer({
    ctx,
    plotWidth: plot.width,
    plotHeight: plot.height,
    latitudes: LATITUDES,
    longitudes: LONGITUDES,
    overlay: state.overlay,
    circulationLayout,
    officialKoppenCanvas: state.overlay === "koppen" && observedMode && officialKoppenLayer.ready
      ? officialKoppenLayer.canvas
      : null,
    world,
    monthIndex,
    koppenColors: KOPPEN_COLORS,
    temperatureColor,
    precipitationColor,
    drawCirculationBands,
  });

  drawWorldOverlay({
    ctx,
    width: plot.width,
    height: plot.height,
    overlay: state.overlay,
    worldGeometry,
    worldMapBorders: WORLD_MAP_BORDERS,
    worldMapRegions: WORLD_MAP_REGIONS,
    lonToX,
    latToY,
    withAlpha,
    average,
  });
  drawExamSpotMarkers({
    ctx,
    plotWidth: plot.width,
    plotHeight: plot.height,
    examSpotlights: EXAM_SPOTLIGHTS,
    activeExamSpot: getActiveExamSpot(),
    lonToX,
    latToY,
    drawOverlayLabel,
  });
  drawMapOverlayAnnotations({
    ctx,
    plotWidth: plot.width,
    plotHeight: plot.height,
    overlay: state.overlay,
    circulationLayout,
    circulationStage: state.circulationStage,
    worldItczLatitude: world.itczLatitude,
    mountainHeight: scenario.mountainHeight,
    mountainLongitude: scenario.mountainLon,
    screenMode: state.screenMode,
    latToY,
    lonToX,
    drawCirculationForeground,
  });

  drawSpotlightMarkers({
    ctx,
    plotWidth: plot.width,
    plotHeight: plot.height,
    spotlights: SPOTLIGHTS,
    selectedLatitude: state.selectedLatitude,
    selectedLongitude: state.selectedLongitude,
    lonToX,
    latToY,
  });
  drawSelectedLocationMarker({
    ctx,
    plotWidth: plot.width,
    plotHeight: plot.height,
    selectedLongitude: state.selectedLongitude,
    selectedLatitude: state.selectedLatitude,
    lonToX,
    latToY,
  });
  ctx.restore();

  if (state.overlay === "circulation") {
    drawCirculationShell(ctx, plot, circulationLayout, state.circulationStage);
  }

  drawMapAxes({
    ctx,
    plot,
    latToY,
    lonToX,
    formatLatitudeAxisLabel,
    formatLongitudeAxisLabel,
  });
}

function renderSpotlightButtons() {
  const spots = SPOTLIGHTS
    .map((spot) => {
      const active = Math.abs(spot.latitude - state.selectedLatitude) < 2.5 && Math.abs(spot.longitude - state.selectedLongitude) < 2.5;
      const spotlightScenario = createScenario({
        climateMode: state.climateMode,
        presetId: spot.presetId,
        month: state.month,
        tilt: state.tilt,
        landScale: state.landScale,
        mountainHeight: state.mountainHeight,
        currentBias: state.currentBias,
      });
      const analysis = finalizeAnalysisForMode(analyzeLocation(spot.latitude, spot.longitude, spotlightScenario));
      const details = getKoppenDetails(analysis.classification.code);
      return {
        id: spot.id,
        name: spot.name,
        code: analysis.classification.code,
        label: details.label,
        active,
      };
    })
    .filter(Boolean);
  spotlightButtons.innerHTML = buildSpotlightButtonsMarkup(spots);
}

function renderMissionPanel(scenario) {
  const mission = getCurrentMission();
  const concept = KEY_CONCEPT_PROMPTS[MISSION_TO_CONCEPT[mission.id]];
  const guidance = SCENARIO_GUIDANCE.find((item) => item.id === MISSION_TO_SCENARIO[mission.id])
    ?? SCENARIO_GUIDANCE.find((item) => item.recommendedPreset === scenario.presetId)
    ?? SCENARIO_GUIDANCE[0];

  missionSteps.innerHTML = buildMissionStepsMarkup(LESSON_MISSIONS, mission.id);
  missionCard.innerHTML = buildMissionCardMarkup({ mission, concept });
  scenarioGuidance.innerHTML = buildScenarioGuidanceMarkup({
    guidance,
    recommendedPresetName: PRESETS[guidance.recommendedPreset]?.name ?? guidance.recommendedPreset,
  });
}
function renderSelectionCard(analysis, scenario) {
  const activeExamSpot = getActiveExamSpot();
  const officialCode = analysis.classification.code;
  const details = getKoppenDetails(officialCode);
  const metrics = getClassificationMetrics(analysis);
  const graphCode = getGraphClimateCode(analysis, activeExamSpot);
  const graphDisplayCode = getGraphClimateDisplayCode(analysis, activeExamSpot);
  const graphDetails = getKoppenDetails(graphCode);
  const comparisonNote = getClimateComparisonNote(analysis, activeExamSpot, isObservedAppMode());
  const breakdowns = getClimateDriverBreakdowns(analysis, scenario);
  const traceRows = getRuleTraceRows({
    analysis,
    metrics,
    explanationCode: graphCode,
    displayCode: graphDisplayCode,
  });
  const context = resolveSelectionContext(analysis);
  const letterRows = getKoppenLetterBreakdown({
    analysis,
    code: graphCode,
    metrics,
  });
  const observedMode = isObservedAppMode();
  const isObservedOceanCell = observedMode && officialCode === "Ocean";
  const highlandAssist = analysis.highlandAssist?.label === graphCode ? analysis.highlandAssist : null;
  const circulationLayout = getCirculationLayout(analysis.selectedMonth.itczLat);
  const jetLayout = getJetStreamLayout(circulationLayout);
  const circulationWind = describeCirculationWindBand(state.selectedLatitude, circulationLayout);
  const circulationPressureBand = describeCirculationPressureBand(state.selectedLatitude, circulationLayout);
  const jetPresence = describeJetStreamPresence(state.selectedLatitude, jetLayout);
  const geostrophicContext = describeGeostrophicContext(state.selectedLatitude, circulationLayout, jetLayout);
  const showUpperCirculation = state.overlay === "circulation" && state.circulationStage === "upper";
  const renderModel = buildSelectionCardRenderModel({
    analysis,
    context,
    coordinateLabel: formatCoordinate(analysis.latitude, analysis.longitude),
    officialCode,
    graphCode,
    graphDisplayCode,
    details,
    graphDetails,
    comparisonNote,
    observedMode,
    isObservedOceanCell,
    highlandAssist,
    activeExamSpot,
    circulationPressureBand,
    circulationWind,
    showUpperCirculation,
    jetPresence,
    geostrophicContext,
    activeClimateDataset: ACTIVE_CLIMATE_DATASET,
    selectedMonth: state.month,
    monthLabels: MONTH_LABELS,
    traceRows,
    letterRows,
    koppenColors: KOPPEN_COLORS,
  });

  selectionLabel.textContent = renderModel.labelText;
  selectionKoppen.innerHTML = renderModel.koppenMarkup;
  selectionSummary.textContent = renderModel.summaryText;
  selectionContext.innerHTML = renderModel.contextMarkup;
  koppenBreakdown.innerHTML = renderModel.breakdownMarkup;
  annualFacts.innerHTML = renderModel.annualFactsMarkup;
  monthlyFactors.innerHTML = renderModel.monthlyFactorsMarkup;

  driverStacks.innerHTML = `
    ${buildDriverInsightCardsMarkup({
      analysis,
      breakdowns,
      context,
      circulationPressureBand,
      circulationWind,
      observedMode,
      activeExamSpot,
      selectedMonth: state.month,
    })}
    ${buildDriverSectionMarkup("이번 달 기온 기여", breakdowns.temperature, observedMode)}
    ${buildDriverSectionMarkup("이번 달 강수 기여", breakdowns.precipitation, observedMode)}
  `;

  ruleTrace.innerHTML = renderModel.ruleTraceMarkup;
  reasonList.innerHTML = renderModel.reasonListMarkup;
}

function renderClimateChart(analysis) {
  const chartTitle = resolveSelectionContext(
    analysis,
    getActiveExamSpotAt(analysis.latitude, analysis.longitude),
  ).title;
  climateChart.innerHTML = buildClimateChartMarkup({
    analysis,
    selectedMonth: state.month,
    monthLabels: MONTH_LABELS,
    observedOceanCell: isObservedAppMode() && analysis.classification.code === "Ocean",
    climateResolution: ACTIVE_CLIMATE_DATASET.resolution,
    exportKey: "primary",
    chartTitle,
  });
}

function renderCirculation(analysis, scenario) {
  const width = 360;
  const height = 320;
  const stage = CIRCULATION_STAGES.find((item) => item.id === state.circulationStage) ?? CIRCULATION_STAGES[0];
  const showUpper = stage.id === "upper";
  const layout = getCirculationLayout(analysis.selectedMonth.itczLat);
  const jetLayout = getJetStreamLayout(layout);
  circulationSvg.innerHTML = buildCirculationSvgMarkup({
    width,
    height,
    stage,
    layout,
    jetLayout,
    selectedLatitude: state.selectedLatitude,
    tradeCrossEquatorThreshold: TRADE_CROSS_EQUATOR_THRESHOLD,
  });

  const wind = describeCirculationWindBand(state.selectedLatitude, layout);
  const pressureBand = describeCirculationPressureBand(state.selectedLatitude, layout);
  const jetPresence = describeJetStreamPresence(state.selectedLatitude, jetLayout);
  const geostrophicContext = describeGeostrophicContext(state.selectedLatitude, layout, jetLayout);
  circulationFacts.innerHTML = buildCirculationFactsMarkup({
    stageLabel: stage.label,
    layout,
    jetLayout,
    showUpper,
    pressureBand,
    wind,
    jetPresence,
    geostrophicContext,
    tilt: scenario.tilt,
  });
}
function renderTransect(scenario) {
  const data = sampleTransect(state.selectedLatitude, scenario.month, scenario);
  const width = 560;
  const height = 250;
  const margin = { top: 22, right: 20, bottom: 28, left: 28 };
  transectSvg.innerHTML = buildTransectSvgMarkup({
    data,
    width,
    height,
    margin,
    longitudeCount: LONGITUDES.length,
    selectedLongitude: state.selectedLongitude,
    mountainLongitude: scenario.mountainLon,
  });
  transectCaption.textContent = buildTransectCaptionText(
    formatCoordinate(state.selectedLatitude, state.selectedLongitude),
  );
}

function renderSpotlightButtonsSection() {
  renderSpotlightButtons();
  renderExamSpotButtons();
}

function renderDashboardScene(scene) {
  const { scenario, world, analysis } = scene;
  renderLegend();
  renderMap(world, scenario);
  renderSpotlightButtonsSection();
  renderMissionPanel(scenario);
  renderSelectionCard(analysis, scenario);
  renderClimateChart(analysis);
  renderCompareSection(analysis, scenario);
  renderCirculation(analysis, scenario);
  renderTransect(scenario);
}

function renderMapAndPanels() {
  const scene = buildDashboardScene({
    state,
    buildScenarioFromState,
    buildWorld,
    analyzeLocation,
    finalizeAnalysisForMode,
  });
  renderDashboardScene(scene);
}

function handleMapSelection(event) {
  const rect = mapCanvas.getBoundingClientRect();
  const plot = getMapPlotBounds(rect.width, rect.height);
  const selection = resolveMapClickSelection({
    clientX: event.clientX,
    clientY: event.clientY,
    rect,
    plot,
    spotlights: SPOTLIGHTS,
    examSpotlights: EXAM_SPOTLIGHTS,
    lonToX,
    latToY,
  });
  if (!selection) {
    return;
  }
  if (selection.kind === "exam") {
    jumpToExamSpot(selection.id);
    return;
  }
  if (selection.kind === "spotlight") {
    jumpToSpotlight(selection.id);
    return;
  }
  applyRenderStateChange(() => applySelectionCoordinates(state, selection.latitude, selection.longitude));
}

function applyUiStateChange(mutator) {
  const changed = mutator();
  if (!changed) {
    return false;
  }
  updateControlUI();
  queueRender();
  return true;
}

function applyRenderStateChange(mutator) {
  const changed = mutator();
  if (!changed) {
    return false;
  }
  queueRender();
  return true;
}

function bindUiButtonGroup(buttons, getValue, action) {
  buttons.forEach((button) => {
    button.addEventListener("click", () => {
      applyUiStateChange(() => action(state, getValue(button)));
    });
  });
}

function bindUiInput(input, eventName, action) {
  input.addEventListener(eventName, (event) => {
    applyUiStateChange(() => action(state, event.target.value));
  });
}

function bindUiInputGroup(inputs, eventName, action) {
  inputs.forEach((input) => {
    bindUiInput(input, eventName, action);
  });
}

function bindDelegatedClick(container, selector, handler) {
  container?.addEventListener("click", (event) => {
    const target = event.target.closest(selector);
    if (!target) {
      return;
    }
    handler(target, event);
  });
}

function syncExclusiveOpenPanel(activePanel) {
  if (!activePanel.open || !isCompactViewport()) {
    return;
  }
  foldPanels.forEach((otherPanel) => {
    if (otherPanel !== activePanel && otherPanel.dataset.mobileCollapsed === "true") {
      otherPanel.open = false;
    }
  });
}

function bindEvents() {
  bindUiButtonGroup(controls.screenModeButtons, (button) => button.dataset.screenMode, applyScreenModeChange);
  bindUiButtonGroup(controls.climateModeButtons, (button) => button.dataset.climateMode, applyClimateModeChange);
  controls.preset.addEventListener("change", (event) => applyPreset(event.target.value));
  bindUiInputGroup(controls.monthRanges, "input", applyMonthChange);
  bindUiInput(controls.tilt, "input", applyTiltChange);
  bindUiInput(controls.landScale, "input", applyLandScaleChange);
  bindUiInput(controls.mountainHeight, "input", applyMountainHeightChange);
  bindUiButtonGroup(controls.currentButtons, (button) => button.dataset.currentBias, applyCurrentBiasChange);
  bindUiButtonGroup(controls.overlayButtons, (button) => button.dataset.overlay, applyOverlayChange);
  bindUiButtonGroup(controls.circulationStageButtons, (button) => button.dataset.circulationStage, applyCirculationStageChange);

  bindDelegatedClick(climateChart, "[data-chart-month]", (target) => {
    applyUiStateChange(() => applyMonthChange(state, Number(target.dataset.chartMonth)));
  });

  bindDelegatedClick(compareSection, "[data-chart-month]", (target) => {
    applyUiStateChange(() => applyMonthChange(state, Number(target.dataset.chartMonth)));
  });

  bindDelegatedClick(climateChart, "[data-chart-export]", (target) => {
    const key = target.dataset.chartKey;
    if (target.dataset.chartExport === "png") {
      void exportChartRaster(key, "image/png", "png");
      return;
    }
    void exportChartRaster(key, "image/jpeg", "jpg", 0.94);
  });

  bindDelegatedClick(compareSection, "[data-chart-export]", (target) => {
    const key = target.dataset.chartKey;
    if (target.dataset.chartExport === "png") {
      void exportChartRaster(key, "image/png", "png");
      return;
    }
    void exportChartRaster(key, "image/jpeg", "jpg", 0.94);
  });

  bindDelegatedClick(missionSteps, "[data-mission-id]", (target) => {
    applyUiStateChange(() => applyMissionChange(state, target.dataset.missionId));
  });

  bindDelegatedClick(scenarioGuidance, "[data-guidance-preset]", (target) => {
    applyPreset(target.dataset.guidancePreset);
  });

  bindDelegatedClick(spotlightButtons, "[data-spotlight]", (target) => {
    jumpToSpotlight(target.dataset.spotlight);
  });

  bindDelegatedClick(examSpotButtons, "[data-exam-spotlight]", (target) => {
    jumpToExamSpot(target.dataset.examSpotlight);
  });

  setCompareAnchorButton?.addEventListener("click", () => {
    applyRenderStateChange(() => applyCompareSelection(state, state.selectedLatitude, state.selectedLongitude));
  });

  clearCompareButton?.addEventListener("click", () => {
    applyRenderStateChange(() => clearCompareSelection(state));
  });

  mapCanvas.addEventListener("click", handleMapSelection);
  window.addEventListener("resize", () => {
    syncFoldPanelsForViewport();
    queueRender();
  });

  foldPanels.forEach((panel) => {
    panel.addEventListener("toggle", () => {
      syncExclusiveOpenPanel(panel);
      if (panel.open) {
        queueRender();
      }
    });
  });
}

function isCompactViewport() {
  return window.matchMedia("(max-width: 760px)").matches;
}

function syncFoldPanelsForViewport(force = false) {
  const compactViewport = isCompactViewport();
  if (!force && compactViewport === lastCompactViewportState) {
    return;
  }
  foldPanels.forEach((panel) => {
    if (panel.dataset.mobileCollapsed === "true") {
      panel.open = !compactViewport;
    }
  });
  lastCompactViewportState = compactViewport;
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
  updateControlUI();
  renderMapAndPanels();
}

async function init() {
  populatePresetSelect();
  syncFoldPanelsForViewport(true);
  bindEvents();
  updateControlUI();
  await Promise.all([loadWorldGeometry(), loadOfficialKoppenLayer()]);
  render();
}

void init();
