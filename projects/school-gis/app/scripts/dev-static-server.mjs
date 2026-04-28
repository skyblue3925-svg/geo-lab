import http from "node:http";
import { readFile, stat } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import {
  DEFAULT_SGIS_API_BASE,
  fetchSgisGridPayload,
  fetchSgisPopulationPayload,
  fetchSgisRegionCodePayload,
} from "../infrastructure/sgis/sgis-proxy-core.mjs";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const rootDir = path.resolve(__dirname, "..");
const port = Number.parseInt(process.argv[2] ?? "8787", 10);

const mimeTypes = new Map([
  [".html", "text/html; charset=utf-8"],
  [".js", "text/javascript; charset=utf-8"],
  [".mjs", "text/javascript; charset=utf-8"],
  [".css", "text/css; charset=utf-8"],
  [".json", "application/json; charset=utf-8"],
  [".geojson", "application/geo+json; charset=utf-8"],
  [".txt", "text/plain; charset=utf-8"],
  [".svg", "image/svg+xml"],
  [".png", "image/png"],
  [".jpg", "image/jpeg"],
  [".jpeg", "image/jpeg"],
  [".ico", "image/x-icon"],
]);

function jsonResponse(response, payload, status = 200) {
  response.writeHead(status, {
    "content-type": "application/json; charset=utf-8",
    "cache-control": status === 200 ? "public, max-age=1800" : "no-store",
  });
  response.end(JSON.stringify(payload, null, 2));
}

function resolvePath(urlPathname) {
  const safePath = decodeURIComponent(urlPathname.split("?")[0]);
  const normalized = safePath === "/" ? "/index.html" : safePath;
  const absolutePath = path.resolve(rootDir, `.${normalized}`);
  if (!absolutePath.startsWith(rootDir)) {
    return null;
  }
  return absolutePath;
}

async function handleLocalSgisPopulation(request, response) {
  try {
    const requestUrl = new URL(request.url ?? "/", `http://${request.headers.host}`);
    const payload = await fetchSgisPopulationPayload({
      requestUrl,
      apiBaseUrl: process.env.SGIS_API_BASE_URL || DEFAULT_SGIS_API_BASE,
      consumerKey: process.env.SGIS_CONSUMER_KEY,
      consumerSecret: process.env.SGIS_CONSUMER_SECRET,
      fetchImpl: fetch,
    });

    jsonResponse(response, payload);
  } catch (error) {
    jsonResponse(
      response,
      {
        error: error instanceof Error ? error.message : "Unknown SGIS proxy error.",
      },
      500,
    );
  }
}

async function handleLocalSgisRegionCode(request, response) {
  try {
    const requestUrl = new URL(request.url ?? "/", `http://${request.headers.host}`);
    const payload = await fetchSgisRegionCodePayload({
      requestUrl,
      apiBaseUrl: process.env.SGIS_API_BASE_URL || DEFAULT_SGIS_API_BASE,
      consumerKey: process.env.SGIS_CONSUMER_KEY,
      consumerSecret: process.env.SGIS_CONSUMER_SECRET,
      fetchImpl: fetch,
    });

    jsonResponse(response, payload);
  } catch (error) {
    jsonResponse(
      response,
      {
        error: error instanceof Error ? error.message : "Unknown SGIS proxy error.",
      },
      500,
    );
  }
}

async function handleLocalSgisGrid(request, response) {
  try {
    const requestUrl = new URL(request.url ?? "/", `http://${request.headers.host}`);
    const payload = await fetchSgisGridPayload({
      requestUrl,
      apiBaseUrl: process.env.SGIS_API_BASE_URL || DEFAULT_SGIS_API_BASE,
      consumerKey: process.env.SGIS_CONSUMER_KEY,
      consumerSecret: process.env.SGIS_CONSUMER_SECRET,
      fetchImpl: fetch,
    });

    jsonResponse(response, payload);
  } catch (error) {
    jsonResponse(
      response,
      {
        error: error instanceof Error ? error.message : "Unknown SGIS proxy error.",
      },
      500,
    );
  }
}

const server = http.createServer(async (request, response) => {
  try {
    const requestUrl = new URL(request.url ?? "/", `http://${request.headers.host}`);

    if (requestUrl.pathname === "/api/sgis/population") {
      await handleLocalSgisPopulation(request, response);
      return;
    }

    if (requestUrl.pathname === "/api/sgis/region-code") {
      await handleLocalSgisRegionCode(request, response);
      return;
    }

    if (requestUrl.pathname === "/api/sgis/grid") {
      await handleLocalSgisGrid(request, response);
      return;
    }

    const absolutePath = resolvePath(requestUrl.pathname);
    if (!absolutePath) {
      response.writeHead(403, { "content-type": "text/plain; charset=utf-8" });
      response.end("Forbidden");
      return;
    }

    let targetPath = absolutePath;
    try {
      const fileStat = await stat(targetPath);
      if (fileStat.isDirectory()) {
        targetPath = path.join(targetPath, "index.html");
      }
    } catch {
      if (!path.extname(targetPath)) {
        targetPath = path.join(targetPath, "index.html");
      }
    }

    const payload = await readFile(targetPath);
    const extension = path.extname(targetPath).toLowerCase();
    response.writeHead(200, {
      "content-type": mimeTypes.get(extension) ?? "application/octet-stream",
      "cache-control": "no-store",
    });
    response.end(payload);
  } catch (error) {
    if (error?.code === "ENOENT") {
      response.writeHead(404, { "content-type": "text/plain; charset=utf-8" });
      response.end("Not Found");
      return;
    }

    response.writeHead(500, { "content-type": "text/plain; charset=utf-8" });
    response.end("Server Error");
    console.error(error);
  }
});

server.listen(port, "127.0.0.1", () => {
  const sgisReady = Boolean(process.env.SGIS_CONSUMER_KEY && process.env.SGIS_CONSUMER_SECRET);
  console.log(`School GIS dev server running at http://127.0.0.1:${port}/`);
  console.log(`SGIS local proxy: ${sgisReady ? "enabled" : "disabled (missing SGIS_CONSUMER_KEY / SGIS_CONSUMER_SECRET)"}`);
});
