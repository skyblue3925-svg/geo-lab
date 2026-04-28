export const SGIS_REGION_LAYER_PROFILES = Object.freeze([
  {
    id: "region-emdong",
    type: "stats",
    label: "현재 위치 읍면동",
    description: "고정한 위치가 포함된 읍면동 경계와 통계를 불러옵니다.",
    codeField: "emdongCd",
    lowSearch: "0",
    clipToReference: true,
  },
  {
    id: "region-korea-sido",
    type: "stats",
    label: "전국 시도 전체",
    description: "전국을 시도 단위로 나눠 통계 레이어를 불러옵니다.",
    staticAdmCd: "non",
    lowSearch: "1",
  },
  {
    id: "region-sgg-children",
    type: "stats",
    label: "현재 주변 읍면동",
    description: "고정한 위치가 속한 시군구에서 현재 반경과 겹치는 읍면동만 보여줍니다.",
    codeField: "sggCd",
    lowSearch: "1",
    clipToReference: true,
  },
  {
    id: "region-sido-children",
    type: "stats",
    label: "현재 주변 시군구",
    description: "고정한 위치가 속한 시도에서 현재 반경과 겹치는 시군구만 보여줍니다.",
    codeField: "sidoCd",
    lowSearch: "1",
    clipToReference: true,
  },
  {
    id: "grid-korea-10km",
    type: "grid",
    label: "전국 10km 격자",
    description: "전국을 10km 격자로 나눠 보여줍니다. 데이터가 많아 느릴 수 있습니다.",
    staticAdmCd: "00",
    statsAdmCd: "non",
    statsLowSearch: "1",
    gridLevelDiv: "10km",
  },
  {
    id: "grid-sido-10km",
    type: "grid",
    label: "현재 주변 10km 격자",
    description: "고정 위치 주변을 10km 격자로 보여줍니다.",
    codeField: "sidoCd",
    statsCodeField: "sidoCd",
    statsLowSearch: "1",
    gridLevelDiv: "10km",
    clipToReference: true,
  },
  {
    id: "grid-sgg-1km",
    type: "grid",
    label: "현재 주변 1km 격자",
    description: "고정 위치 주변을 1km 격자로 보여줍니다.",
    codeField: "sggCd",
    statsCodeField: "sggCd",
    statsLowSearch: "1",
    gridLevelDiv: "1km",
    clipToReference: true,
  },
  {
    id: "grid-sgg-500m",
    type: "grid",
    label: "현재 주변 500m 격자",
    description: "고정 위치 주변을 500m 격자로 촘촘하게 보여줍니다.",
    codeField: "sggCd",
    statsCodeField: "sggCd",
    statsLowSearch: "1",
    gridLevelDiv: "500m",
    clipToReference: true,
  },
  {
    id: "grid-emdong-100m",
    type: "grid",
    label: "현재 주변 100m 격자",
    description: "고정 위치 주변을 100m 격자로 보여줍니다. 넓은 읍면동에서는 SGIS 제한으로 실패할 수 있습니다.",
    codeField: "emdongCd",
    statsCodeField: "emdongCd",
    statsLowSearch: "0",
    gridLevelDiv: "100m",
    clipToReference: true,
  },
]);

const profileMap = new Map(
  SGIS_REGION_LAYER_PROFILES.map((profile) => [profile.id, profile]),
);

function requireRegionValue(value, label) {
  if (!value) {
    throw new Error(`${label} 범위를 정할 수 없습니다. 먼저 위치를 검색해 고정해 주세요.`);
  }

  return value;
}

export function getSgisRegionLayerProfile(profileId) {
  return profileMap.get(profileId) ?? SGIS_REGION_LAYER_PROFILES[1];
}

export function buildRegionSgisSummary({ locationLabel, region, pending, locked = true }) {
  if (!locked) {
    return "먼저 지도 위 검색창에서 위치를 찾고 결과를 선택하세요. 위치를 고정해야 SGIS 행정구역과 통계를 정확히 불러옵니다.";
  }

  if (pending) {
    return `${locationLabel} 기준 행정구역을 확인하는 중입니다.`;
  }

  if (!region) {
    return `${locationLabel} 기준으로 SGIS 행정구역을 아직 확인하지 않았습니다. 행정구역 확인 버튼을 누르거나 범위를 선택해 불러오세요.`;
  }

  const parts = [region.sidoNm, region.sggNm, region.emdongNm].filter(Boolean);
  const addressLabel = parts.length ? parts.join(" ") : region.fullAddr || "행정구역 확인 완료";
  return `고정 위치: ${addressLabel}. 아래에서 행정단위와 통계항목을 골라 여러 레이어로 중첩할 수 있습니다.`;
}

export function buildRegionSgisImportPlan({
  profileId,
  region,
  year,
  metricId,
  color,
  scope = "both",
}) {
  const profile = getSgisRegionLayerProfile(profileId);
  const admCd = profile.staticAdmCd ?? requireRegionValue(region?.[profile.codeField], profile.label);

  if (profile.type === "grid") {
    return {
      sourceType: "grid",
      admCd,
      statsAdmCd: profile.statsAdmCd ?? region?.[profile.statsCodeField ?? profile.codeField] ?? admCd,
      statsLowSearch: profile.statsLowSearch ?? "1",
      gridLevelDiv: profile.gridLevelDiv,
      year,
      metricId,
      color,
      scope,
      profile,
      scopeLabel: profile.label,
      clipToReference: Boolean(profile.clipToReference),
    };
  }

  return {
    sourceType: "stats",
    admCd,
    lowSearch: profile.lowSearch,
    year,
    metricId,
    color,
    scope,
    profile,
    scopeLabel: profile.label,
    clipToReference: Boolean(profile.clipToReference),
  };
}
