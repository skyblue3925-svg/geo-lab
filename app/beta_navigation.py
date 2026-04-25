"""Shared navigation helpers for the deploy-focused Streamlit shell."""

from __future__ import annotations

from pathlib import Path

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STYLE_PATH = PROJECT_ROOT / "assets" / "style.css"
KOPPEN_CLIMATE_URL = "https://koppen-climate-lab.pages.dev/"
CREATOR_LABEL = "제작자 : 한백고등학교 김한솔"

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
        "key": "gif_gallery",
        "label": "GIF 갤러리",
        "url": "/GIF_Gallery",
        "caption": "지형 형성 GIF 모아보기",
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


def apply_sidebar_override() -> None:
    """Keep the Streamlit sidebar compact and remove native fade gradients."""

    st.markdown(
        """
        <style>
          :root {
            --geo-sidebar-width: 260px;
          }

          section[data-testid="stSidebar"],
          section[data-testid="stSidebar"][aria-expanded="true"] {
            width: var(--geo-sidebar-width) !important;
            min-width: var(--geo-sidebar-width) !important;
            max-width: var(--geo-sidebar-width) !important;
            background: #0a0a0a !important;
            background-color: #0a0a0a !important;
            background-image: none !important;
            box-shadow: none !important;
          }

          section[data-testid="stSidebar"] > div,
          section[data-testid="stSidebar"] [data-testid="stSidebarContent"],
          section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
            width: var(--geo-sidebar-width) !important;
            min-width: var(--geo-sidebar-width) !important;
            max-width: var(--geo-sidebar-width) !important;
            background: #0a0a0a !important;
            background-color: #0a0a0a !important;
            background-image: none !important;
            box-shadow: none !important;
          }

          section[data-testid="stSidebar"] *,
          section[data-testid="stSidebar"] *::before,
          section[data-testid="stSidebar"] *::after {
            background-image: none !important;
            -webkit-mask-image: none !important;
            mask-image: none !important;
            box-shadow: none !important;
          }

          section[data-testid="stSidebar"]::before,
          section[data-testid="stSidebar"]::after,
          section[data-testid="stSidebar"] [data-testid="stSidebarContent"]::before,
          section[data-testid="stSidebar"] [data-testid="stSidebarContent"]::after,
          section[data-testid="stSidebar"] [data-testid="stSidebarNav"]::before,
          section[data-testid="stSidebar"] [data-testid="stSidebarNav"]::after {
            content: none !important;
            display: none !important;
            background: transparent !important;
            background-image: none !important;
            -webkit-mask-image: none !important;
            mask-image: none !important;
          }

          section[data-testid="stSidebar"] [data-testid="stSidebarNav"] {
            background: #0a0a0a !important;
            background-color: #0a0a0a !important;
            background-image: none !important;
          }

          section[data-testid="stSidebar"] [data-testid="stSidebarNav"],
          section[data-testid="stSidebar"] [data-testid="stSidebarNav"] nav,
          section[data-testid="stSidebar"] [data-testid="stSidebarNav"] ul,
          section[data-testid="stSidebar"] [data-testid="stSidebarNav"] li,
          section[data-testid="stSidebar"] [data-testid="stSidebarHeader"],
          section[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] {
            background: transparent !important;
            background-color: transparent !important;
            background-image: none !important;
            -webkit-mask-image: none !important;
            mask-image: none !important;
            box-shadow: none !important;
          }

          section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a {
            background: transparent !important;
            background-color: transparent !important;
            background-image: none !important;
            border-radius: 7px !important;
          }

          section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a:hover,
          section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"],
          section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-selected="true"] {
            background: #262626 !important;
            background-color: #262626 !important;
            background-image: none !important;
          }

          section[data-testid="stSidebar"] [data-testid="stSidebarNav"] li:has(a[aria-current="page"]),
          section[data-testid="stSidebar"] [data-testid="stSidebarNav"] div:has(> a[aria-current="page"]),
          section[data-testid="stSidebar"] [data-testid="stSidebarNav"] div:has(> a[aria-selected="true"]) {
            background: #262626 !important;
            background-color: #262626 !important;
            background-image: none !important;
          }

          section[data-testid="stSidebar"] div[style*="gradient"],
          section[data-testid="stSidebar"] div[style*="linear-gradient"],
          section[data-testid="stSidebar"] div[style*="radial-gradient"] {
            background: transparent !important;
            background-color: transparent !important;
            background-image: none !important;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_creator_banner() -> None:
    """Show the project author line at the top of public beta pages."""

    st.markdown(
        f"""
        <div class="geo-creator-banner">
          {CREATOR_LABEL}
        </div>
        <style>
          .geo-creator-banner {{
            margin: 0 0 0.75rem 0;
            padding: 0.45rem 0 0.2rem 0;
            color: #525252;
            font-size: 0.92rem;
            font-weight: 600;
            letter-spacing: 0;
          }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_beta_sidebar(active: str) -> None:
    """Append beta shortcuts while keeping the native local-style sidebar."""

    load_project_style()
    apply_sidebar_override()
    render_creator_banner()

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
