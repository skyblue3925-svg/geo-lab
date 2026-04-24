"""
Geo-Lab Gallery page.
Stable, minimal gallery for 3D landform exploration and animation.
"""

import base64
import html
import inspect
import io
import os
import sys
import time
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
import streamlit as st
from matplotlib import cm
try:
    from PIL import Image
except ImportError:
    Image = None

# Add project root to import path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.components.animation_renderer import (
    create_animated_terrain_figure,
    get_multi_angle_cameras,
)
from app.components.renderer import render_terrain_plotly
from app.services.animation_assets import (
    load_cinematic_metadata,
    load_generated_storyboard_texture,
    resolve_cinematic_media_path,
)
from app.utils.gallery_showcase import (
    ADVANCED_MODE,
    CATALOG_MODE,
    build_lab_showcase_preset,
    consume_gallery_showcase_preset,
    get_gallery_showcase_preset,
    queue_gallery_showcase_preset,
)
from app.utils.world_terrain_cases import (
    extract_selected_world_case_id,
    get_world_case,
    get_world_cases_for_category,
)
from engine.ideal_landforms import IDEAL_LANDFORM_GENERATORS, ANIMATED_LANDFORM_GENERATORS

st.set_page_config(page_title="갤러리", page_icon="📖", layout="wide")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PAGES_DIR = PROJECT_ROOT / "pages"
KICKER_LABELS = {
    "River Systems": "하천 지형",
    "Delta Showcase": "삼각주 지형",
    "Glacial Forms": "빙하 지형",
    "Volcanic Relief": "화산 지형",
    "Karst Landscapes": "카르스트 지형",
    "Arid Terrain": "건조 지형",
    "Coastal Change": "해안 지형",
}


def load_css() -> None:
    css_path = PROJECT_ROOT / "assets" / "style.css"
    if css_path.exists():
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def resolve_page_path(fragment: str) -> str | None:
    page_path = next((path for path in PAGES_DIR.iterdir() if fragment in path.name), None)
    if page_path is None:
        return None
    return page_path.relative_to(PROJECT_ROOT).as_posix()


def show_image_stretch(image) -> None:
    if "use_container_width" in inspect.signature(st.image).parameters:
        st.image(image, use_container_width=True)
    else:
        st.image(image, use_column_width=True)


def load_uploaded_texture(uploaded_file):
    if uploaded_file is None or Image is None:
        return None
    try:
        image = Image.open(uploaded_file).convert("RGB")
        return np.asarray(image, dtype=np.uint8)
    except Exception:
        return None


def pretty_name(key: str) -> str:
    return key.replace("_", " ").title()


def format_kicker_label(value: object) -> str:
    label = str(value)
    return KICKER_LABELS.get(label, label)


def generate_landform(key: str, grid_size: int, stage: float = 1.0) -> np.ndarray:
    func = IDEAL_LANDFORM_GENERATORS[key]
    params = inspect.signature(func).parameters

    if "stage" in params:
        result = func(grid_size, stage)
    else:
        result = func(grid_size)

    if isinstance(result, tuple):
        return result[0]
    return result


def generate_animated_stage(key: str, grid_size: int, stage: float) -> np.ndarray:
    if key not in ANIMATED_LANDFORM_GENERATORS:
        return generate_landform(key, grid_size, stage)

    func = ANIMATED_LANDFORM_GENERATORS[key]
    try:
        result = func(grid_size, stage, return_metadata=True)
        if isinstance(result, tuple):
            return result[0]
        return result
    except Exception:
        result = func(grid_size, stage)
        if isinstance(result, tuple):
            return result[0]
        return result


@st.cache_data(show_spinner=False)
def build_landform_thumbnail(landform_key: str, stage: float = 0.9, grid_size: int = 120) -> bytes | None:
    elevation = np.array(generate_animated_stage(landform_key, grid_size, stage), dtype=float)
    relief = float(np.ptp(elevation))
    if relief <= 1e-6:
        relief = 1.0

    normalized = (elevation - float(np.min(elevation))) / relief
    grad_y, grad_x = np.gradient(elevation)
    slope = np.hypot(grad_x, grad_y)
    shade = 1.0 - np.clip(slope / (np.percentile(slope, 95) + 1e-6), 0.0, 1.0)
    terrain_rgb = cm.terrain(np.clip(0.08 + 0.92 * normalized, 0.0, 1.0))[..., :3]
    lit_rgb = np.clip(terrain_rgb * (0.66 + 0.34 * shade[..., None]), 0.0, 1.0)

    if Image is None:
        return None

    buffer = io.BytesIO()
    Image.fromarray((lit_rgb * 255).astype(np.uint8)).save(buffer, format="PNG")
    return buffer.getvalue()


def build_showcase_card_markup(preset: dict, thumbnail: bytes | None, is_active: bool = False) -> str:
    image_html = '<div class="gallery-showcase-thumb placeholder">미리보기 없음</div>'
    if thumbnail:
        encoded = base64.b64encode(thumbnail).decode("ascii")
        image_html = f'<div class="gallery-showcase-thumb-wrap"><img class="gallery-showcase-thumb" src="data:image/png;base64,{encoded}" alt="{html.escape(preset["title"])}" /></div>'

    chips = [
        f'난이도 {preset.get("difficulty_label", "보통")}',
        preset.get("camera_motion_label", "고정"),
        f"형성 단계 {int(float(preset.get('stage', 1.0)) * 100)}%",
    ]
    chips_html = "".join(f'<span class="gallery-showcase-chip">{html.escape(str(chip))}</span>' for chip in chips)
    active_class = " is-active" if is_active else ""
    focus = html.escape(str(preset.get("lesson_focus", "이 지형에서 먼저 읽을 수 있는 형성 포인트를 확인하세요.")))
    world_case = preset.get("world_case")
    world_case_html = ""
    if isinstance(world_case, dict):
        world_case_title = html.escape(str(world_case.get("title", "")))
        world_case_location = html.escape(str(world_case.get("location_label", "")))
        world_case_hook = html.escape(str(world_case.get("classroom_hook", "")))
        world_case_html = f"""
  <div class="gallery-world-case compact">
    <div class="gallery-world-case-label">대표 세계 사례</div>
    <div class="gallery-world-case-title">{world_case_title}</div>
    <div class="gallery-world-case-copy">{world_case_location}</div>
    <div class="gallery-world-case-copy secondary">{world_case_hook}</div>
  </div>
"""

    return f"""
<div class="gallery-showcase-card{active_class}">
  {image_html}
  <div class="gallery-showcase-kicker">{html.escape(format_kicker_label(preset.get('kicker', '수업 예시')))}</div>
  <div class="gallery-showcase-title">{html.escape(str(preset['title']))}</div>
  <div class="gallery-showcase-copy">{html.escape(str(preset.get('summary', '')))}</div>
  {world_case_html}
  <div class="gallery-showcase-focus-label">수업 포인트</div>
  <div class="gallery-showcase-focus">{focus}</div>
  <div class="gallery-showcase-meta">{chips_html}</div>
</div>
"""


def build_showcase_hero_markup(preset: dict) -> str:
    world_case = preset.get("world_case")
    world_case_html = ""
    if isinstance(world_case, dict):
        title = html.escape(str(world_case.get("title", "")))
        location = html.escape(str(world_case.get("location_label", "")))
        hook = html.escape(str(world_case.get("classroom_hook", "")))
        process_focus = "".join(
            f'<span class="gallery-showcase-chip strong">{html.escape(str(process))}</span>'
            for process in world_case.get("process_focus", ())
        )
        world_case_html = f"""
  <div class="gallery-world-case inverted">
    <div class="gallery-world-case-label inverted">대표 세계 사례</div>
    <div class="gallery-world-case-title inverted">{title}</div>
    <div class="gallery-world-case-copy inverted">{location}</div>
    <div class="gallery-world-case-copy inverted secondary">{hook}</div>
    <div class="gallery-showcase-meta">{process_focus}</div>
  </div>
"""

    return f"""
<div class="gallery-showcase-hero">
  <div class="gallery-showcase-eyebrow">고등학교 수업 카탈로그</div>
  <div class="gallery-showcase-hero-title">{html.escape(str(preset['title']))}</div>
  <div class="gallery-showcase-hero-copy">{html.escape(str(preset.get('summary', '')))}</div>
  <div class="gallery-showcase-focus-row">
    <div>
      <div class="gallery-showcase-focus-label inverted">수업 포인트</div>
      <div class="gallery-showcase-hero-focus">{html.escape(str(preset.get('lesson_focus', '형성 과정의 핵심 장면을 골라 수업에서 바로 설명할 수 있습니다.')))}</div>
    </div>
    <div class="gallery-showcase-difficulty-pill">난이도 {html.escape(str(preset.get('difficulty_label', '보통')))}</div>
  </div>
  <div class="gallery-showcase-meta">
    <span class="gallery-showcase-chip strong">{html.escape(format_kicker_label(preset.get('kicker', '수업 예시')))}</span>
    <span class="gallery-showcase-chip">{html.escape(str(preset.get('render_style_label', '기본 지형')))}</span>
    <span class="gallery-showcase-chip">{html.escape(str(preset.get('camera_motion_label', '고정')))}</span>
    <span class="gallery-showcase-chip">카메라 {html.escape(str(preset.get('camera_view', '기본 사각 뷰')))}</span>
  </div>
  {world_case_html}
</div>
"""


def build_showcase_lesson_panel_markup(preset: dict, has_lab_link: bool) -> str:
    next_step = "Lab 모범사례로 바로 넘겨 수업 시연까지 이어집니다." if has_lab_link else "Gallery 안에서 대표 장면을 미리보고 설명용 예시로 사용할 수 있습니다."
    world_case = preset.get("world_case")
    world_case_markup = ""
    if isinstance(world_case, dict):
        world_case_markup = f"""
  <div class="gallery-showcase-focus-label">세계 사례 질문</div>
  <div class="gallery-showcase-lesson-copy">{html.escape(str(world_case.get('student_question', '')))}</div>
  <div class="gallery-showcase-focus-label">교사 설명 포인트</div>
  <div class="gallery-showcase-lesson-copy">{html.escape(str(world_case.get('teacher_note', '')))}</div>
"""
    return f"""
<div class="gallery-showcase-lesson-panel">
  <div class="gallery-showcase-focus-label">관찰 질문</div>
  <div class="gallery-showcase-lesson-copy">{html.escape(str(preset.get('observation_prompt', '이 지형에서 가장 먼저 달라지는 부분을 찾아보세요.')))}</div>
  {world_case_markup}
  <div class="gallery-showcase-focus-label">추천 흐름</div>
  <div class="gallery-showcase-lesson-copy">{html.escape(next_step)}</div>
</div>
"""


def build_world_case_atlas_markup(world_case: dict, is_active: bool = False) -> str:
    active_class = " is-active" if is_active else ""
    process_focus = "".join(
        f'<span class="gallery-showcase-chip">{html.escape(str(process))}</span>'
        for process in world_case.get("process_focus", ())
    )
    return f"""
<div class="gallery-world-case-atlas{active_class}">
  <div class="gallery-world-case-label">세계 사례</div>
  <div class="gallery-world-case-title">{html.escape(str(world_case.get('title', '')))}</div>
  <div class="gallery-world-case-copy">{html.escape(str(world_case.get('location_label', '')))}</div>
  <div class="gallery-world-case-copy secondary">{html.escape(str(world_case.get('classroom_hook', '')))}</div>
  <div class="gallery-showcase-meta">{process_focus}</div>
</div>
"""


def build_world_case_map_figure(world_cases: list[dict], active_landform: str | None = None) -> go.Figure:
    fig = go.Figure()
    inactive_cases = [case for case in world_cases if case.get("landform_key") != active_landform]
    active_cases = [case for case in world_cases if case.get("landform_key") == active_landform]

    def hover_text(case: dict) -> str:
        process_text = " · ".join(str(item) for item in case.get("process_focus", ()))
        return (
            f"<b>{html.escape(str(case.get('title', '')))}</b><br>"
            f"{html.escape(str(case.get('location_label', '')))}<br>"
            f"핵심 과정: {html.escape(process_text)}"
        )

    if inactive_cases:
        fig.add_trace(
            go.Scattergeo(
                lon=[case["longitude"] for case in inactive_cases],
                lat=[case["latitude"] for case in inactive_cases],
                mode="markers+text",
                text=[case["title"] for case in inactive_cases],
                textposition="top center",
                marker=dict(
                    size=10,
                    color="#0ea5e9",
                    line=dict(color="#f8fafc", width=1.5),
                    opacity=0.85,
                ),
                hovertext=[hover_text(case) for case in inactive_cases],
                hovertemplate="%{hovertext}<extra></extra>",
                customdata=[case["case_id"] for case in inactive_cases],
                name="대표 사례",
            )
        )

    if active_cases:
        fig.add_trace(
            go.Scattergeo(
                lon=[case["longitude"] for case in active_cases],
                lat=[case["latitude"] for case in active_cases],
                mode="markers+text",
                text=[case["title"] for case in active_cases],
                textposition="top center",
                marker=dict(
                    size=15,
                    color="#f97316",
                    line=dict(color="#7c2d12", width=2),
                    opacity=0.95,
                    symbol="diamond",
                ),
                hovertext=[hover_text(case) for case in active_cases],
                hovertemplate="%{hovertext}<extra></extra>",
                customdata=[case["case_id"] for case in active_cases],
                name="선택한 사례",
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
    fig.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        height=340,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        clickmode="event+select",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1.0,
            bgcolor="rgba(255,255,255,0.75)",
        ),
    )
    return fig


def route_to_lab_showcase(category: str, landform_key: str) -> bool:
    preset = build_lab_showcase_preset(category, landform_key)
    if preset is None:
        return False

    st.session_state["gallery_lab_preset"] = preset
    if hasattr(st, "switch_page"):
        st.switch_page("pages/3_🧪_Lab.py")
    return True


CATEGORY_MAP = {
    "하천": [
        "alluvial_fan",
        "free_meander",
        "incised_meander",
        "v_valley",
        "braided_river",
        "waterfall",
        "perched_river",
    ],
    "삼각주": ["delta", "bird_foot_delta", "arcuate_delta", "cuspate_delta", "estuary"],
    "빙하": ["u_valley", "cirque", "horn", "fjord", "drumlin", "moraine", "arete"],
    "화산": ["shield_volcano", "stratovolcano", "caldera", "crater_lake", "lava_plateau"],
    "카르스트": ["karst_doline", "uvala", "tower_karst", "karren"],
    "건조": ["barchan", "transverse_dune", "star_dune", "mesa_butte", "wadi", "playa", "pedestal_rock", "pediment"],
    "해안": ["coastal_cliff", "spit_lagoon", "tombolo", "ria_coast", "sea_arch", "coastal_dune"],
}

CATEGORY_TO_TYPE = {
    "하천": "river",
    "삼각주": "river",
    "빙하": "glacial",
    "화산": "volcanic",
    "카르스트": "karst",
    "건조": "arid",
    "해안": "coastal",
}

LANDFORM_TO_TYPE = {}
for _cat, _items in CATEGORY_MAP.items():
    _lf_type = CATEGORY_TO_TYPE.get(_cat, "river")
    for _item in _items:
        LANDFORM_TO_TYPE[_item] = _lf_type


load_css()

st.markdown("## 갤러리")
st.caption("수업에 바로 쓸 수 있는 지형 예시를 고르고, 선택한 지형의 3D 형성 장면을 먼저 확인합니다.")
st.info("단순 학생용 보기는 새 Learn 페이지, 제작 관리는 Animation Studio 페이지로 분리 중입니다.")
high_school_page = resolve_page_path("High_School_Geography.py")
if high_school_page:
    st.info("고등학교 세계지리 수업용 대표 지형만 빠르게 보려면 별도 수업 페이지를 사용하는 편이 더 가볍습니다.")
    st.markdown(f"[고등학교 수업용 지형 페이지로 이동]({high_school_page})")

main_tab1, main_tab2 = st.tabs(["수업용 예시 카탈로그", "시네마틱 영상"])

with main_tab2:
    st.subheader("시네마틱 영상")
    metadata = load_cinematic_metadata()
    videos = metadata.get("videos", [])

    if not videos:
        st.info("등록된 시네마틱 영상이 아직 없습니다.")
    else:
        show_cinematic_media = st.checkbox(
            "시네마틱 파일 미리보기 로드",
            value=False,
            help="이미지와 WebP 파일이 많아 Gallery 첫 화면이 느려질 수 있어 필요할 때만 로드합니다.",
        )
        for video in videos:
            with st.expander(f"{video.get('title', video.get('id', 'video'))}"):
                st.write(video.get("description", ""))
                status = video.get("status", "pending")
                file_name = video.get("file", "")
                media_path = resolve_cinematic_media_path(file_name)

                if status == "ready" and media_path.exists() and show_cinematic_media:
                    if media_path.suffix.lower() in {".gif", ".webp", ".png", ".jpg", ".jpeg"}:
                        with open(media_path, "rb") as f:
                            show_image_stretch(f.read())
                    else:
                        st.video(str(media_path))
                elif status == "ready" and media_path.exists():
                    st.caption("미리보기 로드를 켜면 파일을 화면에 표시합니다.")
                else:
                    st.warning(f"상태: {status}")

    st.markdown("---")
    st.subheader("인터랙티브 시네마틱 (실험)")
    st.caption("고정 영상 대신, 위성 느낌 렌더링 + 이동 카메라로 실시간 시네마틱 재생을 볼 수 있습니다.")

    cinematic_choices = [k for k in ANIMATED_LANDFORM_GENERATORS.keys()]
    cine_col1, cine_col2, cine_col3, cine_col4, cine_col5 = st.columns([1.2, 1.0, 1.0, 1.0, 1.0])
    with cine_col1:
        cine_landform = st.selectbox(
            "시네마틱 지형",
            cinematic_choices,
            format_func=pretty_name,
            key="cine_landform",
        )
    with cine_col2:
        cine_motion = st.selectbox(
            "카메라 연출",
            ["오빗", "패닝", "고정"],
            key="cine_motion",
        )
    with cine_col3:
        cine_frames = st.slider("프레임", 20, 80, 40, 5, key="cine_frames")
    with cine_col4:
        cine_zoom = st.slider("줌", 0.7, 1.8, 1.0, 0.1, key="cine_zoom")
    with cine_col5:
        cine_texture_mode = st.selectbox(
            "질감 소스",
            ["합성", "생성 이미지", "업로드 이미지"],
            key="cine_texture_mode",
            help="생성 이미지는 새 4패널 스토리보드의 현재 단계 패널을 3D 표면 질감으로 사용합니다.",
        )

    cine_motion_code = {"고정": "fixed", "오빗": "orbit", "패닝": "sweep"}[cine_motion]
    cine_start = st.slider("시작 단계", 0.0, 1.0, 0.15, 0.05, key="cine_start")
    cine_texture = None
    if cine_texture_mode == "생성 이미지":
        cine_texture = load_generated_storyboard_texture(cine_landform, cine_start)
        if cine_texture is None:
            st.info("이 지형에 연결된 생성 이미지 텍스처가 아직 없습니다.")
        else:
            st.caption("생성 이미지 단계 텍스처가 적용됩니다.")
    elif cine_texture_mode == "업로드 이미지":
        cine_texture = st.session_state.get("gallery_uploaded_texture_map")
        if cine_texture is None:
            st.info("업로드 텍스처가 없습니다. 3D 시뮬레이션 탭에서 이미지를 먼저 업로드하세요.")

    cine_func = ANIMATED_LANDFORM_GENERATORS[cine_landform]
    cine_fig = create_animated_terrain_figure(
        landform_func=cine_func,
        grid_size=90,
        num_frames=cine_frames,
        title=f"{pretty_name(cine_landform)} 시네마틱",
        landform_type=LANDFORM_TO_TYPE.get(cine_landform, "river"),
        detailed_type=cine_landform,
        start_stage=cine_start,
        render_style="satellite",
        camera_motion=cine_motion_code,
        cinematic_zoom=cine_zoom,
        texture_map=cine_texture,
    )
    if cine_fig is not None:
        cine_fig.update_layout(
            scene=dict(
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                zaxis=dict(visible=False),
                bgcolor="#020617",
            ),
            paper_bgcolor="#020617",
            plot_bgcolor="#020617",
            margin=dict(l=0, r=0, t=60, b=10),
            height=760,
        )
        st.plotly_chart(
            cine_fig,
            use_container_width=True,
            key="interactive_cinematic_view",
            config={"scrollZoom": True, "displayModeBar": True},
        )

with main_tab1:
    consume_gallery_showcase_preset(st.session_state)
    st.sidebar.subheader("수업용 예시")
    category = st.sidebar.radio("지형 분류", list(CATEGORY_MAP.keys()), key="gallery_cat")
    landform_options = CATEGORY_MAP[category]
    higher_ed_page = resolve_page_path("Higher_Ed.py")

    if st.session_state.get("landform_select") not in landform_options:
        st.session_state["landform_select"] = landform_options[0]

    active_landform = st.session_state.get("landform_select", landform_options[0])
    active_preset = get_gallery_showcase_preset(category, active_landform)
    selected_lab_preset = build_lab_showcase_preset(category, active_landform)
    world_cases = get_world_cases_for_category(category)

    hero_col, panel_col = st.columns([2.3, 1.2])
    with hero_col:
        st.markdown(build_showcase_hero_markup(active_preset), unsafe_allow_html=True)
        st.caption("카드를 누르면 아래 미리보기가 바로 바뀌고, 연결된 대표 지형은 Lab 수업 흐름까지 이어집니다.")
    with panel_col:
        view_mode = st.radio("보기 방식", [CATALOG_MODE, ADVANCED_MODE], horizontal=True, key="gallery_mode")
        st.markdown(
            build_showcase_lesson_panel_markup(active_preset, selected_lab_preset is not None),
            unsafe_allow_html=True,
        )
        if selected_lab_preset is not None:
            if st.button("Lab에서 수업 시작", key="gallery_selected_lab", use_container_width=True):
                if not route_to_lab_showcase(category, active_landform):
                    st.warning("이 지형은 아직 Lab 모범사례와 연결되지 않았습니다.")
        else:
            st.caption("이 예시는 현재 Gallery 미리보기 중심으로 제공됩니다.")
        if higher_ed_page:
            st.markdown(f"[대학·연구 포털로 이동]({higher_ed_page})")

    is_catalog_mode = view_mode == CATALOG_MODE

    if is_catalog_mode:
        selected_landform = active_landform
        preview_preset = active_preset
        gallery_grid_size = int(preview_preset.get("grid_size", 72))
        num_frames = int(preview_preset.get("num_frames", 30))
        stage_value = st.slider(
            "형성 단계 미리보기",
            0.0,
            1.0,
            float(preview_preset.get("stage", 1.0)),
            0.05,
            key="gallery_stage_slider",
        )
        recommended_animation_mode = preview_preset.get("animation_mode", "연속 애니메이션")
        animation_mode = "수동 단계"
        render_style_label = preview_preset.get("render_style_label", "기본 지형")
        camera_motion_label = preview_preset.get("camera_motion_label", "고정")
        cinematic_zoom = float(preview_preset.get("cinematic_zoom", 1.0))
        st.info(
            f"표준 3D를 먼저 표시합니다. 추천 애니메이션: {recommended_animation_mode} · {render_style_label} · {camera_motion_label}"
        )
        st.caption(
            "고급 카메라/텍스처/재생 설정이 필요하면 보기 방식을 '고급 미리보기'로 바꾸세요."
        )
    else:
        selected_landform = st.selectbox(
            "상세 확인 지형",
            landform_options,
            format_func=pretty_name,
            key="landform_select",
        )
        preview_preset = get_gallery_showcase_preset(category, selected_landform)
        p1, p2 = st.columns(2)
        with p1:
            gallery_grid_size = st.slider("해상도", 30, 200, 60, 10, key="gallery_res")
        with p2:
            num_frames = st.slider("프레임 수", 10, 100, 30, 5, key="anim_frames")

        stage_value = st.slider("형성 단계", 0.0, 1.0, 1.0, 0.02, key="gallery_stage_slider")

    camera_presets = get_multi_angle_cameras()
    if is_catalog_mode:
        selected_view = preview_preset.get("camera_view", "기본 사각 뷰")
        selected_camera = camera_presets.get(selected_view, next(iter(camera_presets.values())))
    else:
        selected_view = st.selectbox("카메라 시점", list(camera_presets.keys()), key="camera_view")
        selected_camera = camera_presets[selected_view]

        animation_mode = st.radio(
            "애니메이션 모드",
            ["연속 애니메이션", "수동 단계"],
            horizontal=True,
            key="anim_mode",
        )

        style_col1, style_col2, style_col3 = st.columns([1.2, 1.2, 1.0])
        with style_col1:
            render_style_label = st.selectbox(
                "렌더 스타일",
                ["기본 지형", "위성 느낌"],
                key="gallery_render_style",
            )
        with style_col2:
            camera_motion_label = st.selectbox(
                "카메라 연출",
                ["고정", "오빗", "패닝"],
                key="gallery_camera_motion",
                help="오빗/패닝은 재생 중 카메라가 자동 이동합니다.",
            )
        with style_col3:
            cinematic_zoom = st.slider(
                "시네마틱 줌",
                0.7,
                1.8,
                1.0,
                0.1,
                key="gallery_cinematic_zoom",
            )

    render_style = "satellite" if render_style_label == "위성 느낌" else "terrain"
    camera_motion = {"고정": "fixed", "오빗": "orbit", "패닝": "sweep"}[camera_motion_label]
    texture_map = None
    if render_style == "satellite" and not is_catalog_mode:
        texture_col1, texture_col2 = st.columns([1.2, 1.8])
        with texture_col1:
            texture_mode = st.selectbox(
                "위성 텍스처",
                ["합성 텍스처", "생성 이미지 단계", "이미지 업로드"],
                key="gallery_texture_mode",
            )
        with texture_col2:
            if texture_mode == "생성 이미지 단계":
                texture_map = load_generated_storyboard_texture(selected_landform, stage_value)
                if texture_map is not None:
                    st.caption("선택한 지형의 생성 이미지 단계가 3D 표면 질감으로 적용됩니다.")
                else:
                    st.info("이 지형에 연결된 생성 이미지 텍스처가 아직 없습니다.")
            elif texture_mode == "이미지 업로드":
                uploaded_texture = st.file_uploader(
                    "위성/항공 사진 업로드 (PNG/JPG)",
                    type=["png", "jpg", "jpeg", "webp"],
                    key="gallery_texture_upload",
                )
                texture_map = load_uploaded_texture(uploaded_texture)
                if texture_map is not None:
                    st.session_state["gallery_uploaded_texture_map"] = texture_map
                    st.caption("업로드 텍스처가 적용됩니다.")
                elif uploaded_texture is not None:
                    st.warning("이미지를 읽지 못했습니다. 다른 파일로 다시 시도해 주세요.")
                else:
                    texture_map = st.session_state.get("gallery_uploaded_texture_map")

    landform_type = CATEGORY_TO_TYPE.get(category, "river")

    st.markdown("### 선택한 예시 미리보기")
    if animation_mode == "연속 애니메이션" and selected_landform in ANIMATED_LANDFORM_GENERATORS:
        st.info("선택한 형성 단계부터 재생합니다. 재생 중에도 카메라 조작이 유지됩니다.")
        st.caption("팁: 단계 슬라이더를 바꾼 뒤 재생하면, 그 지점을 시작점으로 유지해 이어서 재생합니다.")

        try:
            _v0 = generate_animated_stage(selected_landform, 48, 0.1)
            _v1 = generate_animated_stage(selected_landform, 48, 0.9)
            _delta = float(np.mean(np.abs(np.array(_v1, dtype=float) - np.array(_v0, dtype=float))))
            if _delta < 0.02:
                st.warning("이 지형은 현재 애니메이션 변화가 매우 작아 정지처럼 보일 수 있습니다.")
        except Exception:
            pass
        play_engine = "표준 재생 (Plotly)"
        if not is_catalog_mode:
            play_engine = st.radio(
                "재생 엔진",
                ["표준 재생 (Plotly)", "안정 재생 (호환 모드)"],
                index=1,
                horizontal=True,
                key="gallery_play_engine",
                help="표준 재생이 멈추면 안정 재생으로 전환하세요.",
            )

        anim_func = ANIMATED_LANDFORM_GENERATORS[selected_landform]
        if play_engine == "표준 재생 (Plotly)":
            fig_animated = create_animated_terrain_figure(
                landform_func=anim_func,
                grid_size=gallery_grid_size,
                num_frames=num_frames,
                title=f"{pretty_name(selected_landform)} 형성과정",
                landform_type=landform_type,
                detailed_type=selected_landform,
                start_stage=stage_value,
                render_style=render_style,
                camera_motion=camera_motion,
                base_camera=selected_camera,
                cinematic_zoom=cinematic_zoom,
                texture_map=texture_map,
            )

            if fig_animated is not None:
                if camera_motion == "fixed":
                    fig_animated.update_layout(scene=dict(camera=selected_camera))
                st.plotly_chart(
                    fig_animated,
                    use_container_width=True,
                    key="animated_view",
                    config={"scrollZoom": True, "displayModeBar": True},
                )
        else:
            st.caption("호환 모드는 Plotly 내부 재생 대신 앱이 프레임을 직접 넘깁니다.")
            if render_style == "satellite":
                st.caption("호환 모드에서는 위성 텍스처의 색감이 일부 단순화됩니다.")

            safe_prefix = f"gallery_safe_{selected_landform}"
            frame_key = f"{safe_prefix}_frame"
            playing_key = f"{safe_prefix}_playing"
            start_idx = int(round(stage_value * (num_frames - 1)))

            if frame_key not in st.session_state:
                st.session_state[frame_key] = start_idx
            if playing_key not in st.session_state:
                st.session_state[playing_key] = False

            c_btn1, c_btn2, c_btn3, c_btn4 = st.columns(4)
            if c_btn1.button("재생", key=f"{safe_prefix}_play", use_container_width=True):
                st.session_state[playing_key] = True
            if c_btn2.button("정지", key=f"{safe_prefix}_pause", use_container_width=True):
                st.session_state[playing_key] = False
            if c_btn3.button("시작 지점", key=f"{safe_prefix}_reset", use_container_width=True):
                st.session_state[playing_key] = False
                st.session_state[frame_key] = start_idx
            if c_btn4.button("한 프레임", key=f"{safe_prefix}_step", use_container_width=True):
                st.session_state[playing_key] = False
                st.session_state[frame_key] = (st.session_state[frame_key] + 1) % num_frames

            speed_ms = st.slider(
                "재생 속도(ms/frame)",
                80,
                500,
                180,
                20,
                key=f"{safe_prefix}_speed",
            )

            if st.session_state[playing_key]:
                time.sleep(speed_ms / 1000.0)
                st.session_state[frame_key] = (st.session_state[frame_key] + 1) % num_frames
                st.rerun()

            cur_idx = st.slider(
                "재생 프레임",
                0,
                num_frames - 1,
                int(st.session_state[frame_key]),
                key=f"{safe_prefix}_slider",
            )
            st.session_state[frame_key] = int(cur_idx)
            stage_dynamic = 0.0 if num_frames <= 1 else cur_idx / (num_frames - 1)

            elevation_dynamic = generate_animated_stage(selected_landform, gallery_grid_size, stage_dynamic)
            water_depth_dynamic = np.maximum(0.0, -elevation_dynamic + 1.0)
            water_depth_dynamic[elevation_dynamic > 2] = 0

            fig_safe = render_terrain_plotly(
                elevation_dynamic,
                f"{pretty_name(selected_landform)} - {int(stage_dynamic * 100)}%",
                add_water=True,
                water_depth_grid=water_depth_dynamic,
                water_level=-999,
                force_camera=False,
                landform_type=landform_type,
                detailed_type=selected_landform,
            )
            if fig_safe is not None:
                fig_safe.update_layout(scene=dict(camera=selected_camera))
                st.plotly_chart(
                    fig_safe,
                    use_container_width=True,
                    key="animated_view_safe",
                    config={"scrollZoom": True, "displayModeBar": True},
                )
    else:
        elevation = generate_animated_stage(selected_landform, gallery_grid_size, stage_value)
        water_depth = np.maximum(0.0, -elevation + 1.0)
        water_depth[elevation > 2] = 0

        fig_stage = render_terrain_plotly(
            elevation,
            f"{pretty_name(selected_landform)} - {int(stage_value * 100)}%",
            add_water=True,
            water_depth_grid=water_depth,
            water_level=-999,
            force_camera=False,
            landform_type=landform_type,
            detailed_type=selected_landform,
        )
        if fig_stage is not None:
            fig_stage.update_layout(scene=dict(camera=selected_camera))
            st.plotly_chart(
                fig_stage,
                use_container_width=True,
                key="stage_view",
                config={"scrollZoom": True, "displayModeBar": True},
            )

    st.markdown(
        build_showcase_lesson_panel_markup(
            preview_preset,
            build_lab_showcase_preset(category, selected_landform) is not None,
        ),
        unsafe_allow_html=True,
    )

    current_elev = generate_animated_stage(selected_landform, gallery_grid_size, stage_value)
    c1, c2, c3 = st.columns(3)
    c1.metric("최저", f"{current_elev.min():.1f} m")
    c2.metric("최고", f"{current_elev.max():.1f} m")
    c3.metric("기복량", f"{(current_elev.max() - current_elev.min()):.1f} m")

    st.markdown("---")

    if world_cases:
        st.markdown("### 세계 대표 사례")
        st.caption("대표 지형을 실제 지역 사례와 연결해 수업 질문과 설명 포인트를 바로 꺼낼 수 있습니다. 지도 마커를 눌러도 같은 preset으로 전환됩니다.")
        atlas_cards_col, atlas_map_col = st.columns([1.45, 1.0])
        with atlas_cards_col:
            atlas_cols = st.columns(min(2, len(world_cases)))
            for idx, world_case in enumerate(world_cases):
                with atlas_cols[idx % len(atlas_cols)]:
                    st.markdown(
                        build_world_case_atlas_markup(
                            world_case,
                            is_active=(world_case.get("landform_key") == active_landform),
                        ),
                        unsafe_allow_html=True,
                    )
                    if st.button(
                        "이 사례 열기",
                        key=f"gallery_world_case_{world_case['case_id']}",
                        use_container_width=True,
                    ):
                        queue_gallery_showcase_preset(
                            st.session_state,
                            get_gallery_showcase_preset(category, str(world_case["landform_key"])),
                        )
                        st.rerun()
        with atlas_map_col:
            st.markdown("#### 세계 위치")
            st.caption("선택한 사례는 주황색으로 강조됩니다. 기후·지형 단원에서 실제 지역과 연결해 설명하기 좋습니다.")
            map_event = st.plotly_chart(
                build_world_case_map_figure(world_cases, active_landform=active_landform),
                use_container_width=True,
                key=f"gallery_world_case_map_{category}_{st.session_state.get('gallery_world_case_map_nonce', 0)}",
                config={"displayModeBar": False, "scrollZoom": False},
                on_select="rerun",
                selection_mode="points",
            )
            selected_case_id = extract_selected_world_case_id(map_event)
            if selected_case_id:
                selected_case = get_world_case(selected_case_id)
                selected_landform = str(selected_case.get("landform_key", "")) if selected_case else ""
                if selected_landform and selected_landform in landform_options and selected_landform != active_landform:
                    queue_gallery_showcase_preset(
                        st.session_state,
                        get_gallery_showcase_preset(category, selected_landform),
                    )
                    st.session_state["gallery_world_case_map_nonce"] = (
                        st.session_state.get("gallery_world_case_map_nonce", 0) + 1
                    )
                    st.rerun()

    st.markdown("### 수업용 예시")
    for row_start in range(0, len(landform_options), 3):
        row_items = landform_options[row_start:row_start + 3]
        row_cols = st.columns(len(row_items))
        for idx, landform_key in enumerate(row_items):
            preset = get_gallery_showcase_preset(category, landform_key)
            thumbnail = None
            with row_cols[idx]:
                st.markdown(
                    build_showcase_card_markup(
                        preset,
                        thumbnail,
                        is_active=(landform_key == active_landform),
                    ),
                    unsafe_allow_html=True,
                )
                if st.button("이 예시 선택", key=f"gallery_showcase_apply_{landform_key}", use_container_width=True):
                    queue_gallery_showcase_preset(st.session_state, preset)
                    st.rerun()

                if build_lab_showcase_preset(category, landform_key) is not None:
                    if st.button("Lab 수업으로 열기", key=f"gallery_showcase_lab_{landform_key}", use_container_width=True):
                        if not route_to_lab_showcase(category, landform_key):
                            st.warning("이 지형은 아직 Lab 모범사례와 연결되지 않았습니다.")
                else:
                    st.caption("대표 지형부터 Lab 수업 흐름과 연결합니다.")
