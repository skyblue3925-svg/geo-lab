from __future__ import annotations

from collections.abc import MutableMapping
from dataclasses import dataclass
from typing import Any

import numpy as np

from engine.ideal_landforms import IDEAL_LANDFORM_GENERATORS
from engine.simple_lem import SimpleLEM
from app.utils.high_school_world_geography import get_high_school_world_topic

LAB_THEORY_EXAMPLE_TEXT = (
    "상류에서 단층성 융기가 반복되고 하천 에너지가 커져 침식이 강해졌다. "
    "중류 이후에는 경사가 완만해지며 퇴적이 누적되어 선상지와 평야가 발달했다. "
    "장기적으로 점진적 변화가 우세하다."
)


@dataclass(frozen=True)
class LabScenarioConfig:
    landform_type: str = "general"
    detailed_type: str | None = None
    generator_key: str | None = None
    custom_surface: str | None = None
    precipitation: float | None = None
    settling_velocity: float | None = None
    sea_level: float | None = None
    glacial_erosion: float | None = None
    aeolian_erosion: float | None = None
    volcanic_rate: float | None = None
    fault_rate: float | None = None
    fold_rate: float | None = None
    fold_wavelength: float | None = None
    wind_direction: float | None = None
    fold_axis: str | None = None
    water_table: float | None = None
    spring_rate: float | None = None
    freeze_elevation: float | None = None
    k_scale: float = 1.0
    d_scale: float = 1.0
    u_scale: float = 1.0
    enable_sediment_transport: bool = False
    enable_lateral_erosion: bool = False
    enable_glacial: bool = False
    enable_glacial_deposit: bool = False
    enable_marine: bool = False
    enable_karst: bool = False
    enable_aeolian: bool = False
    enable_volcanic: bool = False
    enable_faulting: bool = False
    enable_folding: bool = False
    enable_groundwater: bool = False
    enable_freeze_thaw: bool = False
    enable_landslides: bool = False


def create_lab_simple_lem(
    *,
    grid_size: int,
    K: float,
    D: float,
    U: float,
    enable_isostasy: bool,
    enable_karst: bool,
    enable_exner: bool,
    enable_slope_stability: bool,
) -> SimpleLEM:
    lem = SimpleLEM(
        grid_size=grid_size,
        K=K,
        D=D,
        U=U,
        enable_flexure=enable_isostasy,
        enable_karst=enable_karst,
        enable_landslides=enable_slope_stability,
    )

    # Preserve legacy flags referenced by the Lab UI while mapping to supported engine flags.
    lem.enable_isostasy = enable_isostasy
    lem.enable_exner = enable_exner
    lem.enable_slope_stability = enable_slope_stability
    return lem


def apply_lab_theory_example(session_state: MutableMapping[str, Any]) -> None:
    session_state["lab_theory_text"] = LAB_THEORY_EXAMPLE_TEXT


def get_lab_playback_guidance(student_mode: bool) -> dict[str, str]:
    if student_mode:
        return {
            "preview_heading": "학생용 연속 재생",
            "preview_caption": (
                "위의 3D 애니메이션은 자동으로 이어지고, 아래 슬라이더는 다시 보고 싶은 "
                "장면을 고를 때 사용합니다."
            ),
            "comparison_heading": "장면 고정 비교",
            "comparison_caption": (
                "선택한 시점의 지형을 따로 고정해 보고, 변화량과 단면을 함께 확인합니다."
            ),
        }

    return {
        "preview_heading": "교사용 자동 미리보기",
        "preview_caption": (
            "자동 재생을 켜면 위의 3D 미리보기가 바로 움직입니다. 아래 슬라이더는 "
            "같은 결과를 한 시점에 고정해 비교하는 용도입니다."
        ),
        "comparison_heading": "프레임 고정 비교",
        "comparison_caption": (
            "슬라이더로 특정 시점을 멈춰 보고, 필요하면 현재 결과를 GIF로도 저장합니다."
        ),
    }


_HIGH_SCHOOL_TOPIC_BY_KEYWORD: tuple[tuple[str, str], ...] = (
    ("선상지", "alluvial_fan"),
    ("삼각주", "delta"),
    ("곡류", "free_meander"),
    ("V자곡", "v_valley"),
    ("U자곡", "u_valley"),
    ("피오르", "fjord"),
    ("해식애", "coastal_cliff"),
    ("카르스트", "karst_doline"),
    ("화산", "stratovolcano"),
    ("바르한", "barchan"),
)


_HIGH_SCHOOL_TOPIC_BY_STORY_KEY: dict[str, str] = {
    "v_valley": "v_valley",
    "alluvial_fan": "alluvial_fan",
    "delta": "delta",
    "meander": "free_meander",
    "u_valley": "u_valley",
    "fjord": "fjord",
    "karst_doline": "karst_doline",
    "stratovolcano": "stratovolcano",
    "barchan": "barchan",
}


def _resolve_high_school_topic_id(selected_landform: str, story_key: str | None = None) -> str | None:
    for keyword, topic_id in _HIGH_SCHOOL_TOPIC_BY_KEYWORD:
        if keyword in selected_landform:
            return topic_id
    if story_key:
        return _HIGH_SCHOOL_TOPIC_BY_STORY_KEY.get(story_key)
    return None


def _get_high_school_lab_topic(selected_landform: str, story_key: str | None = None) -> dict[str, Any] | None:
    topic_id = _resolve_high_school_topic_id(selected_landform, story_key)
    if not topic_id:
        return None
    return get_high_school_world_topic(topic_id)


def _get_high_school_stage(
    selected_landform: str,
    story_key: str,
    stage_idx: int,
) -> dict[str, Any] | None:
    topic = _get_high_school_lab_topic(selected_landform, story_key)
    if not topic:
        return None
    stages = topic.get("stages") or []
    if 0 <= stage_idx < len(stages):
        return dict(stages[stage_idx])
    return None


def _format_high_school_process_order(topic: dict[str, Any] | None) -> str | None:
    if not topic:
        return None
    stages = topic.get("stages") or []
    dominant_processes = [
        str(stage.get("dominant_process"))
        for stage in stages
        if stage.get("dominant_process")
    ]
    if not dominant_processes:
        return None
    return " → ".join(dominant_processes)


def get_lab_teaching_notes(selected_landform: str) -> dict[str, str]:
    default_notes = {
        "concept": "\uc9c0\ud615 \ubcc0\ud654\ub294 \uce68\uc2dd, \ud1f4\uc801, \uc735\uae30, \uc6a9\ud574 \uac19\uc740 \uacfc\uc815\uc774 \uc5b4\ub514\uc11c \uc6b0\uc138\ud55c\uc9c0\uc5d0 \ub530\ub77c \ub2ec\ub77c\uc9d1\ub2c8\ub2e4.",
        "focus": "\ucc98\uc74c \ubcc0\ud558\ub294 \uc704\uce58\uc640 \uac00\uc7a5 \ub290\ub9ac\uac8c \ub0a8\ub294 \ubd80\ubd84\uc744 \ube44\uad50\ud574 \ubcf4\uc138\uc694.",
        "question": "\uc5b4\ub5a4 \uacfc\uc815\uc774 \uc774 \uc9c0\ud615 \ubcc0\ud654\ub97c \uc9c0\ubc30\ud588\ub294\uc9c0 \uc124\uba85\ud560 \uc218 \uc788\ub098\uc694?",
        "takeaway": "\uad50\uacfc\uc11c\uc5d0 \ub098\uc624\ub294 \ub300\ud45c \ud615\ud0dc\ub294 \ubcf4\ud1b5 \ud55c \uac00\uc9c0 \uacfc\uc815\ub9cc\uc774 \uc544\ub2c8\ub77c \uc5ec\ub7ec \uc791\uc6a9\uc758 \uacb0\uacfc\uc785\ub2c8\ub2e4.",
    }

    landform_overrides = [
        (
            "\uc120\uc0c1\uc9c0",
            {
                "concept": "\uc120\uc0c1\uc9c0\ub294 \uc0b0\uc9c0 \ucd9c\uad6c\uc5d0\uc11c \uc720\uc218\uc758 \uc5d0\ub108\uc9c0\uac00 \uae09\uac70\ud788 \ub5a8\uc5b4\uc9c0\uba70, \ud1f4\uc801\ubb3c\uc774 \ubd80\ucc44\uaf34 \ud615\ud0dc\ub85c \ud37c\uc838 \uc313\ud788\ub294 \uc9c0\ud615\uc785\ub2c8\ub2e4.",
                "focus": "\uc0b0\ub85d \ucd9c\uad6c\uc5d0\uc11c \ud3c9\uc57c\ub85c \ub098\uac08\uc218\ub85d \uc720\ub85c\uac00 \ub108\ud2b8\ub7ec\uc9c0\uace0, \uc911\uc559\ubd80\uc640 \uac00\uc7a5\uc790\ub9ac\uc5d0\uc11c \ub4a4\ud14c\uac00 \uc5b4\ub5bb\uac8c \ubc1c\ub2ec\ud558\ub294\uc9c0 \ubcf4\uc138\uc694.",
                "question": "\uc65c \ud1f4\uc801\uc774 \ud558\ucc9c \uc548\uc774 \uc544\ub2c8\ub77c \uc0b0\uc9c0 \uc785\uad6c\uc5d0\uc11c \ubd80\ucc44\uaf34 \ud615\ud0dc\ub85c \uc2dc\uc791\ud560\uae4c\uc694?",
                "takeaway": "\uc120\uc0c1\uc9c0\ub294 \uc5d0\ub108\uc9c0 \uac10\uc18c, \uacbd\uc0ac \uac10\uc18c, \uc720\ub7c9 \ubd84\uc0b0\uc774 \ud568\uaed8 \uc791\ub3d9\ud558\uba74\uc11c \ud615\uc131\ub418\ub294 \ud1f4\uc801 \uc9c0\ud615\uc785\ub2c8\ub2e4.",
            },
        ),
        (
            "\uace1\ub958",
            {
                "concept": "\uace1\ub958 \ud558\ucc9c\uc740 \ubc14\uae65 \uacf3\uc5d0\uc11c\ub294 \uae4e\uc774\uace0, \uc548\ucabd\uc5d0\uc11c\ub294 \uc313\uc774\uba70 \ud1b5\ub85c\uac00 \uc190\uc2a4\ub7fd\uac8c \uc774\ub3d9\ud558\ub294 \uc7a5\uc18c\uc785\ub2c8\ub2e4.",
                "focus": "\ubc14\uae65 \uad7d\uc774\uc5d0\uc11c \uce68\uc2dd, \uc548\ucabd \uad7d\uc774\uc5d0\uc11c \ud1f4\uc801\uc774 \ubc84\uc5b4\uc9c0\ub294 \uacbd\uacc4\ub97c \uc2dc\uc18c\ub85c \ubcf4\uc138\uc694.",
                "question": "\uc218\ub85c\uac00 \uc65c \uc9c1\uc120\uc73c\ub85c \ub0a8\uc9c0 \uc54a\uace0 \uc88c\uc6b0\ub85c \ud754\ub4e4\ub9b4\uae4c\uc694?",
                "takeaway": "\uce68\uc2dd\uacfc \ud1f4\uc801\uc774 \ucd95\uacfc \ub0b4\ub9ac\uba74\uc11c \ub3d9\uc2dc\uc5d0 \uc77c\uc5b4\ub098\ub294 \uacbd\uacc4 \ubcc0\ud654\ub97c \ubcf4\uc5ec\uc904 \uc218 \uc788\uc2b5\ub2c8\ub2e4.",
            },
        ),
        (
            "\ud574\uc2dd\uc560",
            {
                "concept": "\ud574\uc2dd\uc560\ub294 \ud30c\ub791 \uce68\uc2dd\uc774 \uc808\ubcbd \ud558\ubd80\ub97c \uae4e\uc544 \ud6c4\ud1f4\uc2dc\ud0a4\ub294 \ud574\uc548 \uc9c0\ud615\uc785\ub2c8\ub2e4.",
                "focus": "\uc808\ubcbd \uc544\ub798 \ud3ec\uc778\ud2b8\uc5d0\uc11c \uc5b4\ub5a4 \uacf3\uc774 \uba3c\uc800 \uae4e\uc774\ub294\uc9c0 \ubcf4\uc138\uc694.",
                "question": "\ud574\uc548\uc120\uc774 \uc55e\uc73c\ub85c \ub098\uac00\ub294 \uac83\uc774 \uc544\ub2c8\ub77c \ub4a4\ub85c \ubb3c\ub7ec\ub098\ub294 \uc774\uc720\ub294 \ubb34\uc5c7\uc77c\uae4c\uc694?",
                "takeaway": "\ud30c\ub791 \uc5d0\ub108\uc9c0\uac00 \uae4e\uc774\uace0 \ub4a4\ud1f4\ub97c \ub9cc\ub4dc\ub294 \uc9c0\uc810\uc774 \ud574\uc548 \ud615\ud0dc\ub97c \uacb0\uc815\ud569\ub2c8\ub2e4.",
            },
        ),
        (
            "\ubc14\ub974\ud55c",
            {
                "concept": "\ubc14\ub974\ud55c\uc740 \ud55c \ubc29\ud5a5 \ubc14\ub78c\uc774 \uc9c0\uc18d\ub420 \ub54c \uc774\ub3d9\ud558\ub294 \uc0ac\uad6c \uc9c0\ud615\uc785\ub2c8\ub2e4.",
                "focus": "\ubc14\ub78c\uc774 \ubd88\uc5b4\uc624\ub294 \ucabd\uacfc \uc0ac\uad6c \uaf2c\ub9ac \ubc29\ud5a5\uc744 \ud568\uaed8 \ubcf4\uc138\uc694.",
                "question": "\uc65c \uc0ac\uad6c\uc758 \ubaa8\uc591\uacfc \uc774\ub3d9 \ubc29\ud5a5\uc774 \ubc14\ub78c \ubc29\ud5a5\uacfc \uc5f0\uacb0\ub420\uae4c\uc694?",
                "takeaway": "\uc5d0\uc62c\ub9b0 \ubaa8\ub798\uac00 \uc5b4\ub514\uc5d0 \ub2e4\uc2dc \uc313\uc774\ub294\uc9c0\uac00 \uc0ac\uad6c\uc758 \uacbd\uc0ac\uacfc \uc774\ub3d9\uc5d0 \ub530\ub77c \ubd80\ub958\uac00 \ub2ec\ub77c\uc9d1\ub2c8\ub2e4.",
            },
        ),
    ]

    base_notes = default_notes
    if "습곡" in selected_landform:
        base_notes = {
            "concept": "습곡 산지는 압축을 받아 지층이 물결처럼 휘어 오르며 만들어지고, 이후 풍화와 침식이 능선과 골짜기를 다시 다듬는 구조 지형입니다.",
            "focus": "길게 이어지는 능선 축과 그 사이 낮아지는 골짜기 축이 평행하게 반복되는지 보세요.",
            "question": "왜 습곡 산지에서는 융기 직후보다 시간이 지난 뒤에 능선과 골짜기 대비가 더 또렷해질까요?",
            "takeaway": "습곡은 지형의 골격을 만드는 내적 작용이고, 실제 표면 모양은 그 위에 외적 작용이 겹쳐져 읽혀야 합니다.",
        }
    else:
        for keyword, notes in landform_overrides:
            if keyword in selected_landform:
                base_notes = notes
                break

    note_map = [
        ("\uc120\uc0c1\uc9c0", {
            "concept": "\uc120\uc0c1\uc9c0\ub294 \uc0b0\uc9c0 \ucd9c\uad6c\uc5d0\uc11c \uc720\uc218 \uc5d0\ub108\uc9c0\uac00 \uae09\uac70\ud788 \ub5a8\uc5b4\uc9c0\uba70 \ud1f4\uc801\ubb3c\uc774 \ud37c\uc838 \uc313\uc774\ub294 \uc9c0\ud615\uc785\ub2c8\ub2e4.",
            "focus": "\uc0b0\ub85d \ucd9c\uad6c\uc5d0\uc11c \ud3c9\uc57c\ub85c \ub098\uac08\uc218\ub85d \uacbd\uc0ac\uac00 \uc5b4\ub5bb\uac8c \ub204\uadf8\ub7ec\uc9c0\ub294\uc9c0 \ubcf4\uc138\uc694.",
            "question": "\uc65c \ud1f4\uc801\uc774 \ud558\ucc9c \uc548\uc774 \uc544\ub2c8\ub77c \uc0b0\uc9c0 \uc785\uad6c\uc5d0\uc11c \ud37c\uc9c0\uae30 \uc2dc\uc791\ud560\uae4c\uc694?",
            "takeaway": "\uc5d0\ub108\uc9c0 \uac10\uc18c\uac00 \ud1f4\uc801 \uc704\uce58\ub97c \uacb0\uc815\ud55c\ub2e4\ub294 \uc810\uc774 \ud575\uc2ec\uc785\ub2c8\ub2e4.",
        }),
        ("\uace1\ub958", {
            "concept": "\uace1\ub958 \ud558\ucc9c\uc740 \ubc14\uae65 \uacf3\uc5d0\uc11c\ub294 \uae4e\uc774\uace0 \uc548\ucabd\uc5d0\uc11c\ub294 \uc313\uc774\uba70 \ud1b5\ub85c\uac00 \uc774\ub3d9\ud569\ub2c8\ub2e4.",
            "focus": "\ubc14\uae65 \uad7d\uc774\uc5d0\uc11c \uce68\uc2dd, \uc548\ucabd \uad7d\uc774\uc5d0\uc11c \ud1f4\uc801\uc774 \ubc84\uc5b4\uc9c0\ub294\uc9c0 \ube44\uad50\ud574 \ubcf4\uc138\uc694.",
            "question": "\uc218\ub85c\uac00 \uc65c \uc9c1\uc120\uc73c\ub85c \ub0a8\uc9c0 \uc54a\uace0 \uc88c\uc6b0\ub85c \ud754\ub4e4\ub9b4\uae4c\uc694?",
            "takeaway": "\uce68\uc2dd\uacfc \ud1f4\uc801\uc774 \uac19\uc740 \ud558\ucc9c \uc548\uc5d0\uc11c \ub3d9\uc2dc\uc5d0 \uc77c\uc5b4\ub09c\ub2e4\ub294 \uc810\uc744 \ubcf4\uc5ec\uc904 \uc218 \uc788\uc2b5\ub2c8\ub2e4.",
        }),
        ("V\uc790\uace1", {
            "concept": "V\uc790\uace1\uc740 \ud558\ucc9c\uc774 \uae4a\uac8c \ud30c\ub0b4\ub9ac\uba70 \uacc4\uace1\uc744 \uc0dd\uc131\ud560 \ub54c \ub098\ud0c0\ub098\ub294 \uc804\ud615 \ud615\ud0dc\uc785\ub2c8\ub2e4.",
            "focus": "\uacc4\uace1\uc758 \uae4a\uc774\uac00 \uba3c\uc800 \ucee4\uc9c0\uace0, \ud3ed\uc740 \ub290\ub9ac\uac8c \ud655\uc7a5\ub418\ub294\uc9c0 \ubcf4\uc138\uc694.",
            "question": "\uc65c \ud3ed\ubcf4\ub2e4 \uae4a\uc774 \ubcc0\ud654\uac00 \uba3c\uc800 \ub4dc\ub7ec\ub098\ub098\uc694?",
            "takeaway": "\ud558\ucc9c \uce68\uc2dd \uc5d0\ub108\uc9c0\uac00 \ud55c \uacf3\uc73c\ub85c \uc9d1\uc911\ub420 \ub54c \uacc4\uace1 \ub2e8\uba74\uc774 \ub0a0\uce74\ub86d\uac8c \ud615\uc131\ub429\ub2c8\ub2e4.",
        }),
        ("U\uc790\uace1", {
            "concept": "U\uc790\uace1\uc740 \ube59\ud558\uac00 \uacc4\uace1 \ubc14\ub2e5\uacfc \uc0ac\uba74\uc744 \ud568\uaed8 \ub2e4\ub4ec\uc73c\uba70 \ub113\uace0 \ub465\uae00\uac8c \ub9cc\ub4ed\ub2c8\ub2e4.",
            "focus": "\ubc14\ub2e5\uc774 \ud3c9\ud3c9\ud574\uc9c0\uace0 \uc0ac\uba74\uc774 \ud6c4\ud1f4\ud558\ub294 \ubc29\uc2dd\uc744 \ud655\uc778\ud558\uc138\uc694.",
            "question": "\ud558\ucc9c \uacc4\uace1\uacfc \ube59\ud558 \uacc4\uace1\uc758 \ub2e8\uba74\uc740 \uc65c \ub2ec\ub77c\uc9c8\uae4c\uc694?",
            "takeaway": "\uce68\uc2dd \uc8fc\uccb4\uac00 \ubb3c\uc778\uc9c0 \ube59\ud558\uc778\uc9c0\uc5d0 \ub530\ub77c \uacc4\uace1 \ub2e8\uba74\uc774 \ud06c\uac8c \ub2ec\ub77c\uc9d1\ub2c8\ub2e4.",
        }),
        ("\ud574\uc2dd\uc560", {
            "concept": "\ud574\uc2dd\uc560\ub294 \ud30c\ub791 \uce68\uc2dd\uc774 \uc808\ubcbd \ud558\ubd80\ub97c \uae4e\uc544 \ud6c4\ud1f4\uc2dc\ud0a4\ub294 \ud574\uc548 \uc9c0\ud615\uc785\ub2c8\ub2e4.",
            "focus": "\uc808\ubcbd \uc544\ub798 \ud3ec\uc778\ud2b8에\uc11c \uc5b4\ub5a4 \uacf3\uc774 \uba3c\uc800 \uae4e\uc774\ub294\uc9c0 \ubcf4\uc138\uc694.",
            "question": "\ud574\uc548\uc120\uc774 \uc55e\uc73c\ub85c \ub098\uac00\ub294 \uac83\uc774 \uc544\ub2c8\ub77c \ub4a4\ub85c \ubb3c\ub7ec\ub098\ub294 \uc774\uc720\ub294 \ubb34\uc5c7\uc77c\uae4c\uc694?",
            "takeaway": "\ud574\uc548 \uc9c0\ud615\uc5d0\uc11c\ub294 \ud30c\ub791 \uc5d0\ub108\uc9c0\uac00 \uc9c0\ud615 \ud6c4\ud1f4\ub97c \uacb0\uc815\ud569\ub2c8\ub2e4.",
        }),
        ("\ubc14\ub974\ud55c", {
            "concept": "\ubc14\ub974\ud55c\uc740 \ud55c \ubc29\ud5a5 \ubc14\ub78c\uc774 \uc9c0\uc18d\ub420 \ub54c \uc774\ub3d9\ud558\ub294 \uc0ac\uad6c \uc9c0\ud615\uc785\ub2c8\ub2e4.",
            "focus": "\ubc14\ub78c \ubd88\uc5b4\uc624\ub294 \ucabd\uacfc \uc0ac\uad6c \uaf2c\ub9ac \ubc29\ud5a5\uc744 \ud568\uaed8 \ubcf4\uc138\uc694.",
            "question": "\uc65c \uc0ac\uad6c의 \ubaa8\uc591\uacfc \uc774\ub3d9 \ubc29\ud5a5\uc774 \ubc14\ub78c \ubc29\ud5a5과 \uc5f0\uacb0\ub420\uae4c\uc694?",
            "takeaway": "\uc5d0\uc62c\ub9b0 \ubaa8\ub798\uac00 \uc5b4\ub514\uc5d0 \ub2e4\uc2dc \uc313\uc774\ub294\uc9c0\uac00 \uc0ac\uad6c\uc758 \ubaa8\uc591\uc744 \uacb0\uc815\ud569\ub2c8\ub2e4.",
        }),
        ("\uce74\ub974\uc2a4\ud2b8", {
            "concept": "\uce74\ub974\uc2a4\ud2b8\ub294 \ubb3c\uc774 \uc554\uc11d\uc744 \uc6a9\ud574\ud558\uba70 \uc9c0\ud558\uacf5\uac04\uacfc \ud568\ubab0\uc9c0\ub97c \ub9cc\ub4ed\ub2c8\ub2e4.",
            "focus": "\ud45c\uba74 \ub192\ub0ae\uc774\uac00 \uc904\uc5b4\ub4e4\uba70 \ud568\ubab0 \ud3ec\uc778\ud2b8\uac00 \uc0dd\uae30\ub294 \uc5ed\uc21c\uc744 \ubcf4\uc138\uc694.",
            "question": "\uce68\uc2dd\uacfc \ub2ec\ub9ac \uc6a9\ud574\ub294 \uc65c \uc9c0\ud615\uc744 \uc548\ucabd\uc73c\ub85c \uaebc\uc9c0\uac8c \ub9cc\ub4e4\uae4c\uc694?",
            "takeaway": "\ud45c\uba74 \ubc14\ub85c \uc704\uc5d0\uc11c \uae4e\uc774\ub294 \uac83과 \uc548\ucabd\uc73c\ub85c \ub179\uc544 \ub4e4\uc5b4\uac00\ub294 \uac83\uc740 \ub2e4\ub978 \uc791\uc6a9\uc785\ub2c8\ub2e4.",
        }),
        ("\ud654\uc0b0", {
            "concept": "\ud654\uc0b0 \uc9c0\ud615\uc740 \ubd84\ucd9c\ubb3c\uc774 \uc313\uc774\uac70\ub098 \ud568\ubab0\ud558\uba74\uc11c \ud615\ud0dc\uac00 \ubc1c\ub2ec\ud569\ub2c8\ub2e4.",
            "focus": "\uc911\uc2ec \ubd84\ud654\uad6c \uadfc\ucc98\uc758 \uc0c1\ud558 \ubcc0\ud654\uc640 \uc0ac\uba74 \ud655\uc7a5\uc744 \ud568\uaed8 \ubcf4\uc138\uc694.",
            "question": "\ud654\uc0b0 \uc9c0\ud615\uc740 \uce68\uc2dd\ub9cc\uc73c\ub85c \ub9cc\ub4dc\ub294 \uac83\uacfc \uc5b4\ub5bb\uac8c \ub2e4\ub97c\uae4c\uc694?",
            "takeaway": "\uc313\uc774\ub294 \uacfc\uc815과 \uae4e\uc774\ub294 \uacfc\uc815\uc774 \ub3d9\uc2dc\uc5d0 \uc874\uc7ac\ud558\ub294 \uc9c0\ud615\uc774 \ud654\uc0b0\uc785\ub2c8\ub2e4.",
        }),
    ]

    for keyword, notes in note_map:
        if keyword in selected_landform:
            base_notes = notes
            break

    story_key = _match_process_story_key(selected_landform)
    topic = _get_high_school_lab_topic(selected_landform, story_key)
    if not topic:
        return base_notes

    notes = dict(base_notes)
    notes.update(
        {
            "concept": str(topic.get("classroom_goal") or notes["concept"]),
            "focus": str(topic.get("observation_focus") or notes["focus"]),
            "question": str(topic.get("student_question") or notes["question"]),
            "world_case": str((topic.get("world_case") or {}).get("title") or ""),
            "world_location": str((topic.get("world_case") or {}).get("location_label") or ""),
            "teacher_note": str(topic.get("teacher_note") or ""),
        }
    )
    return notes


_PROCESS_METADATA: dict[str, dict[str, str]] = {
    "mean_weathering_rate": {"label": "풍화", "group": "외적"},
    "mean_erosion_rate": {"label": "하천 침식", "group": "외적"},
    "mean_diffusion": {"label": "사면 이동", "group": "외적"},
    "mean_deposition_rate": {"label": "퇴적", "group": "외적"},
    "mean_lateral_erosion": {"label": "측방 침식", "group": "외적"},
    "mean_glacial": {"label": "빙하 침식", "group": "외적"},
    "mean_marine": {"label": "해안 침식", "group": "외적"},
    "mean_landslide": {"label": "질량 이동", "group": "외적"},
    "mean_karst": {"label": "용해", "group": "외적"},
    "mean_aeolian": {"label": "바람 이동", "group": "외적"},
    "mean_groundwater": {"label": "지하수 침식", "group": "외적"},
    "mean_freeze_thaw": {"label": "동결 파쇄", "group": "외적"},
    "mean_moraine": {"label": "빙하 퇴적", "group": "외적"},
    "mean_uniform_uplift": {"label": "융기", "group": "내적"},
    "mean_subsidence": {"label": "침강", "group": "내적"},
    "mean_faulting": {"label": "단층 운동", "group": "내적"},
    "mean_folding": {"label": "습곡", "group": "내적"},
    "mean_volcanic": {"label": "화산 분출", "group": "내적"},
}


_GENERIC_PROCESS_STAGES = (
    {
        "title": "1단계: 기반 조건 형성",
        "summary": "먼저 융기·단층 같은 내적 작용이 지형 골격을 만들고, 그 위에 풍화와 침식이 어디서 시작될지 조건이 정해집니다.",
        "caption": "지형 변화는 처음부터 침식만 일어나는 것이 아니라, 내적 작용이 만든 높낮이 차 위에서 외적 작용이 반응하며 시작됩니다.",
        "focus": "높은 곳과 낮은 곳의 대비, 급경사 시작 지점을 먼저 찾아보세요.",
        "question": "이 지형에서 외적 작용이 가장 먼저 집중될 곳은 어디일까요?",
        "process_order": "내적 작용(융기·단층) → 외적 작용(풍화·침식·이동·퇴적)",
    },
    {
        "title": "2단계: 침식과 이동 시작",
        "summary": "풍화로 생긴 물질이 하천, 바람, 빙하, 파랑 같은 운반 매체를 따라 이동하며 침식 경로가 드러납니다.",
        "caption": "이 단계부터는 깎이는 곳과 운반되는 길이 분리되기 시작합니다.",
        "focus": "상류 공급지와 물질이 지나가는 길을 연결해서 보세요.",
        "question": "어떤 경로를 따라 물질이 이동하고 있나요?",
        "process_order": "풍화 → 침식 → 이동",
    },
    {
        "title": "3단계: 지형 형태 강화",
        "summary": "침식과 퇴적이 반복되며 교과서에서 보는 대표 지형 단면이 뚜렷해지는 구간입니다.",
        "caption": "형태가 선명해지는 이유는 한 가지 작용이 강해서가 아니라, 공급과 제거가 반복 누적되기 때문입니다.",
        "focus": "깎이는 면과 쌓이는 면의 위치가 서로 어떻게 대응되는지 보세요.",
        "question": "지형의 대표 형태를 만든 핵심 작용 조합은 무엇인가요?",
        "process_order": "침식·이동 반복 → 특정 위치 집중 퇴적/절리 발달",
    },
    {
        "title": "4단계: 결과 해석",
        "summary": "최종 형태를 보고 어떤 내적 작용이 기반을 만들고, 어떤 외적 작용이 표면을 다듬었는지 설명할 수 있는 단계입니다.",
        "caption": "지형 해석은 결과 모양만 보는 것이 아니라, 그 모양을 만든 과정 순서를 읽는 일입니다.",
        "focus": "처음 지형과 마지막 지형을 비교하며 높아진 곳, 낮아진 곳, 넓어진 곳을 정리하세요.",
        "question": "최종 지형을 만든 주된 내적 작용과 외적 작용을 각각 한 가지씩 고르세요.",
        "process_order": "기반 형성 → 침식/이동 → 퇴적/재가공 → 결과 해석",
    },
)


_LANDFORM_PROCESS_STAGES: dict[str, tuple[dict[str, str], ...]] = {
    "folded_range": (
        {
            "title": "1단계: 압축과 습곡 시작",
            "summary": "횡압축이 가해지며 지층이 휘어 오르고, 배사와 향사의 골격이 만들어집니다.",
            "caption": "습곡 산지는 먼저 구조 운동이 지형의 큰 틀을 만듭니다.",
            "focus": "길게 이어지는 융기 축과 내려앉는 축을 구분해 보세요.",
            "question": "왜 습곡은 한 점이 아니라 길게 이어진 띠 모양으로 나타날까요?",
            "process_order": "압축 → 습곡 → 구조적 융기",
        },
        {
            "title": "2단계: 구조 차별과 풍화",
            "summary": "솟아오른 능선과 낮은 골짜기 사이에서 풍화와 하천 침식이 다른 속도로 반응하기 시작합니다.",
            "caption": "내적 작용이 만든 높낮이 차가 외적 작용의 집중 위치를 정해 줍니다.",
            "focus": "능선 축과 그 사이 물길이 형성되는 곳을 함께 보세요.",
            "question": "습곡 축이 생긴 뒤 침식은 어디에 먼저 집중될까요?",
            "process_order": "습곡 골격 형성 → 풍화·하천 침식 시작",
        },
        {
            "title": "3단계: 능선-골짜기 대비 강화",
            "summary": "단단한 부분은 능선으로 남고, 낮은 축과 약한 구간은 더 깎이며 평행한 지형 배열이 강화됩니다.",
            "caption": "습곡 산지의 표면 모양은 구조 운동과 차별 침식이 함께 만든 결과입니다.",
            "focus": "연속된 능선과 그 사이 골짜기의 반복성을 보세요.",
            "question": "왜 습곡 산지에서는 구조선과 침식 골짜기가 서로 맞물려 보일까요?",
            "process_order": "습곡 → 차별 침식 → 능선·골짜기 분화",
        },
        {
            "title": "4단계: 구조 지형 해석",
            "summary": "최종 지형을 통해 내적 작용이 만든 골격과 외적 작용이 다듬은 표면을 나누어 설명할 수 있습니다.",
            "caption": "습곡 산지 해석의 핵심은 지형 모양과 과정 순서를 함께 읽는 것입니다.",
            "focus": "배사 능선과 향사 저지를 묶어 해석해 보세요.",
            "question": "이 지형에서 내적 작용과 외적 작용은 각각 어떤 흔적을 남겼나요?",
            "process_order": "구조 골격 형성 → 풍화·침식 → 지형 해석",
        },
    ),
    "v_valley": (
        {
            "title": "1단계: 융기와 골짜기 시작",
            "summary": "지표가 융기해 경사가 커지고, 하천이 한 줄로 집중되며 하방 침식 조건이 만들어집니다.",
            "caption": "V자곡의 출발점은 높은 지형 경사와 집중된 유수 에너지입니다.",
            "focus": "상류의 급경사와 본류 위치를 먼저 보세요.",
            "question": "왜 계곡 폭보다 깊이가 먼저 커질까요?",
            "process_order": "융기 → 하천 하방 침식 → 사면 이동",
        },
        {
            "title": "2단계: 하방 침식 심화",
            "summary": "하천이 바닥을 집중적으로 깎고, 양쪽 사면에서는 풍화와 작은 붕괴가 함께 일어납니다.",
            "caption": "좁고 깊은 골짜기가 형성되는 핵심은 하천의 집중 침식입니다.",
            "focus": "계곡 바닥이 얼마나 빠르게 낮아지는지 보세요.",
            "question": "사면 이동은 계곡 단면을 어떻게 바꾸나요?",
            "process_order": "하천 침식 → 풍화·사면 이동",
        },
        {
            "title": "3단계: 사면 조정",
            "summary": "사면 물질이 아래로 이동하면서 V자 단면이 더 선명해지고, 골짜기와 능선 대비가 커집니다.",
            "caption": "하천이 파고, 사면이 따라 무너져 내려 V자곡 형태가 강화됩니다.",
            "focus": "계곡 바닥과 사면 각도의 차이를 보세요.",
            "question": "하천 침식만으로 V자곡이 완성될 수 있을까요?",
            "process_order": "하천 침식 + 사면 이동 누적",
        },
        _GENERIC_PROCESS_STAGES[3],
    ),
    "alluvial_fan": (
        {
            "title": "1단계: 단층성 융기와 공급",
            "summary": "산지 출구 부근의 융기와 단층 운동이 큰 경사 차를 만들고, 풍화와 사면 이동이 쇄설물을 공급합니다.",
            "caption": "선상지의 시작은 산지에서 재료가 많이 공급되는 조건입니다.",
            "focus": "산지 출구와 평야 경계의 경사 변화를 보세요.",
            "question": "왜 선상지는 산지 출구에서 시작될까요?",
            "process_order": "융기·단층 → 풍화·사면 이동 → 하천 운반",
        },
        {
            "title": "2단계: 운반 경로 형성",
            "summary": "하천이 협곡을 빠져나오며 물질을 집중 운반하지만, 평야로 나오면서 에너지가 급격히 떨어지기 시작합니다.",
            "caption": "운반은 계속되지만 산지 출구에서 감속이 시작됩니다.",
            "focus": "좁은 수로가 넓어지는 지점을 보세요.",
            "question": "운반력 감소는 어디서 가장 먼저 나타나나요?",
            "process_order": "하천 운반 → 유량 분산",
        },
        {
            "title": "3단계: 부채꼴 퇴적 확산",
            "summary": "유로가 퍼지고 감속되면서 퇴적 중심이 산록 전면으로 넓게 확산됩니다.",
            "caption": "선상지의 대표 모양은 감속과 유로 분산이 만든 결과입니다.",
            "focus": "중심부와 가장자리의 퇴적 폭 차이를 비교해 보세요.",
            "question": "왜 퇴적이 한 줄이 아니라 부채꼴로 퍼질까요?",
            "process_order": "이동 → 감속 → 퇴적 확산",
        },
        {
            "title": "4단계: 선상지 해석",
            "summary": "최종적으로는 산지 공급, 하천 운반, 감속 퇴적이 연결된 선상지 체계를 읽을 수 있습니다.",
            "caption": "선상지는 침식 지형이 아니라 공급과 퇴적이 함께 만든 접점 지형입니다.",
            "focus": "상류 공급지와 하류 퇴적지를 한 세트로 보세요.",
            "question": "선상지 형성에서 내적 작용과 외적 작용은 각각 어떤 역할을 했나요?",
            "process_order": "융기·단층 → 풍화·이동 → 퇴적",
        },
    ),
    "fluvial_plain": (
        {
            "title": "1단계: 완만한 기반과 수로 형성",
            "summary": "경사가 완만한 기반 위에서 하천이 범람원 통로를 만들기 시작합니다.",
            "caption": "평야는 깎이는 힘보다 쌓이는 힘이 상대적으로 커지는 공간입니다.",
            "focus": "중앙 수로와 주변 저지대의 높이 차를 보세요.",
            "question": "왜 평야에서는 깊은 계곡보다 넓은 저지대가 발달할까요?",
            "process_order": "완만한 기반 → 하천 운반",
        },
        {
            "title": "2단계: 범람과 퇴적",
            "summary": "하천이 넘치며 미세 물질을 넓게 남기고, 수로 주변에 제방과 저지가 분화됩니다.",
            "caption": "평야의 핵심은 반복된 범람과 넓은 퇴적입니다.",
            "focus": "수로 가장자리와 바깥쪽 평야를 비교하세요.",
            "question": "왜 퇴적은 하천 주변에서 폭넓게 일어날까요?",
            "process_order": "운반 → 범람 → 광역 퇴적",
        },
        {
            "title": "3단계: 범람원 정리",
            "summary": "침식보다 퇴적이 우세한 상태가 이어지며 평탄한 범람원이 강화됩니다.",
            "caption": "넓고 평평한 지형은 느리지만 반복적인 퇴적의 결과입니다.",
            "focus": "높낮이 차가 줄어드는 방향을 보세요.",
            "question": "퇴적이 계속되면 하천 주변 지형은 어떻게 달라질까요?",
            "process_order": "반복 퇴적 → 평탄화",
        },
        _GENERIC_PROCESS_STAGES[3],
    ),
    "delta": (
        {
            "title": "1단계: 하구 공간 형성",
            "summary": "하구에서는 상대적 해수면과 침강이 퇴적될 공간을 만들고, 상류에서 공급된 물질이 모이기 시작합니다.",
            "caption": "삼각주는 침강과 해수면 조건이 있어야 크게 자랄 수 있습니다.",
            "focus": "바다와 하천이 만나는 낮은 지대를 보세요.",
            "question": "왜 삼각주는 침강이 있어도 오히려 성장할 수 있을까요?",
            "process_order": "침강/해수면 공간 형성 → 하천 공급",
        },
        {
            "title": "2단계: 하구 감속",
            "summary": "하천이 바다로 들어가며 흐름이 약해지고, 하중을 더 이상 다 들지 못해 퇴적을 시작합니다.",
            "caption": "삼각주에서는 운반력 감소가 바로 퇴적 전환점입니다.",
            "focus": "하천 말단의 감속 지점을 보세요.",
            "question": "왜 하천은 바다를 만나면 갑자기 쌓기 시작할까요?",
            "process_order": "하천 운반 → 하구 감속 → 퇴적",
        },
        {
            "title": "3단계: 삼각주 전진",
            "summary": "퇴적이 누적되며 전면이 앞으로 나가고, 파랑·해안 작용이 가장자리를 다시 다듬습니다.",
            "caption": "삼각주는 퇴적만으로 끝나지 않고, 해안 재가공을 함께 받습니다.",
            "focus": "하구 전면과 측면 가장자리의 모양 차이를 보세요.",
            "question": "하천 퇴적과 해안 재가공은 어떤 긴장을 만들까요?",
            "process_order": "퇴적 누적 → 해안 재가공",
        },
        {
            "title": "4단계: 하구 지형 해석",
            "summary": "최종 삼각주는 공급, 침강, 해안 재가공이 균형을 이루며 만들어진 하구 지형으로 해석할 수 있습니다.",
            "caption": "삼각주는 단순한 모래더미가 아니라, 공급과 accommodation의 균형 결과입니다.",
            "focus": "상류 공급량과 하구 전면 확장을 함께 보세요.",
            "question": "삼각주가 자라려면 침강과 퇴적 중 어느 쪽이 더 빨라야 할까요?",
            "process_order": "침강 → 운반 → 퇴적 → 해안 재가공",
        },
    ),
    "meander": (
        {
            "title": "1단계: 완만한 경사와 유로 자리잡기",
            "summary": "완만한 평탄면 위에서 수로가 한쪽으로 치우치기 시작하며 좌우 비대칭 흐름이 생깁니다.",
            "caption": "곡류는 직선 하천이 흔들리기 시작하는 데서 출발합니다.",
            "focus": "물길이 처음 치우치는 지점을 보세요.",
            "question": "왜 완만한 하천이 더 쉽게 굽이칠까요?",
            "process_order": "완만한 기반 → 흐름 비대칭",
        },
        {
            "title": "2단계: 바깥쪽 침식",
            "summary": "굽이 바깥쪽에서 유속이 빨라져 측방 침식이 일어나고, 안쪽은 상대적으로 느려집니다.",
            "caption": "곡류의 핵심은 바깥쪽 침식과 안쪽 퇴적의 동시 진행입니다.",
            "focus": "굽이 바깥쪽 사면을 보세요.",
            "question": "왜 같은 하천 안에서도 한쪽은 깎이고 한쪽은 쌓일까요?",
            "process_order": "측방 침식 강화",
        },
        {
            "title": "3단계: 점바 퇴적과 사행 강화",
            "summary": "굽이 안쪽에서는 퇴적이 늘고, 그 차이 때문에 굽이가 더 크게 확대됩니다.",
            "caption": "곡류는 침식과 퇴적의 위치 차이가 만든 이동형 지형입니다.",
            "focus": "안쪽 퇴적 띠와 바깥쪽 침식 띠를 함께 보세요.",
            "question": "점바 퇴적이 사행을 더 키우는 이유는 무엇일까요?",
            "process_order": "측방 침식 + 점바 퇴적",
        },
        _GENERIC_PROCESS_STAGES[3],
    ),
    "u_valley": (
        {
            "title": "1단계: 고산 환경과 기반 형성",
            "summary": "높은 지형과 한랭 조건이 만들어지며, 빙하가 자리잡을 수 있는 환경이 형성됩니다.",
            "caption": "U자곡은 먼저 높은 지형과 추운 기후가 필요합니다.",
            "focus": "고도가 높은 계곡 상류를 보세요.",
            "question": "왜 모든 계곡이 U자곡이 되지 않을까요?",
            "process_order": "융기 → 한랭화 → 빙하 형성",
        },
        {
            "title": "2단계: 동결 파쇄와 빙하 침식",
            "summary": "사면에서는 동결 파쇄가 재료를 풀어주고, 계곡 안에서는 빙하가 바닥과 벽면을 함께 깎습니다.",
            "caption": "하천 계곡과 달리 빙하는 폭과 깊이를 함께 키웁니다.",
            "focus": "계곡 바닥과 측벽이 함께 넓어지는지 보세요.",
            "question": "빙하는 왜 계곡 바닥만이 아니라 옆면도 강하게 깎을까요?",
            "process_order": "동결 파쇄 → 빙하 침식",
        },
        {
            "title": "3단계: 계곡 확장과 퇴적",
            "summary": "넓고 둥근 계곡 단면이 강화되고, 빙하가 물러난 자리에는 빙하 퇴적물이 남습니다.",
            "caption": "U자곡은 침식 지형이면서 동시에 빙하 퇴적 흔적을 남깁니다.",
            "focus": "넓어진 바닥과 가장자리 퇴적 흔적을 보세요.",
            "question": "빙하 퇴적은 계곡 해석에 어떤 단서를 줄까요?",
            "process_order": "빙하 침식 → 빙하 퇴적",
        },
        _GENERIC_PROCESS_STAGES[3],
    ),
    "fjord": (
        {
            "title": "1단계: 깊은 빙하 계곡 준비",
            "summary": "먼저 고산 계곡이 깊게 파이고, 빙하가 계곡을 해수면 아래까지 심화시킵니다.",
            "caption": "피오르는 바다보다 먼저 빙하가 만든 계곡입니다.",
            "focus": "깊은 계곡과 낮은 하구를 함께 보세요.",
            "question": "왜 피오르는 평범한 해안 만과 다를까요?",
            "process_order": "융기 → 빙하 침식 심화",
        },
        {
            "title": "2단계: 해수 유입",
            "summary": "빙하가 물러난 뒤 바닷물이 낮은 계곡 안으로 들어오며 깊은 만이 형성됩니다.",
            "caption": "피오르는 빙하 침식과 해수 유입이 결합된 지형입니다.",
            "focus": "계곡 안쪽으로 물이 들어오는 범위를 보세요.",
            "question": "해수 유입은 원래의 빙하 계곡을 어떻게 드러낼까요?",
            "process_order": "빙하 후퇴 → 해수 유입",
        },
        {
            "title": "3단계: 해안 재가공",
            "summary": "피오르 내부에서는 해안 작용이 가장자리를 다듬지만, 큰 형태는 빙하가 만든 단면이 유지됩니다.",
            "caption": "해안 작용은 세부를 고치지만, 주된 골격은 빙하가 남깁니다.",
            "focus": "해안선 미세 변화와 깊은 골짜기 축을 비교하세요.",
            "question": "피오르에서 해안 작용은 주연인지 주연출자인지 판단할 수 있나요?",
            "process_order": "해수 유입 → 해안 재가공",
        },
        _GENERIC_PROCESS_STAGES[3],
    ),
    "coastal_cliff": (
        {
            "title": "1단계: 해안 경사와 기반 형성",
            "summary": "해안에 높낮이 차가 있고, 상대적 해수면과 융기 조건이 파랑 작용이 집중될 절벽 발달 조건을 만듭니다.",
            "caption": "해식애와 해안단구는 모두 해안 경사와 해수면 조건에서 시작됩니다.",
            "focus": "해안선과 절벽 하부를 먼저 보세요.",
            "question": "왜 파랑은 절벽 아래쪽을 먼저 공격할까요?",
            "process_order": "상대적 해수면/융기 → 파랑 집중",
        },
        {
            "title": "2단계: 파랑 침식과 하부 약화",
            "summary": "절벽 하부가 먼저 깎이면서 상부가 불안정해지고, 후퇴가 시작됩니다.",
            "caption": "해안 절벽은 아래가 먼저 약해져 뒤로 물러납니다.",
            "focus": "절벽 아래 패인 부분을 보세요.",
            "question": "왜 해안선은 앞으로 전진하지 않고 뒤로 후퇴할까요?",
            "process_order": "해안 침식 → 절벽 후퇴",
        },
        {
            "title": "3단계: 붕괴와 파식대",
            "summary": "사면 붕괴와 파랑 재가공이 반복되며 절벽 앞에는 파식대나 해안단구 흔적이 나타납니다.",
            "caption": "해안 절벽은 파랑 침식과 사면 붕괴가 연결된 지형입니다.",
            "focus": "절벽 상단과 절벽 앞 평탄면을 함께 보세요.",
            "question": "해안단구는 왜 융기와 파랑 작용이 함께 있어야 잘 보일까요?",
            "process_order": "파랑 침식 + 사면 붕괴 + 융기",
        },
        _GENERIC_PROCESS_STAGES[3],
    ),
    "barchan": (
        {
            "title": "1단계: 모래 공급과 바람장",
            "summary": "건조한 환경에서 느슨한 모래가 공급되고, 한 방향 바람이 지속되며 사구 형성 조건이 만들어집니다.",
            "caption": "바르한은 바람 방향이 비교적 일정할 때 잘 생깁니다.",
            "focus": "바람이 불어오는 방향과 모래 공급지를 보세요.",
            "question": "왜 바람 방향이 일정해야 바르한이 유지될까요?",
            "process_order": "풍화·모래 공급 → 바람 이동",
        },
        {
            "title": "2단계: 풍식과 이동",
            "summary": "바람받이 사면에서 입자가 이동하고, 능선을 넘어간 모래가 뒤쪽으로 떨어집니다.",
            "caption": "사구는 깎이는 면과 쌓이는 면이 방향성을 갖습니다.",
            "focus": "앞사면과 뒤사면의 차이를 보세요.",
            "question": "왜 바르한의 꼬리는 바람이 가는 방향을 향할까요?",
            "process_order": "바람 이동 → 능선 통과",
        },
        {
            "title": "3단계: 이풍측 퇴적",
            "summary": "뒤쪽 경사면에 퇴적이 집중되며 초승달형 사구가 강화되고 전체 사구가 이동합니다.",
            "caption": "바르한은 제자리 산이 아니라 이동하는 퇴적 지형입니다.",
            "focus": "꼬리와 중심부의 이동 방향을 보세요.",
            "question": "사구가 이동해도 모양을 유지하는 이유는 무엇일까요?",
            "process_order": "이동 → 이풍측 퇴적 → 사구 이동",
        },
        _GENERIC_PROCESS_STAGES[3],
    ),
    "karst_doline": (
        {
            "title": "1단계: 절리와 지하수 침투",
            "summary": "석회암 기반에 절리와 틈이 발달하고, 물이 스며들며 용해가 시작됩니다.",
            "caption": "카르스트는 표면 침식보다 지하 용해가 먼저 중요해집니다.",
            "focus": "물이 스며들 만한 낮은 곳을 보세요.",
            "question": "왜 카르스트는 지표수보다 지하수 흐름이 더 중요할까요?",
            "process_order": "절리 발달 → 지하수 침투 → 용해",
        },
        {
            "title": "2단계: 용해 확대",
            "summary": "물길을 따라 암석이 녹아 공동과 함몰 전조가 생기고, 지표의 높낮이 차가 점차 커집니다.",
            "caption": "카르스트의 변화는 표면이 깎이는 것보다 내부가 비어 가는 과정입니다.",
            "focus": "함몰이 시작되는 저지대를 보세요.",
            "question": "용해는 침식과 달리 왜 안쪽으로 파고들까요?",
            "process_order": "용해 → 공동 확대",
        },
        {
            "title": "3단계: 함몰과 침강",
            "summary": "지하 공간이 커지면 표면이 내려앉아 돌리네 같은 함몰 지형이 분명해집니다.",
            "caption": "카르스트에서는 침강이 외적 작용의 결과로 나타나는 지형 반응입니다.",
            "focus": "낮아지는 중심부와 주변 완경사를 보세요.",
            "question": "함몰 중심이 생기면 표면 배수는 어떻게 달라질까요?",
            "process_order": "용해 → 함몰·침강 → 배수 재조정",
        },
        _GENERIC_PROCESS_STAGES[3],
    ),
    "stratovolcano": (
        {
            "title": "1단계: 마그마 공급",
            "summary": "내부에서 마그마가 공급되며 분화구 주변에 물질이 쌓일 준비가 됩니다.",
            "caption": "화산 지형은 먼저 쌓이는 내적 작용이 중심입니다.",
            "focus": "분화 중심과 주변 사면을 보세요.",
            "question": "왜 화산은 침식 지형과 달리 처음부터 높아질까요?",
            "process_order": "마그마 공급 → 화산 분출",
        },
        {
            "title": "2단계: 분출과 화산체 성장",
            "summary": "분출물이 중심부에 쌓이며 원추형 화산체가 자라고, 사면 경사가 커집니다.",
            "caption": "화산체는 쌓이는 속도와 깎이는 속도의 경쟁으로 모양이 달라집니다.",
            "focus": "중심부 상승과 사면 확장을 함께 보세요.",
            "question": "분출이 계속되면 어떤 부분이 가장 빨리 자랄까요?",
            "process_order": "분출 → 축적",
        },
        {
            "title": "3단계: 외적 재가공",
            "summary": "분출이 만든 사면 위에서 풍화, 하천 침식, 사면 붕괴가 동시에 작용해 화산체를 다시 다듬습니다.",
            "caption": "화산 지형도 결국 외적 작용을 받아 모양이 바뀝니다.",
            "focus": "분화구 주변과 사면 하부의 차이를 보세요.",
            "question": "쌓이는 작용과 깎이는 작용은 화산에서 어떻게 공존할까요?",
            "process_order": "분출 → 풍화·침식·붕괴",
        },
        _GENERIC_PROCESS_STAGES[3],
    ),
}


def _match_process_story_key(selected_landform: str) -> str:
    keyword_map = (
        ("습곡", "folded_range"),
        ("선상지", "alluvial_fan"),
        ("삼각주", "delta"),
        ("곡류", "meander"),
        ("V자곡", "v_valley"),
        ("U자곡", "u_valley"),
        ("피오르", "fjord"),
        ("해안단구", "coastal_cliff"),
        ("해식애", "coastal_cliff"),
        ("바르한", "barchan"),
        ("카르스트", "karst_doline"),
        ("화산", "stratovolcano"),
        ("평원", "fluvial_plain"),
    )
    for keyword, key in keyword_map:
        if keyword in selected_landform:
            return key
    return "generic"


def summarize_process_stats(stats: dict[str, float] | None, top_n: int = 3) -> list[dict[str, float | str]]:
    if not stats or top_n <= 0:
        return []

    ranked: list[dict[str, float | str]] = []
    for key, meta in _PROCESS_METADATA.items():
        value = float(stats.get(key, 0.0) or 0.0)
        if value <= 1e-12:
            continue
        ranked.append(
            {
                "key": key,
                "label": meta["label"],
                "group": meta["group"],
                "value": value,
            }
        )

    ranked.sort(key=lambda item: float(item["value"]), reverse=True)
    return ranked[:top_n]


def format_process_summary(stats: dict[str, float] | None, top_n: int = 3) -> str:
    dominant = summarize_process_stats(stats, top_n=top_n)
    if not dominant:
        return "아직 변화량이 작아 우세 작용이 분명하지 않습니다."
    return " · ".join(f"{item['label']}({item['group']})" for item in dominant)


def _format_group_summary(dominant: list[dict[str, float | str]]) -> str:
    grouped: dict[str, list[str]] = {"내적": [], "외적": []}
    for item in dominant:
        group = str(item["group"])
        grouped.setdefault(group, []).append(str(item["label"]))

    parts: list[str] = []
    if grouped.get("내적"):
        parts.append(f"내적 작용: {', '.join(grouped['내적'])}")
    if grouped.get("외적"):
        parts.append(f"외적 작용: {', '.join(grouped['외적'])}")
    return " / ".join(parts) if parts else "내적·외적 작용의 우세 관계가 아직 약합니다."


def _stage_idx_from_progress(progress: float | None) -> int:
    progress = max(0.0, min(1.0, float(progress or 0.0)))
    if progress < 0.25:
        return 0
    if progress < 0.5:
        return 1
    if progress < 0.75:
        return 2
    return 3


def _metric(stats: dict[str, float] | None, key: str) -> float:
    if not stats:
        return 0.0
    return float(stats.get(key, 0.0) or 0.0)


def _total_activity(stats: dict[str, float] | None) -> float:
    if not stats:
        return 0.0
    keys = (
        "mean_uniform_uplift",
        "mean_subsidence",
        "mean_faulting",
        "mean_folding",
        "mean_volcanic",
        "mean_erosion_rate",
        "mean_diffusion",
        "mean_weathering_rate",
        "mean_deposition_rate",
        "mean_lateral_erosion",
        "mean_glacial",
        "mean_marine",
        "mean_landslide",
        "mean_karst",
        "mean_aeolian",
        "mean_groundwater",
        "mean_freeze_thaw",
        "mean_moraine",
    )
    return sum(_metric(stats, key) for key in keys)


def _field_array(process_fields: dict[str, Any] | None, key: str) -> np.ndarray | None:
    if not process_fields:
        return None
    field = process_fields.get(key)
    if field is None:
        return None
    array = np.asarray(field, dtype=float)
    if array.size == 0:
        return None
    return np.nan_to_num(array, nan=0.0, posinf=0.0, neginf=0.0)


def _active_cell_fraction(field: np.ndarray | None) -> float:
    if field is None:
        return 0.0
    magnitude = np.abs(field)
    peak = float(np.max(magnitude))
    if peak <= 0.0:
        return 0.0
    return float(np.mean(magnitude >= peak * 0.35))


def _lower_half_activity_ratio(field: np.ndarray | None) -> float:
    if field is None:
        return 0.0
    magnitude = np.abs(field)
    total = float(np.sum(magnitude))
    if total <= 0.0:
        return 0.0
    split = max(magnitude.shape[0] // 2, 1)
    return float(np.sum(magnitude[split:, :]) / total)


def _centerline_activity_ratio(field: np.ndarray | None) -> float:
    if field is None:
        return 0.0
    magnitude = np.abs(field)
    total = float(np.sum(magnitude))
    if total <= 0.0:
        return 0.0
    rows, cols = magnitude.shape
    row_start = max(rows // 3, 0)
    row_end = min(rows - row_start, rows)
    col_start = max(cols // 3, 0)
    col_end = min(cols - col_start, cols)
    row_focus = float(np.sum(magnitude[row_start:row_end, :]) / total)
    col_focus = float(np.sum(magnitude[:, col_start:col_end]) / total)
    return max(row_focus, col_focus)


def _field_spread_score(field: np.ndarray | None) -> float:
    if field is None:
        return 0.0
    magnitude = np.abs(field)
    total = float(np.sum(magnitude))
    if total <= 0.0:
        return 0.0
    yy, xx = np.indices(magnitude.shape)
    cy = float(np.sum(yy * magnitude) / total)
    cx = float(np.sum(xx * magnitude) / total)
    distances = np.sqrt((yy - cy) ** 2 + (xx - cx) ** 2)
    scale = max(float(np.hypot(*magnitude.shape)), 1.0)
    return float(np.sum(distances * magnitude) / total / scale)


def _banded_structure_score(field: np.ndarray | None) -> float:
    if field is None:
        return 0.0
    magnitude = np.abs(field)
    peak = float(np.max(magnitude))
    if peak <= 0.0:
        return 0.0
    row_profile = np.mean(magnitude, axis=1)
    col_profile = np.mean(magnitude, axis=0)
    return float(max(np.std(row_profile), np.std(col_profile)) / peak)


def _suggest_overlay_type(story_key: str, stage_idx: int, selected_landform: str | None = None) -> str:
    if selected_landform:
        high_school_stage = _get_high_school_stage(selected_landform, story_key, stage_idx)
        if high_school_stage and high_school_stage.get("overlay"):
            return str(high_school_stage["overlay"])
    overlay_map = {
        "v_valley": ["tectonic", "erosion", "transport", "change"],
        "alluvial_fan": ["tectonic", "transport", "deposition", "change"],
        "folded_range": ["tectonic", "tectonic", "erosion", "change"],
    }
    return overlay_map.get(story_key, ["tectonic", "erosion", "deposition", "change"])[stage_idx]


def _classify_process_stage_index(
    story_key: str,
    stats: dict[str, float] | None,
    *,
    process_fields: dict[str, Any] | None,
    previous_stage_idx: int,
    peak_activity: float,
) -> int:
    tectonic = _metric(stats, "mean_uniform_uplift") + _metric(stats, "mean_faulting") + _metric(stats, "mean_folding") + _metric(stats, "mean_volcanic")
    erosion = _metric(stats, "mean_erosion_rate") + _metric(stats, "mean_lateral_erosion") + _metric(stats, "mean_glacial") + _metric(stats, "mean_marine")
    slope_adjust = _metric(stats, "mean_diffusion") + _metric(stats, "mean_landslide") + _metric(stats, "mean_weathering_rate") + _metric(stats, "mean_freeze_thaw")
    deposition = _metric(stats, "mean_deposition_rate") + _metric(stats, "mean_moraine")
    activity = _total_activity(stats)
    stabilized = peak_activity > 0.0 and activity <= peak_activity * 0.8
    erosion_field = _field_array(process_fields, "total_erosion")
    if erosion_field is None:
        erosion_field = _field_array(process_fields, "erosion")
    deposition_field = _field_array(process_fields, "deposition")
    folding_field = _field_array(process_fields, "folding")
    tectonic_field = _field_array(process_fields, "tectonic")
    erosion_focus = _centerline_activity_ratio(erosion_field)
    deposition_outlet = _lower_half_activity_ratio(deposition_field)
    deposition_spread = _field_spread_score(deposition_field)
    folding_band_score = _banded_structure_score(folding_field)
    tectonic_coverage = _active_cell_fraction(tectonic_field)

    if story_key == "v_valley":
        if previous_stage_idx >= 2 and stabilized:
            return 3
        if slope_adjust >= erosion * 0.55 and erosion_focus >= 0.38 and (erosion > 0.0 or previous_stage_idx >= 1):
            return 2
        if erosion >= max(slope_adjust * 1.1, deposition * 1.5, tectonic * 0.45) and erosion_focus >= 0.34:
            return 1
        return 0

    if story_key == "alluvial_fan":
        source = tectonic + slope_adjust
        transport = erosion + _metric(stats, "mean_diffusion")
        if previous_stage_idx >= 2 and stabilized:
            return 3
        if deposition >= transport * 0.7 and deposition > 0.0 and deposition_outlet >= 0.5 and deposition_spread >= 0.16:
            return 2
        if transport >= max(source * 0.55, deposition * 1.2) and deposition_outlet <= 0.72:
            return 1
        return 0

    if story_key == "folded_range":
        if previous_stage_idx >= 2 and stabilized:
            return 3
        if erosion + slope_adjust >= tectonic * 0.9 and (erosion > 0.0 or slope_adjust > 0.0) and folding_band_score >= 0.08:
            return 2
        if tectonic > 0.0 and erosion + slope_adjust >= tectonic * 0.35 and max(folding_band_score, tectonic_coverage) >= 0.08:
            return 1
        return 0

    if previous_stage_idx >= 2 and stabilized:
        return 3
    if deposition > erosion * 0.7 and deposition > 0.0:
        return 2
    if erosion + slope_adjust > 0.0:
        return 1
    return 0


def build_lab_stage_history(
    selected_landform: str,
    stats_history: list[dict[str, float]] | None,
    process_history: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    if not stats_history:
        return []

    story_key = _match_process_story_key(selected_landform)
    stage_history: list[dict[str, Any]] = []
    peak_activity = 0.0
    previous_stage_idx = 0
    pending_stage_idx: int | None = None
    pending_stage_hits = 0
    required_hits = 2 if len(stats_history) >= 6 else 1

    for idx, stats in enumerate(stats_history):
        peak_activity = max(peak_activity, _total_activity(stats))
        process_fields = process_history[idx] if process_history and idx < len(process_history) else None
        stage_idx = _classify_process_stage_index(
            story_key,
            stats,
            process_fields=process_fields,
            previous_stage_idx=previous_stage_idx,
            peak_activity=peak_activity,
        )
        stage_idx = max(previous_stage_idx, stage_idx)
        if stage_idx > previous_stage_idx:
            if stage_idx == pending_stage_idx:
                pending_stage_hits += 1
            else:
                pending_stage_idx = stage_idx
                pending_stage_hits = 1
            if pending_stage_hits >= required_hits:
                previous_stage_idx = stage_idx
                pending_stage_idx = None
                pending_stage_hits = 0
            else:
                stage_idx = previous_stage_idx
        else:
            pending_stage_idx = None
            pending_stage_hits = 0

        stage = describe_lab_process_stage(
            selected_landform,
            progress=None,
            stats=stats,
            stage_idx=stage_idx,
            process_fields=process_fields,
        )
        stage["stage_index"] = stage_idx
        stage["overlay_type"] = _suggest_overlay_type(story_key, stage_idx, selected_landform)
        stage_history.append(stage)
        previous_stage_idx = stage_idx

    return stage_history


def describe_lab_process_stage(
    selected_landform: str,
    progress: float | None,
    stats: dict[str, float] | None = None,
    stage_idx: int | None = None,
    process_fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if stage_idx is None:
        stage_idx = _stage_idx_from_progress(progress)

    story_key = _match_process_story_key(selected_landform)
    stages = _LANDFORM_PROCESS_STAGES.get(story_key, _GENERIC_PROCESS_STAGES)
    topic = _get_high_school_lab_topic(selected_landform, story_key)
    high_school_stage = _get_high_school_stage(selected_landform, story_key, stage_idx)
    dominant = summarize_process_stats(stats, top_n=3)
    stage = dict(stages[stage_idx])
    if topic and high_school_stage:
        stage["title"] = str(high_school_stage.get("title") or stage["title"])
        stage["summary"] = str(high_school_stage.get("teacher_copy") or stage["summary"])
        stage["caption"] = str(high_school_stage.get("student_copy") or stage["caption"])
        stage["focus"] = str(topic.get("observation_focus") or stage["focus"])
        stage["question"] = str(high_school_stage.get("question") or stage["question"])
        stage["process_order"] = (
            _format_high_school_process_order(topic)
            or stage["process_order"]
        )
        stage["classroom_goal"] = str(topic.get("classroom_goal") or "")
        stage["compare_hint"] = str(topic.get("compare_hint") or "")
        stage["world_case_title"] = str((topic.get("world_case") or {}).get("title") or "")
        stage["world_case_location"] = str((topic.get("world_case") or {}).get("location_label") or "")
        stage["teacher_note"] = str(topic.get("teacher_note") or high_school_stage.get("teacher_copy") or "")
        stage["overlay_caption"] = str(topic.get("overlay_caption") or "")
        stage["topic_title"] = str(topic.get("title") or "")
    stage["dominant_processes"] = dominant
    stage["dominant_summary"] = format_process_summary(stats, top_n=3)
    stage["balance_summary"] = _format_group_summary(dominant)
    stage["overlay_type"] = _suggest_overlay_type(story_key, stage_idx, selected_landform)
    stage["stage_index"] = stage_idx
    stage["process_fields"] = process_fields
    return stage


def get_lab_scenario_config(selected_landform: str) -> LabScenarioConfig:
    if "습곡" in selected_landform:
        return LabScenarioConfig(
            landform_type="tectonic",
            detailed_type="folded_range",
            custom_surface="folded_range",
            precipitation=0.45,
            fold_rate=0.00045,
            fold_wavelength=0.22,
            fold_axis="x",
            k_scale=0.28,
            d_scale=0.5,
            u_scale=0.22,
            enable_folding=True,
            enable_landslides=True,
        )
    if "V자곡" in selected_landform:
        return LabScenarioConfig(
            landform_type="river",
            detailed_type="v_valley",
            generator_key="v_valley",
            k_scale=0.45,
            d_scale=0.45,
            u_scale=0.35,
            enable_landslides=True,
        )
    if "우각호" in selected_landform:
        return LabScenarioConfig(
            landform_type="river",
            detailed_type="oxbow_lake",
            generator_key="oxbow_lake",
            precipitation=0.7,
            k_scale=0.45,
            d_scale=0.8,
            u_scale=0.05,
            enable_sediment_transport=True,
            enable_lateral_erosion=True,
        )
    if "범람원" in selected_landform or "자연제방" in selected_landform:
        return LabScenarioConfig(
            landform_type="river",
            detailed_type="floodplain_natural_levee",
            generator_key="floodplain_natural_levee",
            precipitation=0.55,
            settling_velocity=2.4,
            k_scale=0.18,
            d_scale=0.7,
            u_scale=0.03,
            enable_sediment_transport=True,
            enable_lateral_erosion=True,
        )
    if "하안단구" in selected_landform:
        return LabScenarioConfig(
            landform_type="river",
            detailed_type="river_terrace",
            generator_key="river_terrace",
            precipitation=0.5,
            k_scale=0.42,
            d_scale=0.45,
            u_scale=0.35,
            enable_sediment_transport=True,
            enable_lateral_erosion=True,
            enable_landslides=True,
        )
    if "평원" in selected_landform:
        return LabScenarioConfig(
            landform_type="river",
            custom_surface="fluvial_plain",
            precipitation=0.5,
            settling_velocity=2.0,
            k_scale=0.2,
            d_scale=0.6,
            u_scale=0.05,
            enable_sediment_transport=True,
        )
    if "선상지" in selected_landform:
        return LabScenarioConfig(
            landform_type="river",
            detailed_type="alluvial_fan",
            generator_key="alluvial_fan",
            precipitation=0.35,
            settling_velocity=2.5,
            fault_rate=0.00035,
            k_scale=0.2,
            d_scale=0.7,
            u_scale=0.1,
            enable_sediment_transport=True,
            enable_lateral_erosion=True,
            enable_faulting=True,
            enable_landslides=True,
        )
    if "삼각주" in selected_landform:
        return LabScenarioConfig(
            landform_type="coastal",
            detailed_type="delta",
            generator_key="delta",
            precipitation=0.45,
            settling_velocity=2.2,
            sea_level=10.0,
            k_scale=0.25,
            d_scale=0.5,
            u_scale=-0.05,
            enable_sediment_transport=True,
            enable_marine=True,
        )
    if "곡류" in selected_landform:
        return LabScenarioConfig(
            landform_type="river",
            detailed_type="meander",
            generator_key="meander",
            precipitation=0.7,
            k_scale=0.5,
            d_scale=0.8,
            u_scale=0.15,
            enable_sediment_transport=True,
            enable_lateral_erosion=True,
        )
    if "U자곡" in selected_landform:
        return LabScenarioConfig(
            landform_type="glacial",
            detailed_type="u_valley",
            generator_key="u_valley",
            glacial_erosion=0.0005,
            freeze_elevation=120.0,
            k_scale=0.35,
            d_scale=0.6,
            u_scale=0.15,
            enable_glacial=True,
            enable_freeze_thaw=True,
            enable_landslides=True,
        )
    if "피오르" in selected_landform:
        return LabScenarioConfig(
            landform_type="glacial",
            detailed_type="fjord",
            generator_key="fjord",
            sea_level=0.0,
            glacial_erosion=0.0004,
            freeze_elevation=120.0,
            k_scale=0.3,
            d_scale=0.5,
            u_scale=0.1,
            enable_glacial=True,
            enable_marine=True,
            enable_freeze_thaw=True,
        )
    if "모레인" in selected_landform:
        return LabScenarioConfig(
            landform_type="glacial",
            detailed_type="moraine",
            generator_key="moraine",
            glacial_erosion=0.00035,
            freeze_elevation=110.0,
            k_scale=0.25,
            d_scale=0.5,
            u_scale=0.08,
            enable_glacial=True,
            enable_glacial_deposit=True,
            enable_freeze_thaw=True,
        )
    if "드럼린" in selected_landform:
        return LabScenarioConfig(
            landform_type="glacial",
            detailed_type="drumlin",
            generator_key="drumlin",
            glacial_erosion=0.00028,
            freeze_elevation=105.0,
            k_scale=0.2,
            d_scale=0.35,
            u_scale=0.04,
            enable_glacial=True,
            enable_glacial_deposit=True,
        )
    if "에스커" in selected_landform:
        return LabScenarioConfig(
            landform_type="glacial",
            detailed_type="esker",
            generator_key="esker",
            glacial_erosion=0.00022,
            freeze_elevation=105.0,
            k_scale=0.15,
            d_scale=0.35,
            u_scale=0.03,
            enable_glacial=True,
            enable_glacial_deposit=True,
        )
    if "해안단구" in selected_landform:
        return LabScenarioConfig(
            landform_type="coastal",
            detailed_type="coastal_cliff",
            generator_key="coastal_cliff",
            sea_level=0.0,
            k_scale=0.25,
            d_scale=0.4,
            u_scale=0.35,
            enable_marine=True,
            enable_landslides=True,
        )
    if "해식애" in selected_landform:
        return LabScenarioConfig(
            landform_type="coastal",
            detailed_type="coastal_cliff",
            generator_key="coastal_cliff",
            sea_level=0.0,
            k_scale=0.3,
            d_scale=0.5,
            u_scale=0.1,
            enable_marine=True,
            enable_landslides=True,
        )
    if "해식동" in selected_landform or "시스택" in selected_landform:
        return LabScenarioConfig(
            landform_type="coastal",
            detailed_type="sea_cave_stack",
            generator_key="sea_cave_stack",
            sea_level=0.0,
            k_scale=0.28,
            d_scale=0.45,
            u_scale=0.08,
            enable_marine=True,
            enable_landslides=True,
        )
    if "파식대" in selected_landform:
        return LabScenarioConfig(
            landform_type="coastal",
            detailed_type="wave_cut_platform",
            generator_key="wave_cut_platform",
            sea_level=0.0,
            k_scale=0.26,
            d_scale=0.5,
            u_scale=0.12,
            enable_marine=True,
            enable_landslides=True,
        )
    if "사주섬" in selected_landform:
        return LabScenarioConfig(
            landform_type="coastal",
            detailed_type="barrier_island",
            generator_key="barrier_island",
            sea_level=0.0,
            precipitation=0.35,
            settling_velocity=2.0,
            k_scale=0.18,
            d_scale=0.45,
            u_scale=-0.02,
            enable_sediment_transport=True,
            enable_marine=True,
        )
    if "사막" in selected_landform:
        return LabScenarioConfig(
            landform_type="arid",
            detailed_type="pediment",
            generator_key="pediment",
            precipitation=0.2,
            aeolian_erosion=0.00035,
            wind_direction=np.pi / 6,
            k_scale=0.1,
            d_scale=0.2,
            u_scale=0.0,
            enable_aeolian=True,
        )
    if "바르한" in selected_landform:
        return LabScenarioConfig(
            landform_type="arid",
            detailed_type="barchan",
            generator_key="barchan",
            precipitation=0.15,
            aeolian_erosion=0.0006,
            wind_direction=np.pi / 4,
            k_scale=0.05,
            d_scale=0.2,
            u_scale=0.0,
            enable_aeolian=True,
        )
    if "폴리에" in selected_landform:
        return LabScenarioConfig(
            landform_type="karst",
            detailed_type="polje",
            generator_key="polje",
            precipitation=0.6,
            water_table=24.0,
            spring_rate=0.0018,
            k_scale=0.32,
            d_scale=0.28,
            u_scale=0.04,
            enable_karst=True,
            enable_groundwater=True,
        )
    if "카르스트" in selected_landform:
        return LabScenarioConfig(
            landform_type="karst",
            detailed_type="karst_doline",
            generator_key="karst_doline",
            precipitation=0.55,
            water_table=30.0,
            spring_rate=0.0015,
            k_scale=0.35,
            d_scale=0.25,
            u_scale=0.1,
            enable_karst=True,
            enable_groundwater=True,
        )
    if "마르" in selected_landform:
        return LabScenarioConfig(
            landform_type="volcanic",
            detailed_type="maar",
            generator_key="maar",
            volcanic_rate=0.012,
            water_table=18.0,
            k_scale=0.16,
            d_scale=0.28,
            u_scale=0.05,
            enable_volcanic=True,
            enable_groundwater=True,
            enable_landslides=True,
        )
    if "용암돔" in selected_landform:
        return LabScenarioConfig(
            landform_type="volcanic",
            detailed_type="lava_dome",
            generator_key="lava_dome",
            volcanic_rate=0.03,
            k_scale=0.14,
            d_scale=0.22,
            u_scale=0.12,
            enable_volcanic=True,
            enable_landslides=True,
        )
    if "화산" in selected_landform:
        return LabScenarioConfig(
            landform_type="volcanic",
            detailed_type="stratovolcano",
            generator_key="stratovolcano",
            volcanic_rate=0.02,
            k_scale=0.2,
            d_scale=0.3,
            u_scale=0.2,
            enable_volcanic=True,
            enable_landslides=True,
        )
    return LabScenarioConfig(landform_type="river")


def _create_fluvial_plain(grid_size: int) -> np.ndarray:
    y, x = np.mgrid[0:grid_size, 0:grid_size]
    base_slope = 30.0 - (y / max(grid_size - 1, 1)) * 18.0
    center = (grid_size - 1) / 2.0
    channel = np.exp(-((x - center) ** 2) / (2 * (grid_size * 0.09) ** 2))
    levee = np.exp(-((x - center) ** 2) / (2 * (grid_size * 0.18) ** 2))
    floodplain = base_slope - channel * 5.0 + levee * 1.2
    floodplain += np.sin(y / max(grid_size - 1, 1) * np.pi) * 0.8
    return floodplain.astype(float)


def _create_folded_range(grid_size: int) -> np.ndarray:
    y, x = np.mgrid[0:grid_size, 0:grid_size]
    x_norm = x / max(grid_size - 1, 1)
    y_norm = y / max(grid_size - 1, 1)

    long_waves = np.sin(2.0 * np.pi * x_norm * 3.0)
    short_waves = 0.35 * np.sin(2.0 * np.pi * x_norm * 7.0 + y_norm * np.pi * 0.6)
    taper = 0.35 + 0.65 * np.exp(-((y_norm - 0.5) ** 2) / (2 * 0.18 ** 2))
    foreland_slope = 36.0 - y_norm * 14.0
    structural_relief = (long_waves + short_waves) * 20.0 * taper
    axial_high = 10.0 * np.exp(-((y_norm - 0.5) ** 2) / (2 * 0.28 ** 2))
    folded = foreland_slope + structural_relief + axial_high
    return np.maximum(folded, 0.0).astype(float)


def _build_surface(config: LabScenarioConfig, grid_size: int) -> np.ndarray | None:
    if config.custom_surface == "fluvial_plain":
        return _create_fluvial_plain(grid_size)
    if config.custom_surface == "folded_range":
        return _create_folded_range(grid_size)
    if config.generator_key:
        return IDEAL_LANDFORM_GENERATORS[config.generator_key](grid_size)
    return None


def configure_lab_scenario(
    lem: SimpleLEM,
    *,
    selected_landform: str,
    grid_size: int,
) -> LabScenarioConfig:
    config = get_lab_scenario_config(selected_landform)

    lem.K *= config.k_scale
    lem.D *= config.d_scale
    lem.U *= config.u_scale

    if config.precipitation is not None:
        lem.precipitation = config.precipitation
    if config.settling_velocity is not None:
        lem.Vs = config.settling_velocity
    if config.sea_level is not None:
        lem.sea_level = config.sea_level
    if config.glacial_erosion is not None:
        lem.Kg = config.glacial_erosion
    if config.aeolian_erosion is not None:
        lem.Ka = config.aeolian_erosion
    if config.volcanic_rate is not None:
        lem.volcanic_rate = config.volcanic_rate
    if config.fault_rate is not None:
        lem.fault_rate = config.fault_rate
    if config.fold_rate is not None:
        lem.fold_rate = config.fold_rate
    if config.fold_wavelength is not None:
        lem.fold_wavelength = config.fold_wavelength
    if config.wind_direction is not None:
        lem.wind_direction = config.wind_direction
    if config.fold_axis is not None:
        lem.fold_axis = config.fold_axis
    if config.water_table is not None:
        lem.water_table = config.water_table
    if config.spring_rate is not None:
        lem.spring_rate = config.spring_rate
    if config.freeze_elevation is not None:
        lem.freeze_elevation = config.freeze_elevation

    lem.enable_sediment_transport = lem.enable_sediment_transport or config.enable_sediment_transport
    lem.enable_lateral_erosion = lem.enable_lateral_erosion or config.enable_lateral_erosion
    lem.enable_glacial = lem.enable_glacial or config.enable_glacial
    lem.enable_glacial_deposit = getattr(lem, "enable_glacial_deposit", False) or config.enable_glacial_deposit
    lem.enable_marine = lem.enable_marine or config.enable_marine
    lem.enable_karst = lem.enable_karst or config.enable_karst
    lem.enable_aeolian = lem.enable_aeolian or config.enable_aeolian
    lem.enable_volcanic = lem.enable_volcanic or config.enable_volcanic
    lem.enable_faulting = lem.enable_faulting or config.enable_faulting
    lem.enable_folding = getattr(lem, "enable_folding", False) or config.enable_folding
    lem.enable_groundwater = lem.enable_groundwater or config.enable_groundwater
    lem.enable_freeze_thaw = lem.enable_freeze_thaw or config.enable_freeze_thaw
    lem.enable_landslides = lem.enable_landslides or config.enable_landslides

    surface = _build_surface(config, grid_size)
    if surface is not None:
        lem.set_initial_topography(surface)
    else:
        lem.create_initial_mountain()

    return config
