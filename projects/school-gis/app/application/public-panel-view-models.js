import { buildFeatureCollectionMeasurementSummary } from "./measurement-use-cases.js";

export function getImportedPublicSourceLabel(layer) {
  if (layer.sourceKind === "preset") {
    return "추천 링크";
  }
  if (layer.sourceKind === "sgis") {
    return "SGIS";
  }
  if (layer.sourceKind === "analysis" && layer.analysisType === "suitability") {
    return "입지점수";
  }
  if (layer.sourceKind === "analysis") {
    return "분석 버퍼";
  }
  return "URL";
}

export function getLayerScopeLabel(scope) {
  if (scope === "school") {
    return "현재 작업공간";
  }
  if (scope === "korea") {
    return "대한민국 보기";
  }
  return "전체";
}

export function getSchoolSgisControlValues(elements) {
  return {
    metricId: elements.sgisMetricField.value,
    year: Number(elements.sgisYearField.value),
    color: elements.sgisColorField.value,
  };
}

export function getCurrentSgisProfile(elements, profiles) {
  const selectedProfileId = elements.sgisProfileField?.value;
  return (
    profiles.find((profile) => profile.id === selectedProfileId)
    ?? profiles.find((profile) => profile.id === "grid-sgg-500m")
    ?? profiles[0]
  );
}

export function getCurrentSgisMetricLabel(elements, getSgisMetricRecommendation) {
  const selectedOption = elements.sgisMetricField?.selectedOptions?.[0];
  if (selectedOption?.textContent) {
    return selectedOption.textContent.trim();
  }
  return getSgisMetricRecommendation(elements.sgisMetricField?.value).studentLabel;
}

function buildGridAvailabilityHint(profile, elements, getSgisMetricRecommendation) {
  if (profile.type !== "grid") {
    return "";
  }

  const metricLabel = getCurrentSgisMetricLabel(elements, getSgisMetricRecommendation);
  const year = elements.sgisYearField?.value || "-";
  return `${profile.gridLevelDiv} 격자 · ${year}년 ${metricLabel}: 격자 경계는 불러오지만, 이 조합의 격자별 통계값은 없을 수 있습니다. 값이 없으면 행정구역 단위로 대체할 수 있습니다.`;
}

function getImportedLayerMeasurementSummary(layer) {
  if (layer.measurementSummary) {
    return layer.measurementSummary;
  }

  if (layer.sourceKind === "analysis") {
    return buildFeatureCollectionMeasurementSummary(layer.featureCollection);
  }

  return null;
}

function getImportedLayerMetricSummary(layer) {
  const values = (layer.featureCollection?.features ?? [])
    .map((feature) => Number(feature?.properties?.metricValue))
    .filter((value) => Number.isFinite(value));

  if (!values.length) {
    return null;
  }

  const firstMetricFeature = (layer.featureCollection?.features ?? [])
    .find((feature) => Number.isFinite(Number(feature?.properties?.metricValue)));
  const properties = firstMetricFeature?.properties ?? {};
  const digits = Number(properties.metricDigits ?? 0);
  const unit = String(properties.metricUnit ?? "");
  const sum = values.reduce((total, value) => total + value, 0);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const average = sum / values.length;
  const range = Math.max(1, max - min);
  const binCount = 5;
  const bins = Array.from({ length: binCount }, () => 0);

  values.forEach((value) => {
    const index = Math.min(binCount - 1, Math.floor(((value - min) / range) * binCount));
    bins[index] += 1;
  });

  const maxBin = Math.max(...bins, 1);

  return {
    label: String(properties.metricLabel ?? "통계값"),
    year: String(properties.metricYear ?? ""),
    unit,
    count: values.length,
    minLabel: `${min.toLocaleString("ko-KR", { maximumFractionDigits: digits })}${unit}`,
    maxLabel: `${max.toLocaleString("ko-KR", { maximumFractionDigits: digits })}${unit}`,
    averageLabel: `${average.toLocaleString("ko-KR", { maximumFractionDigits: digits })}${unit}`,
    bins: bins.map((count, index) => ({
      index,
      count,
      heightPercent: Math.max(8, Math.round((count / maxBin) * 100)),
    })),
  };
}

function isGridFeature(feature) {
  const properties = feature?.properties ?? {};
  return Boolean(properties.isGridFeature || properties.gridLevelDiv || properties.gridCode);
}

function formatMetricValue(properties) {
  const value = Number(properties?.metricValue);
  if (!Number.isFinite(value)) {
    return "격자별 통계값 없음";
  }

  const digits = Number(properties.metricDigits ?? 0);
  const unit = String(properties.metricUnit ?? "");
  return `${value.toLocaleString("ko-KR", { maximumFractionDigits: digits })}${unit}`;
}

function getGridFeatureTitle(properties, fallbackIndex) {
  const gridTitle = [properties.gridSizeLabel ?? properties.gridLevelDiv, "격자", properties.gridCode]
    .filter(Boolean)
    .join(" ");
  return String(properties.title ?? (gridTitle || `격자 ${fallbackIndex + 1}`));
}

function getImportedLayerGridSummary(layer) {
  const gridFeatures = (layer.featureCollection?.features ?? []).filter(isGridFeature);
  if (!gridFeatures.length) {
    return null;
  }

  const firstProperties = gridFeatures[0]?.properties ?? {};
  const withMetricCount = gridFeatures.filter((feature) =>
    Number.isFinite(Number(feature?.properties?.metricValue))).length;

  return {
    gridLevelLabel: String(firstProperties.gridSizeLabel ?? firstProperties.gridLevelDiv ?? "격자"),
    totalCount: gridFeatures.length,
    withMetricCount,
    missingMetricCount: gridFeatures.length - withMetricCount,
    metricLabel: String(firstProperties.metricLabel ?? "통계값"),
    metricYear: String(firstProperties.metricYear ?? ""),
    rows: gridFeatures.slice(0, 4).map((feature, index) => {
      const properties = feature.properties ?? {};
      return {
        title: getGridFeatureTitle(properties, index),
        code: String(properties.gridCode ?? properties.adm_cd ?? properties.adm_nm ?? ""),
        valueLabel: formatMetricValue(properties),
        sourceLabel: String(properties.metricSourceLabel ?? properties.joinedAdmNm ?? "격자 경계 정보"),
      };
    }),
  };
}

function getImportedLayerSuitabilitySummary(layer) {
  if (layer.analysisType !== "suitability") {
    return null;
  }

  const analysis = layer.suitabilityAnalysis ?? {};
  return {
    templateLabel: String(analysis.templateLabel ?? "입지점수"),
    baseGridLayerName: String(analysis.baseGridLayerName ?? ""),
    studentLayerName: String(analysis.studentLayerName ?? ""),
    topCandidates: Array.isArray(layer.topCandidates) ? layer.topCandidates : [],
  };
}

export function buildPublicPanelViewModel({
  state,
  elements,
  config,
  localPublicLayers,
  regionProfiles,
  defaultRecommendationIds,
  getCurrentLocationLabel,
  getCurrentSgisProfile,
  getCurrentSgisMetricLabel,
  getSgisMetricRecommendation,
  buildRegionSgisSummary,
  getLayerScopeLabel,
  getImportedPublicSourceLabel,
}) {
  const locationLabel = getCurrentLocationLabel();
  const selectedProfile = getCurrentSgisProfile(elements, regionProfiles);
  const locationLocked = Boolean(state.referenceLocked);
  const selectedAvailabilityHint = buildGridAvailabilityHint(
    selectedProfile,
    elements,
    getSgisMetricRecommendation,
  );

  return {
    summaryText: locationLocked
      ? "고정한 위치를 기준으로 행정단위, 격자단위, 통계항목을 선택해 여러 SGIS 레이어를 중첩하세요."
      : "먼저 지도 검색으로 위치를 찾고 고정하세요. 그 다음 SGIS 통계 레이어를 추가할 수 있습니다.",
    sgisEnabled: config.sgis.enabled,
    locationLocked,
    sgisImportPending: state.schoolSgisImportPending,
    schoolReferenceActive: state.showSchoolReference,
    sgisHelpText: config.sgis.enabled
      ? `행정코드는 숨겨져 있습니다. '${selectedProfile.label}' 범위를 선택하면 앱이 자동으로 행정구역 또는 격자 SGIS 코드를 사용합니다.`
      : "",
    sgisQuick: {
      selectedProfile: {
        id: selectedProfile.id,
        label: selectedProfile.label,
        typeLabel: selectedProfile.type === "grid" ? "격자" : "행정구역",
        description: selectedProfile.description,
        availabilityHint: selectedAvailabilityHint,
        actionLabel: state.schoolSgisImportPending === selectedProfile.id
          ? "불러오는 중..."
          : selectedProfile.type === "grid"
            ? "격자 레이어 추가"
            : "행정구역 레이어 추가",
      },
      topicHint: locationLocked
        ? `${locationLabel} 위치가 고정되었습니다. 아래에서 통계항목과 행정단위를 고르세요.`
        : "지도 위 검색창에서 학교·주소·지역명을 찾고 결과를 선택하면 SGIS 통계 불러오기가 활성화됩니다.",
      regionSummary: buildRegionSgisSummary({
        locationLabel,
        region: state.workspaceRegion,
        pending: state.workspaceRegionPending,
        locked: locationLocked,
      }),
      metricRecommendations: defaultRecommendationIds.map((metricId) => {
        const recommendation = getSgisMetricRecommendation(metricId);
        return {
          id: metricId,
          label: recommendation.studentLabel,
          helper: recommendation.helper,
          isActive: elements.sgisMetricField.value === metricId,
        };
      }),
      cards: [
        {
          title: "현재 중심 행정구역 확인",
          badge: state.workspaceRegion ? "확인됨" : "대기",
          description: locationLocked
            ? "고정한 위치가 어떤 행정구역인지 다시 확인합니다."
            : "위치를 먼저 검색해 고정해야 사용할 수 있습니다.",
          action: "refresh-school-region",
          actionLabel: state.workspaceRegionPending ? "확인 중..." : "다시 확인",
          disabled: !locationLocked,
          priority: false,
        },
      ],
    },
    exampleLayers: {
      activeCount: localPublicLayers.filter((layer) => state.localPublicVisibility[layer.id]).length,
      totalCount: localPublicLayers.length,
      layers: localPublicLayers.map((layer) => ({
        id: layer.id,
        label: layer.label,
        color: layer.color,
        opacity: Number(state.localPublicOpacity?.[layer.id] ?? 1),
        itemCount: layer.items.length,
        description: layer.description,
        visible: Boolean(state.localPublicVisibility[layer.id]),
      })),
    },
    presetLayers: config.publicLayerCatalog.map((preset) => ({
      id: preset.id,
      label: preset.label,
      color: preset.color ?? "#1d9bf0",
      description: preset.description ?? "수업에서 바로 쓸 수 있는 추천 레이어입니다.",
      scopeLabel: getLayerScopeLabel(preset.scope ?? "both"),
    })),
    importedLayers: state.importedPublicLayers.map((layer) => {
      const measurementSummary = getImportedLayerMeasurementSummary(layer);
      const metricSummary = getImportedLayerMetricSummary(layer);
      const gridSummary = getImportedLayerGridSummary(layer);
      const suitabilitySummary = getImportedLayerSuitabilitySummary(layer);
      return {
        id: layer.id,
        name: layer.name,
        color: layer.color,
        featureCount: layer.featureCollection.features.length,
        description: layer.description || "가져온 공공 레이어",
        sourceLabel: getImportedPublicSourceLabel(layer),
        scopeLabel: getLayerScopeLabel(layer.scope),
        opacity: Number(layer.opacity ?? 1),
        visible: layer.visible,
        measurementSummary: measurementSummary
          ? {
              totalLengthLabel: measurementSummary.totalLengthLabel ?? "",
              totalAreaLabel: measurementSummary.totalAreaLabel ?? "",
              totalPerimeterLabel: measurementSummary.totalPerimeterLabel ?? "",
            }
          : null,
        metricSummary,
        gridSummary,
        suitabilitySummary,
      };
    }),
  };
}
