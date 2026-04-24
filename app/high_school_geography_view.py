from __future__ import annotations

import inspect
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from app.components.renderer import render_terrain_plotly
from app.utils.gallery_showcase import (
    build_lab_showcase_preset,
    get_gallery_showcase_preset,
    queue_gallery_showcase_preset,
)
from app.utils.high_school_world_geography import (
    build_high_school_process_fields,
    get_high_school_world_group,
    get_high_school_world_groups,
    get_high_school_world_topic,
    get_high_school_world_topics,
)
from engine.ideal_landforms import IDEAL_LANDFORM_GENERATORS


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PAGES_DIR = PROJECT_ROOT / "pages"

GROUP_LABELS = {
    "river": "하천 | 하천 침식과 퇴적 지형",
    "delta": "하구 | 하구·삼각주 지형",
    "glacial": "빙하 | 빙하와 고산 지형",
    "volcanic": "화산 | 화산과 분출 지형",
    "karst": "카르스트 | 용식 지형",
    "arid": "건조 | 건조 지형",
    "coastal": "해안 | 해안 침식과 퇴적 지형",
}

HIGH_SCHOOL_CAMERA_OVERRIDES = {
    "alluvial_fan": {"camera_profile": "fan_textbook", "recommended_view": "선상지 정면 평면도"},
    "delta": {"camera_profile": "delta_textbook", "recommended_view": "삼각주 정면 평면도"},
    "bird_foot_delta": {"camera_profile": "delta_textbook", "recommended_view": "삼각주 정면 평면도"},
    "arcuate_delta": {"camera_profile": "delta_textbook", "recommended_view": "삼각주 정면 평면도"},
    "cuspate_delta": {"camera_profile": "delta_textbook", "recommended_view": "삼각주 정면 평면도"},
    "fjord": {"camera_profile": "fjord_textbook", "recommended_view": "피오르 해안 정면뷰"},
    "coastal_cliff": {"camera_profile": "cliff_textbook", "recommended_view": "해식애 해안 정면뷰"},
}

OVERLAY_LABELS = {
    "erosion": "침식",
    "deposition": "퇴적",
    "transport": "이동",
    "tectonic": "구조 작용",
    "change": "지형 변화",
}


def load_css() -> None:
    css_path = PROJECT_ROOT / "assets" / "style.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def resolve_page_path(fragment: str) -> str | None:
    page_path = next((path for path in PAGES_DIR.iterdir() if fragment in path.name), None)
    if page_path is None:
        return None
    return page_path.relative_to(PROJECT_ROOT).as_posix()


def generate_landform(key: str, grid_size: int, stage: float = 1.0) -> np.ndarray:
    func = IDEAL_LANDFORM_GENERATORS[key]
    params = inspect.signature(func).parameters
    result = func(grid_size, stage) if "stage" in params else func(grid_size)
    if isinstance(result, tuple):
        return np.array(result[0], dtype=float)
    return np.array(result, dtype=float)


def build_group_case_map(topics: list[dict[str, object]], active_topic_id: str) -> go.Figure:
    inactive = [topic for topic in topics if topic["topic_id"] != active_topic_id]
    active = [topic for topic in topics if topic["topic_id"] == active_topic_id]
    fig = go.Figure()
    for items, color, size in ((inactive, "#94a3b8", 10), (active, "#f97316", 16)):
        if not items:
            continue
        fig.add_trace(
            go.Scattergeo(
                lon=[topic["world_case"]["longitude"] for topic in items],
                lat=[topic["world_case"]["latitude"] for topic in items],
                text=[topic["title"] for topic in items],
                customdata=[[topic["world_case"]["location_label"]] for topic in items],
                mode="markers+text",
                textposition="top center",
                marker=dict(size=size, color=color, line=dict(color="#334155", width=1)),
                hovertemplate="<b>%{text}</b><br>%{customdata[0]}<extra></extra>",
            )
        )
    fig.update_geos(
        projection_type="natural earth",
        showland=True,
        landcolor="#f8fafc",
        showocean=True,
        oceancolor="#dbeafe",
        showcountries=True,
        countrycolor="#cbd5e1",
        coastlinecolor="#94a3b8",
        showframe=False,
        bgcolor="rgba(0,0,0,0)",
    )
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=290, paper_bgcolor="rgba(0,0,0,0)")
    return fig


def resolve_high_school_camera_spec(topic: dict[str, object]) -> tuple[str, str]:
    topic_id = str(topic.get("topic_id", ""))
    override = HIGH_SCHOOL_CAMERA_OVERRIDES.get(topic_id)
    if override is not None:
        return override["camera_profile"], override["recommended_view"]
    return str(topic["camera_profile"]), str(topic["recommended_view"])


def tune_standard_view_figure(fig: go.Figure | None) -> go.Figure | None:
    """Keep the classroom 3D preview compact and reliably framed."""

    if fig is None:
        return None

    fig.update_layout(
        autosize=True,
        height=520,
        margin=dict(l=0, r=0, t=42, b=0),
    )
    fig.update_layout(scene=dict(domain=dict(x=[0.0, 1.0], y=[0.0, 1.0])))

    for trace in fig.data:
        if getattr(trace, "type", "") != "surface":
            continue
        if getattr(trace, "showscale", None) is False:
            continue
        trace.update(colorbar=dict(thickness=18, len=0.72, x=0.98))

    return fig


def format_group_label(group: dict[str, object]) -> str:
    group_id = str(group["group_id"])
    return GROUP_LABELS.get(group_id, f'{group.get("badge", "")} | {group.get("title", "")}'.strip())


def route_to_lab(category: str, landform_key: str, user_mode: str) -> None:
    preset = build_lab_showcase_preset(category, landform_key)
    if preset is None:
        st.warning("이 지형은 아직 Lab 직접 시연 preset이 없습니다. 먼저 Gallery에서 자세히 보기를 이용해 주세요.")
        return
    preset["user_mode"] = user_mode
    st.session_state["gallery_lab_preset"] = preset
    lab_page = resolve_page_path("Lab.py")
    if lab_page and hasattr(st, "switch_page"):
        st.switch_page(lab_page)


def open_gallery(category: str, landform_key: str) -> None:
    preset = get_gallery_showcase_preset(category, landform_key)
    if preset is not None:
        queue_gallery_showcase_preset(st.session_state, preset)
    gallery_page = resolve_page_path("Gallery.py")
    if gallery_page and hasattr(st, "switch_page"):
        st.switch_page(gallery_page)


def render_high_school_geography_page() -> None:
    load_css()

    groups = get_high_school_world_groups()
    group_ids = [str(group["group_id"]) for group in groups]
    selected_group_id = str(st.session_state.get("hs_world_geo_group", group_ids[0]))
    if selected_group_id not in group_ids:
        selected_group_id = group_ids[0]

    group = get_high_school_world_group(selected_group_id) or groups[0]
    group_topics = get_high_school_world_topics(selected_group_id)
    topic_ids = [str(topic["topic_id"]) for topic in group_topics]
    default_topic_id = str(group["default_topic_id"]) if str(group["default_topic_id"]) in topic_ids else topic_ids[0]
    selected_topic_id = str(st.session_state.get("hs_world_geo_topic", default_topic_id))
    if selected_topic_id not in topic_ids:
        selected_topic_id = default_topic_id

    selected_topic = get_high_school_world_topic(selected_topic_id)
    if selected_topic is None:
        st.error("선택한 지형 정보를 불러오지 못했습니다.")
        st.stop()

    camera_profile, recommended_view = resolve_high_school_camera_spec(selected_topic)
    world_case = selected_topic["world_case"]
    category = str(selected_topic["category"])
    landform_key = str(selected_topic["landform_key"])
    gallery_preset = get_gallery_showcase_preset(category, landform_key) or {}
    preview = generate_landform(
        landform_key,
        int(gallery_preset.get("grid_size", 72)),
        float(selected_topic.get("preview_stage", 0.92)),
    )
    process_fields = build_high_school_process_fields(selected_topic_id, preview)
    lab_preset = build_lab_showcase_preset(category, landform_key)

    st.title("고등학교 세계지리 지형 형성 아틀라스")
    st.caption(
        "세계지리에서 자주 다루는 지형을 단원별로 정리하고, 대표 지역과 형성 과정을 교과서식 시점으로 읽는 페이지입니다."
    )

    st.markdown("### 1. 단원 선택")
    new_group_id = st.radio(
        "단원",
        group_ids,
        index=group_ids.index(selected_group_id),
        format_func=lambda gid: format_group_label(get_high_school_world_group(gid) or {"group_id": gid}),
        horizontal=True,
    )
    if new_group_id != selected_group_id:
        st.session_state["hs_world_geo_group"] = new_group_id
        next_group = get_high_school_world_group(new_group_id)
        if next_group is not None:
            st.session_state["hs_world_geo_topic"] = str(next_group["default_topic_id"])
        st.rerun()

    st.markdown("### 2. 지형 선택")
    new_topic_id = st.selectbox(
        "대표 지형",
        topic_ids,
        index=topic_ids.index(selected_topic_id),
        format_func=lambda tid: str(get_high_school_world_topic(tid)["title"]),
    )
    if new_topic_id != selected_topic_id:
        st.session_state["hs_world_geo_topic"] = new_topic_id
        st.rerun()

    left, right = st.columns([1.35, 1.0])
    with left:
        st.markdown(f"## {selected_topic['title']}")
        st.markdown(
            f"""
**교과 단원**: {selected_topic['curriculum_unit']}  
**대표 지역**: {world_case['title']} · {world_case['location_label']}  
**권장 시점**: {recommended_view}  
**기본 오버레이**: {OVERLAY_LABELS.get(selected_topic['primary_overlay'], selected_topic['primary_overlay'])}
"""
        )
        st.info(selected_topic["classroom_goal"])
        st.caption(f"관찰 포인트: {selected_topic['observation_focus']}")
        st.caption(f"비교 힌트: {selected_topic['compare_hint']}")
        st.caption(f"교사 설명 포인트: {selected_topic['teacher_note']}")
    with right:
        st.plotly_chart(
            build_group_case_map(group_topics, selected_topic_id),
            use_container_width=True,
            config={"displayModeBar": False},
        )

    preview_col, card_col = st.columns([1.3, 1.0])
    with preview_col:
        st.markdown("### 3. 표준 시점 보기")
        figure = render_terrain_plotly(
            preview,
            f"{selected_topic['title']} 표준 시점",
            add_water=False,
            landform_type=str(selected_topic["landform_type"]),
            detailed_type=landform_key,
            process_fields=process_fields,
            overlay_type=str(selected_topic["primary_overlay"]),
            camera_profile=camera_profile,
        )
        figure = tune_standard_view_figure(figure)
        st.plotly_chart(
            figure,
            use_container_width=True,
            config={"displayModeBar": False, "responsive": True},
        )
        st.caption(selected_topic["overlay_caption"])

    with card_col:
        st.markdown("### 4. 수업 카드")
        st.markdown(
            f"""
**학생 질문**  
{selected_topic['student_question']}

**교사 설명 포인트**  
{selected_topic['teacher_note']}

**이 화면에서 먼저 볼 것**  
- {recommended_view} 구도에서 지형의 전체 윤곽 읽기  
- `{OVERLAY_LABELS.get(selected_topic['primary_overlay'], selected_topic['primary_overlay'])}` 오버레이가 강조하는 과정 보기  
- {selected_topic['compare_hint']}
"""
        )

    st.markdown("### 5. 형성 과정 4단계")
    stage_cols = st.columns(2)
    for idx, stage in enumerate(selected_topic["stages"]):
        with stage_cols[idx % 2]:
            st.markdown(
                f"""
#### 단계 {idx + 1}. {stage['title']}
**우세 작용**: {stage['dominant_process']}  
**오버레이**: {OVERLAY_LABELS.get(stage['overlay'], stage['overlay'])}

학생 설명: {stage['student_copy']}

교사 설명 포인트: {stage['teacher_copy']}

질문: {stage['question']}
"""
            )

    st.markdown("### 6. 다음 행동")
    cta1, cta2, cta3 = st.columns(3)
    with cta1:
        if st.button("Lab 교사 시연으로 열기", use_container_width=True, disabled=lab_preset is None):
            route_to_lab(category, landform_key, "교사 상세모드")
    with cta2:
        if st.button("Lab 학생 탐구로 열기", use_container_width=True, disabled=lab_preset is None):
            route_to_lab(category, landform_key, "학생 단순모드")
    with cta3:
        if st.button("Gallery에서 자세히 보기", use_container_width=True):
            open_gallery(category, landform_key)

    if lab_preset is None:
        st.warning("이 지형은 아직 Lab 직접 시연 preset이 없습니다. 현재는 Gallery 자세히 보기로 연결됩니다.")

    st.info("이 페이지는 버튼 수를 줄이고, 대표 세계 사례와 표준 시점을 먼저 보여주는 고등학교 수업용 아틀라스입니다.")
