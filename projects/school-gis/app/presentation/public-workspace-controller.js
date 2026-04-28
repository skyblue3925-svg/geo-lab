export function createPublicWorkspaceController({
  state,
  elements,
  mapWorkspace,
  appConfig,
  getLocalPublicLayers,
  setImportedPublicLayers,
  renderAll,
  renderPublicPanel,
  setNotice,
  getCurrentSgisProfile,
  ensureWorkspaceRegionInfo,
  handleRegionSgisProfileImport,
  importPublicLayerFromUrl,
  importPublicLayerFromPreset,
  collectFeatureCollectionCoordinates,
  getRandomLayerColor,
  downloadGeoJson,
}) {
  function clampOpacity(value) {
    const numericValue = Number(value);
    if (!Number.isFinite(numericValue)) {
      return 1;
    }
    return Math.min(1, Math.max(0, numericValue));
  }

  function moveLayer(layers, layerId, direction) {
    const currentIndex = layers.findIndex((layer) => layer.id === layerId);
    if (currentIndex < 0) {
      return layers;
    }

    const targetIndex = direction === "up"
      ? Math.max(0, currentIndex - 1)
      : Math.min(layers.length - 1, currentIndex + 1);

    if (targetIndex === currentIndex) {
      return layers;
    }

    const nextLayers = [...layers];
    const [layer] = nextLayers.splice(currentIndex, 1);
    nextLayers.splice(targetIndex, 0, layer);
    return nextLayers;
  }

  function enableAllExampleLayers() {
    const nextVisibility = {};
    getLocalPublicLayers().forEach((layer) => {
      nextVisibility[layer.id] = true;
    });
    state.localPublicVisibility = nextVisibility;
    state.showSchoolReference = true;
    renderAll();
    setNotice("실습 예시 레이어를 모두 켰습니다.", "success");
  }

  function clearSchoolPublicLayers() {
    const nextVisibility = {};
    getLocalPublicLayers().forEach((layer) => {
      nextVisibility[layer.id] = false;
    });
    state.localPublicVisibility = nextVisibility;
    renderAll();
    setNotice("실습 예시 레이어를 모두 껐습니다.", "info");
  }

  function handleExampleStarterAction(action) {
    if (action === "enable-all-example-layers") {
      enableAllExampleLayers();
      return;
    }

    if (action === "clear-school-public") {
      clearSchoolPublicLayers();
    }
  }

  function handleExampleLayerAction({ action, layerId, value }) {
    const layer = getLocalPublicLayers().find((item) => item.id === layerId);
    if (!layer) {
      return;
    }

    if (action === "toggle-local-layer") {
      state.localPublicVisibility[layer.id] = !state.localPublicVisibility[layer.id];
      renderAll();
      return;
    }

    if (action === "set-local-layer-opacity") {
      state.localPublicOpacity[layer.id] = clampOpacity(value);
      renderAll();
      return;
    }

    if (action === "focus-local-layer") {
      mapWorkspace.fitCoordinates(layer.items.map((item) => [item.lat, item.lng]));
    }
  }

  function handleSchoolReferenceToggle() {
    state.showSchoolReference = !state.showSchoolReference;
    renderAll();
  }

  async function handleQuickSgisAction({ action, metricId, profileId }) {
    if (action === "select-sgis-metric") {
      if (metricId) {
        elements.sgisMetricField.value = metricId;
        renderPublicPanel();
        setNotice("추천 지표를 선택했습니다. 범위를 고른 뒤 레이어로 추가하세요.", "info");
      }
      return;
    }

    if (action === "refresh-school-region") {
      try {
        await ensureWorkspaceRegionInfo({ forceRefresh: true });
        setNotice("현재 위치 기준 행정구역을 다시 확인했습니다.", "success");
      } catch (error) {
        console.error(error);
        setNotice(error.message || "현재 위치 기준 행정구역을 확인하지 못했습니다.", "error");
      }
      return;
    }

    if (action !== "import-region-sgis-profile") {
      return;
    }

    try {
      state.schoolSgisImportPending = profileId ?? "";
      renderPublicPanel();
      await handleRegionSgisProfileImport(profileId);
    } catch (error) {
      console.error(error);
      setNotice(error.message || "현재 위치 기준 SGIS 레이어를 불러오지 못했습니다.", "error");
    } finally {
      state.schoolSgisImportPending = "";
      renderPublicPanel();
    }
  }

  async function handleSgisSubmit() {
    const profileId = getCurrentSgisProfile().id;

    try {
      state.schoolSgisImportPending = profileId;
      renderPublicPanel();
      setNotice("현재 중심 기준 SGIS 레이어를 불러오는 중입니다.");
      await handleRegionSgisProfileImport(profileId);
    } catch (error) {
      console.error(error);
      setNotice(error.message || "SGIS 레이어를 불러오지 못했습니다.", "error");
    } finally {
      state.schoolSgisImportPending = "";
      renderPublicPanel();
    }
  }

  function handleSgisControlChange() {
    if (elements.adminScaleField && elements.sgisProfileField) {
      const hasMatchingScale = [...elements.adminScaleField.options].some(
        (option) => option.value === elements.sgisProfileField.value,
      );
      if (hasMatchingScale) {
        elements.adminScaleField.value = elements.sgisProfileField.value;
      }
    }
    renderPublicPanel();
  }

  async function handlePublicImportSubmit() {
    try {
      const layer = await importPublicLayerFromUrl({
        name: elements.publicLayerNameField.value.trim(),
        description: elements.publicLayerDescriptionField.value.trim(),
        color: elements.publicLayerColorField.value,
        scope: elements.publicLayerScopeField.value,
        type: elements.publicLayerTypeField.value,
        url: elements.publicLayerUrlField.value.trim(),
      });

      setImportedPublicLayers([layer, ...state.importedPublicLayers]);
      elements.publicLayerImportForm.reset();
      elements.publicLayerScopeField.value = state.viewMode;
      elements.publicLayerTypeField.value = "";
      elements.publicLayerColorField.value = getRandomLayerColor(
        state.importedPublicLayers.length,
      );
      renderAll();
      mapWorkspace.fitCoordinates(collectFeatureCollectionCoordinates(layer.featureCollection));
      setNotice(`${layer.name} 공공 레이어를 가져왔습니다.`, "success");
    } catch (error) {
      console.error(error);
      setNotice(error.message || "공공 레이어를 가져오지 못했습니다.", "error");
    }
  }

  async function handlePresetImport(presetId) {
    const preset = appConfig.publicLayerCatalog.find((item) => item.id === presetId);
    if (!preset) {
      return;
    }

    try {
      const layer = await importPublicLayerFromPreset(
        preset,
        state.importedPublicLayers.length,
      );
      setImportedPublicLayers([layer, ...state.importedPublicLayers]);
      renderAll();
      mapWorkspace.fitCoordinates(collectFeatureCollectionCoordinates(layer.featureCollection));
      setNotice(`${layer.name} 프리셋 레이어를 불러왔습니다.`, "success");
    } catch (error) {
      console.error(error);
      setNotice(error.message || "프리셋 레이어를 불러오지 못했습니다.", "error");
    }
  }

  function handleImportedLayerAction({ action, layerId, value }) {
    const layer = state.importedPublicLayers.find((item) => item.id === layerId);
    if (!layer) {
      return;
    }

    if (action === "toggle-imported-public") {
      mapWorkspace.closePopup?.();
      setImportedPublicLayers(
        state.importedPublicLayers.map((item) =>
          item.id === layer.id ? { ...item, visible: !item.visible } : item,
        ),
      );
      renderAll();
      return;
    }

    if (action === "set-imported-public-opacity") {
      setImportedPublicLayers(
        state.importedPublicLayers.map((item) =>
          item.id === layer.id ? { ...item, opacity: clampOpacity(value) } : item,
        ),
      );
      renderAll();
      return;
    }

    if (action === "move-imported-public-up" || action === "move-imported-public-down") {
      setImportedPublicLayers(
        moveLayer(
          state.importedPublicLayers,
          layer.id,
          action === "move-imported-public-up" ? "up" : "down",
        ),
      );
      renderAll();
      return;
    }

    if (action === "edit-imported-public") {
      const nextName = window.prompt("레이어 이름", layer.name);
      if (nextName === null) {
        return;
      }

      const nextDescription = window.prompt("레이어 설명", layer.description ?? "");
      if (nextDescription === null) {
        return;
      }

      setImportedPublicLayers(
        state.importedPublicLayers.map((item) =>
          item.id === layer.id
            ? {
                ...item,
                name: nextName.trim() || item.name,
                description: nextDescription.trim(),
              }
            : item,
        ),
      );
      renderAll();
      setNotice(`${layer.name} 레이어 정보를 수정했습니다.`, "success");
      return;
    }

    if (action === "focus-imported-public") {
      mapWorkspace.fitCoordinates(collectFeatureCollectionCoordinates(layer.featureCollection));
      return;
    }

    if (action === "export-imported-public") {
      downloadGeoJson(`${layer.id}.geojson`, layer.featureCollection);
      setNotice(`${layer.name} 레이어를 내보냈습니다.`, "success");
      return;
    }

    if (action === "delete-imported-public" && window.confirm(`"${layer.name}" 레이어를 삭제할까요?`)) {
      mapWorkspace.closePopup?.();
      setImportedPublicLayers(
        state.importedPublicLayers.filter((item) => item.id !== layer.id),
      );
      renderAll();
      setNotice(`${layer.name} 레이어를 삭제했습니다.`, "success");
    }
  }

  return {
    handleExampleStarterAction,
    handleQuickSgisAction,
    handleExampleLayerAction,
    handleSchoolReferenceToggle,
    handleSgisSubmit,
    handleSgisControlChange,
    handlePublicImportSubmit,
    handlePresetImport,
    handleImportedLayerAction,
  };
}
