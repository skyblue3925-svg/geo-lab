from __future__ import annotations

from html import escape
from typing import Iterable


def build_provenance_panel(
    title: str,
    summary: str,
    badges: Iterable[dict[str, str]],
    notes: Iterable[str] | None = None,
) -> str:
    badge_html = "".join(
        f'<span class="provenance-badge badge-{escape(badge["tone"])}">{escape(badge["label"])}</span>'
        for badge in badges
    )

    note_items = ""
    if notes:
        note_items = "".join(f"<li>{escape(note)}</li>" for note in notes)
        note_items = f'<ul class="provenance-notes">{note_items}</ul>'

    return (
        '<div class="provenance-panel">'
        f'<div class="provenance-title">{escape(title)}</div>'
        f'<div class="provenance-summary">{escape(summary)}</div>'
        f'<div class="provenance-badges">{badge_html}</div>'
        f"{note_items}"
        "</div>"
    )


def build_export_provenance(context: dict[str, object]) -> dict[str, object]:
    badges = context.get("badges", [])
    return {
        "title": context.get("title"),
        "summary": context.get("summary"),
        "badges": [badge["label"] for badge in badges],
        "notes": context.get("notes", []),
    }


def get_lab_mode_context(student_mode: bool, theory_applied: dict | None = None) -> dict[str, object]:
    if student_mode:
        context = {
            "title": "교육 모드: 개념 이해 중심 시뮬레이션",
            "summary": "단순화된 물리 모델과 이상화된 초기 지형을 사용해 변화 방향을 부드럽게 보여주는 학습용 모드입니다.",
            "badges": [
                {"label": "교육 모드", "tone": "education"},
                {"label": "단순화 물리", "tone": "model"},
                {"label": "시각화 우선", "tone": "hybrid"},
            ],
            "notes": [
                "정확한 현장 재현보다 변화의 방향과 원인 이해가 목표입니다.",
                "해석 검증이 필요하면 Research Lab에서 관측 DEM과 비교하세요.",
            ],
        }
    else:
        context = {
            "title": "실험 모드: 파라미터 비교 중심 시뮬레이션",
            "summary": "단순화된 물리 파라미터를 직접 바꿔가며 결과 차이를 비교하는 탐구용 모드입니다.",
            "badges": [
                {"label": "실험 모드", "tone": "research"},
                {"label": "단순화 물리", "tone": "model"},
                {"label": "가설 비교", "tone": "hybrid"},
            ],
            "notes": [
                "결과는 탐구용 비교 자료로 쓰기에 적합하지만, 보정된 현장 모형으로 간주하면 안 됩니다.",
                "실제 연구 해석에는 관측 자료, 단위 검토, 비교 지표가 추가로 필요합니다.",
            ],
        }

    if theory_applied:
        context["badges"] = list(context["badges"]) + [
            {"label": "텍스트 가설 적용", "tone": "warning"}
        ]
        context["notes"] = list(context["notes"]) + [
            "이론 문장 해석은 키워드 기반 가설 추천이므로 자동 역추정 결과로 해석하면 안 됩니다."
        ]

    return context


def get_research_context(params: dict[str, object]) -> dict[str, object]:
    source = params.get("source")

    if source == "upload":
        return {
            "title": "연구 모드: 관측 DEM 분석",
            "summary": "현재 화면은 업로드한 DEM을 직접 분석합니다. 형상 자체는 관측값이며, 해석은 분석 기준과 비교 자료에 따라 달라집니다.",
            "badges": [
                {"label": "연구 모드", "tone": "research"},
                {"label": "관측 DEM", "tone": "observed"},
                {"label": "비교 가능", "tone": "research"},
            ],
            "notes": [
                "셀 크기와 좌표계가 다른 자료를 비교할 때는 해상도 차이를 먼저 확인하세요.",
                "단일 지표 하나만으로 지형사를 단정하지 말고 단면, 경사, 곡률을 함께 보세요.",
            ],
        }

    if source == "case_mode":
        return {
            "title": "연구 모드: 정책 비교용 시뮬레이션 DEM",
            "summary": "현재 데이터는 사례 수업과 정책 비교를 위해 생성된 시뮬레이션 결과입니다. 정량 비교 연습에는 좋지만 관측 지형의 대체물은 아닙니다.",
            "badges": [
                {"label": "연구 모드", "tone": "research"},
                {"label": "정책 실험", "tone": "hybrid"},
                {"label": "검증 필요", "tone": "warning"},
            ],
            "notes": [
                "A/B 비교는 경향 판단에 유용하지만 실제 의사결정에는 최신 현장 자료가 추가되어야 합니다.",
                "실사례 카드의 수치와 규정은 수업 전에 다시 확인하는 것이 안전합니다.",
            ],
        }

    if source == "simulation":
        return {
            "title": "연구 모드: 이상화 DEM 분석",
            "summary": "현재 데이터는 교과서형 지형을 기하학적으로 만든 synthetic DEM입니다. 분석 절차 연습과 지표 비교에는 적합하지만 현장 지형의 직접 재현은 아닙니다.",
            "badges": [
                {"label": "연구 모드", "tone": "research"},
                {"label": "이상화 DEM", "tone": "model"},
                {"label": "검증 필요", "tone": "warning"},
            ],
            "notes": [
                "이상화 DEM은 분석 방법 연습에는 좋지만, 오차 검증 없이 실재 지형사로 일반화하면 안 됩니다.",
                "관측 DEM과 RMSE, 단면 차이, HI를 함께 비교하면 연구 보조 가치가 높아집니다.",
            ],
        }

    return {
        "title": "연구 모드: 자료 상태 확인 필요",
        "summary": "현재 데이터의 출처 정보가 충분하지 않습니다. 분석 전에 자료 원천과 생성 방식을 먼저 확인하세요.",
        "badges": [
            {"label": "연구 모드", "tone": "research"},
            {"label": "출처 확인 필요", "tone": "warning"},
        ],
        "notes": [
            "자료 출처와 단위를 확인한 뒤 비교 지표를 읽는 편이 안전합니다.",
        ],
    }


def describe_learning_stage(progress: float) -> dict[str, str]:
    progress = max(0.0, min(1.0, float(progress)))

    if progress < 0.25:
        return {
            "title": "1단계: 초기 조건",
            "summary": "지형의 시작 형태가 정해지고, 어느 곳이 먼저 깎이고 쌓일지 기본 방향이 잡히는 구간입니다.",
            "caption": "처음에는 큰 지형 골격이 유지되지만, 급경사와 낮은 지대 경계부터 작은 변화가 먼저 시작됩니다.",
            "focus": "급경사 상류와 저지대가 맞닿는 경계를 먼저 살펴보세요.",
            "question": "어느 위치가 가장 먼저 변하기 시작하는지 찾아보세요.",
        }
    if progress < 0.5:
        return {
            "title": "2단계: 변화 시작",
            "summary": "침식과 퇴적, 또는 융기의 차이가 눈에 띄기 시작하며 지형의 윤곽이 드러나는 구간입니다.",
            "caption": "깎이는 곳과 쌓이는 곳이 분리되면서 계곡, 선상지, 해안선 같은 윤곽이 눈에 띄기 시작합니다.",
            "focus": "처음 장면과 비교해 가장 빠르게 연결되는 침식 경로나 퇴적 띠를 찾아보세요.",
            "question": "초기 장면과 비교했을 때 가장 빠르게 변한 부분은 어디인가요?",
        }
    if progress < 0.75:
        return {
            "title": "3단계: 형태 강화",
            "summary": "골짜기, 사면, 퇴적 지형처럼 교과서에서 보는 핵심 형태가 뚜렷해지는 구간입니다.",
            "caption": "반복된 작용이 누적되면서 지형의 대표 형태가 강화되고, 변화 방향이 한눈에 읽히기 시작합니다.",
            "focus": "사면 경사, 골짜기 깊이, 퇴적 지형의 폭처럼 커지는 특징을 비교해보세요.",
            "question": "이 장면에서 가장 대표적인 지형 특징 한 가지를 말로 설명해보세요.",
        }
    return {
        "title": "4단계: 결과 해석",
        "summary": "변화가 누적되어 최종 지형이 거의 완성되고, 어떤 과정이 우세했는지 해석할 수 있는 구간입니다.",
        "caption": "최종 형태가 거의 완성되어, 어떤 작용이 지형을 지배했는지 근거를 들어 설명할 수 있는 단계입니다.",
        "focus": "처음 장면과 마지막 장면을 비교하며 무엇이 줄고 늘었는지 정리해보세요.",
        "question": "최종 지형을 만든 핵심 과정이 침식, 퇴적, 융기 중 무엇인지 근거와 함께 말해보세요.",
    }
