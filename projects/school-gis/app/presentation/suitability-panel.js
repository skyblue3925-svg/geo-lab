function renderOptions(items, selectedId, escapeHtml, emptyLabel) {
  if (!items.length) {
    return emptyLabel ? `<option value="">${escapeHtml(emptyLabel)}</option>` : "";
  }

  return items
    .map(
      (item) => `
        <option value="${escapeHtml(item.id)}" ${item.id === selectedId ? "selected" : ""}>
          ${escapeHtml(item.name ?? item.label)}
        </option>
      `,
    )
    .join("");
}

function setRangeValue(field, label, value) {
  if (!field) {
    return;
  }

  field.value = String(value);
  if (label) {
    label.textContent = `${value}%`;
  }
}

function renderLatestResult(latestResult, escapeHtml) {
  if (!latestResult) {
    return `
      <div class="empty-state compact">
        <strong>아직 입지점수 결과가 없습니다.</strong>
        <p>SGIS 격자 레이어를 추가한 뒤 조건을 조절해 분석 레이어를 만들어 보세요.</p>
      </div>
    `;
  }

  const candidateRows = latestResult.topCandidates?.length
    ? latestResult.topCandidates
        .map(
          (candidate) => `
            <li>
              <strong>${candidate.rank}위 · ${escapeHtml(candidate.title)}</strong>
              <span>${Number(candidate.score).toLocaleString("ko-KR")}점</span>
              <small>${escapeHtml(candidate.reason)}</small>
            </li>
          `,
        )
        .join("")
    : `<li><strong>후보 격자 없음</strong><span>-</span><small>조건을 다시 조절해 보세요.</small></li>`;

  return `
    <article class="suitability-result-card">
      <div class="layer-stat-head">
        <strong>${escapeHtml(latestResult.name)}</strong>
        <span>상위 후보 3개</span>
      </div>
      <ol class="grid-cell-list">${candidateRows}</ol>
    </article>
  `;
}

export function renderSuitabilityPanel({ elements, viewModel, escapeHtml }) {
  if (!elements.analysisCard) {
    return;
  }

  elements.suitabilityTemplateField.innerHTML = renderOptions(
    viewModel.templates,
    viewModel.selectedTemplateId,
    escapeHtml,
    "템플릿 없음",
  );
  elements.suitabilityGridLayerField.innerHTML = renderOptions(
    viewModel.gridLayers.map((layer) => ({
      id: layer.id,
      name: `${layer.name} · ${layer.metricLabel} · ${layer.featureCount}개 격자`,
    })),
    viewModel.selectedGridLayerId,
    escapeHtml,
    "SGIS 격자 레이어 없음",
  );
  elements.suitabilityStudentLayerField.innerHTML = [
    `<option value="">학생 레이어 사용 안 함</option>`,
    renderOptions(
      viewModel.studentLayers.map((layer) => ({
        id: layer.id,
        name: `${layer.name} · ${layer.featureCount}개 객체`,
      })),
      viewModel.selectedStudentLayerId,
      escapeHtml,
      "",
    ),
  ].join("");
  elements.suitabilityStudentLayerField.value = viewModel.selectedStudentLayerId;
  elements.suitabilityTemplateDescription.textContent = viewModel.selectedTemplateDescription;
  elements.suitabilityEmptyReason.textContent = viewModel.emptyReason;
  elements.createSuitabilityButton.disabled = !viewModel.canCreate;

  setRangeValue(elements.suitabilityPublicWeightField, elements.suitabilityPublicWeightValue, viewModel.weights.publicWeight);
  setRangeValue(elements.suitabilityNearWeightField, elements.suitabilityNearWeightValue, viewModel.weights.nearWeight);
  setRangeValue(elements.suitabilityFarWeightField, elements.suitabilityFarWeightValue, viewModel.weights.farWeight);

  elements.suitabilityResult.innerHTML = renderLatestResult(viewModel.latestResult, escapeHtml);
}

export function bindSuitabilityPanelEvents({
  elements,
  onSuitabilityControlChange,
  onCreateSuitability,
  onOpenPublicTools,
  onOpenStudentTools,
}) {
  [
    elements.suitabilityTemplateField,
    elements.suitabilityGridLayerField,
    elements.suitabilityStudentLayerField,
    elements.suitabilityPublicWeightField,
    elements.suitabilityNearWeightField,
    elements.suitabilityFarWeightField,
  ]
    .filter(Boolean)
    .forEach((field) => {
      field.addEventListener("input", () => {
        onSuitabilityControlChange();
      });
      field.addEventListener("change", () => {
        onSuitabilityControlChange();
      });
    });

  elements.createSuitabilityButton?.addEventListener("click", () => {
    onCreateSuitability();
  });

  elements.openPublicForSuitabilityButton?.addEventListener("click", () => {
    onOpenPublicTools();
  });

  elements.openStudentForSuitabilityButton?.addEventListener("click", () => {
    onOpenStudentTools();
  });
}
