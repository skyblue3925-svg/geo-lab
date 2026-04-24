"""Shared beta navigation for the deploy-focused Streamlit shell."""

from __future__ import annotations

import streamlit as st


KOPPEN_CLIMATE_URL = "https://koppen-climate-lab.pages.dev/"

NAV_ITEMS = [
    {
        "key": "home",
        "label": "Beta Home",
        "url": "/",
        "caption": "Animation Studio 중심 베타",
    },
    {
        "key": "animation",
        "label": "Animation Studio",
        "url": "/Animation_Studio",
        "caption": "지형 형성 이미지 시퀀스",
    },
    {
        "key": "high_school",
        "label": "High School Geography",
        "url": "/High_School_Geography",
        "caption": "고등학교 세계지리 수업",
    },
    {
        "key": "koppen",
        "label": "Köppen Climate Graph",
        "url": KOPPEN_CLIMATE_URL,
        "caption": "기존 쾨펜 기후 그래프",
    },
]


def render_beta_sidebar(active: str) -> None:
    """Render the restricted beta navigation used for deploy preview."""

    st.markdown(
        """
        <style>
          section[data-testid="stSidebar"] div[data-testid="stSidebarNav"] {
            display: none;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.sidebar.markdown("### Geo-Lab Beta")
    st.sidebar.caption("Animation Studio 중심 공개 베타")

    for item in NAV_ITEMS:
        label = str(item["label"])
        if item["key"] == active:
            st.sidebar.markdown(f"**{label}**")
            st.sidebar.caption(str(item["caption"]))
        else:
            st.sidebar.markdown(f"[{label}]({item['url']})")
