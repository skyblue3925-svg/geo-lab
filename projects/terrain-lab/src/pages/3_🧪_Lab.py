from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
import streamlit as st


st.set_page_config(page_title="Geo-Lab Lab", page_icon="🧪", layout="wide")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.beta_navigation import render_beta_sidebar
from app.services.terrain_physics_lab import (
    active_physics_lab_rows,
    force_module_rows_for_scenario,
    get_physics_lab_scenario,
    get_physics_lab_theory,
    list_physics_lab_scenarios,
    planned_physics_lab_rows,
    run_physics_lab_simulation,
)
from app.services.morphometric_metrics import (
    metric_cards,
    normalize_process_field,
    process_field_cards,
    process_field_options,
    validation_cards,
)


def _surface_trace_kwargs(
    surface: np.ndarray,
    overlay: np.ndarray | None = None,
    overlay_label: str | None = None,
) -> dict:
    surface_kwargs = {
        "z": surface,
        "showscale": False,
        "contours": {"z": {"show": False}},
    }
    if overlay is not None:
        surface_kwargs.update(
            {
                "surfacecolor": overlay,
                "colorscale": "Viridis",
                "cmin": 0,
                "cmax": 1,
                "showscale": True,
                "colorbar": {"title": overlay_label or "작용장"},
            }
        )
    else:
        surface_kwargs["colorscale"] = "Earth"
    return surface_kwargs


def surface_figure(surface: np.ndarray, title: str, overlay: np.ndarray | None = None, overlay_label: str | None = None) -> go.Figure:
    figure = go.Figure(
        data=[
            go.Surface(**_surface_trace_kwargs(surface, overlay, overlay_label))
        ]
    )
    figure.update_layout(
        title=title,
        height=520,
        uirevision="lab_surface_camera",
        margin=dict(l=0, r=0, t=42, b=0),
        scene=dict(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            zaxis=dict(visible=False),
            aspectmode="manual",
            aspectratio=dict(x=1.15, y=1.0, z=0.36),
            camera=dict(eye=dict(x=1.45, y=-1.65, z=0.95)),
            uirevision="lab_surface_camera",
        ),
    )
    return figure


def animated_surface_figure(
    history: list[np.ndarray],
    title: str,
    *,
    initial_index: int,
    frame_duration_ms: int,
    overlay_frames: list[np.ndarray] | None = None,
    overlay_label: str | None = None,
) -> go.Figure:
    safe_index = int(np.clip(initial_index, 0, len(history) - 1))
    initial_overlay = overlay_frames[safe_index] if overlay_frames else None
    figure = surface_figure(history[safe_index], title, initial_overlay, overlay_label)
    figure.frames = [
        go.Frame(
            name=str(idx),
            data=[
                go.Surface(
                    **_surface_trace_kwargs(
                        surface,
                        overlay_frames[idx] if overlay_frames else None,
                        overlay_label,
                    )
                )
            ],
        )
        for idx, surface in enumerate(history)
    ]
    steps = [
        {
            "label": str(idx),
            "method": "animate",
            "args": [
                [str(idx)],
                {
                    "mode": "immediate",
                    "frame": {"duration": 0, "redraw": True},
                    "transition": {"duration": 0},
                },
            ],
        }
        for idx in range(len(history))
    ]
    figure.update_layout(
        updatemenus=[
            {
                "type": "buttons",
                "direction": "left",
                "x": 0.0,
                "y": 1.08,
                "showactive": False,
                "buttons": [
                    {
                        "label": "재생",
                        "method": "animate",
                        "args": [
                            None,
                            {
                                "fromcurrent": True,
                                "frame": {"duration": frame_duration_ms, "redraw": True},
                                "transition": {"duration": 0},
                                "mode": "immediate",
                            },
                        ],
                    },
                    {
                        "label": "정지",
                        "method": "animate",
                        "args": [
                            [None],
                            {
                                "mode": "immediate",
                                "frame": {"duration": 0, "redraw": False},
                                "transition": {"duration": 0},
                            },
                        ],
                    },
                ],
            }
        ],
        sliders=[
            {
                "active": safe_index,
                "currentvalue": {"prefix": "형성 단계: "},
                "pad": {"t": 34},
                "steps": steps,
            }
        ],
    )
    return figure


def heatmap_figure(change: np.ndarray) -> go.Figure:
    max_abs = max(float(np.max(np.abs(change))), 1e-9)
    figure = go.Figure(
        data=[
            go.Heatmap(
                z=change,
                colorscale="RdBu",
                zmid=0,
                zmin=-max_abs,
                zmax=max_abs,
                colorbar=dict(title="변화량"),
            )
        ]
    )
    figure.update_layout(
        height=420,
        margin=dict(l=0, r=0, t=28, b=0),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False, scaleanchor="x"),
    )
    return figure


def process_heatmap_figure(field: np.ndarray, title: str) -> go.Figure:
    figure = go.Figure(
        data=[
            go.Heatmap(
                z=field,
                colorscale="Viridis",
                zmin=0,
                zmax=1,
                colorbar=dict(title="상대 강도"),
            )
        ]
    )
    figure.update_layout(
        title=title,
        height=420,
        margin=dict(l=0, r=0, t=42, b=0),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False, scaleanchor="x"),
    )
    return figure


MAIN_OVERLAY_KEYS = {
    "drainage_area",
    "transport_capacity",
    "wave_energy",
    "shoreline_retreat",
    "wave_cut_platform",
    "sand_flux",
    "stoss_erosion",
    "lee_deposition",
    "ice_thickness",
    "glacial_velocity",
    "volcanic_construction",
    "lava_flow",
    "explosion_energy",
    "crater_excavation",
    "pyroclastic_cone_growth",
    "groundwater_flow",
    "solution_rate",
    "collapse_risk",
    "seasonal_flooding",
    "polje_floor_aggradation",
}


def main_overlay_options(process_fields: dict) -> tuple[tuple[str, str], ...]:
    options = process_field_options(process_fields)
    filtered = tuple((key, label) for key, label in options if key in MAIN_OVERLAY_KEYS)
    return filtered or options[:12]


def stage_label(result: dict) -> str:
    final_stage = result.get("final_stage") or {}
    stage_name = final_stage.get("stage_name") or final_stage.get("title") or "형성과정 진행"
    explanation = final_stage.get("teacher_note") or final_stage.get("student_observation") or ""
    return f"{stage_name} — {explanation}" if explanation else str(stage_name)


render_beta_sidebar("lab")

st.markdown("## 지형 물리 실험실")
st.caption(
    "지형 형성 요인을 직접 조절해 같은 지형도 시간, 에너지, 퇴적 조건에 따라 어떻게 달라지는지 비교합니다."
)
st.markdown(
    """
    **사용 방법**
    1. 아래에서 지형 프리셋을 고릅니다.
    2. 주 작용 강도와 보조 조건을 움직입니다.
    3. 재생 또는 시간 단계 슬라이더로 형성과정을 살펴봅니다.
    4. 같은 지형에서 조건 하나만 바꿔 다시 비교하면 수업·연구용 가설을 만들 수 있습니다.
    """
)

scenarios = list_physics_lab_scenarios()
scenario_titles = [f"{scenario.title} · {scenario.group}" for scenario in scenarios]
scenario_by_title = dict(zip(scenario_titles, scenarios, strict=False))

st.markdown("### 지형 프리셋")
st.caption(f"현재 실험 가능한 프리셋은 {len(scenarios)}개입니다. 38개 기본 지형과 추가 보강 지형을 공통 물리엔진 계열로 연결했습니다.")
selected_label = st.selectbox("실험 지형 선택", scenario_titles, index=0, key="lab_main_scenario")
selected_id = scenario_by_title[selected_label].landform_id
scenario = get_physics_lab_scenario(selected_id)

with st.expander("프리셋 목록과 확장 예정 지형", expanded=False):
    st.markdown("#### 현재 실험 가능")
    st.dataframe(active_physics_lab_rows(), hide_index=True, use_container_width=True)
    planned_rows = planned_physics_lab_rows()
    if planned_rows:
        st.markdown("#### 다음 프리셋 후보")
        st.dataframe(planned_rows, hide_index=True, use_container_width=True)

with st.sidebar:
    st.markdown("### 실험 조건")
    st.caption(f"선택한 지형: {scenario.title} · {scenario.group}")

    force = st.slider(scenario.primary_factor, 0, 100, scenario.default_force, 5)
    secondary = st.slider(scenario.secondary_factor, 0, 100, 55, 5)
    uplift = st.slider("융기/침강 경향", 0, 100, scenario.default_uplift, 5)
    diffusion = st.slider("사면 완화·확산", 0, 100, scenario.default_diffusion, 5)
    total_time = st.slider("모의 시간", 5_000, 120_000, scenario.default_time, 5_000)
    grid_size = st.select_slider("해상도", options=[40, 48, 56, 64], value=48)

run_key = (
    selected_id,
    int(force),
    int(secondary),
    int(uplift),
    int(diffusion),
    int(total_time),
    int(grid_size),
)
result = run_physics_lab_simulation(*run_key)
history = result["history"]
initial = history[0]
final = history[-1]
change = final - initial
summary = result["change"]
metrics = result.get("metrics", {})
theory = get_physics_lab_theory(selected_id)

if st.session_state.get("lab_run_key") != run_key:
    st.session_state["lab_run_key"] = run_key
    st.session_state["lab_frame_index"] = len(history) - 1
    st.session_state["lab_playing"] = False

top_cols = st.columns([1.2, 1.0, 1.0, 1.0])
top_cols[0].metric("실험 지형", scenario.title)
top_cols[1].metric("우세 작용", result["dominant_process"])
top_cols[2].metric("최종 기복", f"{summary['relief']:.1f}")
top_cols[3].metric("활성 영역", f"{summary['active_fraction'] * 100:.0f}%")

st.info(stage_label(result))
st.caption(f"모델 커널: {result.get('kernel', 'unknown')} · {result.get('kernel_notes', '')}")
if metrics.get("diagnosis"):
    st.success(str(metrics["diagnosis"]))

metric_cols = st.columns(4)
for col, (label, value, help_text) in zip(metric_cols, metric_cards(metrics), strict=False):
    col.metric(label, value, help=help_text)

with st.expander("모델 검증 지표", expanded=True):
    st.caption(
        "이 지표는 결과가 해당 지형의 전형적 형성 방향과 맞는지 빠르게 점검하기 위한 v1 진단값입니다. "
        "실측 DEM 보정값은 아니며, 수업·프로토타입 단계의 비교 기준으로 사용합니다."
    )
    validation_rows = [
        {"지표": label, "값": value, "해석": help_text}
        for label, value, help_text in validation_cards(selected_id, metrics)
    ]
    if validation_rows:
        st.dataframe(validation_rows, hide_index=True)
    else:
        st.write("이 지형의 전용 검증 지표는 아직 준비 중입니다.")

with st.expander("현재 적용 중인 물리식과 이론", expanded=False):
    st.markdown(f"**모델 계열:** {theory.model_family}")
    st.caption(theory.classroom_note)
    equation_rows = [
        {"작용": label, "식": equation, "의미": explanation}
        for label, equation, explanation in theory.equations
    ]
    st.dataframe(equation_rows, hide_index=True, use_container_width=True)
    st.markdown("**현재 단순화한 부분**")
    for assumption in theory.assumptions:
        st.write(f"- {assumption}")
    st.info("이 식들은 연구용 수치모델로 확장할 때 검증 가능한 작용장과 파라미터로 분리해 나갈 기준입니다.")

with st.expander("공통 물리엔진 작용 모듈", expanded=True):
    st.caption(
        "지형별로 별도 코드를 계속 늘리는 방식이 아니라, 아래 내적·외적 작용 모듈을 조합하고 "
        "지형은 초기 지형과 프리셋으로 다룹니다."
    )
    st.dataframe(force_module_rows_for_scenario(selected_id), hide_index=True, use_container_width=True)
    active_fields = sorted(result["process_history"][-1].keys())
    st.caption("현재 계산 결과에 포함된 주요 출력 필드")
    st.code(", ".join(active_fields[:80]), language="text")

view_col, note_col = st.columns([1.35, 0.85])
with view_col:
    control_cols = st.columns([0.9, 0.9, 1.2])
    with control_cols[0]:
        if st.button("처음", use_container_width=True):
            st.session_state["lab_frame_index"] = 0
    with control_cols[1]:
        if st.button("끝", use_container_width=True):
            st.session_state["lab_frame_index"] = len(history) - 1
    with control_cols[2]:
        playback_delay_ms = st.select_slider(
            "그래프 안 재생 속도",
            options=[250, 500, 800, 1200, 1600],
            value=800,
            format_func=lambda value: f"{value}ms",
        )

    frame_index = st.slider("시간 단계", 0, len(history) - 1, key="lab_frame_index")
    frame_process_fields = result["process_history"][frame_index]
    compact_overlay = st.checkbox("핵심 작용장만 보기", value=True)
    surface_options = main_overlay_options(frame_process_fields) if compact_overlay else process_field_options(frame_process_fields)
    surface_overlay = None
    surface_overlay_label = None
    surface_overlay_key = None
    if surface_options:
        surface_overlay_labels = ["지형 색상"] + [label for _key, label in surface_options]
        surface_overlay_label = st.selectbox("3D 표면 색상", surface_overlay_labels, index=0)
        if surface_overlay_label != "지형 색상":
            surface_overlay_key = dict((label, key) for key, label in surface_options)[surface_overlay_label]
            surface_overlay = normalize_process_field(frame_process_fields, surface_overlay_key)
    overlay_frames = None
    if surface_overlay_key is not None:
        overlay_frames = [
            normalize_process_field(frame_fields, surface_overlay_key)
            for frame_fields in result["process_history"]
        ]
    st.caption("3D 화면 안의 재생/정지 버튼을 쓰면 카메라를 돌린 상태에서 형성과정을 볼 수 있습니다.")
    st.plotly_chart(
        animated_surface_figure(
            history,
            f"{scenario.title} 지형 표면",
            initial_index=frame_index,
            frame_duration_ms=int(playback_delay_ms),
            overlay_frames=overlay_frames,
            overlay_label=surface_overlay_label if surface_overlay is not None else None,
        ),
        width="stretch",
        key=f"lab_surface_plot_{selected_id}_{surface_overlay_key or 'terrain'}",
        config={"displayModeBar": True, "scrollZoom": True},
    )

with note_col:
    st.markdown("### 조작 해석")
    st.markdown(
        f"""
        - **{scenario.primary_factor}**: 해당 지형을 직접 만드는 주 작용의 세기입니다.
        - **{scenario.secondary_factor}**: 주 작용이 표면에 남는 방식을 바꾸는 보조 조건입니다.
        - **융기/침강 경향**: 지형을 높이거나 낮추는 장기 구조 운동입니다.
        - **사면 완화·확산**: 경사가 무너지고 부드러워지는 정도입니다.
        """
    )
    st.markdown("### 현재 결과")
    st.markdown(
        f"""
        - 평균 변화량: `{summary['mean_change']:.2f}`
        - 최대 상승: `{summary['max_uplift']:.2f}`
        - 최대 하강: `{summary['max_lowering']:.2f}`
        - 저장 프레임: `{len(history)}`
        - 지표 진단: `{metrics.get('diagnosis', '계산 중')}`
        """
    )

process_fields = result["process_history"][frame_index]
with st.expander("작용장 상세", expanded=False):
    st.caption(
        "공통 엔진이 계산한 세부 물리장입니다. 값은 서로 다른 단위의 상대 지표이므로 같은 행 안에서 조건 비교용으로 읽습니다."
    )
    process_rows = [
        {"작용장": label, "값": value, "해석": help_text}
        for label, value, help_text in process_field_cards(process_fields)
    ]
    if process_rows:
        st.dataframe(process_rows, hide_index=True)
    else:
        st.write("현재 프레임에서 강하게 활성화된 세부 작용장이 없습니다.")

    options = process_field_options(process_fields)
    if options:
        labels = [label for _key, label in options]
        selected_overlay_label = st.selectbox("지도에 표시할 작용장", labels, index=0)
        selected_overlay_key = dict((label, key) for key, label in options)[selected_overlay_label]
        overlay = normalize_process_field(process_fields, selected_overlay_key)
        st.plotly_chart(
            process_heatmap_figure(overlay, f"{selected_overlay_label} 분포"),
            width="stretch",
            config={"displayModeBar": False},
        )

st.markdown("### 변화량 지도")
st.caption("붉은 영역은 상대적 상승·퇴적, 푸른 영역은 상대적 하강·침식이 강한 곳입니다.")
st.plotly_chart(
    heatmap_figure(change),
    width="stretch",
    config={"displayModeBar": False},
)

with st.expander("형성과정 프레임 로그", expanded=False):
    stage_history = result.get("stage_history") or []
    if not stage_history:
        st.write("아직 분류된 단계가 없습니다.")
    else:
        for idx, stage in enumerate(stage_history):
            progress = float(stage.get("progress", 0.0)) * 100
            name = stage.get("stage_name") or stage.get("title") or "단계"
            note = stage.get("teacher_note") or stage.get("student_observation") or ""
            st.markdown(f"**{idx + 1}. {name}** · {progress:.0f}%")
            if note:
                st.caption(str(note))
