"""Overview page focused on classroom routing."""

from __future__ import annotations

from pathlib import Path

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parent.parent
STYLE_PATH = PROJECT_ROOT / "assets" / "style.css"
PAGES_DIR = PROJECT_ROOT / "pages"

CLASSROOM_ROUTES = [
    {
        "title": "10분 시연",
        "summary": "Gallery에서 모범 사례를 고르고 Lab teacher mode에서 프레임 고정 비교로 핵심 장면을 보여줍니다.",
        "next": "교과서 개념 도입용",
        "page_fragment": "High_School_Geography.py",
        "cta": "수업 페이지로 시작",
    },
    {
        "title": "20분 탐구",
        "summary": "Lab student mode에서 부드러운 재생과 단계 캡션을 따라가며 학생이 스스로 변화를 읽게 합니다.",
        "next": "질문 중심 탐구용",
        "page_fragment": "Lab.py",
        "cta": "Lab으로 시작",
    },
    {
        "title": "심화·후속 활동",
        "summary": "메인 수업 흐름은 끝내고, 필요할 때만 고등교육·연구 포털로 넘어가 비교와 export를 이어갑니다.",
        "next": "연구·교수용 별도 진입",
        "page_fragment": "Higher_Ed.py",
        "cta": "별도 포털 열기",
    },
]

CLASSROOM_BLOCKS = [
    {
        "title": "교사 중심",
        "summary": "모범 사례 고르기, 비교 장면 고정, 설명 포인트 정리",
    },
    {
        "title": "학생 중심",
        "summary": "단계 캡션, 관찰 질문, 부드러운 재생으로 변화 흐름 읽기",
    },
    {
        "title": "수업 후 확장",
        "summary": "심화 탐구나 비교 분석이 필요할 때만 별도 포털에서 시작",
    },
]

LANDSCAPE_GROUPS = [
    {
        "title": "산지·하천",
        "summary": "V자곡, 곡류 하천, 선상지, 삼각주",
        "use_case": "침식과 퇴적의 균형 설명",
    },
    {
        "title": "빙하·해안",
        "summary": "U자곡, 피오르, 해식애, 해안 사구",
        "use_case": "작용 주체에 따라 단면이 달라지는 이유 설명",
    },
    {
        "title": "건조·특수",
        "summary": "바르한, 메사, 카르스트, 화산",
        "use_case": "바람·용해·분출 같은 다른 과정 비교",
    },
]

ACADEMIC_NOTE = {
    "title": "연구 사용자를 메인 홈과 분리하는 이유",
    "summary": (
        "고등학교 현장에서는 버튼 수와 선택지가 적을수록 수업 준비가 쉬워집니다. "
        "반대로 DEM 비교와 export는 데이터 전제와 해석 주의가 필요하므로 별도 포털에서 시작하는 편이 안전합니다."
    ),
    "cta": "고등교육·연구 포털로 이동",
    "page_fragment": "Higher_Ed.py",
}


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
        st.page_link(page_path, label=label)


st.set_page_config(layout="wide")
load_css()

st.markdown(
    """
<section class="overview-banner">
  <div class="overview-banner-eyebrow">Classroom Guide</div>
  <h1 class="overview-banner-title">메인 흐름은 고등학교 수업용으로만 정리합니다</h1>
  <p class="overview-banner-copy">
    이 페이지는 수업 상황별로 어디서 시작하는 게 가장 빠른지 안내합니다.
    연구용 기능은 같은 레벨의 CTA가 아니라 별도 포털로 보냅니다.
  </p>
</section>
""",
    unsafe_allow_html=True,
)

st.markdown("### 수업 상황별 추천 시작점")
route_cols = st.columns(len(CLASSROOM_ROUTES))
for column, route in zip(route_cols, CLASSROOM_ROUTES):
    with column:
        st.markdown(
            f"""
<div class="overview-route-card">
  <div class="overview-route-title">{route["title"]}</div>
  <div class="overview-route-copy">{route["summary"]}</div>
  <div class="overview-route-next">{route["next"]}</div>
</div>
""",
            unsafe_allow_html=True,
        )
        _page_link(route["page_fragment"], route["cta"])

st.markdown("### 메인 홈이 우선하는 사용자")
flow_cols = st.columns(len(CLASSROOM_BLOCKS))
for column, block in zip(flow_cols, CLASSROOM_BLOCKS):
    with column:
        st.markdown(
            f"""
<div class="overview-flow-card">
  <div class="overview-flow-title">{block["title"]}</div>
  <div class="overview-flow-copy">{block["summary"]}</div>
</div>
""",
            unsafe_allow_html=True,
        )

st.markdown("### 수업에서 자주 쓰는 지형 묶음")
category_cols = st.columns(len(LANDSCAPE_GROUPS))
for column, card in zip(category_cols, LANDSCAPE_GROUPS):
    with column:
        st.markdown(
            f"""
<div class="overview-category-card">
  <div class="overview-category-title">{card["title"]}</div>
  <div class="overview-category-copy">{card["summary"]}</div>
  <div class="overview-category-use">{card["use_case"]}</div>
</div>
""",
            unsafe_allow_html=True,
        )

st.markdown(
    f"""
<section class="academic-gateway-card">
  <div class="academic-gateway-eyebrow">Separate Portal</div>
  <div class="academic-gateway-title">{ACADEMIC_NOTE["title"]}</div>
  <div class="academic-gateway-copy">{ACADEMIC_NOTE["summary"]}</div>
</section>
""",
    unsafe_allow_html=True,
)
_page_link(ACADEMIC_NOTE["page_fragment"], ACADEMIC_NOTE["cta"])

st.info("권장 흐름: Gallery에서 예시 선택 → Lab teacher/student mode로 수업 진행 → 필요할 때만 고등교육·연구 포털로 이동")
