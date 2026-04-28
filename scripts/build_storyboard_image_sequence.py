"""Build image-sequence animation assets from 4-panel terrain storyboards.

The production path is:
1. Split the generated 4-panel storyboard into clean keyframes.
2. Create prompt files for AI in-between frames between adjacent keyframes.
3. Optionally create a local draft interpolation for layout/testing only.

The draft mode is intentionally labeled as a draft. The final public animation
should replace draft frames with AI-generated in-between frames.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PROJECT_ROOT / "output" / "terrain-animation-assets"
OUTPUT_ROOT = PROJECT_ROOT / "assets" / "cinematic" / "image_sequence"
IMAGEGEN_CLI = Path.home() / ".codex" / "skills" / "imagegen" / "scripts" / "image_gen.py"

TARGET_SIZE = (1024, 1024)
DEFAULT_FRAME_COUNT = 31
DEFAULT_FPS = 12


@dataclass(frozen=True)
class SequenceFrame:
    frame_index: int
    stage: float
    keyframe_index: int | None
    from_keyframe: int | None
    to_keyframe: int | None
    transition_progress: float


def split_storyboard(image: Image.Image, *, crop_label_band: bool = True) -> list[Image.Image]:
    width, height = image.size
    top = round(height * 0.14) if crop_label_band else 0
    panels: list[Image.Image] = []
    for index in range(4):
        left = round(index * width / 4)
        right = round((index + 1) * width / 4)
        panels.append(image.crop((left, top, right, height)).convert("RGB"))
    return panels


def cover_resize(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    target_w, target_h = size
    scale = max(target_w / image.width, target_h / image.height)
    resized = image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS)
    left = (resized.width - target_w) // 2
    top = (resized.height - target_h) // 2
    return resized.crop((left, top, left + target_w, top + target_h))


def clean_keyframe(panel: Image.Image) -> Image.Image:
    frame = cover_resize(panel, TARGET_SIZE)
    frame = ImageEnhance.Color(frame).enhance(1.04)
    frame = ImageEnhance.Contrast(frame).enhance(1.03)
    return frame


def frame_plan(frame_count: int) -> list[SequenceFrame]:
    if frame_count < 4:
        raise ValueError("frame_count must be at least 4")

    frames: list[SequenceFrame] = []
    for frame_index in range(frame_count):
        stage = frame_index / (frame_count - 1)
        position = stage * 3
        nearest = round(position)
        if abs(position - nearest) < 1e-8 and 0 <= nearest <= 3:
            frames.append(
                SequenceFrame(
                    frame_index=frame_index,
                    stage=stage,
                    keyframe_index=int(nearest),
                    from_keyframe=None,
                    to_keyframe=None,
                    transition_progress=0.0,
                )
            )
            continue

        from_keyframe = min(int(math.floor(position)), 2)
        to_keyframe = from_keyframe + 1
        frames.append(
            SequenceFrame(
                frame_index=frame_index,
                stage=stage,
                keyframe_index=None,
                from_keyframe=from_keyframe,
                to_keyframe=to_keyframe,
                transition_progress=position - from_keyframe,
            )
        )
    return frames


def local_draft_frame(start: Image.Image, end: Image.Image, progress: float) -> Image.Image:
    # This is not the final animation method. It only verifies frame timing,
    # aspect, file paths, and app playback while AI frames are unavailable.
    eased = 0.5 - 0.5 * math.cos(math.pi * float(progress))
    blended = Image.blend(start, end, eased)

    start_edges = start.filter(ImageFilter.FIND_EDGES).convert("L")
    end_edges = end.filter(ImageFilter.FIND_EDGES).convert("L")
    edge = Image.blend(start_edges, end_edges, eased).filter(ImageFilter.GaussianBlur(radius=0.35))
    edge_rgb = Image.merge("RGB", (edge, edge, edge))
    blended = Image.blend(blended, edge_rgb, 0.06)
    return ImageEnhance.Sharpness(blended).enhance(1.08)


def save_keyframes(storyboard_path: Path, output_dir: Path) -> list[Path]:
    image = Image.open(storyboard_path).convert("RGB")
    panels = split_storyboard(image)
    keyframe_dir = output_dir / "keyframes"
    keyframe_dir.mkdir(parents=True, exist_ok=True)

    paths: list[Path] = []
    for index, panel in enumerate(panels):
        path = keyframe_dir / f"keyframe_{index:02d}.png"
        clean_keyframe(panel).save(path)
        paths.append(path)
    return paths


def prompt_for_frame(landform_id: str, frame: SequenceFrame) -> str:
    progress_pct = round(frame.transition_progress * 100)
    stage_pct = round(frame.stage * 100)
    return f"""Use case: infographic-diagram
Asset type: educational terrain formation animation in-between frame
Primary request: Generate exactly one full-frame image for the {landform_id} terrain formation animation at global stage {stage_pct}%.
Inputs:
- Image 1 is the earlier keyframe.
- Image 2 is the later keyframe.
Frame position: {progress_pct}% of the way from Image 1 to Image 2.
Task: Create a plausible intermediate terrain state between the two inputs. The landform itself must visibly change, not just the camera, lighting, zoom, or crop.
Style/medium: high-quality semi-realistic 3D diorama terrain render, matching the reference keyframes.
Composition/framing: same camera angle, same terrain block scale, same perspective, single continuous scene, no split screen, no collage, no storyboard panel.
Process fidelity: interpolate the geomorphic process physically. Preserve the cause-and-process logic of erosion, deposition, volcanic growth/collapse, glacial erosion, karst dissolution, aeolian transport, or coastal deposition as implied by the adjacent keyframes.
Constraints: no text, no labels, no UI, no frame numbers, no watermark, no arrows unless both reference keyframes clearly rely on arrows. Keep material texture, lighting, and camera consistent with both inputs.
Avoid: pan/zoom-only changes, simple crossfade look, duplicated panels, unrelated new terrain, decorative effects, exaggerated fantasy style.
"""


def write_prompt_plan(landform_id: str, output_dir: Path, keyframes: list[Path], frames: list[SequenceFrame], *, model: str) -> Path:
    prompt_dir = output_dir / "prompts"
    frame_dir = output_dir / "frames"
    prompt_dir.mkdir(parents=True, exist_ok=True)
    frame_dir.mkdir(parents=True, exist_ok=True)

    commands: list[str] = [
        "$ErrorActionPreference = 'Stop'",
        f"$python = '{sys.executable}'",
        f"$imagegen = '{IMAGEGEN_CLI}'",
        "",
    ]

    plan: list[dict[str, object]] = []
    for frame in frames:
        frame_path = frame_dir / f"frame_{frame.frame_index:03d}.png"
        if frame.keyframe_index is not None:
            shutil.copyfile(keyframes[frame.keyframe_index], frame_path)
            plan.append(
                {
                    "frame": frame.frame_index,
                    "stage": frame.stage,
                    "type": "keyframe",
                    "source": str(keyframes[frame.keyframe_index].relative_to(PROJECT_ROOT)).replace("\\", "/"),
                    "output": str(frame_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
                }
            )
            continue

        assert frame.from_keyframe is not None and frame.to_keyframe is not None
        prompt_path = prompt_dir / f"frame_{frame.frame_index:03d}.md"
        prompt_path.write_text(prompt_for_frame(landform_id, frame), encoding="utf-8")
        commands.append(
            " & $python $imagegen edit"
            f" --model {model}"
            f" --image '{keyframes[frame.from_keyframe]}'"
            f" --image '{keyframes[frame.to_keyframe]}'"
            f" --prompt-file '{prompt_path}'"
            f" --out '{frame_path}'"
            " --size 1024x1024 --quality high --input-fidelity high --output-format png --force"
        )
        plan.append(
            {
                "frame": frame.frame_index,
                "stage": frame.stage,
                "type": "ai_inbetween",
                "from_keyframe": frame.from_keyframe,
                "to_keyframe": frame.to_keyframe,
                "transition_progress": frame.transition_progress,
                "prompt": str(prompt_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
                "output": str(frame_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            }
        )

    plan_path = output_dir / "ai_inbetween_plan.json"
    plan_path.write_text(json.dumps({"landform_id": landform_id, "model": model, "frames": plan}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    command_path = output_dir / "run_ai_inbetween.ps1"
    command_path.write_text("\n".join(commands) + "\n", encoding="utf-8")
    return command_path


def build_draft_frames(output_dir: Path, keyframes: list[Path], frames: list[SequenceFrame]) -> None:
    frame_dir = output_dir / "frames"
    frame_dir.mkdir(parents=True, exist_ok=True)
    keyframe_images = [Image.open(path).convert("RGB") for path in keyframes]

    for frame in frames:
        frame_path = frame_dir / f"frame_{frame.frame_index:03d}.png"
        if frame.keyframe_index is not None:
            keyframe_images[frame.keyframe_index].save(frame_path)
            continue
        assert frame.from_keyframe is not None and frame.to_keyframe is not None
        draft = local_draft_frame(
            keyframe_images[frame.from_keyframe],
            keyframe_images[frame.to_keyframe],
            frame.transition_progress,
        )
        draft.save(frame_path)


def build_animation_from_frames(landform_id: str, output_dir: Path, *, fps: int) -> Path:
    frame_dir = output_dir / "frames"
    frame_paths = sorted(frame_dir.glob("frame_*.png"))
    if not frame_paths:
        raise FileNotFoundError(f"No frame images found under {frame_dir}")

    frames = [Image.open(path).convert("RGB") for path in frame_paths]
    output_path = output_dir / f"{landform_id}_image_sequence.webp"
    duration_ms = round(1000 / max(fps, 1))
    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=duration_ms,
        loop=0,
        format="WEBP",
        quality=90,
        method=2,
    )
    return output_path


def build_one(storyboard_path: Path, *, mode: str, frame_count: int, fps: int, model: str, force: bool) -> dict[str, object]:
    landform_id = storyboard_path.name.removesuffix("_storyboard_draft.png")
    category = storyboard_path.parents[1].name
    output_dir = OUTPUT_ROOT / landform_id
    if force and output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    keyframes = save_keyframes(storyboard_path, output_dir)
    frames = frame_plan(frame_count)
    command_path = write_prompt_plan(landform_id, output_dir, keyframes, frames, model=model)

    status = "prompt_plan_ready"
    animation_path: Path | None = None
    if mode == "draft":
        build_draft_frames(output_dir, keyframes, frames)
        animation_path = build_animation_from_frames(landform_id, output_dir, fps=fps)
        status = "draft_interpolation"
    elif mode == "openai":
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY is not set; run prompt-plan first or set the key before --mode openai.")
        completed = subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(command_path)],
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr or completed.stdout)
        animation_path = build_animation_from_frames(landform_id, output_dir, fps=fps)
        status = "ai_inbetween_ready"

    entry: dict[str, object] = {
        "id": f"{landform_id}_image_sequence",
        "title": f"{landform_id.replace('_', ' ')} 이미지 기반 형성과정",
        "category": category,
        "frame_count": frame_count,
        "fps": fps,
        "mode": mode,
        "status": status,
        "source_storyboard": str(storyboard_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "keyframes": [str(path.relative_to(PROJECT_ROOT)).replace("\\", "/") for path in keyframes],
        "ai_plan": str((output_dir / "ai_inbetween_plan.json").relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "ai_command": str(command_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "description": "4개 생성 이미지를 키프레임으로 삼아 중간 형성 장면을 이미지 시퀀스로 만드는 산출물입니다.",
    }
    if animation_path is not None:
        entry["file"] = str(animation_path.relative_to(PROJECT_ROOT / "assets" / "cinematic")).replace("\\", "/")
    return entry


def merge_metadata(entries: list[dict[str, object]], *, partial: bool) -> dict[str, object]:
    metadata_path = OUTPUT_ROOT / "metadata.json"
    if partial and metadata_path.exists():
        manifest = json.loads(metadata_path.read_text(encoding="utf-8"))
        by_id = {entry.get("id"): entry for entry in manifest.get("videos", [])}
        for entry in entries:
            by_id[entry.get("id")] = entry
        manifest["videos"] = list(by_id.values())
        return manifest
    return {
        "version": "1.0",
        "description": "Image-sequence terrain formation animations generated from 4-panel storyboard keyframes.",
        "videos": entries,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["prompt-plan", "draft", "openai"], default="draft")
    parser.add_argument("--only", nargs="*", help="Optional landform ids to build.")
    parser.add_argument("--frames", type=int, default=DEFAULT_FRAME_COUNT)
    parser.add_argument("--fps", type=int, default=DEFAULT_FPS)
    parser.add_argument("--model", default="gpt-image-1.5")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    storyboard_paths = sorted(SOURCE_ROOT.glob("*/*/*_storyboard_draft.png"))
    if args.only:
        wanted = set(args.only)
        storyboard_paths = [
            path for path in storyboard_paths
            if path.name.removesuffix("_storyboard_draft.png") in wanted
        ]

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    entries = [
        build_one(path, mode=args.mode, frame_count=args.frames, fps=args.fps, model=args.model, force=args.force)
        for path in storyboard_paths
    ]

    manifest = merge_metadata(entries, partial=bool(args.only))
    metadata_path = OUTPUT_ROOT / "metadata.json"
    metadata_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"built={len(entries)}")
    print(f"mode={args.mode}")
    print(f"frames={args.frames}")
    print(f"output={OUTPUT_ROOT}")


if __name__ == "__main__":
    main()
