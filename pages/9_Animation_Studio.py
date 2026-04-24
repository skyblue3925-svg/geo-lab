"""Animation Studio page for generated terrain formation assets."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from app.beta_navigation import render_beta_sidebar
from app.components.threejs_renderer import create_threejs_terrain_viewer_html
from app.services.animation_assets import (
    PROJECT_ROOT,
    get_asset_counts,
    list_storyboard_assets,
    load_storyboard_panel_image,
    read_image_data_uri,
    read_prompt_text,
)


st.set_page_config(page_title="Animation Studio", page_icon="🎞️", layout="wide")
render_beta_sidebar("animation")


def short_path(path: Path) -> str:
    return path.name


def show_animated_image(path: Path) -> None:
    data_uri = read_image_data_uri(path)
    st.markdown(
        f"""
        <img
          src="{data_uri}"
          style="display:block;width:100%;height:auto;border-radius:4px;"
          alt="terrain formation animation"
        />
        """,
        unsafe_allow_html=True,
    )


st.markdown("## Animation Studio")
st.caption("생성 이미지, 프롬프트, 이미지 시퀀스, 실험용 Three.js 뷰어를 한 화면에서 확인하는 제작 화면입니다.")

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

st.markdown("### 원본과 애니메이션")
preview_col, sequence_col, cinematic_col = st.columns(3)
with preview_col:
    st.markdown("**4단계 스토리보드**")
    st.caption(short_path(selected_asset.storyboard_path))
    st.image(str(selected_asset.storyboard_path), width="stretch")

with sequence_col:
    st.markdown("**이미지 시퀀스 애니메이션**")
    if selected_asset.has_image_sequence and selected_asset.image_sequence_animation_path is not None:
        st.caption(short_path(selected_asset.image_sequence_animation_path))
        show_animated_image(selected_asset.image_sequence_animation_path)
    else:
        st.warning("아직 실제 이미지 시퀀스 애니메이션이 없습니다.")
        if selected_asset.has_image_sequence_plan and selected_asset.image_sequence_plan_path is not None:
            st.caption(f"AI in-between 플랜 준비됨: {short_path(selected_asset.image_sequence_plan_path)}")

with cinematic_col:
    st.markdown("**키프레임 preview**")
    if selected_asset.has_cinematic_animation and selected_asset.cinematic_animation_path is not None:
        st.caption(short_path(selected_asset.cinematic_animation_path))
        show_animated_image(selected_asset.cinematic_animation_path)
    else:
        st.warning("아직 키프레임 preview가 없습니다.")

st.markdown("### Three.js 3D Experimental")
st.caption("필름스트립 이미지를 텍스처로 재생하고, 같은 지형 ID의 표면 생성기를 높이장으로 써서 카메라가 움직이는 실험 뷰어입니다.")

if selected_asset.has_image_sequence:
    three_col1, three_col2, three_col3 = st.columns(3)
    with three_col1:
        three_height = st.slider("뷰어 높이", 480, 820, 620, 20, key="studio_three_height")
    with three_col2:
        three_grid = st.slider("표면 격자", 24, 72, 48, 4, key="studio_three_grid")
    with three_col3:
        three_surface_frames = st.slider("표면 프레임", 6, 20, 10, 1, key="studio_three_surface_frames")

    three_html = create_threejs_terrain_viewer_html(
        selected_asset,
        viewer_height=three_height,
        grid_size=three_grid,
        surface_frames=three_surface_frames,
    )
    if three_html:
        components.html(three_html, height=three_height + 8, scrolling=False)
    else:
        st.info("이 지형은 아직 Three.js 실험 뷰어에 필요한 필름스트립 자산이 없습니다.")
else:
    st.info("이미지 시퀀스가 준비된 지형부터 Three.js 실험 뷰어를 재생할 수 있습니다.")

st.markdown("### 단계별 텍스처 확인")
stage = st.slider("단계", 0.0, 1.0, 0.0, 0.05)
panel = load_storyboard_panel_image(selected_asset.landform_id, stage)
if panel is not None:
    st.image(panel, width="stretch")
else:
    st.info("단계 텍스처를 찾지 못했습니다.")

st.markdown("### 프롬프트")
prompt_text = read_prompt_text(selected_asset)
if prompt_text:
    st.code(prompt_text, language="markdown")
else:
    st.info("연결된 프롬프트가 없습니다.")

st.markdown("### 빌드")
st.caption("4단계 스토리보드를 기준으로 이미지 시퀀스를 만들거나, AI in-between 생성용 플랜을 다시 뽑을 수 있습니다.")
build_col1, build_col2 = st.columns(2)

with build_col1:
    if st.button("선택 지형 이미지 시퀀스 재빌드", width="stretch"):
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
    if st.button("선택 지형 AI 프롬프트 플랜 생성", width="stretch"):
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
