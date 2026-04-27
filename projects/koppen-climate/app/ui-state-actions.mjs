function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

export function applyScreenModeChange(state, nextMode) {
  const normalizedMode = nextMode === "experiment" ? "experiment" : "overview";
  if (state.screenMode === normalizedMode) {
    return false;
  }
  state.screenMode = normalizedMode;
  if (normalizedMode === "overview" && state.overlay === "circulation") {
    state.overlay = "koppen";
  }
  return true;
}

export function applyClimateModeChange(state, nextMode) {
  const normalizedMode = nextMode === "experimental" ? "experimental" : "observed";
  if (state.climateMode === normalizedMode) {
    return false;
  }
  state.climateMode = normalizedMode;
  return true;
}

export function applyMonthChange(state, nextMonth) {
  const month = clamp(Number(nextMonth), 1, 12);
  if (!Number.isFinite(month) || month === state.month) {
    return false;
  }
  state.month = month;
  return true;
}

export function applyTiltChange(state, nextTilt) {
  const tilt = Number(nextTilt);
  if (!Number.isFinite(tilt) || tilt === state.tilt) {
    return false;
  }
  state.tilt = tilt;
  return true;
}

export function applyLandScaleChange(state, nextLandScale) {
  const landScale = Number(nextLandScale);
  if (!Number.isFinite(landScale) || landScale === state.landScale) {
    return false;
  }
  state.landScale = landScale;
  return true;
}

export function applyMountainHeightChange(state, nextMountainHeight) {
  const mountainHeight = Number(nextMountainHeight);
  if (!Number.isFinite(mountainHeight) || mountainHeight === state.mountainHeight) {
    return false;
  }
  state.mountainHeight = mountainHeight;
  return true;
}

export function applyCurrentBiasChange(state, nextCurrentBias) {
  const currentBias = Number(nextCurrentBias);
  if (!Number.isFinite(currentBias) || currentBias === state.currentBias) {
    return false;
  }
  state.currentBias = currentBias;
  return true;
}

export function applyOverlayChange(state, nextOverlay) {
  const overlay = typeof nextOverlay === "string" ? nextOverlay : "koppen";
  if (state.overlay === overlay) {
    return false;
  }
  state.overlay = overlay;
  return true;
}

export function applyCirculationStageChange(state, nextStage) {
  const stage = typeof nextStage === "string" ? nextStage : "surface";
  if (state.circulationStage === stage) {
    return false;
  }
  state.circulationStage = stage;
  return true;
}

export function applyMissionChange(state, nextMissionId) {
  if (!nextMissionId || state.missionId === nextMissionId) {
    return false;
  }
  state.missionId = nextMissionId;
  return true;
}

export function applySelectionCoordinates(state, latitude, longitude) {
  const nextLatitude = clamp(Number(latitude), -90, 90);
  const nextLongitude = clamp(Number(longitude), -180, 180);
  if (!Number.isFinite(nextLatitude) || !Number.isFinite(nextLongitude)) {
    return false;
  }
  if (state.selectedLatitude === nextLatitude && state.selectedLongitude === nextLongitude) {
    return false;
  }
  state.selectedLatitude = nextLatitude;
  state.selectedLongitude = nextLongitude;
  return true;
}

export function applyCompareSelection(state, latitude, longitude) {
  const nextLatitude = clamp(Number(latitude), -90, 90);
  const nextLongitude = clamp(Number(longitude), -180, 180);
  if (!Number.isFinite(nextLatitude) || !Number.isFinite(nextLongitude)) {
    return false;
  }
  if (state.compareLatitude === nextLatitude && state.compareLongitude === nextLongitude) {
    return false;
  }
  state.compareLatitude = nextLatitude;
  state.compareLongitude = nextLongitude;
  return true;
}

export function clearCompareSelection(state) {
  if (!Number.isFinite(state.compareLatitude) && !Number.isFinite(state.compareLongitude)) {
    return false;
  }
  state.compareLatitude = null;
  state.compareLongitude = null;
  return true;
}
