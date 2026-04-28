import { buildRegionSgisImportPlan } from "../application/sgis-region-use-cases.js";

export function createWorkspaceRegionController({
  state,
  appConfig,
  renderPublicPanel,
  getWorkspaceFormValues,
  buildWorkspaceRegionCacheKey,
  loadSgisModule,
  getSchoolSgisControlValues,
  handleSgisImport,
  getCurrentLocationLabel,
  mapWorkspace,
  collectFeatureCollectionCoordinates,
  setNotice,
}) {
  function hasLayerMetricValues(layer) {
    return (layer?.featureCollection?.features ?? []).some((feature) =>
      Number.isFinite(Number(feature?.properties?.metricValue)));
  }

  function getFallbackProfileId(plan) {
    if (plan.profile?.type !== "grid") {
      return "";
    }

    if (plan.gridLevelDiv === "10km") {
      return "region-sido-children";
    }
    if (plan.gridLevelDiv === "100m") {
      return "region-emdong";
    }
    return "region-sgg-children";
  }

  async function ensureWorkspaceRegionInfo({ forceRefresh = false } = {}) {
    if (!state.referenceLocked) {
      throw new Error("먼저 지도 검색으로 위치를 찾고 기준 위치로 고정해 주세요.");
    }

    const workspace = getWorkspaceFormValues();
    const cacheKey = buildWorkspaceRegionCacheKey(workspace);

    if (
      !forceRefresh
      && state.workspaceRegion
      && state.workspaceRegion.cacheKey === cacheKey
    ) {
      return state.workspaceRegion;
    }

    state.workspaceRegionPending = true;
    renderPublicPanel();

    try {
      const { fetchSgisRegionCode } = await loadSgisModule();
      const region = await fetchSgisRegionCode({
        proxyPath: appConfig.sgis.proxyPath,
        lat: workspace.lat,
        lng: workspace.lng,
      });

      state.workspaceRegion = {
        ...region,
        cacheKey,
      };
      return state.workspaceRegion;
    } finally {
      state.workspaceRegionPending = false;
      renderPublicPanel();
    }
  }

  async function handleRegionSgisProfileImport(profileId) {
    const region = await ensureWorkspaceRegionInfo();
    const controlValues = getSchoolSgisControlValues();
    const plan = buildRegionSgisImportPlan({
      profileId,
      region,
      year: controlValues.year,
      metricId: controlValues.metricId,
      color: controlValues.color,
      scope: "school",
    });
    const spatialFilter = plan.clipToReference
      ? {
          center: state.referenceLocation,
          radiusMeters: state.referenceRadiusMeters,
        }
      : null;

    setNotice(`${getCurrentLocationLabel()} 기준 SGIS 레이어를 불러오는 중입니다.`);
    const layer = await handleSgisImport({
      ...plan,
      spatialFilter,
    });
    if (spatialFilter) {
      mapWorkspace.fitReferenceArea?.(state.referenceLocation, state.referenceRadiusMeters);
    } else {
      mapWorkspace.fitCoordinates(
        collectFeatureCollectionCoordinates(layer.featureCollection),
      );
    }
    if (plan.profile?.type === "grid" && !hasLayerMetricValues(layer)) {
      const fallbackProfileId = getFallbackProfileId(plan);
      const fallbackMessage = fallbackProfileId
        ? " 이 지역/연도/지표 조합은 격자별 통계값이 없습니다. 행정구역 단위로 대체해서 불러올 수 있습니다."
        : " 이 지역/연도/지표 조합은 격자별 통계값이 없습니다.";
      setNotice(fallbackMessage.trim(), "warn");
    }
    return layer;
  }

  return {
    ensureWorkspaceRegionInfo,
    handleRegionSgisProfileImport,
  };
}
