"""
🎓 학습 모드 (Learning Interactives)

스펙(JSON)에 적힌 학습목표 → 단계 → 과제 → 힌트 → 피드백 → 풀이 흐름을
검증된 지형 엔진(engine/ideal_landforms.py) 위에서 렌더링한다.

AI 는 스펙을 '제안'만 하고, 교사가 검수한 스펙만 학생에게 간다.
스펙 형식은 learning/schema.py, 판정 규칙은 learning/checks.py 참고.
"""
import json
import os
import sys

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from learning import (  # noqa: E402
    SPEC_VERSION, validate_spec, load_spec, list_specs, spec_to_json,
    generate_stage, available_landforms, evaluate_check, describe_check_keys,
)
from app.components.renderer import render_terrain_plotly  # noqa: E402

st.set_page_config(page_title="🎓 학습 모드", page_icon="🎓", layout="wide")

CUSTOM_KEY = "learn_custom_spec"
PROGRESS_KEY = "learn_progress"
MAX_WRONG_BEFORE_SOLUTION = 2

# ==========================================================
# 스펙 불러오기
# ==========================================================
bundled = {sid: load_spec(path) for sid, path in list_specs().items()}
options = {f"{spec['title']}": sid for sid, spec in bundled.items()}
if st.session_state.get(CUSTOM_KEY):
    custom = st.session_state[CUSTOM_KEY]
    options[f"📋 (검수 중) {custom.get('title', custom.get('id', '사용자 스펙'))}"] = "__custom__"

st.sidebar.subheader("🎓 학습 활동")
chosen_label = st.sidebar.radio("활동 선택", list(options.keys()), key="learn_choice")
chosen_id = options[chosen_label]
spec = st.session_state[CUSTOM_KEY] if chosen_id == "__custom__" else bundled[chosen_id]
spec_id = spec.get("id", chosen_id)

st.sidebar.markdown("---")
grid_size = st.sidebar.slider("해상도", 30, 120, 60, 10, key="learn_res",
                              help="낮을수록 빠릅니다. 판정 기준은 해상도와 무관합니다.")

# ==========================================================
# 진행 상태 (스펙 id 별)
# ==========================================================
if PROGRESS_KEY not in st.session_state:
    st.session_state[PROGRESS_KEY] = {}
progress_all = st.session_state[PROGRESS_KEY]
if spec_id not in progress_all:
    progress_all[spec_id] = {"level": 0, "levels": {}}
progress = progress_all[spec_id]


def level_state(level_id: str) -> dict:
    return progress["levels"].setdefault(level_id, {
        "attempts": 0, "wrong": 0, "hints": 0, "done": False, "target_reached": False,
    })


def reset_progress():
    progress_all[spec_id] = {"level": 0, "levels": {}}


# ==========================================================
# 렌더링 도우미
# ==========================================================
def draw_terrain_2d(elevation: np.ndarray, title: str, zone_mask=None, zone_info=None):
    fig, ax = plt.subplots(figsize=(7, 7))
    im = ax.imshow(elevation, cmap=plt.cm.terrain, origin="upper")
    water = elevation < 0
    if water.any():
        overlay = np.ma.masked_where(~water, np.ones_like(elevation))
        ax.imshow(overlay, cmap="Blues", alpha=0.6, origin="upper")
    if zone_mask is not None:
        from matplotlib.colors import ListedColormap
        from matplotlib.patches import Patch
        cmap = ListedColormap(["#00000000", "#FF6347", "#FFD700", "#4682B4"])
        ax.imshow(np.ma.masked_where(zone_mask == 0, zone_mask), cmap=cmap, alpha=0.55,
                  origin="upper", vmin=0, vmax=3)
        if zone_info:
            colors = {1: "#FF6347", 2: "#FFD700", 3: "#4682B4"}
            ax.legend(handles=[Patch(facecolor=colors[k], label=v["name"]) for k, v in zone_info.items()],
                      loc="lower right")
    ax.set_title(title, fontsize=13)
    ax.axis("off")
    plt.colorbar(im, ax=ax, shrink=0.6, label="고도 (m)")
    st.pyplot(fig)
    plt.close(fig)


def render_level(level: dict, idx: int, total: int):
    state = level_state(level["id"])
    task = level["task"]
    ttype = task["type"]

    st.progress((idx) / total, text=f"단계 {idx + 1} / {total} · {level['title']}")

    col_view, col_task = st.columns([3, 2])

    # ---------- 단계(stage) 결정 ----------
    with col_task:
        st.subheader(f"{idx + 1}. {level['title']}")
        st.markdown(level.get("prompt", ""))

        if "stage_range" in level:
            lo, hi = level["stage_range"]
            stage = st.slider("형성 단계", float(lo), float(hi), float(lo), 0.02,
                              key=f"learn_stage_{spec_id}_{level['id']}", format="%.2f")
        else:
            stage = float(level["stage"])
            st.caption(f"형성 단계: {stage:.0%} (고정)")

    elevation, metadata = generate_stage(spec["landform"], grid_size, stage, spec.get("generator"))

    # ---------- 지형 보기 ----------
    with col_view:
        zone_mask = None
        zone_info = None
        if "zone_mask" in metadata:
            if st.checkbox("🎨 세부 구조 보기 (존 색상)", key=f"learn_zone_{spec_id}_{level['id']}"):
                zone_mask = metadata["zone_mask"]
                zone_info = metadata.get("zone_info")
        draw_terrain_2d(elevation, f"{spec['title']} · {stage:.0%}", zone_mask, zone_info)
        if metadata.get("stage_description"):
            st.success(metadata["stage_description"])
        if st.button("🔲 3D 로 보기", key=f"learn_3d_{spec_id}_{level['id']}"):
            fig3d = render_terrain_plotly(elevation, f"{level['title']} - 3D",
                                          add_water=bool((elevation < 0).any()), water_level=0,
                                          force_camera=True)
            st.plotly_chart(fig3d, use_container_width=True, key=f"learn_3d_fig_{spec_id}_{level['id']}")

    # ---------- 과제 ----------
    with col_task:
        st.markdown("---")

        # slider_target: 먼저 목표 상태 도달
        if ttype == "slider_target":
            ok, why = evaluate_check(task["check"], metadata)
            if ok:
                state["target_reached"] = True
                st.success(f"🎯 목표 상태 도달! ({why})")
            else:
                st.info(f"🔎 현재 판정: {why}")
                if not state["target_reached"]:
                    st.caption("슬라이더를 움직여 목표 상태를 만들어 보세요.")
            if not state["target_reached"]:
                return  # 객관식은 목표 도달 후에 열린다
            if "choices" not in task:
                if not state["done"]:
                    state["done"] = True
                return

        if ttype == "observe":
            st.markdown(f"**{task.get('question', '관찰한 뒤 계속 진행하세요.')}**")
            if not state["done"] and st.button("✅ 확인했어요", key=f"learn_obs_{spec_id}_{level['id']}"):
                state["done"] = True
                st.rerun()
            return

        # multiple_choice (slider_target 뒤에 붙는 객관식 포함)
        st.markdown(f"**Q. {task['question']}**")
        choice = st.radio("보기", task["choices"], index=None,
                          key=f"learn_choice_{spec_id}_{level['id']}",
                          disabled=state["done"], label_visibility="collapsed")

        hints = task.get("hints") or []
        b1, b2 = st.columns(2)
        with b1:
            if st.button("✔️ 정답 확인", key=f"learn_check_{spec_id}_{level['id']}",
                         disabled=state["done"] or choice is None, type="primary"):
                state["attempts"] += 1
                if task["choices"].index(choice) == task["answer"]:
                    state["done"] = True
                else:
                    state["wrong"] += 1
                st.rerun()
        with b2:
            if hints and st.button(f"💡 힌트 ({min(state['hints'], len(hints))}/{len(hints)})",
                                   key=f"learn_hint_{spec_id}_{level['id']}",
                                   disabled=state["done"] or state["hints"] >= len(hints)):
                state["hints"] += 1
                st.rerun()

        for i in range(min(state["hints"], len(hints))):
            st.warning(f"힌트 {i + 1}: {hints[i]}")

        fb = task.get("feedback", {})
        if state["done"]:
            st.success(fb.get("correct", "정답입니다!"))
        elif state["wrong"] > 0:
            st.error(fb.get("incorrect", "다시 생각해 보세요."))

        solution = task.get("worked_solution")
        if solution and (state["done"] or state["wrong"] >= MAX_WRONG_BEFORE_SOLUTION):
            with st.expander("📖 풀이 보기", expanded=not state["done"]):
                st.markdown(solution.replace("\n", "  \n"))
                if not state["done"] and st.button("풀이를 읽고 넘어가기",
                                                   key=f"learn_skip_{spec_id}_{level['id']}"):
                    state["done"] = True
                    st.rerun()


def render_summary(levels: list):
    st.balloons()
    st.subheader("🏁 정리")
    st.markdown(spec.get("summary", ""))

    if spec.get("misconceptions"):
        st.markdown("#### 🚫 자주 하는 오해")
        for m in spec["misconceptions"]:
            st.markdown(f"- ~~{m['belief']}~~ → **{m['correction']}**")

    st.markdown("#### 📊 나의 기록")
    rows = []
    for lv in levels:
        s = level_state(lv["id"])
        rows.append({"단계": lv["title"], "시도": s["attempts"], "오답": s["wrong"], "힌트": s["hints"]})
    st.table(rows)

    if st.button("🔄 처음부터 다시", key=f"learn_restart_{spec_id}"):
        reset_progress()
        st.rerun()


# ==========================================================
# 탭
# ==========================================================
tab_learn, tab_teacher = st.tabs(["🎓 학습", "👩‍🏫 교사용 (검수·생성)"])

with tab_learn:
    st.header(f"🎓 {spec['title']}")
    st.caption(f"{spec.get('grade', '')} · 약 {spec.get('duration_min', '?')}분 · 지형: {spec['landform']}")

    with st.expander("🎯 학습목표", expanded=progress["level"] == 0):
        for o in spec["objectives"]:
            st.markdown(f"- {o}")

    levels = spec["levels"]
    cur = progress["level"]

    if cur >= len(levels):
        render_summary(levels)
    else:
        render_level(levels[cur], cur, len(levels))

        st.markdown("---")
        nav1, nav2, nav3 = st.columns([1, 2, 1])
        with nav1:
            if st.button("◀ 이전", disabled=cur == 0, key=f"learn_prev_{spec_id}"):
                progress["level"] = cur - 1
                st.rerun()
        with nav3:
            done = level_state(levels[cur]["id"])["done"]
            label = "정리 보기 ▶" if cur == len(levels) - 1 else "다음 ▶"
            if st.button(label, disabled=not done, key=f"learn_next_{spec_id}", type="primary"):
                progress["level"] = cur + 1
                st.rerun()
        if not done:
            with nav2:
                st.caption("과제를 완료하면 다음 단계로 넘어갈 수 있습니다.")

with tab_teacher:
    st.header("👩‍🏫 교사용")
    st.markdown(
        "이 페이지의 흐름은 **AI 가 스펙을 제안 → 교사가 검수·수정 → 검증된 엔진이 렌더링** 입니다. "
        "학생에게는 검수를 통과한 스펙만 보입니다."
    )

    if spec.get("teacher_notes"):
        st.info(f"📝 수업 메모: {spec['teacher_notes']}")

    st.markdown("#### 1) 현재 스펙")
    st.download_button("⬇️ JSON 내려받기", spec_to_json(spec), file_name=f"{spec_id}.json",
                       mime="application/json", key="learn_dl")
    with st.expander("JSON 보기"):
        st.code(spec_to_json(spec), language="json")

    st.markdown("#### 2) 스펙 붙여넣기 → 검증 → 미리보기")
    st.text_area("AI 가 제안한 스펙(JSON)을 붙여넣으세요", height=260, key="learn_paste")

    def _validate_pasted():
        # on_click 콜백: 스크립트 재실행 '전'에 돌므로 사이드바 목록에 바로 반영된다.
        try:
            candidate = json.loads(st.session_state.get("learn_paste", ""))
        except json.JSONDecodeError as e:
            st.session_state["learn_validate_result"] = {"errors": [f"JSON 문법 오류: {e}"]}
            return
        errors = validate_spec(candidate, known_landforms=available_landforms())
        if errors:
            st.session_state["learn_validate_result"] = {"errors": errors}
            return
        st.session_state[CUSTOM_KEY] = candidate
        st.session_state[PROGRESS_KEY].pop(candidate.get("id", "__custom__"), None)
        st.session_state["learn_validate_result"] = {"ok": candidate.get("title", candidate.get("id"))}

    st.button("🔍 검증", key="learn_validate", on_click=_validate_pasted)
    result = st.session_state.pop("learn_validate_result", None)
    if result:
        if "errors" in result:
            st.error("검증 실패. 아래 항목을 고쳐 주세요.")
            for e in result["errors"]:
                st.markdown(f"- {e}")
        else:
            st.success(f"검증 통과: '{result['ok']}'. 왼쪽 '활동 선택'에 '(검수 중)' 항목으로 추가되었습니다. "
                       "학습 탭에서 직접 풀어 보며 검수하세요.")

    st.markdown("#### 3) AI 에게 초안 요청하기")
    st.caption("아래 프롬프트를 복사해 사용하는 LLM 에 붙여넣으면 이 형식의 스펙 초안을 받을 수 있습니다. 받은 JSON 은 2) 에서 검증하세요.")
    landform_for_prompt = st.selectbox("대상 지형", available_landforms(),
                                       index=available_landforms().index(spec["landform"])
                                       if spec["landform"] in available_landforms() else 0,
                                       key="learn_prompt_landform")
    key_rows = describe_check_keys(landform_for_prompt)

    def _fmt(v):
        return f"{v:g}" if abs(v) >= 1 or v == 0 else f"{v:.2f}"

    key_lines = []
    for row in key_rows:
        path = " → ".join(f"{int(s * 100)}%: {_fmt(v)}" for s, v in zip(row["stages"], row["values"]))
        note = " (목록 길이, len_gte 사용)" if row["measure"] == "len" else ""
        if row["resolution_dependent"]:
            note += " ⚠️ 해상도에 따라 값이 달라짐, 가급적 쓰지 말 것"
        key_lines.append(f"- {row['key']}: {path}{note}")
    usable_keys = "\n".join(key_lines)
    with st.expander(f"🔑 '{landform_for_prompt}' 판정에 쓸 수 있는 키 ({len(key_rows)}개)"):
        st.markdown(usable_keys.replace("\n", "  \n"))
    schema_doc = open(os.path.join(ROOT, "learning", "schema.py"), encoding="utf-8").read().split('"""')[1]
    example = spec_to_json(bundled[next(iter(bundled))])
    prompt = f"""당신은 고등학교 지리 교사를 돕는 교육 설계 보조입니다.
아래 형식(spec_version {SPEC_VERSION})으로 '{landform_for_prompt}' 지형에 대한 학습 활동 스펙(JSON)을 작성하세요.

요구사항
- 대상: [학년/과목을 적으세요]. 학습목표 2~3개.
- 단계(level) 3~4개. 각 단계에 과제 1개, 계층형 힌트 3개, 정오답 피드백, 풀이(worked_solution).
- 최소 1개 단계는 slider_target 과제로 만들고, check 에는 아래 '사용 가능한 메타데이터 키'만 쓰세요.
- 자주 하는 오해(misconceptions) 2개 이상.
- 한국 교육과정 용어를 쓰고, 지형 형성 '원인 → 과정 → 결과' 순서를 지키세요.
- JSON 만 출력하세요.

사용 가능한 메타데이터 키 (slider_target 의 check.key). 형성 단계별 값을 보고 기준값(check.value)을 정하세요.
stage_range 의 시작에서는 판정이 실패하고, 끝에서는 통과해야 합니다.
{usable_keys}

check.op: equals | gte | lte | contains | len_gte | truthy
"_stage" 는 형성 단계(0~1)로 모든 지형에서 쓸 수 있지만, 지형의 실제 상태를 나타내는 다른 키를 우선하세요.

형식 설명:
{schema_doc.strip()}

예시(다른 지형):
{example}
"""
    st.code(prompt, language="markdown")
