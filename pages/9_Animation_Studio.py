"""Animation Studio page for generated terrain formation assets."""

from __future__ import annotations

from contextlib import suppress
from PIL import Image
import subprocess
import sys
import json
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from app.beta_navigation import render_beta_sidebar
from app.components.babylon_renderer import create_babylon_terrain_viewer_html
from app.components.threejs_renderer import create_threejs_terrain_viewer_html
from app.services.animation_assets import (
    PROJECT_ROOT,
    animation_quality_note_for_landform,
    find_image_sequence_filmstrip_path,
    get_asset_counts,
    image_sequence_grid_for_landform,
    is_student_recommended_landform,
    list_storyboard_assets,
    load_storyboard_panel_image,
    read_image_data_uri,
    teaching_tags_for_landform,
)
from app.services.streamlit_compat import image_stretch
from app.services.terrain_simulation_payload import (
    build_simulation_terrain_3d_payload,
    is_simulation_terrain_supported,
)
from app.services.terrain_lab_catalog import (
    GROUP_LABELS_KO,
    get_additional_lab_scenario,
    process_factor_definitions_for_scenario,
)


st.set_page_config(page_title="애니메이션 스튜디오", page_icon="🎞️", layout="wide")
render_beta_sidebar("animation")


def short_path(path: Path) -> str:
    return path.name


def show_responsive_image(image) -> None:
    image_stretch(st, image)


def show_static_media_frame(path: Path) -> bool:
    with suppress(Exception):
        with Image.open(path) as image:
            image.seek(0)
            frame = image.convert("RGB").copy()
        show_responsive_image(frame)
        return True
    return False


def show_filmstrip_sequence_player(asset, *, frame_interval_ms: int, height: int = 360) -> bool:
    filmstrip_path = find_image_sequence_filmstrip_path(asset)
    if filmstrip_path is None:
        return False

    data_uri = read_image_data_uri(filmstrip_path)
    root_id = f"filmstrip-player-{asset.landform_id.replace('_', '-')}"
    cols, rows, frame_count = image_sequence_grid_for_landform(asset.landform_id)
    config = json.dumps(
        {
            "rootId": root_id,
            "title": asset.title,
            "dataUri": data_uri,
            "cols": cols,
            "rows": rows,
            "frameCount": frame_count,
            "frameIntervalMs": int(frame_interval_ms),
            "cellTrimPx": 2,
        },
        ensure_ascii=False,
    )
    components.html(
        f"""
        <div id="{root_id}" style="width:100%;height:{height}px;position:relative;overflow:hidden;background:#020617;border-radius:4px;">
          <canvas class="filmstrip-canvas" style="display:block;width:100%;height:100%;"></canvas>
          <div class="filmstrip-label" style="position:absolute;left:12px;top:10px;padding:4px 7px;border-radius:4px;background:rgba(2,6,23,.72);color:#e2e8f0;font:12px/1.4 system-ui,sans-serif;"></div>
          <button class="filmstrip-toggle" type="button" style="position:absolute;right:12px;top:10px;padding:6px 10px;border:0;border-radius:4px;background:#f8fafc;color:#0f172a;font:700 12px/1 system-ui,sans-serif;cursor:pointer;">재생</button>
        </div>
        <script>
          const payload = {config};
          const root = document.getElementById(payload.rootId);
          const canvas = root.querySelector(".filmstrip-canvas");
          const context = canvas.getContext("2d", {{ alpha: false }});
          const label = root.querySelector(".filmstrip-label");
          const toggle = root.querySelector(".filmstrip-toggle");
          const filmstripImage = new Image();
          filmstripImage.decoding = "async";
          filmstripImage.src = payload.dataUri;
          let frameIndex = 0;
          let timerId = null;
          let imageReady = false;

          function paint() {{
            if (!imageReady) return;
            const col = frameIndex % payload.cols;
            const row = Math.floor(frameIndex / payload.cols);
            const imageWidth = filmstripImage.naturalWidth || filmstripImage.width;
            const imageHeight = filmstripImage.naturalHeight || filmstripImage.height;
            const cellWidth = Math.floor(imageWidth / payload.cols);
            const cellHeight = Math.floor(imageHeight / payload.rows);
            const cellTrimPx = Math.max(
              0,
              Math.min(
                Number(payload.cellTrimPx || 0),
                Math.floor(cellWidth / 10),
                Math.floor(cellHeight / 10),
              ),
            );
            const sourceX = (col * cellWidth) + cellTrimPx;
            const sourceY = (row * cellHeight) + cellTrimPx;
            const sourceWidth = Math.max(1, cellWidth - (cellTrimPx * 2));
            const sourceHeight = Math.max(1, cellHeight - (cellTrimPx * 2));

            if (canvas.width !== sourceWidth || canvas.height !== sourceHeight) {{
              canvas.width = sourceWidth;
              canvas.height = sourceHeight;
            }}
            context.clearRect(0, 0, canvas.width, canvas.height);
            context.drawImage(filmstripImage, sourceX, sourceY, sourceWidth, sourceHeight, 0, 0, canvas.width, canvas.height);
            const state = timerId === null ? "정지" : "재생";
            label.textContent = `${{payload.title}} · ${{String(frameIndex + 1).padStart(2, "0")}} / ${{payload.frameCount}} · ${{payload.frameIntervalMs}}ms · ${{state}}`;
          }}

          function advance() {{
            frameIndex = (frameIndex + 1) % payload.frameCount;
            paint();
          }}

          function play() {{
            if (timerId !== null) return;
            timerId = window.setInterval(advance, Math.max(payload.frameIntervalMs, 40));
            toggle.textContent = "정지";
            paint();
          }}

          function pause() {{
            if (timerId === null) return;
            window.clearInterval(timerId);
            timerId = null;
            toggle.textContent = "재생";
            paint();
          }}

          toggle.addEventListener("click", () => {{
            if (timerId === null) {{
              play();
            }} else {{
              pause();
            }}
          }});

          filmstripImage.addEventListener("load", () => {{
            imageReady = true;
            paint();
          }});
          filmstripImage.addEventListener("error", () => {{
            label.textContent = `${{payload.title}} · 이미지를 불러오지 못했습니다.`;
          }});
          paint();
        </script>
        """,
        height=height,
        scrolling=False,
    )
    return True


st.markdown("## 애니메이션 스튜디오")
st.caption("생성 이미지, 프롬프트, 이미지 시퀀스, 선택형 3D 뷰어를 확인하는 제작 화면입니다.")

assets = list_storyboard_assets()
counts = get_asset_counts()

metric_cols = st.columns(4)
metric_cols[0].metric("원본 스토리보드", counts["storyboards"])
metric_cols[1].metric("프롬프트", counts["prompts"])
metric_cols[2].metric("이미지 시퀀스", counts["image_sequences"])
metric_cols[3].metric("AI 플랜", counts["image_sequence_plans"])

if not assets:
    st.info("아직 생성된 지형 스토리보드가 없습니다.")
    st.stop()

category_labels = {
    "river_delta": "하천·삼각주",
    "glacial_volcanic": "빙하·화산",
    "karst_arid_coastal": "카르스트·건조·해안",
}

category_options = ["전체"] + sorted({asset.category for asset in assets})
filter_col, asset_col = st.columns([1.0, 1.6])
with filter_col:
    selected_category = st.selectbox(
        "분류",
        category_options,
        format_func=lambda value: category_labels.get(value, value),
    )

filtered_assets = [
    asset for asset in assets
    if selected_category == "전체" or asset.category == selected_category
]

with asset_col:
    selected_asset = st.selectbox(
        "지형",
        filtered_assets,
        format_func=lambda asset: f"{asset.title} ({asset.landform_id})",
    )

tags = teaching_tags_for_landform(selected_asset.landform_id)
if tags:
    st.caption(" · ".join(tags))
if is_student_recommended_landform(selected_asset.landform_id):
    st.success("학생 설명용으로 먼저 보여주기 좋은 지형입니다.")
quality_note = animation_quality_note_for_landform(selected_asset.landform_id)
if quality_note:
    st.warning(quality_note)

catalog_scenario = get_additional_lab_scenario(selected_asset.landform_id)
if catalog_scenario is not None:
    st.markdown("### Lab 카탈로그")
    catalog_cols = st.columns([1.0, 1.0, 1.2])
    catalog_cols[0].metric(
        "분류",
        GROUP_LABELS_KO.get(catalog_scenario.group, catalog_scenario.group),
    )
    catalog_cols[1].metric("모형 계열", catalog_scenario.simulation_family)
    catalog_cols[2].caption(f"표면 소스: {catalog_scenario.procedural_surface_source}")

    with st.expander("형성 단계와 조절 요인", expanded=False):
        st.markdown("**형성 단계**")
        for index, step in enumerate(catalog_scenario.formation_steps_ko, start=1):
            st.markdown(f"{index}. {step}")

        factor_definitions = process_factor_definitions_for_scenario(catalog_scenario.landform_id)
        if factor_definitions:
            st.markdown("**Lab 조절 요인**")
            for definition in factor_definitions:
                st.caption(f"{definition.label_ko}: {definition.description_ko}")

image_frame_interval_ms = 140
if selected_asset.has_image_sequence:
    playback_col, playback_note_col = st.columns([1.0, 2.0])
    with playback_col:
        image_frame_interval_ms = st.slider(
            "이미지 시퀀스 프레임 간격(ms)",
            80,
            500,
            140,
            10,
            key=f"studio_image_frame_interval_{selected_asset.landform_id}",
        )
    with playback_note_col:
        st.caption("재생 버튼을 누르기 전까지 정지합니다. 값이 클수록 느리게 재생됩니다.")

st.markdown("### 원본과 애니메이션")
preview_col, sequence_col, cinematic_col = st.columns(3)
with preview_col:
    st.markdown("**4단계 스토리보드**")
    st.caption(short_path(selected_asset.storyboard_path))
    show_responsive_image(str(selected_asset.storyboard_path))

with sequence_col:
    st.markdown("**이미지 시퀀스 애니메이션**")
    if selected_asset.has_image_sequence and selected_asset.image_sequence_animation_path is not None:
        st.caption(f"{short_path(selected_asset.image_sequence_animation_path)} · {image_frame_interval_ms}ms/frame")
        if not show_filmstrip_sequence_player(
            selected_asset,
            frame_interval_ms=image_frame_interval_ms,
            height=360,
        ):
            show_static_media_frame(selected_asset.image_sequence_animation_path)
    else:
        st.warning("아직 실제 이미지 시퀀스 애니메이션이 없습니다.")
        if selected_asset.has_image_sequence_plan and selected_asset.image_sequence_plan_path is not None:
            st.caption(f"AI in-between 플랜 준비됨: {short_path(selected_asset.image_sequence_plan_path)}")

with cinematic_col:
    st.markdown("**키프레임 preview**")
    if selected_asset.has_cinematic_animation and selected_asset.cinematic_animation_path is not None:
        st.caption(short_path(selected_asset.cinematic_animation_path))
        show_static_media_frame(selected_asset.cinematic_animation_path)
    else:
        st.warning("아직 키프레임 preview가 없습니다.")

st.markdown("### 선택형 3D 실험")
st.caption("렌더링 부하를 줄이기 위해 기본값은 꺼짐입니다. 필요할 때만 켜서 Babylon.js 또는 Three.js로 필름스트립 텍스처와 절차적 지형 표면을 함께 확인합니다.")

if selected_asset.has_image_sequence:
    show_3d_viewer = st.checkbox(
        "3D 실험 뷰어 보기",
        value=False,
        key=f"studio_show_3d_viewer_{selected_asset.landform_id}",
    )
    if show_3d_viewer:
        renderer_col, height_col, grid_col, frame_col = st.columns([1.1, 1.0, 1.0, 1.0])
        with renderer_col:
            renderer_choice = st.radio(
                "렌더러",
                ["Babylon.js", "Three.js"],
                horizontal=True,
                key=f"studio_3d_renderer_{selected_asset.landform_id}",
            )
        with height_col:
            viewer_height = st.slider("뷰어 높이", 480, 820, 620, 20, key="studio_3d_height")
        with grid_col:
            viewer_grid = st.slider("표면 격자", 24, 72, 48, 4, key="studio_3d_grid")
        with frame_col:
            surface_frames = st.slider("표면 프레임", 6, 20, 10, 1, key="studio_3d_surface_frames")

        simulation_available = is_simulation_terrain_supported(selected_asset.landform_id)
        terrain_source = "절차적 샘플 지형"
        if simulation_available:
            terrain_source = st.radio(
                "3D 데이터",
                ["지형 과정 3D 시뮬레이션", "절차적 샘플 지형"],
                horizontal=True,
                key=f"studio_3d_source_{selected_asset.landform_id}",
            )
        else:
            st.caption("이 지형은 아직 SimpleLEM 시나리오 매핑이 없어 절차적 샘플 지형으로 표시합니다.")

        terrain_payload = None
        if terrain_source == "지형 과정 3D 시뮬레이션":
            terrain_payload = build_simulation_terrain_3d_payload(
                selected_asset.landform_id,
                grid_size=viewer_grid,
                frame_count=surface_frames,
            )
            if terrain_payload is None:
                st.warning("이 지형은 현재 물리 시뮬레이션 payload를 만들 수 없어 절차적 샘플로 대체합니다.")
            else:
                support_label = {
                    "direct_simple_lem": "대표 물리장",
                    "process_proxy": "대표 과정 근사",
                }.get(terrain_payload.get("simulationSupportLevel"), "실험 모델")
                st.caption(
                    f"{support_label} · {terrain_payload['surfaceFrameCount']}프레임 · "
                    f"{terrain_payload.get('simulationProcessFamily', 'terrain')}"
                )
                if terrain_payload.get("simulationCaveat"):
                    st.caption(str(terrain_payload["simulationCaveat"]))

        if renderer_choice == "Babylon.js":
            viewer_html = create_babylon_terrain_viewer_html(
                selected_asset,
                viewer_height=viewer_height,
                grid_size=viewer_grid,
                surface_frames=surface_frames,
                terrain_payload=terrain_payload,
            )
        else:
            viewer_html = create_threejs_terrain_viewer_html(
                selected_asset,
                viewer_height=viewer_height,
                grid_size=viewer_grid,
                surface_frames=surface_frames,
                terrain_payload=terrain_payload,
            )

        if viewer_html:
            components.html(viewer_html, height=viewer_height + 8, scrolling=False)
        else:
            st.info("이 지형은 아직 선택한 3D 실험 뷰어에 필요한 필름스트립 자산이 없습니다.")
    else:
        st.info("3D 뷰어는 꺼져 있습니다. 이미지 애니메이션만 확인하면 브라우저 부하가 줄어듭니다.")
else:
    st.info("이미지 시퀀스가 준비된 지형부터 3D 실험 뷰어를 재생할 수 있습니다.")

st.markdown("### 단계별 텍스처 확인")
stage = st.slider("단계", 0.0, 1.0, 0.0, 0.05)
panel = load_storyboard_panel_image(selected_asset.landform_id, stage)
if panel is not None:
    show_responsive_image(panel)
else:
    st.info("단계 텍스처를 찾지 못했습니다.")

st.markdown("### 프롬프트")
if selected_asset.has_prompt:
    st.info("프롬프트 원문은 공개 화면에서 표시하지 않습니다.")
    st.caption("내부 제작용 prompt 파일은 서버에 보관되어 있으며, 공개 베타 UI에서는 노출하지 않습니다.")
else:
    st.info("연결된 프롬프트가 없습니다.")

st.markdown("### 빌드")
st.caption("4단계 스토리보드를 기준으로 이미지 시퀀스를 만들거나, AI in-between 생성용 플랜을 다시 뽑을 수 있습니다.")
build_col1, build_col2 = st.columns(2)

with build_col1:
    if st.button("선택 지형 이미지 시퀀스 재빌드", use_container_width=True):
        script_path = PROJECT_ROOT / "scripts" / "build_storyboard_image_sequence.py"
        result = subprocess.run(
            [
                sys.executable,
                str(script_path),
                "--force",
                "--only",
                selected_asset.landform_id,
            ],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            st.success("이미지 시퀀스 재빌드 완료")
            if result.stdout:
                st.code(result.stdout)
        else:
            st.error("이미지 시퀀스 재빌드 실패")
            st.code(result.stderr or result.stdout)

with build_col2:
    if st.button("선택 지형 AI 프롬프트 플랜 생성", use_container_width=True):
        script_path = PROJECT_ROOT / "scripts" / "build_storyboard_image_sequence.py"
        result = subprocess.run(
            [
                sys.executable,
                str(script_path),
                "--mode",
                "prompt-plan",
                "--only",
                selected_asset.landform_id,
            ],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            st.success("AI 프롬프트 플랜 생성 완료")
            if result.stdout:
                st.code(result.stdout)
        else:
            st.error("AI 프롬프트 플랜 생성 실패")
            st.code(result.stderr or result.stdout)

