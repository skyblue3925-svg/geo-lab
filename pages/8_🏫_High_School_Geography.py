from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.beta_navigation import render_beta_sidebar
from app.high_school_geography_view import render_high_school_geography_page


st.set_page_config(
    page_title="지오랩 고등학교 세계지리 지형 아틀라스",
    page_icon="🏫",
    layout="wide",
)

render_beta_sidebar("high_school")
render_high_school_geography_page()
