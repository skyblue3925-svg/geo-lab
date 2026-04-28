export const SGIS_SCHOOL_LAYER_PROFILES = Object.freeze([
  {
    id: "school-emdong",
    label: "학교가 속한 행정동",
    description: "학교가 속한 행정동 1개만 불러옵니다. 가장 가볍고 빠르게 비교할 수 있습니다.",
    codeField: "emdongCd",
    lowSearch: "0",
  },
  {
    id: "school-sgg-children",
    label: "학교가 속한 시군구의 읍면동",
    description: "학교가 속한 시군구 아래 읍면동을 함께 불러옵니다.",
    codeField: "sggCd",
    lowSearch: "1",
  },
  {
    id: "school-sido-children",
    label: "학교가 속한 시도의 시군구",
    description: "학교가 속한 시도 아래 시군구를 함께 불러옵니다.",
    codeField: "sidoCd",
    lowSearch: "1",
  },
]);

const profileMap = new Map(
  SGIS_SCHOOL_LAYER_PROFILES.map((profile) => [profile.id, profile]),
);

function requireRegionValue(value, label) {
  if (!value) {
    throw new Error(`${label} 코드를 찾지 못했습니다. 학교 위치를 다시 확인해 주세요.`);
  }

  return value;
}

export function getSgisSchoolLayerProfile(profileId) {
  return profileMap.get(profileId) ?? SGIS_SCHOOL_LAYER_PROFILES[1];
}

export function buildSchoolSgisRegionSummary({ schoolName, region, pending }) {
  if (pending) {
    return `${schoolName} 위치가 포함된 행정구역을 확인하는 중입니다.`;
  }

  if (!region) {
    return `${schoolName} 위치를 기준으로 실제 SGIS 통계를 불러올 수 있습니다. 먼저 학교를 검색하거나 지도 중심을 학교 위치로 맞춰 주세요.`;
  }

  const parts = [region.sidoNm, region.sggNm, region.emdongNm].filter(Boolean);
  const addressLabel = parts.length ? parts.join(" ") : region.fullAddr || "행정구역 확인 완료";
  return `${schoolName} 위치는 ${addressLabel}로 확인되었습니다. 이 기준으로 가까운 SGIS 통계를 바로 불러올 수 있습니다.`;
}

export function buildSchoolSgisImportPlan({
  profileId,
  region,
  year,
  metricId,
  color,
  scope = "school",
}) {
  const profile = getSgisSchoolLayerProfile(profileId);
  const admCd = requireRegionValue(
    region?.[profile.codeField],
    profile.label,
  );

  return {
    admCd,
    lowSearch: profile.lowSearch,
    year,
    metricId,
    color,
    scope,
    profile,
  };
}
