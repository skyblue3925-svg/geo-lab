"""
메타데이터 기반 과제 판정

slider_target 과제는 학생이 형성 단계 슬라이더를 움직여 "어떤 상태"에 도달하게 한다.
그 상태는 엔진이 돌려주는 메타데이터로 판정한다. 예:

  {"key": "oxbow_formed", "op": "truthy"}                 # 우각호가 생겼는가
  {"key": "sinuosity",    "op": "gte", "value": 1.5}      # 사행도 1.5 이상
  {"key": "zone_mask",    "op": "contains", "value": 3}   # 선단(3) 존이 등장했는가
  {"key": "stacks_formed","op": "len_gte", "value": 1}    # 시스택이 1개 이상
  {"key": "_stage",       "op": "gte", "value": 0.6}      # 형성 단계 60% 이상 (모든 지형 공통)

op 목록은 schema.CHECK_OPS 와 같아야 한다.
"""
from typing import Any, Dict, Tuple

import numpy as np


def _describe(check: Dict[str, Any]) -> str:
    key, op, value = check.get("key"), check.get("op"), check.get("value")
    if op == "truthy":
        return f"{key} 가 참"
    if op == "contains":
        return f"{key} 에 {value} 포함"
    if op == "len_gte":
        return f"{key} 개수 ≥ {value}"
    return f"{key} {op} {value}"


def evaluate_check(check: Dict[str, Any], metadata: Dict[str, Any]) -> Tuple[bool, str]:
    """(통과 여부, 사람이 읽을 설명)."""
    key = check.get("key")
    op = check.get("op")
    value = check.get("value")

    if key not in metadata:
        return False, f"메타데이터에 '{key}' 가 없습니다 (이 지형은 해당 판정을 지원하지 않음)"

    actual = metadata[key]

    try:
        if op == "truthy":
            ok = bool(actual)
        elif op == "equals":
            ok = actual == value
        elif op == "gte":
            ok = float(actual) >= float(value)
        elif op == "lte":
            ok = float(actual) <= float(value)
        elif op == "contains":
            arr = np.asarray(actual)
            ok = bool(np.any(arr == value))
        elif op == "len_gte":
            ok = len(actual) >= int(value)
        else:
            return False, f"알 수 없는 판정 op: {op}"
    except (TypeError, ValueError) as e:
        return False, f"판정 오류 ({_describe(check)}): {e}"

    shown = actual
    if isinstance(actual, np.ndarray):
        shown = f"배열 {actual.shape}"
    elif isinstance(actual, (list, tuple)):
        shown = f"{len(actual)}개"
    elif isinstance(actual, float):
        shown = f"{actual:.2f}"

    return ok, f"{_describe(check)} → 현재 {shown}"
