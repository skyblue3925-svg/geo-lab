import fs from "node:fs/promises";
import path from "node:path";

const APP_ROOT = path.resolve(process.argv[2] ?? path.join(process.cwd(), "apps", "koppen-climate-lab"));
const INPUT_FILE = path.join(APP_ROOT, "data", "beck-v2", "extracted", "ensemble_mean_1p0_1991_2020.nc");
const OUTPUT_FILE = path.join(APP_ROOT, "data", "real-climate-data.mjs");
const STEP_DEGREES = 1;

const LATITUDES = Array.from({ length: 181 }, (_, index) => -90 + index * STEP_DEGREES);
const LONGITUDES = Array.from({ length: 360 }, (_, index) => -180 + index * STEP_DEGREES);
const CELL_COUNT = LATITUDES.length * LONGITUDES.length;
const SOURCE_LON_COUNT = 360;
const SOURCE_LAT_COUNT = 180;
const FILL_VALUE = -9999;

function round(value, digits = 2) {
  const factor = 10 ** digits;
  return Math.round(value * factor) / factor;
}

function arrayLiteral(values) {
  return `[${values.join(",")}]`;
}

function isValidSourceValue(value) {
  return Number.isFinite(value) && value > FILL_VALUE + 1;
}

function getSourceIndex(monthIndex, latIndex, lonIndex) {
  return monthIndex * SOURCE_LAT_COUNT * SOURCE_LON_COUNT + latIndex * SOURCE_LON_COUNT + lonIndex;
}

function wrapLongitudeCoordinate(longitude) {
  const shifted = longitude + 179.5;
  return ((shifted % 360) + 360) % 360;
}

function clampLatitudeCoordinate(latitude) {
  return Math.max(0, Math.min(SOURCE_LAT_COUNT - 1, 89.5 - latitude));
}

function interpolateField(values, monthIndex, latitude, longitude) {
  const x = wrapLongitudeCoordinate(longitude);
  const y = clampLatitudeCoordinate(latitude);

  const x0 = Math.floor(x);
  const x1 = (x0 + 1) % SOURCE_LON_COUNT;
  const y0 = Math.floor(y);
  const y1 = Math.min(SOURCE_LAT_COUNT - 1, y0 + 1);
  const fx = x - x0;
  const fy = y - y0;

  const corners = [
    { weight: (1 - fx) * (1 - fy), value: values[getSourceIndex(monthIndex, y0, x0)] },
    { weight: fx * (1 - fy), value: values[getSourceIndex(monthIndex, y0, x1)] },
    { weight: (1 - fx) * fy, value: values[getSourceIndex(monthIndex, y1, x0)] },
    { weight: fx * fy, value: values[getSourceIndex(monthIndex, y1, x1)] },
  ];

  let totalWeight = 0;
  let weightedValue = 0;

  for (const corner of corners) {
    if (!isValidSourceValue(corner.value) || corner.weight <= 0) {
      continue;
    }
    totalWeight += corner.weight;
    weightedValue += corner.value * corner.weight;
  }

  if (!totalWeight) {
    return null;
  }

  return weightedValue / totalWeight;
}

async function loadSourceDatasets() {
  const h5wasm = await import("h5wasm/node");
  await h5wasm.ready;
  const file = new h5wasm.File(INPUT_FILE, "r");
  const temperature = file.get("air_temperature").value;
  const precipitation = file.get("precipitation").value;
  return { file, temperature, precipitation };
}

async function buildGrid() {
  const { file, temperature, precipitation } = await loadSourceDatasets();
  const monthlyTemperature = Array.from({ length: 12 }, () => new Float32Array(CELL_COUNT));
  const monthlyPrecipitation = Array.from({ length: 12 }, () => new Float32Array(CELL_COUNT));
  const landMask = new Uint8Array(CELL_COUNT);

  for (let latIndex = 0; latIndex < LATITUDES.length; latIndex += 1) {
    const latitude = LATITUDES[latIndex];
    for (let lonIndex = 0; lonIndex < LONGITUDES.length; lonIndex += 1) {
      const longitude = LONGITUDES[lonIndex];
      const cellIndex = latIndex * LONGITUDES.length + lonIndex;
      let validMonths = 0;

      for (let monthIndex = 0; monthIndex < 12; monthIndex += 1) {
        const sampledTemperature = interpolateField(temperature, monthIndex, latitude, longitude);
        const sampledPrecipitation = interpolateField(precipitation, monthIndex, latitude, longitude);
        if (sampledTemperature != null && sampledPrecipitation != null) {
          validMonths += 1;
          monthlyTemperature[monthIndex][cellIndex] = round(sampledTemperature, 2);
          monthlyPrecipitation[monthIndex][cellIndex] = round(sampledPrecipitation, 2);
        }
      }

      landMask[cellIndex] = validMonths === 12 ? 1 : 0;
      if (!landMask[cellIndex]) {
        for (let monthIndex = 0; monthIndex < 12; monthIndex += 1) {
          monthlyTemperature[monthIndex][cellIndex] = 0;
          monthlyPrecipitation[monthIndex][cellIndex] = 0;
        }
      }
    }
  }

  file.close();

  const annualTemperature = new Float32Array(CELL_COUNT);
  const annualPrecipitation = new Float32Array(CELL_COUNT);
  for (let cellIndex = 0; cellIndex < CELL_COUNT; cellIndex += 1) {
    if (!landMask[cellIndex]) {
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
      dataset: "Beck et al. underlying monthly climate data",
      period: "1991-2020",
      sourceResolution: "1 degree",
      resolution: "1 degree analysis grid",
      source: "https://doi.org/10.6084/m9.figshare.21789074.v2",
      generatedAt: new Date().toISOString(),
      latStepDegrees: STEP_DEGREES,
      lonStepDegrees: STEP_DEGREES,
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
