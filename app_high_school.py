from __future__ import annotations

from app.high_school_geography_view import render_high_school_geography_page

import streamlit as st


st.set_page_config(
    page_title="Geo-Lab 고등학교 세계지리 지형 아틀라스",
    page_icon="🏫",
    layout="wide",
)

render_high_school_geography_page()
