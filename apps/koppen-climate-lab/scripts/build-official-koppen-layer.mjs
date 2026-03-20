import fs from "node:fs/promises";
import path from "node:path";
import { fromFile } from "geotiff";

function rgbToHex(red, green, blue) {
  return `#${[red, green, blue].map((value) => value.toString(16).padStart(2, "0")).join("")}`;
}

function parseLegend(text) {
  const entries = [];
  const lines = text.split(/\r?\n/);

  for (const line of lines) {
    const match = line.match(/^\s*(\d+):\s+([A-Z][A-Za-z]{1,2})\s+(.*?)\s+\[(\d+)\s+(\d+)\s+(\d+)\]\s*$/);
    if (!match) {
      continue;
    }

    const id = Number(match[1]);
    const code = match[2];
    const label = match[3].trim();
    const rgb = [Number(match[4]), Number(match[5]), Number(match[6])];

    entries.push({
      id,
      code,
      label,
      rgb,
      color: rgbToHex(rgb[0], rgb[1], rgb[2]),
    });
  }

  return entries.sort((left, right) => left.id - right.id);
}

function buildModuleSource(metadata, entries, binaryUrl) {
  const entriesJson = JSON.stringify(entries, null, 2);
  const metadataJson = JSON.stringify(metadata, null, 2);

  return `export const OFFICIAL_KOPPEN_META = ${metadataJson};

export const OFFICIAL_KOPPEN_BINARY_URL = ${JSON.stringify(binaryUrl)};

export const OFFICIAL_KOPPEN_CLASSES = Object.freeze(${entriesJson});

export const OFFICIAL_KOPPEN_BY_ID = Object.freeze(
  Object.fromEntries(OFFICIAL_KOPPEN_CLASSES.map((entry) => [entry.id, entry])),
);

export const OFFICIAL_KOPPEN_BY_CODE = Object.freeze(
  Object.fromEntries(OFFICIAL_KOPPEN_CLASSES.map((entry) => [entry.code, entry])),
);
`;
}

async function main() {
  const appDir = process.argv[2]
    ? path.resolve(process.argv[2])
    : path.resolve("C:/Users/HANSOL/OneDrive/Desktop/Geo-lab/apps/koppen-climate-lab");

  const sourceDir = path.join(appDir, "data", "koppen-official");
  const tifPath = path.join(sourceDir, "1991_2020", "koppen_geiger_0p1.tif");
  const legendPath = path.join(sourceDir, "legend.txt");
  const outputBinaryPath = path.join(appDir, "data", "koppen-geiger-1991-2020-0p1.bin");
  const outputModulePath = path.join(appDir, "data", "koppen-geiger-1991-2020.mjs");

  const legendText = await fs.readFile(legendPath, "utf8");
  const entries = parseLegend(legendText);
  if (!entries.length) {
    throw new Error("Legend parsing failed.");
  }

  const tif = await fromFile(tifPath);
  const image = await tif.getImage();
  const raster = await image.readRasters({ interleave: true });
  const codes = raster instanceof Uint8Array ? raster : Uint8Array.from(raster);

  await fs.writeFile(outputBinaryPath, Buffer.from(codes.buffer, codes.byteOffset, codes.byteLength));

  const metadata = {
    dataset: "Beck et al. Koppen-Geiger climate classification",
    version: 2,
    period: "1991-2020",
    resolutionDegrees: 0.1,
    width: image.getWidth(),
    height: image.getHeight(),
    bbox: image.getBoundingBox(),
    nodata: Number(image.getGDALNoData() ?? 0),
    source: "https://doi.org/10.6084/m9.figshare.21789074.v2",
    generatedAt: new Date().toISOString(),
  };

  const moduleSource = buildModuleSource(metadata, entries, "./data/koppen-geiger-1991-2020-0p1.bin");
  await fs.writeFile(outputModulePath, moduleSource, "utf8");

  console.log(
    JSON.stringify(
      {
        binary: outputBinaryPath,
        module: outputModulePath,
        width: metadata.width,
        height: metadata.height,
        classes: entries.length,
      },
      null,
      2,
    ),
  );
}

await main();
