export const SCREEN_MODES = [
  { id: "overview", label: "기본 지도", note: "공식 지도와 관측 그래프를 읽는 기본 화면입니다." },
  { id: "experiment", label: "실험실", note: "실험 레버를 지도 옆에서 바로 돌리며 비교하는 화면입니다." },
];

export const CLIMATE_VIEW_MODES = [
  {
    id: "observed",
    label: "관측 모드",
    shortLabel: "관측",
    note: "공식 쾨펜 지도와 관측 월별 기후값을 봅니다.",
  },
  {
    id: "experimental",
    label: "실험 모드",
    shortLabel: "실험",
    note: "레버 조건으로 지도와 그래프를 다시 계산합니다.",
  },
];

export function createInitialAppState({
  defaultPreset,
  firstCirculationStageId,
  firstMissionId,
  hasObservedClimateDataset,
}) {
  const state = {
    screenMode: "overview",
    climateMode: "observed",
    presetId: defaultPreset.id,
    month: 7,
    tilt: defaultPreset.tilt,
    landScale: defaultPreset.landScale,
    mountainHeight: defaultPreset.mountainHeight,
    currentBias: defaultPreset.currentBias,
    overlay: "koppen",
    circulationStage: firstCirculationStageId,
    missionId: firstMissionId,
    selectedLatitude: defaultPreset.probeLat,
    selectedLongitude: defaultPreset.probeLon,
    compareLatitude: null,
    compareLongitude: null,
  };

  if (!hasObservedClimateDataset) {
    state.screenMode = "experiment";
    state.climateMode = "experimental";
  }

  return state;
}

export function isObservedAppMode(state, hasObservedClimateDataset) {
  return hasObservedClimateDataset && state.screenMode !== "experiment";
}

export function getCurrentClimateModeMeta(state, climateViewModes = CLIMATE_VIEW_MODES) {
  return climateViewModes.find((mode) => mode.id === state.climateMode) ?? climateViewModes[0];
}

export function getCurrentScreenModeMeta(state, screenModes = SCREEN_MODES) {
  return screenModes.find((mode) => mode.id === state.screenMode) ?? screenModes[0];
}

export function syncScreenMode(state, { hasObservedClimateDataset, screenModes = SCREEN_MODES } = {}) {
  if (!hasObservedClimateDataset) {
    state.screenMode = "experiment";
  }
  state.climateMode = state.screenMode === "experiment" ? "experimental" : "observed";
  return getCurrentScreenModeMeta(state, screenModes);
}

export function applyPresetSelection(state, preset, selection = null) {
  state.presetId = preset.id;
  state.tilt = preset.tilt;
  state.landScale = preset.landScale;
  state.mountainHeight = preset.mountainHeight;
  state.currentBias = preset.currentBias;
  state.selectedLatitude = selection?.latitude ?? preset.probeLat;
  state.selectedLongitude = selection?.longitude ?? preset.probeLon;
  return state;
}

export function buildScenarioFromState(state, {
  hasObservedClimateDataset,
  observedPresetId,
  createScenario,
} = {}) {
  if (isObservedAppMode(state, hasObservedClimateDataset)) {
    return createScenario({
      climateMode: "observed",
      presetId: observedPresetId,
      month: state.month,
    });
  }

  return createScenario({
    climateMode: state.climateMode,
    presetId: state.presetId,
    month: state.month,
    tilt: state.tilt,
    landScale: state.landScale,
    mountainHeight: state.mountainHeight,
    currentBias: state.currentBias,
  });
}
