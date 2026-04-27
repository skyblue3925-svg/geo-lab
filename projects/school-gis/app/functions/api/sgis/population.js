const DEFAULT_SGIS_API_BASE = "https://sgisapi.kostat.go.kr/OpenAPI3";
const MIN_YEAR = 2015;
const MAX_YEAR = 2023;

function buildJsonResponse(payload, status = 200) {
  return new Response(JSON.stringify(payload, null, 2), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": status === 200 ? "public, max-age=1800" : "no-store",
    },
  });
}

function normalizeYear(value) {
  const parsed = Number.parseInt(String(value ?? ""), 10);
  if (!Number.isInteger(parsed) || parsed < MIN_YEAR || parsed > MAX_YEAR) {
    throw new Error(`year must be between ${MIN_YEAR} and ${MAX_YEAR}.`);
  }
  return String(parsed);
}

function normalizeAdmCd(value) {
  const normalized = String(value ?? "").trim();
  if (!normalized) {
    return "";
  }
  if (!/^\d{2,8}$/.test(normalized)) {
    throw new Error("admCd must be blank or a 2-8 digit administrative code.");
  }
  return normalized;
}

function normalizeLowSearch(value) {
  const normalized = String(value ?? "1").trim();
  if (!["0", "1", "2"].includes(normalized)) {
    throw new Error("lowSearch must be 0, 1, or 2.");
  }
  return normalized;
}

async function fetchJson(url) {
  const response = await fetch(url);
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

async function fetchAccessToken(env, apiBaseUrl) {
  const consumerKey = env.SGIS_CONSUMER_KEY;
  const consumerSecret = env.SGIS_CONSUMER_SECRET;

  if (!consumerKey || !consumerSecret) {
    throw new Error("Missing Cloudflare environment variables SGIS_CONSUMER_KEY / SGIS_CONSUMER_SECRET.");
  }

  const authUrl = new URL(`${apiBaseUrl}/auth/authentication.json`);
  authUrl.searchParams.set("consumer_key", consumerKey);
  authUrl.searchParams.set("consumer_secret", consumerSecret);

  const authPayload = assertSgisSuccess(
    await fetchJson(authUrl.toString()),
    "SGIS authentication",
  );

  const accessToken = authPayload?.result?.accessToken;
  if (!accessToken) {
    throw new Error("SGIS authentication did not return an access token.");
  }

  return accessToken;
}

export async function onRequestGet(context) {
  try {
    const requestUrl = new URL(context.request.url);
    const year = normalizeYear(requestUrl.searchParams.get("year") ?? String(MAX_YEAR));
    const admCd = normalizeAdmCd(requestUrl.searchParams.get("admCd"));
    const lowSearch = normalizeLowSearch(requestUrl.searchParams.get("lowSearch"));
    const apiBaseUrl = String(
      context.env.SGIS_API_BASE_URL || DEFAULT_SGIS_API_BASE,
    ).replace(/\/$/, "");

    const accessToken = await fetchAccessToken(context.env, apiBaseUrl);

    const boundaryParams = new URLSearchParams({
      accessToken,
      year,
      low_search: lowSearch,
    });
    const statsParams = new URLSearchParams({
      accessToken,
      year,
      low_search: lowSearch,
    });

    if (admCd) {
      boundaryParams.set("adm_cd", admCd);
      statsParams.set("adm_cd", admCd);
    }

    const [boundaryPayload, statsPayload] = await Promise.all([
      fetchJson(`${apiBaseUrl}/boundary/hadmarea.geojson?${boundaryParams.toString()}`),
      fetchJson(`${apiBaseUrl}/stats/population.json?${statsParams.toString()}`),
    ]);

    const safeBoundaryPayload = assertSgisSuccess(boundaryPayload, "SGIS boundary");
    const safeStatsPayload = assertSgisSuccess(statsPayload, "SGIS population");

    return buildJsonResponse({
      year,
      admCd,
      lowSearch,
      boundary: {
        type: safeBoundaryPayload.type,
        features: Array.isArray(safeBoundaryPayload.features)
          ? safeBoundaryPayload.features
          : [],
      },
      statsRows: Array.isArray(safeStatsPayload.result)
        ? safeStatsPayload.result
        : [],
    });
  } catch (error) {
    return buildJsonResponse(
      {
        error: error instanceof Error ? error.message : "Unknown SGIS proxy error.",
      },
      500,
    );
  }
}
