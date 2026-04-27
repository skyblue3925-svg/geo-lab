import {
  DEFAULT_SGIS_API_BASE,
  fetchSgisGridPayload,
  fetchSgisPopulationPayload,
  fetchSgisRegionCodePayload,
} from "./infrastructure/sgis/sgis-proxy-core.mjs";

function jsonResponse(payload, status = 200) {
  return new Response(JSON.stringify(payload, null, 2), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": status === 200 ? "public, max-age=1800" : "no-store",
    },
  });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname === "/api/sgis/population") {
      try {
        const payload = await fetchSgisPopulationPayload({
          requestUrl: url,
          apiBaseUrl: env.SGIS_API_BASE_URL || DEFAULT_SGIS_API_BASE,
          consumerKey: env.SGIS_CONSUMER_KEY,
          consumerSecret: env.SGIS_CONSUMER_SECRET,
        });

        return jsonResponse(payload);
      } catch (error) {
        return jsonResponse(
          {
            error: error instanceof Error ? error.message : "Unknown SGIS proxy error.",
          },
          500,
        );
      }
    }

    if (url.pathname === "/api/sgis/region-code") {
      try {
        const payload = await fetchSgisRegionCodePayload({
          requestUrl: url,
          apiBaseUrl: env.SGIS_API_BASE_URL || DEFAULT_SGIS_API_BASE,
          consumerKey: env.SGIS_CONSUMER_KEY,
          consumerSecret: env.SGIS_CONSUMER_SECRET,
        });

        return jsonResponse(payload);
      } catch (error) {
        return jsonResponse(
          {
            error: error instanceof Error ? error.message : "Unknown SGIS proxy error.",
          },
          500,
        );
      }
    }

    if (url.pathname === "/api/sgis/grid") {
      try {
        const payload = await fetchSgisGridPayload({
          requestUrl: url,
          apiBaseUrl: env.SGIS_API_BASE_URL || DEFAULT_SGIS_API_BASE,
          consumerKey: env.SGIS_CONSUMER_KEY,
          consumerSecret: env.SGIS_CONSUMER_SECRET,
        });

        return jsonResponse(payload);
      } catch (error) {
        return jsonResponse(
          {
            error: error instanceof Error ? error.message : "Unknown SGIS proxy error.",
          },
          500,
        );
      }
    }

    return env.ASSETS.fetch(request);
  },
};
