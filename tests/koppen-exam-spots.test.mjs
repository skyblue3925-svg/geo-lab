import assert from "node:assert/strict";

import { EXAM_CLIMATE_SPOTS } from "../projects/koppen-climate/app/data/exam-climate-spots.mjs";
import {
  getClimateComparisonNote,
  getGraphClimateCode,
  getGraphClimateDisplayCode,
} from "../projects/koppen-climate/app/climate-interpretation.mjs";

function run() {
  const capeTown = EXAM_CLIMATE_SPOTS.find((spot) => spot.displayName === "케이프타운");
  assert.ok(capeTown, "케이프타운 기출 지점이 있어야 합니다.");
  assert.equal(capeTown.examCode, "Cs");
  assert.ok(capeTown.sourceTexts.some((text) => text.includes("케이프타운 Cs")));

  const analysis = {
    latitude: -33.9249,
    temperatures: [22, 22, 20, 18, 15, 13, 12, 13, 15, 17, 19, 21],
    precipitations: [10, 8, 12, 50, 80, 100, 110, 90, 60, 12, 10, 8],
    classification: { code: "Csa" },
    referenceClassification: { code: "Csa" },
    highlandAssist: null,
    profile: { landness: 1, elevation: 15 },
  };
  const staleExamSpot = {
    examCode: "Cw",
    examCount: 5,
    displayName: "케이프타운",
  };
  const compatibleExamSpot = {
    examCode: "Cs",
    examCount: 5,
    displayName: "케이프타운",
  };

  assert.equal(getGraphClimateCode(analysis, staleExamSpot), "Csa");
  assert.equal(getGraphClimateDisplayCode(analysis, staleExamSpot), "Csa");

  const comparisonNote = getClimateComparisonNote(analysis, staleExamSpot, true);
  assert.equal(comparisonNote?.examMismatch, true);
  assert.ok(comparisonNote?.summary.includes("앱 계산값은 Csa입니다."));

  const compatibleNote = getClimateComparisonNote(analysis, compatibleExamSpot, true);
  assert.equal(compatibleNote?.examMismatch, false);
  assert.equal(compatibleNote?.examReferenceStatus, "compatible");
  assert.ok(compatibleNote?.summary.includes("2차 구분까지 같습니다."));

  console.log("koppen-exam-spots: ok");
}

run();
