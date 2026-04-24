from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.koppen_climate_view import render_koppen_climate_page


st.set_page_config(
    page_title="쾨펜 기후 그래프",
    page_icon="☁️",
    layout="wide",
)

render_koppen_climate_page()
