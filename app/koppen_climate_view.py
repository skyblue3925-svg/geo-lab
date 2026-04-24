"""Streamlit wrapper for the static Koppen climate graph app."""

from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components

from app.beta_navigation import render_beta_sidebar


STATIC_KOPPEN_URL = "/app/static/koppen-climate-lab/index.html"


def render_koppen_climate_page() -> None:
    render_beta_sidebar("koppen")

    st.markdown("## Köppen Climate Graph")
    st.caption("기존 쾨펜 기후 그래프 프로젝트를 Geo-Lab 베타 사이드바 안에 포함했습니다.")

    components.iframe(
        STATIC_KOPPEN_URL,
        height=920,
        scrolling=True,
    )
