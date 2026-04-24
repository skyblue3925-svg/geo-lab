from __future__ import annotations

from typing import Any, Dict, Optional

from app.utils.world_terrain_cases import get_featured_world_case

RIVER = "\ud558\ucc9c"
DELTA = "\uc0bc\uac01\uc8fc"
GLACIAL = "\ube59\ud558"
VOLCANIC = "\ud654\uc0b0"
KARST = "\uce74\ub974\uc2a4\ud2b8"
ARID = "\uac74\uc870"
COASTAL = "\ud574\uc548"

CATALOG_MODE = "\uc218\uc5c5\uc6a9 \uce74\ud0c8\ub85c\uadf8"
ADVANCED_MODE = "\uace0\uae09 \ubbf8\ub9ac\ubcf4\uae30"
TEACHER_MODE = CATALOG_MODE
ANIM_CONTINUOUS = "\uc5f0\uc18d \uc560\ub2c8\uba54\uc774\uc158"
ANIM_MANUAL = "\uc218\ub3d9 \ub2e8\uacc4"
RENDER_TERRAIN = "\uae30\ubcf8 \uc9c0\ud615"
RENDER_SATELLITE = "\uc704\uc131 \ub290\ub08c"
CAMERA_PAN = "\ud328\ub2dd"
CAMERA_ORBIT = "\uc624\ube57"
CAMERA_FIXED = "\uace0\uc815"
VIEW_UPSTREAM = "\uc0c1\ub958/\ud558\ub958 \ubdf0"
VIEW_DEFAULT = "\uae30\ubcf8 \uc0ac\uac01 \ubdf0"
VIEW_LOW_DIAGONAL = "\ub300\uac01\uc120 \ub0ae\uc740 \ubdf0"
VIEW_FRONT_Y_NEG = "\uc815\uba74 (Y-)"
TEXTURE_SYNTHETIC = "\ud569\uc131 \ud14d\uc2a4\ucc98"

SCENARIO_MOUNTAIN_RIVER = "\U0001f3d4\ufe0f \uc0b0\uc9c0/\ud558\ucc9c"
SCENARIO_GLACIAL_COASTAL = "\u2744\ufe0f \ube59\ud558/\ud574\uc548"
SCENARIO_ARID_SPECIAL = "\U0001f3dc\ufe0f \uac74\uc870/\ud2b9\uc218"

CATEGORY_DEFAULTS: Dict[str, Dict[str, Any]] = {
    RIVER: {
        "gallery_mode": TEACHER_MODE,
        "stage": 0.9,
        "animation_mode": ANIM_CONTINUOUS,
        "render_style_label": RENDER_TERRAIN,
        "camera_motion_label": CAMERA_PAN,
        "camera_view": VIEW_UPSTREAM,
        "cinematic_zoom": 1.1,
        "grid_size": 72,
        "num_frames": 36,
        "kicker": "하천 지형",
        "summary": "\ud558\ucc9c \uce68\uc2dd\uacfc \ud1f4\uc801 \ud750\ub984\uc744 \ube60\ub974\uac8c \ube44\uad50\ud558\ub294 \uad50\uc0ac\uc6a9 preset\uc785\ub2c8\ub2e4.",
        "lesson_focus": "\uce68\uc2dd\uacfc \ud1f4\uc801\uc774 \uac19\uc740 \ud558\ucc9c\uc5d0\uc11c \uc5b4\ub5bb\uac8c \uac19\uc774 \ubcf4\uc774\ub294\uc9c0 \uc77d\uc5b4\ub0c5\ub2c8\ub2e4.",
        "difficulty_label": "\ubcf4\ud1b5",
        "observation_prompt": "\ubb3c\uc774 \ube60\ub978 \uacf3\uacfc \ud1f4\uc801\uc774 \ub450\ub4dc\ub7ec\uc9c0\ub294 \uacf3\uc744 \uac19\uc774 \ucc3e\uc544\ubcf4\uc138\uc694.",
    },
    DELTA: {
        "gallery_mode": TEACHER_MODE,
        "stage": 0.86,
        "animation_mode": ANIM_CONTINUOUS,
        "render_style_label": RENDER_SATELLITE,
        "camera_motion_label": CAMERA_ORBIT,
        "camera_view": VIEW_FRONT_Y_NEG,
        "cinematic_zoom": 1.05,
        "grid_size": 78,
        "num_frames": 40,
        "kicker": "삼각주 지형",
        "summary": "\ubd84\uae30 \uc218\ub85c\uc640 \ud1f4\uc801 \uc804\uc9c4\uc774 \ub4dc\ub7ec\ub098\ub294 \ud558\uad6c \uc9c0\ud615 \ubaa8\ubc94 \uc0ac\ub840\uc785\ub2c8\ub2e4.",
        "lesson_focus": "\ud1f4\uc801\ubb3c\uc774 \ud558\uad6c\uc5d0\uc11c \uc55e\uc73c\ub85c \ubc00\ub824 \ub098\uac00\ub294 \uacfc\uc815\uc744 \ubcf4\uc5ec\uc90d\ub2c8\ub2e4.",
        "difficulty_label": "\ubcf4\ud1b5",
        "observation_prompt": "\uc218\ub85c\uac00 \uac08\ub77c\uc9c0\ub294 \uc9c0\uc810\uacfc \ubc14\ub2e4\ucabd\uc73c\ub85c \ud1f4\uc801\uc774 \uc804\uc9c4\ud558\ub294 \ubc29\ud5a5\uc744 \ubcf4\uc138\uc694.",
    },
    GLACIAL: {
        "gallery_mode": TEACHER_MODE,
        "stage": 0.94,
        "animation_mode": ANIM_MANUAL,
        "render_style_label": RENDER_TERRAIN,
        "camera_motion_label": CAMERA_ORBIT,
        "camera_view": VIEW_DEFAULT,
        "cinematic_zoom": 1.08,
        "grid_size": 72,
        "num_frames": 28,
        "kicker": "빙하 지형",
        "summary": "\ube59\ud558 \uce68\uc2dd \ubc29\ud5a5\uacfc \uacc4\uace1 \ub2e8\uba74 \ucc28\uc774\ub97c \uc77d\uae30 \uc88b\uc740 preset\uc785\ub2c8\ub2e4.",
        "lesson_focus": "\ud558\ucc9c \uacc4\uace1\uacfc \ube59\ud558 \uacc4\uace1\uc758 \ub2e8\uba74 \ucc28\uc774\ub97c \ube44\uad50\ud558\ub294 \uc218\uc5c5\uc5d0 \uc801\ud569\ud569\ub2c8\ub2e4.",
        "difficulty_label": "\ubcf4\ud1b5",
        "observation_prompt": "\uacc4\uace1 \ubc14\ub2e5\uc774 \ub113\uc5b4\uc9c0\ub294\uc9c0, \uc591 \uc0ac\uba74\uc774 \uac00\ud30c\ub978\uc9c0\ub97c \uac19\uc774 \ube44\uad50\ud574 \ubcf4\uc138\uc694.",
    },
    VOLCANIC: {
        "gallery_mode": TEACHER_MODE,
        "stage": 0.84,
        "animation_mode": ANIM_CONTINUOUS,
        "render_style_label": RENDER_TERRAIN,
        "camera_motion_label": CAMERA_ORBIT,
        "camera_view": VIEW_LOW_DIAGONAL,
        "cinematic_zoom": 1.15,
        "grid_size": 76,
        "num_frames": 34,
        "kicker": "화산 지형",
        "summary": "\ud654\uc0b0\uccb4 \uc131\uc7a5\uacfc \ud568\ubab0 \uad6c\uc870\ub97c \uc785\uccb4\uc801\uc73c\ub85c \ube44\uad50\ud558\ub3c4\ub85d \ub9de\ucd98 preset\uc785\ub2c8\ub2e4.",
        "lesson_focus": "\ubd84\ucd9c\uacfc \ud568\ubab0\uc774 \uc9c0\ud615 \ubaa8\uc591\uc744 \uc5b4\ub5bb\uac8c \ub2e4\ub974\uac8c \ub9cc\ub4dc\ub294\uc9c0 \uc0b4\ud3b5\ub2c8\ub2e4.",
        "difficulty_label": "\ubcf4\ud1b5",
        "observation_prompt": "\uc911\uc2ec \ubd84\ud654\uad6c, \uc0ac\uba74 \uacbd\uc0ac, \ud568\ubab0 \ubd84\uc9c0 \uac19\uc740 \uad6c\uc870\ub97c \ucc3e\uc544\ubcf4\uc138\uc694.",
    },
    KARST: {
        "gallery_mode": TEACHER_MODE,
        "stage": 0.9,
        "animation_mode": ANIM_MANUAL,
        "render_style_label": RENDER_TERRAIN,
        "camera_motion_label": CAMERA_ORBIT,
        "camera_view": VIEW_DEFAULT,
        "cinematic_zoom": 1.08,
        "grid_size": 68,
        "num_frames": 26,
        "kicker": "카르스트 지형",
        "summary": "\ud568\ubab0\uacfc \uc6a9\uc2dd \uc9c0\ud615\uc744 \uc9c0\ud615\uba74 \uc911\uc2ec\uc73c\ub85c \uc77d\uae30 \uc88b\uc740 preset\uc785\ub2c8\ub2e4.",
        "lesson_focus": "\ubb3c\uc5d0 \ub179\ub294 \uc554\uc11d\uc774 \ud568\ubab0\uc9c0\ub97c \uc5f0\uc18d\uc801\uc73c\ub85c \ub9cc\ub4dc\ub294 \uacfc\uc815\uc744 \uc77d\uc5b4\ub0c5\ub2c8\ub2e4.",
        "difficulty_label": "\uc2ec\ud654",
        "observation_prompt": "\ud568\ubab0\uc9c0\uac00 \uc791\uc740 \uc6c0\ud479\uc784\uc5d0\uc11c \ub113\uc740 \ud568\ubab0 \uc9c0\ud615\uc73c\ub85c \uc5b4\ub5bb\uac8c \ubc1c\ub2ec\ud558\ub294\uc9c0 \ubcf4\uc138\uc694.",
    },
    ARID: {
        "gallery_mode": TEACHER_MODE,
        "stage": 0.88,
        "animation_mode": ANIM_CONTINUOUS,
        "render_style_label": RENDER_TERRAIN,
        "camera_motion_label": CAMERA_PAN,
        "camera_view": VIEW_LOW_DIAGONAL,
        "cinematic_zoom": 1.04,
        "grid_size": 70,
        "num_frames": 32,
        "kicker": "건조 지형",
        "summary": "\uc0ac\uad6c\uc640 \uc640\ub514, \uba54\uc0ac \uac19\uc740 \uac74\uc870 \uc9c0\ud615\uc744 \ube60\ub974\uac8c \ud6d1\uc2b5\ub2c8\ub2e4.",
        "lesson_focus": "\ubc14\ub78c\uacfc \uac74\uc870 \ud658\uacbd\uc774 \uc9c0\ud45c \ubaa8\uc591\uc744 \ubc14\uafb8\ub294 \ubc29\uc2dd\uc744 \uc77d\uc5b4\ub0c5\ub2c8\ub2e4.",
        "difficulty_label": "\ubcf4\ud1b5",
        "observation_prompt": "\ubc14\ub78c \ubc29\ud5a5, \uadf8\ub298 \uba74, \uac00\ud30c\ub978 \uc804\uba74 \uac19\uc740 \ud2b9\uc9d5\uc744 \ube44\uad50\ud574 \ubcf4\uc138\uc694.",
    },
    COASTAL: {
        "gallery_mode": TEACHER_MODE,
        "stage": 0.82,
        "animation_mode": ANIM_CONTINUOUS,
        "render_style_label": RENDER_SATELLITE,
        "camera_motion_label": CAMERA_ORBIT,
        "camera_view": VIEW_FRONT_Y_NEG,
        "cinematic_zoom": 1.02,
        "grid_size": 74,
        "num_frames": 36,
        "kicker": "해안 지형",
        "summary": "\uce68\uc2dd\uacfc \ud1f4\uc801\uc774 \ub9cc\ub098\ub294 \ud574\uc548 \uc9c0\ud615\uc744 \uc1fc\ucf00\uc774\uc2a4\ud615\uc73c\ub85c \ubcf4\uc5ec\uc8fc\ub294 preset\uc785\ub2c8\ub2e4.",
        "lesson_focus": "\ud30c\ub791 \uce68\uc2dd\uacfc \uc5f0\uc548 \ud1f4\uc801\uc774 \ud55c \ud574\uc548\uc5d0\uc11c \uc5b4\ub5bb\uac8c \ud568\uaed8 \ubcf4\uc774\ub294\uc9c0 \ube44\uad50\ud569\ub2c8\ub2e4.",
        "difficulty_label": "\ubcf4\ud1b5",
        "observation_prompt": "\uc808\ubcbd\uc774 \ud6c4\ud1f4\ud558\ub294 \uacf3\uacfc \uc0ac\uc8fc\uac00 \ubc1c\ub2ec\ud558\ub294 \uacf3\uc744 \uac19\uc774 \ucc3e\uc544\ubcf4\uc138\uc694.",
    },
}


LANDFORM_OVERRIDES: Dict[str, Dict[str, Any]] = {
    "alluvial_fan": {
        "title": "\uc120\uc0c1\uc9c0",
        "summary": "\uc0b0\uc9c0 \ucd9c\uad6c\uc5d0\uc11c \ud1f4\uc801\ubb3c\uc774 \ubd80\ucc44\uaf34\ub85c \ud37c\uc9c0\ub294 \uc804\ud615\uc801\uc778 \uc120\uc0c1\uc9c0 \uc0ac\ub840\uc785\ub2c8\ub2e4.",
        "lesson_focus": "\uc0b0\uc9c0 \ucd9c\uad6c\uc5d0\uc11c \uc720\uc18d\uc774 \uc904\uba74 \ud1f4\uc801\ubb3c\uc774 \uc65c \ubd80\ucc44\uaf34\ub85c \ud37c\uc9c0\ub294\uc9c0 \ubcf4\uc5ec\uc90d\ub2c8\ub2e4.",
        "difficulty_label": "\ubcf4\ud1b5",
        "observation_prompt": "\uc0b0\ub85d\uc744 \ubc97\uc5b4\ub09c \ub4a4 \ud1f4\uc801\ubb3c\uc774 \ud37c\uc9c0\ub294 \uc9c0\uc810\uc744 \ucc3e\uc544\ubcf4\uc138\uc694.",
        "camera_view": VIEW_FRONT_Y_NEG,
        "lab_selected_landform": "\uc120\uc0c1\uc9c0 (\uae09\uacbd\uc0ac)",
        "lab_scenario_category": SCENARIO_MOUNTAIN_RIVER,
    },
    "free_meander": {
        "title": "\uace1\ub958 \ud558\ucc9c",
        "summary": "\uce21\ubc29 \uce68\uc2dd\uacfc \ud1f4\uc801\uc774 \ud568\uaed8 \ubcf4\uc774\ub294 \uc0ac\ud589\ucc9c \ubaa8\ubc94 \uc0ac\ub840\uc785\ub2c8\ub2e4.",
        "lesson_focus": "\ud558\ucc9c \ubc14\uae65\ucabd \uce68\uc2dd\uacfc \uc548\ucabd \ud1f4\uc801\uc744 \ud55c \ud654\uba74\uc5d0\uc11c \ube44\uad50\ud558\ub294 \ub370 \uc801\ud569\ud569\ub2c8\ub2e4.",
        "difficulty_label": "\ubcf4\ud1b5",
        "observation_prompt": "\uace1\ub958 \ubc14\uae65\ucabd\uacfc \uc548\ucabd \uc911 \uc5b4\ub290 \ucabd\uc774 \uae4e\uc774\uace0 \uc313\uc774\ub294\uc9c0 \ubcf4\uc138\uc694.",
        "lab_selected_landform": "\uace1\ub958 (\uc0ac\ud589\ucc9c)",
        "lab_scenario_category": SCENARIO_MOUNTAIN_RIVER,
    },
    "v_valley": {
        "title": "V\uc790\uace1",
        "summary": "\ud558\ucc9c \uce68\uc2dd\uc774 \uacc4\uace1\uc744 \uae4a\uac8c \ud30c\ub0b4\ub294 \uc7a5\uba74\uc744 \ubcf4\uae30 \uc88b\uc740 preset\uc785\ub2c8\ub2e4.",
        "lesson_focus": "\ud558\ucc9c \uce68\uc2dd\uc774 \uacc4\uace1 \ubc14\ub2e5\uc744 \uae4a\uac8c \ud30c\ub0b4\ub294 \ubcc0\ud654\ub97c \uc9c1\uad00\uc801\uc73c\ub85c \ubcf4\uc5ec\uc90d\ub2c8\ub2e4.",
        "difficulty_label": "\uc785\ubb38",
        "observation_prompt": "\uacc4\uace1\uc774 \ub113\uc5b4\uc9c0\uae30\ubcf4\ub2e4 \uae4a\uc5b4\uc9c0\ub294 \ubcc0\ud654\uac00 \uba3c\uc800 \ubcf4\uc774\ub294\uc9c0 \ud655\uc778\ud574 \ubcf4\uc138\uc694.",
        "lab_selected_landform": "V\uc790\uace1 (\ud558\ucc9c\uce68\uc2dd)",
        "lab_scenario_category": SCENARIO_MOUNTAIN_RIVER,
    },
    "delta": {
        "title": "\uc0bc\uac01\uc8fc",
        "summary": "\ud558\uad6c \uc804\uba74\ubd80\uac00 \uc804\uc9c4\ud558\uba70 \ubd84\uae30 \uc218\ub85c\uac00 \ub9cc\ub4e4\uc5b4\uc9c0\ub294 \ub300\ud45c \uc0ac\ub840\uc785\ub2c8\ub2e4.",
        "lesson_focus": "\ud1f4\uc801\uc774 \uc313\uc774\uba74 \ud558\uad6c \uc120\uc774 \uc55e\uc73c\ub85c \ub098\uc544\uac00\ub294 \uacfc\uc815\uc744 \ubcf4\uc5ec\uc90d\ub2c8\ub2e4.",
        "difficulty_label": "\ubcf4\ud1b5",
        "observation_prompt": "\uc5b4\ub290 \ubd80\ubd84\uc5d0\uc11c \uc0c8\ub85c\uc6b4 \uc721\uc9c0\uac00 \ubc14\ub2e4\ucabd\uc73c\ub85c \ubc1c\ub2ec\ud558\ub294\uc9c0 \ubcf4\uc138\uc694.",
        "camera_view": VIEW_FRONT_Y_NEG,
        "lab_selected_landform": "\uc0bc\uac01\uc8fc (\ud558\uad6c)",
        "lab_scenario_category": SCENARIO_MOUNTAIN_RIVER,
    },
    "bird_foot_delta": {
        "title": "\uc870\uc871\ud615 \uc0bc\uac01\uc8fc",
        "summary": "\uc881\uc740 \uc218\ub85c\uac00 \uba40\ub9ac \ubf57\ub294 \uc0bc\uac01\uc8fc \ud328\ud134\uc744 \ube60\ub974\uac8c \ud655\uc778\ud560 \uc218 \uc788\uc2b5\ub2c8\ub2e4.",
        "lab_selected_landform": "\uc0bc\uac01\uc8fc (\ud558\uad6c)",
        "lab_scenario_category": SCENARIO_MOUNTAIN_RIVER,
    },
    "u_valley": {
        "title": "U\uc790\uace1",
        "summary": "\ube59\ud558\uac00 \uacc4\uace1 \ub2e8\uba74\uc744 \ub113\uace0 \ub465\uae00\uac8c \ub2e4\ub4ec\ub294 \uc804\ud615\uc801\uc778 \uc0ac\ub840\uc785\ub2c8\ub2e4.",
        "lesson_focus": "\ud558\ucc9c \uacc4\uace1\uacfc \ube59\ud558 \uacc4\uace1\uc758 \ub2e8\uba74 \ucc28\uc774\ub97c \ubc14\ub85c \ube44\uad50\ud560 \uc218 \uc788\uc2b5\ub2c8\ub2e4.",
        "difficulty_label": "\ubcf4\ud1b5",
        "observation_prompt": "\uacc4\uace1 \ubc14\ub2e5\uc774 \ud3c9\ud3c9\ud558\uac8c \ub113\uc5b4\uc9c0\ub294 \ubd80\ubd84\uc744 \ucc3e\uc544\ubcf4\uc138\uc694.",
        "lab_selected_landform": "U\uc790\uace1 (\ube59\ud558\uce68\uc2dd)",
        "lab_scenario_category": SCENARIO_GLACIAL_COASTAL,
    },
    "fjord": {
        "title": "\ud53c\uc624\ub974",
        "summary": "\ube59\ud558\uace1\uc774 \ud574\uc218\uba74 \uc0c1\uc2b9\uacfc \ub9cc\ub098 \uae4a\uc740 \ub9cc\uc73c\ub85c \ub0a8\ub294 \uc0ac\ub840\uc785\ub2c8\ub2e4.",
        "camera_view": VIEW_FRONT_Y_NEG,
        "lab_selected_landform": "\ud53c\uc624\ub974 (\ud574\uc218\uba74\uc0c1\uc2b9)",
        "lab_scenario_category": SCENARIO_GLACIAL_COASTAL,
    },
    "shield_volcano": {
        "title": "\uc21c\uc0c1\ud654\uc0b0",
        "summary": "\ub113\uace0 \uc644\ub9cc\ud55c \ud654\uc0b0\uccb4\uac00 \ud615\uc131\ub418\ub294 \uc0ac\ub840\ub97c \ud68c\uc804 \uc2dc\uc810\uc73c\ub85c \uc0b4\ud3b4\ubd05\ub2c8\ub2e4.",
        "lab_selected_landform": "\ud654\uc0b0 (\ubd84\ucd9c)",
        "lab_scenario_category": SCENARIO_ARID_SPECIAL,
    },
    "stratovolcano": {
        "title": "\uc131\uce35\ud654\uc0b0",
        "summary": "\uae09\ud55c \uc0ac\uba74\uacfc \uc911\uc2ec \ubd84\ud654\uad6c\uac00 \uac15\uc870\ub418\ub294 \ud654\uc0b0 \ubaa8\ubc94 \uc0ac\ub840\uc785\ub2c8\ub2e4.",
        "lab_selected_landform": "\ud654\uc0b0 (\ubd84\ucd9c)",
        "lab_scenario_category": SCENARIO_ARID_SPECIAL,
    },
    "karst_doline": {
        "title": "\ub3cc\ub9ac\ub124",
        "summary": "\uc6a9\uc2dd\uc73c\ub85c \ud568\ubab0\uc9c0\uac00 \ubc1c\ub2ec\ud558\ub294 \uce74\ub974\uc2a4\ud2b8 \uc9c0\ud615\uc744 \ubc14\ub85c \ud655\uc778\ud569\ub2c8\ub2e4.",
        "lab_selected_landform": "\uce74\ub974\uc2a4\ud2b8 (\uc6a9\ud574)",
        "lab_scenario_category": SCENARIO_ARID_SPECIAL,
    },
    "tower_karst": {
        "title": "\ud0d1 \uce74\ub974\uc2a4\ud2b8",
        "summary": "\uc6a9\uc2dd\uacfc \uc794\uad6c\uac00 \ud568\uaed8 \ub4dc\ub7ec\ub098\ub294 \uce74\ub974\uc2a4\ud2b8 \ud0d1 \uc9c0\ud615 \uc0ac\ub840\uc785\ub2c8\ub2e4.",
        "lab_selected_landform": "\uce74\ub974\uc2a4\ud2b8 (\uc6a9\ud574)",
        "lab_scenario_category": SCENARIO_ARID_SPECIAL,
    },
    "barchan": {
        "title": "\ubc14\ub974\ud55c",
        "summary": "\ubc14\ub78c \ubc29\ud5a5\uc744 \ub530\ub77c \uc774\ub3d9\ud558\ub294 \ucd08\uc2b9\ub2ec\ud615 \uc0ac\uad6c\ub97c \ube60\ub974\uac8c \ubcfc \uc218 \uc788\uc2b5\ub2c8\ub2e4.",
        "lesson_focus": "\ubc14\ub78c \ubc29\ud5a5\uc774 \uc0ac\uad6c \ubaa8\uc591\uacfc \uc774\ub3d9 \ubc29\ud5a5\uc744 \uacb0\uc815\ud558\ub294 \ubaa8\uc2b5\uc744 \ubcf4\uc5ec\uc90d\ub2c8\ub2e4.",
        "difficulty_label": "\uc785\ubb38",
        "observation_prompt": "\uc644\ub9cc\ud55c \uba74\uacfc \uac00\ud30c\ub978 \uba74\uc774 \uac01\uac01 \ubc14\ub78c \ubc29\ud5a5\uacfc \uc5b4\ub5bb\uac8c \uc5f0\uacb0\ub418\ub294\uc9c0 \ubcf4\uc138\uc694.",
        "lab_selected_landform": "\ubc14\ub974\ud55c (\uc0ac\uad6c)",
        "lab_scenario_category": SCENARIO_ARID_SPECIAL,
    },
    "coastal_cliff": {
        "title": "\ud574\uc2dd\uc560",
        "summary": "\ud30c\ub791 \uce68\uc2dd\uc73c\ub85c \uc808\ubcbd\uc774 \ud6c4\ud1f4\ud558\ub294 \ud574\uc548 \ubaa8\ubc94 \uc0ac\ub840\uc785\ub2c8\ub2e4.",
        "lesson_focus": "\ud30c\ub791 \uce68\uc2dd\uc774 \uc808\ubcbd\uc744 \ub4a4\ub85c \ubb3c\ub9ac\ub294 \ubcc0\ud654\ub97c \ube60\ub974\uac8c \ud655\uc778\ud558\ub294 \ub370 \uc801\ud569\ud569\ub2c8\ub2e4.",
        "difficulty_label": "\ubcf4\ud1b5",
        "observation_prompt": "\ud574\uc548 \uc120\uc774 \ud6c4\ud1f4\ud558\ub294 \uacf3\uacfc \ud30c\ub791 \uce68\uc2dd\uc774 \uc9d1\uc911\ub418\ub294 \ubd80\ubd84\uc744 \ucc3e\uc544\ubcf4\uc138\uc694.",
        "lab_selected_landform": "\ud574\uc2dd\uc560 (\ud30c\ub791\uce68\uc2dd)",
        "lab_scenario_category": SCENARIO_GLACIAL_COASTAL,
    },
}


LAB_PRESET_DEFAULTS: Dict[str, Any] = {
    "user_mode": "\ud559\uc0dd \ub2e8\uc21c\ubaa8\ub4dc",
    "speed_mode": "\uade0\ud615",
    "force_level": 60,
    "auto_run": True,
}


def pretty_title(landform_key: str) -> str:
    return landform_key.replace("_", " ").title()


def get_gallery_showcase_preset(category: str, landform_key: str) -> Dict[str, Any]:
    preset = dict(CATEGORY_DEFAULTS.get(category, CATEGORY_DEFAULTS[RIVER]))
    preset.update(
        {
            "category": category,
            "landform_key": landform_key,
            "title": pretty_title(landform_key),
        }
    )
    preset.update(LANDFORM_OVERRIDES.get(landform_key, {}))
    world_case = get_featured_world_case(landform_key)
    if world_case is not None:
        preset["world_case"] = world_case
        preset["world_case_label"] = f'{world_case["title"]} · {world_case["location_label"]}'
        preset["world_case_processes"] = " · ".join(world_case.get("process_focus", ()))
        preset["world_case_question"] = world_case.get("student_question", "")
        preset["world_case_teacher_note"] = world_case.get("teacher_note", "")
    return preset


def apply_gallery_showcase_preset(session_state, preset: Dict[str, Any]) -> None:
    session_state["gallery_mode"] = preset.get("gallery_mode", TEACHER_MODE)
    session_state["gallery_cat"] = preset["category"]
    session_state["landform_select"] = preset["landform_key"]
    session_state["gallery_stage_slider"] = preset.get("stage", 1.0)
    session_state["anim_mode"] = preset.get("animation_mode", ANIM_CONTINUOUS)
    session_state["gallery_render_style"] = preset.get("render_style_label", RENDER_TERRAIN)
    session_state["gallery_camera_motion"] = preset.get("camera_motion_label", CAMERA_FIXED)
    session_state["camera_view"] = preset.get("camera_view", VIEW_DEFAULT)
    session_state["gallery_cinematic_zoom"] = preset.get("cinematic_zoom", 1.0)
    session_state["gallery_res"] = preset.get("grid_size", 60)
    session_state["anim_frames"] = preset.get("num_frames", 30)
    if preset.get("render_style_label") == RENDER_SATELLITE:
        session_state["gallery_texture_mode"] = TEXTURE_SYNTHETIC


def queue_gallery_showcase_preset(session_state, preset: Dict[str, Any]) -> None:
    session_state["gallery_pending_preset"] = dict(preset)


def consume_gallery_showcase_preset(session_state) -> Optional[Dict[str, Any]]:
    preset = session_state.pop("gallery_pending_preset", None)
    if preset is None:
        return None

    apply_gallery_showcase_preset(session_state, preset)
    return preset


def build_lab_showcase_preset(category: str, landform_key: str) -> Optional[Dict[str, Any]]:
    showcase = get_gallery_showcase_preset(category, landform_key)
    lab_selected_landform = showcase.get("lab_selected_landform")
    lab_scenario_category = showcase.get("lab_scenario_category")
    if not lab_selected_landform or not lab_scenario_category:
        return None

    preset = dict(LAB_PRESET_DEFAULTS)
    preset.update(
        {
            "source": "gallery_showcase",
            "showcase_title": showcase.get("title", pretty_title(landform_key)),
            "scenario_category": lab_scenario_category,
            "selected_landform": lab_selected_landform,
        }
    )
    if showcase.get("world_case") is not None:
        preset["world_case"] = dict(showcase["world_case"])
    return preset
