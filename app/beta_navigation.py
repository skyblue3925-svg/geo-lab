"""Shared beta navigation for the deploy-focused Streamlit shell."""

from __future__ import annotations

import streamlit as st


KOPPEN_CLIMATE_URL = "https://koppen-climate-lab.pages.dev/"

NAV_ITEMS = [
    {
        "key": "home",
        "label": "베타 홈",
        "url": "/",
        "caption": "애니메이션 스튜디오 중심 베타",
    },
    {
        "key": "animation",
        "label": "애니메이션 스튜디오",
        "url": "/Animation_Studio",
        "caption": "지형 형성 이미지 시퀀스",
    },
    {
        "key": "high_school",
        "label": "고등학교 세계지리",
        "url": "/High_School_Geography",
        "caption": "고등학교 세계지리 수업",
    },
    {
        "key": "koppen",
        "label": "쾨펜 기후 그래프",
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

    st.sidebar.markdown("### 지오랩 베타")
    st.sidebar.caption("애니메이션 스튜디오 중심 공개 베타")

    for item in NAV_ITEMS:
        label = str(item["label"])
        if item["key"] == active:
            st.sidebar.markdown(f"**{label}**")
            st.sidebar.caption(str(item["caption"]))
        else:
            st.sidebar.markdown(f"[{label}]({item['url']})")
