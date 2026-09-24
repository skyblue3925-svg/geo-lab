"""
자유곡류 모션그래픽 시연 (프로토타입)

기존 생성기(create_free_meander)의 지형 위에 '과정 레이어'를 얹어 영상으로 내보낸다.
- 양식화된 음영 지형 (판정 데이터는 그대로, 화면에서만 효과)
- 물 입자: 굽이 바깥쪽이 빠르고 안쪽이 느리게 흐른다
- 단계별 이름표: 공격사면·활주사면 → 자연제방·배후습지 → 우각호
- 오른쪽 단면도: 굽이 꼭짓점의 비대칭 단면과 나선형 흐름(helical flow)
- 카메라: 전체 → 굽이로 다가감 → 다시 전체

실행:
    pip install imageio-ffmpeg
    python prototypes/motion/meander_motion.py [출력.mp4] [--preview 미리보기.png]
"""
import argparse
import os
import sys

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import animation, font_manager  # noqa: E402
from matplotlib.colors import LightSource, LinearSegmentedColormap  # noqa: E402
from matplotlib.patches import FancyArrowPatch, Polygon  # noqa: E402
from scipy.ndimage import gaussian_filter, zoom  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from engine.ideal_landforms import create_free_meander  # noqa: E402

# ---------------------------------------------------------------- 설정
GRID = 120            # 생성기 해상도
UP = 3                # 화면 업샘플
NUM_BENDS = 3         # 굽이 수 (생성기 기본값 4 보다 적게 해 굽이 모양이 잘 보이게)
LABEL_BEND = 2.25     # 공격사면·활주사면 이름표를 다는 굽이 (파장 단위, 꼭짓점)
LEVEE_BEND = 1.75     # 자연제방·배후습지 이름표를 다는 굽이
FPS = 20
STAGE_FRAMES = 220    # 0 → 1 로 진행하는 프레임 수
HOLD_FRAMES = 50      # 마지막 장면 유지
N_PARTICLES = 160
SEED = 3

for cand in ("WenQuanYi Zen Hei", "Noto Sans CJK KR", "NanumGothic", "Malgun Gothic", "AppleGothic"):
    if any(cand == f.name for f in font_manager.fontManager.ttflist):
        plt.rcParams["font.family"] = cand
        break
plt.rcParams["axes.unicode_minus"] = False

BG = "#0f1720"
INK = "#e8eef2"
MUTED = "#9fb0bd"
WATER = np.array([0.22, 0.52, 0.74])
ERODE = "#ff7a59"
DEPOSIT = "#ffd166"

floodplain = LinearSegmentedColormap.from_list(
    "fp", [(0.0, "#3d5f4a"), (0.35, "#5f8a4e"), (0.6, "#88a95c"), (0.8, "#b9c47a"), (1.0, "#e2d9a4")])


# ---------------------------------------------------------------- 지형 기하
def channel_geometry(stage, amplitude):
    """생성기와 같은 수식으로 물길 중심선을 계산 (화면 좌표: 행 r, 열 c)."""
    w = h = GRID
    center = w // 2
    wl = h / NUM_BENDS
    cw = max(3, w // 20)

    def x_of(r):
        return center + amplitude * np.sin(2 * np.pi * r / wl)

    def curvature_sign(r):
        # x'' = -A (2π/wl)^2 sin θ → 굽이 바깥쪽은 sin θ 부호 방향
        return np.sign(np.sin(2 * np.pi * r / wl))

    return x_of, curvature_sign, cw, wl


def shaded_frame(elev, water_mask):
    e = zoom(elev, UP, order=1)
    wm = gaussian_filter(zoom(water_mask.astype(float), UP, order=0), 1.2) > 0.5
    z = gaussian_filter(e, 1.0)
    lo, hi = 3.0, 12.0
    rgb = floodplain(np.clip((z - lo) / (hi - lo), 0, 1))[..., :3]
    ls = LightSource(azdeg=315, altdeg=38)
    shaded = ls.shade_rgb(rgb, z, vert_exag=6, blend_mode="soft")
    shaded[wm] = WATER * 0.85 + shaded[wm] * 0.15
    return shaded


def terrain_at(stage):
    elev, meta = create_free_meander(GRID, stage, num_bends=NUM_BENDS, return_metadata=True)
    x_of, _, cw, _ = channel_geometry(stage, meta["amplitude"])
    # 하도·우각호는 고도 5m 이하. 목 절단 뒤 메워진 옛 하도는 물로 칠하지 않는다.
    water = elev <= 5.0
    oxbow = np.isclose(elev, 4.0)
    return elev, meta, water, oxbow


# ---------------------------------------------------------------- 그리기
def label(ax, text, xy, xytext, color=INK, size=11):
    return ax.annotate(
        text, xy=xy, xytext=xytext, color=color, fontsize=size, fontweight="bold",
        ha="center", va="center",
        bbox=dict(boxstyle="round,pad=0.35", fc=(0.06, 0.09, 0.12, 0.78), ec=color, lw=1.2),
        arrowprops=dict(arrowstyle="-|>", color=color, lw=1.6, shrinkA=4, shrinkB=2))


def draw_cross_section(ax, stage, t):
    """굽이 꼭짓점 단면: 바깥(오른쪽) 깊고 가파른 공격사면, 안쪽(왼쪽) 완만한 활주사면."""
    ax.clear()
    ax.set_facecolor(BG)
    ax.set_xlim(-1.3, 1.3)
    ax.set_ylim(-1.05, 0.75)
    ax.axis("off")
    grow = np.clip((stage - 0.15) / 0.45, 0, 1)
    xs = np.linspace(-1.3, 1.3, 300)
    depth = np.where(xs > 0, 0.25 + 0.55 * grow, 0.25 + 0.05 * grow)
    width_out = 0.55 - 0.1 * grow
    width_in = 0.55 + 0.25 * grow
    bed = np.where(
        xs >= 0,
        -depth * np.clip(1 - (xs / width_out) ** 4, 0, 1),
        -depth * np.clip(1 - (np.abs(xs) / width_in) ** 1.6, 0, 1),
    )
    levee = 0.12 * np.clip((stage - 0.5) / 0.3, 0, 1) * (
        np.exp(-((xs - 0.75) / 0.12) ** 2) + np.exp(-((xs + 0.95) / 0.12) ** 2))
    swamp = -0.08 * np.clip((stage - 0.7) / 0.2, 0, 1) * (np.abs(xs) > 1.05)
    ground = bed + levee + swamp
    ax.fill_between(xs, ground, -1.05, color="#6b5a45")
    ax.fill_between(xs, np.minimum(ground, 0), 0, where=ground < 0, color=WATER, alpha=0.9)
    ax.plot(xs, ground, color="#c8b28a", lw=1.5)

    if grow > 0.05:
        # 나선형 흐름: 수면에서 바깥으로, 바닥에서 안쪽으로 도는 순환
        ang = t * 2 * np.pi * 0.6
        cx, cy, rx, ry = 0.05, -0.32 * (0.6 + 0.6 * grow), 0.38, 0.16 + 0.1 * grow
        th = np.linspace(0, 2 * np.pi * 0.8, 60) + ang
        ax.plot(cx + rx * np.cos(th), cy + ry * np.sin(th), color="white", lw=1.4, alpha=0.9)
        ax.annotate("", xy=(cx + rx * np.cos(th[-1]), cy + ry * np.sin(th[-1])),
                    xytext=(cx + rx * np.cos(th[-3]), cy + ry * np.sin(th[-3])),
                    arrowprops=dict(arrowstyle="-|>", color="white", lw=1.4))
        ax.text(0.0, 0.62, "나선형 흐름", color=INK, ha="center", fontsize=11, fontweight="bold")
        ax.text(0.95, 0.35, "공격사면\n침식", color=ERODE, ha="center", fontsize=10, fontweight="bold")
        ax.text(-0.85, 0.35, "활주사면\n퇴적", color=DEPOSIT, ha="center", fontsize=10, fontweight="bold")
        # 침식 화살표(바깥 벽), 퇴적 점(안쪽)
        for k in range(3):
            yy = -0.15 - 0.2 * k * grow
            xw = width_out * 0.95
            ax.annotate("", xy=(xw + 0.12, yy), xytext=(xw - 0.05, yy),
                        arrowprops=dict(arrowstyle="-|>", color=ERODE, lw=1.6))
        rng = np.random.default_rng(1)
        px = rng.uniform(-width_in * 0.9, -0.05, int(40 * grow))
        py = np.interp(px, xs, ground) + rng.uniform(0.0, 0.05, px.size)
        ax.scatter(px, py, s=6, color=DEPOSIT, zorder=5)
    if stage > 0.55:
        ax.text(0.75, 0.2, "자연제방", color=INK, ha="center", fontsize=9)
    if stage > 0.72:
        ax.text(1.2, -0.25, "배후\n습지", color=MUTED, ha="center", fontsize=9)
    ax.text(-1.25, -0.98, "굽이 꼭짓점 단면 (안쪽 ← → 바깥쪽)", color=MUTED, fontsize=9, ha="left")


def strip_emoji(text):
    return "".join(ch for ch in text if ord(ch) < 0x2190 or 0xAC00 <= ord(ch) <= 0xD7A3
                   or 0x3130 <= ord(ch) <= 0x318F).strip()


def stage_of(frame):
    s = min(1.0, frame / STAGE_FRAMES)
    return 0.5 - 0.5 * np.cos(np.pi * s)  # 부드러운 가감속


def camera(stage, x_of):
    """전체 → 이름표 굽이 확대 → 전체."""
    full = (0, GRID * UP, GRID * UP, 0)
    wl = GRID / NUM_BENDS
    r = wl * LABEL_BEND
    cy = r * UP
    cx = x_of(r) * UP
    half = GRID * UP * 0.26
    zoomed = (cx - half * 1.2, cx + half * 1.2, cy + half, cy - half)
    k = np.clip((stage - 0.28) / 0.1, 0, 1) * (1 - np.clip((stage - 0.5) / 0.1, 0, 1))
    k = 0.5 - 0.5 * np.cos(np.pi * k)
    return tuple(f + (z - f) * k for f, z in zip(full, zoomed))


def build(out_path, preview_path=None):
    rng = np.random.default_rng(SEED)
    pr = rng.uniform(0, GRID, N_PARTICLES)          # 입자 행 위치
    pu = rng.uniform(-0.85, 0.85, N_PARTICLES)      # 물길 폭 안의 상대 위치 (-1 안쪽 … +1)
    trail = np.zeros((4, N_PARTICLES, 2))

    fig = plt.figure(figsize=(12.8, 7.2), dpi=100, facecolor=BG)
    ax_map = fig.add_axes([0.02, 0.1, 0.56, 0.86])
    ax_sec = fig.add_axes([0.61, 0.33, 0.37, 0.42])
    ax_map.set_facecolor(BG)

    title = fig.text(0.61, 0.9, "자유곡류는 어떻게 만들어질까", color=INK, fontsize=20, fontweight="bold")
    fig.text(0.61, 0.855, "Free meander · 형성 과정", color=MUTED, fontsize=12)
    caption = fig.text(0.02, 0.035, "", color=INK, fontsize=15, fontweight="bold")
    bar_bg = fig.add_axes([0.61, 0.22, 0.37, 0.018])
    fig.text(0.61, 0.25, "형성 단계", color=MUTED, fontsize=10)

    cache = {}

    def frame_fn(i):
        stage = stage_of(i)
        key = round(stage, 3)
        if key not in cache:
            cache.clear()
            cache[key] = terrain_at(stage)
        elev, meta, water, oxbow = cache[key]
        x_of, csign, cw, wl = channel_geometry(stage, meta["amplitude"])

        ax_map.clear()
        ax_map.imshow(shaded_frame(elev, water), interpolation="bilinear")
        ax_map.axis("off")

        # 물 입자: 굽이 바깥쪽이 빠름
        sgn = csign(pr)
        bend = np.abs(np.sin(2 * np.pi * pr / wl))
        speed = 0.55 * (1 + 0.8 * pu * sgn * bend * np.clip(stage / 0.3, 0, 1))
        pr[:] = (pr + speed) % GRID
        base_x = x_of(pr)
        cut = meta.get("cutoff")
        if cut:   # 목이 잘린 뒤에는 새 물길(곧은 구간)로 흐른다
            on_chord = (pr >= cut["row_start"]) & (pr <= cut["row_end"])
            base_x = np.where(on_chord, cut["col"], base_x)
        px = (base_x + pu * cw * 0.85) * UP
        py = pr * UP
        trail[1:] = trail[:-1]
        trail[0, :, 0], trail[0, :, 1] = px, py
        for k in range(3, 0, -1):
            ax_map.scatter(trail[k, :, 0], trail[k, :, 1], s=3, color="white", alpha=0.12 * (4 - k), lw=0)
        ax_map.scatter(px, py, s=5, color="white", alpha=0.95, lw=0)

        # 이름표 (올바른 위치: 굽이 꼭짓점의 바깥쪽 = 공격사면, 안쪽 = 활주사면)
        r_apex = wl * LABEL_BEND
        xa = x_of(r_apex)
        if stage > 0.22:
            label(ax_map, "빠른 흐름 → 깎임\n공격사면", ((xa + cw) * UP, r_apex * UP),
                  ((xa + cw + 20) * UP, (r_apex - 9) * UP), color=ERODE)
            label(ax_map, "느린 흐름 → 쌓임\n활주사면", ((xa - cw) * UP, r_apex * UP),
                  ((xa - cw - 20) * UP, (r_apex + 10) * UP), color=DEPOSIT)
        if stage > 0.6:
            r_l = wl * LEVEE_BEND
            xl = x_of(r_l)
            out = np.sign(np.sin(2 * np.pi * r_l / wl)) or 1.0   # 굽이 바깥쪽 방향
            label(ax_map, "자연제방", ((xl + out * cw * 1.5) * UP, r_l * UP),
                  ((xl + out * (cw + 16)) * UP, (r_l - 10) * UP))
            label(ax_map, "배후습지", ((xl + out * cw * 3.5) * UP, (r_l + 3) * UP),
                  ((xl + out * (cw + 22)) * UP, (r_l + 12) * UP), color=MUTED)
        if oxbow.any() and stage > 0.78:
            rr, cc = np.nonzero(oxbow)
            label(ax_map, "우각호", (cc.mean() * UP, rr.min() * UP),
                  (cc.mean() * UP, (rr.min() - 14) * UP), color="#8fd3ff")
            cut = meta.get("cutoff")
            if cut:
                label(ax_map, "잘린 목 → 새 물길", (cut["col"] * UP, cut["row_end"] * UP),
                      ((cut["col"] - 14) * UP, (cut["row_end"] + 12) * UP))

        x0, x1, y0, y1 = camera(stage, x_of)
        ax_map.set_xlim(x0, x1)
        ax_map.set_ylim(y0, y1)

        draw_cross_section(ax_sec, stage, i / FPS)
        caption.set_text(strip_emoji(meta.get("stage_description", "")))
        bar_bg.clear()
        bar_bg.set_xlim(0, 1)
        bar_bg.axis("off")
        bar_bg.barh(0, 1, color="#26323d")
        bar_bg.barh(0, stage, color="#5fb3e6")
        return []

    total = STAGE_FRAMES + HOLD_FRAMES
    if preview_path:
        picks = [10, 70, 110, 160, 200, total - 1]
        sheet = []
        for p in picks:
            frame_fn(p)
            fig.canvas.draw()
            sheet.append(np.asarray(fig.canvas.buffer_rgba())[..., :3].copy())
        top = np.concatenate(sheet[:3], axis=1)
        bot = np.concatenate(sheet[3:], axis=1)
        plt.imsave(preview_path, np.concatenate([top, bot], axis=0)[::2, ::2])

    import imageio_ffmpeg
    plt.rcParams["animation.ffmpeg_path"] = imageio_ffmpeg.get_ffmpeg_exe()
    anim = animation.FuncAnimation(fig, frame_fn, frames=total, blit=False)
    anim.save(out_path, writer=animation.FFMpegWriter(fps=FPS, bitrate=4000,
                                                     extra_args=["-pix_fmt", "yuv420p"]))
    plt.close(fig)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("out", nargs="?", default="meander_motion.mp4")
    ap.add_argument("--preview", default=None)
    args = ap.parse_args()
    build(args.out, args.preview)
    print("saved", args.out)
