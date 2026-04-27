const runtimeConfig = window.__SCHOOL_GIS_RUNTIME_CONFIG__ ?? {};

function mergeMapCenter(baseCenter, overrideCenter) {
  if (!overrideCenter) {
    return baseCenter;
  }

  return {
    ...baseCenter,
    ...overrideCenter,
  };
}

function mergeStorage(baseStorage, overrideStorage) {
  if (!overrideStorage) {
    return baseStorage;
  }

  return {
    ...baseStorage,
    ...overrideStorage,
  };
}

const defaultPublicLayerCatalog = [];
const defaultWorkspacePresets = [];

export const APP_CONFIG = {
  appName: runtimeConfig.appName ?? "학생 GIS 작업공간",
  schoolName: runtimeConfig.schoolName ?? "탐색 중심",
  subtitle:
    runtimeConfig.subtitle
    ?? "카카오 지도 위에 SGIS 통계 레이어와 학생 벡터 레이어를 겹쳐 보는 교육용 webGIS",
  mapCenter: mergeMapCenter(
    {
      lat: 37.5665,
      lng: 126.978,
      label: "탐색 중심",
    },
    runtimeConfig.mapCenter,
  ),
  schoolRadiusMeters: runtimeConfig.schoolRadiusMeters ?? 1200,
  initialZoom: runtimeConfig.initialZoom ?? 15,
  mapProvider:
    runtimeConfig.mapProvider
    ?? (runtimeConfig.kakao?.javascriptKey ? "kakao" : "leaflet"),
  mapTile: {
    url:
      runtimeConfig.mapTile?.url
      ?? "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    attribution:
      runtimeConfig.mapTile?.attribution
      ?? '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    note:
      runtimeConfig.mapTile?.note
      ?? "카카오 키가 없을 때는 기본 OSM 타일을 사용합니다.",
  },
  kakao: {
    enabled: runtimeConfig.kakao?.enabled ?? true,
    javascriptKey: runtimeConfig.kakao?.javascriptKey ?? "",
    searchLimit: runtimeConfig.kakao?.searchLimit ?? 5,
  },
  storage: mergeStorage(
    {
      useSupabaseWhenConfigured: true,
      supabaseUrl: "",
      supabaseAnonKey: "",
      tableName: "gis_reports",
    },
    runtimeConfig.storage,
  ),
  moderation: {
    localDemoEnabled: runtimeConfig.moderation?.localDemoEnabled ?? true,
    localModeratorLabel: runtimeConfig.moderation?.localModeratorLabel ?? "로컬 데모",
    supportEmail: runtimeConfig.moderation?.supportEmail ?? "",
  },
  sgis: {
    enabled: runtimeConfig.sgis?.enabled ?? true,
    proxyPath: runtimeConfig.sgis?.proxyPath ?? "/api/sgis",
    apiBaseUrl:
      runtimeConfig.sgis?.apiBaseUrl ?? "https://sgisapi.kostat.go.kr/OpenAPI3",
    defaultYear: runtimeConfig.sgis?.defaultYear ?? 2023,
    defaultBoundaryYear: runtimeConfig.sgis?.defaultBoundaryYear ?? 2023,
    defaultAdmCd: runtimeConfig.sgis?.defaultAdmCd ?? "",
    defaultLowSearch: String(runtimeConfig.sgis?.defaultLowSearch ?? "1"),
    defaultMetric: runtimeConfig.sgis?.defaultMetric ?? "tot_ppltn",
  },
  publicLayerCatalog: runtimeConfig.publicLayerCatalog ?? defaultPublicLayerCatalog,
  workspacePresets: runtimeConfig.workspacePresets ?? defaultWorkspacePresets,
};
