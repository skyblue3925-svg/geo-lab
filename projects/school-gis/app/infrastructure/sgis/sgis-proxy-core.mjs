export const DEFAULT_SGIS_API_BASE = "https://sgisapi.kostat.go.kr/OpenAPI3";
export const MIN_SGIS_YEAR = 2015;
export const MAX_SGIS_YEAR = 2023;

const SGIS_STATS_RESOURCE_PATHS = new Map([
  ["population", "stats/population.json"],
  ["household", "stats/household.json"],
  ["house", "stats/house.json"],
  ["company", "stats/company.json"],
]);

function normalizeApiBaseUrl(apiBaseUrl) {
  return String(apiBaseUrl || DEFAULT_SGIS_API_BASE).replace(/\/$/, "");
}

export function normalizeYear(value) {
  const parsed = Number.parseInt(String(value ?? ""), 10);
  if (!Number.isInteger(parsed) || parsed < MIN_SGIS_YEAR || parsed > MAX_SGIS_YEAR) {
    throw new Error(`year must be between ${MIN_SGIS_YEAR} and ${MAX_SGIS_YEAR}.`);
  }

  return String(parsed);
}

export function normalizeAdmCd(value) {
  const normalized = String(value ?? "").trim();
  if (!normalized) {
    return "";
  }

  if (normalized === "non") {
    return normalized;
  }

  if (!/^\d{2,8}$/.test(normalized)) {
    throw new Error("admCd must be blank, non, or a 2-8 digit administrative code.");
  }

  return normalized;
}

export function normalizeLowSearch(value) {
  const normalized = String(value ?? "1").trim();
  if (!["0", "1", "2"].includes(normalized)) {
    throw new Error("lowSearch must be 0, 1, or 2.");
  }

  return normalized;
}

export function normalizeStatsResource(value) {
  const normalized = String(value ?? "population").trim();
  if (!SGIS_STATS_RESOURCE_PATHS.has(normalized)) {
    throw new Error("statsResource must be one of population, household, house, or company.");
  }

  return normalized;
}

export function normalizeGridLevelDiv(value) {
  const normalized = String(value ?? "").trim();
  if (!["100km", "10km", "1km", "500m", "100m"].includes(normalized)) {
    throw new Error("gridLevelDiv must be one of 100km, 10km, 1km, 500m, or 100m.");
  }

  return normalized;
}

export function normalizeLatitude(value) {
  const parsed = Number.parseFloat(String(value ?? ""));
  if (!Number.isFinite(parsed) || parsed < 33 || parsed > 39.5) {
    throw new Error("lat must be a valid Korean latitude.");
  }

  return parsed;
}

export function normalizeLongitude(value) {
  const parsed = Number.parseFloat(String(value ?? ""));
  if (!Number.isFinite(parsed) || parsed < 124 || parsed > 132.5) {
    throw new Error("lng must be a valid Korean longitude.");
  }

  return parsed;
}

async function fetchJson(url, fetchImpl) {
  let response;
  try {
    response = await fetchImpl(url);
  } catch (error) {
    const reason = error?.cause?.message || error?.message || "network request failed";
    throw new Error(`SGIS request failed: ${reason}`);
  }

  if (!response.ok) {
    throw new Error(`SGIS request failed (${response.status})`);
  }

  return response.json();
}

function assertSgisSuccess(payload, label) {
  if (Number(payload?.errCd) !== 0) {
    throw new Error(`${label}: ${payload?.errMsg ?? "Unknown SGIS error"}`);
  }

  return payload;
}

async function fetchAccessToken({
  apiBaseUrl,
  consumerKey,
  consumerSecret,
  fetchImpl,
}) {
  if (!consumerKey || !consumerSecret) {
    throw new Error("Missing SGIS_CONSUMER_KEY / SGIS_CONSUMER_SECRET.");
  }

  const authUrl = new URL(`${apiBaseUrl}/auth/authentication.json`);
  authUrl.searchParams.set("consumer_key", consumerKey);
  authUrl.searchParams.set("consumer_secret", consumerSecret);

  const authPayload = assertSgisSuccess(
    await fetchJson(authUrl.toString(), fetchImpl),
    "SGIS authentication",
  );

  const accessToken = authPayload?.result?.accessToken;
  if (!accessToken) {
    throw new Error("SGIS authentication did not return an access token.");
  }

  return accessToken;
}

export function parseSgisPopulationRequest(requestUrl, apiBaseUrl = DEFAULT_SGIS_API_BASE) {
  return {
    year: normalizeYear(requestUrl.searchParams.get("year") ?? String(MAX_SGIS_YEAR)),
    admCd: normalizeAdmCd(requestUrl.searchParams.get("admCd")),
    lowSearch: normalizeLowSearch(requestUrl.searchParams.get("lowSearch")),
    statsResource: normalizeStatsResource(requestUrl.searchParams.get("statsResource")),
    apiBaseUrl: normalizeApiBaseUrl(apiBaseUrl),
  };
}

export function parseSgisGridRequest(requestUrl, apiBaseUrl = DEFAULT_SGIS_API_BASE) {
  return {
    admCd: normalizeAdmCd(requestUrl.searchParams.get("admCd")),
    gridLevelDiv: normalizeGridLevelDiv(requestUrl.searchParams.get("gridLevelDiv")),
    apiBaseUrl: normalizeApiBaseUrl(apiBaseUrl),
  };
}

export function parseSgisRegionCodeRequest(requestUrl, apiBaseUrl = DEFAULT_SGIS_API_BASE) {
  return {
    lat: normalizeLatitude(requestUrl.searchParams.get("lat")),
    lng: normalizeLongitude(requestUrl.searchParams.get("lng")),
    apiBaseUrl: normalizeApiBaseUrl(apiBaseUrl),
  };
}

export async function fetchSgisPopulationPayload({
  requestUrl,
  apiBaseUrl = DEFAULT_SGIS_API_BASE,
  consumerKey,
  consumerSecret,
  fetchImpl = fetch,
}) {
  const normalizedRequest = parseSgisPopulationRequest(requestUrl, apiBaseUrl);
  const accessToken = await fetchAccessToken({
    apiBaseUrl: normalizedRequest.apiBaseUrl,
    consumerKey,
    consumerSecret,
    fetchImpl,
  });

  const boundaryParams = new URLSearchParams({
    accessToken,
    year: normalizedRequest.year,
    low_search: normalizedRequest.lowSearch,
  });
  const statsParams = new URLSearchParams({
    accessToken,
    year: normalizedRequest.year,
    low_search: normalizedRequest.lowSearch,
  });

  if (normalizedRequest.admCd) {
    boundaryParams.set("adm_cd", normalizedRequest.admCd);
    statsParams.set("adm_cd", normalizedRequest.admCd);
  }

  const statsResourcePath = SGIS_STATS_RESOURCE_PATHS.get(normalizedRequest.statsResource);
  const [boundaryPayload, statsPayload] = await Promise.all([
    fetchJson(
      `${normalizedRequest.apiBaseUrl}/boundary/hadmarea.geojson?${boundaryParams.toString()}`,
      fetchImpl,
    ),
    fetchJson(
      `${normalizedRequest.apiBaseUrl}/${statsResourcePath}?${statsParams.toString()}`,
      fetchImpl,
    ),
  ]);

  const safeBoundaryPayload = assertSgisSuccess(boundaryPayload, "SGIS boundary");
  const safeStatsPayload = assertSgisSuccess(statsPayload, "SGIS population");

  return {
    year: normalizedRequest.year,
    admCd: normalizedRequest.admCd,
    lowSearch: normalizedRequest.lowSearch,
    statsResource: normalizedRequest.statsResource,
    boundary: {
      type: safeBoundaryPayload.type,
      features: Array.isArray(safeBoundaryPayload.features)
        ? safeBoundaryPayload.features
        : [],
    },
    statsRows: Array.isArray(safeStatsPayload.result) ? safeStatsPayload.result : [],
  };
}

export async function fetchSgisGridPayload({
  requestUrl,
  apiBaseUrl = DEFAULT_SGIS_API_BASE,
  consumerKey,
  consumerSecret,
  fetchImpl = fetch,
}) {
  const normalizedRequest = parseSgisGridRequest(requestUrl, apiBaseUrl);
  const accessToken = await fetchAccessToken({
    apiBaseUrl: normalizedRequest.apiBaseUrl,
    consumerKey,
    consumerSecret,
    fetchImpl,
  });

  const gridParams = new URLSearchParams({
    accessToken,
    grid_level_div: normalizedRequest.gridLevelDiv,
  });

  if (normalizedRequest.admCd) {
    gridParams.set("adm_cd", normalizedRequest.admCd);
  }

  const gridPayload = assertSgisSuccess(
    await fetchJson(
      `${normalizedRequest.apiBaseUrl}/grid/data.geojson?${gridParams.toString()}`,
      fetchImpl,
    ),
    "SGIS grid",
  );

  return {
    admCd: normalizedRequest.admCd,
    gridLevelDiv: normalizedRequest.gridLevelDiv,
    boundary: {
      type: gridPayload.type,
      features: Array.isArray(gridPayload.features) ? gridPayload.features : [],
    },
  };
}

export async function fetchSgisRegionCodePayload({
  requestUrl,
  apiBaseUrl = DEFAULT_SGIS_API_BASE,
  consumerKey,
  consumerSecret,
  fetchImpl = fetch,
}) {
  const normalizedRequest = parseSgisRegionCodeRequest(requestUrl, apiBaseUrl);
  const accessToken = await fetchAccessToken({
    apiBaseUrl: normalizedRequest.apiBaseUrl,
    consumerKey,
    consumerSecret,
    fetchImpl,
  });

  const regionParams = new URLSearchParams({
    accessToken,
    x_coor: String(normalizedRequest.lng),
    y_coor: String(normalizedRequest.lat),
    addr_type: "20",
  });

  const regionPayload = assertSgisSuccess(
    await fetchJson(
      `${normalizedRequest.apiBaseUrl}/addr/rgeocodewgs84.json?${regionParams.toString()}`,
      fetchImpl,
    ),
    "SGIS reverse geocode",
  );

  const region = Array.isArray(regionPayload.result) ? regionPayload.result[0] : null;
  if (!region) {
    throw new Error("SGIS reverse geocode returned no region.");
  }

  return {
    lat: normalizedRequest.lat,
    lng: normalizedRequest.lng,
    sidoCd: String(region.sido_cd ?? "").trim(),
    sidoNm: String(region.sido_nm ?? "").trim(),
    sggCd: `${String(region.sido_cd ?? "").trim()}${String(region.sgg_cd ?? "").trim()}`,
    sggNm: String(region.sgg_nm ?? "").trim(),
    emdongCd: `${String(region.sido_cd ?? "").trim()}${String(region.sgg_cd ?? "").trim()}${String(region.emdong_cd ?? "").trim()}`,
    emdongNm: String(region.emdong_nm ?? "").trim(),
    fullAddr: String(region.full_addr ?? "").trim(),
  };
}
