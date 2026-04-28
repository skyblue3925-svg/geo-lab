import { buildLayerMeasurementSummary } from "../application/measurement-use-cases.js";

const MOBILE_MEDIA_QUERY = "(max-width: 760px)";

function isMobileViewport() {
  return typeof window !== "undefined" && typeof window.matchMedia === "function"
    ? window.matchMedia(MOBILE_MEDIA_QUERY).matches
    : false;
}

function getToolInstruction(activeTool) {
  switch (activeTool) {
    case "point":
      return {
        title: "점 도구 사용 중",
        body: "지도에서 한 번 누르면 바로 점 객체가 추가됩니다.",
      };
    case "line":
      return {
        title: "선 도구 사용 중",
        body: "점을 순서대로 찍고 완료를 누르면 선 객체가 저장됩니다.",
      };
    case "polygon":
      return {
        title: "면 도구 사용 중",
        body: "경계를 따라 점을 찍고 완료를 누르면 면 객체가 저장됩니다.",
      };
    case "measure-line":
      return {
        title: "거리 측정 중",
        body: "점을 순서대로 찍고 완료를 누르면 총거리를 계산합니다.",
      };
    case "measure-area":
      return {
        title: "면적 측정 중",
        body: "경계를 따라 점을 찍고 완료를 누르면 면적과 둘레를 계산합니다.",
      };
    case "delete":
      return {
        title: "삭제 도구 사용 중",
        body: "지도에서 객체를 누르면 삭제 여부를 확인합니다.",
      };
    case "select":
    default:
      return {
        title: "선택 도구 사용 중",
        body: "지도에서 객체를 눌러 메모를 수정하거나 다시 그릴 수 있습니다.",
      };
  }
}

function sortStudentLayersForDisplay(studentLayers, activeLayerId) {
  return [...studentLayers].sort((left, right) => {
    if (left.id === activeLayerId) {
      return -1;
    }
    if (right.id === activeLayerId) {
      return 1;
    }
    if (left.visible !== right.visible) {
      return left.visible ? -1 : 1;
    }
    if (right.features.length !== left.features.length) {
      return right.features.length - left.features.length;
    }
    return left.name.localeCompare(right.name, "ko");
  });
}

function buildObservedValueText(feature) {
  const properties = feature?.properties ?? {};
  const label = String(properties.observedLabel ?? "").trim();
  const value = String(properties.observedValue ?? "").trim();
  const unit = String(properties.observedUnit ?? "").trim();

  if (!label && !value) {
    return "";
  }

  const valueText = [value, unit].filter(Boolean).join(" ");
  return [label, valueText].filter(Boolean).join(": ");
}

function buildLayerCard(layer, {
  activeLayerId,
  selectedFeatureRef,
  getStudentLayerGeometryLabel,
  escapeHtml,
}) {
  const isActive = layer.id === activeLayerId;
  const hasSelectedFeature = selectedFeatureRef?.layerId === layer.id;
  const measurementSummary = buildLayerMeasurementSummary(layer);
  const measurementBadges = [
    measurementSummary.breakdownLabel
      ? `<span>${escapeHtml(measurementSummary.breakdownLabel)}</span>`
      : "",
    measurementSummary.totalLengthLabel
      ? `<span>총 길이 ${escapeHtml(measurementSummary.totalLengthLabel)}</span>`
      : "",
    measurementSummary.totalAreaLabel
      ? `<span>총 면적 ${escapeHtml(measurementSummary.totalAreaLabel)}</span>`
      : "",
  ].filter(Boolean);
  const featureRows = layer.features
    .map((feature, index) => {
      const isSelected = selectedFeatureRef?.featureId === feature.id;
      const geometryLabel = getStudentLayerGeometryLabel({
        ...layer,
        features: [feature],
      });
      const title = feature.title?.trim() || `${geometryLabel} 객체 ${index + 1}`;
      const observedValueText = buildObservedValueText(feature);
      const featureSummary = [
        geometryLabel,
        observedValueText || feature.note || "내용 없음",
      ].filter(Boolean).join(" · ");

      return `
        <li class="layer-feature-row ${isSelected ? "is-selected" : ""}">
          <button
            type="button"
            class="layer-feature-select"
            data-action="select-student-feature"
            data-layer-id="${escapeHtml(layer.id)}"
            data-feature-id="${escapeHtml(feature.id)}"
          >
            <span>${escapeHtml(title)}</span>
            <small>${escapeHtml(featureSummary)}</small>
          </button>
          <button
            type="button"
            class="ghost-button compact-button danger-button"
            data-action="delete-student-feature"
            data-layer-id="${escapeHtml(layer.id)}"
            data-feature-id="${escapeHtml(feature.id)}"
          >
            삭제
          </button>
        </li>
      `;
    })
    .join("");

  return `
    <article class="layer-card ${layer.visible ? "is-active" : ""} ${isActive ? "is-editing" : ""}">
      <div class="layer-card-head">
        <div>
          <span class="layer-dot" style="--swatch:${escapeHtml(layer.color)}"></span>
          <strong>${escapeHtml(layer.name)}</strong>
        </div>
        <span class="layer-count">${layer.features.length}개 객체</span>
      </div>
      <p>${escapeHtml(layer.description || "설명 없음")}</p>
      <div class="layer-meta-row">
        <span>${escapeHtml(getStudentLayerGeometryLabel(layer))} 레이어</span>
        <span>${layer.visible ? "지도에 표시 중" : "숨김"}</span>
        <span>${hasSelectedFeature ? "선택된 객체 있음" : "선택된 객체 없음"}</span>
      </div>
      ${measurementBadges.length ? `<div class="layer-meta-row layer-measurement-row">${measurementBadges.join("")}</div>` : ""}
      <label class="layer-opacity-control">
        <span>투명도</span>
        <input type="range" min="20" max="100" step="5" value="${Math.round(Number(layer.opacity ?? 1) * 100)}" data-action="set-student-layer-opacity" data-layer-id="${escapeHtml(layer.id)}" />
        <strong>${Math.round(Number(layer.opacity ?? 1) * 100)}%</strong>
      </label>
      <div class="layer-actions">
        <button type="button" class="ghost-button compact-button" data-action="activate-student-layer" data-layer-id="${escapeHtml(layer.id)}">${isActive ? "현재 활성 레이어" : "이 레이어에 그리기"}</button>
        <button type="button" class="ghost-button compact-button" data-action="toggle-student-layer" data-layer-id="${escapeHtml(layer.id)}">${layer.visible ? "숨기기" : "보이기"}</button>
        <button type="button" class="ghost-button compact-button" data-action="focus-student-layer" data-layer-id="${escapeHtml(layer.id)}">범위 보기</button>
        <button type="button" class="ghost-button compact-button" data-action="edit-student-layer" data-layer-id="${escapeHtml(layer.id)}">편집</button>
      </div>
      <details class="layer-more-actions">
        <summary>더보기</summary>
        <div class="layer-actions layer-actions-secondary">
        <button type="button" class="ghost-button compact-button" data-action="export-student-layer" data-layer-id="${escapeHtml(layer.id)}">내보내기</button>
        <button type="button" class="ghost-button compact-button" data-action="move-student-layer-up" data-layer-id="${escapeHtml(layer.id)}">위로</button>
        <button type="button" class="ghost-button compact-button" data-action="move-student-layer-down" data-layer-id="${escapeHtml(layer.id)}">아래로</button>
        <button type="button" class="ghost-button compact-button danger-button" data-action="delete-student-layer" data-layer-id="${escapeHtml(layer.id)}">레이어 삭제</button>
        </div>
      ${featureRows
        ? `<ul class="layer-feature-list" aria-label="${escapeHtml(layer.name)} 객체 목록">${featureRows}</ul>`
        : `<p class="help-copy compact-copy">아직 이 레이어에 저장된 객체가 없습니다.</p>`}
      </details>
    </article>
  `;
}

function renderWorkspaceSummary(elements, summary, escapeHtml) {
  elements.summaryHeadline.textContent = summary.headline;
  elements.summarySnapshotGrid.innerHTML = summary.snapshots
    .map(
      (item) => `
        <article class="summary-tile">
          <span>${escapeHtml(item.label)}</span>
          <strong>${escapeHtml(item.value)}</strong>
          <p class="help-copy">${escapeHtml(item.detail)}</p>
        </article>
      `,
    )
    .join("");
  elements.summaryInsightList.innerHTML = summary.insights
    .map(
      (insight) => `
        <article class="summary-insight-item">
          <span class="summary-insight-marker"></span>
          <p>${escapeHtml(insight)}</p>
        </article>
      `,
    )
    .join("");
  elements.presentationSummaryField.value = summary.presentationText;
  elements.presentationSummaryHint.textContent = summary.helperText;
}

function renderMeasurementResult(elements, measurementResult) {
  if (!measurementResult) {
    elements.measurementTitle.textContent = "측정 결과 없음";
    elements.measurementValue.textContent = "거리나 면적 도구를 고른 뒤 지도에서 직접 측정해 보세요.";
    elements.measurementDetail.textContent = "";
    if (elements.saveMeasurementLayerButton) {
      elements.saveMeasurementLayerButton.disabled = true;
    }
    elements.clearMeasurementButton.disabled = true;
    return;
  }

  elements.measurementTitle.textContent = measurementResult.title;
  elements.measurementValue.textContent = `${measurementResult.primaryLabel}: ${measurementResult.primaryValue}`;
  elements.measurementDetail.textContent = measurementResult.detail;
  if (elements.saveMeasurementLayerButton) {
    elements.saveMeasurementLayerButton.disabled = false;
  }
  elements.clearMeasurementButton.disabled = false;
}

function buildSelectedFeatureCoordinateText(feature) {
  if (!feature) {
    return "좌표 정보 없음";
  }

  if (feature.geometryType === "point") {
    const coordinate = feature.coordinates?.[0];
    if (Array.isArray(coordinate) && coordinate.length >= 2) {
      return `위도 ${Number(coordinate[1]).toFixed(6)} · 경도 ${Number(coordinate[0]).toFixed(6)}`;
    }
  }

  return `꼭짓점 ${feature.coordinates?.length ?? 0}개`;
}

function setFoldHint(element, text) {
  if (element) {
    element.textContent = text;
  }
}

function syncResponsiveFoldSection(section, { forceMobileOpen, defaultMobileOpen = false }) {
  if (!section) {
    return;
  }

  if (!isMobileViewport()) {
    section.open = true;
    delete section.dataset.mobileInitialized;
    return;
  }

  if (typeof forceMobileOpen === "boolean") {
    section.open = forceMobileOpen;
    section.dataset.mobileInitialized = "true";
    return;
  }

  if (section.dataset.mobileInitialized !== "true") {
    section.open = defaultMobileOpen;
    section.dataset.mobileInitialized = "true";
  }
}

function syncMobileFoldSections(elements, {
  selectedFeatureRecord,
  measurementResult,
  reflectionNote,
  workspaceSummary,
  savedProjectView,
  getStudentLayerGeometryLabel,
}) {
  const selectedFeatureHint = selectedFeatureRecord
    ? `${selectedFeatureRecord.layer.name} · ${getStudentLayerGeometryLabel({
        ...selectedFeatureRecord.layer,
        features: [selectedFeatureRecord.feature],
      })}`
    : "선택 없음";
  const measurementHint = measurementResult?.primaryValue ?? "없음";
  const summaryHint = workspaceSummary.snapshots?.[0]?.value
    ? `${workspaceSummary.snapshots[0].value}`
    : "요약 보기";
  const reflectionHint = reflectionNote?.trim() ? "작성됨" : "미작성";
  const projectHint = savedProjectView.projects.length
    ? `${savedProjectView.projects.length}개 저장`
    : "없음";

  setFoldHint(elements.selectedFeatureFoldHint, selectedFeatureHint);
  setFoldHint(elements.measurementFoldHint, measurementHint);
  setFoldHint(elements.summaryFoldHint, summaryHint);
  setFoldHint(elements.reflectionFoldHint, reflectionHint);
  setFoldHint(elements.projectFoldHint, projectHint);

  syncResponsiveFoldSection(elements.selectedFeatureSection, {
    forceMobileOpen: Boolean(selectedFeatureRecord),
  });
  syncResponsiveFoldSection(elements.measurementSection, {
    forceMobileOpen: Boolean(measurementResult),
  });
  syncResponsiveFoldSection(elements.summarySection, {
    defaultMobileOpen: false,
  });
  syncResponsiveFoldSection(elements.reflectionSection, {
    defaultMobileOpen: false,
  });
  syncResponsiveFoldSection(elements.projectSection, {
    defaultMobileOpen: false,
  });
}

export function renderStudentPanel({
  elements,
  studentLayers,
  activeLayer,
  activeTool,
  draftGeometry,
  selectedFeatureRecord,
  selectedFeatureMeasurement,
  getDraftStatus,
  getStudentLayerGeometryLabel,
  escapeHtml,
  reflectionNote,
  workspaceSummary,
  measurementResult,
  savedProjectView,
  suggestedProjectName,
}) {
  const toolInstruction = getToolInstruction(activeTool);
  const draftGeometryType = draftGeometry?.geometryType ?? null;
  const draftPoints = draftGeometry?.points ?? [];

  elements.studentActionTitle.textContent = toolInstruction.title;
  elements.studentActionBody.textContent = toolInstruction.body;
  elements.editingLayerLabel.textContent = activeLayer
    ? `현재 활성 레이어: ${activeLayer.name}`
    : "현재 활성 레이어가 없습니다. 먼저 레이어를 만들거나 하나를 선택해 주세요.";
  elements.mapClickLabel.textContent = draftGeometryType
    ? getDraftStatus(draftGeometryType, draftPoints)
    : "도구를 고른 뒤 지도에 직접 그리거나, 저장된 객체를 눌러 메모를 수정해 보세요.";

  if (selectedFeatureRecord) {
    const { layer, feature } = selectedFeatureRecord;
    elements.selectedFeatureMeta.textContent = `${layer.name} · ${getStudentLayerGeometryLabel({
      ...layer,
      features: [feature],
    })} 객체`;
    if (elements.selectedFeatureCoordinates) {
      elements.selectedFeatureCoordinates.textContent = buildSelectedFeatureCoordinateText(feature);
    }
    elements.selectedFeatureMeasurement.textContent = selectedFeatureMeasurement || "길이 또는 면적 정보가 없습니다.";
    if (document.activeElement !== elements.pointTitleField) {
      elements.pointTitleField.value = feature.title ?? "";
    }
    if (document.activeElement !== elements.pointNoteField) {
      elements.pointNoteField.value = feature.note ?? "";
    }
    if (elements.featureValueLabelField && document.activeElement !== elements.featureValueLabelField) {
      elements.featureValueLabelField.value = feature.properties?.observedLabel ?? "";
    }
    if (elements.featureValueField && document.activeElement !== elements.featureValueField) {
      elements.featureValueField.value = feature.properties?.observedValue ?? "";
    }
    if (elements.featureValueUnitField && document.activeElement !== elements.featureValueUnitField) {
      elements.featureValueUnitField.value = feature.properties?.observedUnit ?? "";
    }
    elements.featureSeverityField.value = String(feature.properties?.severity ?? "2");
    elements.pointTitleField.disabled = false;
    elements.pointNoteField.disabled = false;
    if (elements.featureValueLabelField) {
      elements.featureValueLabelField.disabled = false;
    }
    if (elements.featureValueField) {
      elements.featureValueField.disabled = false;
    }
    if (elements.featureValueUnitField) {
      elements.featureValueUnitField.disabled = false;
    }
    elements.featureSeverityField.disabled = false;
    elements.saveSelectedFeatureButton.disabled = false;
    elements.deleteSelectedFeatureButton.disabled = false;
    elements.redrawSelectedFeatureButton.disabled = false;
    elements.featureBufferRadiusField.disabled = false;
    elements.createFeatureBufferButton.disabled = false;
  } else {
    elements.selectedFeatureMeta.textContent = "선택된 객체가 없습니다. 지도에서 객체를 눌러 메모를 수정해 보세요.";
    if (elements.selectedFeatureCoordinates) {
      elements.selectedFeatureCoordinates.textContent = "점은 위도·경도, 선과 면은 꼭짓점 수가 표시됩니다.";
    }
    elements.selectedFeatureMeasurement.textContent = "선택된 선 또는 면 객체의 길이와 면적이 여기에 표시됩니다.";
    elements.pointTitleField.value = "";
    elements.pointNoteField.value = "";
    if (elements.featureValueLabelField) {
      elements.featureValueLabelField.value = "";
      elements.featureValueLabelField.disabled = true;
    }
    if (elements.featureValueField) {
      elements.featureValueField.value = "";
      elements.featureValueField.disabled = true;
    }
    if (elements.featureValueUnitField) {
      elements.featureValueUnitField.value = "";
      elements.featureValueUnitField.disabled = true;
    }
    elements.featureSeverityField.value = "2";
    elements.pointTitleField.disabled = true;
    elements.pointNoteField.disabled = true;
    elements.featureSeverityField.disabled = true;
    elements.saveSelectedFeatureButton.disabled = true;
    elements.deleteSelectedFeatureButton.disabled = true;
    elements.redrawSelectedFeatureButton.disabled = true;
    elements.featureBufferRadiusField.disabled = true;
    elements.createFeatureBufferButton.disabled = true;
  }

  if (document.activeElement !== elements.featureBufferRadiusField && !elements.featureBufferRadiusField.value) {
    elements.featureBufferRadiusField.value = "100";
  }

  renderWorkspaceSummary(elements, workspaceSummary, escapeHtml);
  renderMeasurementResult(elements, measurementResult);

  if (document.activeElement !== elements.reflectionNoteField) {
    elements.reflectionNoteField.value = reflectionNote ?? "";
  }
  if (document.activeElement !== elements.projectNameField && !elements.projectNameField.value.trim()) {
    elements.projectNameField.value = suggestedProjectName;
  }

  elements.savedProjectSelectField.innerHTML = savedProjectView.projects.length
    ? savedProjectView.projects
        .map(
          (project) => `
            <option value="${escapeHtml(project.id)}" ${project.id === savedProjectView.selectedProjectId ? "selected" : ""}>
              ${escapeHtml(project.label)}
            </option>
          `,
        )
        .join("")
    : `<option value="">저장한 프로젝트 없음</option>`;
  elements.savedProjectSelectField.disabled = savedProjectView.projects.length === 0;
  elements.loadSavedProjectButton.disabled = savedProjectView.projects.length === 0;
  elements.deleteSavedProjectButton.disabled = savedProjectView.projects.length === 0;
  elements.savedProjectHint.textContent = savedProjectView.selectedProjectHint;

  elements.studentLayerList.innerHTML = studentLayers.length
    ? sortStudentLayersForDisplay(studentLayers, activeLayer?.id ?? null)
        .map((layer) =>
          buildLayerCard(layer, {
            activeLayerId: activeLayer?.id ?? null,
            selectedFeatureRef: selectedFeatureRecord
              ? { layerId: selectedFeatureRecord.layer.id, featureId: selectedFeatureRecord.feature.id }
              : null,
            getStudentLayerGeometryLabel,
            escapeHtml,
          }))
        .join("")
    : `
        <div class="empty-state">
          <strong>학생 레이어가 아직 없습니다.</strong>
          <p>레이어를 하나 만든 뒤 지도에 점, 선, 면을 직접 그려 보세요.</p>
        </div>
      `;

  syncMobileFoldSections(elements, {
    selectedFeatureRecord,
    measurementResult,
    reflectionNote,
    workspaceSummary,
    savedProjectView,
    getStudentLayerGeometryLabel,
  });
}

export function bindStudentPanelEvents({
  elements,
  onCreateStudentLayer,
  onImportLayerFiles,
  onStudentLayerAction,
  onSaveSelectedFeature,
  onDeleteSelectedFeature,
  onRedrawSelectedFeature,
  onCreateFeatureBuffer,
  onClearMeasurement,
  onSaveMeasurementLayer,
  onReflectionInput,
  onSaveReflection,
  onSaveProject,
  onExportProject,
  onImportProjectFile,
  onSelectProject,
  onLoadProject,
  onDeleteProject,
  onCopyPresentationSummary,
  onPrintPresentationSummary,
}) {
  elements.studentLayerForm.addEventListener("submit", (event) => {
    event.preventDefault();
    onCreateStudentLayer({
      name: elements.studentLayerNameField.value.trim(),
      color: elements.studentLayerColorField.value,
      description: elements.studentLayerDescriptionField.value.trim(),
    });
  });

  elements.layerFileField?.addEventListener("change", async (event) => {
    const files = [...(event.target.files ?? [])];
    if (!files.length) {
      return;
    }

    await onImportLayerFiles(files);
    event.target.value = "";
  });

  elements.studentLayerList.addEventListener("click", (event) => {
    const button = event.target.closest("[data-action]");
    if (!button) {
      return;
    }

    onStudentLayerAction({
      action: button.dataset.action,
      layerId: button.dataset.layerId,
      featureId: button.dataset.featureId,
    });
  });

  elements.studentLayerList.addEventListener("input", (event) => {
    const field = event.target.closest("[data-action='set-student-layer-opacity']");
    if (!field) {
      return;
    }

    onStudentLayerAction({
      action: field.dataset.action,
      layerId: field.dataset.layerId,
      value: Number(field.value) / 100,
    });
  });

  elements.saveSelectedFeatureButton.addEventListener("click", () => {
    onSaveSelectedFeature({
      title: elements.pointTitleField.value.trim(),
      note: elements.pointNoteField.value.trim(),
      severity: elements.featureSeverityField.value,
      observedLabel: elements.featureValueLabelField?.value.trim() ?? "",
      observedValue: elements.featureValueField?.value.trim() ?? "",
      observedUnit: elements.featureValueUnitField?.value.trim() ?? "",
    });
  });

  elements.deleteSelectedFeatureButton.addEventListener("click", () => {
    onDeleteSelectedFeature();
  });

  elements.redrawSelectedFeatureButton.addEventListener("click", () => {
    onRedrawSelectedFeature();
  });

  elements.createFeatureBufferButton.addEventListener("click", () => {
    onCreateFeatureBuffer({
      radiusMeters: elements.featureBufferRadiusField.value,
    });
  });

  elements.clearMeasurementButton.addEventListener("click", () => {
    onClearMeasurement();
  });

  elements.saveMeasurementLayerButton?.addEventListener("click", () => {
    onSaveMeasurementLayer();
  });

  elements.reflectionNoteField.addEventListener("input", () => {
    onReflectionInput(elements.reflectionNoteField.value);
  });

  elements.saveReflectionButton.addEventListener("click", () => {
    onSaveReflection(elements.reflectionNoteField.value);
  });

  elements.saveProjectButton.addEventListener("click", () => {
    onSaveProject({
      name: elements.projectNameField.value.trim(),
    });
  });

  elements.exportProjectButton?.addEventListener("click", () => {
    onExportProject({
      name: elements.projectNameField.value.trim(),
    });
  });

  elements.projectImportFileField?.addEventListener("change", async (event) => {
    const file = event.target.files?.[0] ?? null;
    if (!file) {
      return;
    }

    await onImportProjectFile(file);
    event.target.value = "";
  });

  elements.savedProjectSelectField.addEventListener("change", () => {
    onSelectProject(elements.savedProjectSelectField.value);
  });

  elements.loadSavedProjectButton.addEventListener("click", () => {
    onLoadProject(elements.savedProjectSelectField.value);
  });

  elements.deleteSavedProjectButton.addEventListener("click", () => {
    onDeleteProject(elements.savedProjectSelectField.value);
  });

  elements.copyPresentationSummaryButton.addEventListener("click", () => {
    onCopyPresentationSummary(elements.presentationSummaryField.value);
  });

  elements.printPresentationSummaryButton.addEventListener("click", () => {
    onPrintPresentationSummary();
  });
}
