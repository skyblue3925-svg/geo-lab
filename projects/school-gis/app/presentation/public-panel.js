const EXAMPLE_LAYER_HINT = {
  "bus-stops": "버스정류장 분포와 학생 기록을 비교해 보기 좋은 예시 레이어입니다.",
  "safety-observation": "통학 위험 지점이나 생활 불편 지점을 겹쳐 볼 때 적합한 예시 레이어입니다.",
  "rest-spots": "쉼터, 그늘, 체류 공간을 학생 관찰 결과와 비교할 때 쓰기 좋습니다.",
};

function buildExampleLayerCard(layer, escapeHtml) {
  return `
    <article class="layer-card ${layer.visible ? "is-active" : ""}">
      <div class="layer-card-head">
        <div>
          <span class="layer-dot" style="--swatch:${escapeHtml(layer.color)}"></span>
          <strong>${escapeHtml(layer.label)}</strong>
        </div>
        <span class="layer-count">${layer.itemCount}개</span>
      </div>
      <p>${escapeHtml(EXAMPLE_LAYER_HINT[layer.id] ?? layer.description)}</p>
      <div class="layer-meta-row">
        <span>예시 레이어</span>
        <span>${layer.visible ? "지도에 표시 중" : "꺼짐"}</span>
      </div>
      <label class="layer-opacity-control">
        <span>투명도</span>
        <input
          type="range"
          min="20"
          max="100"
          step="5"
          value="${Math.round(Number(layer.opacity ?? 1) * 100)}"
          data-action="set-local-layer-opacity"
          data-layer-id="${escapeHtml(layer.id)}"
        />
        <strong>${Math.round(Number(layer.opacity ?? 1) * 100)}%</strong>
      </label>
      <div class="layer-actions">
        <button type="button" class="ghost-button compact-button" data-action="toggle-local-layer" data-layer-id="${escapeHtml(layer.id)}">
          ${layer.visible ? "숨기기" : "보이기"}
        </button>
        <button type="button" class="ghost-button compact-button" data-action="focus-local-layer" data-layer-id="${escapeHtml(layer.id)}">
          범위 보기
        </button>
      </div>
    </article>
  `;
}

function buildQuickActionCard(card, escapeHtml) {
  return `
    <article class="quick-action-card ${card.priority ? "is-primary" : ""} ${card.compact ? "is-compact" : ""}">
      <div class="quick-action-copy">
        <div class="quick-action-head">
          <strong>${escapeHtml(card.title)}</strong>
          <span class="layer-count">${escapeHtml(card.badge)}</span>
        </div>
        <p>${escapeHtml(card.description)}</p>
      </div>
      <button
        type="button"
        class="${card.priority ? "primary-button" : "ghost-button"} compact-button"
        data-action="${escapeHtml(card.action)}"
        ${card.metricId ? `data-metric-id="${escapeHtml(card.metricId)}"` : ""}
        ${card.profileId ? `data-profile-id="${escapeHtml(card.profileId)}"` : ""}
        ${card.disabled ? "disabled" : ""}
      >
        ${escapeHtml(card.actionLabel)}
      </button>
    </article>
  `;
}

function buildPresetCard(preset, escapeHtml) {
  return `
    <article class="layer-card">
      <div class="layer-card-head">
        <div>
          <span class="layer-dot" style="--swatch:${escapeHtml(preset.color)}"></span>
          <strong>${escapeHtml(preset.label)}</strong>
        </div>
        <span class="layer-count">${escapeHtml(preset.scopeLabel)}</span>
      </div>
      <p>${escapeHtml(preset.description)}</p>
      <div class="layer-actions">
        <button type="button" class="ghost-button compact-button" data-preset-id="${escapeHtml(preset.id)}">
          바로 추가
        </button>
      </div>
    </article>
  `;
}

function buildMeasurementRows(measurementSummary, escapeHtml) {
  if (!measurementSummary) {
    return "";
  }

  const items = [
    measurementSummary.totalLengthLabel
      ? `<span>총 길이 ${escapeHtml(measurementSummary.totalLengthLabel)}</span>`
      : "",
    measurementSummary.totalAreaLabel
      ? `<span>면적 ${escapeHtml(measurementSummary.totalAreaLabel)}</span>`
      : "",
    measurementSummary.totalPerimeterLabel
      ? `<span>둘레 ${escapeHtml(measurementSummary.totalPerimeterLabel)}</span>`
      : "",
  ].filter(Boolean);

  return items.length
    ? `<div class="layer-meta-row layer-measurement-row">${items.join("")}</div>`
    : "";
}

function buildMetricSummary(metricSummary, escapeHtml) {
  if (!metricSummary) {
    return "";
  }

  const bars = metricSummary.bins
    .map(
      (bin) => `
        <span
          class="mini-chart-bar"
          style="--bar-height:${Number(bin.heightPercent)}%"
          title="${escapeHtml(`${bin.index + 1}구간: ${bin.count}개`)}"
        ></span>
      `,
    )
    .join("");

  return `
    <div class="layer-stat-summary">
      <div class="layer-stat-head">
        <strong>${escapeHtml(metricSummary.label)} ${escapeHtml(metricSummary.year)}</strong>
        <span>${Number(metricSummary.count).toLocaleString("ko-KR")}개 구역</span>
      </div>
      <div class="mini-chart" aria-label="통계값 분포">${bars}</div>
      <div class="layer-meta-row">
        <span>평균 ${escapeHtml(metricSummary.averageLabel)}</span>
        <span>최소 ${escapeHtml(metricSummary.minLabel)}</span>
        <span>최대 ${escapeHtml(metricSummary.maxLabel)}</span>
      </div>
    </div>
  `;
}

function buildGridSummary(gridSummary, escapeHtml) {
  if (!gridSummary) {
    return "";
  }

  const rows = gridSummary.rows
    .map(
      (row) => `
        <li>
          <strong>${escapeHtml(row.title)}</strong>
          <span>${escapeHtml(row.valueLabel)}</span>
          <small>${escapeHtml(row.sourceLabel)}</small>
        </li>
      `,
    )
    .join("");

  return `
    <div class="layer-grid-summary">
      <div class="layer-stat-head">
        <strong>${escapeHtml(gridSummary.gridLevelLabel)} 격자 셀 정보</strong>
        <span>${Number(gridSummary.totalCount).toLocaleString("ko-KR")}개 셀</span>
      </div>
      <div class="layer-meta-row">
        <span>${escapeHtml(gridSummary.metricLabel)} ${escapeHtml(gridSummary.metricYear)}</span>
        <span>값 있음 ${Number(gridSummary.withMetricCount).toLocaleString("ko-KR")}개</span>
        <span>값 없음 ${Number(gridSummary.missingMetricCount).toLocaleString("ko-KR")}개</span>
      </div>
      <ol class="grid-cell-list">${rows}</ol>
    </div>
  `;
}

function buildSuitabilitySummary(suitabilitySummary, escapeHtml) {
  if (!suitabilitySummary) {
    return "";
  }

  const rows = suitabilitySummary.topCandidates?.length
    ? suitabilitySummary.topCandidates
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
    <div class="layer-suitability-summary">
      <div class="layer-stat-head">
        <strong>${escapeHtml(suitabilitySummary.templateLabel)}</strong>
        <span>상위 후보</span>
      </div>
      <div class="layer-meta-row">
        ${suitabilitySummary.baseGridLayerName ? `<span>격자: ${escapeHtml(suitabilitySummary.baseGridLayerName)}</span>` : ""}
        ${suitabilitySummary.studentLayerName ? `<span>학생 레이어: ${escapeHtml(suitabilitySummary.studentLayerName)}</span>` : ""}
      </div>
      <ol class="grid-cell-list">${rows}</ol>
    </div>
  `;
}

function buildImportedLayerCard(layer, escapeHtml) {
  return `
    <article class="layer-card ${layer.visible ? "is-active" : ""}">
      <div class="layer-card-head">
        <div>
          <span class="layer-dot" style="--swatch:${escapeHtml(layer.color)}"></span>
          <strong>${escapeHtml(layer.name)}</strong>
        </div>
        <span class="layer-count">${layer.featureCount}개</span>
      </div>
      <p>${escapeHtml(layer.description)}</p>
      <div class="layer-meta-row">
        <span>${escapeHtml(layer.sourceLabel)}</span>
        <span>${escapeHtml(layer.scopeLabel)}</span>
      </div>
      ${buildMeasurementRows(layer.measurementSummary, escapeHtml)}
      ${buildMetricSummary(layer.metricSummary, escapeHtml)}
      ${buildGridSummary(layer.gridSummary, escapeHtml)}
      ${buildSuitabilitySummary(layer.suitabilitySummary, escapeHtml)}
      <label class="layer-opacity-control">
        <span>투명도</span>
        <input
          type="range"
          min="20"
          max="100"
          step="5"
          value="${Math.round(Number(layer.opacity ?? 1) * 100)}"
          data-action="set-imported-public-opacity"
          data-layer-id="${escapeHtml(layer.id)}"
        />
        <strong>${Math.round(Number(layer.opacity ?? 1) * 100)}%</strong>
      </label>
      <div class="layer-actions">
        <button type="button" class="ghost-button compact-button" data-action="toggle-imported-public" data-layer-id="${escapeHtml(layer.id)}">
          ${layer.visible ? "숨기기" : "보이기"}
        </button>
        <button type="button" class="ghost-button compact-button" data-action="focus-imported-public" data-layer-id="${escapeHtml(layer.id)}">
          범위 보기
        </button>
        <button type="button" class="ghost-button compact-button" data-action="edit-imported-public" data-layer-id="${escapeHtml(layer.id)}">
          정보 수정
        </button>
        <button type="button" class="ghost-button compact-button" data-action="export-imported-public" data-layer-id="${escapeHtml(layer.id)}">
          내보내기
        </button>
        <button type="button" class="ghost-button compact-button" data-action="move-imported-public-up" data-layer-id="${escapeHtml(layer.id)}">
          위로
        </button>
        <button type="button" class="ghost-button compact-button" data-action="move-imported-public-down" data-layer-id="${escapeHtml(layer.id)}">
          아래로
        </button>
        <button type="button" class="ghost-button compact-button danger-button" data-action="delete-imported-public" data-layer-id="${escapeHtml(layer.id)}">
          삭제
        </button>
      </div>
    </article>
  `;
}

function syncPublicSectionStates(elements, viewModel) {
  if (elements.publicExampleFoldHint) {
    elements.publicExampleFoldHint.textContent = `${viewModel.exampleLayers.activeCount}/${viewModel.exampleLayers.totalCount}`;
  }

  if (elements.importedPublicSection) {
    elements.importedPublicSection.open = viewModel.importedLayers.length > 0;
  }

  if (elements.importedPublicFoldHint) {
    elements.importedPublicFoldHint.textContent = viewModel.importedLayers.length
      ? `${viewModel.importedLayers.length}개`
      : "없음";
  }
}

export function renderPublicPanelView({ elements, viewModel, escapeHtml }) {
  elements.schoolPublicBlock.hidden = false;
  elements.nationalPublicBlock.hidden = true;
  elements.publicLayerSummary.textContent = viewModel.summaryText;

  elements.schoolSgisQuickBlock.hidden = !viewModel.sgisEnabled;
  elements.sgisImportBlock.hidden = !viewModel.sgisEnabled;
  elements.schoolReferenceToggle.classList.toggle("is-active", viewModel.schoolReferenceActive);
  elements.schoolReferenceToggle.textContent = viewModel.schoolReferenceActive ? "켜짐" : "꺼짐";
  elements.schoolSgisTopicHint.textContent = viewModel.sgisQuick.topicHint;
  elements.schoolSgisRegionSummary.textContent = viewModel.sgisQuick.regionSummary;
  elements.sgisHelpCopy.textContent =
    viewModel.sgisQuick.selectedProfile.availabilityHint || viewModel.sgisHelpText;
  if (elements.sgisProfileSubmitButton) {
    elements.sgisProfileSubmitButton.disabled =
      !viewModel.locationLocked || Boolean(viewModel.sgisImportPending);
    elements.sgisProfileSubmitButton.textContent = viewModel.sgisQuick.selectedProfile.actionLabel;
  }
  if (elements.simplePublicSubmitButton) {
    const simpleActionDisabled = !viewModel.locationLocked || Boolean(viewModel.sgisImportPending);
    elements.simplePublicSubmitButton.disabled =
      simpleActionDisabled;
    elements.simplePublicSubmitButton.textContent = viewModel.locationLocked
      ? viewModel.sgisQuick.selectedProfile.actionLabel
      : "위치 검색 후 추가 가능";
  }

  elements.sgisMetricRecommendationList.innerHTML = viewModel.sgisQuick.metricRecommendations
    .map(
      (metric) => `
        <button
          type="button"
          class="filter-chip ${metric.isActive ? "is-active" : ""}"
          data-action="select-sgis-metric"
          data-metric-id="${escapeHtml(metric.id)}"
          title="${escapeHtml(metric.helper)}"
        >
          ${escapeHtml(metric.label)}
        </button>
      `,
    )
    .join("");

  elements.schoolSgisQuickActions.innerHTML = viewModel.sgisQuick.cards
    .map((card) => buildQuickActionCard({ ...card, compact: true }, escapeHtml))
    .join("");

  elements.publicStarterCard.innerHTML = `
    <article class="public-starter-card">
      <p class="eyebrow">Examples</p>
      <h3>기본/예시 레이어</h3>
      <p>예시 레이어는 기능 연습용입니다. 실제 수업에서는 SGIS나 학생 벡터 레이어와 비교해 보세요.</p>
      <div class="public-starter-meta">
        <span class="mission-status">${viewModel.exampleLayers.activeCount} / ${viewModel.exampleLayers.totalCount}개 켜짐</span>
      </div>
      <div class="workspace-actions">
        <button type="button" class="ghost-button" data-action="enable-all-example-layers">예시 레이어 모두 켜기</button>
        <button type="button" class="ghost-button" data-action="clear-school-public">예시 레이어 모두 끄기</button>
      </div>
    </article>
  `;

  elements.recommendedLocalLayerList.innerHTML = viewModel.exampleLayers.layers
    .map((layer) => buildExampleLayerCard(layer, escapeHtml))
    .join("");

  elements.publicPresetSection.hidden = viewModel.presetLayers.length === 0;
  elements.publicPresetList.innerHTML = viewModel.presetLayers
    .map((preset) => buildPresetCard(preset, escapeHtml))
    .join("");

  elements.importedPublicLayerList.innerHTML = viewModel.importedLayers.length
    ? viewModel.importedLayers.map((layer) => buildImportedLayerCard(layer, escapeHtml)).join("")
    : `
      <div class="empty-state">
        <strong>가져온 공공 레이어가 없습니다.</strong>
        <p>위쪽에서 SGIS를 추가하거나 추천 링크 레이어를 불러오세요.</p>
      </div>
    `;

  syncPublicSectionStates(elements, viewModel);

  elements.nationalSummary.innerHTML = "";
  elements.nationalRankingList.innerHTML = "";
  elements.nationalDatasetFilters.innerHTML = "";
  elements.nationalYearFilters.innerHTML = "";
  elements.nationalFacilityFilters.innerHTML = "";
}

export function bindPublicPanelEvents({
  elements,
  onExampleStarterAction,
  onQuickSgisAction,
  onExampleLayerAction,
  onSchoolReferenceToggle,
  onSgisSubmit,
  onSgisControlChange,
  onPublicImportSubmit,
  onPresetImport,
  onImportedLayerAction,
}) {
  elements.publicStarterCard?.addEventListener("click", (event) => {
    const button = event.target.closest("[data-action]");
    if (!button) {
      return;
    }
    if (button.disabled) {
      return;
    }

    onExampleStarterAction(button.dataset.action);
  });

  elements.schoolSgisQuickActions?.addEventListener("click", (event) => {
    const button = event.target.closest("[data-action]");
    if (!button) {
      return;
    }
    if (button.disabled) {
      return;
    }

    onQuickSgisAction({
      action: button.dataset.action,
      metricId: button.dataset.metricId,
      profileId: button.dataset.profileId,
    });
  });

  elements.recommendedLocalLayerList?.addEventListener("click", (event) => {
    const button = event.target.closest("[data-action]");
    if (!button) {
      return;
    }

    onExampleLayerAction({
      action: button.dataset.action,
      layerId: button.dataset.layerId,
    });
  });

  elements.recommendedLocalLayerList?.addEventListener("input", (event) => {
    const field = event.target.closest("[data-action='set-local-layer-opacity']");
    if (!field) {
      return;
    }

    onExampleLayerAction({
      action: field.dataset.action,
      layerId: field.dataset.layerId,
      value: Number(field.value) / 100,
    });
  });

  elements.schoolReferenceToggle?.addEventListener("click", () => {
    onSchoolReferenceToggle();
  });

  elements.sgisLayerForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    await onSgisSubmit();
  });

  [
    elements.sgisMetricField,
    elements.sgisYearField,
    elements.sgisColorField,
    elements.sgisProfileField,
  ]
    .filter(Boolean)
    .forEach((field) => {
      field.addEventListener("change", () => {
        onSgisControlChange();
      });
    });

  elements.publicLayerImportForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    await onPublicImportSubmit();
  });

  elements.publicPresetList?.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-preset-id]");
    if (!button) {
      return;
    }

    await onPresetImport(button.dataset.presetId);
  });

  elements.importedPublicLayerList?.addEventListener("click", (event) => {
    const button = event.target.closest("[data-action]");
    if (!button) {
      return;
    }

    onImportedLayerAction({
      action: button.dataset.action,
      layerId: button.dataset.layerId,
    });
  });

  elements.importedPublicLayerList?.addEventListener("input", (event) => {
    const field = event.target.closest("[data-action='set-imported-public-opacity']");
    if (!field) {
      return;
    }

    onImportedLayerAction({
      action: field.dataset.action,
      layerId: field.dataset.layerId,
      value: Number(field.value) / 100,
    });
  });
}
