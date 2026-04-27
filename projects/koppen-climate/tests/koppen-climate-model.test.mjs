import assert from "node:assert/strict";

import { LATITUDES, LONGITUDES, analyzeLocation, buildWorld, classifyKoppen } from "../app/climate-model.mjs";

function run() {
  const tropical = classifyKoppen(Array.from({ length: 12 }, () => 26), Array.from({ length: 12 }, () => 180), 4, 1);
  assert.equal(tropical.code, "Af");

  const desert = classifyKoppen(Array.from({ length: 12 }, () => 25), Array.from({ length: 12 }, () => 6), 24, 1);
  assert.equal(desert.code, "BWh");

  const temperateBoundary = classifyKoppen([-2, 0, 5, 11, 16, 21, 24, 23, 18, 12, 6, 1], Array.from({ length: 12 }, () => 80), 42, 1);
  assert.equal(temperateBoundary.code, "Cfa");

  const continentalBoundary = classifyKoppen([-3, -1, 4, 10, 16, 21, 24, 23, 18, 11, 5, 0], Array.from({ length: 12 }, () => 80), 42, 1);
  assert.equal(continentalBoundary.code, "Dfa");

  const humidTropics = analyzeLocation(1.3, 103.8, { presetId: "earthLite", month: 7 });
  const sahara = analyzeLocation(25.0, 32.5, { presetId: "earthLite", month: 7 });
  assert.equal(humidTropics.classification.code, "Af");
  assert.equal(sahara.classification.code, "BWh");
  assert.ok(humidTropics.selectedMonth.precipitation > sahara.selectedMonth.precipitation + 100);
  assert.ok(humidTropics.annual.annualPrecip > sahara.annual.annualPrecip + 1000);

  const world = buildWorld({ presetId: "oceanWorld", month: 7 });
  assert.equal(world.cellCount, LATITUDES.length * LONGITUDES.length);
  assert.equal(world.koppenCodes.length, world.cellCount);
  assert.ok(world.cellCount > 20000);
  assert.ok(world.koppenCodes.includes("Ocean"));

  console.log("koppen-climate-model: ok");
}

run();
