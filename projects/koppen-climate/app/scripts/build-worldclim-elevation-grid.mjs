import fs from "node:fs/promises";
import path from "node:path";
import { fromFile } from "geotiff";

const APP_ROOT = path.resolve(process.argv[2] ?? path.join(process.cwd(), "apps", "koppen-climate-lab"));
const RAW_FILE = path.join(APP_ROOT, "data", "worldclim", "raw", "wc2.1_10m_elev", "wc2.1_10m_elev.tif");
const OUTPUT_FILE = path.join(APP_ROOT, "data", "real-elevation-data.mjs");
const STEP_DEGREES = Number(process.argv[3] ?? 0.5);
const SAMPLE_OFFSET = STEP_DEGREES * 0.24;
const SAMPLE_OFFSETS = [
  [0, 0],
  [-SAMPLE_OFFSET, -SAMPLE_OFFSET],
  [-SAMPLE_OFFSET, SAMPLE_OFFSET],
  [SAMPLE_OFFSET, -SAMPLE_OFFSET],
  [SAMPLE_OFFSET, SAMPLE_OFFSET],
];

if (!Number.isFinite(STEP_DEGREES) || STEP_DEGREES <= 0) {
  throw new Error(`Invalid grid step: ${process.argv[3] ?? "undefined"}`);
}
if (Math.abs((180 / STEP_DEGREES) - Math.round(180 / STEP_DEGREES)) > 1e-9) {
  throw new Error(`Grid step must divide 180 evenly. Received ${STEP_DEGREES}.`);
}
if (Math.abs((360 / STEP_DEGREES) - Math.round(360 / STEP_DEGREES)) > 1e-9) {
  throw new Error(`Grid step must divide 360 evenly. Received ${STEP_DEGREES}.`);
}

const LATITUDES = Array.from({ length: Math.round(180 / STEP_DEGREES) + 1 }, (_, index) => -90 + index * STEP_DEGREES);
const LONGITUDES = Array.from({ length: Math.round(360 / STEP_DEGREES) }, (_, index) => -180 + index * STEP_DEGREES);
const CELL_COUNT = LATITUDES.length * LONGITUDES.length;

function arrayLiteral(values) {
  return `[${values.join(",")}]`;
}

function round(value, digits = 0) {
  const factor = 10 ** digits;
  return Math.round(value * factor) / factor;
}

function wrapLongitude(longitude) {
  let value = Number(longitude);
  while (value < -180) {
    value += 360;
  }
  while (value > 180) {
    value -= 360;
  }
  return value === 180 ? -180 : value;
}

async function loadRaster(filePath) {
  const tiff = await fromFile(filePath);
  const image = await tiff.getImage();
  const raster = await image.readRasters({ interleave: true });
  const [minX, minY, maxX, maxY] = image.getBoundingBox();
  const noData = image.getGDALNoData();

  return {
    data: raster,
    width: image.getWidth(),
    height: image.getHeight(),
    minX,
    minY,
    maxX,
    maxY,
    noData: noData == null ? null : Number(noData),
  };
}

function sampleRasterValue(raster, longitude, latitude) {
  const xRatio = (longitude - raster.minX) / (raster.maxX - raster.minX);
  const yRatio = (raster.maxY - latitude) / (raster.maxY - raster.minY);
  const column = Math.min(raster.width - 1, Math.max(0, Math.floor(xRatio * raster.width)));
  const row = Math.min(raster.height - 1, Math.max(0, Math.floor(yRatio * raster.height)));
  const index = row * raster.width + column;
  const value = raster.data[index];

  if (!Number.isFinite(value)) {
    return null;
  }
  if (raster.noData != null && value === raster.noData) {
    return null;
  }

  return Number(value);
}

function sampleCellElevation(raster, longitude, latitude) {
  const samples = [];
  for (const [lonOffset, latOffset] of SAMPLE_OFFSETS) {
    const sampleLon = wrapLongitude(longitude + lonOffset);
    const sampleLat = Math.max(-90, Math.min(90, latitude + latOffset));
    const value = sampleRasterValue(raster, sampleLon, sampleLat);
    if (value != null) {
      samples.push(value);
    }
  }

  if (!samples.length) {
    return 0;
  }

  return round(samples.reduce((total, value) => total + value, 0) / samples.length, 0);
}

async function buildGrid() {
  const raster = await loadRaster(RAW_FILE);
  const elevation = new Float32Array(CELL_COUNT);

  for (let latIndex = 0; latIndex < LATITUDES.length; latIndex += 1) {
    const latitude = LATITUDES[latIndex];
    for (let lonIndex = 0; lonIndex < LONGITUDES.length; lonIndex += 1) {
      const longitude = LONGITUDES[lonIndex];
      const cellIndex = latIndex * LONGITUDES.length + lonIndex;
      elevation[cellIndex] = sampleCellElevation(raster, longitude, latitude);
    }
  }

  return {
    elevation,
  };
}

async function writeModule(grid) {
  const moduleSource = `export const REAL_ELEVATION_GRID_META = ${JSON.stringify(
    {
      dataset: "WorldClim 2.1 elevation",
      period: "static topography",
      sourceResolution: "10 minutes",
      resolution: `${STEP_DEGREES} degree analysis grid`,
      source: "https://www.worldclim.org/data/worldclim21.html",
      generatedAt: new Date().toISOString(),
      latStepDegrees: STEP_DEGREES,
      lonStepDegrees: STEP_DEGREES,
      cellCount: CELL_COUNT,
      sampleMethod: "5-point mean within each cell",
    },
    null,
    2,
  )};

export const REAL_ELEVATION_GRID = {
  elevation: new Float32Array(${arrayLiteral(Array.from(grid.elevation, (value) => round(value, 0)))}),
};
`;

  await fs.writeFile(OUTPUT_FILE, moduleSource, "utf8");
}

async function main() {
  const grid = await buildGrid();
  await writeModule(grid);
  console.log(`Wrote ${OUTPUT_FILE}`);
  console.log(`Grid step: ${STEP_DEGREES} degree`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
