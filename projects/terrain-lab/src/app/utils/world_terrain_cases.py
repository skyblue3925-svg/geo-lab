from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class WorldTerrainCase:
    case_id: str
    title: str
    region_label: str
    location_label: str
    latitude: float
    longitude: float
    category: str
    landform_key: str
    classroom_hook: str
    process_focus: tuple[str, ...]
    student_question: str
    teacher_note: str
    recommended_view: str
    overlay_priority: tuple[str, ...]
    higher_ed_focus: str


_WORLD_TERRAIN_CASES: tuple[WorldTerrainCase, ...] = (
    WorldTerrainCase(
        case_id="death_valley_alluvial_fan",
        title="데스밸리 선상지",
        region_label="북아메리카",
        location_label="미국 캘리포니아 데스밸리",
        latitude=36.24,
        longitude=-116.82,
        category="하천",
        landform_key="alluvial_fan",
        classroom_hook="산지 출구에서 급격히 감속한 퇴적물이 왜 부채꼴로 퍼지는지 연결하기 좋은 사례입니다.",
        process_focus=("공급", "이동", "감속 퇴적"),
        student_question="왜 좁은 골짜기를 빠져나온 뒤에만 퇴적이 넓게 퍼질까요?",
        teacher_note="선상지는 산지 출구, 유로 분산, 입자 분급을 함께 설명할 때 가장 교육 효과가 큽니다.",
        recommended_view="정면 (Y-)",
        overlay_priority=("transport", "deposition", "change"),
        higher_ed_focus="건조 기후 선상지에서 debris flow와 sheetflood 해석을 비교하는 확장 수업에 적합합니다.",
    ),
    WorldTerrainCase(
        case_id="alpine_v_valley",
        title="알프스 상류 V자곡",
        region_label="유럽",
        location_label="스위스 알프스",
        latitude=46.57,
        longitude=8.43,
        category="하천",
        landform_key="v_valley",
        classroom_hook="융기 이후 하천의 하방 침식과 사면 조정이 왜 V자 단면을 만드는지 보여주는 사례입니다.",
        process_focus=("융기", "하방 침식", "사면 이동"),
        student_question="왜 계곡은 처음부터 넓어지기보다 깊어지는 변화가 먼저 보일까요?",
        teacher_note="V자곡은 하천 침식만이 아니라 사면 붕괴와 headward erosion까지 같이 봐야 설명이 완성됩니다.",
        recommended_view="상류/하류 뷰",
        overlay_priority=("tectonic", "erosion", "change"),
        higher_ed_focus="relief growth와 stream power 개념을 함께 다루는 상류 지형 해석으로 확장하기 좋습니다.",
    ),
    WorldTerrainCase(
        case_id="mississippi_meander_plain",
        title="미시시피 곡류 평야",
        region_label="북아메리카",
        location_label="미국 중남부 미시시피 평야",
        latitude=33.10,
        longitude=-91.10,
        category="하천",
        landform_key="free_meander",
        classroom_hook="같은 하천 안에서 바깥쪽 침식과 안쪽 퇴적이 동시에 진행된다는 점을 설명하기 좋습니다.",
        process_focus=("측방 침식", "포인트바 퇴적", "수로 이동"),
        student_question="왜 같은 강인데 바깥쪽은 깎이고 안쪽은 쌓일까요?",
        teacher_note="곡류는 helicoidal flow를 간단히 보조 설명으로 붙이면 학생 오해를 줄이기 쉽습니다.",
        recommended_view="상류/하류 뷰",
        overlay_priority=("transport", "erosion", "deposition"),
        higher_ed_focus="cutoff, oxbow lake, floodplain migration까지 연결하는 수업으로 확장할 수 있습니다.",
    ),
    WorldTerrainCase(
        case_id="nile_delta",
        title="나일 삼각주",
        region_label="아프리카",
        location_label="이집트 북부 지중해 연안",
        latitude=31.20,
        longitude=31.10,
        category="삼각주",
        landform_key="delta",
        classroom_hook="하구에서 유속이 줄고 전면 퇴적이 전진하는 삼각주의 기본 구조를 설명하기 좋습니다.",
        process_focus=("이동", "하구 감속", "전면 퇴적"),
        student_question="왜 강은 바다를 만나자마자 갑자기 넓어지는 모양을 만들까요?",
        teacher_note="삼각주는 하천만의 결과가 아니라 침강, 파랑, 조석과의 균형으로 읽어야 합니다.",
        recommended_view="기본 사각 뷰",
        overlay_priority=("transport", "deposition", "change"),
        higher_ed_focus="하구 accommodation과 인위적 개입 이후 삼각주 변화 비교로 확장 가능합니다.",
    ),
    WorldTerrainCase(
        case_id="norway_fjord",
        title="노르웨이 피오르",
        region_label="유럽",
        location_label="노르웨이 서해안",
        latitude=61.10,
        longitude=6.80,
        category="빙하",
        landform_key="fjord",
        classroom_hook="빙하가 깊게 깎은 U자곡에 해수가 들어오며 긴 만이 되는 과정을 보여줍니다.",
        process_focus=("빙하 침식", "U자 단면", "해수 침수"),
        student_question="피오르는 처음부터 바다가 파고든 만일까요, 빙하곡의 연장일까요?",
        teacher_note="V자곡과 U자곡 단면 차이를 먼저 보여준 뒤 피오르를 연결하면 이해가 훨씬 빨라집니다.",
        recommended_view="기본 사각 뷰",
        overlay_priority=("erosion", "change", "tectonic"),
        higher_ed_focus="hanging valley와 빙하 퇴적의 분급 불량까지 연결하는 심화 설명에 적합합니다.",
    ),
    WorldTerrainCase(
        case_id="hawaii_shield_volcano",
        title="하와이 순상화산",
        region_label="오세아니아",
        location_label="미국 하와이 빅아일랜드",
        latitude=19.47,
        longitude=-155.59,
        category="화산",
        landform_key="shield_volcano",
        classroom_hook="점성이 낮은 용암이 넓고 완만한 화산체를 반복적으로 쌓는 모습을 연결하기 좋습니다.",
        process_focus=("분출", "용암 확산", "화산체 성장"),
        student_question="왜 어떤 화산은 뾰족한 성층화산보다 넓고 완만한 모양이 될까요?",
        teacher_note="순상화산은 분화 형태와 용암 점성이 지형 모양을 바꾼다는 점을 강조하기 좋습니다.",
        recommended_view="대각선 낮은 뷰",
        overlay_priority=("tectonic", "change", "transport"),
        higher_ed_focus="hotspot track과 점성 차이에 따른 화산체 대비로 확장하기 좋습니다.",
    ),
    WorldTerrainCase(
        case_id="guilin_tower_karst",
        title="구이린 탑 카르스트",
        region_label="동아시아",
        location_label="중국 광시 구이린",
        latitude=25.28,
        longitude=110.29,
        category="카르스트",
        landform_key="tower_karst",
        classroom_hook="용식이 누적된 뒤 남은 잔구가 탑 모양으로 드러나는 카르스트 경관입니다.",
        process_focus=("용식", "지하 배수", "잔구 형성"),
        student_question="왜 카르스트에서는 가장 높게 남은 탑보다 주변이 먼저 낮아졌다고 볼까요?",
        teacher_note="카르스트는 표면 요철뿐 아니라 지하 배수, terra rossa, 재침전까지 함께 설명해야 교육적으로 탄탄합니다.",
        recommended_view="기본 사각 뷰",
        overlay_priority=("erosion", "transport", "change"),
        higher_ed_focus="doline-uvala-polje 연속성과 tower karst의 기후 조건 비교 수업에 적합합니다.",
    ),
    WorldTerrainCase(
        case_id="pacific_coastal_cliff",
        title="태평양 해식애",
        region_label="환태평양",
        location_label="칠레·캘리포니아형 융기 해안",
        latitude=-33.45,
        longitude=-71.68,
        category="해안",
        landform_key="coastal_cliff",
        classroom_hook="파랑 침식과 지반 융기가 겹치면 왜 해식애와 해안단구가 함께 나타나는지 보여줍니다.",
        process_focus=("파랑 침식", "절벽 후퇴", "단구 형성"),
        student_question="왜 해식애는 앞으로 자라기보다 뒤로 물러나는 모양으로 보일까요?",
        teacher_note="notch와 wave-cut platform을 먼저 보여주고, 그다음 융기와 해수면 변화를 연결하면 이해가 좋아집니다.",
        recommended_view="정면 (Y-)",
        overlay_priority=("erosion", "tectonic", "change"),
        higher_ed_focus="연안 표사 이동과 uplifted marine terrace를 함께 비교하는 대학 수업으로 확장하기 좋습니다.",
    ),
)


def _serialize(case: WorldTerrainCase) -> dict[str, object]:
    return asdict(case)


def _get_attr_or_key(item: object, name: str) -> object | None:
    if isinstance(item, dict):
        return item.get(name)
    return getattr(item, name, None)


def get_all_world_cases() -> list[dict[str, object]]:
    return [_serialize(case) for case in _WORLD_TERRAIN_CASES]


def get_featured_world_cases(limit: int | None = None) -> list[dict[str, object]]:
    cases = [_serialize(case) for case in _WORLD_TERRAIN_CASES]
    if limit is None:
        return cases
    return cases[:limit]


def get_world_cases_for_category(category: str) -> list[dict[str, object]]:
    return [_serialize(case) for case in _WORLD_TERRAIN_CASES if case.category == category]


def get_featured_world_case(landform_key: str) -> dict[str, object] | None:
    for case in _WORLD_TERRAIN_CASES:
        if case.landform_key == landform_key:
            return _serialize(case)
    return None


def get_world_case(case_id: str) -> dict[str, object] | None:
    for case in _WORLD_TERRAIN_CASES:
        if case.case_id == case_id:
            return _serialize(case)
    return None


def extract_selected_world_case_id(event_data: object) -> str | None:
    if event_data is None:
        return None

    selection = _get_attr_or_key(event_data, "selection")
    container = selection if selection is not None else event_data
    points = _get_attr_or_key(container, "points")
    if not points:
        return None

    point = points[0]
    customdata = _get_attr_or_key(point, "customdata")
    if customdata is None:
        return None
    if isinstance(customdata, (list, tuple)):
        if not customdata:
            return None
        customdata = customdata[0]
    return str(customdata)
