const TOOL_LABEL = {
  select: "선택",
  point: "점",
  line: "선",
  polygon: "면",
  "measure-line": "거리",
  "measure-area": "면적",
  delete: "삭제",
};

const STUDENT_LAYER_DRAW_TOOLS = new Set(["point", "line", "polygon"]);

function getToolbarHint({ studentLayers, activeTool, draftGeometry }) {
  if (!studentLayers.length) {
    return "점·선·면을 누르면 새 학생 레이어가 자동으로 만들어집니다. 거리와 면적은 레이어 없이도 측정할 수 있습니다.";
  }

  const draftCount = draftGeometry?.points?.length ?? 0;
  if (!draftGeometry) {
    return `${TOOL_LABEL[activeTool] ?? "선택"} 도구가 준비되었습니다.`;
  }

  return `${TOOL_LABEL[activeTool] ?? draftGeometry.geometryType} 임시 도형 · 점 ${draftCount}개`;
}

export function renderDrawToolbar({
  elements,
  studentLayers,
  activeLayerId,
  activeTool,
  draftGeometry,
  canCompleteDraft,
  escapeHtml,
}) {
  const hasStudentLayer = studentLayers.length > 0;
  const options = hasStudentLayer
    ? studentLayers
        .map((layer) => `
          <option value="${escapeHtml(layer.id)}" ${layer.id === activeLayerId ? "selected" : ""}>
            ${escapeHtml(layer.name)}
          </option>
        `)
        .join("")
    : `<option value="">레이어를 먼저 만들어 주세요</option>`;

  elements.activeLayerField.innerHTML = options;
  elements.activeLayerField.disabled = !hasStudentLayer;

  if (elements.quickCreateLayerButton) {
    elements.quickCreateLayerButton.disabled = false;
    elements.quickCreateLayerButton.textContent = hasStudentLayer ? "새 레이어" : "내 레이어 시작";
    elements.quickCreateLayerButton.title = hasStudentLayer
      ? "새 학생 레이어를 하나 더 만듭니다."
      : "빈 학생 레이어를 만들고 점 도구를 켭니다.";
  }

  elements.drawToolbar.querySelectorAll("[data-draw-tool]").forEach((button) => {
    const tool = button.dataset.drawTool;
    const requiresLayer = STUDENT_LAYER_DRAW_TOOLS.has(tool);
    const disabled = false;

    button.disabled = disabled;
    button.classList.toggle("is-disabled", false);
    button.classList.toggle("needs-layer", requiresLayer && !hasStudentLayer);
    button.classList.toggle("is-active", !disabled && tool === activeTool);
    button.title = requiresLayer && !hasStudentLayer
      ? "누르면 새 학생 레이어를 자동으로 만들고 이 도구를 켭니다."
      : "";
  });

  elements.drawToolbarHint.textContent = getToolbarHint({
    studentLayers,
    activeTool,
    draftGeometry,
  });
  if (elements.undoDraftPointButton) {
    elements.undoDraftPointButton.disabled = !(draftGeometry?.points?.length);
  }
  elements.completeDraftButton.disabled = !canCompleteDraft;
  elements.cancelDraftButton.disabled = !draftGeometry;
}

export function bindDrawToolbarEvents({
  elements,
  onToolSelect,
  onActiveLayerChange,
  onCompleteDraft,
  onCancelDraft,
  onUndoDraftPoint,
  onQuickCreateLayer,
}) {
  elements.drawToolbar.addEventListener("click", (event) => {
    const button = event.target.closest("[data-draw-tool]");
    if (!button || button.disabled) {
      return;
    }

    onToolSelect(button.dataset.drawTool);
  });

  elements.activeLayerField.addEventListener("change", () => {
    onActiveLayerChange(elements.activeLayerField.value);
  });

  elements.quickCreateLayerButton?.addEventListener("click", () => {
    onQuickCreateLayer();
  });

  elements.completeDraftButton.addEventListener("click", () => {
    onCompleteDraft();
  });

  elements.undoDraftPointButton?.addEventListener("click", () => {
    onUndoDraftPoint();
  });

  elements.cancelDraftButton.addEventListener("click", () => {
    onCancelDraft();
  });
}
