"""
스펙 → 엔진 브리지

스펙의 landform 키로 engine.ideal_landforms 의 생성기를 찾아
(고도 배열, 메타데이터) 를 돌려준다. 메타데이터를 지원하지 않는 생성기면
메타데이터는 빈 dict 가 된다.

일부 지형은 애니메이션 레지스트리에 등록된 함수가 메타데이터를 지원하지 않고
같은 이름의 정적 생성기가 지원한다 (예: coastal_cliff). 그 경우 스펙의
"generator" 항목으로 함수 이름을 직접 지정한다.
"""
from typing import Any, Callable, Dict, List, Optional, Tuple  # noqa: F401

import numpy as np

from engine import ideal_landforms as _il
from engine.ideal_landforms import ANIMATED_LANDFORM_GENERATORS, IDEAL_LANDFORM_GENERATORS


def available_landforms() -> List[str]:
    """스펙에서 쓸 수 있는 landform 키 (단계 애니메이션 지원)."""
    return sorted(ANIMATED_LANDFORM_GENERATORS.keys())


def _resolve_generator(landform: str, generator: Optional[str]) -> Callable:
    if generator:
        fn = getattr(_il, generator, None)
        if fn is None or not callable(fn):
            raise KeyError(f"engine.ideal_landforms 에 '{generator}' 함수가 없습니다.")
        return fn
    if landform in ANIMATED_LANDFORM_GENERATORS:
        return ANIMATED_LANDFORM_GENERATORS[landform]
    if landform in IDEAL_LANDFORM_GENERATORS:
        return IDEAL_LANDFORM_GENERATORS[landform]
    raise KeyError(f"알 수 없는 landform: '{landform}'")


def generate_stage(landform: str, grid_size: int, stage: float,
                   generator: Optional[str] = None) -> Tuple[np.ndarray, Dict[str, Any]]:
    """지정 단계의 지형과 메타데이터를 생성한다.

    메타데이터 미지원 생성기는 TypeError 를 내므로 그때는 고도만 받는다.
    """
    fn = _resolve_generator(landform, generator)
    stage = float(min(1.0, max(0.0, stage)))

    try:
        result = fn(grid_size, stage, return_metadata=True)
    except TypeError:
        result = fn(grid_size, stage)

    if isinstance(result, tuple) and len(result) == 2:
        elevation, metadata = result
        metadata = dict(metadata or {})
    else:
        elevation, metadata = result, {}

    elevation = np.asarray(elevation)
    # 모든 지형에서 쓸 수 있는 공통 키. 생성기가 같은 이름을 주면 생성기 값을 우선한다.
    metadata.setdefault("_stage", stage)
    for key, value in terrain_metrics(elevation).items():
        metadata.setdefault(key, value)
    return elevation, metadata


def _as_scalar(value: Any) -> Optional[float]:
    """판정에 쓸 수 있는 값을 숫자로. 목록은 길이, 배열·dict·문자열은 None."""
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float, np.integer, np.floating)):
        return float(value)
    if isinstance(value, (list, tuple)):
        return float(len(value))
    return None


def describe_check_keys(landform: str, generator: Optional[str] = None,
                        stages: Tuple[float, ...] = (0.0, 0.5, 1.0),
                        grids: Tuple[int, int] = (40, 100)) -> List[Dict[str, Any]]:
    """slider_target 판정에 쓸 만한 키와, 형성 단계에 따른 값 변화를 돌려준다.

    단계에 따라 값이 변하지 않는 키는 뺀다 (슬라이더를 움직일 이유가 없으므로).
    두 해상도에서 같은 단계의 값이 10% 넘게 다르면 resolution_dependent=True.
    """
    lo_grid, hi_grid = grids
    probes = {g: [generate_stage(landform, g, s, generator)[1] for s in stages] for g in grids}

    out: List[Dict[str, Any]] = []
    for key in sorted(probes[hi_grid][0]):
        if key == "stage_description":
            continue
        values = [_as_scalar(m.get(key)) for m in probes[hi_grid]]
        if any(v is None for v in values):
            continue
        if key != "_stage" and max(values) - min(values) < 1e-9:
            continue
        other = [_as_scalar(m.get(key)) for m in probes[lo_grid]]
        dependent = any(
            o is None or abs(o - v) > 0.1 * max(abs(v), abs(o), 1e-9)
            for o, v in zip(other, values)
        )
        is_len = isinstance(probes[hi_grid][-1].get(key), (list, tuple))
        out.append({
            "key": key,
            "values": values,
            "stages": list(stages),
            "measure": "len" if is_len else "value",
            "resolution_dependent": dependent,
        })
    return out


def terrain_metrics(elevation: np.ndarray) -> Dict[str, float]:
    """고도 배열만으로 계산하는 공통 판정값.

    - relief         : 최고 고도 - 최저 고도 (m)
    - max_elevation  : 최고 고도 (m)
    - min_elevation  : 최저 고도 (m)
    - water_fraction : 고도 0 미만(바다·호수) 격자 비율 (0~1). 갤러리의 물 표시 기준과 같다.

    주의: 일부 생성기는 골짜기 폭 등을 '격자 칸 수'로 그리므로 water_fraction 은
    해상도에 따라 달라질 수 있다 (예: 리아스 해안). 판정 기준으로 쓰기 전에
    tests/test_learning_specs.py 가 여러 해상도에서 확인한다.
    """
    e = np.asarray(elevation, dtype=float)
    return {
        "relief": float(e.max() - e.min()),
        "max_elevation": float(e.max()),
        "min_elevation": float(e.min()),
        "water_fraction": float((e < 0).mean()),
    }
