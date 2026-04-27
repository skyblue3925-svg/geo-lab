"""Shared home page focused on high-school classroom use."""

from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
from typing import Dict

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parent.parent
STYLE_PATH = PROJECT_ROOT / "assets" / "style.css"
VISITOR_COUNT_PATH = PROJECT_ROOT / "visitor_count.json"
LEGACY_VISITOR_PATH = PROJECT_ROOT / "visitor_data.json"
PAGES_DIR = PROJECT_ROOT / "pages"

PRIMARY_DESTINATIONS = [
    {
        "badge": "Teacher Demo",
        "title": "교사용 시작",
        "summary": "수업용 예시 카탈로그에서 대표 지형을 고른 뒤 Lab 교사 흐름으로 바로 시연합니다.",
        "cta": "교사용 예시 열기",
        "page_fragment": "High_School_Geography.py",
    },
    {
        "badge": "Student Inquiry",
        "title": "학생 탐구 시작",
        "summary": "Lab student mode에서 부드러운 재생, 단계 캡션, 관찰 질문으로 변화 흐름을 읽습니다.",
        "cta": "학생용 Lab 열기",
        "page_fragment": "Lab.py",
    },
]

CLASSROOM_FLOW = [
    {
        "step": "01",
        "badge": "Warm-up",
        "title": "모범 사례 먼저 보기",
        "summary": "Gallery 카드에서 대표 지형을 고르고, 학생이 볼 핵심 장면을 먼저 정합니다.",
    },
    {
        "step": "02",
        "badge": "Explain",
        "title": "교사용 시연",
        "summary": "Lab teacher mode에서 프레임 고정 비교와 미리보기로 수업 설명의 기준 장면을 보여줍니다.",
    },
    {
        "step": "03",
        "badge": "Explore",
        "title": "학생 탐구",
        "summary": "Lab student mode에서 캡션과 질문을 따라가며 왜 지형이 달라지는지 해석하게 합니다.",
    },
]

CLASSROOM_BENEFITS = [
    {
        "title": "설명 없는 첫 진입",
        "summary": "처음 들어온 학생도 어디를 눌러야 하는지 바로 알 수 있게 메인 흐름을 좁혀 보여줍니다.",
    },
    {
        "title": "수업용 캡션 중심",
        "summary": "애니메이션보다 설명이 먼저 읽히도록 단계 캡션, 관찰 포인트, 질문을 같이 보여줍니다.",
    },
    {
        "title": "모범 사례에서 바로 시연",
        "summary": "Gallery에서 고른 예시를 그대로 Lab으로 넘겨 수업 준비 시간을 줄입니다.",
    },
]

PERSONAS = [
    {
        "title": "지리 교사",
        "description": "짧은 시간 안에 개념을 설명하고 비교 장면을 고정해 보여줘야 하는 사용자",
        "recommended": "Gallery → Lab teacher mode",
    },
    {
        "title": "고등학생",
        "description": "지형이 왜 바뀌는지, 어떤 과정이 우세한지 스스로 읽어야 하는 사용자",
        "recommended": "Lab student mode",
    },
    {
        "title": "동아리·탐구반",
        "description": "수업 활동 이후 비교 분석과 보고서형 정리가 필요한 심화 사용자",
        "recommended": "고등교육·연구 포털",
    },
]

ACADEMIC_GATEWAY = {
    "eyebrow": "Higher Ed / Research",
    "title": "대학·연구·교수 사용자는 별도 페이지에서 시작합니다",
    "summary": (
        "메인 홈은 고등학교 수업용 흐름에만 집중합니다. DEM 비교, 단면 분석, export는 "
        "별도 포털에서 문맥과 한계를 먼저 설명한 뒤 Research Lab으로 보냅니다."
    ),
    "cta": "고등교육·연구 포털 열기",
    "page_fragment": "Higher_Ed.py",
}


def load_css() -> None:
    try:
        st.markdown(f"<style>{STYLE_PATH.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass


def _read_local_visitor_count(today: str) -> Dict[str, int | str]:
    if VISITOR_COUNT_PATH.exists():
        try:
            payload = json.loads(VISITOR_COUNT_PATH.read_text(encoding="utf-8"))
            total = int(payload.get("total", 0))
            saved_date = str(payload.get("date", today))
            saved_today = int(payload.get("today", 0)) if saved_date == today else 0
            return {"total": total, "today": saved_today, "date": today}
        except Exception:
            pass

    if LEGACY_VISITOR_PATH.exists():
        try:
            payload = json.loads(LEGACY_VISITOR_PATH.read_text(encoding="utf-8"))
            total = int(payload.get("total", 0))
            daily = payload.get("daily", {})
            today_count = int(daily.get(today, 0))
            return {"total": total, "today": today_count, "date": today}
        except Exception:
            pass

    return {"total": 0, "today": 0, "date": today}


def _write_local_visitor_count(data: Dict[str, int | str]) -> None:
    VISITOR_COUNT_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def get_visitor_count() -> Dict[str, int]:
    today = datetime.now().strftime("%Y-%m-%d")

    try:
        if "supabase" in st.secrets:
            from supabase import create_client

            supabase = create_client(
                st.secrets["supabase"]["url"],
                st.secrets["supabase"]["key"],
            )

            if "visitor_counted" not in st.session_state:
                st.session_state["visitor_counted"] = True
                result = supabase.table("visitors").select("*").eq("date", today).execute()

                if result.data:
                    current_count = result.data[0]["count"]
                    supabase.table("visitors").update({"count": current_count + 1}).eq("date", today).execute()
                else:
                    supabase.table("visitors").insert({"date": today, "count": 1}).execute()

            today_result = supabase.table("visitors").select("count").eq("date", today).execute()
            today_count = today_result.data[0]["count"] if today_result.data else 0

            total_result = supabase.table("visitors").select("count").execute()
            total_count = sum(row["count"] for row in total_result.data)
            return {"today": today_count, "total": total_count}
    except Exception:
        pass

    try:
        data = _read_local_visitor_count(today)
        if "visitor_counted" not in st.session_state:
            st.session_state["visitor_counted"] = True
            data["total"] = int(data["total"]) + 1
            data["today"] = int(data["today"]) + 1
            data["date"] = today
            _write_local_visitor_count(data)
        return {"today": int(data["today"]), "total": int(data["total"])}
    except Exception:
        return {"today": 0, "total": 0}


def _resolve_page_path(fragment: str) -> str | None:
    page_path = next((path for path in PAGES_DIR.iterdir() if fragment in path.name), None)
    if page_path is None:
        return None
    return page_path.relative_to(PROJECT_ROOT).as_posix()


def _page_link(fragment: str, label: str) -> None:
    page_path = _resolve_page_path(fragment)
    if page_path and hasattr(st, "page_link"):
        st.page_link(page_path, label=label)


def _render_primary_card(card: dict[str, str]) -> None:
    st.markdown(
        f"""
<div class="classroom-primary-card">
  <div class="classroom-card-badge">{card["badge"]}</div>
  <div class="classroom-card-title">{card["title"]}</div>
  <div class="classroom-card-copy">{card["summary"]}</div>
</div>
""",
        unsafe_allow_html=True,
    )
    _page_link(card["page_fragment"], card["cta"])


def _render_flow_card(card: dict[str, str]) -> None:
    st.markdown(
        f"""
<div class="classroom-flow-card">
  <div class="classroom-flow-step">{card["step"]}</div>
  <div class="classroom-flow-badge">{card["badge"]}</div>
  <div class="classroom-flow-title">{card["title"]}</div>
  <div class="classroom-flow-copy">{card["summary"]}</div>
</div>
""",
        unsafe_allow_html=True,
    )


def _render_benefit_card(card: dict[str, str]) -> None:
    st.markdown(
        f"""
<div class="classroom-benefit-card">
  <div class="classroom-benefit-title">{card["title"]}</div>
  <div class="classroom-benefit-copy">{card["summary"]}</div>
</div>
""",
        unsafe_allow_html=True,
    )


def _render_persona_card(persona: dict[str, str]) -> None:
    st.markdown(
        f"""
<div class="classroom-persona-card">
  <div class="classroom-persona-title">{persona["title"]}</div>
  <div class="classroom-persona-copy">{persona["description"]}</div>
  <div class="classroom-persona-recommended">추천 시작점: {persona["recommended"]}</div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_home_page() -> None:
    load_css()
    visitor_data = get_visitor_count()

    st.markdown(
        """
<section class="classroom-hero">
  <div class="classroom-hero-eyebrow">Geo-Lab for High School</div>
  <h1 class="classroom-hero-title">고등학교 지형 수업을 바로 시작하는 메인 홈</h1>
  <p class="classroom-hero-copy">
    메인 홈은 교사 시연과 학생 탐구에만 집중합니다.
    모범 사례를 고르고, Lab에서 보여주고, 심화 분석은 별도 포털로 넘깁니다.
  </p>
</section>
""",
        unsafe_allow_html=True,
    )

    metric_col1, metric_col2, metric_col3 = st.columns(3)
    metric_col1.metric("메인 대상", "고등학교 수업", "교사 시연 + 학생 탐구")
    metric_col2.metric("권장 수업 흐름", "3단계", "Gallery → Lab → 정리")
    metric_col3.metric("오늘 방문", f"{visitor_data['today']}")

    st.markdown("### 수업용 바로 시작")
    primary_cols = st.columns(len(PRIMARY_DESTINATIONS))
    for column, card in zip(primary_cols, PRIMARY_DESTINATIONS):
        with column:
            _render_primary_card(card)

    st.markdown("### 한 차시 운영 흐름")
    flow_cols = st.columns(len(CLASSROOM_FLOW))
    for column, card in zip(flow_cols, CLASSROOM_FLOW):
        with column:
            _render_flow_card(card)

    st.markdown("### 왜 현장에서 바로 쓰기 쉬운가")
    benefit_cols = st.columns(len(CLASSROOM_BENEFITS))
    for column, card in zip(benefit_cols, CLASSROOM_BENEFITS):
        with column:
            _render_benefit_card(card)

    st.markdown("### 메인 홈이 우선하는 사용자")
    persona_cols = st.columns(len(PERSONAS))
    for column, persona in zip(persona_cols, PERSONAS):
        with column:
            _render_persona_card(persona)

    st.markdown(
        f"""
<section class="academic-gateway-card">
  <div class="academic-gateway-eyebrow">{ACADEMIC_GATEWAY["eyebrow"]}</div>
  <div class="academic-gateway-title">{ACADEMIC_GATEWAY["title"]}</div>
  <div class="academic-gateway-copy">{ACADEMIC_GATEWAY["summary"]}</div>
</section>
""",
        unsafe_allow_html=True,
    )
    _page_link(ACADEMIC_GATEWAY["page_fragment"], ACADEMIC_GATEWAY["cta"])

    st.sidebar.markdown(
        """
<div style='text-align: center; padding: 1rem 0;'>
  <span style='font-size: 2rem;'>Geo</span>
  <h2 style='font-size: 1.2rem; font-weight: 700; margin: 0.5rem 0 0 0;'>Geo-Lab AI</h2>
  <p style='color: #a3a3a3; font-size: 0.82rem; margin: 0.35rem 0 0 0;'>high-school classroom first</p>
</div>
""",
        unsafe_allow_html=True,
    )
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 홈의 기준")
    st.sidebar.caption("메인은 고등학교 수업용, 연구 기능은 별도 포털에서 시작")
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 방문 통계")
    side_col1, side_col2 = st.sidebar.columns(2)
    side_col1.metric("오늘", f"{visitor_data['today']}")
    side_col2.metric("누적", f"{visitor_data['total']}")
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 빠른 링크")
    _page_link("Gallery.py", "교사용 Gallery")
    _page_link("Lab.py", "학생·교사용 Lab")
    _page_link("Overview.py", "수업 운영 안내")
    _page_link("Higher_Ed.py", "고등교육·연구 포털")
