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
    get_physics_lab_scenario,
    list_physics_lab_scenarios,
    run_physics_lab_simulation,
)
from app.services.morphometric_metrics import (
    metric_cards,
    normalize_process_field,
    process_field_cards,
    process_field_options,
    validation_cards,
)


def surface_figure(surface: np.ndarray, title: str) -> go.Figure:
    figure = go.Figure(
        data=[
            go.Surface(
                z=surface,
                colorscale="Earth",
                showscale=False,
                contours={"z": {"show": False}},
            )
        ]
    )
    figure.update_layout(
        title=title,
        height=520,
        margin=dict(l=0, r=0, t=42, b=0),
        scene=dict(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            zaxis=dict(visible=False),
            aspectmode="manual",
            aspectratio=dict(x=1.15, y=1.0, z=0.36),
            camera=dict(eye=dict(x=1.45, y=-1.65, z=0.95)),
        ),
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
    1. 왼쪽에서 지형을 고릅니다.
    2. 주 작용 강도와 보조 조건을 움직입니다.
    3. 3D 표면에서 모양 변화를 보고, 아래 정량 지표에서 어떤 작용이 우세했는지 확인합니다.
    4. 같은 지형에서 조건 하나만 바꿔 다시 비교하면 수업·연구용 가설을 만들 수 있습니다.
    """
)

scenarios = list_physics_lab_scenarios()
scenario_titles = [f"{scenario.title} · {scenario.group}" for scenario in scenarios]

with st.sidebar:
    st.markdown("### 실험 조건")
    selected_label = st.selectbox("지형", scenario_titles, index=0)
    selected_id = scenarios[scenario_titles.index(selected_label)].landform_id
    scenario = get_physics_lab_scenario(selected_id)

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

view_col, note_col = st.columns([1.35, 0.85])
with view_col:
    frame_index = st.slider("시간 단계", 0, len(history) - 1, len(history) - 1)
    st.plotly_chart(
        surface_figure(history[frame_index], f"{scenario.title} 지형 표면"),
        width="stretch",
        config={"displayModeBar": False, "scrollZoom": False},
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
