"""Dedicated portal for university, professor, and research users."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from app.utils.world_terrain_cases import get_featured_world_cases


PROJECT_ROOT = Path(__file__).resolve().parent.parent
STYLE_PATH = PROJECT_ROOT / "assets" / "style.css"
PAGES_DIR = PROJECT_ROOT / "pages"

ACADEMIC_AUDIENCES = [
    {
        "title": "대학 강의",
        "summary": "지형 형성 과정, 단면 해석, DEM 비교를 교양·전공 수업 흐름에 맞춰 바로 연결합니다.",
    },
    {
        "title": "교수·연구실",
        "summary": "기준 DEM 비교, 요약 지표, export 결과를 연구 메모와 수업 자료에 함께 활용할 수 있습니다.",
    },
    {
        "title": "대학원·세미나",
        "summary": "실제 사례와 과정 모델을 나란히 두고 토론·발표·과제 설계까지 이어가기 좋습니다.",
    },
]

ACADEMIC_SECTIONS = [
    {
        "title": "Research Lab",
        "summary": "기준 DEM 업로드, 단면 비교, HI 차이, comparison export까지 한 흐름으로 이어집니다.",
        "cta": "Research Lab 열기",
        "page_fragment": "Research.py",
    },
    {
        "title": "세계 지형 사례 Atlas",
        "summary": "대표 지역을 세계 지도와 함께 보며 Gallery preset과 Lab 수업 흐름으로 바로 넘길 수 있습니다.",
        "cta": "Gallery Atlas 열기",
        "page_fragment": "Gallery.py",
    },
    {
        "title": "케이스 모드",
        "summary": "실제 지역 사례를 바탕으로 질문, 비교, 탐구 활동을 설계하는 별도 페이지입니다.",
        "cta": "케이스 모드 열기",
        "page_fragment": "케이스_모드.py",
    },
]

ACADEMIC_RULES = [
    "메인 홈은 고등학교 수업 진입을 우선하고, 이 페이지는 대학·연구용 확장 흐름만 모아둡니다.",
    "Gallery의 세계 사례 Atlas는 실제 지역과 과정 모델을 연결하는 브리지 역할을 합니다.",
    "Research 결과는 shape 기준 보간 비교라는 한계를 함께 설명하고 해석에 주의하도록 안내합니다.",
]


def load_css() -> None:
    try:
        st.markdown(f"<style>{STYLE_PATH.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass


def _resolve_page_path(fragment: str) -> str | None:
    page_path = next((path for path in PAGES_DIR.iterdir() if fragment in path.name), None)
    if page_path is None:
        return None
    return page_path.relative_to(PROJECT_ROOT).as_posix()


def _page_link(fragment: str, label: str) -> None:
    page_path = _resolve_page_path(fragment)
    if page_path and hasattr(st, "page_link"):
        st.page_link(page_path, label=label, width="stretch")


st.set_page_config(page_title="🎓 Higher Ed & Research", page_icon="🎓", layout="wide")
load_css()

st.markdown(
    """
<section class="academic-portal-hero">
  <div class="academic-portal-eyebrow">Higher Ed / Research Portal</div>
  <h1 class="academic-portal-title">대학·연구 사용자는 이 페이지에서 시작합니다.</h1>
  <p class="academic-portal-copy">
    메인 홈이 고등학교 수업 흐름에 맞춰 정리되어 있다면,
    여기서는 연구 비교, 세계 사례, 케이스 기반 탐구처럼 더 깊은 분석과 해석에 필요한 진입점을 모아 둡니다.
  </p>
</section>
""",
    unsafe_allow_html=True,
)

st.markdown("### 누구를 위한 포털인가요?")
audience_cols = st.columns(len(ACADEMIC_AUDIENCES))
for column, card in zip(audience_cols, ACADEMIC_AUDIENCES):
    with column:
        st.markdown(
            f"""
<div class="academic-portal-card">
  <div class="academic-portal-card-title">{card["title"]}</div>
  <div class="academic-portal-card-copy">{card["summary"]}</div>
</div>
""",
            unsafe_allow_html=True,
        )

st.markdown("### 바로 이동")
section_cols = st.columns(len(ACADEMIC_SECTIONS))
for column, card in zip(section_cols, ACADEMIC_SECTIONS):
    with column:
        st.markdown(
            f"""
<div class="academic-portal-card">
  <div class="academic-portal-card-title">{card["title"]}</div>
  <div class="academic-portal-card-copy">{card["summary"]}</div>
</div>
""",
            unsafe_allow_html=True,
        )
        _page_link(card["page_fragment"], card["cta"])

st.markdown("### 대표 세계 사례")
st.caption("세계 사례는 과정 중심 지형 모델을 실제 지역에 연결해 주는 브리지입니다. 자세한 지도와 preset 연결은 Gallery Atlas에서 제공합니다.")
case_cols = st.columns(2)
for idx, world_case in enumerate(get_featured_world_cases(limit=4)):
    with case_cols[idx % len(case_cols)]:
        st.markdown(
            f"""
<div class="academic-portal-card">
  <div class="academic-portal-card-title">{world_case["title"]}</div>
  <div class="academic-portal-card-copy">{world_case["location_label"]}</div>
  <div class="academic-portal-card-copy">{world_case["classroom_hook"]}</div>
  <div class="academic-portal-card-copy">{world_case["higher_ed_focus"]}</div>
</div>
""",
            unsafe_allow_html=True,
        )

st.markdown("### 운영 원칙")
for item in ACADEMIC_RULES:
    st.markdown(f"- {item}")

st.info("고등학교 수업은 Home, Gallery, Lab에서 바로 시작하고, 대학·연구 사용자는 이 포털을 통해 Research, Atlas, 케이스 모드로 들어가는 구조를 권장합니다.")
