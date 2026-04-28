function normalizePoint(point) {
  if (!Array.isArray(point) || point.length !== 2) {
    throw new TypeError("Each point must be a [lon, lat] pair.");
  }

  const [lon, lat] = point;
  return [Number(lon), Number(lat)];
}

export function pointsToPath(points) {
  const normalized = points.map(normalizePoint);
  if (normalized.length === 0) {
    return "";
  }

  return `${normalized
    .map(([lon, lat], index) => `${index === 0 ? "M" : "L"} ${lon} ${lat}`)
    .join(" ")} Z`;
}

export function pathToCssPolygonPath(points) {
  return pointsToPath(points);
}

export const WORLD_MAP_REGIONS = Object.freeze([
  Object.freeze({
    id: "north_america",
    name: "North America",
    label: "북아메리카",
    type: "continent",
    fill: "#f0c36a",
    stroke: "#8e6a22",
    points: Object.freeze([
      [-168, 72], [-150, 66], [-138, 58], [-130, 50], [-124, 44], [-118, 38],
      [-112, 32], [-104, 28], [-96, 24], [-88, 22], [-82, 18], [-80, 12],
      [-84, 8], [-92, 10], [-100, 14], [-110, 18], [-118, 24], [-126, 30],
      [-134, 38], [-144, 50], [-156, 60], [-168, 72],
    ]),
  }),
  Object.freeze({
    id: "greenland",
    name: "Greenland",
    label: "그린란드",
    type: "ice",
    fill: "#dfe8ee",
    stroke: "#90a4b2",
    points: Object.freeze([
      [-73, 84], [-58, 83], [-44, 78], [-38, 70], [-42, 60], [-54, 58],
      [-66, 62], [-74, 70], [-78, 78], [-73, 84],
    ]),
  }),
  Object.freeze({
    id: "south_america",
    name: "South America",
    label: "남아메리카",
    type: "continent",
    fill: "#e3b04b",
    stroke: "#8e6a22",
    points: Object.freeze([
      [-81, 12], [-74, 8], [-68, 2], [-64, -6], [-60, -14], [-58, -22],
      [-56, -30], [-54, -38], [-54, -48], [-58, -54], [-64, -52], [-68, -42],
      [-70, -30], [-74, -18], [-78, -6], [-81, 12],
    ]),
  }),
  Object.freeze({
    id: "africa",
    name: "Africa",
    label: "아프리카",
    type: "continent",
    fill: "#d9a441",
    stroke: "#83591f",
    points: Object.freeze([
      [-18, 36], [0, 38], [12, 36], [24, 32], [34, 24], [42, 12], [48, 2],
      [48, -10], [44, -22], [36, -30], [26, -36], [14, -34], [6, -28], [-2, -20],
      [-8, -10], [-14, 2], [-18, 16], [-20, 28], [-18, 36],
    ]),
  }),
  Object.freeze({
    id: "eurasia",
    name: "Eurasia",
    label: "유라시아",
    type: "continent",
    fill: "#efc66f",
    stroke: "#8e6a22",
    points: Object.freeze([
      [-10, 72], [10, 74], [30, 74], [52, 72], [72, 68], [90, 62], [106, 58],
      [124, 56], [140, 50], [150, 42], [160, 34], [168, 28], [166, 18],
      [154, 12], [138, 14], [126, 18], [114, 24], [98, 28], [82, 30], [68, 28],
      [58, 22], [46, 18], [34, 20], [26, 28], [14, 34], [4, 40], [-4, 48],
      [-10, 58], [-14, 66], [-10, 72],
    ]),
  }),
  Object.freeze({
    id: "india_se_asia",
    name: "South and Southeast Asia",
    label: "남아시아/동남아",
    type: "subregion",
    fill: "#f4d77e",
    stroke: "#8e6a22",
    points: Object.freeze([
      [68, 24], [76, 22], [84, 20], [92, 18], [100, 14], [108, 10], [114, 6],
      [118, 0], [116, -8], [110, -10], [102, -4], [94, 0], [86, 6], [78, 14],
      [68, 24],
    ]),
  }),
  Object.freeze({
    id: "australia",
    name: "Australia",
    label: "오스트레일리아",
    type: "continent",
    fill: "#deb35b",
    stroke: "#83591f",
    points: Object.freeze([
      [112, -10], [122, -8], [132, -10], [140, -16], [148, -24], [150, -32],
      [144, -40], [134, -44], [124, -42], [116, -36], [110, -28], [108, -18],
      [112, -10],
    ]),
  }),
  Object.freeze({
    id: "antarctica",
    name: "Antarctica",
    label: "남극",
    type: "ice",
    fill: "#f4f7fb",
    stroke: "#a8b8c8",
    points: Object.freeze([
      [-180, -60], [-150, -64], [-120, -66], [-90, -68], [-60, -69], [-30, -71],
      [0, -72], [30, -71], [60, -69], [90, -68], [120, -66], [150, -64],
      [180, -60], [180, -90], [-180, -90], [-180, -60],
    ]),
  }),
]);

export const WORLD_MAP_LABELS = Object.freeze([
  Object.freeze({ name: "ITCZ", lon: 0, lat: 5, kind: "circulation" }),
  Object.freeze({ name: "Hadley", lon: -25, lat: 20, kind: "circulation" }),
  Object.freeze({ name: "Ferrel", lon: 55, lat: 45, kind: "circulation" }),
  Object.freeze({ name: "Polar", lon: 105, lat: 72, kind: "circulation" }),
  Object.freeze({ name: "Tropics", lon: -155, lat: -23.5, kind: "latitude" }),
  Object.freeze({ name: "Tropics", lon: -155, lat: 23.5, kind: "latitude" }),
]);

export const WORLD_MAP_BORDERS = Object.freeze([
  Object.freeze({ name: "Equator", lat: 0, dash: true }),
  Object.freeze({ name: "Tropic of Cancer", lat: 23.5, dash: true }),
  Object.freeze({ name: "Tropic of Capricorn", lat: -23.5, dash: true }),
  Object.freeze({ name: "Arctic Circle", lat: 66.5, dash: true }),
  Object.freeze({ name: "Antarctic Circle", lat: -66.5, dash: true }),
]);

export function getWorldMapOverlay() {
  return WORLD_MAP_REGIONS.map((region) => ({
    ...region,
    path: pointsToPath(region.points),
  }));
}

export function getRegionById(regionId) {
  return WORLD_MAP_REGIONS.find((region) => region.id === regionId) ?? null;
}

export function getLabelByName(name) {
  return WORLD_MAP_LABELS.find((label) => label.name === name) ?? null;
}
