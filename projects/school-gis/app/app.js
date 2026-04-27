import { APP_CONFIG } from "./config.js";
import {
  KOREA_MAP_VIEW,
  NATIONAL_DATASETS,
  NATIONAL_FACILITY_LAYERS,
} from "./national-data.js";
import {
  buildLocalPublicLayers,
  createId,
  escapeHtml,
  formatNumber,
  getRandomLayerColor,
  loadStudentLayers,
  loadWorkspaceProjectsRaw,
  loadWorkspaceReflection,
  parseCsvText,
  parseGeoJsonText,
  saveStudentLayers,
  saveWorkspaceProjectsRaw,
  saveWorkspaceReflection,
} from "./layer-workspace-data.js";
import {
  buildStudentLayerFeatureCollection,
  getStudentGeometryLabel,
  getStudentLayerCoordinates,
  getStudentLayerGeometryLabel,
  normalizeStudentLayer,
} from "./domain/student-layer.js";
import {
  getStudentDraftStatus,
} from "./application/student-layer-use-cases.js";
import {
  DRAW_TOOL_META,
  canCompleteDraftGeometry,
  getDrawToolGeometryType,
  isMeasurementTool,
  isStudentFeatureDrawTool,
  isGeometryDrawTool,
  resolveDrawTool,
} from "./application/draw-session-use-cases.js";
import {
  buildFeatureMeasurementSummary,
  buildMeasurementResult,
} from "./application/measurement-use-cases.js";
import {
  removeStudentFeature,
} from "./application/student-layer-edit-use-cases.js";
import {
  createSelectedFeatureRef,
  findSelectedStudentFeature,
} from "./application/feature-selection-use-cases.js";
import {
  buildRegionSgisSummary,
  SGIS_REGION_LAYER_PROFILES,
} from "./application/sgis-region-use-cases.js";
import {
  buildSuitabilityPanelViewModel,
  createSuitabilityAnalysisLayer,
  getSuitabilityTemplate,
} from "./application/suitability-use-cases.js";
import { buildWorkspaceSummary } from "./application/workspace-summary-use-cases.js";
import {
  buildWorkspacePanelViewModel as buildWorkspacePanelViewModelUseCase,
  buildWorkspaceRegionCacheKey as buildWorkspaceRegionCacheKeyUseCase,
  buildWorkspaceUrl as buildWorkspaceUrlUseCase,
  normalizeWorkspaceValues as normalizeWorkspaceValuesUseCase,
} from "./application/workspace-panel-use-cases.js";
import {
  buildWorkspaceProjectSnapshot,
  buildWorkspaceProjectViewModel,
  normalizeWorkspaceProject,
  normalizeWorkspaceProjects,
  removeWorkspaceProject,
  upsertWorkspaceProject,
} from "./application/project-workspace-use-cases.js";
import {
  buildPublicPanelViewModel as buildPublicPanelViewModelUseCase,
  getCurrentSgisMetricLabel as getCurrentSgisMetricLabelUseCase,
  getCurrentSgisProfile as getCurrentSgisProfileUseCase,
  getImportedPublicSourceLabel as getImportedPublicSourceLabelUseCase,
  getLayerScopeLabel as getLayerScopeLabelUseCase,
  getSchoolSgisControlValues as getSchoolSgisControlValuesUseCase,
} from "./application/public-panel-view-models.js";
import {
  collectFeatureCollectionCoordinates,
  importPublicLayerFromPreset,
  importPublicLayerFromUrl,
  loadImportedPublicLayers,
  normalizeImportedPublicLayer,
  saveImportedPublicLayers,
} from "./public-layer-imports.js";
import { createLayerWorkspaceMap } from "./layer-workspace-map.js";
import {
  bindPublicPanelEvents,
  renderPublicPanelView,
} from "./presentation/public-panel.js";
import { createPublicWorkspaceController } from "./presentation/public-workspace-controller.js";
import { createWorkspaceRegionController } from "./presentation/workspace-region-controller.js";
import {
  bindWorkspacePanelEvents,
  renderWorkspacePanelView,
} from "./presentation/workspace-panel.js";
import {
  bindDrawToolbarEvents,
  renderDrawToolbar,
} from "./presentation/draw-toolbar.js";
import {
  bindStudentPanelEvents,
  renderStudentPanel as renderStudentPanelView,
} from "./presentation/student-panel.js";
import {
  bindSuitabilityPanelEvents,
  renderSuitabilityPanel as renderSuitabilityPanelView,
} from "./presentation/suitability-panel.js";
import { createStudentWorkspaceController } from "./presentation/student-workspace-controller.js";

const nationalDatasetMap = new Map(
  NATIONAL_DATASETS.map((dataset) => [dataset.id, dataset]),
);

const SGIS_METRIC_RECOMMENDATION_META = {
  tot_ppltn: {
    studentLabel: "사람이 많이 사는 곳",
    helper: "주거 인구가 많이 모인 생활권을 볼 때 적합합니다.",
  },
  avg_age: {
    studentLabel: "평균연령 보기",
    helper: "연령 구조 차이를 통해 지역 특성을 읽을 때 유용합니다.",
  },
  ppltn_dnsty: {
    studentLabel: "밀집도 보기",
    helper: "사람이 얼마나 촘촘하게 분포하는지 볼 수 있습니다.",
  },
  corp_cnt: {
    studentLabel: "사업체 많은 곳",
    helper: "상업·업무 활동이 모이는 곳을 읽을 때 적합합니다.",
  },
  employee_cnt: {
    studentLabel: "일하는 사람 많은 곳",
    helper: "통학 시간대 유동과 업무 밀집 지역을 해석할 때 유용합니다.",
  },
  aged_child_idx: {
    studentLabel: "고령화 정도 보기",
    helper: "노년층 비중이 높은 지역성을 읽을 때 유용합니다.",
  },
  household_cnt: {
    studentLabel: "가구 많은 곳",
    helper: "생활권 규모와 주거 밀집을 비교할 때 적합합니다.",
  },
  house_cnt: {
    studentLabel: "주택 많은 곳",
    helper: "주거 공급과 주거지 분포를 볼 때 적합합니다.",
  },
};

const DEFAULT_SGIS_RECOMMENDATION_IDS = ["ppltn_dnsty", "avg_age", "corp_cnt", "aged_child_idx", "household_cnt", "house_cnt"];

const MAP_OVERLAY_OPTIONS = [
  { id: "traffic", label: "교통" },
  { id: "bicycle", label: "자전거" },
  { id: "terrain", label: "지형" },
  { id: "district", label: "지적편집도" },
];

const SIMPLE_PUBLIC_TOPIC_METRIC = {
  population: "ppltn_dnsty",
  age: "avg_age",
  business: "corp_cnt",
  household: "household_cnt",
  other: "aged_child_idx",
};

const SIMPLE_PUBLIC_PROFILE = {
  "grid-current": "grid-sgg-500m",
  "grid-sgg": "grid-sgg-500m",
  "grid-emd": "grid-emd-100m",
  "region-current": "region-sgg-children",
  "region-sgg": "region-sgg-children",
  "region-emd": "region-emd-children",
};

const OBSERVATION_SEVERITY_LABEL = {
  "1": "낮음",
  "2": "보통",
  "3": "높음",
};

const SIDEBAR_PANEL_LABEL = {
  workspace: "워크스페이스",
  public: "공공데이터",
  student: "내 레이어",
  analysis: "분석",
  layers: "레이어",
};

const WORKSPACE_SEARCH_ENDPOINT = "https://nominatim.openstreetmap.org/search";
let sgisModulePromise = null;

function parseFiniteNumber(value, fallback) {
  if (value === null || value === undefined || String(value).trim() === "") {
    return fallback;
  }

  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function buildWorkspaceSearchQuery(query) {
  const trimmed = String(query ?? "").trim();
  if (!trimmed) {
    return "";
  }

  return trimmed;
}

function normalizeSearchText(value) {
  return String(value ?? "")
    .trim()
    .toLowerCase()
    .replace(/\s+/g, "");
}

function buildWorkspacePresetSearchResults(searchQuery) {
  const normalizedQuery = normalizeSearchText(searchQuery);
  if (!normalizedQuery) {
    return [];
  }

  return (EFFECTIVE_CONFIG.workspacePresets ?? [])
    .filter((preset) => {
      const searchableText = [
        preset.id,
        preset.label,
        preset.schoolName,
        preset.name,
        preset.address,
        ...(preset.aliases ?? []),
      ].map(normalizeSearchText).join(" ");
      return searchableText.includes(normalizedQuery);
    })
    .map((preset) => ({
      id: `preset-${preset.id}`,
      name: preset.label ?? preset.schoolName ?? preset.name ?? searchQuery,
      subtitle: preset.address ?? "저장된 위치",
      lat: Number(preset.lat),
      lng: Number(preset.lng),
      type: "preset",
      rawClass: "preset",
    }))
    .filter((item) => Number.isFinite(item.lat) && Number.isFinite(item.lng));
}

function buildMapCenterSearchResult(searchQuery) {
  const center = mapWorkspace?.map?.getCenter?.() ?? state.referenceLocation ?? EFFECTIVE_CONFIG.mapCenter;
  const lat = Number(center.lat);
  const lng = Number(center.lng);
  if (!Number.isFinite(lat) || !Number.isFinite(lng)) {
    return null;
  }

  return {
    id: `map-center-${normalizeSearchText(searchQuery) || "location"}`,
    name: searchQuery,
    subtitle: "정확한 검색 결과가 없으면 지도를 해당 위치로 이동한 뒤 현재 지도 중심을 이 이름으로 고정하세요.",
    lat,
    lng,
    type: "map-center",
    rawClass: "manual",
  };
}

function dedupeWorkspaceSearchResults(results) {
  const seen = new Set();
  return results.filter((result) => {
    const key = [
      normalizeSearchText(result.name),
      Number(result.lat).toFixed(5),
      Number(result.lng).toFixed(5),
    ].join("|");
    if (seen.has(key)) {
      return false;
    }
    seen.add(key);
    return true;
  });
}

async function searchWorkspaceLocationsWithFallback(searchQuery) {
  if (!searchQuery) {
    return [];
  }

  const url = new URL(WORKSPACE_SEARCH_ENDPOINT);
  url.searchParams.set("q", searchQuery);
  url.searchParams.set("format", "jsonv2");
  url.searchParams.set("limit", "5");
  url.searchParams.set("addressdetails", "1");
  url.searchParams.set("countrycodes", "kr");

  const response = await fetch(url.toString(), {
    headers: {
      Accept: "application/json",
    },
  });
  if (!response.ok) {
    throw new Error(`장소 검색 응답을 불러오지 못했습니다 (${response.status}).`);
  }

  const payload = await response.json();
  return payload
    .map((item) => ({
      id: String(item.place_id),
      name: item.name || item.display_name?.split(",")[0]?.trim() || searchQuery,
      subtitle: item.display_name || "",
      lat: Number(item.lat),
      lng: Number(item.lon),
      type: item.type || item.class || "location",
      rawClass: item.class || "",
    }))
    .filter((item) => Number.isFinite(item.lat) && Number.isFinite(item.lng))
    .filter((item) => !(item.type === "country" && !searchQuery.includes("대한민국")));
}

async function searchWorkspaceLocations(query) {
  const searchQuery = buildWorkspaceSearchQuery(query);
  if (!searchQuery) {
    return [];
  }

  const presetResults = buildWorkspacePresetSearchResults(searchQuery);

  if (typeof mapWorkspace?.searchPlaces === "function") {
    try {
      const kakaoResults = await mapWorkspace.searchPlaces(searchQuery);
      if (Array.isArray(kakaoResults) && kakaoResults.length) {
        return dedupeWorkspaceSearchResults([...presetResults, ...kakaoResults]);
      }
    } catch (error) {
      console.warn("Falling back to default search provider.", error);
    }
  }

  try {
    const fallbackResults = await searchWorkspaceLocationsWithFallback(searchQuery);
    const mergedResults = dedupeWorkspaceSearchResults([...presetResults, ...fallbackResults]);
    if (mergedResults.length) {
      return mergedResults;
    }
  } catch (error) {
    console.warn("Default search provider failed.", error);
    if (presetResults.length) {
      return presetResults;
    }
  }

  const mapCenterFallback = buildMapCenterSearchResult(searchQuery);
  return mapCenterFallback ? [mapCenterFallback] : [];
}

async function loadSgisModule() {
  if (!sgisModulePromise) {
    sgisModulePromise = import("./sgis-adapter.js");
  }

  return sgisModulePromise;
}

function bindEvents() {
  elements.viewModeToggle.addEventListener("click", (event) => {
    const button = event.target.closest("[data-view-mode]");
    if (!button) {
      return;
    }

    const nextViewMode = button.dataset.viewMode;
    if (!nextViewMode || nextViewMode === state.viewMode) {
      return;
    }

    state.viewMode = nextViewMode;
    state.activeSidebarPanel = resolveDefaultSidebarPanel(nextViewMode);
    elements.publicLayerScopeField.value = nextViewMode;
    state.selectedNationalPointId = null;
    syncUrlState();
    renderAll();
    mapWorkspace.focusScope(state.viewMode);
  });

  elements.sidebarPanelTabs.addEventListener("click", (event) => {
    const button = event.target.closest("[data-sidebar-panel]");
    if (!button) {
      return;
    }

    const nextPanel = button.dataset.sidebarPanel;
    if (!nextPanel || nextPanel === state.activeSidebarPanel) {
      return;
    }

    state.activeSidebarPanel = nextPanel;
    renderSidebarPanels();
  });

  elements.mobileToolsButton.addEventListener("click", () => {
    setMobileToolsOpen(true);
  });

  elements.closeMobileToolsButton.addEventListener("click", () => {
    setMobileToolsOpen(false);
  });

  elements.mobileSheetBackdrop.addEventListener("click", () => {
    setMobileToolsOpen(false);
  });

  elements.layerAddButton?.addEventListener("click", () => {
    setLayerAddSheetOpen(!state.isLayerAddSheetOpen);
  });

  elements.closeLayerAddSheetButton?.addEventListener("click", () => {
    setLayerAddSheetOpen(false);
  });

  elements.layerAddSheet?.addEventListener("click", (event) => {
    const choice = event.target.closest("[data-layer-add-choice]");
    if (!choice) {
      return;
    }

    if (choice.dataset.layerAddChoice === "public") {
      startPublicLayerFlow();
      return;
    }

    if (choice.dataset.layerAddChoice === "draw") {
      startDrawingLayerFlow();
    }
  });

  elements.publicSimpleFlow?.addEventListener("click", async (event) => {
    const submitButton = event.target.closest("[data-public-action='submit']");
    if (submitButton) {
      await publicWorkspaceController?.handleSgisSubmit();
      return;
    }

    const button = event.target.closest("[data-public-topic], [data-public-shape], [data-public-scope]");
    if (!button) {
      return;
    }

    handleSimplePublicChoice(button);
  });

  window.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") {
      return;
    }

    mapWorkspace.closePopup?.();
    if (state.isLayerAddSheetOpen) {
      setLayerAddSheetOpen(false);
    }
    if (state.isMobileToolsOpen) {
      setMobileToolsOpen(false);
    }
  });

  window.addEventListener("resize", () => {
    if (window.innerWidth > 760 && state.isMobileToolsOpen) {
      setMobileToolsOpen(false);
    } else {
      renderMobileToolsSheet();
    }
  });

  elements.focusPrimaryButton.addEventListener("click", () => {
    mapWorkspace.focusLocation?.(state.referenceLocation);
  });

  elements.fitPrimaryButton.addEventListener("click", () => {
    const coordinates = getVisibleMapCoordinates();
    if (coordinates.length < 2) {
      mapWorkspace.focusLocation?.(state.referenceLocation);
      return;
    }

    mapWorkspace.fitCoordinates(coordinates);
  });

  elements.baseMapModeField.addEventListener("change", () => {
    state.baseMapMode = elements.baseMapModeField.value;
    mapWorkspace.setBaseMapMode?.(state.baseMapMode);
    renderHero();
  });

  elements.adminScaleField?.addEventListener("change", () => {
    const profileId = elements.adminScaleField.value;
    if (elements.sgisProfileField && profileId) {
      elements.sgisProfileField.value = profileId;
      renderPublicPanel();
      setNotice("공간 단위를 바꿨습니다. 레이어로 추가하면 이 단위가 적용됩니다.", "info");
    }
  });

  elements.mapOverlayFilterList?.addEventListener("click", (event) => {
    const button = event.target.closest("[data-overlay-id]");
    if (!button) {
      return;
    }

    const overlayId = button.dataset.overlayId;
    if (!overlayId) {
      return;
    }

    const wasActive = state.mapOverlayLayerIds.includes(overlayId);
    state.mapOverlayLayerIds = wasActive
      ? state.mapOverlayLayerIds.filter((item) => item !== overlayId)
      : [...state.mapOverlayLayerIds, overlayId];
    mapWorkspace.setOverlayLayerIds?.(state.mapOverlayLayerIds);
    renderHero();
    const overlayLabel = MAP_OVERLAY_OPTIONS.find((option) => option.id === overlayId)?.label ?? "지도 보기";
    setNotice(`${overlayLabel} 보기 레이어를 ${wasActive ? "껐습니다" : "켰습니다"}.`, "info");
  });

  elements.locateMeButton.addEventListener("click", () => {
    if (!navigator.geolocation) {
      setNotice("이 브라우저에서는 현재 위치 기능을 지원하지 않습니다.", "warn");
      return;
    }

    state.geolocationPending = true;
    renderHero();

    navigator.geolocation.getCurrentPosition(
      (position) => {
        if (!confirmReferenceLock("현재 위치")) {
          state.geolocationPending = false;
          setNotice("현재 위치 고정을 취소했습니다.", "info");
          renderHero();
          return;
        }

        state.geolocationPending = false;
        mapWorkspace.map.flyTo(
          [position.coords.latitude, position.coords.longitude],
          Math.max(mapWorkspace.map.getZoom(), 16),
          { duration: 0.6 },
        );
        elements.workspaceSchoolNameField.value = "현재 위치";
        elements.workspaceLatField.value = position.coords.latitude.toFixed(6);
        elements.workspaceLngField.value = position.coords.longitude.toFixed(6);
        syncReferenceStateFromWorkspaceForm();
        setReferenceLocked(true);
        rebuildExampleLayers(state.referenceLocation);
        resetWorkspaceRegionCache();
        setNotice("현재 위치를 탐색 중심으로 설정했습니다.", "success");
        renderAll();
      },
      (error) => {
        console.error(error);
        state.geolocationPending = false;
        setNotice("현재 위치를 불러오지 못했습니다. 위치 권한을 확인해 주세요.", "warn");
        renderHero();
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 60000,
      },
    );
  });

  elements.downloadGeoJsonButton.addEventListener("click", () => {
    const payload = buildVisibleWorkspaceGeoJson();
    downloadGeoJson(`${WORKSPACE_STORAGE_SCOPE}-${state.viewMode}-layers.geojson`, payload);
    setNotice("현재 보이는 레이어를 GeoJSON으로 내보냈습니다.", "success");
  });

  elements.legend.addEventListener("click", (event) => {
    const button = event.target.closest("[data-legend-action]");
    if (!button) {
      return;
    }

    handleLegendAction({
      action: button.dataset.legendAction,
      layerId: button.dataset.layerId,
      featureId: button.dataset.featureId,
    });
  });

  elements.mapLayerHub?.addEventListener("click", (event) => {
    const button = event.target.closest("[data-layer-hub-action]");
    if (!button || button.disabled) {
      return;
    }

    handleLayerHubAction({
      action: button.dataset.layerHubAction,
      layerId: button.dataset.layerId,
      featureId: button.dataset.featureId,
    });
  });

  bindWorkspacePanelEvents({
    elements,
    onPresetChange: (presetId) => {
      handleWorkspacePresetChange(presetId);
    },
    onSearchSubmit: async () => {
      await handleWorkspaceSearch();
    },
    onSearchResultPick: (resultId) => {
      handleWorkspaceSearchResultPick(resultId);
    },
    onWorkspaceFieldSync: (options) => {
      handleWorkspaceFieldSync(options);
    },
    onUseMapCenter: () => {
      handleUseMapCenter();
    },
    onWorkspaceSubmit: () => {
      handleWorkspaceSubmit();
    },
    onCopyWorkspaceLink: async () => {
      await handleCopyWorkspaceLink();
    },
    onResetWorkspace: () => {
      handleResetWorkspace();
    },
  });

  bindPublicPanelEvents({
    elements,
    onExampleStarterAction: (action) => {
      publicWorkspaceController.handleExampleStarterAction(action);
    },
    onQuickSgisAction: async ({ action, metricId, profileId }) => {
      await publicWorkspaceController.handleQuickSgisAction({ action, metricId, profileId });
    },
    onExampleLayerAction: ({ action, layerId }) => {
      publicWorkspaceController.handleExampleLayerAction({ action, layerId });
    },
    onSchoolReferenceToggle: () => {
      publicWorkspaceController.handleSchoolReferenceToggle();
    },
    onSgisSubmit: async () => {
      await publicWorkspaceController.handleSgisSubmit();
    },
    onSgisControlChange: () => {
      publicWorkspaceController.handleSgisControlChange();
    },
    onPublicImportSubmit: async () => {
      await publicWorkspaceController.handlePublicImportSubmit();
    },
    onPresetImport: async (presetId) => {
      await publicWorkspaceController.handlePresetImport(presetId);
    },
    onImportedLayerAction: ({ action, layerId }) => {
      publicWorkspaceController.handleImportedLayerAction({ action, layerId });
    },
  });

  elements.nationalStatsToggle.addEventListener("click", () => {
    state.showNationalStats = !state.showNationalStats;
    renderAll();
  });

  elements.nationalDatasetFilters.addEventListener("click", (event) => {
    const button = event.target.closest("[data-dataset-id]");
    if (!button) {
      return;
    }

    const nextDataset = nationalDatasetMap.get(button.dataset.datasetId);
    if (!nextDataset) {
      return;
    }

    state.selectedNationalDatasetId = nextDataset.id;
    if (!nextDataset.years.map(String).includes(state.selectedNationalYear)) {
      state.selectedNationalYear = String(nextDataset.years.at(-1));
    }
    state.selectedNationalPointId = null;
    renderAll();
  });

  elements.nationalYearFilters.addEventListener("click", (event) => {
    const button = event.target.closest("[data-year]");
    if (!button) {
      return;
    }

    state.selectedNationalYear = String(button.dataset.year);
    state.selectedNationalPointId = null;
    renderAll();
  });

  elements.nationalFacilityFilters.addEventListener("click", (event) => {
    const button = event.target.closest("[data-layer-id]");
    if (!button) {
      return;
    }

    const layerId = button.dataset.layerId;
    if (!layerId) {
      return;
    }

    state.activeNationalFacilityLayerIds = state.activeNationalFacilityLayerIds.includes(layerId)
      ? state.activeNationalFacilityLayerIds.filter((item) => item !== layerId)
      : [...state.activeNationalFacilityLayerIds, layerId];
    renderAll();
  });

  elements.nationalRankingList.addEventListener("click", (event) => {
    const button = event.target.closest("[data-point-id]");
    if (!button) {
      return;
    }

    const dataset = getNationalDataset();
    const point = dataset.points.find((item) => item.id === button.dataset.pointId);
    if (!point) {
      return;
    }

    state.selectedNationalPointId = point.id;
    renderAll();
    mapWorkspace.map.flyTo([point.lat, point.lng], Math.max(mapWorkspace.map.getZoom(), 9), {
      duration: 0.6,
    });
  });

  bindStudentPanelEvents({
    elements,
    onCreateStudentLayer: (layerInput) => {
      studentWorkspaceController.handleCreateStudentLayer(layerInput);
    },
    onImportLayerFiles: async (files) => {
      await studentWorkspaceController.handleImportStudentLayerFiles(files);
    },
    onStudentLayerAction: ({ action, layerId, value, featureId }) => {
      studentWorkspaceController.handleStudentLayerAction(action, layerId, value, featureId);
    },
    onSaveSelectedFeature: ({
      title,
      note,
      severity,
      observedLabel,
      observedValue,
      observedUnit,
    }) => {
      studentWorkspaceController.handleSaveSelectedFeature({
        title,
        note,
        severity,
        observedLabel,
        observedValue,
        observedUnit,
      });
    },
    onDeleteSelectedFeature: () => {
      studentWorkspaceController.handleDeleteSelectedFeature();
    },
    onRedrawSelectedFeature: () => {
      studentWorkspaceController.handleRedrawSelectedFeature();
    },
    onCreateFeatureBuffer: ({ radiusMeters }) => {
      studentWorkspaceController.handleCreateFeatureBuffer({ radiusMeters });
    },
    onClearMeasurement: () => {
      clearMeasurementResult();
      clearDraftGeometry();
      renderAll();
      setNotice("현재 측정 결과를 지웠습니다.", "info");
    },
    onSaveMeasurementLayer: () => {
      studentWorkspaceController.handleSaveMeasurementLayer();
    },
    onReflectionInput: (note) => {
      setReflectionNote(note);
    },
    onSaveReflection: () => {
      saveReflection();
    },
    onSaveProject: ({ name }) => {
      saveCurrentWorkspaceProject(name);
    },
    onExportProject: ({ name }) => {
      exportCurrentWorkspaceProject(name);
    },
    onImportProjectFile: async (file) => {
      await importWorkspaceProjectFile(file);
    },
    onSelectProject: (projectId) => {
      state.selectedProjectId = projectId;
      renderStudentPanel();
    },
    onLoadProject: (projectId) => {
      loadSavedWorkspaceProject(projectId);
    },
    onDeleteProject: (projectId) => {
      deleteSavedWorkspaceProject(projectId);
    },
    onCopyPresentationSummary: async (text) => {
      try {
        await copyText(text);
        setNotice("발표용 요약 문장을 복사했습니다.", "success");
      } catch (error) {
        console.error(error);
        setNotice("요약 문장을 복사하지 못했습니다.", "error");
      }
    },
    onPrintPresentationSummary: () => {
      printPresentationSummary();
    },
  });

  bindSuitabilityPanelEvents({
    elements,
    onSuitabilityControlChange: () => {
      syncSuitabilityControlsFromFields();
      renderSuitabilityPanel();
    },
    onCreateSuitability: () => {
      createSuitabilityLayerFromControls();
    },
    onOpenPublicTools: () => {
      openSidebarPanel("public");
    },
    onOpenStudentTools: () => {
      openSidebarPanel("layers");
    },
  });

  bindDrawToolbarEvents({
    elements,
    onToolSelect: (tool) => {
      studentWorkspaceController.handleToolSelect(tool);
    },
    onQuickCreateLayer: () => {
      studentWorkspaceController.handleQuickCreateStudentLayer();
    },
    onActiveLayerChange: (layerId) => {
      studentWorkspaceController.handleActiveLayerChange(layerId);
    },
    onCompleteDraft: () => {
      studentWorkspaceController.handleCompleteDraft();
    },
    onUndoDraftPoint: () => {
      studentWorkspaceController.handleUndoDraftGeometryPoint();
    },
    onCancelDraft: () => {
      studentWorkspaceController.handleCancelDraft();
    },
  });
}

window.__SCHOOL_GIS_READY = false;

function init() {
  initializeWorkspaceForm();
  initializeSgisFormControls();
  elements.publicLayerScopeField.value = state.viewMode;
  elements.publicLayerTypeField.value = "";
  elements.publicLayerColorField.value = getRandomLayerColor(state.importedPublicLayers.length);
  elements.studentLayerColorField.value = getRandomLayerColor(state.studentLayers.length);
  elements.baseMapModeField.value = state.baseMapMode;
  syncStudentEditingState();
  bindEvents();
  syncUrlState();
  mapWorkspace.setBaseMapMode?.(state.baseMapMode);
  renderAll();
  mapWorkspace.focusLocation?.(state.referenceLocation);
  if (EFFECTIVE_CONFIG.sgis.enabled && state.referenceLocked) {
    void workspaceRegionController.ensureWorkspaceRegionInfo().catch((error) => {
      console.warn("Failed to prefetch workspace region.", error);
    });
  }
  window.__SCHOOL_GIS_READY = true;
  document.documentElement.dataset.gisReady = "true";
}

window.addEventListener("load", () => init(), { once: true });

function parsePositiveInteger(value, fallback) {
  const parsed = Number.parseInt(String(value ?? ""), 10);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : fallback;
}

function resolveWorkspaceConfig(baseConfig) {
  const params = new URLSearchParams(window.location.search);
  const hasExplicitLocation = params.has("lat") && params.has("lng");
  const schoolName = params.get("school")?.trim() || baseConfig.schoolName;
  const lat = parseFiniteNumber(params.get("lat"), baseConfig.mapCenter.lat);
  const lng = parseFiniteNumber(params.get("lng"), baseConfig.mapCenter.lng);
  const radiusMeters = parsePositiveInteger(
    params.get("radius"),
    baseConfig.schoolRadiusMeters,
  );

  return {
    ...baseConfig,
    hasExplicitLocation,
    schoolName,
    schoolRadiusMeters: radiusMeters,
    workspaceTopic: "general",
    mapCenter: {
      ...baseConfig.mapCenter,
      lat,
      lng,
      label: `${schoolName} 중심`,
    },
  };
}

function buildWorkspaceStorageScope(workspaceConfig) {
  return `${workspaceConfig.schoolName}-${workspaceConfig.mapCenter.lat.toFixed(4)}-${workspaceConfig.mapCenter.lng.toFixed(4)}-${workspaceConfig.schoolRadiusMeters}`
    .replace(/[^\w.-]+/g, "-")
    .toLowerCase();
}

function buildInitialLocalPublicVisibility(layers) {
  return Object.fromEntries(
    layers.map((layer) => [
      layer.id,
      false,
    ]),
  );
}

function buildInitialLocalPublicOpacity(layers) {
  return Object.fromEntries(
    layers.map((layer) => [
      layer.id,
      1,
    ]),
  );
}

function buildAllLocalPublicVisibility(value) {
  return Object.fromEntries(localPublicLayers.map((layer) => [layer.id, Boolean(value)]));
}

function buildAllLocalPublicOpacity(value = 1) {
  const safeValue = Number.isFinite(Number(value)) ? Math.min(1, Math.max(0, Number(value))) : 1;
  return Object.fromEntries(localPublicLayers.map((layer) => [layer.id, safeValue]));
}

const ADMIN_SCALE_PROFILE_OPTIONS = Object.freeze([
  { profileId: "grid-sgg-500m", label: "현재 주변 500m 격자" },
  { profileId: "region-korea-sido", label: "전국 · 시도 단위" },
  { profileId: "region-sido-children", label: "시도 · 시군구 단위" },
  { profileId: "region-sgg-children", label: "시군구 · 읍면동 단위" },
  { profileId: "region-emdong", label: "읍면동 단위" },
]);

const EFFECTIVE_CONFIG = resolveWorkspaceConfig(APP_CONFIG);
const WORKSPACE_STORAGE_SCOPE = buildWorkspaceStorageScope(EFFECTIVE_CONFIG);
let localPublicLayers = buildLocalPublicLayers(EFFECTIVE_CONFIG.mapCenter);
const initialImportedPublicLayers = loadImportedPublicLayers(WORKSPACE_STORAGE_SCOPE);
const initialStudentLayers = loadStudentLayers(EFFECTIVE_CONFIG.mapCenter, WORKSPACE_STORAGE_SCOPE);
const initialSavedProjects = normalizeWorkspaceProjects(
  loadWorkspaceProjectsRaw(WORKSPACE_STORAGE_SCOPE),
  (project) =>
    normalizeWorkspaceProject(project, {
      normalizeWorkspaceValues: normalizeWorkspaceValuesUseCase,
      fallbackConfig: EFFECTIVE_CONFIG,
      parseFiniteNumber,
      parsePositiveInteger,
      localPublicLayers,
    }),
);

const state = {
  viewMode: "school",
  activeSidebarPanel: "public",
  isMobileToolsOpen: false,
  isLayerAddSheetOpen: false,
  isDrawingToolsOpen: false,
  baseMapMode: "roadmap",
  mapOverlayLayerIds: [],
  showSchoolReference: true,
  showNationalStats: true,
  selectedNationalDatasetId: NATIONAL_DATASETS[0].id,
  selectedNationalYear: String(NATIONAL_DATASETS[0].years.at(-1)),
  activeNationalFacilityLayerIds: NATIONAL_FACILITY_LAYERS
    .filter((layer) => layer.id !== "none")
    .slice(0, 1)
    .map((layer) => layer.id),
  localPublicVisibility: buildInitialLocalPublicVisibility(localPublicLayers),
  localPublicOpacity: buildInitialLocalPublicOpacity(localPublicLayers),
  referenceLocked: Boolean(EFFECTIVE_CONFIG.hasExplicitLocation),
  referenceLocation: {
    lat: EFFECTIVE_CONFIG.mapCenter.lat,
    lng: EFFECTIVE_CONFIG.mapCenter.lng,
  },
  referenceRadiusMeters: EFFECTIVE_CONFIG.schoolRadiusMeters,
  referenceLabel: EFFECTIVE_CONFIG.schoolName,
  importedPublicLayers: initialImportedPublicLayers,
  studentLayers: initialStudentLayers,
  savedProjects: initialSavedProjects,
  selectedProjectId: initialSavedProjects[0]?.id ?? "",
  reflectionNote: loadWorkspaceReflection(WORKSPACE_STORAGE_SCOPE),
  measurementResult: null,
  activeTool: "select",
  activeLayerId: initialStudentLayers[0]?.id ?? null,
  draftGeometry: null,
  selectedFeatureRef: null,
  selectedNationalPointId: null,
  noticeMessage: "",
  noticeTone: "info",
  workspaceSearchResults: [],
  workspaceSearchPending: false,
  geolocationPending: false,
  workspaceRegion: null,
  workspaceRegionPending: false,
  schoolSgisImportPending: "",
  selectedSuitabilityTemplateId: "access",
  selectedSuitabilityGridLayerId: "",
  selectedSuitabilityStudentLayerId: "",
  suitabilityWeights: {
    publicWeight: 55,
    nearWeight: 45,
    farWeight: 0,
  },
};

const elements = {
  heroTitle: document.querySelector("#heroTitle"),
  heroSubtitle: document.querySelector("#heroSubtitle"),
  storageModePill: document.querySelector("#storageModePill"),
  scopePill: document.querySelector("#scopePill"),
  topicPill: document.querySelector("#topicPill"),
  studentLayerPill: document.querySelector("#studentLayerPill"),
  workspaceHint: document.querySelector("#workspaceHint"),
  viewModeToggle: document.querySelector("#viewModeToggle"),
  sidebar: document.querySelector("#sidebar"),
  sidebarPanelTabs: document.querySelector("#sidebarPanelTabs"),
  mobilePanelTitle: document.querySelector("#mobilePanelTitle"),
  mobileToolsButton: document.querySelector("#mobileToolsButton"),
  closeMobileToolsButton: document.querySelector("#closeMobileToolsButton"),
  mobileSheetBackdrop: document.querySelector("#mobileSheetBackdrop"),
  focusPrimaryButton: document.querySelector("#focusPrimaryButton"),
  downloadGeoJsonButton: document.querySelector("#downloadGeoJsonButton"),
  adminScaleField: document.querySelector("#adminScaleField"),
  baseMapModeField: document.querySelector("#baseMapModeField"),
  mapOverlayFilterList: document.querySelector("#mapOverlayFilterList"),
  layerAddButton: document.querySelector("#layerAddButton"),
  layerAddSheet: document.querySelector("#layerAddSheet"),
  closeLayerAddSheetButton: document.querySelector("#closeLayerAddSheetButton"),
  locateMeButton: document.querySelector("#locateMeButton"),
  activePublicCount: document.querySelector("#activePublicCount"),
  studentLayerCount: document.querySelector("#studentLayerCount"),
  studentPointCount: document.querySelector("#studentPointCount"),
  scopeLabel: document.querySelector("#scopeLabel"),
  workspaceForm: document.querySelector("#workspaceForm"),
  workspacePresetField: document.querySelector("#workspacePresetField"),
  workspaceSchoolNameField: document.querySelector("#workspaceSchoolNameField"),
  workspaceSearchButton: document.querySelector("#workspaceSearchButton"),
  workspaceSearchResults: document.querySelector("#workspaceSearchResults"),
  locationSearchField: document.querySelector("#locationSearchField"),
  locationSearchButton: document.querySelector("#locationSearchButton"),
  locationSearchResults: document.querySelector("#locationSearchResults"),
  workspaceLatField: document.querySelector("#workspaceLatField"),
  workspaceLngField: document.querySelector("#workspaceLngField"),
  workspaceRadiusField: document.querySelector("#workspaceRadiusField"),
  workspaceTopicField: document.querySelector("#workspaceTopicField"),
  useMapCenterButton: document.querySelector("#useMapCenterButton"),
  workspaceShareLinkField: document.querySelector("#workspaceShareLinkField"),
  copyWorkspaceLinkButton: document.querySelector("#copyWorkspaceLinkButton"),
  resetWorkspaceButton: document.querySelector("#resetWorkspaceButton"),
  workspaceSummary: document.querySelector("#workspaceSummary"),
  workspaceCard: document.querySelector("#workspaceCard"),
  statsCard: document.querySelector("#statsCard"),
  publicCard: document.querySelector("#publicCard"),
  studentCard: document.querySelector("#studentCard"),
  analysisCard: document.querySelector("#analysisCard"),
  layerStackCard: document.querySelector("#layerStackCard"),
  layerStackSummary: document.querySelector("#layerStackSummary"),
  publicLayerSummary: document.querySelector("#publicLayerSummary"),
  publicSimpleFlow: document.querySelector("#publicSimpleFlow"),
  simplePublicSubmitButton: document.querySelector("#simplePublicSubmitButton"),
  schoolPublicBlock: document.querySelector("#schoolPublicBlock"),
  schoolSgisQuickBlock: document.querySelector("#schoolSgisQuickBlock"),
  schoolSgisTopicHint: document.querySelector("#schoolSgisTopicHint"),
  schoolSgisRegionSummary: document.querySelector("#schoolSgisRegionSummary"),
  sgisMetricRecommendationList: document.querySelector("#sgisMetricRecommendationList"),
  schoolSgisQuickActions: document.querySelector("#schoolSgisQuickActions"),
  publicStarterCard: document.querySelector("#publicStarterCard"),
  schoolReferenceToggle: document.querySelector("#schoolReferenceToggle"),
  publicExampleSection: document.querySelector("#publicExampleSection"),
  publicExampleFoldHint: document.querySelector("#publicExampleFoldHint"),
  recommendedLocalLayerList: document.querySelector("#recommendedLocalLayerList"),
  nationalPublicBlock: document.querySelector("#nationalPublicBlock"),
  nationalStatsToggle: document.querySelector("#nationalStatsToggle"),
  nationalDatasetFilters: document.querySelector("#nationalDatasetFilters"),
  nationalYearFilters: document.querySelector("#nationalYearFilters"),
  nationalFacilityFilters: document.querySelector("#nationalFacilityFilters"),
  nationalSummary: document.querySelector("#nationalSummary"),
  nationalRankingList: document.querySelector("#nationalRankingList"),
  sgisImportBlock: document.querySelector("#sgisImportBlock"),
  sgisLayerForm: document.querySelector("#sgisLayerForm"),
  sgisMetricField: document.querySelector("#sgisMetricField"),
  sgisYearField: document.querySelector("#sgisYearField"),
  sgisProfileField: document.querySelector("#sgisProfileField"),
  sgisProfileSubmitButton: document.querySelector("#sgisProfileSubmitButton"),
  sgisColorField: document.querySelector("#sgisColorField"),
  sgisHelpCopy: document.querySelector("#sgisHelpCopy"),
  publicLayerImportForm: document.querySelector("#publicLayerImportForm"),
  publicLayerNameField: document.querySelector("#publicLayerNameField"),
  publicLayerScopeField: document.querySelector("#publicLayerScopeField"),
  publicLayerTypeField: document.querySelector("#publicLayerTypeField"),
  publicLayerColorField: document.querySelector("#publicLayerColorField"),
  publicLayerUrlField: document.querySelector("#publicLayerUrlField"),
  publicLayerDescriptionField: document.querySelector("#publicLayerDescriptionField"),
  publicPresetSection: document.querySelector("#publicPresetSection"),
  publicPresetList: document.querySelector("#publicPresetList"),
  importedPublicSection: document.querySelector("#importedPublicSection"),
  importedPublicFoldHint: document.querySelector("#importedPublicFoldHint"),
  importedPublicLayerList: document.querySelector("#importedPublicLayerList"),
  studentLayerForm: document.querySelector("#studentLayerForm"),
  studentLayerNameField: document.querySelector("#studentLayerNameField"),
  studentLayerColorField: document.querySelector("#studentLayerColorField"),
  studentLayerDescriptionField: document.querySelector("#studentLayerDescriptionField"),
  layerFileField: document.querySelector("#layerFileField"),
  studentActionTitle: document.querySelector("#studentActionTitle"),
  studentActionBody: document.querySelector("#studentActionBody"),
  selectedFeatureSection: document.querySelector("#selectedFeatureSection"),
  selectedFeatureFoldHint: document.querySelector("#selectedFeatureFoldHint"),
  selectedFeatureMeta: document.querySelector("#selectedFeatureMeta"),
  selectedFeatureCoordinates: document.querySelector("#selectedFeatureCoordinates"),
  featureSeverityField: document.querySelector("#featureSeverityField"),
  featureValueLabelField: document.querySelector("#featureValueLabelField"),
  featureValueField: document.querySelector("#featureValueField"),
  featureValueUnitField: document.querySelector("#featureValueUnitField"),
  selectedFeatureMeasurement: document.querySelector("#selectedFeatureMeasurement"),
  measurementSection: document.querySelector("#measurementSection"),
  measurementFoldHint: document.querySelector("#measurementFoldHint"),
  measurementTitle: document.querySelector("#measurementTitle"),
  measurementValue: document.querySelector("#measurementValue"),
  measurementDetail: document.querySelector("#measurementDetail"),
  saveMeasurementLayerButton: document.querySelector("#saveMeasurementLayerButton"),
  clearMeasurementButton: document.querySelector("#clearMeasurementButton"),
  reflectionSection: document.querySelector("#reflectionSection"),
  reflectionFoldHint: document.querySelector("#reflectionFoldHint"),
  reflectionNoteField: document.querySelector("#reflectionNoteField"),
  saveReflectionButton: document.querySelector("#saveReflectionButton"),
  reflectionHint: document.querySelector("#reflectionHint"),
  projectSection: document.querySelector("#projectSection"),
  projectFoldHint: document.querySelector("#projectFoldHint"),
  projectNameField: document.querySelector("#projectNameField"),
  savedProjectSelectField: document.querySelector("#savedProjectSelectField"),
  saveProjectButton: document.querySelector("#saveProjectButton"),
  loadSavedProjectButton: document.querySelector("#loadSavedProjectButton"),
  exportProjectButton: document.querySelector("#exportProjectButton"),
  projectImportFileField: document.querySelector("#projectImportFileField"),
  deleteSavedProjectButton: document.querySelector("#deleteSavedProjectButton"),
  savedProjectHint: document.querySelector("#savedProjectHint"),
  summarySection: document.querySelector("#summarySection"),
  summaryFoldHint: document.querySelector("#summaryFoldHint"),
  summaryHeadline: document.querySelector("#summaryHeadline"),
  summarySnapshotGrid: document.querySelector("#summarySnapshotGrid"),
  summaryInsightList: document.querySelector("#summaryInsightList"),
  presentationSummaryField: document.querySelector("#presentationSummaryField"),
  copyPresentationSummaryButton: document.querySelector("#copyPresentationSummaryButton"),
  printPresentationSummaryButton: document.querySelector("#printPresentationSummaryButton"),
  presentationSummaryHint: document.querySelector("#presentationSummaryHint"),
  editingLayerLabel: document.querySelector("#editingLayerLabel"),
  mapClickLabel: document.querySelector("#mapClickLabel"),
  pointTitleField: document.querySelector("#pointTitleField"),
  pointNoteField: document.querySelector("#pointNoteField"),
  featureBufferRadiusField: document.querySelector("#featureBufferRadiusField"),
  saveSelectedFeatureButton: document.querySelector("#saveSelectedFeatureButton"),
  redrawSelectedFeatureButton: document.querySelector("#redrawSelectedFeatureButton"),
  deleteSelectedFeatureButton: document.querySelector("#deleteSelectedFeatureButton"),
  createFeatureBufferButton: document.querySelector("#createFeatureBufferButton"),
  studentLayerList: document.querySelector("#studentLayerList"),
  drawToolbar: document.querySelector("#drawToolbar"),
  quickCreateLayerButton: document.querySelector("#quickCreateLayerButton"),
  activeLayerField: document.querySelector("#activeLayerField"),
  undoDraftPointButton: document.querySelector("#undoDraftPointButton"),
  completeDraftButton: document.querySelector("#completeDraftButton"),
  cancelDraftButton: document.querySelector("#cancelDraftButton"),
  drawToolbarHint: document.querySelector("#drawToolbarHint"),
  mapTitle: document.querySelector("#mapTitle"),
  fitPrimaryButton: document.querySelector("#fitPrimaryButton"),
  mapLayerHub: document.querySelector("#mapLayerHub"),
  legend: document.querySelector("#legend"),
  statusNotice: document.querySelector("#statusNotice"),
  suitabilityTemplateField: document.querySelector("#suitabilityTemplateField"),
  suitabilityTemplateDescription: document.querySelector("#suitabilityTemplateDescription"),
  suitabilityGridLayerField: document.querySelector("#suitabilityGridLayerField"),
  suitabilityStudentLayerField: document.querySelector("#suitabilityStudentLayerField"),
  suitabilityPublicWeightField: document.querySelector("#suitabilityPublicWeightField"),
  suitabilityPublicWeightValue: document.querySelector("#suitabilityPublicWeightValue"),
  suitabilityNearWeightField: document.querySelector("#suitabilityNearWeightField"),
  suitabilityNearWeightValue: document.querySelector("#suitabilityNearWeightValue"),
  suitabilityFarWeightField: document.querySelector("#suitabilityFarWeightField"),
  suitabilityFarWeightValue: document.querySelector("#suitabilityFarWeightValue"),
  suitabilityEmptyReason: document.querySelector("#suitabilityEmptyReason"),
  createSuitabilityButton: document.querySelector("#createSuitabilityButton"),
  openPublicForSuitabilityButton: document.querySelector("#openPublicForSuitabilityButton"),
  openStudentForSuitabilityButton: document.querySelector("#openStudentForSuitabilityButton"),
  suitabilityResult: document.querySelector("#suitabilityResult"),
};

function resolveInitialViewMode() {
  return "school";
}

function resolveDefaultSidebarPanel(viewMode = state.viewMode) {
  return viewMode === "school" ? "public" : "public";
}

function getSidebarPanelLabel(panelId = state.activeSidebarPanel) {
  return SIDEBAR_PANEL_LABEL[panelId] ?? SIDEBAR_PANEL_LABEL.student;
}

function setMobileToolsOpen(nextOpen) {
  state.isMobileToolsOpen = Boolean(nextOpen);
  renderMobileToolsSheet();
}

function renderLayerAddSheet() {
  if (!elements.layerAddSheet || !elements.layerAddButton) {
    return;
  }

  elements.layerAddSheet.hidden = !state.isLayerAddSheetOpen;
  elements.layerAddButton.setAttribute("aria-expanded", String(state.isLayerAddSheetOpen));
}

function setLayerAddSheetOpen(nextOpen) {
  state.isLayerAddSheetOpen = Boolean(nextOpen);
  renderLayerAddSheet();
}

function startPublicLayerFlow() {
  state.isLayerAddSheetOpen = false;
  state.isDrawingToolsOpen = false;
  state.activeSidebarPanel = "public";
  renderAll();
  setNotice("통계자료 가져오기를 열었습니다. 먼저 볼 주제를 고르세요.", "info");
}

function startDrawingLayerFlow() {
  state.isLayerAddSheetOpen = false;
  state.isDrawingToolsOpen = true;
  state.activeSidebarPanel = "student";
  studentWorkspaceController?.handleToolSelect("point");
  renderAll();
}

function setSimplePublicActive(button, selector) {
  elements.publicSimpleFlow?.querySelectorAll(selector).forEach((item) => {
    item.classList.toggle("is-active", item === button);
  });
}

function getSimplePublicSelection(selector, attributeName, fallback) {
  const activeButton = elements.publicSimpleFlow?.querySelector(`${selector}.is-active`);
  return activeButton?.dataset?.[attributeName] ?? fallback;
}

function syncSimplePublicProfile() {
  const shape = getSimplePublicSelection("[data-public-shape]", "publicShape", "grid");
  const scope = getSimplePublicSelection("[data-public-scope]", "publicScope", "current");
  const profileId = SIMPLE_PUBLIC_PROFILE[`${shape}-${scope}`] ?? SIMPLE_PUBLIC_PROFILE["grid-current"];

  if (elements.sgisProfileField && [...elements.sgisProfileField.options].some((option) => option.value === profileId)) {
    elements.sgisProfileField.value = profileId;
  }
  if (elements.adminScaleField && [...elements.adminScaleField.options].some((option) => option.value === profileId)) {
    elements.adminScaleField.value = profileId;
  }
}

function handleSimplePublicChoice(button) {
  const topic = button.dataset.publicTopic;
  if (topic) {
    setSimplePublicActive(button, "[data-public-topic]");
    const metricId = SIMPLE_PUBLIC_TOPIC_METRIC[topic] ?? SIMPLE_PUBLIC_TOPIC_METRIC.population;
    if (elements.sgisMetricField && [...elements.sgisMetricField.options].some((option) => option.value === metricId)) {
      elements.sgisMetricField.value = metricId;
    }
    renderPublicPanel();
    setNotice("통계 주제를 바꿨습니다. 레이어로 추가하면 지도에 반영됩니다.", "info");
    return;
  }

  if (button.dataset.publicShape) {
    setSimplePublicActive(button, "[data-public-shape]");
    syncSimplePublicProfile();
    renderPublicPanel();
    setNotice("통계를 표시할 모양을 바꿨습니다.", "info");
    return;
  }

  if (button.dataset.publicScope) {
    setSimplePublicActive(button, "[data-public-scope]");
    syncSimplePublicProfile();
    renderPublicPanel();
    setNotice("통계를 볼 범위를 바꿨습니다.", "info");
  }
}

function getSgisMetricRecommendation(metricId) {
  return SGIS_METRIC_RECOMMENDATION_META[metricId] ?? {
    studentLabel: metricId,
    helper: "",
  };
}

function getCurrentLocationLabel() {
  return String(elements.workspaceSchoolNameField?.value || state.referenceLabel || "탐색 중심").trim();
}

function syncReferenceStateFromWorkspaceForm() {
  const values = getWorkspaceFormValues();
  state.referenceLocation = {
    lat: values.lat,
    lng: values.lng,
  };
  state.referenceRadiusMeters = values.radiusMeters;
  state.referenceLabel = values.schoolName;
}

function rebuildExampleLayers(center) {
  localPublicLayers = buildLocalPublicLayers(center);
  state.localPublicVisibility = buildAllLocalPublicVisibility(false);
  state.localPublicOpacity = buildAllLocalPublicOpacity(1);
}

function syncUrlState() {
  const url = new URL(window.location.href);
  url.searchParams.delete("view");
  url.searchParams.delete("mode");
  window.history.replaceState({}, "", `${url.pathname}${url.search}${url.hash}`);
}

function getNationalDataset(targetState = state) {
  return nationalDatasetMap.get(targetState.selectedNationalDatasetId) ?? NATIONAL_DATASETS[0];
}

function getNationalPointValue(point, year) {
  return Number(point.values[year]);
}

function getNationalStats(dataset, year) {
  const values = dataset.points.map((point) => getNationalPointValue(point, year));
  const sorted = [...values].sort((left, right) => right - left);
  const average = values.reduce((total, value) => total + value, 0) / values.length;
  const middle = Math.floor(sorted.length / 2);

  return {
    min: Math.min(...values),
    max: Math.max(...values),
    average,
    median:
      sorted.length % 2 === 0
        ? (sorted[middle - 1] + sorted[middle]) / 2
        : sorted[middle],
  };
}

function getNationalGradient(dataset) {
  return dataset.higherIsBetter
    ? { low: "#db6d56", high: "#258b63" }
    : { low: "#258b63", high: "#db6d56" };
}

let studentWorkspaceController = null;
let publicWorkspaceController = null;
let workspaceRegionController = null;

const mapWorkspace = createLayerWorkspaceMap({
  mapId: "map",
  appConfig: EFFECTIVE_CONFIG,
  koreaMapView: KOREA_MAP_VIEW,
  localPublicLayers: () => localPublicLayers,
  nationalFacilityLayers: NATIONAL_FACILITY_LAYERS,
  getNationalDataset,
  getNationalPointValue,
  getNationalStats,
  getNationalGradient,
  onMapClick: (latlng) => {
    studentWorkspaceController?.handleMapClick(latlng);
  },
  onStudentFeatureInteract: (featureRef) => {
    studentWorkspaceController?.handleStudentFeatureInteract(featureRef);
  },
  onNationalPointSelect: (pointId) => {
    state.selectedNationalPointId = pointId;
    renderPublicPanel();
  },
});

studentWorkspaceController = createStudentWorkspaceController({
  state,
  elements,
  mapWorkspace,
  createId,
  drawToolMeta: DRAW_TOOL_META,
  observationSeverityLabel: OBSERVATION_SEVERITY_LABEL,
  setStudentLayers,
  setActiveStudentLayer,
  selectStudentFeature,
  getActiveStudentLayer,
  getSelectedStudentFeatureRecord,
  setMeasurementResult,
  clearMeasurementResult,
  clearDraftGeometry,
  resetStudentDraftInputs,
  resetStudentLayerForm,
  renderAll,
  setNotice,
  downloadGeoJson,
  importLayerFile,
  setImportedPublicLayers,
  getNextImportedPublicColor: () => getRandomLayerColor(state.importedPublicLayers.length),
  getNextStudentLayerColor: () => getRandomLayerColor(state.studentLayers.length),
  openStudentTools: () => openSidebarPanel("student"),
});

workspaceRegionController = createWorkspaceRegionController({
  state,
  appConfig: EFFECTIVE_CONFIG,
  renderPublicPanel,
  getWorkspaceFormValues,
  buildWorkspaceRegionCacheKey: buildWorkspaceRegionCacheKeyUseCase,
  loadSgisModule,
  getSchoolSgisControlValues: () => getSchoolSgisControlValuesUseCase(elements),
  handleSgisImport,
  getCurrentLocationLabel,
  mapWorkspace,
  collectFeatureCollectionCoordinates,
  setNotice,
});

publicWorkspaceController = createPublicWorkspaceController({
  state,
  elements,
  mapWorkspace,
  appConfig: EFFECTIVE_CONFIG,
  getLocalPublicLayers: () => localPublicLayers,
  setImportedPublicLayers,
  renderAll,
  renderPublicPanel,
  setNotice,
  getCurrentSgisProfile: () => getCurrentSgisProfileUseCase(elements, SGIS_REGION_LAYER_PROFILES),
  ensureWorkspaceRegionInfo: (options) => workspaceRegionController.ensureWorkspaceRegionInfo(options),
  handleRegionSgisProfileImport: (profileId) => workspaceRegionController.handleRegionSgisProfileImport(profileId),
  importPublicLayerFromUrl,
  importPublicLayerFromPreset,
  collectFeatureCollectionCoordinates,
  getRandomLayerColor,
  downloadGeoJson,
});

function getVisibleStudentLayers() {
  return state.studentLayers.filter((layer) => layer.visible);
}

function getActiveStudentLayer() {
  return state.studentLayers.find((layer) => layer.id === state.activeLayerId) ?? null;
}

function clearDraftGeometry() {
  state.draftGeometry = null;
}

function getSelectedStudentFeatureRecord() {
  return findSelectedStudentFeature(state.studentLayers, state.selectedFeatureRef);
}

function syncStudentEditingState() {
  state.activeTool = resolveDrawTool(state.activeTool);

  if (!state.studentLayers.some((layer) => layer.id === state.activeLayerId)) {
    state.activeLayerId = state.studentLayers[0]?.id ?? null;
  }

  if (!findSelectedStudentFeature(state.studentLayers, state.selectedFeatureRef)) {
    state.selectedFeatureRef = null;
  }

  if (!state.activeLayerId) {
    clearDraftGeometry();
    if (isStudentFeatureDrawTool(state.activeTool)) {
      state.activeTool = "select";
    }
    return;
  }

  const expectedGeometryType = getDrawToolGeometryType(state.activeTool);
  if (
    state.draftGeometry
    && (!expectedGeometryType || state.draftGeometry.geometryType !== expectedGeometryType)
  ) {
    clearDraftGeometry();
  }
}

function setStudentLayers(nextLayers) {
  state.studentLayers = nextLayers.map(normalizeStudentLayer);
  saveStudentLayers(state.studentLayers, WORKSPACE_STORAGE_SCOPE);
  syncStudentEditingState();
}

function resetStudentDraftInputs() {
  elements.pointTitleField.value = "";
  elements.pointNoteField.value = "";
  if (elements.featureValueLabelField) {
    elements.featureValueLabelField.value = "";
  }
  if (elements.featureValueField) {
    elements.featureValueField.value = "";
  }
  if (elements.featureValueUnitField) {
    elements.featureValueUnitField.value = "";
  }
  elements.featureSeverityField.value = "2";
}

function resetStudentLayerForm() {
  elements.studentLayerForm.reset();
  elements.studentLayerColorField.value = getRandomLayerColor(state.studentLayers.length);
}

function selectStudentFeature(layerId, featureId) {
  const nextRef = createSelectedFeatureRef(layerId, featureId);
  if (!nextRef) {
    state.selectedFeatureRef = null;
    return;
  }

  state.activeLayerId = layerId;
  state.selectedFeatureRef = nextRef;
}

function setActiveStudentLayer(layerId) {
  const nextLayer = state.studentLayers.find((layer) => layer.id === layerId);
  state.activeLayerId = nextLayer?.id ?? null;
  if (state.selectedFeatureRef && state.selectedFeatureRef.layerId !== state.activeLayerId) {
    state.selectedFeatureRef = null;
  }
  syncStudentEditingState();
}

function saveReflection() {
  setReflectionNote(elements.reflectionNoteField.value, { persist: true });
  renderStudentPanel();
  setNotice("지역성 한 줄 정리를 저장했습니다.", "success");
}

function getVisibleImportedPublicLayers() {
  return state.importedPublicLayers
    .filter((layer) => layer.visible)
    .filter((layer) => layer.scope === "both" || layer.scope === state.viewMode);
}

function setImportedPublicLayers(nextLayers) {
  state.importedPublicLayers = nextLayers.map(normalizeImportedPublicLayer);
  saveImportedPublicLayers(state.importedPublicLayers, WORKSPACE_STORAGE_SCOPE);
}

function setSavedProjects(nextProjects) {
  state.savedProjects = nextProjects;
  if (!state.savedProjects.some((project) => project.id === state.selectedProjectId)) {
    state.selectedProjectId = state.savedProjects[0]?.id ?? "";
  }
  saveWorkspaceProjectsRaw(state.savedProjects, WORKSPACE_STORAGE_SCOPE);
}

function setReflectionNote(note, { persist = false } = {}) {
  state.reflectionNote = String(note ?? "");
  if (persist) {
    saveWorkspaceReflection(state.reflectionNote, WORKSPACE_STORAGE_SCOPE);
  }
}

function setMeasurementResult(result) {
  state.measurementResult = result;
}

function clearMeasurementResult() {
  state.measurementResult = null;
}

function setNotice(message, tone = "info") {
  state.noticeMessage = message;
  state.noticeTone = tone;
  renderStatusNotice();
}

function getActivePublicLayerCount() {
  return Number(state.showSchoolReference)
    + localPublicLayers.filter((layer) => state.localPublicVisibility[layer.id]).length
    + getVisibleImportedPublicLayers().length;
}

function getVisibleStudentFeatureCount() {
  return getVisibleStudentLayers().reduce((total, layer) => total + layer.features.length, 0);
}

function getActivePublicLayersForSummary() {
  const layers = [];

  if (state.showSchoolReference) {
    layers.push({
      id: "reference-area",
      label: "탐색 기준 반경",
    });
  }

  localPublicLayers
    .filter((layer) => state.localPublicVisibility[layer.id])
    .forEach((layer) => {
      layers.push({
        id: layer.id,
        label: layer.label,
      });
    });

  getVisibleImportedPublicLayers().forEach((layer) => {
    layers.push({
      id: layer.id,
      label: layer.name,
    });
  });

  return layers;
}

function getLatestAnalysisLayer() {
  return [...getVisibleImportedPublicLayers()]
    .filter((layer) => layer.sourceKind === "analysis")
    .sort((left, right) =>
      new Date(right.createdAt ?? 0).getTime() - new Date(left.createdAt ?? 0).getTime())[0]
    ?? null;
}

function getRecentAnalysisSummary() {
  const latestAnalysisLayer = [...getVisibleImportedPublicLayers()]
    .filter((layer) => layer.sourceKind === "analysis" && layer.analysisType !== "suitability")
    .sort((left, right) =>
      new Date(right.createdAt ?? 0).getTime() - new Date(left.createdAt ?? 0).getTime())[0]
    ?? null;
  const latestSuitabilityLayer = getLatestSuitabilityLayer();
  const latestBuffer = latestAnalysisLayer
    ? {
        name: latestAnalysisLayer.name,
        areaLabel: latestAnalysisLayer.measurementSummary?.totalAreaLabel ?? "",
        perimeterLabel: latestAnalysisLayer.measurementSummary?.totalPerimeterLabel ?? "",
      }
    : null;

  const latestMeasurement = state.measurementResult
    ? {
        title: state.measurementResult.title,
        primaryLabel: state.measurementResult.primaryLabel,
        primaryValue: state.measurementResult.primaryValue,
        detail: state.measurementResult.detail,
      }
    : null;

  return {
    latestBuffer,
    latestMeasurement,
    latestSuitability: latestSuitabilityLayer
      ? {
          name: latestSuitabilityLayer.name,
          topCandidates: latestSuitabilityLayer.topCandidates ?? [],
        }
      : null,
  };
}

function getStudentWorkspaceSummary() {
  return buildWorkspaceSummary({
    schoolName: getCurrentLocationLabel(),
    topicLabel: "자유형 GIS",
    activePublicLayers: getActivePublicLayersForSummary(),
    studentLayers: getVisibleStudentLayers(),
    reflectionNote: state.reflectionNote,
    recentAnalysis: getRecentAnalysisSummary(),
  });
}

function getCurrentProjectNameSuggestion() {
  return `${getCurrentLocationLabel()} 프로젝트`;
}

function getSelectedFeatureMeasurementSummary() {
  const selectedFeatureRecord = getSelectedStudentFeatureRecord();
  if (!selectedFeatureRecord) {
    return "";
  }

  const measurementSummary = buildFeatureMeasurementSummary(selectedFeatureRecord.feature);
  if (!measurementSummary) {
    return "점 객체는 길이와 면적이 없습니다.";
  }

  if (selectedFeatureRecord.feature.geometryType === "line") {
    return `길이 ${measurementSummary.lengthLabel}`;
  }

  if (selectedFeatureRecord.feature.geometryType === "polygon") {
    return `면적 ${measurementSummary.areaLabel} · 둘레 ${measurementSummary.perimeterLabel}`;
  }

  return "";
}

function getCurrentSgisControlValues() {
  return getSchoolSgisControlValuesUseCase(elements);
}

function getWorkspaceProjectView() {
  return buildWorkspaceProjectViewModel(state.savedProjects, state.selectedProjectId);
}

function getLatestSuitabilityLayer() {
  return [...getVisibleImportedPublicLayers()]
    .filter((layer) => layer.sourceKind === "analysis" && layer.analysisType === "suitability")
    .sort((left, right) =>
      new Date(right.createdAt ?? 0).getTime() - new Date(left.createdAt ?? 0).getTime())[0]
    ?? null;
}

function getSuitabilityWeightsFromFields() {
  return {
    publicWeight: Number(elements.suitabilityPublicWeightField?.value ?? state.suitabilityWeights.publicWeight),
    nearWeight: Number(elements.suitabilityNearWeightField?.value ?? state.suitabilityWeights.nearWeight),
    farWeight: Number(elements.suitabilityFarWeightField?.value ?? state.suitabilityWeights.farWeight),
  };
}

function syncSuitabilityControlsFromFields() {
  const nextTemplateId = elements.suitabilityTemplateField?.value || state.selectedSuitabilityTemplateId;
  const templateChanged = nextTemplateId !== state.selectedSuitabilityTemplateId;
  state.selectedSuitabilityTemplateId = nextTemplateId;
  state.selectedSuitabilityGridLayerId = elements.suitabilityGridLayerField?.value ?? "";
  state.selectedSuitabilityStudentLayerId = elements.suitabilityStudentLayerField?.value ?? "";

  if (templateChanged) {
    const template = getSuitabilityTemplate(nextTemplateId);
    state.suitabilityWeights = {
      publicWeight: template.publicWeight,
      nearWeight: template.nearWeight,
      farWeight: template.farWeight,
    };
    return;
  }

  state.suitabilityWeights = getSuitabilityWeightsFromFields();
}

function getSuitabilityPanelView() {
  return buildSuitabilityPanelViewModel({
    importedPublicLayers: state.importedPublicLayers,
    studentLayers: state.studentLayers,
    selectedTemplateId: state.selectedSuitabilityTemplateId,
    selectedGridLayerId: state.selectedSuitabilityGridLayerId,
    selectedStudentLayerId: state.selectedSuitabilityStudentLayerId,
    weights: state.suitabilityWeights,
    latestSuitabilityLayer: getLatestSuitabilityLayer(),
  });
}

function renderSuitabilityPanel() {
  const viewModel = getSuitabilityPanelView();
  state.selectedSuitabilityTemplateId = viewModel.selectedTemplateId;
  state.selectedSuitabilityGridLayerId = viewModel.selectedGridLayerId;
  state.selectedSuitabilityStudentLayerId = viewModel.selectedStudentLayerId;
  state.suitabilityWeights = viewModel.weights;

  renderSuitabilityPanelView({
    elements,
    viewModel,
    escapeHtml,
  });
}

function createSuitabilityLayerFromControls() {
  syncSuitabilityControlsFromFields();
  const viewModel = getSuitabilityPanelView();
  const gridLayer = state.importedPublicLayers.find((layer) => layer.id === viewModel.selectedGridLayerId);
  const studentLayer = state.studentLayers.find((layer) => layer.id === viewModel.selectedStudentLayerId) ?? null;

  try {
    const layer = createSuitabilityAnalysisLayer({
      idFactory: createId,
      gridLayer,
      studentLayer,
      templateId: viewModel.selectedTemplateId,
      weights: state.suitabilityWeights,
      color: getRandomLayerColor(state.importedPublicLayers.length),
      scope: state.viewMode,
    });
    setImportedPublicLayers([layer, ...state.importedPublicLayers]);
    state.activeSidebarPanel = "analysis";
    renderAll();
    setNotice(`${layer.name} 분석 레이어를 만들었습니다. 상위 후보 3개를 결과 카드에서 확인하세요.`, "success");
  } catch (error) {
    console.error(error);
    setNotice(error.message || "입지점수 레이어를 만들지 못했습니다.", "error");
    renderSuitabilityPanel();
  }
}

function buildPresentationPrintHtml(summary) {
  const generatedAt = new Date().toLocaleString("ko-KR");
  const topicLabel = "자유형 GIS";
  const insightMarkup = summary.insights
    .map((insight) => `<li>${escapeHtml(insight)}</li>`)
    .join("");
  const snapshotMarkup = summary.snapshots
    .map(
      (item) => `
        <article class="snapshot-card">
          <span>${escapeHtml(item.label)}</span>
          <strong>${escapeHtml(item.value)}</strong>
          <p>${escapeHtml(item.detail)}</p>
        </article>
      `,
    )
    .join("");

  return `<!doctype html>
<html lang="ko">
  <head>
    <meta charset="utf-8" />
    <title>${escapeHtml(getCurrentLocationLabel())} 발표 요약</title>
    <style>
      :root {
        color-scheme: light;
        --ink: #10221d;
        --ink-soft: #4b635d;
        --line: rgba(16, 77, 66, 0.12);
        --panel: #ffffff;
        --accent: #1c6a57;
        --soft: #f3f7f2;
      }

      * { box-sizing: border-box; }
      body {
        margin: 0;
        padding: 32px;
        color: var(--ink);
        font-family: "IBM Plex Sans KR", sans-serif;
        background: #f6f8f5;
      }
      .sheet {
        max-width: 920px;
        margin: 0 auto;
        padding: 28px;
        border: 1px solid var(--line);
        border-radius: 24px;
        background: var(--panel);
      }
      h1, h2, h3, p { margin: 0; }
      .eyebrow {
        color: var(--accent);
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
      }
      .hero {
        display: grid;
        gap: 10px;
        margin-bottom: 24px;
      }
      .sub {
        color: var(--ink-soft);
        line-height: 1.6;
      }
      .meta {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
      }
      .pill {
        display: inline-flex;
        align-items: center;
        padding: 8px 12px;
        border-radius: 999px;
        background: var(--soft);
        color: var(--accent);
        font-size: 13px;
        font-weight: 700;
      }
      .section {
        margin-top: 24px;
        display: grid;
        gap: 12px;
      }
      .snapshot-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 12px;
      }
      .snapshot-card {
        padding: 14px 16px;
        border-radius: 16px;
        border: 1px solid var(--line);
        background: var(--soft);
      }
      .snapshot-card span {
        display: block;
        color: var(--ink-soft);
        font-size: 13px;
      }
      .snapshot-card strong {
        display: block;
        margin-top: 6px;
        font-size: 22px;
      }
      .snapshot-card p {
        margin-top: 8px;
        color: var(--ink-soft);
        line-height: 1.5;
      }
      ul {
        margin: 0;
        padding-left: 20px;
      }
      li {
        margin: 0 0 8px;
        color: var(--ink-soft);
        line-height: 1.6;
      }
      .statement {
        padding: 18px;
        border-radius: 18px;
        border: 1px solid var(--line);
        background: linear-gradient(135deg, rgba(28, 106, 87, 0.08), rgba(240, 191, 85, 0.08));
      }
      .statement p {
        margin-top: 8px;
        line-height: 1.7;
      }
      @media print {
        body {
          padding: 0;
          background: #ffffff;
        }
        .sheet {
          border: none;
          border-radius: 0;
          margin: 0;
          max-width: none;
        }
      }
    </style>
  </head>
  <body>
    <main class="sheet">
      <section class="hero">
        <p class="eyebrow">Student GIS Summary</p>
        <h1>${escapeHtml(getCurrentLocationLabel())} GIS 탐구 요약</h1>
        <p class="sub">${escapeHtml(summary.headline)}</p>
        <div class="meta">
          <span class="pill">${escapeHtml(topicLabel)}</span>
          <span class="pill">${escapeHtml(generatedAt)} 생성</span>
        </div>
      </section>

      <section class="section">
        <h2>탐구 한눈에 보기</h2>
        <div class="snapshot-grid">${snapshotMarkup}</div>
      </section>

      <section class="section">
        <h2>겹쳐 보고 찾은 점</h2>
        <ul>${insightMarkup}</ul>
      </section>

      <section class="section statement">
        <p class="eyebrow">Presentation Statement</p>
        <h2>발표용 요약 문장</h2>
        <p>${escapeHtml(summary.presentationText)}</p>
      </section>
    </main>
  </body>
</html>`;
}

function printPresentationSummary() {
  const summary = getStudentWorkspaceSummary();
  const popup = window.open("", "_blank", "noopener,noreferrer");

  if (!popup) {
    setNotice("인쇄 창을 열지 못했습니다. 팝업 차단 설정을 확인해 주세요.", "error");
    return;
  }

  popup.document.open();
  popup.document.write(buildPresentationPrintHtml(summary));
  popup.document.close();
  popup.focus();
  window.setTimeout(() => {
    popup.print();
  }, 250);
}

async function getDefaultSgisYear() {
  const { SGIS_SUPPORTED_YEARS } = await loadSgisModule();
  const configuredYear = Number(
    EFFECTIVE_CONFIG.sgis.defaultYear ?? EFFECTIVE_CONFIG.sgis.defaultBoundaryYear,
  );
  return SGIS_SUPPORTED_YEARS.includes(configuredYear)
    ? configuredYear
    : SGIS_SUPPORTED_YEARS.at(-1);
}

async function initializeSgisFormControls() {
  if (!elements.sgisLayerForm) {
    return;
  }

  try {
    const { SGIS_POPULATION_METRICS, SGIS_SUPPORTED_YEARS } = await loadSgisModule();

    elements.sgisMetricField.innerHTML = SGIS_POPULATION_METRICS.map(
      (metric) =>
        `<option value="${escapeHtml(metric.id)}">${escapeHtml(metric.label)}</option>`,
    ).join("");
    elements.sgisYearField.innerHTML = SGIS_SUPPORTED_YEARS.map(
      (year) => `<option value="${year}">${year}</option>`,
    ).join("");
    if (elements.adminScaleField) {
      elements.adminScaleField.innerHTML = ADMIN_SCALE_PROFILE_OPTIONS.map(
        (option) =>
          `<option value="${escapeHtml(option.profileId)}">${escapeHtml(option.label)}</option>`,
      ).join("");
    }
    if (elements.sgisProfileField) {
      elements.sgisProfileField.innerHTML = SGIS_REGION_LAYER_PROFILES.map(
        (profile) =>
          `<option value="${escapeHtml(profile.id)}">${escapeHtml(profile.label)}</option>`,
      ).join("");
      const defaultProfileId = elements.adminScaleField?.value
        || (SGIS_REGION_LAYER_PROFILES.find((profile) => profile.id === "grid-sgg-500m")?.id
        ?? SGIS_REGION_LAYER_PROFILES[0]?.id
        ?? "");
      elements.sgisProfileField.value = defaultProfileId;
    }
    elements.sgisMetricField.value = EFFECTIVE_CONFIG.sgis.defaultMetric;
    elements.sgisYearField.value = String(await getDefaultSgisYear());
    renderPublicPanel();
  } catch (error) {
    console.error(error);
    elements.sgisImportBlock.hidden = true;
  }
}

function getWorkspaceFormValues() {
  return normalizeWorkspaceValuesUseCase({
    schoolName: elements.workspaceSchoolNameField.value,
    lat: elements.workspaceLatField.value,
    lng: elements.workspaceLngField.value,
    radiusMeters: elements.workspaceRadiusField.value,
    topic: elements.workspaceTopicField.value,
  }, {
    fallbackConfig: EFFECTIVE_CONFIG,
    parseFiniteNumber,
    parsePositiveInteger,
  });
}

function resetWorkspaceRegionCache() {
  state.workspaceRegion = null;
  state.workspaceRegionPending = false;
  state.schoolSgisImportPending = "";
}

function confirmReferenceLock(label) {
  return window.confirm(
    `"${label}" 위치를 지금 이 화면의 GIS 기준 위치로 고정할까요?\n\n고정 후에는 이 위치를 기준으로 시군구/읍면동 범위와 SGIS 통계 레이어를 불러옵니다.`,
  );
}

function setReferenceLocked(locked = true) {
  state.referenceLocked = Boolean(locked);
}

function buildWorkspaceUrl(values, viewMode = state.viewMode) {
  return buildWorkspaceUrlUseCase(values, viewMode, (rawValues) =>
    normalizeWorkspaceValuesUseCase(rawValues, {
      fallbackConfig: EFFECTIVE_CONFIG,
      parseFiniteNumber,
      parsePositiveInteger,
    }));
}

function buildWorkspaceShareState(values = getWorkspaceFormValues()) {
  return {
    link: buildWorkspaceUrl(values, state.viewMode),
    summary: `${values.schoolName} · 반경 ${(values.radiusMeters / 1000).toFixed(1)}km · 공유 링크 준비 완료`,
  };
}

function fillWorkspaceForm(values) {
  const normalized = normalizeWorkspaceValuesUseCase(values, {
    fallbackConfig: EFFECTIVE_CONFIG,
    parseFiniteNumber,
    parsePositiveInteger,
  });
  elements.workspaceSchoolNameField.value = normalized.schoolName;
  elements.workspaceLatField.value = String(normalized.lat);
  elements.workspaceLngField.value = String(normalized.lng);
  elements.workspaceRadiusField.value = String(normalized.radiusMeters);
  elements.workspaceTopicField.value = normalized.topic;
}

function applyWorkspaceSearchResult(result, { requireConfirm = true } = {}) {
  if (requireConfirm && !confirmReferenceLock(result.name)) {
    setNotice("위치 고정을 취소했습니다. 다른 검색 결과를 선택하거나 지도를 이동한 뒤 다시 시도하세요.", "info");
    return false;
  }

  elements.locationSearchField.value = result.name;
  elements.workspaceSchoolNameField.value = result.name;
  elements.workspaceLatField.value = String(result.lat);
  elements.workspaceLngField.value = String(result.lng);
  syncReferenceStateFromWorkspaceForm();
  setReferenceLocked(true);
  rebuildExampleLayers(state.referenceLocation);
  state.workspaceSearchResults = [];
  resetWorkspaceRegionCache();
  renderAll();
  mapWorkspace.map.flyTo([result.lat, result.lng], Math.max(mapWorkspace.map.getZoom(), 15), {
    duration: 0.7,
  });
  void workspaceRegionController.ensureWorkspaceRegionInfo().catch((error) => {
    console.warn("Failed to prefetch workspace region.", error);
  });
  return true;
}

async function copyText(text) {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text);
    return;
  }

  const field = document.createElement("textarea");
  field.value = text;
  document.body.append(field);
  field.select();
  document.execCommand("copy");
  field.remove();
}

function initializeWorkspaceForm() {
  elements.workspacePresetField.innerHTML = [
    `<option value="">직접 입력</option>`,
    ...EFFECTIVE_CONFIG.workspacePresets.map(
      (preset) =>
        `<option value="${escapeHtml(preset.id)}">${escapeHtml(preset.label)}</option>`,
    ),
  ].join("");

  fillWorkspaceForm({
    schoolName: EFFECTIVE_CONFIG.schoolName,
    lat: EFFECTIVE_CONFIG.mapCenter.lat,
    lng: EFFECTIVE_CONFIG.mapCenter.lng,
    radiusMeters: EFFECTIVE_CONFIG.schoolRadiusMeters,
    topic: EFFECTIVE_CONFIG.workspaceTopic,
  });
  elements.locationSearchField.value = EFFECTIVE_CONFIG.schoolName;
  syncReferenceStateFromWorkspaceForm();
}

function buildWorkspacePanelViewModel() {
  return buildWorkspacePanelViewModelUseCase({
    values: getWorkspaceFormValues(),
    viewMode: state.viewMode,
    searchPending: state.workspaceSearchPending,
    searchResults: state.workspaceSearchResults,
    buildUrl: buildWorkspaceUrl,
  });
}

function renderWorkspacePanel() {
  renderWorkspacePanelView({
    elements,
    viewModel: buildWorkspacePanelViewModel(),
    escapeHtml,
  });
}

function handleWorkspacePresetChange(presetId) {
  const preset = EFFECTIVE_CONFIG.workspacePresets.find((item) => item.id === presetId);
  if (!preset) {
    renderWorkspacePanel();
    return;
  }

  if (!confirmReferenceLock(preset.label ?? preset.schoolName ?? "선택한 위치")) {
    setNotice("위치 고정을 취소했습니다.", "info");
    renderWorkspacePanel();
    return;
  }

  fillWorkspaceForm(preset);
  syncReferenceStateFromWorkspaceForm();
  setReferenceLocked(true);
  rebuildExampleLayers(state.referenceLocation);
  resetWorkspaceRegionCache();
  renderAll();
  mapWorkspace.map.flyTo([preset.lat, preset.lng], Math.max(mapWorkspace.map.getZoom(), 14), {
    duration: 0.6,
  });
  void workspaceRegionController.ensureWorkspaceRegionInfo().catch((error) => {
    console.warn("Failed to prefetch workspace region.", error);
  });
}

async function handleWorkspaceSearch() {
  const query = elements.locationSearchField.value.trim();
  if (!query) {
    setNotice("학교나 장소 이름을 먼저 입력해 주세요.", "warn");
    return;
  }

  elements.workspaceSchoolNameField.value = query;

  try {
    state.workspaceSearchPending = true;
    renderWorkspacePanel();
    const results = await searchWorkspaceLocations(query);
    state.workspaceSearchResults = results;
    renderWorkspacePanel();

    if (!results.length) {
      setNotice("검색 결과가 없습니다. 학교명이나 지역명을 조금 더 길게 입력해 주세요.", "warn");
      return;
    }

    if (results.length === 1 && results[0].type === "map-center") {
      setNotice("정확한 검색 결과가 없어 현재 지도 중심을 위치로 고정하는 선택지를 표시했습니다. 지도를 먼저 맞춘 뒤 선택하세요.", "warn");
      return;
    }

    if (results.length === 1) {
      if (applyWorkspaceSearchResult(results[0])) {
        setNotice(`${results[0].name} 위치를 탐색 중심으로 설정했습니다.`, "success");
      }
      return;
    }

    const previewCoordinates = results.map((item) => [item.lat, item.lng]);
    mapWorkspace.fitCoordinates(previewCoordinates);
    setNotice("검색 결과를 찾았습니다. 아래 목록에서 위치를 선택해 주세요.", "info");
  } catch (error) {
    console.error(error);
    state.workspaceSearchResults = [];
    renderWorkspacePanel();
    setNotice("장소 검색에 실패했습니다. 현재는 지도 중심 사용만 가능합니다.", "error");
  } finally {
    state.workspaceSearchPending = false;
    renderWorkspacePanel();
  }
}

function handleWorkspaceSearchResultPick(resultId) {
  const result = state.workspaceSearchResults.find((item) => item.id === resultId);
  if (!result) {
    return;
  }

  if (applyWorkspaceSearchResult(result)) {
    setNotice(`${result.name} 위치를 탐색 중심으로 설정했습니다.`, "success");
  }
}

function handleWorkspaceFieldSync({ unlockReference = true } = {}) {
  syncReferenceStateFromWorkspaceForm();
  if (unlockReference) {
    setReferenceLocked(false);
    resetWorkspaceRegionCache();
  }
  rebuildExampleLayers(state.referenceLocation);
  renderAll();
}

function handleUseMapCenter() {
  const center = mapWorkspace.map.getCenter();
  if (!confirmReferenceLock("현재 지도 중심")) {
    setNotice("지도 중심 고정을 취소했습니다.", "info");
    return;
  }

  elements.workspaceSchoolNameField.value = "현재 지도 중심";
  elements.workspaceLatField.value = center.lat.toFixed(6);
  elements.workspaceLngField.value = center.lng.toFixed(6);
  syncReferenceStateFromWorkspaceForm();
  setReferenceLocked(true);
  rebuildExampleLayers(state.referenceLocation);
  resetWorkspaceRegionCache();
  renderAll();
  void workspaceRegionController.ensureWorkspaceRegionInfo().catch((error) => {
    console.warn("Failed to prefetch workspace region.", error);
  });
  setNotice("현재 지도 중심을 탐색 기준으로 설정했습니다.", "success");
}

function handleWorkspaceSubmit() {
  window.location.assign(buildWorkspaceUrl(getWorkspaceFormValues(), state.viewMode));
}

async function handleCopyWorkspaceLink() {
  try {
    await copyText(buildWorkspaceShareState().link);
    setNotice("현재 작업공간 링크를 복사했습니다.", "success");
  } catch (error) {
    console.error(error);
    setNotice("워크스페이스 링크를 복사하지 못했습니다.", "error");
  }
}

function handleResetWorkspace() {
  const url = new URL(window.location.href);
  ["school", "lat", "lng", "radius", "topic", "view"].forEach((key) => {
    url.searchParams.delete(key);
  });
  window.location.assign(url.toString());
}

function buildCurrentWorkspaceProjectSnapshot(projectName) {
  const normalizedProjectName = projectName.trim() || getCurrentProjectNameSuggestion();
  const existingProject = state.savedProjects.find((project) => project.name === normalizedProjectName);
  return buildWorkspaceProjectSnapshot({
    idFactory: createId,
    name: normalizedProjectName,
    workspaceValues: getWorkspaceFormValues(),
    viewMode: state.viewMode,
    baseMapMode: state.baseMapMode,
    mapOverlayLayerIds: state.mapOverlayLayerIds,
    showSchoolReference: state.showSchoolReference,
    localPublicVisibility: state.localPublicVisibility,
    localPublicOpacity: state.localPublicOpacity,
    importedPublicLayers: state.importedPublicLayers,
    studentLayers: state.studentLayers,
    reflectionNote: state.reflectionNote,
    sgisControls: getCurrentSgisControlValues(),
    activeLayerId: state.activeLayerId,
    existingProjectId: existingProject?.id ?? null,
  });
}

function applyWorkspaceProject(project) {
  fillWorkspaceForm(project.workspaceValues);
  elements.locationSearchField.value = project.workspaceValues.schoolName;
  elements.projectNameField.value = project.name;

  state.viewMode = project.viewMode;
  state.activeSidebarPanel = "student";
  state.baseMapMode = project.baseMapMode;
  state.mapOverlayLayerIds = [...project.mapOverlayLayerIds];
  state.showSchoolReference = project.showSchoolReference;

  syncReferenceStateFromWorkspaceForm();
  setReferenceLocked(true);
  rebuildExampleLayers(state.referenceLocation);
  state.localPublicVisibility = { ...project.localPublicVisibility };
  state.localPublicOpacity = { ...project.localPublicOpacity };
  setImportedPublicLayers(project.importedPublicLayers);
  setStudentLayers(project.studentLayers);
  state.activeLayerId = project.activeLayerId;
  state.activeTool = "select";
  state.selectedFeatureRef = null;
  clearMeasurementResult();
  clearDraftGeometry();
  setReflectionNote(project.reflectionNote, { persist: true });
  resetWorkspaceRegionCache();

  if (project.sgisControls.metricId) {
    elements.sgisMetricField.value = project.sgisControls.metricId;
  }
  if (project.sgisControls.year) {
    elements.sgisYearField.value = String(project.sgisControls.year);
  }
  if (project.sgisControls.color) {
    elements.sgisColorField.value = project.sgisControls.color;
  }

  syncStudentEditingState();
  syncUrlState();
  renderAll();
  mapWorkspace.map.flyTo(
    [project.workspaceValues.lat, project.workspaceValues.lng],
    Math.max(mapWorkspace.map.getZoom(), project.viewMode === "korea" ? 10 : 15),
    { duration: 0.6 },
  );
  void workspaceRegionController.ensureWorkspaceRegionInfo().catch((error) => {
    console.warn("Failed to restore workspace region.", error);
  });
}

function saveCurrentWorkspaceProject(projectName) {
  const nextProject = buildCurrentWorkspaceProjectSnapshot(projectName);
  setSavedProjects(upsertWorkspaceProject(state.savedProjects, nextProject));
  state.selectedProjectId = nextProject.id;
  elements.projectNameField.value = nextProject.name;
  renderStudentPanel();
  setNotice(`${nextProject.name} 프로젝트를 저장했습니다.`, "success");
}

function exportCurrentWorkspaceProject(projectName) {
  const project = buildCurrentWorkspaceProjectSnapshot(projectName);
  downloadJson(`${project.name.replace(/[\\/:*?"<>|]+/g, "-")}.webgis-project.json`, {
    schema: "student-webgis-project-v1",
    exportedAt: new Date().toISOString(),
    project,
  });
  setNotice(`${project.name} 프로젝트 파일을 저장했습니다.`, "success");
}

async function importWorkspaceProjectFile(file) {
  try {
    const payload = JSON.parse(await file.text());
    const rawProject = payload?.project ?? payload;
    const project = normalizeWorkspaceProject(rawProject, {
      normalizeWorkspaceValues: normalizeWorkspaceValuesUseCase,
      fallbackConfig: EFFECTIVE_CONFIG,
      parseFiniteNumber,
      parsePositiveInteger,
      localPublicLayers,
    });
    if (!project.id) {
      throw new Error("프로젝트 파일 형식이 올바르지 않습니다.");
    }

    setSavedProjects(upsertWorkspaceProject(state.savedProjects, project));
    state.selectedProjectId = project.id;
    applyWorkspaceProject(project);
    setNotice(`${project.name} 프로젝트 파일을 불러왔습니다.`, "success");
  } catch (error) {
    console.error(error);
    setNotice(error.message || "프로젝트 파일을 불러오지 못했습니다.", "error");
  }
}

function loadSavedWorkspaceProject(projectId) {
  const project = state.savedProjects.find((item) => item.id === projectId);
  if (!project) {
    setNotice("불러올 프로젝트를 먼저 선택해 주세요.", "warn");
    return;
  }

  state.selectedProjectId = project.id;
  applyWorkspaceProject(project);
  setNotice(`${project.name} 프로젝트를 불러왔습니다.`, "success");
}

function deleteSavedWorkspaceProject(projectId) {
  const project = state.savedProjects.find((item) => item.id === projectId);
  if (!project) {
    setNotice("삭제할 프로젝트를 먼저 선택해 주세요.", "warn");
    return;
  }

  if (!window.confirm(`"${project.name}" 프로젝트를 삭제할까요?`)) {
    return;
  }

  setSavedProjects(removeWorkspaceProject(state.savedProjects, project.id));
  renderStudentPanel();
  setNotice(`${project.name} 프로젝트를 삭제했습니다.`, "success");
}

function getVisibleMapCoordinates() {
  const coordinates = [];

  if (state.showSchoolReference) {
    coordinates.push([state.referenceLocation.lat, state.referenceLocation.lng]);
  }
  localPublicLayers
    .filter((layer) => state.localPublicVisibility[layer.id])
    .forEach((layer) => {
      layer.items.forEach((item) => coordinates.push([item.lat, item.lng]));
    });

  getVisibleImportedPublicLayers().forEach((layer) => {
    collectFeatureCollectionCoordinates(layer.featureCollection).forEach((coordinate) =>
      coordinates.push(coordinate),
    );
  });
  getVisibleStudentLayers().forEach((layer) => {
    getStudentLayerCoordinates(layer).forEach((coordinate) => coordinates.push(coordinate));
  });

  return coordinates;
}

function buildVisibleWorkspaceGeoJson() {
  const features = [];

  getVisibleImportedPublicLayers().forEach((layer) => {
    layer.featureCollection.features.forEach((feature) => {
      features.push({
        ...feature,
        properties: {
          ...(feature.properties ?? {}),
          sourceGroup: "public-imported",
          layerId: layer.id,
          layerName: layer.name,
        },
      });
    });
  });

  getVisibleStudentLayers().forEach((layer) => {
    buildStudentLayerFeatureCollection(layer).features.forEach((feature) => {
      features.push({
        ...feature,
        properties: {
          ...feature.properties,
          sourceGroup: "student",
        },
      });
    });
  });

  localPublicLayers
    .filter((layer) => state.localPublicVisibility[layer.id])
    .forEach((layer) => {
      layer.items.forEach((item) => {
        features.push({
          type: "Feature",
          geometry: { type: "Point", coordinates: [item.lng, item.lat] },
          properties: {
            sourceGroup: "public",
            layerId: layer.id,
            layerName: layer.label,
            name: item.name,
            itemType: item.type,
            note: item.note,
          },
        });
      });
    });

  return {
    type: "FeatureCollection",
    features,
  };
}

function downloadGeoJson(filename, payload) {
  const blob = new Blob([JSON.stringify(payload, null, 2)], {
    type: "application/geo+json",
  });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

function downloadJson(filename, payload) {
  const blob = new Blob([JSON.stringify(payload, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

function renderHero() {
  const locationLabel = getCurrentLocationLabel();
  const lockLabel = state.referenceLocked ? "위치 고정됨" : "위치 미고정";
  const workspaceHint = state.referenceLocked
    ? "기준 위치가 고정되어 있습니다. 공공 통계 레이어를 불러오거나 학생 레이어를 지도 위에 직접 그리세요."
    : EFFECTIVE_CONFIG.kakao.javascriptKey
      ? "장소를 검색한 뒤 확인창에서 위치를 고정해야 SGIS 통계 레이어를 불러올 수 있습니다."
      : "현재는 기본 지도로 실행 중이며, Kakao JavaScript 키를 넣으면 학교/장소 검색 품질이 더 좋아집니다.";
  elements.heroTitle.textContent = "내 지역 통계지도 만들기";
  elements.heroSubtitle.textContent = "카카오 지도 위에 SGIS 통계 레이어와 내가 만든 점·선·면 레이어를 겹쳐 분석합니다.";
  elements.scopePill.textContent = `${lockLabel} · ${locationLabel} · 반경 ${(state.referenceRadiusMeters / 1000).toFixed(1)}km`;
  elements.scopePill.dataset.locked = state.referenceLocked ? "true" : "false";
  elements.topicPill.textContent = `공공 레이어 ${getActivePublicLayerCount()}개`;
  elements.studentLayerPill.textContent = `학생 레이어 ${state.studentLayers.length}개`;
  elements.storageModePill.textContent = "로컬 저장";
  elements.workspaceHint.textContent = workspaceHint;
  elements.mapTitle.textContent = "Kakao GIS 레이어 캔버스";
  elements.focusPrimaryButton.textContent = "탐색 중심으로 돌아가기";
  elements.baseMapModeField.value = state.baseMapMode;
  elements.locateMeButton.textContent = state.geolocationPending ? "위치 확인 중..." : "현재 위치";
  elements.locateMeButton.disabled = state.geolocationPending;
  if (elements.mapOverlayFilterList) {
    elements.mapOverlayFilterList.innerHTML = MAP_OVERLAY_OPTIONS.map(
      (option) => `
        <button
          type="button"
          class="filter-chip ${state.mapOverlayLayerIds.includes(option.id) ? "is-active" : ""}"
          data-overlay-id="${escapeHtml(option.id)}"
        >
          ${escapeHtml(option.label)}
        </button>
      `,
    ).join("");
  }
}

function renderModeToggle() {
  elements.viewModeToggle.querySelectorAll("[data-view-mode]").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.viewMode === state.viewMode);
  });
}

function renderSidebarPanels() {
  const activePanel = state.activeSidebarPanel || resolveDefaultSidebarPanel();
  elements.sidebarPanelTabs.querySelectorAll("[data-sidebar-panel]").forEach((button) => {
    const isActive = button.dataset.sidebarPanel === activePanel;
    button.classList.toggle("is-active", isActive);
    button.setAttribute("aria-selected", String(isActive));
  });

  elements.workspaceCard.hidden = true;
  elements.statsCard.hidden = true;
  elements.publicCard.hidden = activePanel !== "public";
  elements.studentCard.hidden = activePanel !== "student";
  elements.analysisCard.hidden = activePanel !== "analysis";
  elements.layerStackCard.hidden = activePanel !== "layers";
  elements.mobilePanelTitle.textContent = getSidebarPanelLabel(activePanel);
  renderMobileToolsSheet();
}

function renderMobileToolsSheet() {
  const isMobileViewport = window.innerWidth <= 760;
  const isOpen = isMobileViewport && state.isMobileToolsOpen;
  elements.sidebar.classList.toggle("is-mobile-open", isOpen);
  elements.mobileToolsButton.hidden = !isMobileViewport || isOpen;
  elements.mobileSheetBackdrop.hidden = !isOpen;
  elements.mobileToolsButton.textContent = `${getSidebarPanelLabel()} 열기`;
  elements.mobileToolsButton.setAttribute("aria-expanded", String(isOpen));
  document.body.classList.toggle("sidebar-sheet-open", isOpen);
}

function renderStats() {
  elements.activePublicCount.textContent = String(getActivePublicLayerCount());
  elements.studentLayerCount.textContent = String(state.studentLayers.length);
  elements.studentPointCount.textContent = String(getVisibleStudentFeatureCount());
  elements.scopeLabel.textContent = getCurrentLocationLabel();
}

function renderLayerStackSummary() {
  if (!elements.layerStackSummary) {
    return;
  }

  const visibleImportedCount = getVisibleImportedPublicLayers().length;
  const visibleStudentCount = getVisibleStudentLayers().length;
  const visibleExampleCount = localPublicLayers.filter((layer) => state.localPublicVisibility[layer.id]).length;
  const activeLayer = getActiveStudentLayer();

  elements.layerStackSummary.textContent = [
    `표시 중인 공공 ${visibleImportedCount + visibleExampleCount + Number(state.showSchoolReference)}개`,
    `학생 레이어 ${visibleStudentCount}개`,
    activeLayer ? `그리기 대상: ${activeLayer.name}` : "그리기 대상 레이어 없음",
  ].join(" · ");
}

function renderPublicPanel() {
  renderPublicPanelView({
    elements,
    viewModel: buildPublicPanelViewModelUseCase({
      state,
      elements,
      config: EFFECTIVE_CONFIG,
      localPublicLayers,
      regionProfiles: SGIS_REGION_LAYER_PROFILES,
      defaultRecommendationIds: DEFAULT_SGIS_RECOMMENDATION_IDS,
      getCurrentLocationLabel,
      getCurrentSgisProfile: getCurrentSgisProfileUseCase,
      getCurrentSgisMetricLabel: getCurrentSgisMetricLabelUseCase,
      getSgisMetricRecommendation,
      buildRegionSgisSummary,
      getLayerScopeLabel: getLayerScopeLabelUseCase,
      getImportedPublicSourceLabel: getImportedPublicSourceLabelUseCase,
    }),
    escapeHtml,
  });
}

function renderStudentPanel() {
  renderStudentPanelView({
    elements,
    studentLayers: state.studentLayers,
    activeLayer: getActiveStudentLayer(),
    activeTool: state.activeTool,
    draftGeometry: state.draftGeometry,
    selectedFeatureRecord: getSelectedStudentFeatureRecord(),
    selectedFeatureMeasurement: getSelectedFeatureMeasurementSummary(),
    getDraftStatus: getStudentDraftStatus,
    getStudentLayerGeometryLabel,
    escapeHtml,
    reflectionNote: state.reflectionNote,
    workspaceSummary: getStudentWorkspaceSummary(),
    measurementResult: state.measurementResult,
    savedProjectView: getWorkspaceProjectView(),
    suggestedProjectName: getCurrentProjectNameSuggestion(),
  });
}

function renderStudentDrawToolbar() {
  const shouldShowToolbar = state.isDrawingToolsOpen || Boolean(state.draftGeometry);
  elements.drawToolbar.hidden = !shouldShowToolbar;
  elements.drawToolbarHint.hidden = !shouldShowToolbar;

  renderDrawToolbar({
    elements,
    studentLayers: state.studentLayers,
    activeLayerId: state.activeLayerId,
    activeTool: state.activeTool,
    draftGeometry: state.draftGeometry,
    canCompleteDraft: canCompleteDraftGeometry(state.draftGeometry),
    escapeHtml,
  });
}

function buildLayerHubFeatureRows(layer) {
  if (!layer.features?.length) {
    return "";
  }

  const rows = layer.features.slice(0, 4).map((feature, index) => {
    const title = feature.title?.trim() || `${getStudentGeometryLabel(feature.geometryType)} 객체 ${index + 1}`;
    const properties = feature.properties ?? {};
    const observedLabel = String(properties.observedLabel ?? "").trim();
    const observedValue = String(properties.observedValue ?? "").trim();
    const observedUnit = String(properties.observedUnit ?? "").trim();
    const observedText = [observedLabel, [observedValue, observedUnit].filter(Boolean).join(" ")]
      .filter(Boolean)
      .join(": ");
    const featureMeta = [
      getStudentGeometryLabel(feature.geometryType),
      observedText || feature.note || "내용 없음",
    ].filter(Boolean).join(" · ");
    return `
      <div class="layer-hub-feature-row">
        <button type="button" class="layer-hub-feature-select" data-layer-hub-action="select-student-feature" data-layer-id="${escapeHtml(layer.id)}" data-feature-id="${escapeHtml(feature.id)}">
          <span>${escapeHtml(title)}</span>
          <small>${escapeHtml(featureMeta)}</small>
        </button>
        <button type="button" class="ghost-button compact-button danger-button" data-layer-hub-action="delete-student-feature" data-layer-id="${escapeHtml(layer.id)}" data-feature-id="${escapeHtml(feature.id)}">
          객체 삭제
        </button>
      </div>
    `;
  });
  const extraCount = layer.features.length - rows.length;

  return `
    <div class="layer-hub-feature-list">
      ${rows.join("")}
      ${extraCount > 0 ? `<small>외 ${extraCount}개 객체는 전체 관리에서 확인</small>` : ""}
    </div>
  `;
}

function buildLayerHubRow({ type, layer }) {
  const isPublic = type === "public";
  const featureCount = isPublic
    ? layer.featureCollection?.features?.length ?? 0
    : layer.features?.length ?? 0;
  const sourceLabel = isPublic
    ? layer.sourceKind === "analysis"
      ? layer.analysisType === "suitability"
        ? "입지점수 분석"
        : "분석 레이어"
      : "공공 통계"
    : "학생 조사";
  const primaryAction = isPublic ? "toggle-imported-public" : "toggle-student-layer";
  const focusAction = isPublic ? "focus-imported-public" : "focus-student-layer";
  const deleteAction = isPublic ? "delete-imported-public" : "delete-student-layer";
  const activateAction = isPublic ? "" : "activate-student-layer";
  const activeLabel = !isPublic && state.activeLayerId === layer.id ? "그리기 대상" : "";

  return `
    <article class="layer-hub-row ${layer.visible ? "is-visible" : "is-hidden"}">
      <span class="layer-dot" style="--swatch:${escapeHtml(layer.color)}"></span>
      <div class="layer-hub-copy">
        <strong>${escapeHtml(layer.name)}</strong>
        <small>${escapeHtml(sourceLabel)} · ${Number(featureCount).toLocaleString("ko-KR")}개 객체 · ${layer.visible ? "켜짐" : "꺼짐"}${activeLabel ? ` · ${activeLabel}` : ""}</small>
      </div>
      <div class="layer-hub-actions">
        ${activateAction
          ? `<button type="button" class="ghost-button compact-button" data-layer-hub-action="${activateAction}" data-layer-id="${escapeHtml(layer.id)}">그리기</button>`
          : ""}
        <button type="button" class="ghost-button compact-button" data-layer-hub-action="${primaryAction}" data-layer-id="${escapeHtml(layer.id)}">
          ${layer.visible ? "끄기" : "켜기"}
        </button>
        <button type="button" class="ghost-button compact-button" data-layer-hub-action="${focusAction}" data-layer-id="${escapeHtml(layer.id)}">
          보기
        </button>
        <button type="button" class="ghost-button compact-button danger-button" data-layer-hub-action="${deleteAction}" data-layer-id="${escapeHtml(layer.id)}">
          삭제
        </button>
      </div>
      ${isPublic ? "" : buildLayerHubFeatureRows(layer)}
    </article>
  `;
}

function renderMapLayerHub() {
  if (!elements.mapLayerHub) {
    return;
  }

  const importedCount = state.importedPublicLayers.length;
  const studentCount = state.studentLayers.length;
  const visibleImportedCount = getVisibleImportedPublicLayers().length;
  const visibleStudentCount = getVisibleStudentLayers().length;
  const rows = [
    ...state.importedPublicLayers.map((layer) => buildLayerHubRow({ type: "public", layer })),
    ...state.studentLayers.map((layer) => buildLayerHubRow({ type: "student", layer })),
  ];

  elements.mapLayerHub.innerHTML = `
    <div class="layer-hub-head">
      <div>
        <p class="eyebrow">Layer Hub</p>
        <h3>현재 지도 레이어</h3>
        <p>공공 ${visibleImportedCount}/${importedCount}개 · 학생 ${visibleStudentCount}/${studentCount}개 표시 중</p>
      </div>
      <div class="layer-hub-shortcuts">
        <button type="button" class="ghost-button compact-button" data-layer-hub-action="open-public-tools">공공 추가</button>
        <button type="button" class="ghost-button compact-button" data-layer-hub-action="open-student-tools">그리기</button>
        <button type="button" class="ghost-button compact-button" data-layer-hub-action="open-layer-tools">전체 관리</button>
      </div>
    </div>
    ${rows.length
      ? `<div class="layer-hub-list">${rows.join("")}</div>`
      : `<div class="layer-hub-empty">아직 직접 추가한 레이어가 없습니다. 공공 통계를 불러오거나 학생 레이어를 만들어 지도 위에 그리세요.</div>`}
  `;
}

function openSidebarPanel(panelId) {
  state.activeSidebarPanel = panelId;
  renderSidebarPanels();
  if (window.innerWidth <= 760) {
    setMobileToolsOpen(true);
  }
}

function handleLayerHubAction({ action, layerId, featureId }) {
  if (action === "open-public-tools") {
    openSidebarPanel("public");
    return;
  }

  if (action === "open-student-tools") {
    openSidebarPanel("student");
    return;
  }

  if (action === "open-layer-tools") {
    openSidebarPanel("layers");
    return;
  }

  if (
    action === "toggle-imported-public"
    || action === "focus-imported-public"
    || action === "delete-imported-public"
  ) {
    publicWorkspaceController?.handleImportedLayerAction({ action, layerId });
    return;
  }

  if (
    action === "toggle-student-layer"
    || action === "focus-student-layer"
    || action === "delete-student-layer"
    || action === "activate-student-layer"
    || action === "select-student-feature"
    || action === "delete-student-feature"
  ) {
    studentWorkspaceController?.handleStudentLayerAction(action, layerId, undefined, featureId);
  }
}

function buildLegendControl({
  markerHtml,
  label,
  subLabel = "",
  action,
  deleteAction = "",
  layerId = "",
  featureId = "",
  deleteLabel = "삭제",
}) {
  const data = [
    layerId ? `data-layer-id="${escapeHtml(layerId)}"` : "",
    featureId ? `data-feature-id="${escapeHtml(featureId)}"` : "",
  ].filter(Boolean).join(" ");

  return `
    <span class="legend-item legend-control">
      <button
        type="button"
        class="legend-main-button"
        data-legend-action="${escapeHtml(action)}"
        ${data}
      >
        ${markerHtml}
        <span class="legend-labels">
          <strong>${escapeHtml(label)}</strong>
          ${subLabel ? `<small>${escapeHtml(subLabel)}</small>` : ""}
        </span>
      </button>
      ${deleteAction
        ? `<button
            type="button"
            class="legend-delete-button"
            data-legend-action="${escapeHtml(deleteAction)}"
            ${data}
            aria-label="${escapeHtml(`${label} ${deleteLabel}`)}"
          >${escapeHtml(deleteLabel)}</button>`
        : ""}
    </span>
  `;
}

function getFeatureLegendTitle(layer, feature, index) {
  const geometryLabel = getStudentGeometryLabel(feature.geometryType);
  return feature.title?.trim() || `${layer.name} ${geometryLabel} ${index + 1}`;
}

function renderLegend() {
  const items = [];
  if (state.showSchoolReference) {
    items.push(buildLegendControl({
      markerHtml: `<span class="legend-ring"></span>`,
      label: "탐색 기준 반경",
      subLabel: "지도에서 숨기기",
      action: "hide-school-reference",
      deleteLabel: "숨김",
    }));
  }
  localPublicLayers
    .filter((layer) => state.localPublicVisibility[layer.id])
    .forEach((layer) => {
      items.push(buildLegendControl({
        markerHtml: `<span class="legend-dot" style="--swatch:${escapeHtml(layer.color)}"></span>`,
        label: layer.label,
        subLabel: "예시 레이어 · 지도에서 숨기기",
        action: "hide-local-public",
        layerId: layer.id,
        deleteLabel: "숨김",
      }));
    });
  getVisibleImportedPublicLayers().forEach((layer) => {
    const markerClass = layer.sourceKind === "analysis" ? "legend-analysis" : "legend-dot";
    const label = layer.sourceKind === "analysis"
      ? `${layer.name} (분석)`
      : layer.name;
    items.push(buildLegendControl({
      markerHtml: `<span class="${markerClass}" style="--swatch:${escapeHtml(layer.color)}"></span>`,
      label,
      subLabel: `${layer.featureCollection.features.length}개 객체 · 범위 보기`,
      action: "focus-imported-public",
      deleteAction: "delete-imported-public",
      layerId: layer.id,
    }));
  });
  getVisibleStudentLayers().forEach((layer) => {
    items.push(buildLegendControl({
      markerHtml: `<span class="legend-square" style="--swatch:${escapeHtml(layer.color)}"></span>`,
      label: layer.name,
      subLabel: `${layer.features.length}개 객체 · 이 레이어에 그리기`,
      action: "activate-student-layer",
      deleteAction: "delete-student-layer",
      layerId: layer.id,
      deleteLabel: "레이어 삭제",
    }));

    layer.features.forEach((feature, index) => {
      const isSelected = state.selectedFeatureRef?.layerId === layer.id
        && state.selectedFeatureRef?.featureId === feature.id;
      items.push(buildLegendControl({
        markerHtml: `<span class="legend-feature-marker ${isSelected ? "is-selected" : ""}" style="--swatch:${escapeHtml(layer.color)}">${escapeHtml(getStudentGeometryLabel(feature.geometryType).slice(0, 1))}</span>`,
        label: getFeatureLegendTitle(layer, feature, index),
        subLabel: `${layer.name} 객체 · 선택`,
        action: "select-student-feature",
        deleteAction: "delete-student-feature",
        layerId: layer.id,
        featureId: feature.id,
        deleteLabel: "객체 삭제",
      }));
    });
  });
  elements.legend.innerHTML = items.length
    ? items.join("")
    : `<span class="legend-empty">현재 지도에 표시 중인 레이어가 없습니다.</span>`;
}

function handleLegendAction({ action, layerId, featureId }) {
  if (action === "hide-school-reference") {
    state.showSchoolReference = false;
    renderAll();
    setNotice("탐색 기준 반경을 숨겼습니다.", "info");
    return;
  }

  if (action === "hide-local-public") {
    const layer = localPublicLayers.find((item) => item.id === layerId);
    if (!layer) {
      return;
    }
    state.localPublicVisibility[layer.id] = false;
    renderAll();
    setNotice(`${layer.label} 예시 레이어를 숨겼습니다.`, "info");
    return;
  }

  if (action === "focus-imported-public" || action === "delete-imported-public") {
    const layer = state.importedPublicLayers.find((item) => item.id === layerId);
    if (!layer) {
      return;
    }

    if (action === "focus-imported-public") {
      mapWorkspace.fitCoordinates(collectFeatureCollectionCoordinates(layer.featureCollection));
      setNotice(`${layer.name} 레이어 범위로 이동했습니다.`, "info");
      return;
    }

    if (!window.confirm(`"${layer.name}" 레이어를 삭제할까요?`)) {
      return;
    }
    setImportedPublicLayers(state.importedPublicLayers.filter((item) => item.id !== layer.id));
    renderAll();
    setNotice(`${layer.name} 레이어를 삭제했습니다.`, "success");
    return;
  }

  if (action === "activate-student-layer" || action === "delete-student-layer") {
    const layer = state.studentLayers.find((item) => item.id === layerId);
    if (!layer) {
      return;
    }

    if (action === "activate-student-layer") {
      setActiveStudentLayer(layer.id);
      state.activeTool = "select";
      renderAll();
      setNotice(`${layer.name} 레이어를 선택했습니다.`, "info");
      return;
    }

    if (!window.confirm(`"${layer.name}" 학생 레이어를 삭제할까요?`)) {
      return;
    }
    setStudentLayers(state.studentLayers.filter((item) => item.id !== layer.id));
    clearDraftGeometry();
    renderAll();
    setNotice(`${layer.name} 학생 레이어를 삭제했습니다.`, "success");
    return;
  }

  if (action === "select-student-feature" || action === "delete-student-feature") {
    const selectedFeatureRecord = findSelectedStudentFeature(
      state.studentLayers,
      createSelectedFeatureRef(layerId, featureId),
    );
    if (!selectedFeatureRecord) {
      return;
    }

    if (action === "select-student-feature") {
      state.activeTool = "select";
      selectStudentFeature(selectedFeatureRecord.layer.id, selectedFeatureRecord.feature.id);
      renderAll();
      setNotice("객체를 선택했습니다.", "info");
      return;
    }

    const title = selectedFeatureRecord.feature.title?.trim()
      || getStudentGeometryLabel(selectedFeatureRecord.feature.geometryType);
    if (!window.confirm(`"${title}" 객체를 삭제할까요?`)) {
      return;
    }

    setStudentLayers(
      removeStudentFeature(
        state.studentLayers,
        selectedFeatureRecord.layer.id,
        selectedFeatureRecord.feature.id,
      ),
    );
    state.selectedFeatureRef = null;
    clearDraftGeometry();
    renderAll();
    setNotice("객체를 삭제했습니다.", "success");
  }
}

function renderStatusNotice() {
  let message = state.noticeMessage;
  let tone = state.noticeTone;
  const activeLayer = getActiveStudentLayer();
  if (!message) {
    if (state.draftGeometry && activeLayer) {
      message = `${activeLayer.name} 레이어에 ${getStudentGeometryLabel(state.draftGeometry.geometryType)} 도형을 그리는 중입니다.`;
    } else if (activeLayer) {
      message = `${activeLayer.name} 레이어를 선택한 상태입니다. 지도 도구로 객체를 추가해 보세요.`;
    } else {
      message = "위치를 검색하고, SGIS 통계를 켠 뒤, 학생 레이어를 점·선·면으로 직접 그려 보세요.";
    }
    tone = "info";
  }
  elements.statusNotice.textContent = message;
  elements.statusNotice.dataset.tone = tone;
}

function renderAll() {
  renderWorkspacePanel();
  renderHero();
  renderModeToggle();
  renderSidebarPanels();
  renderStats();
  renderLayerStackSummary();
  renderPublicPanel();
  renderStudentPanel();
  renderSuitabilityPanel();
  renderLayerAddSheet();
  renderStudentDrawToolbar();
  renderMapLayerHub();
  renderLegend();
  renderStatusNotice();
  mapWorkspace.setBaseMapMode?.(state.baseMapMode);
  mapWorkspace.setOverlayLayerIds?.(state.mapOverlayLayerIds);
  mapWorkspace.render(state);
}

async function importLayerFile(file) {
  const text = await file.text();
  const name = file.name.replace(/\.[^.]+$/, "");
  const color = getRandomLayerColor(state.studentLayers.length);
  const features = file.name.toLowerCase().endsWith(".csv")
    ? parseCsvText(text)
    : parseGeoJsonText(text, name);
  const cleanFeatures = features
    .map((feature) =>
      normalizeStudentLayer({
        id: createId("student-import"),
        geometryType: "mixed",
        features: [feature],
      }).features[0])
    .filter(Boolean);
  if (!cleanFeatures.length) {
    throw new Error("현재 파일에서 불러올 수 있는 학생 도형이 없습니다.");
  }
  const layer = normalizeStudentLayer({
    id: createId("student-layer"),
    name,
    geometryType: "mixed",
    color,
    description: `파일 업로드: ${file.name}`,
    visible: true,
    source: "imported",
    features: cleanFeatures,
  });
  setStudentLayers([layer, ...state.studentLayers]);
  state.activeLayerId = layer.id;
  state.selectedFeatureRef = null;
  setNotice(`${layer.name} 레이어를 업로드했습니다.`, "success");
}

async function handleSgisImport(overrides = {}) {
  const {
    fetchSgisGridLayer,
    fetchSgisPopulationLayer,
  } = await loadSgisModule();
  const admCd = String(overrides.admCd ?? "").trim();
  const sourceType = overrides.sourceType ?? "stats";

  if (sourceType === "grid") {
    const gridLevelDiv = String(overrides.gridLevelDiv ?? "").trim();
    if (!admCd || !gridLevelDiv) {
      throw new Error("격자 범위를 정할 수 없습니다. 현재 중심 기준 범위를 먼저 선택해 주세요.");
    }

    const layer = await fetchSgisGridLayer({
      proxyPath: EFFECTIVE_CONFIG.sgis.proxyPath,
      admCd,
      gridLevelDiv,
      year: Number(overrides.year ?? elements.sgisYearField.value),
      metricId: overrides.metricId ?? elements.sgisMetricField.value,
      statsAdmCd: overrides.statsAdmCd ?? admCd,
      statsLowSearch: overrides.statsLowSearch ?? "1",
      color: overrides.color ?? elements.sgisColorField.value,
      scope: overrides.scope ?? "both",
      scopeLabel: overrides.scopeLabel ?? "",
      spatialFilter: overrides.spatialFilter ?? null,
    });
    setImportedPublicLayers([layer, ...state.importedPublicLayers]);
    const hasMetricValue = layer.featureCollection.features.some((feature) =>
      Number.isFinite(Number(feature?.properties?.metricValue)));
    setNotice(
      hasMetricValue
        ? `${layer.name} SGIS 격자 레이어를 가져왔습니다.`
        : `${layer.name} 격자 경계는 가져왔지만, 이 조건의 격자별 통계값은 없습니다. 행정구역 단위나 다른 연도를 선택해 보세요.`,
      hasMetricValue ? "success" : "warn",
    );
    renderAll();
    return layer;
  }

  const lowSearch = String(overrides.lowSearch ?? "").trim();

  if (!admCd || !lowSearch) {
    throw new Error("SGIS 범위를 직접 입력할 필요는 없습니다. 현재 중심 기준 범위를 먼저 선택해 주세요.");
  }

  const layer = await fetchSgisPopulationLayer({
    proxyPath: EFFECTIVE_CONFIG.sgis.proxyPath,
    year: Number(overrides.year ?? elements.sgisYearField.value),
    admCd,
    lowSearch,
    metricId: overrides.metricId ?? elements.sgisMetricField.value,
    color: overrides.color ?? elements.sgisColorField.value,
    scope: overrides.scope ?? "both",
    scopeLabel: overrides.scopeLabel ?? "",
    spatialFilter: overrides.spatialFilter ?? null,
  });
  setImportedPublicLayers([layer, ...state.importedPublicLayers]);
  const hasMetricValue = layer.featureCollection.features.some((feature) =>
    Number.isFinite(Number(feature?.properties?.metricValue)));
  setNotice(
    hasMetricValue
      ? `${layer.name} SGIS 레이어를 가져왔습니다.`
      : `${layer.name} 경계는 가져왔지만, 이 조건의 통계값은 없습니다. 다른 지표나 범위를 선택해 보세요.`,
    hasMetricValue ? "success" : "warn",
  );
  renderAll();
  return layer;
}

