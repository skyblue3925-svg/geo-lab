const GEOMETRY_LABEL = {
  point: "점",
  line: "선",
  polygon: "면",
};

function pluralizeCountLabel(count, unit = "개") {
  return `${count}${unit}`;
}

function summarizeLabels(labels, fallbackLabel) {
  if (!labels.length) {
    return fallbackLabel;
  }

  if (labels.length <= 3) {
    return labels.join(", ");
  }

  return `${labels.slice(0, 3).join(", ")} 외 ${labels.length - 3}개`;
}

function getTopEntry(map) {
  return [...map.entries()]
    .sort((left, right) => {
      if (right[1] !== left[1]) {
        return right[1] - left[1];
      }

      return left[0].localeCompare(right[0], "ko");
    })[0] ?? null;
}

function collectStudentFeatureFacts(studentLayers) {
  const geometryCounts = new Map();
  const categoryCounts = new Map();
  const severityCounts = new Map();

  studentLayers.forEach((layer) => {
    layer.features.forEach((feature) => {
      const geometryType = feature.geometryType ?? layer.geometryType ?? "point";
      const categoryLabel = feature.properties?.categoryLabel ?? layer.name;
      const severityLabel = feature.properties?.severityLabel ?? null;

      geometryCounts.set(geometryType, (geometryCounts.get(geometryType) ?? 0) + 1);
      categoryCounts.set(categoryLabel, (categoryCounts.get(categoryLabel) ?? 0) + 1);
      if (severityLabel) {
        severityCounts.set(severityLabel, (severityCounts.get(severityLabel) ?? 0) + 1);
      }
    });
  });

  return {
    geometryCounts,
    categoryCounts,
    severityCounts,
  };
}

function buildAnalysisInsight(recentAnalysis) {
  const parts = [];
  const latestBufferName = recentAnalysis.latestBuffer?.name
    ? recentAnalysis.latestBuffer.name.includes("버퍼")
      ? recentAnalysis.latestBuffer.name
      : `${recentAnalysis.latestBuffer.name} 버퍼`
    : "";

  if (latestBufferName && recentAnalysis.latestBuffer.areaLabel) {
    parts.push(
      `${latestBufferName}의 면적은 ${recentAnalysis.latestBuffer.areaLabel}`,
    );
  } else if (latestBufferName) {
    parts.push(`${latestBufferName}를 만들었습니다`);
  }

  if (recentAnalysis.latestMeasurement?.primaryLabel && recentAnalysis.latestMeasurement?.primaryValue) {
    parts.push(
      `${recentAnalysis.latestMeasurement.primaryLabel}은 ${recentAnalysis.latestMeasurement.primaryValue}`,
    );
  }

  if (recentAnalysis.latestSuitability?.name) {
    const topCandidate = recentAnalysis.latestSuitability.topCandidates?.[0];
    parts.push(
      topCandidate
        ? `${recentAnalysis.latestSuitability.name}에서 1위 후보는 ${topCandidate.title}(${topCandidate.score}점)`
        : `${recentAnalysis.latestSuitability.name} 입지점수를 계산했습니다`,
    );
  }

  if (!parts.length) {
    return "";
  }

  return `${parts.join(", ")}입니다.`;
}

function buildSummaryHeadline({
  schoolName,
  topicLabel,
  publicLayerCount,
  studentFeatureCount,
  topCategory,
  recentAnalysis,
}) {
  const analysisInsight = buildAnalysisInsight(recentAnalysis);

  if (studentFeatureCount === 0) {
    return `${schoolName} 지역에서 ${topicLabel} 탐색을 시작할 준비가 되었습니다. 공공 레이어를 켜고 학생 레이어에 객체를 추가해 보세요.`;
  }

  if (publicLayerCount === 0) {
    return `${schoolName} 주변에서 학생 조사 ${studentFeatureCount}건이 기록되었습니다. 이제 공공 레이어를 함께 켜서 공간 패턴을 비교해 보세요.`;
  }

  if (topCategory) {
    return analysisInsight
      ? `${schoolName} 주변에서 "${topCategory[0]}" 관련 기록이 가장 많았고, ${analysisInsight}`
      : `${schoolName} 주변에서 "${topCategory[0]}" 관련 기록이 가장 많았습니다.`;
  }

  return analysisInsight
    ? `${schoolName} 영역에서 공공 레이어와 학생 레이어를 겹쳐 보고 있으며, ${analysisInsight}`
    : `${schoolName} 영역에서 공공 레이어와 학생 레이어를 겹쳐 보고 있습니다.`;
}

function buildInsights({
  publicLayerSummary,
  visibleStudentLayerSummary,
  studentFeatureCount,
  topCategory,
  topGeometry,
  topSeverity,
  reflectionNote,
  recentAnalysis,
}) {
  const insights = [];

  insights.push(`공공 레이어: ${publicLayerSummary}`);
  insights.push(`학생 레이어: ${visibleStudentLayerSummary}`);

  if (studentFeatureCount > 0) {
    if (topCategory) {
      insights.push(`가장 많이 기록된 주제는 "${topCategory[0]}"이고 총 ${pluralizeCountLabel(topCategory[1], "건")}입니다.`);
    }

    if (topGeometry) {
      insights.push(`가장 많이 사용한 도형은 ${GEOMETRY_LABEL[topGeometry[0]] ?? topGeometry[0]}이고 총 ${pluralizeCountLabel(topGeometry[1], "건")}입니다.`);
    }

    if (topSeverity) {
      insights.push(`중요도 분포에서는 "${topSeverity[0]}" 평가가 가장 많습니다.`);
    }
  }

  if (recentAnalysis.latestBuffer?.name) {
    const latestBufferName = recentAnalysis.latestBuffer.name.includes("버퍼")
      ? recentAnalysis.latestBuffer.name
      : `${recentAnalysis.latestBuffer.name} 버퍼`;
    const bufferParts = [
      latestBufferName,
      recentAnalysis.latestBuffer.areaLabel ? `면적 ${recentAnalysis.latestBuffer.areaLabel}` : "",
      recentAnalysis.latestBuffer.perimeterLabel ? `둘레 ${recentAnalysis.latestBuffer.perimeterLabel}` : "",
    ].filter(Boolean);
    insights.push(bufferParts.join(" · "));
  }

  if (recentAnalysis.latestMeasurement?.title && recentAnalysis.latestMeasurement?.primaryValue) {
    insights.push(
      `최근 ${recentAnalysis.latestMeasurement.title.toLowerCase()} 결과: ${recentAnalysis.latestMeasurement.primaryLabel} ${recentAnalysis.latestMeasurement.primaryValue}`,
    );
  }

  if (recentAnalysis.latestSuitability?.name) {
    const candidates = recentAnalysis.latestSuitability.topCandidates ?? [];
    if (candidates.length) {
      insights.push(
        `입지점수 상위 후보: ${candidates
          .map((candidate) => `${candidate.rank}위 ${candidate.title} ${candidate.score}점`)
          .join(", ")}`,
      );
    } else {
      insights.push(`${recentAnalysis.latestSuitability.name} 입지점수 레이어를 만들었습니다.`);
    }
  }

  if (reflectionNote.trim()) {
    insights.push(`직접 정리한 지역성 문장: ${reflectionNote.trim()}`);
  } else if (studentFeatureCount > 0) {
    insights.push("공공 레이어와 학생 조사 레이어를 겹쳐 보고, 어떤 위치에 기록이 모이는지 한 문장으로 정리해 보세요.");
  }

  return insights;
}

function buildPresentationText({
  schoolName,
  topicLabel,
  publicLayerSummary,
  visibleStudentLayers,
  studentFeatureCount,
  topCategory,
  topGeometry,
  reflectionNote,
  recentAnalysis,
}) {
  if (studentFeatureCount === 0) {
    return `${schoolName} 영역에서 ${topicLabel} 탐색을 위해 먼저 공공 레이어를 켜고 학생 조사 객체를 기록해야 합니다.`;
  }

  const studentLayerNames = summarizeLabels(
    visibleStudentLayers.map((layer) => layer.name),
    "학생 조사 레이어",
  );
  const categorySentence = topCategory
    ? `"${topCategory[0]}" 기록이 가장 많고`
    : "학생 조사 기록이 쌓였고";
  const geometrySentence = topGeometry
    ? `${GEOMETRY_LABEL[topGeometry[0]] ?? topGeometry[0]} 형태 기록이 중심이었습니다.`
    : "여러 도형으로 공간 특성을 표현했습니다.";
  const analysisInsight = buildAnalysisInsight(recentAnalysis);

  if (reflectionNote.trim()) {
    return `${schoolName} 영역에서 ${publicLayerSummary} 레이어와 ${studentLayerNames}를 겹쳐 보니 학생 조사 ${studentFeatureCount}건 중 ${categorySentence} ${geometrySentence} ${analysisInsight ? `${analysisInsight} ` : ""}직접 해석한 지역성은 "${reflectionNote.trim()}"입니다.`;
  }

  return `${schoolName} 영역에서 ${publicLayerSummary} 레이어와 ${studentLayerNames}를 겹쳐 보니 학생 조사 ${studentFeatureCount}건 중 ${categorySentence} ${geometrySentence} ${analysisInsight ? `${analysisInsight} ` : ""}이제 이 패턴이 무엇을 뜻하는지 한 문장으로 정리하면 발표 준비가 됩니다.`;
}

export function buildWorkspaceSummary({
  schoolName,
  topicLabel,
  activePublicLayers,
  studentLayers,
  reflectionNote = "",
  recentAnalysis = {},
}) {
  const visibleStudentLayers = studentLayers.filter((layer) => layer.visible);
  const studentFeatureCount = visibleStudentLayers.reduce(
    (total, layer) => total + layer.features.length,
    0,
  );
  const publicLayerLabels = activePublicLayers.map((layer) => layer.label);
  const publicLayerSummary = summarizeLabels(publicLayerLabels, "선택된 공공 레이어 없음");
  const visibleStudentLayerSummary = visibleStudentLayers.length
    ? `${visibleStudentLayers.length}개 레이어 / ${studentFeatureCount}개 객체`
    : "아직 학생 조사 레이어가 없습니다";

  const {
    geometryCounts,
    categoryCounts,
    severityCounts,
  } = collectStudentFeatureFacts(visibleStudentLayers);

  const topCategory = getTopEntry(categoryCounts);
  const topGeometry = getTopEntry(geometryCounts);
  const topSeverity = getTopEntry(severityCounts);
  const analysisInsight = buildAnalysisInsight(recentAnalysis);

  const snapshots = [
    {
      label: "공공 레이어",
      value: pluralizeCountLabel(activePublicLayers.length),
      detail: publicLayerSummary,
    },
    {
      label: "학생 레이어",
      value: pluralizeCountLabel(visibleStudentLayers.length),
      detail: visibleStudentLayers.length
        ? summarizeLabels(visibleStudentLayers.map((layer) => layer.name), "학생 조사 레이어")
        : "점 · 선 · 면 레이어를 추가해 보세요.",
    },
    {
      label: "학생 객체",
      value: pluralizeCountLabel(studentFeatureCount),
      detail: topCategory
        ? `가장 많이 기록된 주제: ${topCategory[0]}`
        : "아직 조사 객체가 없습니다",
    },
    {
      label: "최근 분석",
      value: analysisInsight ? "있음" : "-",
      detail: analysisInsight || "버퍼, 측정, 입지점수 결과가 아직 없습니다.",
    },
  ];

  return {
    headline: buildSummaryHeadline({
      schoolName,
      topicLabel,
      publicLayerCount: activePublicLayers.length,
      studentFeatureCount,
      topCategory,
      recentAnalysis,
    }),
    snapshots,
    insights: buildInsights({
      publicLayerSummary,
      visibleStudentLayerSummary,
      studentFeatureCount,
      topCategory,
      topGeometry,
      topSeverity,
      reflectionNote,
      recentAnalysis,
    }),
    presentationText: buildPresentationText({
      schoolName,
      topicLabel,
      publicLayerSummary,
      visibleStudentLayers,
      studentFeatureCount,
      topCategory,
      topGeometry,
      reflectionNote,
      recentAnalysis,
    }),
    helperText: reflectionNote.trim()
      ? "자동 요약에 최근 버퍼, 측정, 입지점수 결과를 함께 반영했습니다."
      : "버퍼, 측정, 입지점수를 만든 뒤 지역성 한 줄 정리를 넣으면 발표 문장이 더 구체적으로 됩니다.",
  };
}
