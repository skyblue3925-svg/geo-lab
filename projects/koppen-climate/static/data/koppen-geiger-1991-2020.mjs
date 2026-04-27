export const OFFICIAL_KOPPEN_META = {
  "dataset": "Beck et al. Koppen-Geiger climate classification",
  "version": 2,
  "period": "1991-2020",
  "resolutionDegrees": 0.1,
  "width": 3600,
  "height": 1800,
  "bbox": [
    -180,
    -90,
    180,
    90
  ],
  "nodata": 0,
  "source": "https://doi.org/10.6084/m9.figshare.21789074.v2",
  "generatedAt": "2026-03-20T06:07:55.103Z"
};

export const OFFICIAL_KOPPEN_BINARY_URL = "./data/koppen-geiger-1991-2020-0p1.bin";

export const OFFICIAL_KOPPEN_CLASSES = Object.freeze([
  {
    "id": 1,
    "code": "Af",
    "label": "Tropical, rainforest",
    "rgb": [
      0,
      0,
      255
    ],
    "color": "#0000ff"
  },
  {
    "id": 2,
    "code": "Am",
    "label": "Tropical, monsoon",
    "rgb": [
      0,
      120,
      255
    ],
    "color": "#0078ff"
  },
  {
    "id": 3,
    "code": "Aw",
    "label": "Tropical, savannah",
    "rgb": [
      70,
      170,
      250
    ],
    "color": "#46aafa"
  },
  {
    "id": 4,
    "code": "BWh",
    "label": "Arid, desert, hot",
    "rgb": [
      255,
      0,
      0
    ],
    "color": "#ff0000"
  },
  {
    "id": 5,
    "code": "BWk",
    "label": "Arid, desert, cold",
    "rgb": [
      255,
      150,
      150
    ],
    "color": "#ff9696"
  },
  {
    "id": 6,
    "code": "BSh",
    "label": "Arid, steppe, hot",
    "rgb": [
      245,
      165,
      0
    ],
    "color": "#f5a500"
  },
  {
    "id": 7,
    "code": "BSk",
    "label": "Arid, steppe, cold",
    "rgb": [
      255,
      220,
      100
    ],
    "color": "#ffdc64"
  },
  {
    "id": 8,
    "code": "Csa",
    "label": "Temperate, dry summer, hot summer",
    "rgb": [
      255,
      255,
      0
    ],
    "color": "#ffff00"
  },
  {
    "id": 9,
    "code": "Csb",
    "label": "Temperate, dry summer, warm summer",
    "rgb": [
      200,
      200,
      0
    ],
    "color": "#c8c800"
  },
  {
    "id": 10,
    "code": "Csc",
    "label": "Temperate, dry summer, cold summer",
    "rgb": [
      150,
      150,
      0
    ],
    "color": "#969600"
  },
  {
    "id": 11,
    "code": "Cwa",
    "label": "Temperate, dry winter, hot summer",
    "rgb": [
      150,
      255,
      150
    ],
    "color": "#96ff96"
  },
  {
    "id": 12,
    "code": "Cwb",
    "label": "Temperate, dry winter, warm summer",
    "rgb": [
      100,
      200,
      100
    ],
    "color": "#64c864"
  },
  {
    "id": 13,
    "code": "Cwc",
    "label": "Temperate, dry winter, cold summer",
    "rgb": [
      50,
      150,
      50
    ],
    "color": "#329632"
  },
  {
    "id": 14,
    "code": "Cfa",
    "label": "Temperate, no dry season, hot summer",
    "rgb": [
      200,
      255,
      80
    ],
    "color": "#c8ff50"
  },
  {
    "id": 15,
    "code": "Cfb",
    "label": "Temperate, no dry season, warm summer",
    "rgb": [
      100,
      255,
      80
    ],
    "color": "#64ff50"
  },
  {
    "id": 16,
    "code": "Cfc",
    "label": "Temperate, no dry season, cold summer",
    "rgb": [
      50,
      200,
      0
    ],
    "color": "#32c800"
  },
  {
    "id": 17,
    "code": "Dsa",
    "label": "Cold, dry summer, hot summer",
    "rgb": [
      255,
      0,
      255
    ],
    "color": "#ff00ff"
  },
  {
    "id": 18,
    "code": "Dsb",
    "label": "Cold, dry summer, warm summer",
    "rgb": [
      200,
      0,
      200
    ],
    "color": "#c800c8"
  },
  {
    "id": 19,
    "code": "Dsc",
    "label": "Cold, dry summer, cold summer",
    "rgb": [
      150,
      50,
      150
    ],
    "color": "#963296"
  },
  {
    "id": 20,
    "code": "Dsd",
    "label": "Cold, dry summer, very cold winter",
    "rgb": [
      150,
      100,
      150
    ],
    "color": "#966496"
  },
  {
    "id": 21,
    "code": "Dwa",
    "label": "Cold, dry winter, hot summer",
    "rgb": [
      170,
      175,
      255
    ],
    "color": "#aaafff"
  },
  {
    "id": 22,
    "code": "Dwb",
    "label": "Cold, dry winter, warm summer",
    "rgb": [
      90,
      120,
      220
    ],
    "color": "#5a78dc"
  },
  {
    "id": 23,
    "code": "Dwc",
    "label": "Cold, dry winter, cold summer",
    "rgb": [
      75,
      80,
      180
    ],
    "color": "#4b50b4"
  },
  {
    "id": 24,
    "code": "Dwd",
    "label": "Cold, dry winter, very cold winter",
    "rgb": [
      50,
      0,
      135
    ],
    "color": "#320087"
  },
  {
    "id": 25,
    "code": "Dfa",
    "label": "Cold, no dry season, hot summer",
    "rgb": [
      0,
      255,
      255
    ],
    "color": "#00ffff"
  },
  {
    "id": 26,
    "code": "Dfb",
    "label": "Cold, no dry season, warm summer",
    "rgb": [
      55,
      200,
      255
    ],
    "color": "#37c8ff"
  },
  {
    "id": 27,
    "code": "Dfc",
    "label": "Cold, no dry season, cold summer",
    "rgb": [
      0,
      125,
      125
    ],
    "color": "#007d7d"
  },
  {
    "id": 28,
    "code": "Dfd",
    "label": "Cold, no dry season, very cold winter",
    "rgb": [
      0,
      70,
      95
    ],
    "color": "#00465f"
  },
  {
    "id": 29,
    "code": "ET",
    "label": "Polar, tundra",
    "rgb": [
      178,
      178,
      178
    ],
    "color": "#b2b2b2"
  },
  {
    "id": 30,
    "code": "EF",
    "label": "Polar, frost",
    "rgb": [
      102,
      102,
      102
    ],
    "color": "#666666"
  }
]);

export const OFFICIAL_KOPPEN_BY_ID = Object.freeze(
  Object.fromEntries(OFFICIAL_KOPPEN_CLASSES.map((entry) => [entry.id, entry])),
);

export const OFFICIAL_KOPPEN_BY_CODE = Object.freeze(
  Object.fromEntries(OFFICIAL_KOPPEN_CLASSES.map((entry) => [entry.code, entry])),
);
