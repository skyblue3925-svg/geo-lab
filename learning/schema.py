"""
학습 스펙(JSON) 형식 정의와 검증

스펙은 LLM이 제안하고 교사가 검수하는 산출물이다. 따라서
- 사람이 읽고 고칠 수 있게 평범한 JSON 으로 유지한다.
- 검증기는 "렌더러가 터지지 않을 만큼"만 엄격하다. 교육 내용의 옳고 그름은 교사가 본다.

최상위 구조:
{
  "spec_version": "0.1",
  "id": "alluvial_fan_basic",          # 파일명과 같게
  "title": "...",                       # 학생에게 보이는 제목
  "landform": "alluvial_fan",           # engine.ideal_landforms 의 키
  "generator": "create_coastal_cliff",  # (선택) 메타데이터를 지원하는 생성기 이름으로 덮어쓰기
  "grade": "고1 통합사회 / 고2 한국지리",
  "duration_min": 15,
  "objectives": ["...", "..."],         # 교사가 승인한 학습목표
  "misconceptions": [{"belief": "...", "correction": "..."}],
  "levels": [ { ...level... }, ... ],
  "summary": "...",                     # 마지막에 보여줄 정리
  "teacher_notes": "..."                # 수업 운영 메모 (학생에게는 안 보임)
}

level 구조:
{
  "id": "L1",
  "title": "...",
  "stage": 0.25,                 # 고정 단계 (0~1)  — 또는
  "stage_range": [0.3, 0.7],     # 학생이 이 범위에서 슬라이더를 움직임
  "prompt": "...",               # 이 단계에서 무엇을 보라는 안내
  "task": {
    "type": "multiple_choice" | "slider_target" | "observe",
    "question": "...",
    "choices": ["...", "..."],   # multiple_choice
    "answer": 1,                 # choices 의 인덱스 (0부터)
    "check": { ... },            # slider_target: checks.py 참고
    "hints": ["1차 힌트", "2차 힌트", "3차 힌트"],   # 계층형 힌트
    "feedback": {"correct": "...", "incorrect": "..."},
    "worked_solution": "..."     # 두 번 틀리면 열리는 풀이
  }
}
"""
import json
import os
from typing import Any, Dict, List

SPEC_VERSION = "0.1"
SPECS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "specs")

TASK_TYPES = ("multiple_choice", "slider_target", "observe")
CHECK_OPS = ("equals", "gte", "lte", "contains", "len_gte", "truthy")


def _is_number(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def validate_spec(spec: Dict[str, Any], known_landforms: List[str] = None) -> List[str]:
    """스펙을 검사하고 문제 목록을 돌려준다. 빈 목록이면 통과."""
    errors: List[str] = []

    if not isinstance(spec, dict):
        return ["스펙은 JSON 객체여야 합니다."]

    for key in ("id", "title", "landform", "objectives", "levels"):
        if key not in spec:
            errors.append(f"필수 항목 누락: '{key}'")

    if spec.get("spec_version") not in (None, SPEC_VERSION):
        errors.append(f"spec_version 은 '{SPEC_VERSION}' 이어야 합니다 (현재: {spec.get('spec_version')})")

    if known_landforms is not None and spec.get("landform") not in known_landforms:
        errors.append(f"알 수 없는 landform: '{spec.get('landform')}'")

    objectives = spec.get("objectives", [])
    if not isinstance(objectives, list) or not objectives:
        errors.append("objectives 는 비어 있지 않은 문자열 목록이어야 합니다.")

    for i, m in enumerate(spec.get("misconceptions", []) or []):
        if not isinstance(m, dict) or "belief" not in m or "correction" not in m:
            errors.append(f"misconceptions[{i}] 에는 belief 와 correction 이 필요합니다.")

    levels = spec.get("levels", [])
    if not isinstance(levels, list) or not levels:
        errors.append("levels 는 비어 있지 않은 목록이어야 합니다.")
        return errors

    seen_ids = set()
    for i, level in enumerate(levels):
        where = f"levels[{i}]"
        if not isinstance(level, dict):
            errors.append(f"{where} 는 객체여야 합니다.")
            continue

        lid = level.get("id")
        if not lid:
            errors.append(f"{where}: id 가 필요합니다.")
        elif lid in seen_ids:
            errors.append(f"{where}: id '{lid}' 가 중복됩니다.")
        seen_ids.add(lid)

        if "title" not in level:
            errors.append(f"{where}: title 이 필요합니다.")

        has_stage = "stage" in level
        has_range = "stage_range" in level
        if has_stage == has_range:
            errors.append(f"{where}: stage 와 stage_range 중 정확히 하나만 지정해야 합니다.")
        if has_stage and not (_is_number(level["stage"]) and 0.0 <= level["stage"] <= 1.0):
            errors.append(f"{where}: stage 는 0~1 사이 숫자여야 합니다.")
        if has_range:
            rng = level["stage_range"]
            ok = (isinstance(rng, list) and len(rng) == 2 and all(_is_number(v) for v in rng)
                  and 0.0 <= rng[0] < rng[1] <= 1.0)
            if not ok:
                errors.append(f"{where}: stage_range 는 [시작, 끝] (0 ≤ 시작 < 끝 ≤ 1) 이어야 합니다.")

        task = level.get("task")
        if not isinstance(task, dict):
            errors.append(f"{where}: task 가 필요합니다.")
            continue

        ttype = task.get("type")
        if ttype not in TASK_TYPES:
            errors.append(f"{where}.task: type 은 {TASK_TYPES} 중 하나여야 합니다.")
            continue

        if ttype == "multiple_choice":
            choices = task.get("choices")
            if not isinstance(choices, list) or len(choices) < 2:
                errors.append(f"{where}.task: choices 는 2개 이상이어야 합니다.")
            ans = task.get("answer")
            if not isinstance(ans, int) or isinstance(ans, bool) or not (0 <= ans < len(choices or [])):
                errors.append(f"{where}.task: answer 는 choices 의 유효한 인덱스여야 합니다.")
            if "question" not in task:
                errors.append(f"{where}.task: question 이 필요합니다.")

        if ttype == "slider_target":
            if not has_range:
                errors.append(f"{where}: slider_target 과제는 stage_range 가 필요합니다.")
            check = task.get("check")
            if not isinstance(check, dict):
                errors.append(f"{where}.task: check 가 필요합니다.")
            else:
                if check.get("op") not in CHECK_OPS:
                    errors.append(f"{where}.task.check: op 는 {CHECK_OPS} 중 하나여야 합니다.")
                if "key" not in check:
                    errors.append(f"{where}.task.check: key (메타데이터 키) 가 필요합니다.")
                if check.get("op") != "truthy" and "value" not in check:
                    errors.append(f"{where}.task.check: value 가 필요합니다.")
            # slider_target 뒤에 객관식을 붙일 수 있음 (선택)
            if "choices" in task:
                choices = task["choices"]
                ans = task.get("answer")
                if not isinstance(choices, list) or len(choices) < 2:
                    errors.append(f"{where}.task: choices 는 2개 이상이어야 합니다.")
                elif not isinstance(ans, int) or isinstance(ans, bool) or not (0 <= ans < len(choices)):
                    errors.append(f"{where}.task: answer 는 choices 의 유효한 인덱스여야 합니다.")

        hints = task.get("hints", [])
        if hints is not None and not isinstance(hints, list):
            errors.append(f"{where}.task: hints 는 문자열 목록이어야 합니다.")

    return errors


def load_spec(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def list_specs(specs_dir: str = SPECS_DIR) -> Dict[str, str]:
    """{spec_id: 파일경로}. 파일명 순으로 정렬."""
    out: Dict[str, str] = {}
    if not os.path.isdir(specs_dir):
        return out
    for name in sorted(os.listdir(specs_dir)):
        if name.endswith(".json"):
            out[name[:-5]] = os.path.join(specs_dir, name)
    return out


def spec_to_json(spec: Dict[str, Any]) -> str:
    return json.dumps(spec, ensure_ascii=False, indent=2)
