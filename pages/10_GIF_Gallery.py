from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.beta_navigation import render_beta_sidebar
from app.services.animation_assets import (
    animation_quality_note_for_landform,
    is_student_recommended_landform,
    list_image_sequence_gif_assets,
    ordered_landform_group_labels,
    teaching_tags_for_landform,
)
from app.services.streamlit_compat import image_stretch


def format_size(size_bytes: int) -> str:
    return f"{size_bytes / 1024 / 1024:.1f} MB"


def render_tag_row(tags: tuple[str, ...]) -> None:
    if not tags:
        return
    tag_html = "".join(
        f"<span class='gif-gallery-tag'>{tag}</span>"
        for tag in tags[:4]
    )
    st.markdown(
        f"""
        <div class="gif-gallery-tag-row">{tag_html}</div>
        <style>
          .gif-gallery-tag-row {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.25rem;
            margin: 0.25rem 0 0.45rem 0;
          }}
          .gif-gallery-tag {{
            border: 1px solid #d4d4d4;
            border-radius: 4px;
            padding: 0.1rem 0.35rem;
            color: #404040;
            background: #fafafa;
            font-size: 0.78rem;
            line-height: 1.4;
            white-space: nowrap;
          }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def open_lab_with_asset(asset) -> None:
    st.session_state["gallery_lab_preset"] = {
        "user_mode": "학생 단순모드",
        "scenario_category": "추가 지형",
        "selected_landform_id": asset.landform_id,
        "speed_mode": "균형",
        "force_level": 60,
        "auto_run": False,
        "showcase_title": f"{asset.title} GIF 갤러리",
    }
    if hasattr(st, "switch_page"):
        st.switch_page("pages/3_🧪_Lab.py")
    st.success("Lab preset을 준비했습니다. 왼쪽 메뉴에서 Lab을 열면 같은 지형으로 시작합니다.")


st.set_page_config(
    page_title="GIF 갤러리",
    page_icon="🎞️",
    layout="wide",
)

render_beta_sidebar("gif_gallery")

st.markdown("## GIF 갤러리")
st.caption("지형 형성 이미지 시퀀스 GIF만 모아 보는 화면입니다.")

gif_assets = list_image_sequence_gif_assets()
if not gif_assets:
    st.warning("아직 생성된 GIF가 없습니다. scripts/build_image_sequence_gifs.py를 먼저 실행하세요.")
    st.stop()

metric_cols = st.columns(3)
metric_cols[0].metric("GIF", len(gif_assets))
metric_cols[1].metric("전체 용량", format_size(sum(asset.size_bytes for asset in gif_assets)))
metric_cols[2].metric("평균 프레임", round(sum(asset.frame_count for asset in gif_assets) / len(gif_assets)))

available_categories = {asset.category for asset in gif_assets}
ordered_categories = [
    category
    for category in ordered_landform_group_labels()
    if category in available_categories
]
extra_categories = sorted(available_categories - set(ordered_categories))
categories = ["전체"] + ordered_categories + extra_categories
filter_col1, filter_col2 = st.columns([1.0, 1.2])
with filter_col1:
    category = st.selectbox("분류", categories)
with filter_col2:
    view_filter = st.selectbox(
        "보기",
        ["전체", "학생 설명용 추천", "품질 점검 필요"],
    )
query = st.text_input("검색", placeholder="지형 이름 또는 id")

filtered_assets = gif_assets
if category != "전체":
    filtered_assets = [asset for asset in filtered_assets if asset.category == category]
if view_filter == "학생 설명용 추천":
    filtered_assets = [
        asset for asset in filtered_assets
        if is_student_recommended_landform(asset.landform_id)
    ]
elif view_filter == "품질 점검 필요":
    filtered_assets = [
        asset for asset in filtered_assets
        if animation_quality_note_for_landform(asset.landform_id)
    ]
if query.strip():
    needle = query.strip().lower()
    filtered_assets = [
        asset
        for asset in filtered_assets
        if needle in asset.landform_id.lower() or needle in asset.title.lower()
    ]

st.caption(f"{len(filtered_assets)}개 표시")

per_page = st.selectbox("페이지당", [9, 12, 18, 38], index=1)
page_count = max((len(filtered_assets) + per_page - 1) // per_page, 1)
page_number = st.number_input("페이지", min_value=1, max_value=page_count, value=1, step=1)
start = (int(page_number) - 1) * per_page
visible_assets = filtered_assets[start : start + per_page]

columns = st.columns(3)
for index, asset in enumerate(visible_assets):
    with columns[index % 3]:
        st.markdown(f"### {asset.title}")
        st.caption(f"{asset.landform_id} · {asset.frame_count} frames · {format_size(asset.size_bytes)}")
        render_tag_row(teaching_tags_for_landform(asset.landform_id))
        quality_note = animation_quality_note_for_landform(asset.landform_id)
        if quality_note:
            st.warning(quality_note)
        image_stretch(st, str(asset.gif_path))
        if st.button("Lab에서 실험", key=f"gif_gallery_lab_{asset.landform_id}"):
            open_lab_with_asset(asset)

