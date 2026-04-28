"""Text-to-hypothesis mapper for theory-driven terrain modeling.

This module converts free-form theory text into simulation-ready
parameter scenarios (K, D, U, grid_size, total_time).
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Dict, List, Sequence, Tuple


@dataclass(frozen=True)
class TheoryScenario:
    scenario_id: str
    title: str
    narrative: str
    confidence: float
    parameters: Dict[str, float]
    assumptions: List[str]


@dataclass(frozen=True)
class TheoryInterpretation:
    summary: str
    signals: Dict[str, float]
    evidence_hints: List[str]
    uncertainty_notes: List[str]
    scenarios: List[TheoryScenario]


_ParamMap = Dict[str, float]
_KeywordMap = Sequence[Tuple[str, float]]


DIRECT_PATTERNS = {
    "K": re.compile(r"\bK\s*[:=]\s*([0-9]*\.?[0-9]+(?:e-?[0-9]+)?)", re.IGNORECASE),
    "D": re.compile(r"\bD\s*[:=]\s*([0-9]*\.?[0-9]+(?:e-?[0-9]+)?)", re.IGNORECASE),
    "U": re.compile(r"\bU\s*[:=]\s*([0-9]*\.?[0-9]+(?:e-?[0-9]+)?)", re.IGNORECASE),
    "grid_size": re.compile(r"(?:grid|격자|해상도)\s*[:=]?\s*([0-9]{2,3})", re.IGNORECASE),
    "total_time": re.compile(r"(?:time|기간|연수|years?)\s*[:=]?\s*([0-9]{4,6})", re.IGNORECASE),
}

EROSION_HINTS: _KeywordMap = (
    ("침식", 1.0),
    ("하각", 1.1),
    ("절단", 0.9),
    ("급경사", 0.7),
    ("홍수", 0.8),
    ("유량 증가", 0.8),
    ("하천 에너지", 0.9),
    ("파랑", 0.7),
)
DEPOSITION_HINTS: _KeywordMap = (
    ("퇴적", 1.0),
    ("선상지", 0.8),
    ("삼각주", 0.9),
    ("평야", 0.6),
    ("하중", 0.7),
    ("완만", 0.5),
    ("사면 붕괴", 0.7),
)
UPLIFT_HINTS: _KeywordMap = (
    ("융기", 1.2),
    ("조산", 1.0),
    ("단층", 0.9),
    ("지각 상승", 1.1),
    ("구조 운동", 0.8),
)
STABILITY_HINTS: _KeywordMap = (
    ("안정", 1.0),
    ("보전", 0.8),
    ("완충", 0.7),
    ("저감", 0.6),
)
RAPID_HINTS: _KeywordMap = (
    ("급격", 1.0),
    ("단기간", 1.0),
    ("빠르게", 0.8),
    ("짧은 시간", 0.9),
)
LONGTERM_HINTS: _KeywordMap = (
    ("장기", 1.0),
    ("점진", 0.8),
    ("수만년", 1.2),
    ("오랜 기간", 1.0),
    ("누적", 0.8),
)
HIGHRES_HINTS: _KeywordMap = (
    ("정밀", 1.0),
    ("고해상도", 1.0),
    ("세밀", 0.9),
)
LOWRES_HINTS: _KeywordMap = (
    ("개략", 1.0),
    ("거시", 0.7),
    ("빠른 검토", 0.9),
)

TYPE_HINTS = [
    ("빙하", "빙하 우세 가설"),
    ("피오르", "빙하-해안 복합 가설"),
    ("사막", "건조지형 가설"),
    ("와디", "건조지형-돌발홍수 가설"),
    ("카르스트", "용식 우세 가설"),
    ("화산", "화산지형 가설"),
    ("해안", "해안변형 가설"),
    ("삼각주", "하구 퇴적 가설"),
]


def _clip(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _score_text(text: str, mapping: _KeywordMap) -> Tuple[float, List[str]]:
    score = 0.0
    hits: List[str] = []
    for key, weight in mapping:
        if key in text:
            score += weight
            hits.append(key)
    return score, hits


def _extract_direct(text: str) -> Dict[str, float]:
    direct: Dict[str, float] = {}
    for key, pattern in DIRECT_PATTERNS.items():
        match = pattern.search(text)
        if match:
            try:
                direct[key] = float(match.group(1))
            except Exception:
                continue
    return direct


def _normalize_params(params: Dict[str, float]) -> Dict[str, float]:
    return {
        "K": float(_clip(params["K"], 1e-6, 1e-2)),
        "D": float(_clip(params["D"], 1e-4, 1.0)),
        "U": float(_clip(params["U"], 0.0, 1e-2)),
        "grid_size": int(_clip(params["grid_size"], 50, 180)),
        "total_time": int(_clip(params["total_time"], 10000, 120000)),
    }


def _make_alt(
    base: Dict[str, float],
    scenario_id: str,
    title: str,
    narrative: str,
    confidence: float,
    k_mult: float,
    d_mult: float,
    u_mult: float,
    t_mult: float,
    assumptions: List[str],
) -> TheoryScenario:
    params = _normalize_params(
        {
            "K": base["K"] * k_mult,
            "D": base["D"] * d_mult,
            "U": base["U"] * u_mult,
            "grid_size": base["grid_size"],
            "total_time": base["total_time"] * t_mult,
        }
    )
    return TheoryScenario(
        scenario_id=scenario_id,
        title=title,
        narrative=narrative,
        confidence=float(_clip(confidence, 0.05, 0.95)),
        parameters=params,
        assumptions=assumptions,
    )


def interpret_theory_text(text: str, base_params: _ParamMap | None = None) -> TheoryInterpretation:
    """Interpret theory text into one primary and two alternative scenarios."""
    base = {
        "K": 0.00010,
        "D": 0.0100,
        "U": 0.00030,
        "grid_size": 100,
        "total_time": 50000,
    }
    if base_params:
        for key in base:
            if key in base_params:
                base[key] = float(base_params[key])

    text = (text or "").strip()
    if not text:
        params = _normalize_params(base)
        empty = TheoryScenario(
            scenario_id="baseline",
            title="기본 가설",
            narrative="이론 텍스트가 없어 현재 기본 파라미터를 유지합니다.",
            confidence=0.30,
            parameters=params,
            assumptions=["추가 이론 입력 전 기본값 유지"],
        )
        return TheoryInterpretation(
            summary="이론 입력 없음",
            signals={"erosion": 0.0, "deposition": 0.0, "uplift": 0.0},
            evidence_hints=["이론 문장을 입력하면 자동으로 가설 시나리오를 생성합니다."],
            uncertainty_notes=["현재 결과는 모델 기본값에 의존합니다."],
            scenarios=[empty],
        )

    erosion_s, erosion_hits = _score_text(text, EROSION_HINTS)
    deposition_s, deposition_hits = _score_text(text, DEPOSITION_HINTS)
    uplift_s, uplift_hits = _score_text(text, UPLIFT_HINTS)
    stability_s, stability_hits = _score_text(text, STABILITY_HINTS)
    rapid_s, rapid_hits = _score_text(text, RAPID_HINTS)
    longterm_s, longterm_hits = _score_text(text, LONGTERM_HINTS)
    highres_s, _ = _score_text(text, HIGHRES_HINTS)
    lowres_s, _ = _score_text(text, LOWRES_HINTS)

    erosion_s = min(erosion_s, 3.0)
    deposition_s = min(deposition_s, 3.0)
    uplift_s = min(uplift_s, 3.0)
    stability_s = min(stability_s, 2.0)
    rapid_s = min(rapid_s, 2.0)
    longterm_s = min(longterm_s, 2.0)

    direct = _extract_direct(text)

    k_mult = 1.0 + (0.18 * erosion_s) - (0.10 * deposition_s) - (0.08 * stability_s) + (0.06 * rapid_s)
    d_mult = 1.0 + (0.20 * deposition_s) + (0.10 * stability_s) - (0.08 * erosion_s)
    u_mult = 1.0 + (0.22 * uplift_s) - (0.06 * stability_s)
    t_mult = 1.0 + (0.22 * longterm_s) - (0.18 * rapid_s)
    grid_add = int(round((highres_s - lowres_s) * 20.0))

    primary_params = {
        "K": base["K"] * _clip(k_mult, 0.45, 1.85),
        "D": base["D"] * _clip(d_mult, 0.45, 1.90),
        "U": base["U"] * _clip(u_mult, 0.45, 2.00),
        "grid_size": base["grid_size"] + grid_add,
        "total_time": base["total_time"] * _clip(t_mult, 0.60, 1.70),
    }

    for key, value in direct.items():
        if key in primary_params:
            primary_params[key] = value
    primary_params = _normalize_params(primary_params)

    title = "복합 지형 가설"
    for keyword, name in TYPE_HINTS:
        if keyword in text:
            title = name
            break

    all_hits = erosion_hits + deposition_hits + uplift_hits + stability_hits + rapid_hits + longterm_hits
    unique_hits = sorted(set(all_hits))
    signal_count = len(unique_hits) + (2 * len(direct))
    confidence = _clip(0.38 + (0.045 * signal_count), 0.30, 0.92)

    evidence_hints: List[str] = []
    if erosion_hits:
        evidence_hints.append(f"침식 신호: {', '.join(sorted(set(erosion_hits)))}")
    if deposition_hits:
        evidence_hints.append(f"퇴적 신호: {', '.join(sorted(set(deposition_hits)))}")
    if uplift_hits:
        evidence_hints.append(f"융기 신호: {', '.join(sorted(set(uplift_hits)))}")
    if stability_hits:
        evidence_hints.append(f"안정화 신호: {', '.join(sorted(set(stability_hits)))}")
    if direct:
        direct_txt = ", ".join(f"{k}={v:g}" for k, v in direct.items())
        evidence_hints.append(f"직접 입력 파라미터 감지: {direct_txt}")
    if not evidence_hints:
        evidence_hints.append("명시적 키워드가 적어 기본 가정 비중이 높습니다.")

    primary = TheoryScenario(
        scenario_id="primary",
        title=title,
        narrative="입력 이론에서 추출한 신호를 반영한 주 가설 시나리오입니다.",
        confidence=confidence,
        parameters=primary_params,
        assumptions=[
            "형태 변화는 K(침식), D(확산), U(융기)의 결합으로 근사합니다.",
            "동일 지형 결과를 만드는 대안 경로가 존재할 수 있습니다.",
        ],
    )
    conservative = _make_alt(
        base=primary_params,
        scenario_id="alt_conservative",
        title="대안 A (보수적 변화)",
        narrative="침식과 융기 강도를 낮추고 시간 규모를 늘린 보수적 대안입니다.",
        confidence=confidence * 0.72,
        k_mult=0.86,
        d_mult=1.08,
        u_mult=0.92,
        t_mult=1.20,
        assumptions=["장기 누적 변화 가정", "완만한 파라미터 조합"],
    )
    aggressive = _make_alt(
        base=primary_params,
        scenario_id="alt_aggressive",
        title="대안 B (공격적 변화)",
        narrative="침식·융기 강도를 높이고 시간 규모를 줄인 빠른 변화 대안입니다.",
        confidence=confidence * 0.66,
        k_mult=1.22,
        d_mult=0.90,
        u_mult=1.14,
        t_mult=0.84,
        assumptions=["상대적으로 고에너지 과정 가정", "단기 지형 재편 가능성 가정"],
    )

    uncertainties = [
        "실제 지형사는 단일 경로가 아니라 복수 가설이 동등하게 설명할 수 있습니다.",
        "지형 증거(사면, 퇴적체, 하천망) 해석에 따라 파라미터 역추정 결과가 달라질 수 있습니다.",
        "현재 모델은 단순화된 물리항을 사용하므로 절대치보다 상대 비교에 적합합니다.",
    ]

    summary = (
        f"해석 결과: 침식 {erosion_s:.1f}, 퇴적 {deposition_s:.1f}, "
        f"융기 {uplift_s:.1f}, 시간스케일(장기-단기) {(longterm_s - rapid_s):+.1f}"
    )

    return TheoryInterpretation(
        summary=summary,
        signals={
            "erosion": float(erosion_s),
            "deposition": float(deposition_s),
            "uplift": float(uplift_s),
            "stability": float(stability_s),
            "rapid": float(rapid_s),
            "longterm": float(longterm_s),
        },
        evidence_hints=evidence_hints,
        uncertainty_notes=uncertainties,
        scenarios=[primary, conservative, aggressive],
    )

