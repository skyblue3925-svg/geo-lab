export function normalizeWorkspaceValues(rawValues, { fallbackConfig, parseFiniteNumber, parsePositiveInteger }) {
  return {
    schoolName: rawValues.schoolName.trim() || fallbackConfig.schoolName,
    lat: parseFiniteNumber(rawValues.lat, fallbackConfig.mapCenter.lat),
    lng: parseFiniteNumber(rawValues.lng, fallbackConfig.mapCenter.lng),
    radiusMeters: parsePositiveInteger(
      rawValues.radiusMeters,
      fallbackConfig.schoolRadiusMeters,
    ),
    topic: "general",
  };
}

export function buildWorkspaceUrl(values, viewMode, normalizeValues) {
  const normalized = normalizeValues(values);
  const url = new URL(window.location.href);
  url.searchParams.set("school", normalized.schoolName);
  url.searchParams.set("lat", String(normalized.lat));
  url.searchParams.set("lng", String(normalized.lng));
  url.searchParams.set("radius", String(normalized.radiusMeters));
  url.searchParams.set("topic", normalized.topic);
  if (viewMode === "korea") {
    url.searchParams.set("view", "korea");
  } else {
    url.searchParams.delete("view");
  }
  return url.toString();
}

export function buildWorkspaceShareState(values, { viewMode, buildUrl }) {
  return {
    link: buildUrl(values, viewMode),
    summary: `${values.schoolName} · 반경 ${(values.radiusMeters / 1000).toFixed(1)}km · 공유 링크 준비 완료`,
  };
}

export function buildWorkspaceRegionCacheKey(values) {
  return `${values.lat.toFixed(6)}:${values.lng.toFixed(6)}`;
}

export function buildWorkspacePanelViewModel({ values, viewMode, searchPending, searchResults, buildUrl }) {
  const shareState = buildWorkspaceShareState(values, {
    viewMode,
    buildUrl,
  });

  return {
    searchPending,
    searchResults: searchResults.map((result) => ({
      id: result.id,
      name: result.name,
      subtitle: result.subtitle,
    })),
    shareLink: shareState.link,
    shareSummary: shareState.summary,
  };
}
