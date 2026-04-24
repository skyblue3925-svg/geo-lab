"""Streamlit link-out page for the existing Koppen climate graph app."""

from __future__ import annotations

import streamlit as st

from app.beta_navigation import render_beta_sidebar


KOPPEN_CLIMATE_URL = "https://koppen-climate-lab.pages.dev/"


def render_koppen_climate_page() -> None:
    render_beta_sidebar("koppen")

    st.markdown("## 쾨펜 기후 그래프")
    st.caption("기존 쾨펜 기후 그래프 프로젝트로 이동합니다.")
    st.markdown(f"[쾨펜 기후 그래프 열기]({KOPPEN_CLIMATE_URL})")
