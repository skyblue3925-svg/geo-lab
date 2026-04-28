# 대표 지형 이미지 기반 애니메이션 필름스트립 프롬프트
목표는 4단계 스토리보드를 흔드는 preview가 아니라, 하나의 지형 형성 과정을 30개의 연속 이미지로 쪼갠 필름스트립을 만드는 것이다. 생성 결과는 `scripts/import_filmstrip_sequence.py`로 분할해 앱 자산으로 넣는다.

## 공통 조건

- 한 장의 이미지 안에 5열 x 6행, 총 30개의 작은 패널.
- 왼쪽 위에서 오른쪽 아래로 시간 순서.
- 패널 사이에는 얇은 여백만 둔다.
- 패널 안에는 글자, 번호, 화살표, UI, 워터마크를 넣지 않는다.
- 카메라 위치, 조명, 지형 블록 크기, 스타일을 전체 패널에서 최대한 유지한다.
- 변화는 카메라 이동이 아니라 지형 자체의 변화여야 한다.

## 석호와 사주

```text
Create one high-resolution 5-column by 6-row filmstrip contact sheet, 30 sequential frames total, showing the continuous formation of a sand spit and lagoon.

Subject: a realistic textbook-style 3D coastal geomorphology diorama viewed from the same high oblique aerial camera throughout.
Animation logic: frame 1 begins with an open bay coast and oblique incoming waves moving sand alongshore. Across the frames, longshore drift gradually extends a narrow sandy spit from one side of the bay mouth. The spit becomes longer and gently hooked, progressively separating calm pale turquoise water behind it from darker open sea outside. By frame 30, a nearly complete sandy barrier leaves a clear shallow lagoon behind it with only a small tidal opening.
Style: realistic educational 3D terrain render, clean classroom geomorphology illustration, not cartoonish, not fantasy.
Color: open sea deep blue, lagoon pale turquoise, sand light tan, land muted green-brown.
Constraints: same camera, same coastline, same lighting, no text, no labels, no numbers, no arrows, no people, no city, no boats, no split-screen labels. The landform itself must change from frame to frame; do not only pan, zoom, or crossfade.
```

## 해안사구

```text
Create one high-resolution 5-column by 6-row filmstrip contact sheet, 30 sequential frames total, showing the continuous formation of coastal dunes behind a beach.

Subject: a realistic textbook-style 3D coastal geomorphology diorama viewed from the same oblique beach-to-inland camera throughout.
Animation logic: frame 1 shows a wide dry sandy beach in front of the sea, with a flat backshore. Across the frames, wind-blown beach sand gradually migrates inland. Small ripples and embryo dunes appear behind the beach, sand accumulates around beach grasses and low obstacles, and the dune ridge grows higher and more continuous parallel to the shoreline. By frame 30, a clear stabilized coastal dune ridge sits behind the beach with grasses on it and the sea still visible in front.
Style: realistic educational 3D terrain render, clean classroom geomorphology illustration, not cartoonish, not fantasy.
Color: beach sand light tan, sea blue, dune sand warm beige, vegetation green.
Constraints: same camera, same shoreline, same lighting, no text, no labels, no numbers, no arrows, no people, no city, no buildings. This is a coastal dune behind a beach, not a desert dune field. The dune ridge must grow frame by frame; do not only pan, zoom, or crossfade.
```

## 삼각주

```text
Create one high-resolution 5-column by 6-row filmstrip contact sheet, 30 sequential frames total, showing the continuous formation of a river delta at a river mouth.

Subject: a realistic textbook-style 3D geomorphology diorama viewed from the same high oblique camera looking from land toward calm standing water.
Animation logic: frame 1 shows a single river entering a calm sea or lake with almost no deposit. Across the frames, the river slows at the mouth and sediment gradually accumulates just offshore. The deposit grows outward, becomes fan-shaped, and forces the channel to split into distributary channels. By frame 30, a broad triangular delta has prograded into the water with several distributary channels and tan sediment lobes.
Style: realistic educational 3D terrain render, clean classroom geomorphology illustration, not cartoonish, not fantasy.
Color: water blue, sediment tan, vegetated land muted green, active deposits slightly lighter tan.
Constraints: same camera, same river mouth, same lighting, no text, no labels, no numbers, no arrows, no people, no city. This is a delta in standing water, not an alluvial fan at a mountain front. The delta body and distributary channels must develop frame by frame; do not only pan, zoom, or crossfade.
```

## 피오르

```text
Create one high-resolution 5-column by 6-row filmstrip contact sheet, 30 sequential frames total, showing the continuous formation of a fjord from a glacial U-shaped valley flooded by seawater.

Subject: a realistic textbook-style 3D geomorphology diorama viewed from the same oblique coastal valley camera throughout.
Animation logic: frame 1 begins with a mountain valley occupied by glacial ice and steep valley walls. Across the frames, the glacier erodes the valley into a deeper U-shaped trough, then retreats toward the mountains. Seawater gradually enters from the coast and floods the deep trough. By frame 30, a long narrow dark-blue fjord fills the U-shaped valley, with steep rock walls and small remnants of ice or snow upstream.
Style: realistic educational 3D terrain render, clean classroom geomorphology illustration, not cartoonish, not fantasy.
Color: glacier pale blue-white, rock gray-brown, vegetation muted green, seawater deep blue.
Constraints: same camera, same valley, same lighting, no text, no labels, no numbers, no arrows, no people, no city, no boats. This is a glacial valley flooded by the sea, not a river valley or ria coast. The glacier retreat and seawater flooding must visibly progress frame by frame; do not only pan, zoom, or crossfade.
```

## 가져오기 명령 예시

```powershell
& 'C:\Users\HANSOL\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' scripts\import_filmstrip_sequence.py --landform spit_lagoon --filmstrip path\to\spit_lagoon_filmstrip.png --cols 5 --rows 6 --fps 12
```
