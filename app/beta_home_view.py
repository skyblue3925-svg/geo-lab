"""Beta landing page for the deploy-ready Geo-Lab subset."""

from __future__ import annotations

import streamlit as st

from app.beta_navigation import NAV_ITEMS, resolve_page_path


def _page_target(fragment: str) -> str | None:
    return resolve_page_path(fragment)


def render_beta_home_page() -> None:
    st.markdown(
        """
<section style="padding: 1.5rem 0 1rem;">
  <p style="margin:0 0 .5rem;color:#2563eb;font-weight:700;letter-spacing:.04em;text-transform:uppercase;">
    Geo-Lab Beta
  </p>
  <h1 style="margin:0;font-size:2.35rem;line-height:1.12;">Animation Studio 중심 지형 학습 베타</h1>
  <p style="max-width:760px;margin:.85rem 0 0;color:#475569;font-size:1.05rem;line-height:1.7;">
    이번 배포판은 지형 형성 애니메이션, 고등학교 세계지리 수업 화면,
    쾨펜 기후 그래프만 노출합니다. 나머지 실험 페이지는 베타 기간 동안 잠금 처리했습니다.
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
            "body": "별도 프로젝트로 만들었던 쾨펜 기후 그래프 앱을 베타 안에 포함했습니다.",
            "fragment": "Climate.py",
            "cta": "쾨펜 기후 그래프 열기",
        },
    ]

    columns = st.columns(3)
    for column, card in zip(columns, cards):
        with column:
            st.markdown(f"### {card['title']}")
            st.write(card["body"])
            target = _page_target(card["fragment"])
            if target:
                st.page_link(target, label=card["cta"])

    st.markdown("---")
    st.caption("Locked beta pages")
    st.write("Gallery, Overview, Lab, Research, Case Mode, Higher Ed는 이번 배포판에서 숨김/잠금 상태로 둡니다.")
