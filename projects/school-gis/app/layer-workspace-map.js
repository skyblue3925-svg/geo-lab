import {
  escapeHtml,
  formatNumber,
  interpolateColor,
} from "./layer-workspace-data.js";

import {
  buildStudentLayerFeatureCollection,
  getStudentGeometryLabel,
} from "./domain/student-layer.js";

const KAKAO_SDK_ID = "school-gis-kakao-sdk";
const KAKAO_DEFAULT_LIBRARIES = ["services"];
const KAKAO_MIN_LEVEL = 1;
const KAKAO_MAX_LEVEL = 14;
const PSEUDO_ZOOM_BASE = 18;
const KAKAO_OVERLAY_IDS = ["traffic", "bicycle", "terrain", "district"];

let kakaoSdkPromise = null;
let renderObjectIdSeed = 0;
const renderObjectIds = new WeakMap();

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function pseudoZoomToKakaoLevel(zoom) {
  return clamp(Math.round(PSEUDO_ZOOM_BASE - Number(zoom ?? 14)), KAKAO_MIN_LEVEL, KAKAO_MAX_LEVEL);
}

function kakaoLevelToPseudoZoom(level) {
  return PSEUDO_ZOOM_BASE - Number(level ?? 4);
}

function toPlainLatLng(value) {
  if (Array.isArray(value)) {
    return {
      lat: Number(value[0]),
      lng: Number(value[1]),
    };
  }

  return {
    lat: Number(value?.lat ?? value?.getLat?.()),
    lng: Number(value?.lng ?? value?.getLng?.()),
  };
}

function buildReferenceAreaCoordinates(location, radiusMeters) {
  const { lat, lng } = toPlainLatLng(location);
  const radius = Math.max(50, Number(radiusMeters ?? 0));
  if (!Number.isFinite(lat) || !Number.isFinite(lng)) {
    return [];
  }

  const latDelta = radius / 111320;
  const lngDelta = radius / (111320 * Math.max(0.2, Math.cos((lat * Math.PI) / 180)));
  return [
    { lat: lat - latDelta, lng: lng - lngDelta },
    { lat: lat - latDelta, lng: lng + lngDelta },
    { lat: lat + latDelta, lng: lng - lngDelta },
    { lat: lat + latDelta, lng: lng + lngDelta },
  ];
}

function getRenderObjectId(value) {
  if (!value || typeof value !== "object") {
    return String(value ?? "");
  }

  let objectId = renderObjectIds.get(value);
  if (!objectId) {
    objectId = `obj-${++renderObjectIdSeed}`;
    renderObjectIds.set(value, objectId);
  }

  return objectId;
}

function createRenderCache() {
  return {
    reference: "",
    localPublic: "",
    importedPublic: "",
    nationalStats: "",
    nationalFacilities: "",
    studentLayers: "",
    draft: "",
  };
}

function renderSliceIfChanged(cache, key, signature, renderFn) {
  if (cache[key] === signature) {
    return;
  }

  cache[key] = signature;
  renderFn();
}

function getSelectedFeatureSignature(selectedFeatureRef) {
  if (!selectedFeatureRef?.layerId || !selectedFeatureRef?.featureId) {
    return "none";
  }

  return `${selectedFeatureRef.layerId}:${selectedFeatureRef.featureId}`;
}

function getReferenceAreaSignature(state, appConfig) {
  return [
    state.viewMode,
    state.showSchoolReference ? "visible" : "hidden",
    Number(state.referenceLocation?.lat ?? appConfig.mapCenter.lat).toFixed(6),
    Number(state.referenceLocation?.lng ?? appConfig.mapCenter.lng).toFixed(6),
    Number(state.referenceRadiusMeters ?? appConfig.schoolRadiusMeters),
    String(state.referenceLabel ?? appConfig.schoolName),
  ].join("|");
}

function getLocalPublicLayersSignature(state, localPublicLayers) {
  if (state.viewMode !== "school") {
    return `hidden|${state.viewMode}`;
  }

  return localPublicLayers
    .map(
      (layer) =>
        `${layer.id}:${state.localPublicVisibility[layer.id] ? "visible" : "hidden"}:${Number(
          state.localPublicOpacity?.[layer.id] ?? 1,
        ).toFixed(2)}:${getRenderObjectId(layer)}`,
    )
    .join("|");
}

function getImportedPublicLayersSignature(state) {
  return [
    state.viewMode,
    ...state.importedPublicLayers
      .filter((layer) => layer.visible)
      .filter((layer) => layer.scope === "both" || layer.scope === state.viewMode)
      .map(
        (layer) =>
          [
            layer.id,
            getRenderObjectId(layer),
            getRenderObjectId(layer.featureCollection),
            layer.scope,
            layer.color,
          ].join(":"),
      ),
  ].join("|");
}

function getNationalStatsSignature(state, getNationalDataset) {
  if (state.viewMode !== "korea" || !state.showNationalStats) {
    return `hidden|${state.viewMode}`;
  }

  const dataset = getNationalDataset(state);
  return [
    state.viewMode,
    state.selectedNationalDatasetId,
    state.selectedNationalYear,
    getRenderObjectId(dataset),
  ].join("|");
}

function getNationalFacilitiesSignature(state) {
  if (state.viewMode !== "korea") {
    return `hidden|${state.viewMode}`;
  }

  return [
    state.viewMode,
    ...[...state.activeNationalFacilityLayerIds].sort(),
  ].join("|");
}

function getStudentLayersSignature(state) {
  return [
    getSelectedFeatureSignature(state.selectedFeatureRef),
    ...state.studentLayers
      .filter((layer) => layer.visible)
      .map((layer) => `${layer.id}:${getRenderObjectId(layer)}`),
  ].join("|");
}

function getDraftGeometrySignature(state) {
  if (!state.draftGeometry || !state.activeLayerId) {
    return `none|${state.activeTool}|${state.activeLayerId ?? ""}`;
  }

  const points = (state.draftGeometry.points ?? [])
    .map((point) => `${Number(point.lat).toFixed(6)},${Number(point.lng).toFixed(6)}`)
    .join(";");

  return [
    state.activeLayerId,
    state.activeTool,
    state.draftGeometry.geometryType,
    points,
  ].join("|");
}

function buildPopup(title, pills, lines) {
  return `
    <div class="popup-card">
      <button type="button" class="popup-close-button" data-popup-close aria-label="정보 닫기">닫기</button>
      <div class="popup-pills">${pills
        .map(
          (pill) =>
            `<span class="popup-pill"${
              pill.color ? ` style="--pill-color:${escapeHtml(pill.color)}"` : ""
            }>${escapeHtml(pill.label)}</span>`,
        )
        .join("")}</div>
      <strong>${escapeHtml(title)}</strong>
      ${lines.map((line) => `<p>${line}</p>`).join("")}
    </div>
  `;
}

function getImportedFeatureTitle(layer, properties) {
  if (properties.isGridFeature || properties.gridLevelDiv || properties.gridCode) {
    const gridTitle = [properties.gridSizeLabel ?? properties.gridLevelDiv, "격자", properties.gridCode]
      .filter(Boolean)
      .join(" ");
    return properties.title ?? (gridTitle || layer.name);
  }

  return properties.title ?? properties.name ?? properties.adm_nm ?? layer.name;
}

function getImportedFeatureTypeLabel(properties) {
  if (properties.isGridFeature || properties.gridLevelDiv || properties.gridCode) {
    return "SGIS 격자";
  }
  if (properties.source === "SGIS") {
    return "SGIS 통계";
  }
  return "공공 레이어";
}

function buildImportedLayerPopupLines(properties, fallbackNote) {
  const lines = [];
  const isGridFeature = properties.isGridFeature || properties.gridLevelDiv || properties.gridCode;

  if (isGridFeature) {
    if (properties.gridCode) {
      lines.push(`<b>격자 코드:</b> ${escapeHtml(properties.gridCode)}`);
    }
    if (properties.gridSizeLabel || properties.gridLevelDiv) {
      lines.push(`<b>격자 크기:</b> ${escapeHtml(properties.gridSizeLabel ?? properties.gridLevelDiv)}`);
    }
    if (properties.gridIndex) {
      lines.push(`<b>레이어 내 순번:</b> ${escapeHtml(String(properties.gridIndex))}`);
    }
  }

  if (properties.metricLabel && Number.isFinite(Number(properties.metricValue))) {
    lines.push(
      `<b>${escapeHtml(properties.metricLabel)}:</b> ${formatNumber(
        Number(properties.metricValue),
        Number(properties.metricDigits ?? 0),
      )}${escapeHtml(properties.metricUnit ?? "")}`,
    );
  } else if (isGridFeature && properties.metricLabel) {
    lines.push(`<b>${escapeHtml(properties.metricLabel)}:</b> 격자별 통계값 없음`);
  }

  if (properties.metricYear) {
    lines.push(`<b>기준연도:</b> ${escapeHtml(properties.metricYear)}`);
  }
  if (isGridFeature && properties.metricSourceLabel) {
    lines.push(`<b>자료 기준:</b> ${escapeHtml(properties.metricSourceLabel)}`);
  }
  if (isGridFeature && (properties.joinedAdmNm || properties.joinedAdmCd)) {
    lines.push(
      `<b>결합 행정구역:</b> ${escapeHtml(
        [properties.joinedAdmNm, properties.joinedAdmCd].filter(Boolean).join(" "),
      )}`,
    );
  }

  if (properties.lengthLabel) {
    lines.push(`<b>길이:</b> ${escapeHtml(properties.lengthLabel)}`);
  }
  if (properties.areaLabel) {
    lines.push(`<b>면적:</b> ${escapeHtml(properties.areaLabel)}`);
  }
  if (properties.perimeterLabel) {
    lines.push(`<b>둘레:</b> ${escapeHtml(properties.perimeterLabel)}`);
  }

  lines.push(escapeHtml(fallbackNote));
  return lines;
}

function buildImportedPopup(layer, feature) {
  const properties = feature?.properties ?? {};
  const title = getImportedFeatureTitle(layer, properties);
  const note = properties.note ?? properties.description ?? layer.description ?? "설명 없음";
  return buildPopup(
    title,
    [
      { label: layer.name, color: layer.color },
      { label: getImportedFeatureTypeLabel(properties) },
    ],
    buildImportedLayerPopupLines(properties, note),
  );
}

function buildImportedFeatureStyle(layer, feature) {
  const style = feature?.properties?.__style ?? {};
  const layerOpacity = clamp(Number(layer?.opacity ?? 1), 0, 1);
  return {
    color: style.color ?? layer.color,
    weight: style.weight ?? 3,
    opacity: (style.opacity ?? 0.9) * layerOpacity,
    fillColor: style.fillColor ?? layer.color,
    fillOpacity: (style.fillOpacity ?? 0.15) * layerOpacity,
  };
}

function buildStudentFeatureStyle(layer, selected = false) {
  const layerOpacity = clamp(Number(layer?.opacity ?? 1), 0, 1);
  return {
    color: layer.color,
    weight: selected ? 6 : 4,
    opacity: 0.92 * layerOpacity,
    fillColor: layer.color,
    fillOpacity: (selected ? 0.26 : 0.16) * layerOpacity,
  };
}

function isSelectedStudentFeature(selectedFeatureRef, feature) {
  return Boolean(
    selectedFeatureRef
    && feature?.properties?.featureId
    && selectedFeatureRef.layerId === feature.properties.layerId
    && selectedFeatureRef.featureId === feature.properties.featureId,
  );
}

function buildStudentPopupLines(properties) {
  const lines = [];
  if (properties.categoryLabel) {
    lines.push(`<b>카테고리:</b> ${escapeHtml(properties.categoryLabel)}`);
  }
  const observedLabel = String(properties.observedLabel ?? "").trim();
  const observedValue = String(properties.observedValue ?? "").trim();
  const observedUnit = String(properties.observedUnit ?? "").trim();
  if (observedLabel || observedValue) {
    const observedText = [
      observedLabel,
      [observedValue, observedUnit].filter(Boolean).join(" "),
    ].filter(Boolean).join(": ");
    lines.push(`<b>속성값:</b> ${escapeHtml(observedText)}`);
  }
  if (properties.lengthLabel) {
    lines.push(`<b>길이:</b> ${escapeHtml(properties.lengthLabel)}`);
  }
  if (properties.areaLabel) {
    lines.push(`<b>면적:</b> ${escapeHtml(properties.areaLabel)}`);
  }
  if (properties.perimeterLabel) {
    lines.push(`<b>둘레:</b> ${escapeHtml(properties.perimeterLabel)}`);
  }
  lines.push(escapeHtml(properties.note || "메모 없음"));
  return lines;
}

function buildStudentPopup(layer, feature) {
  const properties = feature.properties ?? {};
  const severityLabel = properties.severityLabel;
  const geometryType = properties.featureGeometryType ?? properties.layerGeometryType ?? layer.geometryType;
  const lines = buildStudentPopupLines(properties);
  if (feature.geometry?.type === "Point" && Array.isArray(feature.geometry.coordinates)) {
    const [lng, lat] = feature.geometry.coordinates;
    if (Number.isFinite(Number(lat)) && Number.isFinite(Number(lng))) {
      lines.unshift(
        `<b>좌표:</b> ${escapeHtml(Number(lat).toFixed(6))}, ${escapeHtml(Number(lng).toFixed(6))}`,
      );
    }
  }
  return buildPopup(
    properties.title ?? layer.name,
    [
      { label: layer.name, color: layer.color },
      { label: "학생 조사" },
      { label: `${getStudentGeometryLabel(geometryType)} 객체` },
      ...(severityLabel ? [{ label: severityLabel }] : []),
    ],
    lines,
  );
}

function ensureMapContainer(mapId) {
  const element = document.getElementById(mapId);
  if (!element) {
    throw new Error(`Map container "#${mapId}" was not found.`);
  }
  return element;
}

function createStatusController(container) {
  const node = document.createElement("div");
  node.className = "map-status";
  node.hidden = true;
  container.appendChild(node);

  return {
    show(message, tone = "info") {
      node.hidden = false;
      node.dataset.tone = tone;
      node.innerHTML = `<strong>${tone === "error" ? "지도 오류" : "지도 안내"}</strong><p>${escapeHtml(message)}</p>`;
    },
    hide() {
      node.hidden = true;
      node.dataset.tone = "info";
      node.innerHTML = "";
    },
  };
}

function createStubMapFacade(appConfig) {
  let center = { ...appConfig.mapCenter };
  let zoom = Number(appConfig.initialZoom);

  return {
    getCenter() {
      return { ...center };
    },
    getZoom() {
      return zoom;
    },
    flyTo(coords, nextZoom) {
      center = toPlainLatLng(coords);
      if (Number.isFinite(Number(nextZoom))) {
        zoom = Number(nextZoom);
      }
    },
  };
}

function createNoopWorkspaceMap(appConfig, status) {
  return {
    map: createStubMapFacade(appConfig),
    render() {},
    focusScope() {},
    focusLocation() {},
    fitCoordinates() {},
    fitReferenceArea() {},
    closePopup() {},
    showDraftCursor() {},
    setOverlayLayerIds() {},
    async searchPlaces() {
      status.show("카카오 지도 키를 넣으면 장소 검색과 한국형 지도를 바로 쓸 수 있습니다.", "warn");
      return [];
    },
  };
}

function createLeafletMarkerIcon(Leaflet, className, color, size) {
  return Leaflet.divIcon({
    className: "marker-wrapper",
    html: `<span class="${className}" style="--marker:${color}; --size:${size}px"></span>`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
    popupAnchor: [0, -10],
  });
}

function createLeafletWorkspaceMap({
  mapId,
  appConfig,
  koreaMapView,
  localPublicLayers,
  nationalFacilityLayers,
  getNationalDataset,
  getNationalPointValue,
  getNationalStats,
  getNationalGradient,
  onMapClick,
  onStudentFeatureInteract,
  onNationalPointSelect,
  statusMessage = "",
}) {
  const Leaflet = window.L;
  const mapContainer = ensureMapContainer(mapId);
  const status = createStatusController(mapContainer);
  const getLocalPublicLayers = typeof localPublicLayers === "function"
    ? localPublicLayers
    : () => localPublicLayers ?? [];
  const renderCache = createRenderCache();

  if (!Leaflet) {
    status.show("기본 지도를 불러오지 못했습니다. 페이지를 새로고침해 주세요.", "error");
    return createNoopWorkspaceMap(appConfig, status);
  }

  const map = Leaflet.map(mapId, { zoomControl: false, minZoom: 6 }).setView(
    [appConfig.mapCenter.lat, appConfig.mapCenter.lng],
    appConfig.initialZoom,
  );

  Leaflet.control.zoom({ position: "bottomright" }).addTo(map);
  const tileLayer = Leaflet.tileLayer(appConfig.mapTile.url, {
    attribution: appConfig.mapTile.attribution,
    maxZoom: 19,
  }).addTo(map);
  let baseMapMode = "default";
  let tileLoadCount = 0;
  let tileErrorCount = 0;

  if (statusMessage) {
    status.show(statusMessage, "warn");
  }

  tileLayer.on("load", () => {
    if (baseMapMode === "off") {
      return;
    }

    tileLoadCount += 1;
    if (!statusMessage && tileErrorCount === 0) {
      status.hide();
    }
  });

  tileLayer.on("tileerror", () => {
    tileErrorCount += 1;
    if (tileLoadCount > 0) {
      return;
    }

    status.show(
      "기본 OSM 타일을 불러오지 못했습니다. 새로고침하거나 백지도 설정을 다시 선택해 주세요.",
      "error",
    );
  });

  const groups = {
    schoolReference: Leaflet.layerGroup().addTo(map),
    localPublic: new Map(),
    importedPublic: new Map(),
    nationalStats: Leaflet.layerGroup().addTo(map),
    nationalFacilities: new Map(),
    studentLayers: new Map(),
    draftCursor: Leaflet.layerGroup().addTo(map),
  };

  mapContainer.addEventListener("click", (event) => {
    const closeButton = event.target.closest("[data-popup-close]");
    if (!closeButton) {
      return;
    }

    event.preventDefault();
    event.stopPropagation();
    map.closePopup();
  });

  map.on("click", (event) => onMapClick(event.latlng));
  map.whenReady(() => {
    map.invalidateSize();
  });
  window.requestAnimationFrame(() => map.invalidateSize());
  window.setTimeout(() => map.invalidateSize(), 250);
  window.setTimeout(() => map.invalidateSize(), 900);

  function renderReferenceArea(state) {
    groups.schoolReference.clearLayers();
    if (state.viewMode !== "school" || !state.showSchoolReference) {
      return;
    }

    const referenceLat = Number(state.referenceLocation?.lat ?? appConfig.mapCenter.lat);
    const referenceLng = Number(state.referenceLocation?.lng ?? appConfig.mapCenter.lng);
    const referenceRadius = Number(
      state.referenceRadiusMeters ?? appConfig.schoolRadiusMeters,
    );
    const referenceLabel = state.referenceLabel ?? appConfig.schoolName;

    Leaflet.circle([referenceLat, referenceLng], {
      radius: referenceRadius,
      color: "#184d42",
      weight: 2,
      fillColor: "#4ec08f",
      fillOpacity: 0.08,
    }).addTo(groups.schoolReference);

    Leaflet.circleMarker([referenceLat, referenceLng], {
      radius: 8,
      color: "#103d34",
      fillColor: "#f0bf55",
      fillOpacity: 1,
      weight: 3,
    })
      .bindTooltip(`${referenceLabel} 중심`, {
        direction: "top",
        offset: [0, -8],
      })
      .addTo(groups.schoolReference);
  }

  function renderLocalPublicLayers(state, currentLocalPublicLayers) {
    groups.localPublic.forEach((group) => group.remove());
    groups.localPublic.clear();
    if (state.viewMode !== "school") {
      return;
    }

    currentLocalPublicLayers
      .filter((layer) => state.localPublicVisibility[layer.id])
      .forEach((layer) => {
        const layerOpacity = clamp(Number(state.localPublicOpacity?.[layer.id] ?? 1), 0, 1);
        const group = Leaflet.layerGroup().addTo(map);
        layer.items.forEach((item) => {
          Leaflet.marker([item.lat, item.lng], {
            icon: createLeafletMarkerIcon(Leaflet, "public-marker", layer.color, 18),
            opacity: layerOpacity,
            keyboard: false,
          })
            .bindPopup(
              buildPopup(
                item.name,
                [
                  { label: layer.label, color: layer.color },
                  { label: item.type },
                ],
                [escapeHtml(item.note)],
              ),
            )
            .addTo(group);
        });
        groups.localPublic.set(layer.id, group);
      });
  }

  function renderNationalStats(state) {
    groups.nationalStats.clearLayers();
    if (state.viewMode !== "korea" || !state.showNationalStats) {
      return;
    }

    const dataset = getNationalDataset(state);
    const stats = getNationalStats(dataset, state.selectedNationalYear, getNationalPointValue);
    const gradient = getNationalGradient(dataset);
    const denominator = Math.max(1, stats.max - stats.min);

    dataset.points.forEach((point) => {
      const value = getNationalPointValue(point, state.selectedNationalYear);
      const ratio = (value - stats.min) / denominator;
      const color = interpolateColor(gradient.low, gradient.high, ratio);
      const size = 18 + ratio * 14;

      Leaflet.marker([point.lat, point.lng], {
        icon: createLeafletMarkerIcon(Leaflet, "public-marker", color, size),
        keyboard: false,
      })
        .bindPopup(
          buildPopup(
            point.name,
            [{ label: dataset.label }, { label: String(state.selectedNationalYear) }],
            [
              `<b>지표값:</b> ${formatNumber(value)}${escapeHtml(dataset.unit)}`,
              escapeHtml(point.note),
            ],
          ),
        )
        .on("click", () => onNationalPointSelect(point.id))
        .addTo(groups.nationalStats);
    });
  }

  function renderNationalFacilities(state) {
    groups.nationalFacilities.forEach((group) => group.remove());
    groups.nationalFacilities.clear();
    if (state.viewMode !== "korea") {
      return;
    }

    nationalFacilityLayers
      .filter(
        (layer) =>
          layer.id !== "none" && state.activeNationalFacilityLayerIds.includes(layer.id),
      )
      .forEach((layer) => {
        const group = Leaflet.layerGroup().addTo(map);
        layer.items.forEach((item) => {
          Leaflet.marker([item.lat, item.lng], {
            icon: createLeafletMarkerIcon(Leaflet, "public-marker", layer.color, 18),
            keyboard: false,
          })
            .bindPopup(
              buildPopup(
                item.name,
                [
                  { label: layer.label, color: layer.color },
                  { label: item.type },
                ],
                [escapeHtml(layer.description)],
              ),
            )
            .addTo(group);
        });
        groups.nationalFacilities.set(layer.id, group);
      });
  }

  function renderImportedPublicLayers(state) {
    map.closePopup();
    groups.importedPublic.forEach((group) => group.remove());
    groups.importedPublic.clear();

    state.importedPublicLayers
      .filter((layer) => layer.visible)
      .filter((layer) => layer.scope === "both" || layer.scope === state.viewMode)
      .forEach((layer) => {
        const isInteractive = layer.sourceKind !== "analysis";
        const geoJsonLayer = Leaflet.geoJSON(layer.featureCollection, {
          interactive: isInteractive,
          style: (feature) => buildImportedFeatureStyle(layer, feature),
          pointToLayer: (_feature, latlng) =>
            Leaflet.marker(latlng, {
              icon: createLeafletMarkerIcon(Leaflet, "public-marker", layer.color, 18),
              opacity: clamp(Number(layer.opacity ?? 1), 0, 1),
              interactive: isInteractive,
              keyboard: false,
            }),
          onEachFeature: (feature, featureLayer) => {
            if (!isInteractive) {
              return;
            }

            featureLayer.bindPopup(buildImportedPopup(layer, feature));
          },
        }).addTo(map);

        groups.importedPublic.set(layer.id, geoJsonLayer);
      });
  }

  function renderStudentLayers(state) {
    groups.studentLayers.forEach((group) => group.remove());
    groups.studentLayers.clear();

    state.studentLayers
      .filter((layer) => layer.visible)
      .forEach((layer) => {
        const group = Leaflet.geoJSON(buildStudentLayerFeatureCollection(layer), {
          pointToLayer: (feature, latlng) =>
            Leaflet.marker(latlng, {
              icon: createLeafletMarkerIcon(
                Leaflet,
                "student-marker",
                layer.color,
                isSelectedStudentFeature(state.selectedFeatureRef, feature) ? 24 : 20,
              ),
              opacity: clamp(Number(layer.opacity ?? 1), 0, 1),
              keyboard: false,
            }),
          style: (feature) => buildStudentFeatureStyle(
            layer,
            isSelectedStudentFeature(state.selectedFeatureRef, feature),
          ),
          onEachFeature: (feature, featureLayer) => {
            featureLayer.bindPopup(buildStudentPopup(layer, feature));
            featureLayer.on("click", () => {
              onStudentFeatureInteract?.({
                layerId: feature.properties?.layerId,
                featureId: feature.properties?.featureId,
              });
            });
          },
        }).addTo(map);
        groups.studentLayers.set(layer.id, group);
      });
  }

  function renderStudentDraft(state) {
    groups.draftCursor.clearLayers();

    const activeLayer = state.studentLayers.find((layer) => layer.id === state.activeLayerId);
    const draftGeometry = state.draftGeometry;
    if (!activeLayer || !draftGeometry || draftGeometry.geometryType === "point") {
      return;
    }

    const draftLatLngs = (draftGeometry.points ?? [])
      .map((point) => [Number(point.lat), Number(point.lng)])
      .filter(([lat, lng]) => Number.isFinite(lat) && Number.isFinite(lng));

    if (!draftLatLngs.length) {
      return;
    }

    draftLatLngs.forEach((latlng) => {
      Leaflet.circleMarker(latlng, {
        radius: 6,
        color: "#16354a",
        fillColor: activeLayer.color,
        fillOpacity: 0.92,
        weight: 2,
      }).addTo(groups.draftCursor);
    });

    if (draftLatLngs.length >= 2) {
      Leaflet.polyline(draftLatLngs, {
        color: activeLayer.color,
        weight: 3,
        opacity: 0.85,
        dashArray: "8 6",
      }).addTo(groups.draftCursor);
    }

    if (draftGeometry.geometryType === "polygon" && draftLatLngs.length >= 3) {
      Leaflet.polygon(draftLatLngs, {
        color: activeLayer.color,
        weight: 2,
        opacity: 0.8,
        fillColor: activeLayer.color,
        fillOpacity: 0.1,
        dashArray: "8 6",
      }).addTo(groups.draftCursor);
    }
  }

  function render(state) {
    const currentLocalPublicLayers = getLocalPublicLayers();

    renderSliceIfChanged(
      renderCache,
      "reference",
      getReferenceAreaSignature(state, appConfig),
      () => renderReferenceArea(state),
    );
    renderSliceIfChanged(
      renderCache,
      "localPublic",
      getLocalPublicLayersSignature(state, currentLocalPublicLayers),
      () => renderLocalPublicLayers(state, currentLocalPublicLayers),
    );
    renderSliceIfChanged(
      renderCache,
      "importedPublic",
      getImportedPublicLayersSignature(state),
      () => renderImportedPublicLayers(state),
    );
    renderSliceIfChanged(
      renderCache,
      "nationalStats",
      getNationalStatsSignature(state, getNationalDataset),
      () => renderNationalStats(state),
    );
    renderSliceIfChanged(
      renderCache,
      "nationalFacilities",
      getNationalFacilitiesSignature(state),
      () => renderNationalFacilities(state),
    );
    renderSliceIfChanged(
      renderCache,
      "studentLayers",
      getStudentLayersSignature(state),
      () => renderStudentLayers(state),
    );
    renderSliceIfChanged(
      renderCache,
      "draft",
      getDraftGeometrySignature(state),
      () => renderStudentDraft(state),
    );
    window.setTimeout(() => map.invalidateSize(), 0);
  }

  function showDraftCursor(latlng, visible) {
    groups.draftCursor.clearLayers();
    if (!visible) {
      return;
    }

    Leaflet.circleMarker([latlng.lat, latlng.lng], {
      radius: 8,
      color: "#16354a",
      fillColor: "#ffffff",
      fillOpacity: 0,
      opacity: 1,
      weight: 3,
    }).addTo(groups.draftCursor);
  }

  function focusScope(viewMode) {
    if (viewMode === "korea") {
      map.fitBounds(koreaMapView.bounds, { padding: [20, 20] });
      return;
    }

    focusLocation({
      lat: appConfig.mapCenter.lat,
      lng: appConfig.mapCenter.lng,
    });
  }

  function focusLocation(location) {
    const lat = Number(location?.lat ?? appConfig.mapCenter.lat);
    const lng = Number(location?.lng ?? appConfig.mapCenter.lng);
    map.flyTo([lat, lng], appConfig.initialZoom, {
      duration: 0.6,
    });
  }

  function fitCoordinates(coordinates) {
    if (!coordinates.length) {
      return;
    }

    map.fitBounds(Leaflet.latLngBounds(coordinates).pad(0.2));
  }

  function fitReferenceArea(location, radiusMeters) {
    const coordinates = buildReferenceAreaCoordinates(location, radiusMeters);
    if (!coordinates.length) {
      focusLocation(location);
      return;
    }

    map.fitBounds(Leaflet.latLngBounds(coordinates).pad(0.12));
  }

  function setBaseMapMode(mode) {
    if (baseMapMode === mode) {
      return;
    }

    baseMapMode = mode;
    mapContainer.dataset.baseMapMode = baseMapMode;

    if (!map.hasLayer(tileLayer)) {
      tileLayer.addTo(map);
    }

    tileLayer.setOpacity(1);
    if (tileLoadCount > 0 && tileErrorCount === 0 && !statusMessage) {
      status.hide();
    }
    map.invalidateSize();
  }

  return {
    map: {
      getCenter() {
        return toPlainLatLng(map.getCenter());
      },
      getZoom() {
        return map.getZoom();
      },
      flyTo(coords, zoom, options = {}) {
        const { lat, lng } = toPlainLatLng(coords);
        map.flyTo([lat, lng], zoom, options);
      },
    },
    render,
    focusScope,
    focusLocation,
    fitCoordinates,
    fitReferenceArea,
    closePopup: () => map.closePopup(),
    showDraftCursor,
    setBaseMapMode,
    setOverlayLayerIds() {},
    async searchPlaces() {
      return [];
    },
  };
}

function clearKakaoOverlayList(overlays) {
  overlays.forEach((overlay) => overlay?.setMap?.(null));
  overlays.length = 0;
}

function clearKakaoOverlayMap(overlayMap) {
  overlayMap.forEach((overlays) => clearKakaoOverlayList(overlays));
  overlayMap.clear();
}
function createKakaoMarkerImage(kakao, color, size) {
  const normalizedSize = Math.max(14, Math.round(size));
  const radius = Math.max(4, Math.round((normalizedSize - 6) / 2));
  const center = normalizedSize / 2;
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="${normalizedSize}" height="${normalizedSize}" viewBox="0 0 ${normalizedSize} ${normalizedSize}">
      <circle cx="${center}" cy="${center}" r="${radius}" fill="${color}" stroke="#ffffff" stroke-width="3" />
    </svg>
  `.trim();

  return new kakao.maps.MarkerImage(
    `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`,
    new kakao.maps.Size(normalizedSize, normalizedSize),
  );
}

function createKakaoTooltip(kakao, position, label) {
  return new kakao.maps.CustomOverlay({
    position,
    yAnchor: 1.9,
    zIndex: 3,
    content: `<div class="map-inline-label">${escapeHtml(label)}</div>`,
  });
}

function buildKakaoBounds(kakao, coordinates) {
  const bounds = new kakao.maps.LatLngBounds();
  coordinates.forEach((coordinate) => {
    const { lat, lng } = toPlainLatLng(coordinate);
    if (Number.isFinite(lat) && Number.isFinite(lng)) {
      bounds.extend(new kakao.maps.LatLng(lat, lng));
    }
  });
  return bounds;
}

function loadKakaoSdk(appConfig) {
  const key = String(appConfig.kakao?.javascriptKey ?? "").trim();
  if (!key) {
    throw new Error("runtime-config.js에 Kakao JavaScript 키가 없습니다.");
  }

  const currentOrigin = window.location.origin;
  const kakaoLoadError = () =>
    new Error(
      `카카오 지도 SDK 스크립트를 불러오지 못했습니다. 현재 접속 주소 ${currentOrigin} 가 Kakao JavaScript SDK 도메인에 등록되어 있는지 확인해 주세요.`,
    );

  if (window.kakao?.maps?.services) {
    return Promise.resolve(window.kakao);
  }

  if (kakaoSdkPromise) {
    return kakaoSdkPromise;
  }

  kakaoSdkPromise = new Promise((resolve, reject) => {
    const existingScript = document.getElementById(KAKAO_SDK_ID);
    const onReady = () => {
      if (!window.kakao?.maps) {
        kakaoSdkPromise = null;
        reject(new Error("카카오 지도 SDK가 로드되지 않았습니다."));
        return;
      }

      window.kakao.maps.load(() => {
        if (!window.kakao?.maps?.services) {
          kakaoSdkPromise = null;
          reject(new Error("카카오 services 라이브러리가 로드되지 않았습니다."));
          return;
        }

        resolve(window.kakao);
      });
    };

    if (existingScript) {
      if (existingScript.dataset.loadState === "loaded" && window.kakao?.maps) {
        onReady();
        return;
      }

      if (existingScript.dataset.loadState === "error") {
        kakaoSdkPromise = null;
        reject(kakaoLoadError());
        return;
      }

      existingScript.addEventListener("load", onReady, { once: true });
      existingScript.addEventListener(
        "error",
        () => {
          existingScript.dataset.loadState = "error";
          kakaoSdkPromise = null;
          reject(kakaoLoadError());
        },
        { once: true },
      );
      return;
    }

    const script = document.createElement("script");
    script.id = KAKAO_SDK_ID;
    script.async = true;
    script.dataset.loadState = "loading";
    script.src = `https://dapi.kakao.com/v2/maps/sdk.js?appkey=${encodeURIComponent(
      key,
    )}&autoload=false&libraries=${encodeURIComponent(KAKAO_DEFAULT_LIBRARIES.join(","))}`;
    script.addEventListener(
      "load",
      () => {
        script.dataset.loadState = "loaded";
        onReady();
      },
      { once: true },
    );
    script.addEventListener(
      "error",
      () => {
        script.dataset.loadState = "error";
        kakaoSdkPromise = null;
        reject(kakaoLoadError());
      },
      { once: true },
    );
    document.head.appendChild(script);
  });

  return kakaoSdkPromise;
}

function createKakaoWorkspaceMap({
  mapId,
  appConfig,
  koreaMapView,
  localPublicLayers,
  nationalFacilityLayers,
  getNationalDataset,
  getNationalPointValue,
  getNationalStats,
  getNationalGradient,
  onMapClick,
  onStudentFeatureInteract,
  onNationalPointSelect,
}) {
  const mapContainer = ensureMapContainer(mapId);
  const status = createStatusController(mapContainer);
  const mapFacade = createStubMapFacade(appConfig);
  const getLocalPublicLayers = typeof localPublicLayers === "function"
    ? localPublicLayers
    : () => localPublicLayers ?? [];
  const renderCache = createRenderCache();
  const pendingState = {
    renderState: null,
    focusScope: null,
    focusLocation: null,
    fitCoordinates: null,
    fitReferenceArea: null,
    draftCursor: null,
    baseMapMode: "roadmap",
    overlayLayerIds: [],
  };

  let kakao = null;
  let map = null;
  let places = null;
  let activeInfoWindow = null;
  let resizeListener = null;
  let overlayLayerSignature = "";
  let fallbackWorkspace = null;

  const groups = {
    schoolReference: [],
    localPublic: new Map(),
    importedPublic: new Map(),
    nationalStats: [],
    nationalFacilities: new Map(),
    studentLayers: new Map(),
    draftCursor: [],
  };

  function activateLeafletFallback(error) {
    if (fallbackWorkspace) {
      return fallbackWorkspace;
    }

    const fallbackMessage = "카카오 지도를 불러오지 못해 기본 지도로 전환했습니다. 지도 기능은 계속 사용할 수 있습니다.";

    mapContainer.innerHTML = "";
    fallbackWorkspace = createLeafletWorkspaceMap({
      mapId,
      appConfig: {
        ...appConfig,
        mapProvider: "leaflet",
      },
      koreaMapView,
      localPublicLayers,
      nationalFacilityLayers,
      getNationalDataset,
      getNationalPointValue,
      getNationalStats,
      getNationalGradient,
      onMapClick,
      onStudentFeatureInteract,
      onNationalPointSelect,
      statusMessage: fallbackMessage,
    });

    if (pendingState.renderState) {
      fallbackWorkspace.render(pendingState.renderState);
    }
    if (pendingState.focusScope) {
      fallbackWorkspace.focusScope(pendingState.focusScope);
    }
    if (pendingState.focusLocation) {
      fallbackWorkspace.focusLocation(pendingState.focusLocation);
    }
    if (pendingState.fitCoordinates?.length) {
      fallbackWorkspace.fitCoordinates(pendingState.fitCoordinates);
    }
    if (pendingState.fitReferenceArea) {
      fallbackWorkspace.fitReferenceArea(
        pendingState.fitReferenceArea.location,
        pendingState.fitReferenceArea.radiusMeters,
      );
    }
    if (pendingState.draftCursor) {
      fallbackWorkspace.showDraftCursor(
        pendingState.draftCursor.latlng,
        pendingState.draftCursor.visible,
      );
    }
    fallbackWorkspace.setBaseMapMode(pendingState.baseMapMode);
    fallbackWorkspace.setOverlayLayerIds(pendingState.overlayLayerIds);

    return fallbackWorkspace;
  }

  function closeInfoWindow() {
    if (activeInfoWindow) {
      activeInfoWindow.close();
      activeInfoWindow = null;
    }
  }

  mapContainer.addEventListener("click", (event) => {
    const closeButton = event.target.closest("[data-popup-close]");
    if (!closeButton) {
      return;
    }

    event.preventDefault();
    event.stopPropagation();
    closeInfoWindow();
  });

  function openPopup(content, position, marker) {
    closeInfoWindow();
    activeInfoWindow = new kakao.maps.InfoWindow({ content });
    if (marker) {
      activeInfoWindow.open(map, marker);
      return;
    }
    activeInfoWindow.setPosition(position);
    activeInfoWindow.open(map);
  }

  function createMarker(lat, lng, color, size, popupContent, onClick, interactive = true, opacity = 1) {
    const marker = new kakao.maps.Marker({
      position: new kakao.maps.LatLng(lat, lng),
      image: createKakaoMarkerImage(kakao, color, size),
      clickable: interactive,
    });
    marker.setMap(map);
    if (typeof marker.setOpacity === "function") {
      marker.setOpacity(clamp(Number(opacity ?? 1), 0, 1));
    }
    if (interactive) {
      kakao.maps.event.addListener(marker, "click", () => {
        openPopup(popupContent, marker.getPosition(), marker);
        onClick?.();
      });
    }
    return marker;
  }

  function setOverlayList(target, overlays) {
    clearKakaoOverlayList(target);
    overlays.forEach((overlay) => overlay?.setMap?.(map));
    target.push(...overlays);
  }

  function setOverlayGroup(targetMap, key, overlays) {
    clearKakaoOverlayList(targetMap.get(key) ?? []);
    overlays.forEach((overlay) => overlay?.setMap?.(map));
    targetMap.set(key, overlays);
  }

  function createGeoJsonOverlays(layer, feature, options = {}) {
    const geometry = feature?.geometry;
    if (!geometry) {
      return [];
    }

    const style = options.style ?? buildImportedFeatureStyle(layer, feature);
    const popupContent = options.popupContent ?? buildImportedPopup(layer, feature);
    const markerSize = Number(options.markerSize ?? 18);
    const interactive = options.interactive !== false;

    const pointMarker = (coordinates) => {
      const [lng, lat] = coordinates;
      if (!Number.isFinite(lat) || !Number.isFinite(lng)) {
        return [];
      }
      return [
        createMarker(
          lat,
          lng,
          style.fillColor ?? style.color ?? layer.color,
          markerSize,
          popupContent,
          options.onClick,
          interactive,
          style.opacity ?? layer.opacity ?? 1,
        ),
      ];
    };

    const lineOverlay = (lineCoordinates) => {
      const path = lineCoordinates
        .map(([lng, lat]) => new kakao.maps.LatLng(lat, lng))
        .filter((point) => Number.isFinite(point.getLat()) && Number.isFinite(point.getLng()));
      if (!path.length) {
        return [];
      }

      const polyline = new kakao.maps.Polyline({
        path,
        strokeWeight: style.weight ?? 3,
        strokeColor: style.color ?? layer.color,
        strokeOpacity: style.opacity ?? 0.9,
        strokeStyle: "solid",
      });
      polyline.setMap(map);
      if (interactive) {
        kakao.maps.event.addListener(polyline, "click", (mouseEvent) => {
          openPopup(popupContent, mouseEvent.latLng);
          options.onClick?.();
        });
      }
      return [polyline];
    };

    const polygonOverlay = (polygonCoordinates) => {
      const path = polygonCoordinates
        .map((ring) =>
          ring
            .map(([lng, lat]) => new kakao.maps.LatLng(lat, lng))
            .filter((point) => Number.isFinite(point.getLat()) && Number.isFinite(point.getLng())),
        )
        .filter((ring) => ring.length);
      if (!path.length) {
        return [];
      }

      const polygon = new kakao.maps.Polygon({
        path,
        strokeWeight: style.weight ?? 3,
        strokeColor: style.color ?? layer.color,
        strokeOpacity: style.opacity ?? 0.9,
        fillColor: style.fillColor ?? layer.color,
        fillOpacity: style.fillOpacity ?? 0.15,
      });
      polygon.setMap(map);
      if (interactive) {
        kakao.maps.event.addListener(polygon, "click", (mouseEvent) => {
          openPopup(popupContent, mouseEvent.latLng);
          options.onClick?.();
        });
      }
      return [polygon];
    };

    switch (geometry.type) {
      case "Point":
        return pointMarker(geometry.coordinates);
      case "MultiPoint":
        return geometry.coordinates.flatMap(pointMarker);
      case "LineString":
        return lineOverlay(geometry.coordinates);
      case "MultiLineString":
        return geometry.coordinates.flatMap(lineOverlay);
      case "Polygon":
        return polygonOverlay(geometry.coordinates);
      case "MultiPolygon":
        return geometry.coordinates.flatMap(polygonOverlay);
      default:
        return [];
    }
  }

  function renderReferenceArea(state) {
    const overlays = [];
    if (state.viewMode === "school" && state.showSchoolReference) {
      const referenceLat = Number(state.referenceLocation?.lat ?? appConfig.mapCenter.lat);
      const referenceLng = Number(state.referenceLocation?.lng ?? appConfig.mapCenter.lng);
      const referenceRadius = Number(
        state.referenceRadiusMeters ?? appConfig.schoolRadiusMeters,
      );
      const referenceLabel = state.referenceLabel ?? appConfig.schoolName;
      const center = new kakao.maps.LatLng(referenceLat, referenceLng);
      const radius = new kakao.maps.Circle({
        center,
        radius: referenceRadius,
        strokeWeight: 2,
        strokeColor: "#184d42",
        strokeOpacity: 1,
        fillColor: "#4ec08f",
        fillOpacity: 0.08,
      });
      const centerMarker = new kakao.maps.Marker({
        position: center,
        image: createKakaoMarkerImage(kakao, "#f0bf55", 18),
        clickable: false,
      });
      const label = createKakaoTooltip(kakao, center, `${referenceLabel} 중심`);

      overlays.push(radius, centerMarker, label);
    }
    setOverlayList(groups.schoolReference, overlays);
  }

  function renderLocalPublicLayers(state, currentLocalPublicLayers) {
    clearKakaoOverlayMap(groups.localPublic);
    if (state.viewMode !== "school") {
      return;
    }

    currentLocalPublicLayers
      .filter((layer) => state.localPublicVisibility[layer.id])
      .forEach((layer) => {
        const layerOpacity = clamp(Number(state.localPublicOpacity?.[layer.id] ?? 1), 0, 1);
        const overlays = layer.items.map((item) =>
          createMarker(
            item.lat,
            item.lng,
            layer.color,
            18,
            buildPopup(
              item.name,
              [
                { label: layer.label, color: layer.color },
                { label: item.type },
              ],
              [escapeHtml(item.note)],
            ),
            undefined,
            true,
            layerOpacity,
          ),
        );
        setOverlayGroup(groups.localPublic, layer.id, overlays);
      });
  }

  function renderImportedPublicLayers(state) {
    closeInfoWindow();
    clearKakaoOverlayMap(groups.importedPublic);

    state.importedPublicLayers
      .filter((layer) => layer.visible)
      .filter((layer) => layer.scope === "both" || layer.scope === state.viewMode)
      .forEach((layer) => {
        const overlays = (layer.featureCollection?.features ?? []).flatMap((feature) =>
          createGeoJsonOverlays(layer, feature, {
            interactive: layer.sourceKind !== "analysis",
          }),
        );
        setOverlayGroup(groups.importedPublic, layer.id, overlays);
      });
  }
  function renderNationalStats(state) {
    const overlays = [];
    if (state.viewMode === "korea" && state.showNationalStats) {
      const dataset = getNationalDataset(state);
      const stats = getNationalStats(dataset, state.selectedNationalYear, getNationalPointValue);
      const gradient = getNationalGradient(dataset);
      const denominator = Math.max(1, stats.max - stats.min);

      dataset.points.forEach((point) => {
        const value = getNationalPointValue(point, state.selectedNationalYear);
        const ratio = (value - stats.min) / denominator;
        const color = interpolateColor(gradient.low, gradient.high, ratio);
        const size = 18 + ratio * 14;
        const marker = createMarker(
          point.lat,
          point.lng,
          color,
          size,
          buildPopup(
            point.name,
            [{ label: dataset.label }, { label: String(state.selectedNationalYear) }],
            [
              `<b>지표값:</b> ${formatNumber(value)}${escapeHtml(dataset.unit)}`,
              escapeHtml(point.note),
            ],
          ),
          () => onNationalPointSelect(point.id),
        );
        overlays.push(marker);
      });
    }

    setOverlayList(groups.nationalStats, overlays);
  }

  function renderNationalFacilities(state) {
    clearKakaoOverlayMap(groups.nationalFacilities);
    if (state.viewMode !== "korea") {
      return;
    }

    nationalFacilityLayers
      .filter(
        (layer) =>
          layer.id !== "none" && state.activeNationalFacilityLayerIds.includes(layer.id),
      )
      .forEach((layer) => {
        const overlays = layer.items.map((item) =>
          createMarker(
            item.lat,
            item.lng,
            layer.color,
            18,
            buildPopup(
              item.name,
              [
                { label: layer.label, color: layer.color },
                { label: item.type },
              ],
              [escapeHtml(layer.description)],
            ),
          ),
        );
        setOverlayGroup(groups.nationalFacilities, layer.id, overlays);
      });
  }

  function renderStudentLayers(state) {
    clearKakaoOverlayMap(groups.studentLayers);

    state.studentLayers
      .filter((layer) => layer.visible)
      .forEach((layer) => {
        const overlays = buildStudentLayerFeatureCollection(layer).features.flatMap((feature) =>
          createGeoJsonOverlays(layer, feature, {
            style: buildStudentFeatureStyle(
              layer,
              isSelectedStudentFeature(state.selectedFeatureRef, feature),
            ),
            popupContent: buildStudentPopup(layer, feature),
            markerSize: isSelectedStudentFeature(state.selectedFeatureRef, feature) ? 24 : 20,
            onClick: () => {
              onStudentFeatureInteract?.({
                layerId: feature.properties?.layerId,
                featureId: feature.properties?.featureId,
              });
            },
          }),
        );
        setOverlayGroup(groups.studentLayers, layer.id, overlays);
      });
  }

  function renderStudentDraft(state) {
    clearKakaoOverlayList(groups.draftCursor);

    const activeLayer = state.studentLayers.find((layer) => layer.id === state.activeLayerId);
    const draftGeometry = state.draftGeometry;
    if (!activeLayer || !draftGeometry || draftGeometry.geometryType === "point") {
      return;
    }

    const path = (draftGeometry.points ?? [])
      .map((point) => new kakao.maps.LatLng(Number(point.lat), Number(point.lng)))
      .filter((point) => Number.isFinite(point.getLat()) && Number.isFinite(point.getLng()));

    if (!path.length) {
      return;
    }

    const overlays = path.map((position) =>
      new kakao.maps.Marker({
        position,
        image: createKakaoMarkerImage(kakao, activeLayer.color, 14),
        clickable: false,
      }),
    );

    if (path.length >= 2) {
      overlays.push(
        new kakao.maps.Polyline({
          path,
          strokeWeight: 3,
          strokeColor: activeLayer.color,
          strokeOpacity: 0.85,
          strokeStyle: "shortdash",
        }),
      );
    }

    if (draftGeometry.geometryType === "polygon" && path.length >= 3) {
      overlays.push(
        new kakao.maps.Polygon({
          path,
          strokeWeight: 2,
          strokeColor: activeLayer.color,
          strokeOpacity: 0.8,
          fillColor: activeLayer.color,
          fillOpacity: 0.1,
        }),
      );
    }

    setOverlayList(groups.draftCursor, overlays);
  }

  function renderDraftCursor(latlng, visible) {
    clearKakaoOverlayList(groups.draftCursor);
    if (!visible) {
      return;
    }

    const marker = new kakao.maps.Marker({
      position: new kakao.maps.LatLng(latlng.lat, latlng.lng),
      image: createKakaoMarkerImage(kakao, "#16354a", 18),
      clickable: false,
    });
    marker.setMap(map);
    groups.draftCursor.push(marker);
  }

  function render(state) {
    pendingState.renderState = state;
    if (!map) {
      return;
    }

    const currentLocalPublicLayers = getLocalPublicLayers();

    renderSliceIfChanged(
      renderCache,
      "reference",
      getReferenceAreaSignature(state, appConfig),
      () => renderReferenceArea(state),
    );
    renderSliceIfChanged(
      renderCache,
      "localPublic",
      getLocalPublicLayersSignature(state, currentLocalPublicLayers),
      () => renderLocalPublicLayers(state, currentLocalPublicLayers),
    );
    renderSliceIfChanged(
      renderCache,
      "importedPublic",
      getImportedPublicLayersSignature(state),
      () => renderImportedPublicLayers(state),
    );
    renderSliceIfChanged(
      renderCache,
      "nationalStats",
      getNationalStatsSignature(state, getNationalDataset),
      () => renderNationalStats(state),
    );
    renderSliceIfChanged(
      renderCache,
      "nationalFacilities",
      getNationalFacilitiesSignature(state),
      () => renderNationalFacilities(state),
    );
    renderSliceIfChanged(
      renderCache,
      "studentLayers",
      getStudentLayersSignature(state),
      () => renderStudentLayers(state),
    );
    renderSliceIfChanged(
      renderCache,
      "draft",
      getDraftGeometrySignature(state),
      () => renderStudentDraft(state),
    );
  }

  function focusScope(viewMode) {
    pendingState.focusScope = viewMode;
    if (!map) {
      return;
    }

    if (viewMode === "korea") {
      map.setBounds(buildKakaoBounds(kakao, koreaMapView.bounds));
      return;
    }

    moveKakaoView(
      { lat: appConfig.mapCenter.lat, lng: appConfig.mapCenter.lng },
      appConfig.initialZoom,
    );
  }

  function moveKakaoView(target, zoom) {
    const position = new kakao.maps.LatLng(target.lat, target.lng);
    const nextLevel = Number.isFinite(Number(zoom))
      ? pseudoZoomToKakaoLevel(zoom)
      : null;

    map.panTo(position);
    if (nextLevel !== null && nextLevel !== map.getLevel()) {
      window.setTimeout(() => {
        if (map) {
          map.setLevel(nextLevel);
        }
      }, 220);
    }
  }

  function focusLocation(location) {
    pendingState.focusLocation = location;
    const lat = Number(location?.lat ?? appConfig.mapCenter.lat);
    const lng = Number(location?.lng ?? appConfig.mapCenter.lng);
    if (!map) {
      mapFacade.flyTo({ lat, lng }, appConfig.initialZoom);
      return;
    }

    moveKakaoView({ lat, lng }, appConfig.initialZoom);
  }

  function fitCoordinates(coordinates) {
    pendingState.fitCoordinates = coordinates;
    if (!map || !coordinates.length) {
      return;
    }
    map.setBounds(buildKakaoBounds(kakao, coordinates));
  }

  function fitReferenceArea(location, radiusMeters) {
    pendingState.fitReferenceArea = { location, radiusMeters };
    const coordinates = buildReferenceAreaCoordinates(location, radiusMeters);
    if (!map || !coordinates.length) {
      if (!map) {
        mapFacade.flyTo(location, appConfig.initialZoom);
      }
      return;
    }
    map.setBounds(buildKakaoBounds(kakao, coordinates));
  }

  function showDraftCursor(latlng, visible) {
    pendingState.draftCursor = { latlng, visible };
    if (!map) {
      return;
    }
    renderDraftCursor(latlng, visible);
  }

  function setBaseMapMode(mode) {
    pendingState.baseMapMode = mode;
    if (!map || !kakao?.maps?.MapTypeId) {
      return;
    }

    if (map.getMapTypeId() === (mode === "skyview"
      ? kakao.maps.MapTypeId.SKYVIEW
      : mode === "hybrid"
        ? kakao.maps.MapTypeId.HYBRID
        : kakao.maps.MapTypeId.ROADMAP)) {
      return;
    }

    const typeMap = {
      roadmap: kakao.maps.MapTypeId.ROADMAP,
      skyview: kakao.maps.MapTypeId.SKYVIEW,
      hybrid: kakao.maps.MapTypeId.HYBRID,
    };

    map.setMapTypeId(typeMap[mode] ?? kakao.maps.MapTypeId.ROADMAP);
  }

  function setOverlayLayerIds(nextOverlayLayerIds) {
    pendingState.overlayLayerIds = [...nextOverlayLayerIds];
    if (!map || !kakao?.maps?.MapTypeId) {
      return;
    }

    const nextSignature = [...nextOverlayLayerIds].sort().join("|");
    if (overlayLayerSignature === nextSignature) {
      return;
    }
    overlayLayerSignature = nextSignature;

    const overlayMap = {
      traffic: kakao.maps.MapTypeId.TRAFFIC,
      bicycle: kakao.maps.MapTypeId.BICYCLE,
      terrain: kakao.maps.MapTypeId.TERRAIN,
      district: kakao.maps.MapTypeId.USE_DISTRICT,
    };

    KAKAO_OVERLAY_IDS.forEach((overlayId) => {
      const overlayType = overlayMap[overlayId];
      if (overlayType) {
        map.removeOverlayMapTypeId(overlayType);
      }
    });

    nextOverlayLayerIds.forEach((overlayId) => {
      const overlayType = overlayMap[overlayId];
      if (overlayType) {
        map.addOverlayMapTypeId(overlayType);
      }
    });
  }

  async function searchPlaces(query) {
    if (!places) {
      return [];
    }

    return new Promise((resolve, reject) => {
      places.keywordSearch(
        query,
        (data, searchStatus) => {
          if (searchStatus === kakao.maps.services.Status.ZERO_RESULT) {
            resolve([]);
            return;
          }
          if (searchStatus !== kakao.maps.services.Status.OK) {
            reject(new Error("카카오 장소 검색에 실패했습니다."));
            return;
          }

          resolve(
            data.map((item) => ({
              id: String(item.id ?? `${item.x}-${item.y}`),
              name: item.place_name ?? query,
              subtitle: item.road_address_name || item.address_name || "",
              lat: Number(item.y),
              lng: Number(item.x),
              type: item.category_group_name || item.category_name || "place",
            })),
          );
        },
        {
          size: Number(appConfig.kakao?.searchLimit ?? 5),
        },
      );
    });
  }

  async function initialize() {
    try {
      status.show("카카오 지도를 불러오는 중입니다.", "info");
      kakao = await loadKakaoSdk(appConfig);
      map = new kakao.maps.Map(mapContainer, {
        center: new kakao.maps.LatLng(appConfig.mapCenter.lat, appConfig.mapCenter.lng),
        level: pseudoZoomToKakaoLevel(appConfig.initialZoom),
      });
      places = new kakao.maps.services.Places();

      kakao.maps.event.addListener(map, "click", (mouseEvent) => {
        closeInfoWindow();
        onMapClick({
          lat: mouseEvent.latLng.getLat(),
          lng: mouseEvent.latLng.getLng(),
        });
      });

      resizeListener = () => map.relayout();
      window.addEventListener("resize", resizeListener);
      status.hide();

      if (pendingState.renderState) {
        render(pendingState.renderState);
      }
      if (pendingState.focusScope) {
        focusScope(pendingState.focusScope);
      }
      if (pendingState.focusLocation) {
        focusLocation(pendingState.focusLocation);
      }
      if (pendingState.fitCoordinates?.length) {
        fitCoordinates(pendingState.fitCoordinates);
      }
      if (pendingState.fitReferenceArea) {
        fitReferenceArea(
          pendingState.fitReferenceArea.location,
          pendingState.fitReferenceArea.radiusMeters,
        );
      }
      if (pendingState.draftCursor) {
        renderDraftCursor(pendingState.draftCursor.latlng, pendingState.draftCursor.visible);
      }
      setBaseMapMode(pendingState.baseMapMode);
      setOverlayLayerIds(pendingState.overlayLayerIds);
    } catch (error) {
      console.warn(error);
      activateLeafletFallback(error);
    }
  }

  void initialize();

  return {
    map: {
      getCenter() {
        if (fallbackWorkspace) {
          return fallbackWorkspace.map.getCenter();
        }
        if (!map) {
          return mapFacade.getCenter();
        }
        return {
          lat: map.getCenter().getLat(),
          lng: map.getCenter().getLng(),
        };
      },
      getZoom() {
        if (fallbackWorkspace) {
          return fallbackWorkspace.map.getZoom();
        }
        if (!map) {
          return mapFacade.getZoom();
        }
        return kakaoLevelToPseudoZoom(map.getLevel());
      },
      flyTo(coords, zoom) {
        const target = toPlainLatLng(coords);
        if (fallbackWorkspace) {
          fallbackWorkspace.map.flyTo(target, zoom);
          return;
        }
        mapFacade.flyTo(target, zoom);
        if (!map) {
          return;
        }
        moveKakaoView(target, zoom);
      },
    },
    render(state) {
      if (fallbackWorkspace) {
        fallbackWorkspace.render(state);
        return;
      }
      render(state);
    },
    focusScope(viewMode) {
      if (fallbackWorkspace) {
        fallbackWorkspace.focusScope(viewMode);
        return;
      }
      focusScope(viewMode);
    },
    focusLocation(coords) {
      if (fallbackWorkspace) {
        fallbackWorkspace.focusLocation(coords);
        return;
      }
      focusLocation(coords);
    },
    fitCoordinates(coordinates) {
      if (fallbackWorkspace) {
        fallbackWorkspace.fitCoordinates(coordinates);
        return;
      }
      fitCoordinates(coordinates);
    },
    fitReferenceArea(location, radiusMeters) {
      if (fallbackWorkspace) {
        fallbackWorkspace.fitReferenceArea(location, radiusMeters);
        return;
      }
      fitReferenceArea(location, radiusMeters);
    },
    closePopup() {
      if (fallbackWorkspace) {
        fallbackWorkspace.closePopup();
        return;
      }
      closeInfoWindow();
    },
    showDraftCursor(latlng, visible) {
      if (fallbackWorkspace) {
        fallbackWorkspace.showDraftCursor(latlng, visible);
        return;
      }
      showDraftCursor(latlng, visible);
    },
    setBaseMapMode(mode) {
      if (fallbackWorkspace) {
        fallbackWorkspace.setBaseMapMode(mode);
        return;
      }
      setBaseMapMode(mode);
    },
    setOverlayLayerIds(nextOverlayLayerIds) {
      if (fallbackWorkspace) {
        fallbackWorkspace.setOverlayLayerIds(nextOverlayLayerIds);
        return;
      }
      setOverlayLayerIds(nextOverlayLayerIds);
    },
    searchPlaces(query) {
      if (fallbackWorkspace) {
        return fallbackWorkspace.searchPlaces(query);
      }
      return searchPlaces(query);
    },
  };
}

export function createLayerWorkspaceMap(options) {
  const { appConfig } = options;
  const wantsKakao = appConfig.mapProvider === "kakao";
  const hasKakaoKey = Boolean(String(appConfig.kakao?.javascriptKey ?? "").trim());

  try {
    if (wantsKakao && hasKakaoKey) {
      return createKakaoWorkspaceMap(options);
    }

    const statusMessage =
      wantsKakao && !hasKakaoKey
        ? "runtime-config.js에 Kakao JavaScript 키가 없어 기본 지도로 표시합니다. 키를 넣으면 카카오 지도로 바로 전환됩니다."
        : "";

    return createLeafletWorkspaceMap({
      ...options,
      statusMessage,
    });
  } catch (error) {
    console.error(error);
    const status = createStatusController(ensureMapContainer(options.mapId));
    status.show(error.message || "지도를 초기화하지 못했습니다.", "error");
    return createNoopWorkspaceMap(options.appConfig, status);
  }
}
