export function renderWorkspacePanelView({ elements, viewModel, escapeHtml }) {
  elements.workspaceSearchButton.disabled = viewModel.searchPending;
  elements.workspaceSearchButton.textContent = viewModel.searchPending ? "검색 중..." : "지도에서 찾기";

  if (elements.locationSearchButton) {
    elements.locationSearchButton.disabled = viewModel.searchPending;
    elements.locationSearchButton.textContent = viewModel.searchPending ? "검색 중..." : "찾기";
  }

  elements.workspaceShareLinkField.value = viewModel.shareLink;
  elements.workspaceSummary.textContent = viewModel.shareSummary;

  if (!viewModel.searchResults.length) {
    elements.workspaceSearchResults.hidden = true;
    elements.workspaceSearchResults.innerHTML = "";

    if (elements.locationSearchResults) {
      elements.locationSearchResults.hidden = true;
      elements.locationSearchResults.innerHTML = "";
    }

    return;
  }

  const searchResultHtml = viewModel.searchResults
    .map(
      (result) => `
        <button
          type="button"
          class="search-result-card"
          data-search-result-id="${escapeHtml(result.id)}"
        >
          <strong>${escapeHtml(result.name)}</strong>
          <span>${escapeHtml(result.subtitle)}</span>
        </button>
      `,
    )
    .join("");

  elements.workspaceSearchResults.hidden = false;
  elements.workspaceSearchResults.innerHTML = searchResultHtml;

  if (elements.locationSearchResults) {
    elements.locationSearchResults.hidden = false;
    elements.locationSearchResults.innerHTML = searchResultHtml;
  }
}

export function bindWorkspacePanelEvents({
  elements,
  onPresetChange,
  onSearchSubmit,
  onSearchResultPick,
  onWorkspaceFieldSync,
  onUseMapCenter,
  onWorkspaceSubmit,
  onCopyWorkspaceLink,
  onResetWorkspace,
}) {
  elements.workspacePresetField?.addEventListener("change", () => {
    onPresetChange(elements.workspacePresetField.value);
  });

  elements.locationSearchButton?.addEventListener("click", () => {
    void onSearchSubmit();
  });

  elements.locationSearchField?.addEventListener("keydown", (event) => {
    if (event.key !== "Enter") {
      return;
    }

    event.preventDefault();
    void onSearchSubmit();
  });

  elements.workspaceSearchButton?.addEventListener("click", () => {
    void onSearchSubmit();
  });

  elements.workspaceSchoolNameField?.addEventListener("keydown", (event) => {
    if (event.key !== "Enter") {
      return;
    }

    event.preventDefault();
    void onSearchSubmit();
  });

  [elements.workspaceSearchResults, elements.locationSearchResults].forEach((container) => {
    container?.addEventListener("click", (event) => {
      const button = event.target.closest("[data-search-result-id]");
      if (!button) {
        return;
      }

      onSearchResultPick(button.dataset.searchResultId);
    });
  });

  ["input", "change"].forEach((eventName) => {
    elements.workspaceForm?.addEventListener(eventName, (event) => {
      if (event.target === elements.workspacePresetField) {
        return;
      }

      onWorkspaceFieldSync({
        unlockReference:
          event.target === elements.workspaceLatField
          || event.target === elements.workspaceLngField,
      });
    });
  });

  elements.useMapCenterButton?.addEventListener("click", () => {
    onUseMapCenter();
  });

  elements.workspaceForm?.addEventListener("submit", (event) => {
    event.preventDefault();
    onWorkspaceSubmit();
  });

  elements.copyWorkspaceLinkButton?.addEventListener("click", async () => {
    await onCopyWorkspaceLink();
  });

  elements.resetWorkspaceButton?.addEventListener("click", () => {
    onResetWorkspace();
  });
}
