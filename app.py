"""Active Streamlit entrypoint for the Geo-Lab multipage app."""

import streamlit as st

from app.beta_home_view import render_beta_home_page
from app.beta_navigation import render_beta_sidebar


st.set_page_config(
    page_title="지오랩",
    layout="wide",
    initial_sidebar_state="expanded",
)

render_beta_sidebar("home")
render_beta_home_page()
