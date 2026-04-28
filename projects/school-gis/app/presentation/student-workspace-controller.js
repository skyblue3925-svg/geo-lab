import {
  buildStudentLayerFeatureCollection,
  getStudentGeometryLabel,
  getStudentLayerCoordinates,
} from "../domain/student-layer.js";
import {
  buildStudentFeatureFromDraft,
  canFinalizeStudentDraftGeometry,
  createStudentLayer,
} from "../application/student-layer-use-cases.js";
import { buildMeasurementResult } from "../application/measurement-use-cases.js";
import {
  appendPointToDraftGeometry,
  createDraftGeometry,
  getDrawToolGeometryType,
  getMeasurementKind,
  isGeometryDrawTool,
  isMeasurementTool,
  isStudentFeatureDrawTool,
  removeLastDraftPoint,
  resolveDrawTool,
} from "../application/draw-session-use-cases.js";
import {
  createSelectedFeatureRef,
  findSelectedStudentFeature,
  isSameSelectedFeatureRef,
} from "../application/feature-selection-use-cases.js";
import {
  appendFeatureToStudentLayers,
  removeStudentFeature,
  updateStudentFeatureDetails,
} from "../application/student-layer-edit-use-cases.js";
import { createBufferLayer } from "../application/buffer-use-cases.js";

function buildDraftGeometryFromFeature(feature) {
  return {
    geometryType: feature.geometryType,
    points: feature.coordinates.map(([lng, lat]) => ({
      lat: Number(lat),
      lng: Number(lng),
    })),
  };
}

export function createStudentWorkspaceController({
  state,
  elements,
  mapWorkspace,
  createId,
  drawToolMeta,
  observationSeverityLabel,
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
  getNextImportedPublicColor,
  getNextStudentLayerColor,
  openStudentTools = () => {},
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

  function activateDrawTool(tool) {
    const nextTool = resolveDrawTool(tool);
    state.activeTool = nextTool;

    if (!isGeometryDrawTool(nextTool)) {
      clearDraftGeometry();
      clearMeasurementResult();
      return;
    }

    if (isStudentFeatureDrawTool(nextTool) && !state.activeLayerId) {
      state.activeTool = "select";
      clearDraftGeometry();
      clearMeasurementResult();
      return;
    }

    state.selectedFeatureRef = null;
    clearMeasurementResult();
    state.draftGeometry = createDraftGeometry(getDrawToolGeometryType(nextTool));
  }

  function handleToolSelect(tool) {
    if (isStudentFeatureDrawTool(tool) && !state.activeLayerId) {
      createStudentLayerFromInput({
        name: "",
        color: elements.studentLayerColorField?.value ?? getNextStudentLayerColor(),
        description: "지도에서 직접 만든 점·선·면 조사 레이어",
        initialTool: tool,
        autoStart: true,
      });
      return;
    }

    activateDrawTool(tool);
    renderAll();

    if (tool === "select") {
      setNotice("선택 도구로 바뀌었습니다.", "info");
      return;
    }

    if (tool === "delete") {
      setNotice("삭제 도구로 바뀌었습니다. 객체를 누르면 삭제를 확인합니다.", "info");
      return;
    }

    if (tool === "measure-line") {
      setNotice("거리 측정을 시작합니다. 점을 찍고 완료를 눌러 주세요.", "info");
      return;
    }

    if (tool === "measure-area") {
      setNotice("면적 측정을 시작합니다. 경계를 따라 점을 찍고 완료를 눌러 주세요.", "info");
      return;
    }

    setNotice(`${drawToolMeta[tool].label} 도구로 바뀌었습니다. 지도 위에 직접 그려 보세요.`, "info");
  }

  function handleActiveLayerChange(layerId) {
    setActiveStudentLayer(layerId);
    renderAll();
  }

  function cancelDraftGeometry() {
    clearDraftGeometry();
    clearMeasurementResult();
    renderAll();
    setNotice("임시 도형을 취소했습니다.", "info");
  }

  function completeMeasurementDraft(draftGeometry) {
    const measurementResult = buildMeasurementResult(state.activeTool, draftGeometry);
    if (!measurementResult) {
      return;
    }

    setMeasurementResult(measurementResult);
    renderAll();
    openStudentTools();
    setNotice(`${measurementResult.title}을 계산했습니다. 필요하면 측정값을 레이어로 저장하세요.`, "success");
  }

  function completeStudentFeatureDraft(activeLayer, draftGeometry) {
    const feature = buildStudentFeatureFromDraft({
      idFactory: createId,
      layer: activeLayer,
      geometryType: draftGeometry.geometryType,
      draftPoints: draftGeometry.points,
      title: "",
      note: "",
      properties: {
        severity: "2",
        severityLabel: observationSeverityLabel["2"],
      },
    });

    setStudentLayers(appendFeatureToStudentLayers(state.studentLayers, activeLayer.id, feature));
    state.selectedFeatureRef = createSelectedFeatureRef(activeLayer.id, feature.id);
    clearDraftGeometry();
    resetStudentDraftInputs();
    renderAll();
    openStudentTools();
    setNotice(`${activeLayer.name} 레이어에 ${getStudentGeometryLabel(feature.geometryType)} 객체를 추가했습니다. 제목과 속성값을 바로 입력하세요.`, "success");
  }

  function handleCompleteDraft() {
    const draftGeometry = state.draftGeometry;
    if (
      !draftGeometry
      || !canFinalizeStudentDraftGeometry(draftGeometry.geometryType, draftGeometry.points)
    ) {
      return;
    }

    try {
      if (isMeasurementTool(state.activeTool)) {
        completeMeasurementDraft(draftGeometry);
        return;
      }

      const activeLayer = getActiveStudentLayer();
      if (!activeLayer) {
        return;
      }

      completeStudentFeatureDraft(activeLayer, draftGeometry);
    } catch (error) {
      console.error(error);
      setNotice(error.message || "도형을 완성하지 못했습니다. 점 수를 다시 확인해 주세요.", "warn");
      renderAll();
    }
  }

  function createStudentLayerFromInput({
    name,
    color,
    description,
    initialTool = "point",
    autoStart = false,
  }) {
    const resolvedName = String(name ?? "").trim() || `학생 레이어 ${state.studentLayers.length + 1}`;
    const resolvedTool = isStudentFeatureDrawTool(initialTool) ? initialTool : "point";

    const layer = createStudentLayer({
      idFactory: createId,
      name: resolvedName,
      color,
      description,
    });
    setStudentLayers([layer, ...state.studentLayers]);
    state.activeLayerId = layer.id;
    state.activeTool = "select";
    state.selectedFeatureRef = null;
    clearMeasurementResult();
    clearDraftGeometry();
    resetStudentDraftInputs();
    resetStudentLayerForm();
    activateDrawTool(resolvedTool);
    renderAll();
    const toolLabel = drawToolMeta[resolvedTool]?.label ?? "점";
    setNotice(
      autoStart
        ? `${layer.name}을 자동으로 만들고 ${toolLabel} 도구를 켰습니다. 이제 지도 위에 바로 그리세요.`
        : `${layer.name} 학생 레이어를 만들었습니다. ${toolLabel} 도구로 바로 그릴 수 있습니다.`,
      "success",
    );
  }

  function handleQuickCreateStudentLayer() {
    createStudentLayerFromInput({
      name: elements.studentLayerNameField?.value ?? "",
      color: elements.studentLayerColorField?.value ?? "#1b6a57",
      description: elements.studentLayerDescriptionField?.value ?? "",
    });
  }

  async function importStudentLayerFiles(files) {
    try {
      for (const file of files) {
        await importLayerFile(file);
      }
      renderAll();
      setNotice(`${files.length}개 파일을 학생 레이어로 가져왔습니다.`, "success");
    } catch (error) {
      console.error(error);
      setNotice(error.message || "파일 레이어를 가져오지 못했습니다.", "error");
    }
  }

  function handleStudentLayerAction(action, layerId, value, featureId) {
    const layer = state.studentLayers.find((item) => item.id === layerId);
    if (!layer) {
      return;
    }

    const feature = featureId
      ? layer.features.find((item) => item.id === featureId)
      : null;

    if (action === "select-student-feature" && feature) {
      state.activeTool = "select";
      state.selectedFeatureRef = createSelectedFeatureRef(layer.id, feature.id);
      renderAll();
      openStudentTools();
      setNotice(`${layer.name} 레이어의 객체를 선택했습니다.`, "info");
      return;
    }

    if (action === "delete-student-feature" && feature) {
      const label = feature.title?.trim() || getStudentGeometryLabel(feature.geometryType);
      if (!window.confirm(`"${label}" 객체를 삭제할까요?`)) {
        return;
      }

      mapWorkspace.closePopup?.();
      setStudentLayers(removeStudentFeature(state.studentLayers, layer.id, feature.id));
      if (isSameSelectedFeatureRef(state.selectedFeatureRef, { layerId: layer.id, featureId: feature.id })) {
        state.selectedFeatureRef = null;
      }
      clearDraftGeometry();
      renderAll();
      setNotice("객체를 삭제했습니다.", "success");
      return;
    }

    if (action === "toggle-student-layer") {
      mapWorkspace.closePopup?.();
      setStudentLayers(
        state.studentLayers.map((item) =>
          item.id === layer.id ? { ...item, visible: !item.visible } : item,
        ),
      );
      renderAll();
      return;
    }

    if (action === "activate-student-layer") {
      setActiveStudentLayer(layer.id);
      renderAll();
      setNotice(`${layer.name} 레이어를 활성 레이어로 선택했습니다.`, "info");
      return;
    }

    if (action === "focus-student-layer") {
      mapWorkspace.fitCoordinates(getStudentLayerCoordinates(layer));
      return;
    }

    if (action === "set-student-layer-opacity") {
      setStudentLayers(
        state.studentLayers.map((item) =>
          item.id === layer.id ? { ...item, opacity: clampOpacity(value) } : item,
        ),
      );
      renderAll();
      return;
    }

    if (action === "move-student-layer-up" || action === "move-student-layer-down") {
      setStudentLayers(
        moveLayer(
          state.studentLayers,
          layer.id,
          action === "move-student-layer-up" ? "up" : "down",
        ),
      );
      renderAll();
      return;
    }

    if (action === "edit-student-layer") {
      const nextName = window.prompt("레이어 이름", layer.name);
      if (nextName === null) {
        return;
      }

      const nextDescription = window.prompt("레이어 설명", layer.description ?? "");
      if (nextDescription === null) {
        return;
      }

      setStudentLayers(
        state.studentLayers.map((item) =>
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

    if (action === "export-student-layer") {
      downloadGeoJson(`${layer.id}.geojson`, buildStudentLayerFeatureCollection(layer));
      setNotice(`${layer.name} 레이어를 내보냈습니다.`, "success");
      return;
    }

    if (action === "delete-student-layer" && window.confirm(`"${layer.name}" 학생 레이어를 삭제할까요?`)) {
      mapWorkspace.closePopup?.();
      setStudentLayers(state.studentLayers.filter((item) => item.id !== layer.id));
      renderAll();
      setNotice(`${layer.name} 학생 레이어를 삭제했습니다.`, "success");
    }
  }

  function handleUndoDraftGeometryPoint() {
    if (!state.draftGeometry) {
      return;
    }

    state.draftGeometry = removeLastDraftPoint(state.draftGeometry);
    if (!state.draftGeometry.points.length) {
      clearDraftGeometry();
      clearMeasurementResult();
    }
    renderAll();
  }

  function handleSaveSelectedFeature({
    title,
    note,
    severity,
    observedLabel,
    observedValue,
    observedUnit,
  }) {
    const selectedFeatureRecord = getSelectedStudentFeatureRecord();
    if (!selectedFeatureRecord) {
      return;
    }

    setStudentLayers(
      updateStudentFeatureDetails(state.studentLayers, {
        layerId: selectedFeatureRecord.layer.id,
        featureId: selectedFeatureRecord.feature.id,
        title: title || selectedFeatureRecord.feature.title,
        note,
        severity,
        observedLabel,
        observedValue,
        observedUnit,
      }),
    );
    state.selectedFeatureRef = createSelectedFeatureRef(
      selectedFeatureRecord.layer.id,
      selectedFeatureRecord.feature.id,
    );
    renderAll();
    setNotice("객체 메모를 저장했습니다.", "success");
  }

  function handleSaveMeasurementLayer() {
    const measurementResult = state.measurementResult;
    const draftGeometry = state.draftGeometry;
    if (!measurementResult || !draftGeometry?.points?.length) {
      setNotice("저장할 측정 결과가 없습니다. 먼저 거리나 면적을 측정해 주세요.", "warn");
      return;
    }

    try {
      const layer = createStudentLayer({
        idFactory: createId,
        name: `${measurementResult.title} ${measurementResult.primaryValue}`,
        color: getNextStudentLayerColor?.() ?? "#4f8a8b",
        description: measurementResult.detail,
        geometryType: draftGeometry.geometryType,
        source: "measurement",
      });
      const feature = buildStudentFeatureFromDraft({
        idFactory: createId,
        layer,
        geometryType: draftGeometry.geometryType,
        draftPoints: draftGeometry.points,
        title: measurementResult.title,
        note: measurementResult.detail,
        properties: {
          measurementKind: measurementResult.kind,
          measurementLabel: measurementResult.primaryLabel,
          measurementValueLabel: measurementResult.primaryValue,
          observedLabel: measurementResult.primaryLabel,
          observedValue: measurementResult.primaryValue,
          observedUnit: "",
          severity: "2",
          severityLabel: observationSeverityLabel["2"],
        },
      });

      setStudentLayers(appendFeatureToStudentLayers([layer, ...state.studentLayers], layer.id, feature));
      state.activeLayerId = layer.id;
      state.selectedFeatureRef = createSelectedFeatureRef(layer.id, feature.id);
      clearMeasurementResult();
      clearDraftGeometry();
      renderAll();
      openStudentTools();
      setNotice("측정 결과를 학생 레이어로 저장했습니다.", "success");
    } catch (error) {
      console.error(error);
      setNotice(error.message || "측정 결과를 레이어로 저장하지 못했습니다.", "error");
    }
  }

  function handleDeleteSelectedFeature() {
    const selectedFeatureRecord = getSelectedStudentFeatureRecord();
    if (!selectedFeatureRecord) {
      return;
    }

    if (!window.confirm(`"${selectedFeatureRecord.feature.title}" 객체를 삭제할까요?`)) {
      return;
    }

    mapWorkspace.closePopup?.();
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

  function handleRedrawSelectedFeature() {
    const selectedFeatureRecord = getSelectedStudentFeatureRecord();
    if (!selectedFeatureRecord) {
      return;
    }

    const { layer, feature } = selectedFeatureRecord;
    setStudentLayers(removeStudentFeature(state.studentLayers, layer.id, feature.id));
    state.activeLayerId = layer.id;
    state.activeTool = feature.geometryType;
    state.draftGeometry = buildDraftGeometryFromFeature(feature);
    state.selectedFeatureRef = null;
    clearMeasurementResult();
    resetStudentDraftInputs();
    renderAll();
    setNotice(`${layer.name} 레이어의 객체를 다시 그리는 중입니다.`, "info");
  }

  function handleCreateFeatureBuffer({ radiusMeters }) {
    const selectedFeatureRecord = getSelectedStudentFeatureRecord();
    if (!selectedFeatureRecord) {
      setNotice("먼저 버퍼를 만들 객체를 하나 선택해 주세요.", "warn");
      return;
    }

    const parsedRadius = Number(radiusMeters);
    if (!Number.isFinite(parsedRadius) || parsedRadius <= 0) {
      setNotice("버퍼 반경은 1m 이상의 숫자로 입력해 주세요.", "warn");
      return;
    }

    try {
      const bufferLayer = createBufferLayer({
        idFactory: createId,
        selectedFeatureRecord,
        radiusMeters: Math.round(parsedRadius),
        color: getNextImportedPublicColor(),
        scope: state.viewMode,
      });

      setImportedPublicLayers([bufferLayer, ...state.importedPublicLayers]);
      renderAll();
      setNotice(`${bufferLayer.name} 분석 레이어를 만들었습니다.`, "success");
    } catch (error) {
      console.error(error);
      setNotice(error.message || "버퍼 레이어를 만들지 못했습니다.", "error");
    }
  }

  function handleStudentFeatureInteract({ layerId, featureId }) {
    if (!layerId || !featureId) {
      return;
    }

    if (state.activeTool === "delete") {
      const selectedFeatureRecord = findSelectedStudentFeature(
        state.studentLayers,
        createSelectedFeatureRef(layerId, featureId),
      );
      if (!selectedFeatureRecord) {
        return;
      }

      if (window.confirm(`"${selectedFeatureRecord.feature.title}" 객체를 삭제할까요?`)) {
        mapWorkspace.closePopup?.();
        setStudentLayers(removeStudentFeature(state.studentLayers, layerId, featureId));
        if (isSameSelectedFeatureRef(state.selectedFeatureRef, { layerId, featureId })) {
          state.selectedFeatureRef = null;
        }
        renderAll();
        setNotice("객체를 삭제했습니다.", "success");
      }
      return;
    }

    if (state.activeTool === "select") {
      selectStudentFeature(layerId, featureId);
      renderAll();
      openStudentTools();
    }
  }

  function handleMapClick(latlng) {
    if (!isGeometryDrawTool(state.activeTool)) {
      if (state.activeTool === "select") {
        state.selectedFeatureRef = null;
        renderAll();
      }
      mapWorkspace.showDraftCursor(latlng, false);
      elements.mapClickLabel.textContent = `최근 클릭 위치: ${latlng.lat.toFixed(5)}, ${latlng.lng.toFixed(5)}`;
      return;
    }

    if (isMeasurementTool(state.activeTool) && state.measurementResult) {
      state.draftGeometry = createDraftGeometry(getDrawToolGeometryType(state.activeTool));
      clearMeasurementResult();
    }

    const activeLayer = getActiveStudentLayer();
    const geometryType = getDrawToolGeometryType(state.activeTool);

    if (isStudentFeatureDrawTool(state.activeTool) && !activeLayer) {
      setNotice("먼저 학생 레이어를 하나 선택해 주세요.", "warn");
      return;
    }

    if (geometryType !== "point") {
      state.draftGeometry = appendPointToDraftGeometry(state.draftGeometry, latlng);
      renderAll();

      if (isMeasurementTool(state.activeTool)) {
        const label = getMeasurementKind(state.activeTool) === "distance" ? "거리" : "면적";
        setNotice(`${label} 측정 점 ${state.draftGeometry.points.length}개를 기록했습니다.`, "info");
        return;
      }

      setNotice(`${activeLayer.name} 레이어에 점 ${state.draftGeometry.points.length}개를 기록했습니다.`, "info");
      return;
    }

    const feature = buildStudentFeatureFromDraft({
      idFactory: createId,
      layer: activeLayer,
      geometryType,
      draftPoints: [latlng],
      title: "",
      note: "",
      properties: {
        severity: "2",
        severityLabel: observationSeverityLabel["2"],
      },
    });

    setStudentLayers(appendFeatureToStudentLayers(state.studentLayers, activeLayer.id, feature));
    state.selectedFeatureRef = createSelectedFeatureRef(activeLayer.id, feature.id);

    mapWorkspace.showDraftCursor(latlng, true);
    elements.mapClickLabel.textContent = `${activeLayer.name} 레이어에 객체를 추가했습니다: ${latlng.lat.toFixed(5)}, ${latlng.lng.toFixed(5)}`;
    resetStudentDraftInputs();
    renderAll();
    openStudentTools();
    setNotice(`${activeLayer.name} 레이어에 점 객체를 추가했습니다. 제목과 속성값을 바로 입력하세요.`, "success");
  }

  return {
    handleToolSelect,
    handleActiveLayerChange,
    handleCompleteDraft,
    handleCancelDraft: cancelDraftGeometry,
    handleCreateStudentLayer: createStudentLayerFromInput,
    handleQuickCreateStudentLayer,
    handleImportStudentLayerFiles: importStudentLayerFiles,
    handleStudentLayerAction,
    handleSaveSelectedFeature,
    handleDeleteSelectedFeature,
    handleRedrawSelectedFeature,
    handleStudentFeatureInteract,
    handleMapClick,
    handleUndoDraftGeometryPoint,
    handleCreateFeatureBuffer,
    handleSaveMeasurementLayer,
  };
}
