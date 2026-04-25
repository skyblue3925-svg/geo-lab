from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.beta_navigation import render_beta_sidebar
from app.services.animation_assets import list_image_sequence_gif_assets


def format_size(size_bytes: int) -> str:
    return f"{size_bytes / 1024 / 1024:.1f} MB"


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

categories = ["전체"] + sorted({asset.category for asset in gif_assets})
category = st.selectbox("분류", categories)
query = st.text_input("검색", placeholder="지형 이름 또는 id")

filtered_assets = gif_assets
if category != "전체":
    filtered_assets = [asset for asset in filtered_assets if asset.category == category]
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
        with st.container(border=True):
            st.markdown(f"### {asset.title}")
            st.caption(f"{asset.landform_id} · {asset.frame_count} frames · {format_size(asset.size_bytes)}")
            st.image(str(asset.gif_path), use_container_width=True)
