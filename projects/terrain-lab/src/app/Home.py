"""Legacy alternate entrypoint that reuses the active home page view."""

import streamlit as st

from app.home_view import render_home_page


st.set_page_config(
    page_title="🌍 Geo-Lab AI",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

render_home_page()
