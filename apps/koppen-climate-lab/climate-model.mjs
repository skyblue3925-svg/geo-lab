const TWO_PI = Math.PI * 2;
const MONTH_MID_DAYS = [15, 45, 74, 105, 135, 166, 196, 227, 258, 288, 319, 349];

import { REAL_CLIMATE_GRID, REAL_CLIMATE_GRID_META } from "./data/real-climate-data.mjs";

export const CLIMATE_DATA_MODE = "observed";
export const ACTIVE_CLIMATE_DATASET = Object.freeze({
  mode: CLIMATE_DATA_MODE,
  ...REAL_CLIMATE_GRID_META,
});

export const MONTH_LABELS = ["1월", "2월", "3월", "4월", "5월", "6월", "7월", "8월", "9월", "10월", "11월", "12월"];
export const LATITUDES = Array.from({ length: 37 }, (_, index) => -90 + index * 5);
export const LONGITUDES = Array.from({ length: 72 }, (_, index) => -180 + index * 5);

export const KOPPEN_COLORS = {
  Ocean: "#21495c",
  Af: "#1f6f43",
  Am: "#2d9257",
  Aw: "#7aa63f",
  As: "#b2b44f",
  BWh: "#d75a2a",
  BWk: "#d9a487",
  BSh: "#cc862f",
  BSk: "#c8ac67",
  Csa: "#d9bb3f",
  Csb: "#bfa552",
  Csc: "#989562",
  Cfa: "#73b85a",
  Cfb: "#5aa56d",
  Cfc: "#427f69",
  Cwa: "#8fc95d",
  Cwb: "#6ea96b",
  Cwc: "#547f67",
  Dsa: "#8b72bc",
  Dsb: "#745da8",
  Dsc: "#5e4b92",
  Dsd: "#493979",
  Dfa: "#63bfd1",
  Dfb: "#4a9fbe",
  Dfc: "#34748f",
  Dfd: "#244c63",
  Dwa: "#89b0ee",
  Dwb: "#668dd2",
  Dwc: "#4a69ad",
  Dwd: "#324781",
  ET: "#b6c0c8",
  EF: "#edf1f5",
};

const KOPPEN_META = {
  Ocean: { group: "해양", label: "해양 셀", summary: "쾨펜 기후구분은 원칙적으로 육상 기후 구분이라 해양 셀은 참고값만 보여줍니다." },
  Af: { group: "열대", label: "열대우림", summary: "매달 덥고 충분히 습합니다." },
  Am: { group: "열대", label: "열대몬순", summary: "연중 덥지만 짧은 약건기와 강한 우기가 있습니다." },
  Aw: { group: "열대", label: "사바나, 겨울 건기", summary: "항상 덥지만 겨울이 뚜렷한 건기입니다." },
  As: { group: "열대", label: "사바나, 여름 건기", summary: "항상 덥지만 여름이 상대적으로 건조합니다." },
  BWh: { group: "건조", label: "고온 사막", summary: "증발 요구량이 강수보다 훨씬 큽니다." },
  BWk: { group: "건조", label: "냉량 사막", summary: "건조하지만 연평균 기온은 낮은 편입니다." },
  BSh: { group: "건조", label: "고온 스텝", summary: "사막 직전 수준으로 건조합니다." },
  BSk: { group: "건조", label: "냉량 스텝", summary: "건조하면서 겨울이 춥습니다." },
  Csa: { group: "온대", label: "지중해성, 더운 여름", summary: "여름 건기와 더운 여름이 결합합니다." },
  Csb: { group: "온대", label: "지중해성, 온난한 여름", summary: "여름 건기지만 여름 최고온은 더 낮습니다." },
  Csc: { group: "온대", label: "지중해성, 서늘한 여름", summary: "여름 건기와 짧은 서늘한 여름이 나타납니다." },
  Cfa: { group: "온대", label: "습윤 온대", summary: "사계절 강수가 비교적 고르고 여름이 덥습니다." },
  Cfb: { group: "온대", label: "서안 해양성", summary: "사계절 습윤하고 여름이 온난합니다." },
  Cfc: { group: "온대", label: "아한대 해양성", summary: "사계절 습윤하지만 여름이 짧고 서늘합니다." },
  Cwa: { group: "온대", label: "겨울 건기 온대, 더운 여름", summary: "몬순 영향으로 겨울 건기가 뚜렷합니다." },
  Cwb: { group: "온대", label: "겨울 건기 온대, 온난한 여름", summary: "겨울 건기와 고지/내륙성의 온화한 여름이 결합합니다." },
  Cwc: { group: "온대", label: "겨울 건기 온대, 서늘한 여름", summary: "겨울 건기가 있지만 여름은 짧고 서늘합니다." },
  Dsa: { group: "냉대", label: "여름 건기 냉대, 더운 여름", summary: "냉대 기후이면서 여름 건기가 나타나고 여름은 덥습니다." },
  Dsb: { group: "냉대", label: "여름 건기 냉대, 온난한 여름", summary: "냉대 기후이면서 여름 건기가 나타나고 여름은 온난합니다." },
  Dsc: { group: "냉대", label: "여름 건기 냉대, 짧은 여름", summary: "냉대 기후이면서 여름 건기와 짧은 여름이 결합합니다." },
  Dsd: { group: "냉대", label: "여름 건기 냉대, 혹한 겨울", summary: "냉대 기후이면서 여름 건기와 매우 추운 겨울이 함께 나타납니다." },
  Dfa: { group: "냉대", label: "습윤 냉대, 더운 여름", summary: "겨울이 춥고 여름은 덥습니다." },
  Dfb: { group: "냉대", label: "습윤 냉대, 온난한 여름", summary: "겨울이 춥고 여름은 비교적 온난합니다." },
  Dfc: { group: "냉대", label: "아한대, 짧은 여름", summary: "긴 겨울과 짧은 여름이 특징입니다." },
  Dfd: { group: "냉대", label: "극한 한대성", summary: "매우 추운 겨울과 극단적 대륙성이 나타납니다." },
  Dwa: { group: "냉대", label: "겨울 건기 냉대, 더운 여름", summary: "겨울이 매우 건조하고 여름은 덥습니다." },
  Dwb: { group: "냉대", label: "겨울 건기 냉대, 온난한 여름", summary: "겨울 건기와 온난한 여름이 결합합니다." },
  Dwc: { group: "냉대", label: "겨울 건기 아한대", summary: "겨울 건기와 짧은 여름이 나타납니다." },
  Dwd: { group: "냉대", label: "겨울 건기 극한 한대성", summary: "겨울 건기와 매우 혹독한 겨울이 함께 나타납니다." },
  ET: { group: "한대", label: "툰드라", summary: "가장 따뜻한 달도 10°C를 넘지 못합니다." },
  EF: { group: "한대", label: "빙설", summary: "가장 따뜻한 달도 0°C 미만입니다." },
};

const PRESET_DEFS = {
  earthLite: {
    id: "earthLite",
    name: "지구 기본형",
    description: "지구와 비슷한 육해 분포 위에서 대기대순환과 계절 이동을 읽는 기본 프리셋입니다.",
    tilt: 23.4,
    landScale: 1.0,
    mountainHeight: 3400,
    mountainLon: 92,
    mountainLat: 30,
    mountainBand: 13,
    mountainWidth: 7,
    currentBias: 0.1,
    monsoonStrength: 0.58,
    probeLat: 37.5,
    probeLon: 127.5,
    continents: [
      { centerLat: 47, centerLon: -105, halfLat: 28, halfLon: 32, weight: 1.0 },
      { centerLat: 18, centerLon: -92, halfLat: 16, halfLon: 18, weight: 0.55 },
      { centerLat: -17, centerLon: -60, halfLat: 33, halfLon: 21, weight: 0.95 },
      { centerLat: 6, centerLon: 20, halfLat: 35, halfLon: 24, weight: 1.0 },
      { centerLat: 50, centerLon: 10, halfLat: 18, halfLon: 24, weight: 0.95 },
      { centerLat: 28, centerLon: 46, halfLat: 16, halfLon: 18, weight: 0.82 },
      { centerLat: 49, centerLon: 92, halfLat: 24, halfLon: 48, weight: 0.92 },
      { centerLat: 27, centerLon: 104, halfLat: 20, halfLon: 28, weight: 0.96 },
      { centerLat: 36, centerLon: 130, halfLat: 12, halfLon: 14, weight: 0.92 },
      { centerLat: 2, centerLon: 105, halfLat: 12, halfLon: 18, weight: 0.85 },
      { centerLat: 76, centerLon: 20, halfLat: 8, halfLon: 18, weight: 0.72 },
      { centerLat: -24, centerLon: 134, halfLat: 16, halfLon: 18, weight: 0.82 },
      { centerLat: -76, centerLon: 0, halfLat: 12, halfLon: 180, weight: 0.9 },
    ],
  },
  monsoonLab: {
    id: "monsoonLab",
    name: "몬순 실험",
    description: "대륙이 넓고 남쪽 바다에서 습한 공기가 밀려오며, 산맥이 바람을 들어 올려 강수를 집중시키는 프리셋입니다.",
    tilt: 24,
    landScale: 1.15,
    mountainHeight: 4600,
    mountainLon: 96,
    mountainLat: 27,
    mountainBand: 12,
    mountainWidth: 8,
    currentBias: 0.45,
    monsoonStrength: 0.95,
    probeLat: 22.5,
    probeLon: 82.5,
    continents: [
      { centerLat: 24, centerLon: 88, halfLat: 32, halfLon: 65, weight: 1.0 },
      { centerLat: 54, centerLon: 92, halfLat: 16, halfLon: 34, weight: 0.75 },
      { centerLat: -12, centerLon: 124, halfLat: 12, halfLon: 18, weight: 0.45 },
    ],
  },
  rainShadowLab: {
    id: "rainShadowLab",
    name: "푄과 비그늘",
    description: "편서풍이 산맥을 넘으면서 바람받이 사면에 비가 집중되고, 반대편은 건조하고 따뜻해지는 프리셋입니다.",
    tilt: 22,
    landScale: 1.0,
    mountainHeight: 4200,
    mountainLon: -108,
    mountainLat: 41,
    mountainBand: 11,
    mountainWidth: 7,
    currentBias: -0.2,
    monsoonStrength: 0.28,
    probeLat: 41,
    probeLon: -93,
    continents: [
      { centerLat: 39, centerLon: -72, halfLat: 24, halfLon: 62, weight: 1.0 },
      { centerLat: 14, centerLon: -82, halfLat: 18, halfLon: 26, weight: 0.4 },
    ],
  },
  oceanWorld: {
    id: "oceanWorld",
    name: "대양 행성",
    description: "대륙이 거의 없어 육지-바다 대비보다 위도와 대기대순환이 지배적인 경우를 보여 줍니다.",
    tilt: 23.4,
    landScale: 0.45,
    mountainHeight: 0,
    mountainLon: 40,
    mountainLat: 15,
    mountainBand: 10,
    mountainWidth: 6,
    currentBias: 0.18,
    monsoonStrength: 0.05,
    probeLat: 0,
    probeLon: 0,
    continents: [],
  },
};

export const PRESETS = Object.freeze(
  Object.fromEntries(
    Object.entries(PRESET_DEFS).map(([key, value]) => [key, Object.freeze({ ...value, continents: Object.freeze(value.continents.map((shape) => Object.freeze({ ...shape }))) })]),
  ),
);

const OBSERVED_BASE_SCENARIO = Object.freeze({
  presetId: PRESETS.earthLite.id,
  tilt: PRESETS.earthLite.tilt,
  landScale: PRESETS.earthLite.landScale,
  mountainHeight: 0,
  currentBias: 0,
  monsoonStrength: PRESETS.earthLite.monsoonStrength,
});

let observedWorldCache = null;

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function sum(values) {
  return values.reduce((total, value) => total + value, 0);
}

function average(values) {
  return values.length ? sum(values) / values.length : 0;
}

function degToRad(value) {
  return (value * Math.PI) / 180;
}

function wrappedLongitude(value) {
  let lon = ((value + 180) % 360 + 360) % 360 - 180;
  if (lon === -180) {
    lon = 180;
  }
  return lon;
}

function wrappedDistance(a, b) {
  const delta = Math.abs(wrappedLongitude(a) - wrappedLongitude(b));
  return delta > 180 ? 360 - delta : delta;
}

function signedWrappedDistance(a, b) {
  let delta = wrappedLongitude(a) - wrappedLongitude(b);
  if (delta > 180) {
    delta -= 360;
  }
  if (delta < -180) {
    delta += 360;
  }
  return delta;
}

function gaussian(distance, spread) {
  if (spread <= 0) {
    return 0;
  }
  return Math.exp(-((distance * distance) / (2 * spread * spread)));
}

function smoothstep(value) {
  const t = clamp(value, 0, 1);
  return t * t * (3 - 2 * t);
}

function scaleContinents(continents, landScale) {
  return continents.map((shape) => ({
    ...shape,
    halfLat: shape.halfLat * Math.sqrt(landScale),
    halfLon: shape.halfLon * landScale,
  }));
}

function solarDeclination(month, tilt) {
  const safeMonth = clamp(Math.round(month), 1, 12);
  const dayOfYear = MONTH_MID_DAYS[safeMonth - 1];
  return tilt * Math.sin(TWO_PI * (dayOfYear - 81) / 365);
}

function itczLatitude(month, tilt) {
  return solarDeclination(month, tilt) * 0.72 + 2;
}

export function describeWindBand(latitude) {
  const absLat = Math.abs(latitude);
  if (absLat < 25) {
    return {
      label: "무역풍대",
      flow: -1,
      shortArrow: "동 → 서",
      explanation: "아열대 고압대에서 적도 저압대로 향하는 표층 바람입니다.",
    };
  }
  if (absLat < 60) {
    return {
      label: "편서풍대",
      flow: 1,
      shortArrow: "서 → 동",
      explanation: "중위도에서 서쪽에서 동쪽으로 이동하는 표층 바람입니다.",
    };
  }
  return {
    label: "극동풍대",
    flow: -1,
    shortArrow: "동 → 서",
    explanation: "극고압대에서 아극 저압대로 퍼지는 차갑고 건조한 바람입니다.",
  };
}

function describePressureBand(latitude, itczLat) {
  const distance = latitude - itczLat;
  const absDistance = Math.abs(distance);
  if (absDistance < 10) {
    return "적도 저압대";
  }
  if (absDistance < 30) {
    return "아열대 고압대";
  }
  if (absDistance < 60) {
    return "아극 저압대";
  }
  return "극고압대";
}

function shapeStrength(latitude, longitude, shape) {
  const dx = wrappedDistance(longitude, shape.centerLon) / Math.max(shape.halfLon, 1);
  const dy = Math.abs(latitude - shape.centerLat) / Math.max(shape.halfLat, 1);
  const edge = Math.max(dx, dy);
  if (edge <= 1) {
    return (1 - smoothstep(edge)) * shape.weight;
  }
  if (edge <= 1.35) {
    return (1 - (edge - 1) / 0.35) * 0.16 * shape.weight;
  }
  return 0;
}

function getLandness(latitude, longitude, scenario) {
  const total = scenario.continents.reduce((accumulator, shape) => accumulator + shapeStrength(latitude, longitude, shape), 0);
  return clamp(total, 0, 1);
}

function getLandDensity(latitude, longitude, scenario) {
  const latOffsets = [-10, 0, 10];
  const lonOffsets = [-30, -15, 0, 15, 30];
  let total = 0;
  let samples = 0;

  for (const latOffset of latOffsets) {
    for (const lonOffset of lonOffsets) {
      total += getLandness(clamp(latitude + latOffset, -90, 90), wrappedLongitude(longitude + lonOffset), scenario);
      samples += 1;
    }
  }

  return total / Math.max(samples, 1);
}

function getOceanFetch(latitude, longitude, flow, scenario) {
  let oceanFraction = 0;
  let samples = 0;

  for (let step = 1; step <= 6; step += 1) {
    const sourceLon = wrappedLongitude(longitude - flow * step * 10);
    oceanFraction += 1 - getLandness(latitude, sourceLon, scenario);
    samples += 1;
  }

  return oceanFraction / Math.max(samples, 1);
}

function getMountainProfile(latitude, longitude, flow, scenario) {
  if (scenario.mountainHeight <= 0) {
    return {
      elevation: 0,
      mountainSignal: 0,
      windwardLift: 0,
      leewardShadow: 0,
      foehnPotential: 0,
    };
  }

  const latWeight = gaussian(latitude - scenario.mountainLat, scenario.mountainBand);
  const lonDelta = signedWrappedDistance(longitude, scenario.mountainLon);
  const mountainSignal = latWeight * gaussian(lonDelta, scenario.mountainWidth);
  const windwardCenter = flow > 0 ? -scenario.mountainWidth * 1.2 : scenario.mountainWidth * 1.2;
  const leewardCenter = flow > 0 ? scenario.mountainWidth * 1.8 : -scenario.mountainWidth * 1.8;
  const heightKm = scenario.mountainHeight / 1000;

  return {
    elevation: mountainSignal * scenario.mountainHeight,
    mountainSignal,
    windwardLift: latWeight * gaussian(lonDelta - windwardCenter, scenario.mountainWidth * 1.5) * heightKm,
    leewardShadow: latWeight * gaussian(lonDelta - leewardCenter, scenario.mountainWidth * 2.2) * heightKm,
    foehnPotential: latWeight * gaussian(lonDelta - leewardCenter, scenario.mountainWidth * 1.7) * heightKm,
  };
}

function buildSiteProfile(latitude, longitude, scenario) {
  const landness = getLandness(latitude, longitude, scenario);
  const wind = describeWindBand(latitude);
  const landDensity = getLandDensity(latitude, longitude, scenario);
  const oceanFetch = getOceanFetch(latitude, longitude, wind.flow, scenario);
  const coastalness = clamp(landness * (oceanFetch * 0.9 + (1 - landDensity) * 0.35), 0, 1);
  const interiorness = clamp(landness * (landDensity * 1.12 - coastalness * 0.58), 0, 1);
  const mountain = getMountainProfile(latitude, longitude, wind.flow, scenario);
  const currentZone = gaussian(Math.abs(latitude) - 30, 16);

  return {
    latitude,
    longitude,
    landness,
    landDensity,
    oceanFetch,
    coastalness,
    interiorness,
    wind,
    currentZone,
    mountain,
    elevation: mountain.elevation,
  };
}

function getSeasonWave(month) {
  return Math.sin((month - 4) / 12 * TWO_PI);
}

function analyzeMonthFromProfile(profile, month, scenario) {
  const absLat = Math.abs(profile.latitude);
  const hemisphere = profile.latitude === 0 ? 0 : Math.sign(profile.latitude);
  const seasonWave = getSeasonWave(month);
  const declination = solarDeclination(month, scenario.tilt);
  const itczLat = itczLatitude(month, scenario.tilt);
  const heatingSign = hemisphere === 0 ? 1 : hemisphere;
  const summerHeating = Math.max(0, seasonWave * heatingSign);
  const winterCooling = Math.max(0, -seasonWave * heatingSign);
  const solarPulse = (Math.cos(degToRad(profile.latitude - declination)) - Math.cos(degToRad(profile.latitude))) * 9;
  const currentTemp = scenario.currentBias * profile.coastalness * profile.currentZone * 3.4;
  const seasonAmplitude = clamp(
    (1.8 + absLat * 0.18) * (scenario.tilt / 23.4) + profile.interiorness * 9 - profile.coastalness * 4.5,
    0.8,
    26,
  );
  const baseTemp =
    29
    - 0.39 * absLat
    - 0.0014 * absLat * absLat
    - 0.0057 * profile.elevation
    + profile.landness * 0.9
    - profile.interiorness * 1.8
    + currentTemp * 0.6;
  const foehnWarm = profile.mountain.foehnPotential * (0.5 + winterCooling * 0.45);
  const seasonalOffset = seasonAmplitude * seasonWave * heatingSign * (hemisphere === 0 ? 0.2 : 1);
  const temperature = baseTemp + solarPulse + seasonalOffset + foehnWarm;

  const baselineMoisture = 18 + 32 * (1 - profile.landness) + 24 * profile.coastalness;
  const itczRain = 145 * gaussian(profile.latitude - itczLat, 11) * (0.75 + profile.oceanFetch * 0.35);
  const stormTrack = 62 * gaussian(absLat - 50, 10) * (0.5 + profile.oceanFetch * 0.5);
  const subtropicalDry = 78 * gaussian(absLat - 28, 8) * (0.65 + profile.interiorness);
  const interiorDry = 50 * profile.interiorness;
  const polarDry = absLat > 65 ? (absLat - 65) * 1.4 : 0;
  const monsoonBand = clamp((absLat - 8) / 12, 0, 1) * clamp((38 - absLat) / 12, 0, 1);
  const monsoonWet = scenario.monsoonStrength * profile.landness * profile.oceanFetch * monsoonBand * summerHeating * 150;
  const monsoonDry = scenario.monsoonStrength * profile.landness * monsoonBand * winterCooling * 34;
  const currentWet = scenario.currentBias * profile.coastalness * profile.currentZone * 24;
  const orographicWet = profile.mountain.windwardLift * (13 + profile.oceanFetch * 20);
  const shadowDry = profile.mountain.leewardShadow * (18 + profile.interiorness * 20);
  const precipitation = clamp(
    baselineMoisture + itczRain + stormTrack + monsoonWet + currentWet + orographicWet - subtropicalDry - interiorDry - monsoonDry - shadowDry - polarDry,
    0,
    420,
  );

  return {
    month,
    declination,
    itczLat,
    pressureBand: describePressureBand(profile.latitude, itczLat),
    temperature,
    precipitation,
    monsoonWet,
    orographicWet,
    shadowDry,
    foehnWarm,
  };
}

function getSummerHalfIndices(latitude) {
  return latitude >= 0 ? [3, 4, 5, 6, 7, 8] : [9, 10, 11, 0, 1, 2];
}

function getKoppenMeta(code) {
  return KOPPEN_META[code] ?? { group: "기타", label: code, summary: "간이 모형에서 계산한 기후 코드입니다." };
}

export function classifyKoppen(temperatures, precipitations, latitude, landness = 1) {
  if (landness < 0.42) {
    return {
      code: "Ocean",
      ...getKoppenMeta("Ocean"),
      reasons: ["육지 비율이 낮아 쾨펜 분류 대신 해양 셀로 처리했습니다."],
    };
  }

  const annualTemp = average(temperatures);
  const annualPrecip = sum(precipitations);
  const warmest = Math.max(...temperatures);
  const coldest = Math.min(...temperatures);
  const driest = Math.min(...precipitations);
  const warmMonths = temperatures.filter((value) => value >= 10).length;
  const summerIndices = getSummerHalfIndices(latitude);
  const winterIndices = Array.from({ length: 12 }, (_, index) => index).filter((index) => !summerIndices.includes(index));
  const summerPrecip = sum(summerIndices.map((index) => precipitations[index]));
  const winterPrecip = sum(winterIndices.map((index) => precipitations[index]));
  const driestSummer = Math.min(...summerIndices.map((index) => precipitations[index]));
  const wettestSummer = Math.max(...summerIndices.map((index) => precipitations[index]));
  const driestWinter = Math.min(...winterIndices.map((index) => precipitations[index]));
  const wettestWinter = Math.max(...winterIndices.map((index) => precipitations[index]));
  const summerRatio = annualPrecip > 0 ? summerPrecip / annualPrecip : 0;

  if (warmest < 10) {
    const code = warmest < 0 ? "EF" : "ET";
    return {
      code,
      ...getKoppenMeta(code),
      reasons: [
        `가장 더운 달이 ${warmest.toFixed(1)}°C로 10°C를 넘지 못했습니다.`,
        `연강수량은 ${annualPrecip.toFixed(0)} mm입니다.`,
      ],
    };
  }

  const drynessOffset = summerRatio >= 0.7 ? 280 : summerRatio >= 0.3 ? 140 : 0;
  const drynessThreshold = Math.max(0, 20 * annualTemp + drynessOffset);
  if (annualPrecip < drynessThreshold) {
    const moistureCode = annualPrecip < drynessThreshold / 2 ? "BW" : "BS";
    const thermalCode = annualTemp >= 18 ? "h" : "k";
    const code = `${moistureCode}${thermalCode}`;
    return {
      code,
      ...getKoppenMeta(code),
      reasons: [
        `연강수량 ${annualPrecip.toFixed(0)} mm가 건조 한계 ${drynessThreshold.toFixed(0)} mm보다 적습니다.`,
        `연평균 기온은 ${annualTemp.toFixed(1)}°C입니다.`,
      ],
    };
  }

  if (coldest >= 18) {
    let code = "Aw";
    if (driest >= 60) {
      code = "Af";
    } else if (driest >= 100 - annualPrecip / 25) {
      code = "Am";
    } else {
      code = summerPrecip < winterPrecip ? "As" : "Aw";
    }

    return {
      code,
      ...getKoppenMeta(code),
      reasons: [
        `가장 추운 달도 ${coldest.toFixed(1)}°C로 18°C 이상입니다.`,
        `가장 건조한 달 강수량은 ${driest.toFixed(0)} mm입니다.`,
      ],
    };
  }

  const mainCode = coldest >= 0 ? "C" : "D";
  let seasonalCode = "f";
  if (driestSummer < 40 && driestSummer < wettestWinter / 3) {
    seasonalCode = "s";
  } else if (driestWinter < wettestSummer / 10) {
    seasonalCode = "w";
  }

  let thermalCode = "c";
  if (mainCode === "D" && coldest < -38) {
    thermalCode = "d";
  } else if (warmest >= 22 && warmMonths >= 4) {
    thermalCode = "a";
  } else if (warmMonths >= 4) {
    thermalCode = "b";
  }

  const code = `${mainCode}${seasonalCode}${thermalCode}`;
  return {
    code,
    ...getKoppenMeta(code),
    reasons: [
      `가장 더운 달 ${warmest.toFixed(1)}°C, 가장 추운 달 ${coldest.toFixed(1)}°C입니다.`,
      seasonalCode === "f"
        ? "뚜렷한 건기가 없습니다."
        : seasonalCode === "s"
          ? `여름 최건월 ${driestSummer.toFixed(0)} mm가 겨울 최다우월의 1/3보다 작아 여름 건기입니다.`
          : `겨울 최건월 ${driestWinter.toFixed(0)} mm가 여름 최다우월의 1/10보다 작아 겨울 건기입니다.`,
    ],
  };
}

function buildReasonList(profile, months, classification, scenario) {
  const selected = months[scenario.month - 1];
  const reasons = [...classification.reasons];
  if (Math.abs(profile.latitude - selected.itczLat) < 10) {
    reasons.push("선택한 달에는 ITCZ가 가까워 상승기류와 대류성 비가 강화됩니다.");
  }
  if (profile.wind.label === "편서풍대") {
    reasons.push("이 위도대는 편서풍 지배를 받아 서쪽 공기가 동쪽으로 이동합니다.");
  } else if (profile.wind.label === "무역풍대") {
    reasons.push("이 위도대는 무역풍 지배를 받아 동쪽 공기가 서쪽으로 이동합니다.");
  }
  if (profile.interiorness > 0.45) {
    reasons.push("대륙 내부 효과가 커서 연교차가 커지고 수분 공급이 줄어듭니다.");
  } else if (profile.coastalness > 0.35) {
    reasons.push("해양과 가까워 연교차가 줄고 수분 공급이 쉬워집니다.");
  }
  if (selected.orographicWet > 22) {
    reasons.push("산맥 바람받이 사면이라 상승 냉각으로 강수가 크게 늘어납니다.");
  }
  if (selected.shadowDry > 18) {
    reasons.push("산맥 뒤쪽 비그늘이라 공기가 내려오며 건조해집니다.");
  }
  if (selected.foehnWarm > 1.2) {
    reasons.push("내려오는 공기가 단열 가열되어 푄 성격의 온난화가 추가됩니다.");
  }
  return reasons.slice(0, 6);
}

function getObservedScenario(rawScenario = {}) {
  return createScenario({
    presetId: OBSERVED_BASE_SCENARIO.presetId,
    month: rawScenario.month ?? 7,
    tilt: OBSERVED_BASE_SCENARIO.tilt,
    landScale: OBSERVED_BASE_SCENARIO.landScale,
    mountainHeight: OBSERVED_BASE_SCENARIO.mountainHeight,
    currentBias: OBSERVED_BASE_SCENARIO.currentBias,
    monsoonStrength: OBSERVED_BASE_SCENARIO.monsoonStrength,
  });
}

function normalizeObservedLongitude(value) {
  let longitude = Number.isFinite(Number(value)) ? Number(value) : 0;
  while (longitude < -180) {
    longitude += 360;
  }
  while (longitude > 180) {
    longitude -= 360;
  }
  return longitude === 180 ? -180 : longitude;
}

function getObservedLatitudeIndex(latitude) {
  const safeLat = clamp(Number(latitude), -90, 90);
  return clamp(Math.round((safeLat + 90) / 5), 0, LATITUDES.length - 1);
}

function getObservedLongitudeIndex(longitude) {
  const safeLon = normalizeObservedLongitude(longitude);
  return clamp(Math.round((safeLon + 180) / 5), 0, LONGITUDES.length - 1);
}

function getObservedCellIndex(latitude, longitude) {
  return getObservedLatitudeIndex(latitude) * LONGITUDES.length + getObservedLongitudeIndex(longitude);
}

function getObservedLandness(latitude, longitude) {
  return REAL_CLIMATE_GRID.landMask[getObservedCellIndex(latitude, longitude)] ?? 0;
}

function getObservedLandDensity(latitude, longitude) {
  const latOffsets = [-10, 0, 10];
  const lonOffsets = [-30, -15, 0, 15, 30];
  let total = 0;
  let samples = 0;

  for (const latOffset of latOffsets) {
    for (const lonOffset of lonOffsets) {
      total += getObservedLandness(clamp(latitude + latOffset, -90, 90), normalizeObservedLongitude(longitude + lonOffset));
      samples += 1;
    }
  }

  return total / Math.max(samples, 1);
}

function getObservedOceanFetch(latitude, longitude, flow) {
  let oceanFraction = 0;
  let samples = 0;

  for (let step = 1; step <= 6; step += 1) {
    const sourceLon = normalizeObservedLongitude(longitude - flow * step * 10);
    oceanFraction += 1 - getObservedLandness(latitude, sourceLon);
    samples += 1;
  }

  return oceanFraction / Math.max(samples, 1);
}

function buildObservedSiteProfile(latitude, longitude) {
  const landness = getObservedLandness(latitude, longitude);
  const wind = describeWindBand(latitude);
  const landDensity = getObservedLandDensity(latitude, longitude);
  const oceanFetch = getObservedOceanFetch(latitude, longitude, wind.flow);
  const coastalness = clamp(landness * (oceanFetch * 0.9 + (1 - landDensity) * 0.35), 0, 1);
  const interiorness = clamp(landness * (landDensity * 1.12 - coastalness * 0.58), 0, 1);
  const mountain = {
    elevation: 0,
    mountainSignal: 0,
    windwardLift: 0,
    leewardShadow: 0,
    foehnPotential: 0,
  };

  return {
    latitude,
    longitude,
    landness,
    landDensity,
    oceanFetch,
    coastalness,
    interiorness,
    wind,
    currentZone: gaussian(Math.abs(latitude) - 30, 16),
    mountain,
    elevation: 0,
  };
}

function getObservedMonthlySeries(cellIndex) {
  return {
    temperatures: REAL_CLIMATE_GRID.monthlyTemperature.map((values) => values[cellIndex]),
    precipitations: REAL_CLIMATE_GRID.monthlyPrecipitation.map((values) => values[cellIndex]),
  };
}

function buildObservedMonths(profile, scenario, temperatures, precipitations) {
  return Array.from({ length: 12 }, (_, index) => {
    const explanation = analyzeMonthFromProfile(profile, index + 1, scenario);
    return {
      ...explanation,
      temperature: temperatures[index],
      precipitation: precipitations[index],
    };
  });
}

function computeObservedLocationSeries(latitude, longitude, rawScenario) {
  const scenario = getObservedScenario(rawScenario);
  const cellIndex = getObservedCellIndex(latitude, longitude);
  const profile = buildObservedSiteProfile(latitude, longitude);
  const { temperatures, precipitations } = getObservedMonthlySeries(cellIndex);
  const months = buildObservedMonths(profile, scenario, temperatures, precipitations);
  const classification = classifyKoppen(temperatures, precipitations, latitude, profile.landness);
  const annual = {
    meanTemp: REAL_CLIMATE_GRID.annualTemperature[cellIndex],
    annualPrecip: REAL_CLIMATE_GRID.annualPrecipitation[cellIndex],
    warmestTemp: Math.max(...temperatures),
    coldestTemp: Math.min(...temperatures),
    driestMonth: Math.min(...precipitations),
    wettestMonth: Math.max(...precipitations),
  };

  return {
    cellIndex,
    profile,
    months,
    temperatures,
    precipitations,
    classification,
    annual,
    selectedMonth: months[scenario.month - 1],
    reasons: classification.code === "Ocean"
      ? [
          "선택 위치는 해양 셀이라 육상 쾨펜 기후구분 대신 해양 셀로 처리했습니다.",
          `${ACTIVE_CLIMATE_DATASET.dataset} ${ACTIVE_CLIMATE_DATASET.period} 자료는 육상 월평균 기후 정상값입니다.`,
        ]
      : buildReasonList(profile, months, classification, scenario),
    observed: true,
    dataSource: ACTIVE_CLIMATE_DATASET,
  };
}

function getObservedWorldCache() {
  if (observedWorldCache) {
    return observedWorldCache;
  }

  const cellCount = REAL_CLIMATE_GRID.landMask.length;
  const landness = Float32Array.from(REAL_CLIMATE_GRID.landMask, (value) => value);
  const elevation = new Float32Array(cellCount);
  const koppenCodes = new Array(cellCount);

  for (let cellIndex = 0; cellIndex < cellCount; cellIndex += 1) {
    const latitude = LATITUDES[Math.floor(cellIndex / LONGITUDES.length)];
    const landValue = landness[cellIndex];

    if (landValue < 0.42) {
      koppenCodes[cellIndex] = "Ocean";
      continue;
    }

    const { temperatures, precipitations } = getObservedMonthlySeries(cellIndex);
    koppenCodes[cellIndex] = classifyKoppen(temperatures, precipitations, latitude, landValue).code;
  }

  observedWorldCache = {
    cellCount,
    monthlyTemperature: REAL_CLIMATE_GRID.monthlyTemperature,
    monthlyPrecipitation: REAL_CLIMATE_GRID.monthlyPrecipitation,
    annualTemperature: REAL_CLIMATE_GRID.annualTemperature,
    annualPrecipitation: REAL_CLIMATE_GRID.annualPrecipitation,
    landness,
    elevation,
    koppenCodes,
  };

  return observedWorldCache;
}

function computeLocationSeries(latitude, longitude, rawScenario) {
  const scenario = createScenario(rawScenario);
  const profile = buildSiteProfile(latitude, longitude, scenario);
  const months = Array.from({ length: 12 }, (_, index) => analyzeMonthFromProfile(profile, index + 1, scenario));
  const temperatures = months.map((month) => month.temperature);
  const precipitations = months.map((month) => month.precipitation);
  const classification = classifyKoppen(temperatures, precipitations, latitude, profile.landness);
  const annual = {
    meanTemp: average(temperatures),
    annualPrecip: sum(precipitations),
    warmestTemp: Math.max(...temperatures),
    coldestTemp: Math.min(...temperatures),
    driestMonth: Math.min(...precipitations),
    wettestMonth: Math.max(...precipitations),
  };

  return {
    profile,
    months,
    temperatures,
    precipitations,
    classification,
    annual,
    selectedMonth: months[scenario.month - 1],
    reasons: buildReasonList(profile, months, classification, scenario),
  };
}

export function createScenario(options = {}) {
  const preset = PRESETS[options.presetId] ?? PRESETS.earthLite;
  const landScale = clamp(Number(options.landScale ?? preset.landScale), 0.45, 1.6);

  return {
    presetId: preset.id,
    presetName: preset.name,
    description: preset.description,
    month: clamp(Math.round(Number(options.month ?? 7)), 1, 12),
    tilt: clamp(Number(options.tilt ?? preset.tilt), 10, 35),
    landScale,
    mountainHeight: clamp(Number(options.mountainHeight ?? preset.mountainHeight), 0, 5500),
    mountainLon: wrappedLongitude(Number(options.mountainLon ?? preset.mountainLon)),
    mountainLat: clamp(Number(options.mountainLat ?? preset.mountainLat), -60, 60),
    mountainBand: Number(options.mountainBand ?? preset.mountainBand),
    mountainWidth: Number(options.mountainWidth ?? preset.mountainWidth),
    currentBias: clamp(Number(options.currentBias ?? preset.currentBias), -1, 1),
    monsoonStrength: clamp(Number(options.monsoonStrength ?? preset.monsoonStrength), 0, 1),
    continents: scaleContinents(preset.continents, landScale),
    defaultProbe: {
      latitude: preset.probeLat,
      longitude: preset.probeLon,
    },
  };
}

export function analyzeLocation(latitude, longitude, scenario) {
  const safeLat = clamp(Number(latitude), -90, 90);
  const safeLon = wrappedLongitude(Number(longitude));
  const series = computeObservedLocationSeries(safeLat, safeLon, scenario);

  return {
    latitude: safeLat,
    longitude: safeLon,
    ...series,
  };
}

export function buildWorld(rawScenario) {
  const scenario = getObservedScenario(rawScenario);
  const cached = getObservedWorldCache();

  return {
    scenario,
    latitudes: LATITUDES,
    longitudes: LONGITUDES,
    cellCount: cached.cellCount,
    monthlyTemperature: cached.monthlyTemperature,
    monthlyPrecipitation: cached.monthlyPrecipitation,
    annualTemperature: cached.annualTemperature,
    annualPrecipitation: cached.annualPrecipitation,
    landness: cached.landness,
    elevation: cached.elevation,
    koppenCodes: cached.koppenCodes,
    itczLatitude: itczLatitude(scenario.month, scenario.tilt),
    dataSource: ACTIVE_CLIMATE_DATASET,
  };
}

export function sampleTransect(latitude, month, rawScenario) {
  const scenario = createScenario(rawScenario);
  const safeLat = clamp(Number(latitude), -90, 90);
  return LONGITUDES.map((longitude) => {
    const series = analyzeLocation(safeLat, longitude, { ...scenario, month });
    return {
      longitude,
      elevation: series.profile.elevation,
      landness: series.profile.landness,
      temperature: series.selectedMonth.temperature,
      precipitation: series.selectedMonth.precipitation,
      koppenCode: series.classification.code,
    };
  });
}

export function getCellIndex(latIndex, lonIndex) {
  return latIndex * LONGITUDES.length + lonIndex;
}

export function getKoppenDetails(code) {
  return getKoppenMeta(code);
}

