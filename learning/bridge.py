"""
스펙 → 엔진 브리지

스펙의 landform 키로 engine.ideal_landforms 의 생성기를 찾아
(고도 배열, 메타데이터) 를 돌려준다. 메타데이터를 지원하지 않는 생성기면
메타데이터는 빈 dict 가 된다.

일부 지형은 애니메이션 레지스트리에 등록된 함수가 메타데이터를 지원하지 않고
같은 이름의 정적 생성기가 지원한다 (예: coastal_cliff). 그 경우 스펙의
"generator" 항목으로 함수 이름을 직접 지정한다.
"""
from typing import Any, Callable, Dict, List, Optional, Tuple

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

    # 모든 지형에서 쓸 수 있는 공통 키. 판정에서 {"key": "_stage", ...} 로 참조.
    metadata.setdefault("_stage", stage)
    return np.asarray(elevation), metadata
