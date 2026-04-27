"""Home page for the deploy-ready Geo-Lab subset."""

from __future__ import annotations

import streamlit as st


PAGE_URLS = {
    "animation": "/Animation_Studio",
    "high_school": "/High_School_Geography",
    "koppen": "https://koppen-climate-lab.pages.dev/",
}


def _render_destination(title: str, body: str, url: str, cta: str) -> None:
    st.markdown(
        f"""
<div class="classroom-primary-card">
  <div class="classroom-card-title">{title}</div>
  <div class="classroom-card-copy">{body}</div>
</div>
""",
        unsafe_allow_html=True,
    )
    st.markdown(f"[{cta}]({url})")


def render_beta_home_page() -> None:
    st.markdown(
        """
<section class="classroom-hero">
  <div class="classroom-hero-eyebrow">Geo-Lab Beta</div>
  <h1 class="classroom-hero-title">지형 형성 수업을 바로 시작하는 지오랩</h1>
  <p class="classroom-hero-copy">
    기존 로컬 화면의 사용 흐름을 유지하면서, 배포판에서는 애니메이션 스튜디오,
    고등학교 세계지리 수업 화면, 쾨펜 기후 그래프 링크를 먼저 열 수 있게 정리했습니다.
  </p>
</section>
""",
        unsafe_allow_html=True,
    )

    st.markdown("### 바로 열기")
    columns = st.columns(3)
    with columns[0]:
        _render_destination(
            "애니메이션 스튜디오",
            "지형별 이미지 시퀀스, 프롬프트, 단계별 텍스처를 확인합니다.",
            PAGE_URLS["animation"],
            "애니메이션 스튜디오 열기",
        )
    with columns[1]:
        _render_destination(
            "고등학교 세계지리",
            "세계지리 수업용 대표 지형과 표준 시점, 수업 카드를 확인합니다.",
            PAGE_URLS["high_school"],
            "고등학교 세계지리 열기",
        )
    with columns[2]:
        _render_destination(
            "쾨펜 기후 그래프",
            "기존 별도 프로젝트로 만든 쾨펜 기후 그래프 앱을 새 탭에서 엽니다.",
            PAGE_URLS["koppen"],
            "쾨펜 기후 그래프 열기",
        )
