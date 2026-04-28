"""Student-facing terrain formation library."""

from __future__ import annotations

import streamlit as st

from app.services.animation_assets import (
    get_asset_counts,
    list_storyboard_assets,
    load_storyboard_panel_image,
    read_image_data_uri,
    read_prompt_text,
)
from app.services.streamlit_compat import image_stretch


st.set_page_config(page_title="Learn", page_icon="🌍", layout="wide")


def show_animated_image(path) -> None:
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

st.markdown("## Learn")
st.caption("학생용 화면입니다. 지형 형성 애니메이션과 핵심 이미지만 빠르게 확인합니다.")

assets = list_storyboard_assets()
counts = get_asset_counts()

if not assets:
    st.info("아직 등록된 지형 애니메이션이 없습니다.")
    st.stop()

metric_cols = st.columns(4)
metric_cols[0].metric("지형", counts["storyboards"])
metric_cols[1].metric("이미지 시퀀스", counts["image_sequences"])
metric_cols[2].metric("AI 플랜", counts["image_sequence_plans"])
metric_cols[3].metric("프롬프트", counts["prompts"])

category_labels = {
    "river_delta": "하천·삼각주",
    "glacial_volcanic": "빙하·화산",
    "karst_arid_coastal": "카르스트·건조·해안",
}

category_options = ["전체"] + sorted({asset.category for asset in assets})
selected_category = st.radio(
    "분류",
    category_options,
    horizontal=True,
    format_func=lambda value: category_labels.get(value, value),
)

filtered_assets = [
    asset for asset in assets
    if selected_category == "전체" or asset.category == selected_category
]

selected_asset = st.selectbox(
    "지형",
    filtered_assets,
    format_func=lambda asset: f"{asset.title} ({asset.landform_id})",
)

st.markdown(f"### {selected_asset.title}")
viewer_col, source_col = st.columns([1.3, 1.0])

with viewer_col:
    if selected_asset.has_image_sequence:
        st.caption("이미지 기반 형성과정 시퀀스")
    else:
        st.caption("4단계 키프레임 preview")
    if selected_asset.has_animation and selected_asset.animation_path is not None:
        show_animated_image(selected_asset.animation_path)
    else:
        st.warning("이미지 시퀀스가 아직 없습니다.")

with source_col:
    st.caption("4개 원본 키프레임")
    image_stretch(st, str(selected_asset.storyboard_path))

st.markdown("### 단계별 핵심 이미지")
stage_cols = st.columns(4)
for index, col in enumerate(stage_cols):
    stage = index / 3
    panel = load_storyboard_panel_image(selected_asset.landform_id, stage, crop_label_band=False)
    with col:
        st.caption(f"{index + 1}단계")
        if panel is not None:
            image_stretch(st, panel)
        else:
            st.info("이미지 없음")

with st.expander("제작 프롬프트 보기"):
    prompt_text = read_prompt_text(selected_asset)
    if prompt_text:
        st.code(prompt_text, language="markdown")
    else:
        st.info("프롬프트가 없습니다.")

