from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent
COMPOSITIONS = ROOT / "compositions"


@dataclass(frozen=True)
class TerrainVideo:
    landform_id: str
    title: str
    subtitle: str
    gif: str
    observation: str
    labels: tuple[tuple[str, str], tuple[str, str], tuple[str, str]]


VIDEOS: tuple[TerrainVideo, ...] = (
    TerrainVideo(
        "barchan",
        "바르한 형성과정",
        "모래 공급이 제한된 건조 지역에서 바람이 만든 초승달 모양 사구입니다.",
        "assets/barchan_image_sequence.gif",
        "풍상면은 깎이고 풍하면에는 모래가 쌓이면서 사구가 바람 방향으로 이동합니다.",
        (
            ("풍속", "모래 이동량을 키우는 주 작용"),
            ("모래 공급", "사구의 크기와 연속성을 결정"),
            ("풍하면 퇴적", "초승달형 전진을 보여주는 핵심"),
        ),
    ),
    TerrainVideo(
        "waterfall",
        "폭포 형성과정",
        "단단한 암석층과 약한 암석층의 차이, 하천 침식이 만나 급경사 낙차를 만듭니다.",
        "assets/waterfall_image_sequence.gif",
        "하천은 약한 암석을 더 빠르게 깎고, 후퇴 침식이 계속되면서 폭포와 협곡이 발달합니다.",
        (
            ("차별 침식", "약한 암석층이 더 빠르게 깎임"),
            ("낙차 형성", "하상 고도 차이가 커짐"),
            ("후퇴 침식", "폭포 위치가 상류 쪽으로 이동"),
        ),
    ),
    TerrainVideo(
        "delta",
        "삼각주 형성과정",
        "하천이 운반하던 퇴적물이 하구에서 쌓이며 바다 쪽으로 평야를 확장합니다.",
        "assets/delta_image_sequence.gif",
        "유속이 느려지는 하구에서 모래와 실트가 쌓이고, 분류 하천이 갈라지며 삼각주 전면이 성장합니다.",
        (
            ("퇴적물 공급", "하천이 운반한 물질이 쌓임"),
            ("유속 감소", "하구에서 운반력이 약해짐"),
            ("분류 하천", "퇴적체 위로 물길이 갈라짐"),
        ),
    ),
)


STYLE = """
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body {
        width: 1920px;
        height: 1080px;
        overflow: hidden;
        background: #f7f3e8;
        color: #151515;
        font-family: "Pretendard", "Noto Sans KR", "Segoe UI", sans-serif;
      }
      #root {
        position: relative;
        width: 1920px;
        height: 1080px;
        overflow: hidden;
        background:
          linear-gradient(90deg, rgba(247, 243, 232, 0.9), rgba(247, 243, 232, 0.48)),
          radial-gradient(circle at 76% 20%, rgba(240, 178, 93, 0.28), transparent 32%),
          #f7f3e8;
      }
      .clip { position: absolute; }
      .creator {
        left: 72px;
        top: 46px;
        font-size: 34px;
        font-weight: 700;
        color: #5c4a2d;
      }
      .title { left: 72px; top: 132px; width: 680px; }
      .title h1 {
        font-size: 88px;
        line-height: 1.05;
        letter-spacing: 0;
      }
      .title p {
        margin-top: 24px;
        font-size: 35px;
        line-height: 1.35;
        color: #4b5563;
      }
      .terrain-frame {
        right: 80px;
        top: 86px;
        width: 980px;
        height: 740px;
        border: 8px solid #161616;
        background: #0f172a;
        overflow: hidden;
      }
      .terrain-frame img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        display: block;
      }
      .stage {
        left: 72px;
        bottom: 126px;
        width: 620px;
        padding: 36px 42px;
        background: rgba(255, 255, 255, 0.78);
        border: 2px solid rgba(22, 22, 22, 0.16);
      }
      .stage strong {
        display: block;
        font-size: 42px;
        margin-bottom: 18px;
      }
      .stage span {
        display: block;
        font-size: 31px;
        line-height: 1.42;
        color: #374151;
      }
      .labels {
        right: 80px;
        bottom: 116px;
        width: 980px;
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 18px;
      }
      .label {
        padding: 24px 28px;
        min-height: 112px;
        background: #151515;
        color: #fff;
      }
      .label b {
        display: block;
        font-size: 28px;
        margin-bottom: 8px;
      }
      .label span {
        color: #d1d5db;
        font-size: 23px;
        line-height: 1.34;
      }
      .bar {
        left: 72px;
        right: 80px;
        bottom: 52px;
        height: 14px;
        background: rgba(21, 21, 21, 0.16);
        overflow: hidden;
      }
      .bar-fill {
        width: 100%;
        height: 100%;
        background: #0f766e;
        transform-origin: left center;
      }
"""


def composition_html(video: TerrainVideo) -> str:
    labels = "\n".join(
        f"""        <div class="label">
          <b>{title}</b>
          <span>{body}</span>
        </div>"""
        for title, body in video.labels
    )
    return f"""<!doctype html>
<html lang="ko">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>{STYLE}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="{video.landform_id}" data-start="0" data-duration="10" data-width="1920" data-height="1080">
      <div class="clip creator" data-start="0" data-duration="10" data-track-index="1">제작자: 한백고등학교 김한솔</div>
      <section class="clip title" data-start="0" data-duration="10" data-track-index="2">
        <h1>{video.title}</h1>
        <p>{video.subtitle}</p>
      </section>
      <figure class="clip terrain-frame" data-start="0" data-duration="10" data-track-index="3">
        <img src="{video.gif}" alt="{video.title} GIF" />
      </figure>
      <section class="clip stage" data-start="1" data-duration="8" data-track-index="4">
        <strong>관찰 포인트</strong>
        <span>{video.observation}</span>
      </section>
      <section class="clip labels" data-start="2" data-duration="8" data-track-index="5">
{labels}
      </section>
      <div class="clip bar" data-start="0" data-duration="10" data-track-index="6">
        <div id="bar-fill" class="bar-fill"></div>
      </div>
    </div>
    <script>
      window.__timelines = window.__timelines || {{}};
      const tl = gsap.timeline({{ paused: true }});
      tl.from(".creator", {{ opacity: 0, y: -24, duration: 0.6 }}, 0);
      tl.from(".title", {{ opacity: 0, x: -40, duration: 0.8 }}, 0.2);
      tl.from(".terrain-frame", {{ opacity: 0, scale: 0.97, duration: 0.9 }}, 0.4);
      tl.from(".stage", {{ opacity: 0, y: 36, duration: 0.7 }}, 1.0);
      tl.from(".label", {{ opacity: 0, y: 28, stagger: 0.18, duration: 0.6 }}, 2.0);
      tl.fromTo("#bar-fill", {{ scaleX: 0 }}, {{ scaleX: 1, duration: 10, ease: "none" }}, 0);
      window.__timelines["{video.landform_id}"] = tl;
    </script>
  </body>
</html>
"""


def preview_html() -> str:
    cards = "\n".join(
        f"""      <article class="card">
        <img src="{video.gif}" alt="{video.title}" />
        <div>
          <h2>{video.title}</h2>
          <p>{video.observation}</p>
          <a href="compositions/{video.landform_id}.html">HyperFrames composition 열기</a>
        </div>
      </article>"""
        for video in VIDEOS
    )
    return f"""<!doctype html>
<html lang="ko">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Geo-Lab HyperFrames 지형 영상 예시</title>
    <style>
      * {{ box-sizing: border-box; }}
      body {{ margin: 0; background: #f5f1e7; color: #151515; font-family: "Pretendard", "Noto Sans KR", "Segoe UI", sans-serif; }}
      header {{ padding: 30px clamp(18px, 4vw, 54px); border-bottom: 1px solid rgba(21,21,21,.12); }}
      h1 {{ margin: 0 0 8px; font-size: clamp(30px, 5vw, 56px); letter-spacing: 0; }}
      .sub {{ margin: 0; color: #4b5563; font-size: 20px; line-height: 1.45; }}
      main {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; padding: 28px clamp(18px, 4vw, 54px) 54px; }}
      .card {{ background: rgba(255,255,255,.78); border: 1px solid rgba(21,21,21,.14); overflow: hidden; }}
      .card img {{ width: 100%; aspect-ratio: 4 / 3; object-fit: cover; display: block; background: #111827; }}
      .card div {{ padding: 18px 20px 22px; }}
      h2 {{ margin: 0 0 8px; font-size: 24px; }}
      p {{ margin: 0 0 14px; color: #374151; font-size: 17px; line-height: 1.5; }}
      a {{ color: #0369a1; font-weight: 800; }}
    </style>
  </head>
  <body>
    <header>
      <h1>HyperFrames 지형 영상 예시</h1>
      <p class="sub">바르한, 폭포, 삼각주 GIF를 수업용 MP4로 렌더링하기 위한 HTML composition 시안입니다. 제작자: 한백고등학교 김한솔</p>
    </header>
    <main>
{cards}
    </main>
  </body>
</html>
"""


def main() -> None:
    COMPOSITIONS.mkdir(exist_ok=True)
    for video in VIDEOS:
        (COMPOSITIONS / f"{video.landform_id}.html").write_text(composition_html(video), encoding="utf-8")
    (ROOT / "index.html").write_text(composition_html(VIDEOS[0]), encoding="utf-8")
    (ROOT / "preview.html").write_text(preview_html(), encoding="utf-8")


if __name__ == "__main__":
    main()
