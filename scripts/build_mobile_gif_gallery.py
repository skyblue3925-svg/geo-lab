from __future__ import annotations

import csv
import html
import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
COLLECTION = ROOT / "output" / "terrain-gif-collection"
THUMBS = COLLECTION / "thumbnails"


GROUPS = {
    "river": ("하천 지형", {"alluvial_fan", "braided_river", "floodplain_natural_levee", "free_meander", "oxbow_lake", "river_terrace", "v_valley", "waterfall"}),
    "delta": ("하구ㆍ삼각주", {"arcuate_delta", "bird_foot_delta", "cuspate_delta", "delta", "estuary"}),
    "glacial": ("빙하 지형", {"arete", "cirque", "drumlin", "esker", "fjord", "horn", "kettle_lake", "moraine", "outwash_plain", "thermokarst", "u_valley"}),
    "volcanic": ("화산 지형", {"caldera", "cinder_cone", "crater_lake", "lava_dome", "lava_plateau", "maar", "shield_volcano", "stratovolcano"}),
    "karst": ("카르스트 지형", {"karren", "karst_doline", "polje", "tower_karst", "uvala"}),
    "arid": ("건조 지형", {"barchan", "mesa_butte", "pedestal_rock", "pediment", "playa", "star_dune", "transverse_dune", "wadi"}),
    "coastal": ("해안 지형", {"barrier_island", "coastal_cliff", "coastal_dune", "marine_terrace", "ria_coast", "sea_arch", "sea_cave_stack", "spit_lagoon", "tidal_flat", "tombolo", "wave_cut_platform"}),
}


KO_TITLES = {
    "alluvial_fan": "선상지",
    "arcuate_delta": "원호상 삼각주",
    "arete": "아레트",
    "barrier_island": "장벽섬",
    "barchan": "바르한",
    "bird_foot_delta": "조족상 삼각주",
    "braided_river": "망상 하천",
    "caldera": "칼데라",
    "cinder_cone": "분석구",
    "cirque": "권곡",
    "coastal_cliff": "해식애",
    "coastal_dune": "해안 사구",
    "crater_lake": "화구호",
    "cuspate_delta": "첨상 삼각주",
    "delta": "삼각주",
    "drumlin": "드럼린",
    "esker": "에스커",
    "estuary": "하구",
    "fjord": "피오르",
    "floodplain_natural_levee": "범람원과 자연제방",
    "free_meander": "자유 곡류천",
    "horn": "호른",
    "karren": "카렌",
    "karst_doline": "돌리네",
    "kettle_lake": "케틀호",
    "lava_dome": "용암돔",
    "lava_plateau": "용암대지",
    "maar": "마르",
    "marine_terrace": "해안단구",
    "mesa_butte": "메사와 뷰트",
    "moraine": "모레인",
    "outwash_plain": "빙수평원",
    "oxbow_lake": "우각호",
    "pedestal_rock": "버섯바위",
    "pediment": "페디먼트",
    "playa": "플라야",
    "polje": "폴리에",
    "ria_coast": "리아스식 해안",
    "river_terrace": "하안단구",
    "sea_arch": "해식 아치",
    "sea_cave_stack": "해식동과 시스택",
    "shield_volcano": "순상화산",
    "spit_lagoon": "사주와 석호",
    "star_dune": "성사구",
    "stratovolcano": "성층화산",
    "thermokarst": "열카르스트",
    "tidal_flat": "갯벌",
    "tombolo": "육계사주",
    "tower_karst": "탑 카르스트",
    "transverse_dune": "횡단사구",
    "u_valley": "U자곡",
    "uvala": "우발라",
    "v_valley": "V자곡",
    "wadi": "와디",
    "waterfall": "폭포",
    "wave_cut_platform": "파식대",
}


def group_for_landform(landform_id: str) -> tuple[str, str]:
    for key, (label, ids) in GROUPS.items():
        if landform_id in ids:
            return key, label
    return "other", "기타"


def build_rows() -> list[dict[str, str]]:
    THUMBS.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, str]] = []
    with (COLLECTION / "index.csv").open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            gif_path = COLLECTION / row["filename"]
            if not gif_path.exists():
                continue

            landform_id = row["landform_id"]
            thumb_name = f"{landform_id}.jpg"
            thumb_path = THUMBS / thumb_name
            if not thumb_path.exists() or thumb_path.stat().st_mtime < gif_path.stat().st_mtime:
                with Image.open(gif_path) as image:
                    image.seek(0)
                    frame = image.convert("RGB")
                    frame.thumbnail((900, 900), Image.Resampling.LANCZOS)
                    frame.save(thumb_path, "JPEG", quality=82, optimize=True)

            group_key, group_label = group_for_landform(landform_id)
            rows.append(
                {
                    "id": landform_id,
                    "title": KO_TITLES.get(landform_id, landform_id),
                    "group": group_key,
                    "groupLabel": group_label,
                    "gif": row["filename"],
                    "thumb": f"thumbnails/{thumb_name}",
                    "size": row["size_mb"],
                }
            )
    return sorted(rows, key=lambda item: (item["groupLabel"], item["title"]))


def render_gallery(rows: list[dict[str, str]]) -> str:
    groups = [("all", "전체")] + [
        (key, label)
        for key, (label, _ids) in GROUPS.items()
        if any(row["group"] == key for row in rows)
    ]
    filter_buttons = "\n".join(
        f'<button class="filter{" active" if key == "all" else ""}" type="button" data-filter="{html.escape(key)}">{html.escape(label)}</button>'
        for key, label in groups
    )
    cards = "\n".join(
        f'''<article class="card playing" data-group="{html.escape(row['group'])}" data-search="{html.escape((row['title'] + ' ' + row['id']).lower())}">
  <button class="media" type="button" data-gif="{html.escape(row['gif'])}" data-thumb="{html.escape(row['thumb'])}" aria-label="{html.escape(row['title'])} GIF 정지 또는 재생">
    <img src="{html.escape(row['gif'])}" alt="{html.escape(row['title'])}" loading="lazy" decoding="async">
    <span class="play">정지</span>
  </button>
  <div class="meta">
    <h2>{html.escape(row['title'])}</h2>
    <p>{html.escape(row['id'])} · {html.escape(row['groupLabel'])} · {html.escape(str(row['size']))} MB</p>
  </div>
</article>'''
        for row in rows
    )
    return f'''<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <title>Geo-Lab 지형 GIF 갤러리</title>
  <style>
    :root {{ color-scheme: light; --ink:#111827; --muted:#6b7280; --line:#e5e7eb; --bg:#ffffff; --chip:#f3f4f6; --accent:#0f766e; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: var(--bg); color: var(--ink); }}
    header {{ position: sticky; top: 0; z-index: 5; background: rgba(255,255,255,.96); backdrop-filter: blur(10px); border-bottom: 1px solid var(--line); padding: max(14px, env(safe-area-inset-top)) 14px 12px; }}
    h1 {{ margin: 0 0 6px; font-size: clamp(1.35rem, 6vw, 2rem); letter-spacing: 0; }}
    .sub {{ margin: 0; color: var(--muted); font-size: .94rem; line-height: 1.45; }}
    .toolbar {{ display: grid; gap: 10px; margin-top: 12px; }}
    .creator {{ margin: 8px 0 0; color: var(--muted); font-size: .9rem; font-weight: 700; }}
    .filters {{ display: flex; gap: 8px; overflow-x: auto; padding-bottom: 2px; scrollbar-width: none; }}
    .filters::-webkit-scrollbar {{ display: none; }}
    .filter, .control {{ flex: 0 0 auto; min-height: 40px; border: 1px solid var(--line); background: var(--chip); border-radius: 999px; padding: 0 13px; font-size: .94rem; color: var(--ink); }}
    .filter.active, .control.primary {{ background: var(--ink); color: white; border-color: var(--ink); }}
    .search-row {{ display: grid; grid-template-columns: 1fr auto auto; gap: 8px; }}
    input {{ width: 100%; min-height: 44px; border: 1px solid var(--line); border-radius: 10px; padding: 0 12px; font-size: 1rem; }}
    main {{ padding: 14px; }}
    .count {{ color: var(--muted); font-size: .92rem; margin: 0 0 12px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 14px; }}
    .card {{ border: 1px solid var(--line); border-radius: 10px; overflow: hidden; background: #fff; }}
    .media {{ display: block; position: relative; width: 100%; padding: 0; border: 0; background: #111827; aspect-ratio: 1 / 1; overflow: hidden; }}
    .media img {{ width: 100%; height: 100%; object-fit: cover; display: block; }}
    .play {{ position: absolute; right: 10px; bottom: 10px; min-width: 56px; min-height: 36px; display: inline-flex; align-items: center; justify-content: center; border-radius: 8px; background: rgba(17,24,39,.86); color: #fff; font-weight: 700; font-size: .92rem; }}
    .card.playing .play {{ background: var(--accent); }}
    .meta {{ padding: 11px 12px 13px; }}
    h2 {{ margin: 0 0 5px; font-size: 1.08rem; letter-spacing: 0; }}
    .meta p {{ margin: 0; color: var(--muted); font-size: .9rem; line-height: 1.35; overflow-wrap: anywhere; }}
    @media (max-width: 640px) {{
      main {{ padding: 10px; }}
      .grid {{ grid-template-columns: 1fr; gap: 12px; }}
      .card {{ border-radius: 8px; }}
      .media {{ aspect-ratio: 4 / 3; }}
      .sub {{ font-size: .9rem; }}
      .search-row {{ grid-template-columns: 1fr; }}
      .control {{ width: 100%; border-radius: 10px; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>지형 GIF 갤러리</h1>
    <p class="sub">고등학생 설명용 지형 형성 GIF입니다. 화면이 무거우면 전체 정지를 누르고 필요한 지형만 다시 재생하세요.</p>
    <p class="creator">제작자: 한백고등학교 김한솔</p>
    <div class="toolbar">
      <div class="filters" aria-label="지형 분류 필터">{filter_buttons}</div>
      <div class="search-row">
        <input id="search" type="search" placeholder="지형 이름 또는 id 검색" autocomplete="off">
        <button id="playAll" class="control primary" type="button">전체 재생</button>
        <button id="pauseAll" class="control" type="button">전체 정지</button>
      </div>
    </div>
  </header>
  <main>
    <p class="count"><span id="count">{len(rows)}</span>개 표시 · 전체 {len(rows)}개</p>
    <section class="grid" id="grid">{cards}</section>
  </main>
  <script>
    const cards = [...document.querySelectorAll('.card')];
    const count = document.querySelector('#count');
    const search = document.querySelector('#search');
    let activeFilter = 'all';

    function setCardPlaying(card, playing) {{
      const button = card.querySelector('.media');
      const img = button.querySelector('img');
      const label = button.querySelector('.play');
      card.classList.toggle('playing', playing);
      img.src = playing ? button.dataset.gif : button.dataset.thumb;
      label.textContent = playing ? '정지' : '재생';
    }}

    function applyFilters() {{
      const q = search.value.trim().toLowerCase();
      let visible = 0;
      cards.forEach(card => {{
        const groupOk = activeFilter === 'all' || card.dataset.group === activeFilter;
        const searchOk = !q || card.dataset.search.includes(q);
        const show = groupOk && searchOk;
        card.hidden = !show;
        if (show) visible += 1;
      }});
      count.textContent = visible;
    }}

    document.querySelectorAll('.filter').forEach(button => {{
      button.addEventListener('click', () => {{
        document.querySelectorAll('.filter').forEach(item => item.classList.remove('active'));
        button.classList.add('active');
        activeFilter = button.dataset.filter;
        applyFilters();
      }});
    }});
    search.addEventListener('input', applyFilters);
    document.querySelector('#playAll').addEventListener('click', () => cards.forEach(card => setCardPlaying(card, true)));
    document.querySelector('#pauseAll').addEventListener('click', () => cards.forEach(card => setCardPlaying(card, false)));
    document.querySelectorAll('.media').forEach(button => {{
      button.addEventListener('click', () => {{
        const card = button.closest('.card');
        setCardPlaying(card, !card.classList.contains('playing'));
      }});
    }});
  </script>
</body>
</html>
'''


def main() -> None:
    rows = build_rows()
    (COLLECTION / "index.html").write_text(render_gallery(rows), encoding="utf-8")
    (COLLECTION / "mobile-gallery-data.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {COLLECTION / 'index.html'}")
    print(f"rows={len(rows)} thumbnails={len(list(THUMBS.glob('*.jpg')))}")


if __name__ == "__main__":
    main()
