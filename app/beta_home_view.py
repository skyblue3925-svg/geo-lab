"""Beta landing page for the deploy-ready Geo-Lab subset."""

from __future__ import annotations

import streamlit as st


PAGE_URLS = {
    "Animation_Studio.py": "/Animation_Studio",
    "High_School_Geography.py": "/High_School_Geography",
    "Climate.py": "https://koppen-climate-lab.pages.dev/",
}


def render_beta_home_page() -> None:
    st.markdown(
        """
<section style="padding: 1.5rem 0 1rem;">
  <p style="margin:0 0 .5rem;color:#2563eb;font-weight:700;letter-spacing:.04em;text-transform:uppercase;">
    Geo-Lab Beta
  </p>
  <h1 style="margin:0;font-size:2.35rem;line-height:1.12;">Animation Studio 중심 지형 학습 베타</h1>
  <p style="max-width:760px;margin:.85rem 0 0;color:#475569;font-size:1.05rem;line-height:1.7;">
    이번 배포에서는 지형 형성 애니메이션, 고등학교 세계지리 수업 화면,
    기존 쾨펜 기후 그래프 링크만 노출합니다.
  </p>
</section>
""",
        unsafe_allow_html=True,
    )

    cards = [
        {
            "title": "Animation Studio",
            "body": "38개 지형의 이미지 시퀀스, 원본 스토리보드, Three.js 실험 뷰어를 확인합니다.",
            "fragment": "Animation_Studio.py",
            "cta": "Animation Studio 열기",
        },
        {
            "title": "High School Geography",
            "body": "고등학교 세계지리 수업용 지형 형성과 과정 중심 탐구 화면입니다.",
            "fragment": "High_School_Geography.py",
            "cta": "수업 화면 열기",
        },
        {
            "title": "Köppen Climate Graph",
            "body": "별도 프로젝트로 만들었던 기존 쾨펜 기후 그래프 앱으로 연결합니다.",
            "fragment": "Climate.py",
            "cta": "쾨펜 기후 그래프 열기",
        },
    ]

    columns = st.columns(3)
    for column, card in zip(columns, cards):
        with column:
            st.markdown(f"### {card['title']}")
            st.write(card["body"])
            target = PAGE_URLS.get(card["fragment"])
            if target:
                st.markdown(f"[{card['cta']}]({target})")

    st.markdown("---")
    st.caption("Beta navigation")
    st.write("사이드바에는 Animation Studio, High School Geography, Köppen Climate Graph만 노출합니다.")
