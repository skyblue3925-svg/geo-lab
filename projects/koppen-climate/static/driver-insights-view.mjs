import { MONTH_LABELS, getKoppenDetails } from "./climate-model.mjs";
import {
  getClassificationMetrics,
  getClimateComparisonNote,
  getGraphClimateCode,
  getGraphClimateCodeSource,
  getGraphClimateDisplayCode,
} from "./climate-interpretation.mjs";
import {
  describeKoppenClimateLink,
  describeMonthlyClimateFocus,
  describeRegionalSetting,
} from "./selection-insights.mjs";

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

function gaussian(distance, spread) {
  const ratio = distance / spread;
  return Math.exp(-(ratio * ratio));
}

function degToRad(value) {
  return (value * Math.PI) / 180;
}

function formatSigned(value, unit) {
  return `${value >= 0 ? "+" : ""}${value.toFixed(1)} ${unit}`;
}

function getDriverSectionSummary(title, observedMode) {
  const prefix = observedMode
    ? "관측값을 직접 역산한 값이 아니라, 같은 달을 읽기 위한 개념 모델입니다. "
    : "";
  return title.includes("기온")
    ? `${prefix}플러스 값은 이번 달 기온을 올리는 방향, 마이너스 값은 낮추는 방향을 뜻합니다. 막대 길이는 상대적인 영향 크기입니다.`
    : `${prefix}플러스 값은 이번 달 강수를 늘리는 방향, 마이너스 값은 줄이는 방향을 뜻합니다. 막대 길이는 상대적인 영향 크기입니다.`;
}

function describeDriver(driver, analysis, scenario) {
  switch (driver.key) {
    case "latitude-base":
      return `위도 ${Math.abs(analysis.latitude).toFixed(1)}°에서는 적도보다 평균 일사량이 적어 기본 온도대가 정해집니다. 적도에 가까울수록 값이 커지고 극으로 갈수록 작아집니다.`;
    case "ocean-land-adjustment":
      return analysis.profile.coastalness > analysis.profile.interiorness
        ? "바다와 가까우면 열용량이 큰 바다가 기온을 완화하고 수분 공급도 늘립니다. 해류 효과도 이 항목에 함께 반영됩니다."
        : "대륙 내부로 갈수록 해양 완충이 약해져 여름엔 더 뜨겁고 겨울엔 더 차가워지기 쉽습니다.";
    case "elevation-cooling":
      return Math.abs(driver.value) < 0.2
        ? "현재 위치는 큰 고도 효과가 거의 없습니다."
        : `고도가 높아질수록 공기가 팽창 냉각되어 기온이 내려갑니다. 현재는 고도 효과가 ${formatSigned(driver.value, driver.unit)}로 반영됩니다.`;
    case "season-shift":
      return `${MONTH_LABELS[scenario.month - 1]}에는 태양 직달점과 계절 가열 중심이 ${analysis.selectedMonth.declination >= 0 ? "북반구" : "남반구"} 쪽으로 치우쳐 있어 계절 이동 효과가 반영됩니다.`;
    case "foehn-warm":
      return Math.abs(driver.value) < 0.2
        ? "산을 넘은 뒤 하강하며 덥고 건조해지는 푄 성격은 약합니다."
        : "산맥 뒤쪽으로 공기가 내려오며 단열 가열될 때 푄 성격의 온난화가 더해집니다.";
    case "baseline-moisture":
      return "해양 접근성, 기본 수증기량, 해안 노출 정도가 합쳐진 출발 수분량입니다. 다른 항목들은 이 기본값 위에 강수를 더하거나 뺍니다.";
    case "itcz-rain":
      return Math.abs(analysis.latitude - analysis.selectedMonth.itczLat) < 12
        ? "현재 달에는 ITCZ가 가까워 상승기류와 대류성 비가 강해집니다."
        : "ITCZ와 멀수록 적도 저압대성 강수 기여는 약해집니다.";
    case "storm-track":
      return "중위도에서는 전선과 온대저기압이 자주 지나가며 비를 더합니다. 특히 편서풍대 해안에서 영향이 잘 나타납니다.";
    case "monsoon":
      return driver.value >= 0
        ? "육지와 바다의 가열 차가 커지면 계절풍이 발달해 우기에 강수가 집중됩니다."
        : "현재 달은 몬순 건기 성격이 강해 계절풍이 수분 공급보다 건조 효과로 작용합니다.";
    case "current-coast":
      return driver.value >= 0
        ? "따뜻한 해류나 습한 바닷바람은 해안 수분 공급을 늘려 강수를 도와줍니다."
        : "찬 해류나 건조한 연안 조건은 공기 안정도를 높여 강수를 줄이는 쪽으로 작용합니다.";
    case "orographic-wet":
      return Math.abs(driver.value) < 1
        ? "현재 위치는 산맥 바람받이 상승 효과가 약합니다."
        : "습한 공기가 산을 타고 오르며 냉각될 때 구름과 강수가 집중됩니다.";
    case "rain-shadow":
      return Math.abs(driver.value) < 1
        ? "현재 위치는 산맥 비그늘 효과가 약합니다."
        : "산을 넘은 뒤 내려오는 공기는 더 건조해져 강수가 줄어듭니다.";
    case "subtropical-dry":
      return "약 20~35° 부근의 아열대 고압대에서는 하강기류가 우세해 구름이 억제되고 건조해지기 쉽습니다.";
    case "interior-dry":
      return "대륙 안쪽으로 갈수록 바다에서 수분을 공급받기 어려워져 강수가 줄어듭니다.";
    case "polar-dry":
      return "한랭한 고위도 공기는 머금을 수 있는 수증기량 자체가 적어 강수가 많기 어렵습니다.";
    default:
      return "이 항목은 이번 달 기후값을 설명하는 기여 요인입니다.";
  }
}

export function getClimateDriverBreakdowns(analysis, scenario) {
  const absLat = Math.abs(analysis.latitude);
  const hemisphere = analysis.latitude === 0 ? 0 : Math.sign(analysis.latitude);
  const heatingSign = hemisphere === 0 ? 1 : hemisphere;
  const seasonWave = Math.sin(((scenario.month - 4) / 12) * Math.PI * 2);
  const currentTemp = scenario.currentBias * analysis.profile.coastalness * analysis.profile.currentZone * 3.4;
  const seasonAmplitude = clamp(
    (1.8 + absLat * 0.18) * (scenario.tilt / 23.4) + analysis.profile.interiorness * 9 - analysis.profile.coastalness * 4.5,
    0.8,
    26,
  );
  const latitudeBase = 29 - 0.39 * absLat - 0.0014 * absLat * absLat;
  const elevationCooling = -0.0057 * analysis.profile.elevation;
  const oceanLandAdjustment = analysis.profile.landness * 0.9 - analysis.profile.interiorness * 1.8 + currentTemp * 0.6;
  const solarPulse = (Math.cos(degToRad(analysis.latitude - analysis.selectedMonth.declination)) - Math.cos(degToRad(analysis.latitude))) * 9;
  const seasonalOffset = seasonAmplitude * seasonWave * heatingSign * (hemisphere === 0 ? 0.2 : 1);
  const summerHeating = Math.max(0, seasonWave * heatingSign);
  const winterCooling = Math.max(0, -seasonWave * heatingSign);
  const baselineMoisture = 18 + 32 * (1 - analysis.profile.landness) + 24 * analysis.profile.coastalness;
  const itczRain = 145 * gaussian(analysis.latitude - analysis.selectedMonth.itczLat, 11) * (0.75 + analysis.profile.oceanFetch * 0.35);
  const stormTrack = 62 * gaussian(absLat - 50, 10) * (0.5 + analysis.profile.oceanFetch * 0.5);
  const subtropicalDry = -78 * gaussian(absLat - 28, 8) * (0.65 + analysis.profile.interiorness);
  const interiorDry = -50 * analysis.profile.interiorness;
  const monsoonBand = clamp((absLat - 8) / 12, 0, 1) * clamp((38 - absLat) / 12, 0, 1);
  const monsoonWet = scenario.monsoonStrength * analysis.profile.landness * analysis.profile.oceanFetch * monsoonBand * summerHeating * 150;
  const monsoonDry = -scenario.monsoonStrength * analysis.profile.landness * monsoonBand * winterCooling * 34;
  const currentWet = scenario.currentBias * analysis.profile.coastalness * analysis.profile.currentZone * 24;
  const polarDry = -(absLat > 65 ? (absLat - 65) * 1.4 : 0);

  const temperature = [
    { key: "latitude-base", label: "위도 기본값", value: latitudeBase, unit: "°C" },
    { key: "ocean-land-adjustment", label: "해양/대륙 조정", value: oceanLandAdjustment, unit: "°C" },
    { key: "elevation-cooling", label: "지형 냉각", value: elevationCooling, unit: "°C" },
    { key: "season-shift", label: "계절 이동", value: solarPulse + seasonalOffset, unit: "°C" },
    { key: "foehn-warm", label: "푄 가열", value: analysis.selectedMonth.foehnWarm, unit: "°C" },
  ].map((driver) => ({ ...driver, description: describeDriver(driver, analysis, scenario) }));

  const precipitation = [
    { key: "baseline-moisture", label: "기본 수분", value: baselineMoisture, unit: "mm" },
    { key: "itcz-rain", label: "ITCZ", value: itczRain, unit: "mm" },
    { key: "storm-track", label: "중위도 저기압", value: stormTrack, unit: "mm" },
    { key: "monsoon", label: "몬순", value: monsoonWet + monsoonDry, unit: "mm" },
    { key: "current-coast", label: "해류/해안", value: currentWet, unit: "mm" },
    { key: "orographic-wet", label: "산맥 상승", value: analysis.selectedMonth.orographicWet, unit: "mm" },
    { key: "rain-shadow", label: "비그늘", value: -analysis.selectedMonth.shadowDry, unit: "mm" },
    { key: "subtropical-dry", label: "아열대 건조대", value: subtropicalDry, unit: "mm" },
    { key: "interior-dry", label: "내륙 건조", value: interiorDry, unit: "mm" },
    { key: "polar-dry", label: "극지 건조", value: polarDry, unit: "mm" },
  ].map((driver) => ({ ...driver, description: describeDriver(driver, analysis, scenario) }));

  return { temperature, precipitation };
}

export function buildDriverSectionMarkup(title, drivers, observedMode) {
  const maxAbs = Math.max(...drivers.map((item) => Math.abs(item.value)), 1);
  return `
    <section class="driver-section">
      <h3>${title}</h3>
      <p class="driver-section-copy">${getDriverSectionSummary(title, observedMode)}</p>
      ${drivers.map((driver) => {
        const width = (Math.abs(driver.value) / maxAbs) * 100;
        const toneClass = driver.value >= 0 ? "positive" : "negative";
        return `
            <article class="driver-row ${toneClass}">
              <div class="driver-row-head">
                <span>${driver.label}</span>
                <strong>${formatSigned(driver.value, driver.unit)}</strong>
              </div>
              <div class="driver-meter"><i style="width:${width}%"></i></div>
              <p class="driver-help">${driver.description}</p>
            </article>
          `;
      }).join("")}
    </section>
  `;
}

export function buildDriverInsightCardsMarkup({
  analysis,
  breakdowns,
  context,
  circulationPressureBand,
  circulationWind,
  observedMode,
  activeExamSpot,
  selectedMonth,
}) {
  const officialCode = analysis.classification.code;
  const graphCode = getGraphClimateCode(analysis, activeExamSpot);
  const graphDisplayCode = getGraphClimateDisplayCode(analysis, activeExamSpot);
  const graphCodeSource = getGraphClimateCodeSource(analysis, activeExamSpot);
  const comparisonNote = getClimateComparisonNote(analysis, activeExamSpot, observedMode);
  const details = getKoppenDetails(graphCode);
  const metrics = getClassificationMetrics(analysis);
  const monthLabel = MONTH_LABELS[selectedMonth - 1];
  const cards = [
    {
      eyebrow: "지역 특성",
      title: `${context.subtitle} 배경`,
      body: describeRegionalSetting({
        analysis,
        context,
        circulationPressureBand,
        circulationWindLabel: circulationWind.label,
        monthLabel,
      }),
    },
    {
      eyebrow: "쾨펜 연결",
      title: observedMode
        ? officialCode === graphCode
          ? `공식 코드 ${officialCode}`
          : `공식 ${officialCode} · 그래프 ${graphDisplayCode}`
        : `${officialCode} · ${details.label}`,
      body: describeKoppenClimateLink({
        analysis,
        isObservedMode: observedMode,
        officialCode,
        graphCode,
        graphDisplayCode,
        details,
        metrics,
        graphCodeSource,
        comparisonNote,
      }),
    },
    {
      eyebrow: "이번 달 핵심",
      title: `${monthLabel} 포인트`,
      body: describeMonthlyClimateFocus({
        analysis,
        breakdowns,
        graphCode,
        isObservedMode: observedMode,
      }),
    },
  ];

  return `
    <div class="driver-insight-grid">
      ${cards.map((card) => `
          <article class="driver-insight-card">
            <span>${card.eyebrow}</span>
            <strong>${card.title}</strong>
            <p>${card.body}</p>
          </article>
        `).join("")}
    </div>
  `;
}
