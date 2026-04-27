"""여행지리 수업용 케이스 모드."""

from __future__ import annotations

import csv
import io
import inspect
import json
import os
import sys
import time
import zipfile
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.cases.travel_cases import (
    CaseSpec,
    get_case,
    get_real_case_cards,
    list_case_ids,
    title_map,
)
from app.components.renderer import render_terrain_plotly
from engine.ideal_landforms import IDEAL_LANDFORM_GENERATORS
from engine.simple_lem import SimpleLEM


st.set_page_config(page_title="케이스 모드", page_icon="C", layout="wide")


def load_css() -> None:
    css_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "assets",
        "style.css",
    )
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def generate_landform(landform_key: str, grid_size: int, stage: float) -> np.ndarray:
    func = IDEAL_LANDFORM_GENERATORS[landform_key]
    params = inspect.signature(func).parameters

    if "stage" in params:
        result = func(grid_size, stage)
    else:
        result = func(grid_size)

    if isinstance(result, tuple):
        return np.array(result[0], dtype=float)
    return np.array(result, dtype=float)


@st.cache_data(show_spinner=False)
def run_case_simulation(
    landform_key: str,
    stage: float,
    grid_size: int,
    k: float,
    d: float,
    u: float,
    total_time: int,
) -> Tuple[np.ndarray, np.ndarray]:
    initial = generate_landform(landform_key, grid_size, stage)

    lem = SimpleLEM(grid_size=grid_size, K=k, D=d, U=u)
    lem.set_initial_topography(initial)
    history, _ = lem.run(total_time=total_time, dt=100.0, verbose=False)

    final = np.array(history[-1], dtype=float)
    return initial, final


def terrain_stats(elev: np.ndarray) -> Dict[str, float]:
    return {
        "min": float(np.min(elev)),
        "max": float(np.max(elev)),
        "mean": float(np.mean(elev)),
        "relief": float(np.max(elev) - np.min(elev)),
        "std": float(np.std(elev)),
    }


def diff_stats(diff: np.ndarray) -> Dict[str, float]:
    return {
        "mean_delta": float(np.mean(diff)),
        "abs_mean_delta": float(np.mean(np.abs(diff))),
        "positive_ratio": float((diff > 0).mean() * 100.0),
        "negative_ratio": float((diff < 0).mean() * 100.0),
    }


def estimate_runtime_seconds(grid_size: int, total_time: int) -> float:
    """A/B 2회 실행 기준 대략적인 실행시간(초) 추정."""
    single_run_base = 0.0024 * (grid_size ** 2)
    single_run = single_run_base * (total_time / 50000.0)
    return max(2.0, single_run * 2.0)


def recommended_run_params(spec: CaseSpec, run_mode: str) -> Tuple[int, float, int]:
    if run_mode == "수업 빠른모드":
        return 60, spec.research_stage, 20000
    return spec.research_grid_size, spec.research_stage, 50000


def create_diff_map_png(diff: np.ndarray) -> bytes:
    fig_diff, ax = plt.subplots(figsize=(9, 4))
    im = ax.imshow(diff, cmap="RdBu", origin="lower")
    ax.set_title("고도 차이")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    plt.colorbar(im, ax=ax, label="m")
    buffer = io.BytesIO()
    fig_diff.savefig(buffer, format="png", dpi=180, bbox_inches="tight")
    plt.close(fig_diff)
    return buffer.getvalue()


def build_submission_zip(
    spec: CaseSpec,
    briefing_md: str,
    real_case_md: str,
    worksheet_md: str,
    evidence_table: List[Dict[str, str]],
    metrics_payload: Dict[str, float],
    diff_png: bytes,
) -> bytes:
    csv_buffer = io.StringIO()
    csv_columns = ["지표", "값", "연도", "출처", "수업 메모"]
    writer = csv.DictWriter(csv_buffer, fieldnames=csv_columns)
    writer.writeheader()
    writer.writerows(evidence_table)

    archive_buffer = io.BytesIO()
    with zipfile.ZipFile(archive_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("01_케이스_브리핑.md", briefing_md)
        zf.writestr("02_실사례_연결카드.md", real_case_md)
        zf.writestr("03_정책_워크시트.md", worksheet_md)
        zf.writestr("04_증거표.csv", csv_buffer.getvalue())
        zf.writestr("05_시뮬레이션_지표.json", json.dumps(metrics_payload, ensure_ascii=False, indent=2))
        zf.writestr("06_차이맵.png", diff_png)
        zf.writestr(
            "README.txt",
            (
                f"케이스: {spec.title}\n"
                f"생성시각(epoch): {int(time.time())}\n"
                "파일 구성:\n"
                "- 01_케이스_브리핑.md\n"
                "- 02_실사례_연결카드.md\n"
                "- 03_정책_워크시트.md\n"
                "- 04_증거표.csv\n"
                "- 05_시뮬레이션_지표.json\n"
                "- 06_차이맵.png\n"
            ),
        )
    archive_buffer.seek(0)
    return archive_buffer.getvalue()


def evidence_rows(spec: CaseSpec) -> List[Dict[str, str]]:
    return [
        {
            "지표": item.indicator,
            "값": item.value,
            "연도": item.year,
            "출처": item.source,
            "수업 메모": item.note,
        }
        for item in spec.evidence_items
    ]


def real_case_rows(spec: CaseSpec) -> List[Dict[str, str]]:
    rows = []
    for card in get_real_case_cards(spec.case_id):
        rows.append(
            {
                "사례": card.title,
                "지역": card.location,
                "시기": card.period,
                "핵심 포인트": card.key_point,
                "수업 활용": card.classroom_use,
                "출처": card.source_name,
                "링크": card.source_url,
            }
        )
    return rows


def real_case_markdown(spec: CaseSpec) -> str:
    cards = get_real_case_cards(spec.case_id)
    if not cards:
        return f"# {spec.title}\n\n실사례 카드가 등록되지 않았습니다.\n"

    blocks = []
    for card in cards:
        blocks.append(
            "\n".join(
                [
                    f"## {card.title}",
                    f"- 지역: {card.location}",
                    f"- 시기: {card.period}",
                    f"- 핵심 포인트: {card.key_point}",
                    f"- 수업 활용: {card.classroom_use}",
                    f"- 출처: {card.source_name}",
                    f"- 링크: {card.source_url}",
                ]
            )
        )
    return f"# {spec.title} - 실사례 연결 카드\n\n" + "\n\n".join(blocks) + "\n"


def briefing_text(spec: CaseSpec) -> str:
    timeline_lines = "\n".join(
        f"- {item.period}: {item.event} -> {item.implication}" for item in spec.timeline
    )
    objective_lines = "\n".join(f"- {item}" for item in spec.learning_objectives)
    prompt_lines = "\n".join(f"- {item}" for item in spec.classroom_prompts)
    evidence_lines = "\n".join(
        f"- {item.indicator} | {item.value} | {item.year} | {item.source}" for item in spec.evidence_items
    )
    option_lines = "\n".join(
        f"- 선택지 {opt.option_id} ({opt.title}): {opt.summary} / 기대효과: {opt.expected_effect} / 한계: {opt.tradeoff}"
        for opt in spec.policy_options
    )
    source_lines = "\n".join(f"- {line}" for line in spec.source_notes)

    return (
        f"# {spec.title}\n\n"
        f"## 지역과 실제 앵커\n"
        f"- 지역: {spec.region}\n"
        f"- 실제 사례 앵커: {spec.real_world_anchor}\n"
        f"- 이해관계자: {spec.stakeholders}\n\n"
        f"## 상황 내러티브\n{spec.narrative}\n\n"
        f"## 핵심 질문\n{spec.guiding_question}\n\n"
        f"## 수업 초점\n{spec.lesson_focus}\n\n"
        f"## 학습목표\n{objective_lines}\n\n"
        f"## 사건 흐름(타임라인)\n{timeline_lines}\n\n"
        f"## 증거 팩\n{evidence_lines}\n\n"
        f"## 정책 선택지\n{option_lines}\n\n"
        f"## 토론 질문\n{prompt_lines}\n\n"
        f"## 출처 메모\n{source_lines}\n"
    )


def case_note_text(
    spec: CaseSpec,
    stats_base: Dict[str, float],
    stats_int: Dict[str, float],
    stats_diff: Dict[str, float],
) -> str:
    return (
        f"# {spec.title} - 정책 워크시트\n\n"
        f"## 핵심 질문\n{spec.guiding_question}\n\n"
        "## A/B 설정\n"
        f"- A(기준안): {spec.baseline_label}\n"
        f"- B(개입안): {spec.intervention_label}\n\n"
        "## 수치 근거 표\n"
        f"- 기준안 기복량: {stats_base['relief']:.2f} m\n"
        f"- 개입안 기복량: {stats_int['relief']:.2f} m\n"
        f"- 기복량 변화(B-A): {(stats_int['relief'] - stats_base['relief']):+.2f} m\n"
        f"- 기준안 평균고도: {stats_base['mean']:.2f} m\n"
        f"- 개입안 평균고도: {stats_int['mean']:.2f} m\n"
        f"- 셀 평균 변화(B-A): {stats_diff['mean_delta']:+.3f} m\n"
        f"- 셀 절대평균 변화: {stats_diff['abs_mean_delta']:.3f} m\n"
        f"- 양의 변화 면적비: {stats_diff['positive_ratio']:.1f}%\n"
        f"- 음의 변화 면적비: {stats_diff['negative_ratio']:.1f}%\n\n"
        "## CER 초안\n"
        "- Claim(주장):\n"
        "- Evidence(근거: 수치 최소 2개):\n"
        "- Reasoning(과정 기반 해석):\n"
        "- Counterargument/Limitation(반론·한계):\n"
    )


load_css()
st.markdown("## 케이스 모드")
st.caption("여행지리 수업용: 내러티브 + 근거 + A/B 시뮬레이션")

case_ids = list_case_ids()
case_titles = title_map()

selected_case_id = st.selectbox(
    "사례 선택",
    case_ids,
    format_func=lambda x: case_titles.get(x, x),
)
spec = get_case(selected_case_id)
prefix = f"case_{spec.case_id}"
briefing_md = briefing_text(spec)

st.markdown("---")
st.markdown("### 수업 진행판")

check_items = [
    ("step_case", "1) 사례 읽기 완료"),
    ("step_research", "2) Research Lab 근거 추출 완료"),
    ("step_ab", "3) A/B 시뮬레이션 실행 완료"),
    ("step_cer", "4) CER 문장 작성 완료"),
    ("step_submit", "5) 결과물 저장/제출 완료"),
]

progress_col, timer_col = st.columns([1.35, 1.0])
with progress_col:
    done_count = 0
    for check_key, check_label in check_items:
        if st.checkbox(check_label, key=f"{prefix}_{check_key}"):
            done_count += 1
    progress_ratio = done_count / len(check_items)
    st.progress(progress_ratio)
    st.caption(f"진행률: {done_count}/{len(check_items)}")

with timer_col:
    timer_running_key = f"{prefix}_timer_running"
    timer_elapsed_key = f"{prefix}_timer_elapsed"
    timer_start_key = f"{prefix}_timer_started_at"

    if timer_running_key not in st.session_state:
        st.session_state[timer_running_key] = False
    if timer_elapsed_key not in st.session_state:
        st.session_state[timer_elapsed_key] = 0.0
    if timer_start_key not in st.session_state:
        st.session_state[timer_start_key] = time.time()

    if st.session_state[timer_running_key]:
        try:
            from streamlit_autorefresh import st_autorefresh

            st_autorefresh(interval=1000, limit=None, key=f"{prefix}_timer_refresh")
        except Exception:
            pass

    elapsed = st.session_state[timer_elapsed_key]
    if st.session_state[timer_running_key]:
        elapsed += time.time() - st.session_state[timer_start_key]

    minute = int(elapsed // 60)
    second = int(elapsed % 60)
    st.metric("수업 타이머", f"{minute:02d}:{second:02d}")

    tcol1, tcol2, tcol3 = st.columns(3)
    with tcol1:
        if st.button("시작", key=f"{prefix}_timer_start", use_container_width=True):
            if not st.session_state[timer_running_key]:
                st.session_state[timer_start_key] = time.time()
                st.session_state[timer_running_key] = True
                st.rerun()
    with tcol2:
        if st.button("일시정지", key=f"{prefix}_timer_pause", use_container_width=True):
            if st.session_state[timer_running_key]:
                st.session_state[timer_elapsed_key] += time.time() - st.session_state[timer_start_key]
                st.session_state[timer_running_key] = False
                st.rerun()
    with tcol3:
        if st.button("초기화", key=f"{prefix}_timer_reset", use_container_width=True):
            st.session_state[timer_running_key] = False
            st.session_state[timer_elapsed_key] = 0.0
            st.session_state[timer_start_key] = time.time()
            st.rerun()

header_left, header_right = st.columns([1.45, 1.0])
with header_left:
    st.markdown(f"### {spec.title}")
    st.markdown(f"- 지역: `{spec.region}`")
    st.markdown(f"- 실제 앵커: `{spec.real_world_anchor}`")
    st.markdown(f"- 이해관계자: {spec.stakeholders}")
    st.markdown(f"- 수업 초점: **{spec.lesson_focus}**")
    st.markdown(f"- 핵심 질문: **{spec.guiding_question}**")
    st.info(spec.narrative)

with header_right:
    st.markdown("### 빠른 실행")
    if st.button("기본 DEM을 Research Lab으로 보내기", use_container_width=True):
        baseline_dem = generate_landform(spec.research_landform, spec.research_grid_size, spec.research_stage)
        st.session_state["research_elevation"] = baseline_dem
        st.session_state["research_params"] = {
            "source": "case_mode",
            "case_id": spec.case_id,
            "case_title": spec.title,
            "landform": spec.research_landform,
            "grid_size": spec.research_grid_size,
            "stage": spec.research_stage,
            "cell_size": spec.research_cell_size,
            "baseline_label": spec.baseline_label,
            "intervention_label": spec.intervention_label,
            "anchor": spec.real_world_anchor,
        }
        st.success("기본 DEM을 Research Lab 세션으로 전송했습니다.")

    if st.button("기후 프리셋을 Climate Lab으로 보내기", use_container_width=True):
        st.session_state["case_climate_month"] = spec.climate_month
        st.session_state["case_climate_mode"] = spec.climate_mode
        st.session_state["case_climate_pending"] = True
        st.session_state["case_climate_case_title"] = spec.title
        st.success("기후 프리셋 저장 완료. Climate Lab에서 자동 적용됩니다.")

    mode_label = "현실 근사 모델" if spec.climate_mode == "real" else "이론 모델"
    st.caption(f"기후 프리셋: {spec.climate_month}월 / {mode_label}")

st.markdown("---")
st.markdown("### 실사례 연결 카드")
real_cards = get_real_case_cards(spec.case_id)
if real_cards:
    st.caption("아래 카드는 실제 사례 기반 맥락입니다. 수업 전 최신 수치와 운영 규정을 한 번 더 확인하세요.")
    for idx, card in enumerate(real_cards, 1):
        with st.expander(f"{idx}. {card.title} ({card.period})", expanded=(idx == 1)):
            st.markdown(f"- 지역: `{card.location}`")
            st.markdown(f"- 핵심 포인트: {card.key_point}")
            st.markdown(f"- 수업 활용: {card.classroom_use}")
            st.markdown(f"- 출처: {card.source_name}")
            st.link_button("출처 열기", card.source_url, use_container_width=False)
    with st.expander("실사례 카드 표로 보기", expanded=False):
        st.dataframe(real_case_rows(spec), use_container_width=True, hide_index=True)
else:
    st.info("등록된 실사례 카드가 없습니다.")

st.download_button(
    "케이스 브리핑 다운로드 (.md)",
    data=briefing_md,
    file_name=f"{spec.case_id}_briefing.md",
    mime="text/markdown",
)

st.markdown("---")
st.markdown("### 증거 팩")

pack_left, pack_right = st.columns([1.1, 1.4])
with pack_left:
    st.markdown("#### 타임라인")
    for item in spec.timeline:
        st.markdown(f"- **{item.period}**: {item.event} -> {item.implication}")

    st.markdown("#### 학습목표")
    for objective in spec.learning_objectives:
        st.markdown(f"- {objective}")

    st.markdown("#### 토론 질문")
    for prompt in spec.classroom_prompts:
        st.markdown(f"- {prompt}")

with pack_right:
    st.markdown("#### 관측 지표")
    st.dataframe(evidence_rows(spec), use_container_width=True, hide_index=True)
    st.markdown("#### 출처 메모")
    for line in spec.source_notes:
        st.markdown(f"- {line}")

st.markdown("---")
st.markdown("### 정책 선택지")
option_cols = st.columns(len(spec.policy_options))
for col, option in zip(option_cols, spec.policy_options):
    with col:
        st.markdown(f"#### 선택지 {option.option_id}: {option.title}")
        st.markdown(f"- 요약: {option.summary}")
        st.markdown(f"- 기대효과: {option.expected_effect}")
        st.markdown(f"- 트레이드오프: {option.tradeoff}")

st.markdown("---")
st.markdown("### A/B 정책 실험")

user_mode = st.radio(
    "사용자 모드",
    ["학생 단순모드", "교사 상세모드"],
    horizontal=True,
    key=f"{prefix}_user_mode",
)
is_student_mode = user_mode == "학생 단순모드"

if is_student_mode:
    st.markdown(
        """
        <div class="mode-banner mode-student">
            <div class="mode-title">학생 단순모드</div>
            <div class="mode-copy">핵심 선택만 남겨 빠르게 실험하고, 결과 해석(CER)에 집중합니다.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        """
        <div class="mode-banner mode-teacher">
            <div class="mode-title">교사 상세모드</div>
            <div class="mode-copy">격자·단계·기간과 K/D/U를 직접 조절해 정책 시나리오를 정밀 비교합니다.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

if is_student_mode:
    quality_mode = st.radio(
        "실행 품질",
        ["빠름", "균형", "정밀"],
        horizontal=True,
        key=f"{prefix}_quality_mode",
    )
    quality_map = {
        "빠름": (50, spec.research_stage, 30000),
        "균형": (70, spec.research_stage, 50000),
        "정밀": (90, spec.research_stage, 70000),
    }
    grid_size, stage, total_time = quality_map[quality_mode]
    st.caption(
        f"학생 단순모드 자동설정: 격자 {grid_size}, 단계 {stage:.2f}, 기간 {total_time:,}년"
    )
else:
    run_mode = st.radio(
        "실행 모드",
        ["수업 빠른모드", "정밀 분석모드"],
        horizontal=True,
        key=f"{prefix}_run_mode",
    )

    rec_grid, rec_stage, rec_total_time = recommended_run_params(spec, run_mode)
    if st.button("권장 실행값 불러오기", key=f"{prefix}_apply_recommended"):
        st.session_state[f"{prefix}_grid_size"] = rec_grid
        st.session_state[f"{prefix}_stage"] = rec_stage
        st.session_state[f"{prefix}_total_time"] = rec_total_time

    if f"{prefix}_grid_size" not in st.session_state:
        st.session_state[f"{prefix}_grid_size"] = rec_grid
    if f"{prefix}_stage" not in st.session_state:
        st.session_state[f"{prefix}_stage"] = rec_stage
    if f"{prefix}_total_time" not in st.session_state:
        st.session_state[f"{prefix}_total_time"] = rec_total_time

    ctrl1, ctrl2, ctrl3 = st.columns(3)
    with ctrl1:
        grid_size = st.slider("격자 크기", 50, 180, step=10, key=f"{prefix}_grid_size")
    with ctrl2:
        stage = st.slider("초기 형성 단계", 0.2, 1.0, step=0.05, key=f"{prefix}_stage")
    with ctrl3:
        total_time = st.slider("시뮬레이션 기간(년)", 10000, 120000, step=5000, key=f"{prefix}_total_time")

est_sec = estimate_runtime_seconds(grid_size, total_time)
if est_sec < 60:
    st.caption(f"예상 실행시간(A/B 합): 약 {int(est_sec)}초")
else:
    st.caption(f"예상 실행시간(A/B 합): 약 {int(est_sec // 60)}분 {int(est_sec % 60)}초")

st.markdown(f"- A(기준안): **{spec.baseline_label}**")
st.markdown(f"- B(개입안): **{spec.intervention_label}**")

if is_student_mode:
    st.markdown("#### 학생용 자동 파라미터")
    policy_strength = st.slider(
        "개입 강도(10~100)",
        10,
        100,
        80,
        5,
        key=f"{prefix}_policy_strength",
        help="개입안 파라미터를 기준안에서 개입안 기본값 방향으로 얼마나 이동할지 조절합니다.",
    )
    # Student mode keeps a meaningful A/B gap by enforcing minimum blend.
    blend = 0.35 + (policy_strength / 100.0) * 0.65
    base_k = float(spec.baseline_k)
    base_d = float(spec.baseline_d)
    base_u = float(spec.baseline_u)
    int_k = base_k + (float(spec.intervention_k) - base_k) * blend
    int_d = base_d + (float(spec.intervention_d) - base_d) * blend
    int_u = base_u + (float(spec.intervention_u) - base_u) * blend

    st.caption(
        f"자동설정: A는 고정, B는 개입 강도 {policy_strength}%를 적용합니다. (최소 35% 개입 반영)"
    )
    gap_cols = st.columns(3)
    gap_cols[0].metric("ΔK (B-A)", f"{(int_k - base_k):+.6f}")
    gap_cols[1].metric("ΔD (B-A)", f"{(int_d - base_d):+.4f}")
    gap_cols[2].metric("ΔU (B-A)", f"{(int_u - base_u):+.6f}")
    with st.expander("자동 파라미터 상세 보기", expanded=False):
        st.markdown(f"- A: K={base_k:.6f}, D={base_d:.4f}, U={base_u:.6f}")
        st.markdown(f"- B: K={int_k:.6f}, D={int_d:.4f}, U={int_u:.6f}")
else:
    base_col, int_col = st.columns(2)
    with base_col:
        st.markdown("#### 기준안 파라미터")
        base_k = st.number_input("K (기준안)", value=float(spec.baseline_k), format="%.6f", key=f"{prefix}_base_k")
        base_d = st.number_input("D (기준안)", value=float(spec.baseline_d), format="%.4f", key=f"{prefix}_base_d")
        base_u = st.number_input("U (기준안)", value=float(spec.baseline_u), format="%.6f", key=f"{prefix}_base_u")

    with int_col:
        st.markdown("#### 개입안 파라미터")
        int_k = st.number_input("K (개입안)", value=float(spec.intervention_k), format="%.6f", key=f"{prefix}_int_k")
        int_d = st.number_input("D (개입안)", value=float(spec.intervention_d), format="%.4f", key=f"{prefix}_int_d")
        int_u = st.number_input("U (개입안)", value=float(spec.intervention_u), format="%.6f", key=f"{prefix}_int_u")

run = st.button("A/B 시뮬레이션 실행", type="primary", key=f"{prefix}_run", use_container_width=True)

if run:
    with st.spinner("기준안/개입안 시뮬레이션을 실행 중입니다..."):
        initial_base, final_base = run_case_simulation(
            spec.research_landform,
            stage,
            grid_size,
            base_k,
            base_d,
            base_u,
            total_time,
        )
        _, final_int = run_case_simulation(
            spec.research_landform,
            stage,
            grid_size,
            int_k,
            int_d,
            int_u,
            total_time,
        )

    st.session_state["case_mode_result"] = {
        "case_id": spec.case_id,
        "initial": initial_base,
        "final_base": final_base,
        "final_int": final_int,
    }

result = st.session_state.get("case_mode_result")
if result and result.get("case_id") == spec.case_id:
    initial = result["initial"]
    final_base = result["final_base"]
    final_int = result["final_int"]

    stats_initial = terrain_stats(initial)
    stats_base = terrain_stats(final_base)
    stats_int = terrain_stats(final_int)

    diff = final_int - final_base
    stats_d = diff_stats(diff)

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("초기 기복량", f"{stats_initial['relief']:.1f} m")
    m2.metric("기준안 기복량", f"{stats_base['relief']:.1f} m")
    m3.metric("개입안 기복량", f"{stats_int['relief']:.1f} m")
    m4.metric("기복량 변화", f"{(stats_int['relief'] - stats_base['relief']):+.1f} m")
    m5.metric("절대평균 변화", f"{stats_d['abs_mean_delta']:.3f} m")

    col_base, col_int = st.columns(2)
    with col_base:
        st.markdown("#### 기준안 최종 지형")
        fig_base = render_terrain_plotly(
            final_base,
            f"{spec.title} - 기준안",
            add_water=True,
            water_level=-999,
            force_camera=False,
            landform_type=spec.render_landform_type,
            detailed_type=spec.research_landform,
        )
        if fig_base is not None:
            st.plotly_chart(fig_base, use_container_width=True)

    with col_int:
        st.markdown("#### 개입안 최종 지형")
        fig_int = render_terrain_plotly(
            final_int,
            f"{spec.title} - 개입안",
            add_water=True,
            water_level=-999,
            force_camera=False,
            landform_type=spec.render_landform_type,
            detailed_type=spec.research_landform,
        )
        if fig_int is not None:
            st.plotly_chart(fig_int, use_container_width=True)

    st.markdown("#### 차이 맵 (개입안 - 기준안)")
    fig_diff, ax = plt.subplots(figsize=(9, 4))
    im = ax.imshow(diff, cmap="RdBu", origin="lower")
    ax.set_title("고도 차이")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    plt.colorbar(im, ax=ax, label="m")
    st.pyplot(fig_diff)
    plt.close(fig_diff)

    worksheet = case_note_text(spec, stats_base, stats_int, stats_d)
    st.download_button(
        "정책 워크시트 다운로드 (.md)",
        data=worksheet,
        file_name=f"{spec.case_id}_worksheet.md",
        mime="text/markdown",
    )

    metrics_payload = {
        "case_id": spec.case_id,
        "case_title": spec.title,
        "initial_relief": float(stats_initial["relief"]),
        "baseline_relief": float(stats_base["relief"]),
        "intervention_relief": float(stats_int["relief"]),
        "relief_delta": float(stats_int["relief"] - stats_base["relief"]),
        "baseline_mean": float(stats_base["mean"]),
        "intervention_mean": float(stats_int["mean"]),
        "mean_delta": float(stats_d["mean_delta"]),
        "abs_mean_delta": float(stats_d["abs_mean_delta"]),
        "positive_ratio": float(stats_d["positive_ratio"]),
        "negative_ratio": float(stats_d["negative_ratio"]),
        "grid_size": int(grid_size),
        "stage": float(stage),
        "total_time": int(total_time),
    }
    package_zip = build_submission_zip(
        spec=spec,
        briefing_md=briefing_md,
        real_case_md=real_case_markdown(spec),
        worksheet_md=worksheet,
        evidence_table=evidence_rows(spec),
        metrics_payload=metrics_payload,
        diff_png=create_diff_map_png(diff),
    )
    st.download_button(
        "수업 제출 패키지 다운로드 (.zip)",
        data=package_zip,
        file_name=f"{spec.case_id}_수업패키지.zip",
        mime="application/zip",
    )

st.markdown("---")
st.markdown("### 권장 수업 흐름 (45~50분)")
st.markdown("1. 사례를 선택하고 내러티브·타임라인·증거 팩을 읽습니다.")
st.markdown("2. `기본 DEM을 Research Lab으로 보내기`를 눌러 분석 데이터를 넘깁니다.")
st.markdown("3. Research Lab에서 프로파일/경사/하이프소메트릭 근거를 확보합니다.")
st.markdown("4. 다시 케이스 모드로 돌아와 A/B 시뮬레이션을 실행합니다.")
st.markdown("5. 워크시트를 내려받아 CER와 정책 메모를 완성합니다.")
