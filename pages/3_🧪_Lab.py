"""
?? Geo-Lab Lab ???
?? ?? ??? ????? ???? ???? ??? ?????.
"""
"""
Geo-Lab Lab page.
지형 형성 과정을 직접 조절하며 변화 방향을 읽는 실험실 화면입니다.
"""
import streamlit as st
import streamlit.components.v1 as components
import numpy as np
import sys
import os
from pathlib import Path

STUDENT_MODE_LABEL = "학생 단순모드"
TEACHER_MODE_LABEL = "교사 상세모드"
SCENARIO_MOUNTAIN_RIVER = "산지/하천"
SCENARIO_GLACIAL_COASTAL = "빙하/해안"
SCENARIO_ARID_SPECIAL = "건조/특수"
SCENARIO_ADDITIONAL_LAB = "추가 지형"

LAB_OVERLAY_OPTIONS = {
    "자동": None,
    "끄기": "off",
    "구조 작용": "tectonic",
    "침식": "erosion",
    "퇴적": "deposition",
    "이동": "transport",
    "지형 변화": "change",
}
LAB_OVERLAY_LABELS = {
    "tectonic": "구조 작용",
    "erosion": "침식",
    "deposition": "퇴적",
    "transport": "이동",
    "change": "지형 변화",
}

# ?? ???? ?? ??
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.grid import WorldGrid
from engine.script_engine import ScriptExecutor
from app.components.renderer import render_terrain_plotly
from app.components.animation_renderer import (
    create_history_animation_embed_html,
    create_history_animation_figure,
    create_history_gif_bytes,
)
from app.utils.lab_model import (
    apply_lab_theory_example,
    build_lab_stage_history,
    configure_lab_scenario,
    create_lab_simple_lem,
    describe_lab_process_stage,
    get_lab_scenario_config,
    get_lab_playback_guidance,
    get_lab_teaching_notes,
)
from app.services.terrain_lab_catalog import (
    GROUP_LABELS_KO,
    build_lab_experiment_design_summary,
    derive_lab_parameter_multipliers,
    list_additional_lab_scenarios,
    process_factor_definitions_for_scenario,
    scenario_slider_defaults,
)
from app.theory import interpret_theory_text
from app.utils.mode_helpers import build_provenance_panel, get_lab_mode_context

# ?? ?? import
try:
    from engine.lem.climate import ClimateSystem
    from engine.lem.human import HumanActivity
    from engine.lem.visualization import LEMVisualizer
    LEM_EXTENSIONS = True
except ImportError:
    LEM_EXTENSIONS = False

# ========== Page Config ==========
st.set_page_config(page_title="🧪 Lab", page_icon="🧪", layout="wide")

# ========== CSS ?? ==========
def load_css():
    css_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "style.css")
    if os.path.exists(css_path):
        with open(css_path, 'r', encoding='utf-8') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

load_css()
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PAGES_DIR = PROJECT_ROOT / "pages"


def resolve_page_path(fragment: str) -> str | None:
    page_path = next((path for path in PAGES_DIR.iterdir() if fragment in path.name), None)
    if page_path is None:
        return None
    return page_path.relative_to(PROJECT_ROOT).as_posix()


HIGHER_ED_PAGE = resolve_page_path("Higher_Ed.py")


def render_higher_ed_lab_hint(sidebar: bool = False) -> None:
    target = st.sidebar if sidebar else st
    target.info(
        "연구용 비교, 심화 설명, 실제 DEM 검증이 필요하면 "
        "현재 Lab보다 Higher Ed 흐름으로 넘어가는 편이 더 적합합니다."
    )
    if HIGHER_ED_PAGE and hasattr(target, "page_link"):
        target.page_link(HIGHER_ED_PAGE, label="Higher Ed로 이동", width="stretch")

# ========== ?? ??? ==========
def resolve_lab_overlay(stage_context: dict | None, selection_label: str = "자동") -> tuple[str | None, str]:
    if selection_label == "끄기":
        return None, "끄기"
    if selection_label == "자동":
        overlay_type = (stage_context or {}).get("overlay_type")
        return overlay_type, LAB_OVERLAY_LABELS.get(overlay_type, "자동")
    overlay_type = LAB_OVERLAY_OPTIONS.get(selection_label)
    return overlay_type, selection_label


def render_lab_animation_preview(
    figure,
    *,
    frame_duration_ms: int,
    transition_duration_ms: int,
    height: int,
    fallback_key: str,
) -> None:
    if figure is None:
        return

    embed_html = create_history_animation_embed_html(
        figure,
        frame_duration_ms=frame_duration_ms,
        transition_duration_ms=transition_duration_ms,
        height=height,
    )
    if embed_html:
        components.html(embed_html, height=height + 60, scrolling=False)
        return

    st.plotly_chart(
        figure,
        width="stretch",
        key=fallback_key,
        config={"scrollZoom": False, "displayModeBar": True},
    )

if 'lem_history' not in st.session_state:
    st.session_state['lem_history'] = []
if 'lem_stats_history' not in st.session_state:
    st.session_state['lem_stats_history'] = []
if 'lem_process_history' not in st.session_state:
    st.session_state['lem_process_history'] = []
if 'lem_stage_history' not in st.session_state:
    st.session_state['lem_stage_history'] = []

pending_gallery_preset = st.session_state.pop("gallery_lab_preset", None)
if pending_gallery_preset:
    st.session_state["lab_user_mode"] = pending_gallery_preset.get("user_mode", STUDENT_MODE_LABEL)
    st.session_state["lab_scenario_category"] = pending_gallery_preset.get("scenario_category", SCENARIO_MOUNTAIN_RIVER)
    st.session_state["lab_selected_landform"] = pending_gallery_preset.get("selected_landform")
    st.session_state["lab_speed_mode"] = pending_gallery_preset.get("speed_mode", "균형")
    st.session_state["lab_force_level"] = pending_gallery_preset.get("force_level", 60)
    st.session_state["lab_pending_autorun"] = bool(pending_gallery_preset.get("auto_run", False))
    st.session_state["lab_pending_showcase_title"] = pending_gallery_preset.get("showcase_title", "모범 사례")

st.sidebar.markdown("### 실험 모드 선택")
user_mode = st.sidebar.radio(
    "모드",
    [STUDENT_MODE_LABEL, TEACHER_MODE_LABEL],
    horizontal=True,
    key="lab_user_mode",
)
student_mode = user_mode == STUDENT_MODE_LABEL
if student_mode:
    st.session_state["lab_dev_mode"] = False
    st.session_state["lab_theory_applied"] = None

# ========== Parameter Mapper (Easy Mode) ==========
class ParameterMapper:
    """수업용 0-100 슬라이더 값을 실제 모형 파라미터로 변환한다."""
    
    @staticmethod
    def map_erosion(value): # 0-100
        # K: 0.00001 ~ 0.001
        return 0.00001 + (value / 100) * (0.001 - 0.00001)

    @staticmethod
    def map_diffusion(value): # 0-100
        # D: 0.001 ~ 0.1
        return 0.001 + (value / 100) * (0.1 - 0.001)
    
    @staticmethod
    def map_uplift(value): # 0-100
        # U: 0.0 ~ 0.001
        return (value / 100) * 0.001

# ========== UI Header ==========
dev_mode = False

col_hd1, col_hd2 = st.columns([3, 1])
with col_hd1:
    st.markdown("""
    <div style='margin-bottom: 0.5rem;'>
        <h1 style='font-size: 2.2rem; margin-bottom: 0;'>🧪 Geo-Lab Laboratory</h1>
        <p style='color: #64748B; font-size: 1rem;'>지형 형성 과정을 직접 조절하며 변화 방향을 읽는 실험실입니다.</p>
    </div>
    """, unsafe_allow_html=True)

with col_hd2:
    if student_mode:
        st.caption("학생이 처음 보는 장면에서도 변화 이유를 읽도록 단순화한 보기입니다.")
    else:
        st.caption("교사가 설명과 비교를 붙이기 좋은 상세 시연 보기입니다.")
if student_mode:
    st.markdown(
        """
        <div class="mode-banner mode-student">
            <div class="mode-title">학생 단순모드</div>
            <div class="mode-copy">핵심 과정과 변화 방향을 먼저 읽도록 단순화했습니다.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        """
        <div class="mode-banner mode-teacher">
            <div class="mode-title">교사 상세모드</div>
            <div class="mode-copy">수업 설명, 비교 시연, 모범 사례 확인에 맞춘 상세 보기입니다.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

mode_context = get_lab_mode_context(
    student_mode=student_mode,
    theory_applied=st.session_state.get("lab_theory_applied"),
)
st.markdown(
    build_provenance_panel(
        mode_context["title"],
        mode_context["summary"],
        mode_context["badges"],
        mode_context["notes"],
    ),
    unsafe_allow_html=True,
)

# ========== Sidebar (Controls) ==========
st.sidebar.markdown("### 실험 조건 설정")

# 1. ?쒕굹由ъ삤 ?좏깮 (吏곴???洹몃９??
scenario_category = st.sidebar.radio(
    "시나리오",
    [SCENARIO_MOUNTAIN_RIVER, SCENARIO_GLACIAL_COASTAL, SCENARIO_ARID_SPECIAL, SCENARIO_ADDITIONAL_LAB],
    horizontal=True,
    label_visibility="collapsed",
    key="lab_scenario_category",
)

PRESETS = {
    SCENARIO_MOUNTAIN_RIVER: ["V자곡 (하천침식)", "선상지 (급경사)", "삼각주 (하구)", "곡류 (사행천)", "습곡 산지 (구조운동)"],
    SCENARIO_GLACIAL_COASTAL: ["U자곡 (빙하침식)", "피오르 (해수면상승)", "해안단구 (융기해안)", "해식애 (파랑침식)"],
    SCENARIO_ARID_SPECIAL: ["바르한 (사구)", "카르스트 (용해)", "화산 (분출)"],
}

ADDITIONAL_LAB_SCENARIOS = list_additional_lab_scenarios()
ADDITIONAL_LAB_LABEL_TO_ID = {
    f"{scenario.title_ko} ({GROUP_LABELS_KO.get(scenario.group, scenario.group)})": scenario.landform_id
    for scenario in ADDITIONAL_LAB_SCENARIOS
}
PRESETS[SCENARIO_ADDITIONAL_LAB] = list(ADDITIONAL_LAB_LABEL_TO_ID)

mountain_category = next(iter(PRESETS))
if "습곡 산지 (구조운동)" not in PRESETS[mountain_category]:
    PRESETS[mountain_category].append("습곡 산지 (구조운동)")

if scenario_category not in PRESETS:
    scenario_category = SCENARIO_MOUNTAIN_RIVER
    st.session_state["lab_scenario_category"] = scenario_category

if st.session_state.get("lab_selected_landform") not in PRESETS[scenario_category]:
    st.session_state["lab_selected_landform"] = PRESETS[scenario_category][0]

selected_landform = st.sidebar.selectbox(
    "대표 지형",
    PRESETS[scenario_category],
    key="lab_selected_landform",
)
selected_catalog_landform_id = ADDITIONAL_LAB_LABEL_TO_ID.get(selected_landform)
selected_catalog_scenario = next(
    (
        scenario
        for scenario in ADDITIONAL_LAB_SCENARIOS
        if scenario.landform_id == selected_catalog_landform_id
    ),
    None,
)

with st.sidebar.expander("🎓 Higher Ed / 연구·심화 흐름", expanded=False):
    st.caption("연구·심화 설명이 필요한 경우 이 Lab보다 Higher Ed 흐름으로 넘어가는 편이 낫습니다.")
    render_higher_ed_lab_hint(sidebar=True)

if not student_mode:
    with st.sidebar.expander("🧰 고급 실험자 옵션", expanded=False):
        if "lab_dev_mode" not in st.session_state:
            st.session_state["lab_dev_mode"] = False
        st.toggle("개발자 모드", key="lab_dev_mode")
        st.caption("일반 수업 흐름에는 숨기고, 고급 조정이 필요할 때만 여는 옵션입니다.")
        if st.session_state.get("lab_dev_mode", False):
            st.warning("고급 파라미터는 수업용 시연의 안정성을 낮출 수 있으니 주의하세요.")
dev_mode = bool(st.session_state.get("lab_dev_mode", False)) if not student_mode else False

st.sidebar.markdown("---")

catalog_factor_values: dict[str, float] = {}
catalog_parameter_multipliers: dict[str, float] = {}
catalog_design_summary: dict[str, object] = {}
if selected_catalog_scenario is not None:
    st.sidebar.markdown("### 카탈로그 요인")
    st.sidebar.caption(
        f"{selected_catalog_scenario.title_ko} | "
        f"{GROUP_LABELS_KO.get(selected_catalog_scenario.group, selected_catalog_scenario.group)}"
    )
    with st.sidebar.expander("형성 단계", expanded=student_mode):
        for index, step in enumerate(selected_catalog_scenario.formation_steps_ko, start=1):
            st.markdown(f"{index}. {step}")

    defaults = scenario_slider_defaults(selected_catalog_scenario.landform_id)
    with st.sidebar.expander("조절 요인", expanded=not student_mode):
        for definition in process_factor_definitions_for_scenario(selected_catalog_scenario.landform_id):
            value = st.slider(
                definition.label_ko,
                int(definition.min_value),
                int(definition.max_value),
                int(defaults.get(definition.factor_id, definition.default_value)),
                step=5,
                key=f"lab_catalog_factor_{selected_catalog_scenario.landform_id}_{definition.factor_id}",
                help=definition.description_ko,
            )
            catalog_factor_values[definition.factor_id] = float(value)
    catalog_parameter_multipliers = derive_lab_parameter_multipliers(
        selected_catalog_scenario.landform_id,
        catalog_factor_values,
    )
    catalog_design_summary = build_lab_experiment_design_summary(
        selected_catalog_scenario.landform_id,
        catalog_factor_values,
        catalog_parameter_multipliers,
    )
    with st.sidebar.expander("실험 설계 요약", expanded=student_mode):
        st.markdown(f"**{catalog_design_summary.get('title', selected_catalog_scenario.title_ko)}**")
        st.caption(
            f"{catalog_design_summary.get('group', '')} | "
            f"{catalog_design_summary.get('simulation_family', selected_catalog_scenario.simulation_family)}"
        )
        factor_lines = catalog_design_summary.get("factor_lines") or ()
        if factor_lines:
            st.markdown("요인값")
            for line in factor_lines:
                st.caption(str(line))
        multiplier_lines = catalog_design_summary.get("multiplier_lines") or ()
        if multiplier_lines:
            st.markdown("모형 반영")
            for line in multiplier_lines:
                st.caption(str(line))

# 2. 형성 파라미터
st.sidebar.markdown("### 지형 형성 강도")

# 기본 플래그 초기화
enable_isostasy = False
enable_exner = False
enable_slope_stability = False
enable_karst = False
enable_volcanic = False

if student_mode:
    speed_mode = st.sidebar.radio(
        "재생 속도",
        ["느리게", "균형", "빠르게"],
        horizontal=True,
        key="lab_speed_mode",
    )
    force_slider_kwargs = {}
    if "lab_force_level" not in st.session_state:
        force_slider_kwargs["value"] = 50
    force_level = st.sidebar.slider(
        "변화가 얼마나 뚜렷하게 보이게 할지",
        0,
        100,
        step=5,
        help="침식, 퇴적, 융기 같은 과정이 얼마나 강하게 보일지 조절합니다.",
        key="lab_force_level",
        **force_slider_kwargs,
    )

    p_erosion = int(min(100, 35 + force_level * 0.55))
    p_diffusion = int(min(100, 20 + force_level * 0.45))
    p_uplift = int(min(100, 10 + force_level * 0.40))

    K = ParameterMapper.map_erosion(p_erosion)
    D = ParameterMapper.map_diffusion(p_diffusion)
    U = ParameterMapper.map_uplift(p_uplift)

    speed_map = {
        "느리게": (60, 20000),
        "균형": (80, 35000),
        "빠르게": (100, 50000),
    }
    lem_grid_size, total_time = speed_map[speed_mode]
    st.sidebar.caption(
        f"현재 설정: 해상도 {lem_grid_size}, 전체 시간 {total_time:,}년"
    )

elif not dev_mode:
    # Easy Mode Sliders (0-100)
    p_erosion = st.sidebar.slider("침식 강도", 0, 100, 50, help="하천과 물이 지형을 얼마나 빠르게 깎는지")
    p_diffusion = st.sidebar.slider("사면 이동 강도", 0, 100, 30, help="무너짐과 확산이 얼마나 빠르게 일어나는지")
    p_uplift = st.sidebar.slider("융기 강도", 0, 100, 20, help="지형이 얼마나 빠르게 높아지는지")

    # Internal Mapping
    K = ParameterMapper.map_erosion(p_erosion)
    D = ParameterMapper.map_diffusion(p_diffusion)
    U = ParameterMapper.map_uplift(p_uplift)

    # Keep teacher defaults below the developer preset so classroom demos stay responsive.
    lem_grid_size = 80
    total_time = 35000
    st.sidebar.caption(f"현재 설정: 해상도 {lem_grid_size}, 전체 시간 {total_time:,}년")

else:
    # Advanced Params (Direct access)
    st.sidebar.info("고급 수치는 직접 수업용 설명보다 실험 조정이 목적입니다.")
    K = st.sidebar.number_input("침식률 (K)", 1e-6, 1e-2, 0.0001, format="%.6f")
    D = st.sidebar.number_input("확산률 (D)", 1e-4, 1.0, 0.01, format="%.4f")
    U = st.sidebar.number_input("융기율 (U)", 0.0, 1e-2, 0.0003, format="%.5f")
    lem_grid_size = st.sidebar.slider("해상도", 50, 150, 100)
    total_time = st.sidebar.slider("전체 시간 (년)", 10000, 500000, 50000)
    
    # Advanced Physics Expander
    with st.sidebar.expander("고급 물리 옵션", expanded=False):
        st.markdown("기본 수업용 흐름보다 더 세밀한 물리 실험이 필요할 때만 여세요.")
        enable_isostasy = st.checkbox("지각 평형 (Isostasy)", value=False, help="하중 변화에 따른 지각 반응")
        enable_exner = st.checkbox("Exner 퇴적 방정식", value=False, help="퇴적물 보존을 더 직접적으로 반영")
        enable_slope_stability = st.checkbox("사면 안정성", value=False, help="급경사 붕괴 반응")
        enable_karst = st.checkbox("카르스트 용해", value=False, help="석회암 용식 작용")
        
        if enable_karst:
             st.info("카르스트 용해는 용식 지형 계열에서 특히 의미 있게 보입니다.")

# 3. Action Buttons
st.sidebar.markdown("---")
showcase_autorun = bool(st.session_state.pop("lab_pending_autorun", False))
showcase_title = st.session_state.pop("lab_pending_showcase_title", None)
if showcase_title:
    st.sidebar.caption(f"선택된 preset: {showcase_title}")
col_act1, col_act2 = st.sidebar.columns(2)
with col_act1:
    btn_reset = st.button("초기화", width="stretch")
with col_act2:
    btn_run = st.button("실행", type="primary", width="stretch")
if showcase_autorun:
    btn_run = True

if btn_reset:
    for key in ("lem_history", "lem_times", "lem_stats_history", "lem_process_history", "lem_stage_history", "lem_obj", "lem_export_gif", "lem_current_frame", "lem_visual_context", "lem_selected_landform", "lem_frame_slider_manual", "lem_teacher_gif_bytes", "lem_teacher_overlay_choice", "lem_autoplay", "lem_catalog_context"):
        st.session_state.pop(key, None)
    st.rerun()



# ========== Theory-driven Modeling ==========
if "lab_theory_result" not in st.session_state:
    st.session_state["lab_theory_result"] = None
if "lab_theory_selected" not in st.session_state:
    st.session_state["lab_theory_selected"] = None
if "lab_theory_applied" not in st.session_state:
    st.session_state["lab_theory_applied"] = None
if "lab_theory_text" not in st.session_state:
    st.session_state["lab_theory_text"] = ""


def fill_lab_theory_example() -> None:
    apply_lab_theory_example(st.session_state)


if not student_mode:
    st.markdown("---")
    with st.expander("🎓 심화 가설 실험 (Higher Ed 권장)", expanded=False):
        st.caption(
            "자연어 설명을 바탕으로 가설 시나리오를 재구성하는 실험입니다. "
            "수업용 본문보다는 심화 실험이나 연구 흐름에서 사용하는 편이 적합합니다."
        )
        render_higher_ed_lab_hint()

        theory_text = st.text_area(
            "가설 문장",
            key="lab_theory_text",
            height=120,
            placeholder=(
                "예) 지반이 천천히 융기하고 강의 하방 침식이 강해지면서 깊은 V자곡이 발달한다. "
                "산록에서는 운반물이 쌓이며 선상지가 함께 형성된다."
            ),
        )

        tcol1, tcol2, tcol3 = st.columns(3)
        if tcol1.button("가설 해석", key="lab_theory_parse", width="stretch"):
            base_params = {
                "K": float(K),
                "D": float(D),
                "U": float(U),
                "grid_size": int(lem_grid_size),
                "total_time": int(total_time),
            }
            st.session_state["lab_theory_result"] = interpret_theory_text(theory_text, base_params=base_params)
            scenarios = st.session_state["lab_theory_result"].scenarios
            st.session_state["lab_theory_selected"] = scenarios[0].scenario_id if scenarios else None

        if tcol2.button("적용 해제", key="lab_theory_clear_apply", width="stretch"):
            st.session_state["lab_theory_applied"] = None

        tcol3.button(
            "예시 문장",
            key="lab_theory_fill_example",
            width="stretch",
            on_click=fill_lab_theory_example,
        )

        theory_result = st.session_state.get("lab_theory_result")
        if theory_result:
            st.info(theory_result.summary)

            e_col, u_col = st.columns(2)
            with e_col:
                st.markdown("#### 해석 근거")
                for hint in theory_result.evidence_hints:
                    st.markdown(f"- {hint}")
            with u_col:
                st.markdown("#### 불확실한 점")
                for note in theory_result.uncertainty_notes:
                    st.markdown(f"- {note}")

            scenario_ids = [s.scenario_id for s in theory_result.scenarios]
            scenario_map = {s.scenario_id: s for s in theory_result.scenarios}
            if scenario_ids:
                if st.session_state["lab_theory_selected"] not in scenario_ids:
                    st.session_state["lab_theory_selected"] = scenario_ids[0]

                selected_theory_scenario_id = st.selectbox(
                    "추천 시나리오",
                    scenario_ids,
                    format_func=lambda sid: (
                        f"{scenario_map[sid].title} | 신뢰도 {scenario_map[sid].confidence * 100:.0f}%"
                    ),
                    key="lab_theory_selected",
                )
                selected_theory_scenario = scenario_map[selected_theory_scenario_id]

                p = selected_theory_scenario.parameters
                p_cols = st.columns(5)
                p_cols[0].metric("K", f"{p['K']:.6f}")
                p_cols[1].metric("D", f"{p['D']:.4f}")
                p_cols[2].metric("U", f"{p['U']:.6f}")
                p_cols[3].metric("해상도", f"{int(p['grid_size'])}")
                p_cols[4].metric("시간", f"{int(p['total_time']):,}년")
                st.caption(selected_theory_scenario.narrative)

                if st.button("이 시나리오를 현재 실험에 적용", key="lab_theory_apply"): 
                    st.session_state["lab_theory_applied"] = {
                        "scenario_id": selected_theory_scenario.scenario_id,
                        "title": selected_theory_scenario.title,
                        "confidence": selected_theory_scenario.confidence,
                        "parameters": selected_theory_scenario.parameters,
                    }
                    st.success(f"적용 완료: {selected_theory_scenario.title}")


# ========== Main Area ==========

# ?듯빀 酉? 3D 酉곗뼱媛 媛??以묒슂??# 寃곌낵媛 ?덉쑝硫?寃곌낵 酉? ?놁쑝硫?珥덇린 ?덈궡 酉?
run_K = float(K)
run_D = float(D)
run_U = float(U)
run_grid_size = int(lem_grid_size)
run_total_time = int(total_time)

theory_applied = st.session_state.get("lab_theory_applied")
if theory_applied and theory_applied.get("parameters"):
    tp = theory_applied["parameters"]
    run_K = float(tp["K"])
    run_D = float(tp["D"])
    run_U = float(tp["U"])
    run_grid_size = int(tp["grid_size"])
    run_total_time = int(tp["total_time"])
    st.warning(
        f"적용된 가설 시나리오: {theory_applied['title']} "
        f"(신뢰도 {theory_applied['confidence'] * 100:.0f}%)"
    )

current_scenario_config = get_lab_scenario_config(selected_landform)
current_teaching_notes = get_lab_teaching_notes(selected_landform)
playback_copy = get_lab_playback_guidance(student_mode)
if selected_catalog_scenario is not None:
    catalog_steps = "\n".join(
        f"{index}. {step}"
        for index, step in enumerate(selected_catalog_scenario.formation_steps_ko, start=1)
    )
    st.info(
        f"카탈로그 연결: {selected_catalog_scenario.title_ko}\n\n"
        f"{catalog_steps}\n\n"
        "왼쪽의 카탈로그 요인 슬라이더는 이번 실행의 물리 계수에 반영됩니다."
    )
if student_mode:
    with st.expander("\uc774 \uc2e4\ud5d8\uc5d0\uc11c \ubcfc \uac83", expanded=True):
        st.markdown(f"**\ud575\uc2ec \uac1c\ub150**  \\n{current_teaching_notes['concept']}")
        st.markdown(f"**\uad00\ucc30 \ud3ec\uc778\ud2b8**  \\n{current_teaching_notes['focus']}")
        if current_teaching_notes.get("world_case"):
            st.caption(
                f"대표 세계 사례: {current_teaching_notes['world_case']}"
                f" ({current_teaching_notes.get('world_location', '')})"
            )
else:
    st.markdown("### \uc218\uc5c5 \uc6b4\uc601 \ud3ec\uc778\ud2b8")
    teach_col1, teach_col2, teach_col3 = st.columns(3)
    teach_col1.markdown(f"**\ud575\uc2ec \uac1c\ub150**  \\n{current_teaching_notes['concept']}")
    teach_col2.markdown(f"**\uc2dc\uc5f0 \ud3ec\uc778\ud2b8**  \\n{current_teaching_notes['focus']}")
    teach_col3.markdown(f"**\uc9c8\ubb38 \uc608\uc2dc**  \\n{current_teaching_notes['question']}")
    st.caption(f"\uc218\uc5c5 takeaway: {current_teaching_notes['takeaway']}")
    if current_teaching_notes.get("world_case"):
        st.caption(
            f"대표 세계 사례: {current_teaching_notes['world_case']}"
            f" ({current_teaching_notes.get('world_location', '')})"
        )
visual_context = st.session_state.get(
    "lem_visual_context",
    {
        "landform_type": current_scenario_config.landform_type,
        "detailed_type": current_scenario_config.detailed_type,
    },
)
visual_landform_type = visual_context.get("landform_type", current_scenario_config.landform_type)
visual_detailed_type = visual_context.get("detailed_type", current_scenario_config.detailed_type)
active_landform = st.session_state.get("lem_selected_landform", selected_landform)

if btn_run:
    with st.spinner("지형을 생성하고 물리 법칙을 적용하는 중입니다..."):
        try:
            # 1. LEM 초기화
            if enable_karst:
                # 카르스트 지형은 용식이 드러나도록 침식 계수를 보정한다.
                run_K = max(run_K, 0.0005)
            scenario_config = current_scenario_config
            lem = create_lab_simple_lem(
                grid_size=run_grid_size,
                K=run_K,
                D=run_D,
                U=run_U,
                enable_isostasy=enable_isostasy,
                enable_karst=enable_karst,
                enable_exner=enable_exner,
                enable_slope_stability=enable_slope_stability,
            )

            # 2. 시나리오별 초기 지형 설정
            scenario_config = configure_lab_scenario(
                lem,
                selected_landform=selected_landform,
                grid_size=run_grid_size,
            )
            if selected_catalog_scenario is not None and catalog_parameter_multipliers:
                lem.K *= catalog_parameter_multipliers.get("k_scale", 1.0)
                lem.D *= catalog_parameter_multipliers.get("d_scale", 1.0)
                lem.U *= catalog_parameter_multipliers.get("u_scale", 1.0)
                lem.Vs *= catalog_parameter_multipliers.get("deposition_scale", 1.0)
                lem.precipitation *= catalog_parameter_multipliers.get("water_scale", 1.0)
                lem.Kg *= catalog_parameter_multipliers.get("glacial_scale", 1.0)
                lem.Km *= catalog_parameter_multipliers.get("marine_scale", 1.0)
                lem.Kk *= catalog_parameter_multipliers.get("karst_scale", 1.0)
                lem.volcanic_rate *= catalog_parameter_multipliers.get("volcanic_scale", 1.0)

            # 3. 시뮬레이션 실행
            history, times = lem.run(total_time=run_total_time, dt=100.0, verbose=False)
            process_history = getattr(lem, 'process_history', [])
            stage_history = build_lab_stage_history(selected_landform, getattr(lem, 'stats_history', []), process_history)
            
            # 4. 결과 저장
            st.session_state['lem_history'] = history
            st.session_state['lem_times'] = times
            st.session_state['lem_stats_history'] = getattr(lem, 'stats_history', [])
            st.session_state['lem_process_history'] = process_history
            st.session_state['lem_stage_history'] = stage_history
            st.session_state['lem_obj'] = lem # Store object for map retrieval
            st.session_state['lem_visual_context'] = {
                'landform_type': scenario_config.landform_type,
                'detailed_type': scenario_config.detailed_type,
            }
            if selected_catalog_scenario is not None:
                st.session_state['lem_catalog_context'] = {
                    'landform_id': selected_catalog_scenario.landform_id,
                    'title_ko': selected_catalog_scenario.title_ko,
                    'group': selected_catalog_scenario.group,
                    'formation_steps_ko': list(selected_catalog_scenario.formation_steps_ko),
                    'factor_values': dict(catalog_factor_values),
                    'parameter_multipliers': dict(catalog_parameter_multipliers),
                    'design_summary': dict(catalog_design_summary),
                }
            else:
                st.session_state.pop('lem_catalog_context', None)
            st.session_state['lem_selected_landform'] = selected_landform
            st.session_state.pop('lem_teacher_gif_bytes', None)
            
            st.success("지형 생성과 과정 계산이 완료되었습니다.")
            
        except Exception as e:
            st.error(f"실행 중 오류가 발생했습니다: {e}")

# Visualization Area
if st.session_state['lem_history']:
    history = st.session_state['lem_history']
    times = st.session_state.get('lem_times', list(range(len(history))))
    stats_history = st.session_state.get('lem_stats_history', [])
    process_history = st.session_state.get('lem_process_history', [])
    stage_history = st.session_state.get('lem_stage_history', [])
    catalog_context = st.session_state.get('lem_catalog_context')
    max_frame = len(history) - 1
    cur_frame = max_frame

    student_landform_type = visual_landform_type
    student_detailed_type = visual_detailed_type
    if catalog_context:
        with st.expander("카탈로그 요인 적용값", expanded=False):
            st.markdown(f"**{catalog_context.get('title_ko', '')}**")
            design_summary = catalog_context.get("design_summary") or {}
            if design_summary:
                st.caption(
                    f"{design_summary.get('group', '')} | "
                    f"{design_summary.get('simulation_family', '')}"
                )
            steps = catalog_context.get("formation_steps_ko") or []
            if steps:
                st.markdown("형성 단계: " + " → ".join(str(step) for step in steps))
            factor_lines = design_summary.get("factor_lines") or ()
            if factor_lines:
                st.markdown("요인값: " + " · ".join(str(line) for line in factor_lines))
            multiplier_lines = design_summary.get("multiplier_lines") or ()
            if multiplier_lines:
                st.markdown("모형 반영: " + " · ".join(str(line) for line in multiplier_lines))
    st.caption(playback_copy["preview_caption"])

    if student_mode:
        st.markdown("### 부드러운 형성 애니메이션")
        st.caption("학생이 지형 변화의 방향을 먼저 읽도록, 저장된 장면 사이를 부드럽게 이어서 보여줍니다.")

        smooth_steps = 6 if len(history) <= 10 else 4
        st.markdown(f"#### {playback_copy['preview_heading']}")
        fig_anim = create_history_animation_figure(
            history=history,
            times=times,
            process_history=process_history,
            stage_history=stage_history,
            title="학생용 지형 애니메이션",
            landform_type=student_landform_type,
            detailed_type=student_detailed_type,
            render_style="terrain",
            interpolation_steps=smooth_steps,
            camera_motion="auto",
            cinematic_zoom=1.08,
            frame_duration_ms=80,
            transition_duration_ms=70,
        )
        render_lab_animation_preview(
            fig_anim,
            frame_duration_ms=80,
            transition_duration_ms=70,
            height=760,
            fallback_key="lem_student_animation",
        )

        st.caption("애니메이션으로 전체 흐름을 본 뒤, 아래 핵심 장면에서 우세 작용을 다시 확인해 보세요.")
        st.markdown(f"#### {playback_copy['comparison_heading']}")
        st.caption(playback_copy["comparison_caption"])
        focus_frame = st.slider(
            "핵심 장면",
            0,
            max_frame,
            max_frame,
            key="lem_focus_frame",
        )
        cur_frame = focus_frame
        progress = 0.0 if max_frame <= 0 else (cur_frame / max_frame)
        current_stats = stats_history[cur_frame] if cur_frame < len(stats_history) else None
        if cur_frame < len(stage_history):
            stage_context = stage_history[cur_frame]
        else:
            stage_context = describe_lab_process_stage(active_landform, progress, current_stats)
        student_overlay_type, student_overlay_label = resolve_lab_overlay(stage_context, "자동")
        student_stage_index = int(stage_context.get("stage_index", 0)) + 1
        student_dominant = stage_context.get("dominant_processes", [])
        student_dominant_label = str(student_dominant[0]["label"]) if student_dominant else "주요 과정 없음"
        if cur_frame > 0:
            step_delta = history[cur_frame] - history[cur_frame - 1]
        else:
            step_delta = history[cur_frame] - history[0]
        avg_step_change = float(np.mean(np.abs(step_delta)))
        peak_step_change = float(np.max(np.abs(step_delta)))
        stage_badges = [
            {"label": f"장면 {cur_frame + 1}/{len(history)}", "tone": "education"},
            {"label": f"{times[cur_frame]:,.0f} yr", "tone": "hybrid"},
            {"label": f"단계 {student_stage_index}/4", "tone": "education"},
            {"label": f"오버레이 {student_overlay_label}", "tone": "model"},
            {"label": f"우세 작용 {student_dominant_label}", "tone": "hybrid"},
        ]
        student_panel_lines = [
            f"핵심 해석: {stage_context['summary']}",
            f"관찰 포인트: {stage_context['focus']}",
        ]
        if stage_context.get("classroom_goal"):
            student_panel_lines.append(f"교과 목표: {stage_context['classroom_goal']}")
        if stage_context.get("world_case_title"):
            student_panel_lines.append(
                f"대표 사례: {stage_context['world_case_title']} ({stage_context.get('world_case_location', '')})"
            )
        student_panel_lines.extend(
            [
                f"직전 장면 대비 평균 절대 변화 {avg_step_change:.2f} m, 최대 {peak_step_change:.2f} m",
                f"관찰 질문: {stage_context['question']}",
            ]
        )
        st.markdown(
            build_provenance_panel(
                stage_context["title"],
                stage_context["caption"],
                stage_badges,
                student_panel_lines,
            ),
            unsafe_allow_html=True,
        )

        student_info_lines = [
            "과정 순서: "
            f"{stage_context['process_order']}",
            "우세 작용: "
            f"{stage_context['dominant_summary']}",
            "내적·외적 작용 구성: "
            f"{stage_context['balance_summary']}",
        ]
        if stage_context.get("teacher_note"):
            student_info_lines.extend(
                [
                    "설명 포인트: "
                    f"{stage_context['teacher_note']}",
                ]
            )
        st.info("\n\n".join(student_info_lines))

        delta = history[-1] - history[0]
        student_process_fields = process_history[cur_frame] if cur_frame < len(process_history) else None
        student_overlay_type, student_overlay_label = resolve_lab_overlay(stage_context, "자동")
        col_story1, col_story2, col_story3 = st.columns(3)
        col_story1.metric("전체 경과", f"{times[-1]:,.0f} yr")
        col_story2.metric("평균 지형 변화", f"{float(np.mean(delta)):+.1f}m")
        col_story3.metric("최대 지형 변화", f"{float(np.max(delta)):+.1f}m")

        st.markdown(f"#### 현재 장면 ({times[cur_frame]:,.0f} yr)")
        fig_focus = render_terrain_plotly(
            history[cur_frame],
            "현재 장면",
            add_water=True,
            water_level=0,
            landform_type=student_landform_type,
            detailed_type=student_detailed_type,
            process_fields=student_process_fields,
            overlay_type=student_overlay_type,
        )
        st.plotly_chart(fig_focus, width="stretch", key="lem_focus_view")
        if student_overlay_type:
            overlay_caption = stage_context.get("overlay_caption")
            if overlay_caption:
                st.caption(f"현재 보이는 오버레이: {student_overlay_label} | {overlay_caption}")
            else:
                st.caption(f"현재 보이는 오버레이: {student_overlay_label}")
    else:
        with st.container():
            st.caption("교사 모드는 브라우저에서 직접 재생되는 3D 미리보기와 고정 프레임 비교를 함께 사용하도록 구성했습니다.")

            st.markdown(f"#### {playback_copy['comparison_heading']}")
            st.caption(playback_copy["comparison_caption"])
            teacher_overlay_choice = st.selectbox(
                "오버레이 선택",
                list(LAB_OVERLAY_OPTIONS.keys()),
                index=0,
                key="lem_teacher_overlay_choice",
            )
            cur_frame = st.slider(
                "프레임",
                0,
                max_frame,
                st.session_state.get('lem_current_frame', max_frame),
                key="lem_frame_slider_manual",
            )
            st.session_state['lem_current_frame'] = cur_frame
            progress = 0.0 if max_frame <= 0 else (cur_frame / max_frame)
            current_stats = stats_history[cur_frame] if cur_frame < len(stats_history) else None
            if cur_frame < len(stage_history):
                teacher_stage = stage_history[cur_frame]
            else:
                teacher_stage = describe_lab_process_stage(active_landform, progress, current_stats)
            teacher_process_fields = process_history[cur_frame] if cur_frame < len(process_history) else None
            teacher_overlay_type, teacher_overlay_label = resolve_lab_overlay(teacher_stage, teacher_overlay_choice)

            gif_bytes = st.session_state.get('lem_teacher_gif_bytes')
            st.markdown("### 지형 애니메이션 미리보기")
            st.markdown(f"#### {playback_copy['preview_heading']}")
            teacher_anim = create_history_animation_figure(
                history=history,
                times=times,
                process_history=process_history,
                stage_history=stage_history,
                title="교사용 지형 애니메이션",
                landform_type=visual_landform_type,
                detailed_type=visual_detailed_type,
                render_style="terrain",
                interpolation_steps=1,
                camera_motion="auto",
                cinematic_zoom=1.04,
                frame_duration_ms=220,
                transition_duration_ms=150,
                show_slider=False,
            )
            render_lab_animation_preview(
                teacher_anim,
                frame_duration_ms=220,
                transition_duration_ms=150,
                height=760,
                fallback_key="lem_teacher_animation",
            )
            st.caption("위 미리보기는 브라우저에서 바로 재생됩니다. 아래 슬라이더는 설명용 고정 프레임 비교에만 사용하세요.")

            st.markdown(f"### 고정 프레임 비교 ({times[cur_frame]:,.0f} yr)")
            fig = render_terrain_plotly(
                history[cur_frame],
                "교사용 고정 프레임",
                add_water=True,
                water_level=0,
                landform_type=visual_landform_type,
                detailed_type=visual_detailed_type,
                process_fields=teacher_process_fields,
                overlay_type=teacher_overlay_type,
            )
            st.plotly_chart(fig, width="stretch")
            if teacher_overlay_type:
                overlay_caption = teacher_stage.get("overlay_caption")
                if overlay_caption:
                    st.caption(f"현재 고정 프레임 오버레이: {teacher_overlay_label} | {overlay_caption}")
                else:
                    st.caption(f"현재 고정 프레임 오버레이: {teacher_overlay_label}")
            teacher_stage_index = int(teacher_stage.get("stage_index", 0)) + 1
            teacher_info_lines = [
                f"단계: {teacher_stage_index}/4 | 오버레이: {teacher_overlay_label if teacher_overlay_type else '끄기'}",
                "과정 순서: "
                f"{teacher_stage['process_order']}",
                "우세 작용: "
                f"{teacher_stage['dominant_summary']}",
                "질문 예시: "
                f"{teacher_stage['question']}",
            ]
            if teacher_stage.get("classroom_goal"):
                teacher_info_lines.extend(
                    [
                        "교과 목표: "
                        f"{teacher_stage['classroom_goal']}",
                    ]
                )
            if teacher_stage.get("world_case_title"):
                teacher_info_lines.extend(
                    [
                        "대표 사례: "
                        f"{teacher_stage['world_case_title']} ({teacher_stage.get('world_case_location', '')})",
                    ]
                )
            st.info("\n\n".join(teacher_info_lines))

            with st.expander("수업 자료 저장 (선택)", expanded=False):
                st.caption("GIF는 보조 자료용 저장 기능입니다. 먼저 위 미리보기와 고정 프레임을 확인하세요.")
                if st.button("GIF 저장", width="stretch"):
                    st.session_state['lem_export_gif'] = True

                if st.session_state.get('lem_export_gif', False) and gif_bytes is None:
                    with st.spinner("3D GIF를 생성하는 중입니다..."):
                        try:
                            gif_bytes = create_history_gif_bytes(
                                history=history,
                                times=times,
                                process_history=process_history,
                                stage_history=stage_history,
                                overlay_type=teacher_overlay_type,
                                fps=5,
                                landform_type=visual_landform_type,
                                detailed_type=visual_detailed_type,
                            )
                            st.session_state['lem_teacher_gif_bytes'] = gif_bytes
                        except Exception as e:
                            st.error(f"GIF 생성 실패: {e}")
                            st.session_state['lem_export_gif'] = False
                            gif_bytes = None

                if st.session_state.get('lem_export_gif', False) and gif_bytes:
                    st.download_button(
                        "GIF 다운로드",
                        data=gif_bytes,
                        file_name="geolab_simulation.gif",
                        mime="image/gif",
                    )
                    st.session_state['lem_export_gif'] = False

    tab_stat1, tab_stat2 = st.tabs(["지형 통계", "침식 지도"])

    with tab_stat1:
        elev = history[cur_frame]
        c1, c2, c3 = st.columns(3)
        c1.metric("최고 고도", f"{elev.max():.1f}m")
        c2.metric("최저 고도", f"{elev.min():.1f}m")
        c3.metric("평균 고도", f"{elev.mean():.1f}m")

    with tab_stat2:
        if 'lem_obj' in st.session_state:
            lem_obj = st.session_state['lem_obj']
            import matplotlib.pyplot as plt

            fig, ax = plt.subplots()
            im = ax.imshow(lem_obj.erosion_rate, cmap='Reds')
            plt.colorbar(im)
            ax.set_title("침식률 분포")
            st.pyplot(fig)

    if not student_mode:
        st.markdown("---")
        st.info("이 결과는 수업 설명용 synthetic DEM입니다. 실제 DEM 비교와 export 검증은 Higher Ed에서 진행하세요.")
        if HIGHER_ED_PAGE and hasattr(st, "page_link"):
            st.page_link(HIGHER_ED_PAGE, label="실제 DEM 비교로 이동", width="stretch")

else:
    # Empty State Guide
    st.info("아직 지형을 생성하지 않았습니다. 왼쪽 사이드바에서 조건을 정한 뒤 [실행]을 눌러 보세요.")
    
    # Visual Guide
    cols = st.columns(3)
    with cols[0]:
        st.markdown("#### 1. 지형 선택")
        st.caption("하천, 빙하, 해안, 화산 같은 대표 지형 중 하나를 고르세요.")
    with cols[1]:
        st.markdown("#### 2. 강도와 시간 조절")
        st.caption("침식, 이동, 융기 같은 작용이 얼마나 빠르게 보일지 정합니다.")
    with cols[2]:
        st.markdown("#### 3. 결과 해석")
        st.caption("애니메이션과 고정 장면을 비교하며 어떤 과정이 우세한지 읽어 보세요.")
    st.caption("실제 지형 사례나 DEM 비교가 필요하면 Higher Ed 흐름으로 넘어가면 됩니다.")
    if HIGHER_ED_PAGE and hasattr(st, "page_link"):
        st.page_link(HIGHER_ED_PAGE, label="Higher Ed로 이동", width="stretch")

# ========== Developer Section (Bottom, Hidden by default) ==========
if dev_mode:
    st.markdown("---")
    st.subheader("고급 Python Script Editor")
    with st.expander("개발자 코드 입력", expanded=False):
        code = st.text_area("Custom Code", height=300, value="# 수업용 기본 흐름에서는 비활성화")
        if st.button("코드 실행"):
            st.write("개발자 코드 실행은 아직 연결되지 않았습니다.")
