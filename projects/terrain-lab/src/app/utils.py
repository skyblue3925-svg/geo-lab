"""
공통 유틸리티 및 CSS 로더
"""
import streamlit as st
import os

def load_css():
    """Ultimate Hybrid CSS 로드"""
    # 상위 디렉토리에서 assets/style.css 찾기
    current_dir = os.path.dirname(os.path.abspath(__file__))
    possible_paths = [
        os.path.join(current_dir, "..", "assets", "style.css"),
        os.path.join(current_dir, "..", "..", "assets", "style.css"),
        "assets/style.css",
    ]
    
    for css_path in possible_paths:
        if os.path.exists(css_path):
            try:
                with open(css_path, 'r', encoding='utf-8') as f:
                    css = f.read()
                st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)
                return True
            except:
                pass
    return False
