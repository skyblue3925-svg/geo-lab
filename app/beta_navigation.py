"""Shared navigation helpers for the deploy-focused Streamlit shell."""

from __future__ import annotations

from pathlib import Path

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STYLE_PATH = PROJECT_ROOT / "assets" / "style.css"
KOPPEN_CLIMATE_URL = "https://koppen-climate-lab.pages.dev/"

NAV_ITEMS = [
    {
        "key": "home",
        "label": "홈",
        "url": "/",
        "caption": "지오랩 시작 화면",
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


def load_project_style() -> None:
    """Apply the same project styling used by the local Streamlit pages."""

    if STYLE_PATH.exists():
        st.markdown(f"<style>{STYLE_PATH.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def render_beta_sidebar(active: str) -> None:
    """Append beta shortcuts while keeping the native local-style sidebar."""

    load_project_style()

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 공개 베타 빠른 링크")
    st.sidebar.caption("기본 로컬 메뉴 아래에 배포용 핵심 화면만 모았습니다.")

    for item in NAV_ITEMS:
        label = str(item["label"])
        if item["key"] == active:
            st.sidebar.markdown(f"**{label}**")
            st.sidebar.caption(str(item["caption"]))
        else:
            st.sidebar.markdown(f"[{label}]({item['url']})")
