import fs from "node:fs/promises";
import path from "node:path";
import { fromFile } from "geotiff";

const APP_ROOT = path.resolve(process.argv[2] ?? path.join(process.cwd(), "apps", "koppen-climate-lab"));
const RAW_DIR = path.join(APP_ROOT, "data", "worldclim", "raw");
const OUTPUT_FILE = path.join(APP_ROOT, "data", "real-climate-data.mjs");
const LATITUDES = Array.from({ length: 37 }, (_, index) => -90 + index * 5);
const LONGITUDES = Array.from({ length: 72 }, (_, index) => -180 + index * 5);
const CELL_COUNT = LATITUDES.length * LONGITUDES.length;

function round(value, digits = 2) {
  const factor = 10 ** digits;
  return Math.round(value * factor) / factor;
}

function arrayLiteral(values) {
  return `[${values.join(",")}]`;
}

async function getVariableFiles(variable) {
  const entries = await fs.readdir(RAW_DIR);
  const regex = new RegExp(`^wc2\\.1_10m_${variable}_(\\d{2})\\.tif$`, "i");
  const matches = entries
    .map((entry) => ({ entry, match: entry.match(regex) }))
    .filter((item) => item.match)
    .sort((left, right) => Number(left.match[1]) - Number(right.match[1]))
    .map((item) => path.join(RAW_DIR, item.entry));

  if (matches.length !== 12) {
    throw new Error(`Expected 12 monthly GeoTIFF files for ${variable}, found ${matches.length}.`);
  }

  return matches;
}

async function loadRaster(filePath) {
  const tiff = await fromFile(filePath);
  const image = await tiff.getImage();
  const raster = await image.readRasters({ interleave: true });
  const [minX, minY, maxX, maxY] = image.getBoundingBox();
  const noData = image.getGDALNoData();

  return {
    filePath,
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

  return value;
}

function normalizeTemperature(value) {
  if (value == null) {
    return null;
  }
  return Math.abs(value) > 100 ? value / 10 : value;
}

function normalizePrecipitation(value) {
  if (value == null) {
    return null;
  }
  return value;
}

async function buildGrid() {
  const [temperatureFiles, precipitationFiles] = await Promise.all([
    getVariableFiles("tavg"),
    getVariableFiles("prec"),
  ]);

  const monthlyTemperature = Array.from({ length: 12 }, () => new Float32Array(CELL_COUNT));
  const monthlyPrecipitation = Array.from({ length: 12 }, () => new Float32Array(CELL_COUNT));
  const landMask = new Uint8Array(CELL_COUNT);

  for (let monthIndex = 0; monthIndex < 12; monthIndex += 1) {
    const [temperatureRaster, precipitationRaster] = await Promise.all([
      loadRaster(temperatureFiles[monthIndex]),
      loadRaster(precipitationFiles[monthIndex]),
    ]);

    for (let latIndex = 0; latIndex < LATITUDES.length; latIndex += 1) {
      for (let lonIndex = 0; lonIndex < LONGITUDES.length; lonIndex += 1) {
        const latitude = LATITUDES[latIndex];
        const longitude = LONGITUDES[lonIndex];
        const cellIndex = latIndex * LONGITUDES.length + lonIndex;
        const temperature = normalizeTemperature(sampleRasterValue(temperatureRaster, longitude, latitude));
        const precipitation = normalizePrecipitation(sampleRasterValue(precipitationRaster, longitude, latitude));
        const isLand = temperature != null && precipitation != null;

        if (monthIndex === 0) {
          landMask[cellIndex] = isLand ? 1 : 0;
        } else if (landMask[cellIndex] && !isLand) {
          landMask[cellIndex] = 0;
        }

        monthlyTemperature[monthIndex][cellIndex] = temperature ?? 0;
        monthlyPrecipitation[monthIndex][cellIndex] = precipitation ?? 0;
      }
    }

    console.log(`Processed month ${monthIndex + 1} / 12`);
  }

  const annualTemperature = new Float32Array(CELL_COUNT);
  const annualPrecipitation = new Float32Array(CELL_COUNT);

  for (let cellIndex = 0; cellIndex < CELL_COUNT; cellIndex += 1) {
    if (!landMask[cellIndex]) {
      annualTemperature[cellIndex] = 0;
      annualPrecipitation[cellIndex] = 0;
      for (let monthIndex = 0; monthIndex < 12; monthIndex += 1) {
        monthlyTemperature[monthIndex][cellIndex] = 0;
        monthlyPrecipitation[monthIndex][cellIndex] = 0;
      }
      continue;
    }

    let temperatureTotal = 0;
    let precipitationTotal = 0;
    for (let monthIndex = 0; monthIndex < 12; monthIndex += 1) {
      temperatureTotal += monthlyTemperature[monthIndex][cellIndex];
      precipitationTotal += monthlyPrecipitation[monthIndex][cellIndex];
    }
    annualTemperature[cellIndex] = round(temperatureTotal / 12, 2);
    annualPrecipitation[cellIndex] = round(precipitationTotal, 2);
  }

  return {
    landMask,
    monthlyTemperature,
    monthlyPrecipitation,
    annualTemperature,
    annualPrecipitation,
  };
}

async function writeModule(grid) {
  const moduleSource = `export const REAL_CLIMATE_GRID_META = ${JSON.stringify(
    {
      dataset: "WorldClim 2.1 historical climate",
      period: "1970-2000",
      resolution: "10 minutes",
      source: "https://www.worldclim.org/data/worldclim21.html",
      generatedAt: new Date().toISOString(),
      latStepDegrees: 5,
      lonStepDegrees: 5,
      cellCount: CELL_COUNT,
    },
    null,
    2,
  )};

export const REAL_CLIMATE_GRID = {
  landMask: new Uint8Array(${arrayLiteral(Array.from(grid.landMask))}),
  monthlyTemperature: [
${grid.monthlyTemperature
  .map((values) => `    new Float32Array(${arrayLiteral(Array.from(values, (value) => round(value, 2)))})`)
  .join(",\n")}
  ],
  monthlyPrecipitation: [
${grid.monthlyPrecipitation
  .map((values) => `    new Float32Array(${arrayLiteral(Array.from(values, (value) => round(value, 2)))})`)
  .join(",\n")}
  ],
  annualTemperature: new Float32Array(${arrayLiteral(Array.from(grid.annualTemperature, (value) => round(value, 2)))}),
  annualPrecipitation: new Float32Array(${arrayLiteral(Array.from(grid.annualPrecipitation, (value) => round(value, 2)))}),
};
`;

  await fs.writeFile(OUTPUT_FILE, moduleSource, "utf8");
}

async function main() {
  const grid = await buildGrid();
  await writeModule(grid);

  const landCells = Array.from(grid.landMask).reduce((total, value) => total + value, 0);
  console.log(`Wrote ${OUTPUT_FILE}`);
  console.log(`Land cells: ${landCells} / ${CELL_COUNT}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
