"""Shared beta navigation for the deploy-focused Streamlit shell."""

from __future__ import annotations

from pathlib import Path

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PAGES_DIR = PROJECT_ROOT / "pages"


NAV_ITEMS = [
    {
        "key": "home",
        "label": "Beta Home",
        "target": "app.py",
        "caption": "Animation Studio 중심 베타",
    },
    {
        "key": "animation",
        "label": "Animation Studio",
        "fragment": "Animation_Studio.py",
        "caption": "지형 형성 이미지 시퀀스",
    },
    {
        "key": "high_school",
        "label": "High School Geography",
        "fragment": "High_School_Geography.py",
        "caption": "고등학교 세계지리 수업",
    },
    {
        "key": "koppen",
        "label": "Köppen Climate Graph",
        "fragment": "Climate.py",
        "caption": "쾨펜 기후 그래프 앱",
    },
]

LOCKED_ITEMS = [
    "Gallery",
    "Overview",
    "Lab",
    "Research",
    "Case Mode",
    "Higher Ed",
]


def resolve_page_path(fragment: str) -> str | None:
    page_path = next((path for path in PAGES_DIR.iterdir() if fragment in path.name), None)
    if page_path is None:
        return None
    return page_path.relative_to(PROJECT_ROOT).as_posix()


def render_beta_sidebar(active: str) -> None:
    """Render the restricted beta navigation used for deploy preview."""

    st.sidebar.markdown("### Geo-Lab Beta")
    st.sidebar.caption("Animation Studio 중심 공개 베타")

    for item in NAV_ITEMS:
        target = item.get("target")
        fragment = item.get("fragment")
        if fragment:
            target = resolve_page_path(str(fragment))

        if not target:
            continue

        label = str(item["label"])
        if item["key"] == active:
            st.sidebar.markdown(f"**{label}**")
            st.sidebar.caption(str(item["caption"]))
        else:
            st.sidebar.page_link(target, label=label)

    st.sidebar.markdown("---")
    st.sidebar.caption("Locked in this beta")
    for label in LOCKED_ITEMS:
        st.sidebar.markdown(f"- {label} - locked")
