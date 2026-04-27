from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable

import numpy as np


RIVER = "하천"
DELTA = "하구·삼각주"
GLACIAL = "빙하"
VOLCANIC = "화산"
KARST = "카르스트"
ARID = "건조"
COASTAL = "해안"


CAMERA_LABELS = {
    "planform_front": "정면 평면도",
    "planform_oblique": "사선 평면도",
    "valley_profile": "계곡 단면 사선뷰",
    "basin_overlook": "함몰 지형 상공뷰",
    "relief_oblique": "입체 지형 사선뷰",
    "coastal_front": "해안 정면뷰",
}


@dataclass(frozen=True)
class TeachingStage:
    stage_id: str
    title: str
    dominant_process: str
    overlay: str
    student_copy: str
    teacher_copy: str
    question: str


@dataclass(frozen=True)
class WorldCase:
    case_id: str
    title: str
    location_label: str
    latitude: float
    longitude: float
    recommended_view: str
    student_question: str
    teacher_note: str


@dataclass(frozen=True)
class TopicSpec:
    topic_id: str
    group_id: str
    title: str
    category: str
    landform_key: str
    landform_type: str
    primary_overlay: str
    overlay_caption: str
    classroom_goal: str
    observation_focus: str
    compare_hint: str
    curriculum_unit: str
    preview_stage: float
    camera_profile: str
    world_case: WorldCase
    stages: tuple[TeachingStage, ...]


GROUPS: tuple[dict[str, str], ...] = (
    {
        "group_id": "river",
        "badge": "하천",
        "title": "하천 침식과 퇴적 지형",
        "curriculum_unit": "하천의 침식·운반·퇴적 작용",
        "summary": "상류의 하방 침식부터 중·하류의 퇴적 지형까지, 물의 에너지 변화가 지형을 어떻게 바꾸는지 본다.",
        "default_topic_id": "v_valley",
    },
    {
        "group_id": "delta",
        "badge": "하구",
        "title": "하구·삼각주와 연안 퇴적",
        "curriculum_unit": "하구에서의 퇴적과 해안 상호작용",
        "summary": "강이 바다를 만나며 감속할 때 생기는 하구, 삼각주, 분류 하천의 차이를 비교한다.",
        "default_topic_id": "delta",
    },
    {
        "group_id": "glacial",
        "badge": "빙하",
        "title": "빙하와 고산 지형",
        "curriculum_unit": "빙하 침식과 고산 지형 형성",
        "summary": "하천 계곡과 빙하 계곡을 비교하며, 빙하가 넓고 둥근 계곡을 만드는 이유를 본다.",
        "default_topic_id": "u_valley",
    },
    {
        "group_id": "volcanic",
        "badge": "화산",
        "title": "화산과 분출 지형",
        "curriculum_unit": "화산 활동과 화산 지형",
        "summary": "분출 양상과 마그마 성질 차이가 화산체의 모양을 어떻게 바꾸는지 살핀다.",
        "default_topic_id": "shield_volcano",
    },
    {
        "group_id": "karst",
        "badge": "카르스트",
        "title": "용식 지형과 지하 배수",
        "curriculum_unit": "석회암 지형과 용식 작용",
        "summary": "지표를 깎는 것만이 아니라, 지하로 스며드는 물이 지형을 바꾸는 방식에 집중한다.",
        "default_topic_id": "karst_doline",
    },
    {
        "group_id": "arid",
        "badge": "건조",
        "title": "건조 지역 지형",
        "curriculum_unit": "풍식·풍적 작용과 건조 지형",
        "summary": "바람, 간헐 하천, 증발이 만든 건조 지형을 비교하며 과정 차이를 읽는다.",
        "default_topic_id": "barchan",
    },
    {
        "group_id": "coastal",
        "badge": "해안",
        "title": "해안 침식과 해안 퇴적",
        "curriculum_unit": "파랑·연안류와 해안 지형",
        "summary": "파랑이 깎는 해안과 연안류가 쌓는 해안을 나누어 보고, 해안선이 바뀌는 원리를 이해한다.",
        "default_topic_id": "coastal_cliff",
    },
)


def _stage(
    stage_id: str,
    title: str,
    dominant_process: str,
    overlay: str,
    student_copy: str,
    teacher_copy: str,
    question: str,
) -> TeachingStage:
    return TeachingStage(
        stage_id=stage_id,
        title=title,
        dominant_process=dominant_process,
        overlay=overlay,
        student_copy=student_copy,
        teacher_copy=teacher_copy,
        question=question,
    )


def _stages(*items: TeachingStage) -> tuple[TeachingStage, ...]:
    return items


def _group(group_id: str) -> dict[str, str]:
    return next(group for group in GROUPS if group["group_id"] == group_id)


def _case(
    case_id: str,
    title: str,
    location_label: str,
    latitude: float,
    longitude: float,
    camera_profile: str,
    student_question: str,
    teacher_note: str,
) -> WorldCase:
    return WorldCase(
        case_id=case_id,
        title=title,
        location_label=location_label,
        latitude=latitude,
        longitude=longitude,
        recommended_view=CAMERA_LABELS[camera_profile],
        student_question=student_question,
        teacher_note=teacher_note,
    )


def _topic(
    topic_id: str,
    group_id: str,
    title: str,
    category: str,
    landform_key: str,
    landform_type: str,
    primary_overlay: str,
    overlay_caption: str,
    classroom_goal: str,
    observation_focus: str,
    compare_hint: str,
    camera_profile: str,
    world_case: WorldCase,
    stages: tuple[TeachingStage, ...],
    preview_stage: float = 0.92,
) -> TopicSpec:
    return TopicSpec(
        topic_id=topic_id,
        group_id=group_id,
        title=title,
        category=category,
        landform_key=landform_key,
        landform_type=landform_type,
        primary_overlay=primary_overlay,
        overlay_caption=overlay_caption,
        classroom_goal=classroom_goal,
        observation_focus=observation_focus,
        compare_hint=compare_hint,
        curriculum_unit=_group(group_id)["curriculum_unit"],
        preview_stage=preview_stage,
        camera_profile=camera_profile,
        world_case=world_case,
        stages=stages,
    )


V_VALLEY_STAGES = _stages(
    _stage("s1", "융기와 경사 형성", "융기", "tectonic", "높이 차가 커지며 물이 흐를 길이 정해집니다.", "학생이 물의 시작 방향부터 읽게 하는 단계입니다.", "물이 처음 집중되는 곳은 어디일까요?"),
    _stage("s2", "하방 침식", "하천 침식", "erosion", "하천이 골짜기 바닥을 먼저 깊게 깎습니다.", "양옆보다 바닥이 먼저 깊어지는 점을 짚어 주세요.", "왜 바닥의 깊이가 먼저 커질까요?"),
    _stage("s3", "사면 조정", "사면 이동", "change", "골짜기 양옆 사면이 무너지며 V자 모양이 더 분명해집니다.", "하천만이 아니라 사면 반응도 계곡 모양을 만든다고 설명하세요.", "계곡 옆면은 왜 함께 변할까요?"),
    _stage("s4", "V자곡 완성", "침식 우세", "change", "깊고 좁은 V자 단면이 분명해집니다.", "최종 모습보다 반복된 침식의 결과라는 점을 강조하세요.", "이 모양은 어떤 작용의 누적 결과일까요?"),
)

WATERFALL_STAGES = _stages(
    _stage("s1", "경사 차 준비", "지층 차이", "tectonic", "강이 흐르는 길에 단단함이 다른 지층이 놓입니다.", "폭포는 단순 낙차가 아니라 지층 차이와 침식 차이에서 시작합니다.", "같은 강인데 왜 경사가 갑자기 커질까요?"),
    _stage("s2", "폭포 형성", "차별 침식", "erosion", "약한 층이 먼저 깎이며 낙차가 만들어집니다.", "단단한 층과 약한 층의 침식 속도 차이를 보여 주세요.", "어느 층이 더 빨리 깎일까요?"),
    _stage("s3", "낙하부 후퇴", "두부 침식", "erosion", "폭포는 상류 쪽으로 조금씩 물러납니다.", "폭포가 제자리에서만 깎이는 것이 아니라 뒤로 물러난다고 설명하세요.", "폭포 위치는 시간이 지나도 그대로일까요?"),
    _stage("s4", "협곡 확대", "후퇴와 재정비", "change", "폭포 아래의 깊은 소와 좁은 협곡이 함께 발달합니다.", "폭포와 협곡을 하나의 과정으로 묶어 설명하는 단계입니다.", "폭포 아래쪽에는 왜 깊은 소가 생길까요?"),
)

ALLUVIAL_FAN_STAGES = _stages(
    _stage("s1", "산지 공급", "풍화·사면 이동", "change", "산지에서 자갈과 모래가 계속 공급됩니다.", "선상지는 먼저 공급원이 있는 퇴적 지형이라고 짚어 주세요.", "퇴적될 물질은 어디에서 올까요?"),
    _stage("s2", "협곡 운반", "하천 운반", "transport", "좁은 골짜기에서는 물질이 빠르게 운반됩니다.", "좁은 구간에서는 아직 부채꼴 모양이 잘 보이지 않는다고 설명하세요.", "좁은 골짜기에서는 왜 계속 실려 갈까요?"),
    _stage("s3", "산지 출구 감속", "유속 저하", "deposition", "산지 출구에서 갑자기 속도가 줄며 퇴적이 시작됩니다.", "선상지 설명의 핵심 시작점은 산지 출구입니다.", "왜 산지 출구에서 갑자기 쌓이기 시작할까요?"),
    _stage("s4", "부채꼴 확산", "전면 퇴적", "change", "퇴적이 앞쪽으로 퍼지며 부채꼴 모양이 뚜렷해집니다.", "깎인 지형이 아니라 쌓인 지형임을 강조하세요.", "왜 퇴적이 한 줄이 아니라 부채꼴로 퍼질까요?"),
)

BRAIDED_RIVER_STAGES = _stages(
    _stage("s1", "퇴적물 과잉 공급", "운반물 증가", "transport", "하천이 실어 나르는 자갈과 모래가 매우 많아집니다.", "유량만이 아니라 운반물의 양도 중요하다고 설명하세요.", "강이 너무 많은 자갈을 실으면 어떤 일이 생길까요?"),
    _stage("s2", "하중 조절", "하도 분기", "transport", "한 줄의 수로로 감당하지 못해 여러 갈래로 나뉩니다.", "망상하천은 여러 갈래의 불안정한 하도라는 점을 짚어 주세요.", "왜 물길이 한 줄로 유지되지 않을까요?"),
    _stage("s3", "중간 사주 형성", "중앙 퇴적", "deposition", "가운데에 사주가 생기며 흐름이 다시 나뉩니다.", "사주와 하도 분기를 함께 보여 주세요.", "강 한가운데 퇴적이 생기면 물길은 어떻게 달라질까요?"),
    _stage("s4", "망상 구조 반복", "분기·합류 반복", "change", "갈라졌다 합쳐지는 망상 구조가 반복됩니다.", "곡류하천과 달리 하도가 자주 갈라지는 점을 비교하세요.", "망상하천은 왜 계속 형태가 바뀔까요?"),
)

MEANDER_STAGES = _stages(
    _stage("s1", "완만한 굽이 시작", "유로 곡률 증가", "change", "완만한 굽이가 생기며 흐름이 비대칭이 되기 시작합니다.", "직선 수로가 작은 굽이에서 출발한다는 점을 먼저 보여 주세요.", "직선 하천에도 작은 굽이가 생길 수 있을까요?"),
    _stage("s2", "바깥쪽 침식", "측방 침식", "erosion", "굽이의 바깥쪽에서 침식이 강해집니다.", "바깥쪽이 깊고 빠르다는 설명을 연결하세요.", "왜 굽이 바깥쪽이 더 빨리 깎일까요?"),
    _stage("s3", "안쪽 퇴적", "내측 퇴적", "deposition", "안쪽에는 모래와 자갈이 쌓이며 완만한 사면이 생깁니다.", "침식과 퇴적이 같은 수로 안에서 동시에 일어난다고 설명하세요.", "같은 강 안에서 왜 한쪽은 쌓이고 한쪽은 깎일까요?"),
    _stage("s4", "사행 확대", "하도 이동", "change", "굽이가 커지며 하천이 옆으로 이동합니다.", "최종 모양보다 하도의 측방 이동을 강조하세요.", "하천 중심선은 시간이 지나면 어디로 움직일까요?"),
)

DELTA_STAGES = _stages(
    _stage("s1", "하구 공간 형성", "하구 감속", "transport", "강이 바다를 만나며 흐름이 느려질 준비를 합니다.", "강과 바다의 경계가 삼각주 형성의 출발점임을 짚어 주세요.", "강이 바다를 만나면 무엇이 먼저 달라질까요?"),
    _stage("s2", "전면 퇴적 시작", "퇴적 시작", "deposition", "하구 앞쪽에서 운반력이 줄어 퇴적이 시작됩니다.", "삼각주 전면부를 먼저 보게 하는 단계입니다.", "왜 하구 바로 앞에서 퇴적이 시작될까요?"),
    _stage("s3", "수로 분기", "수로 분기", "transport", "쌓인 퇴적물 때문에 물길이 여러 갈래로 갈라집니다.", "분류 하천은 퇴적의 결과라는 점을 설명하세요.", "물길이 여러 갈래로 나뉘는 이유는 무엇일까요?"),
    _stage("s4", "삼각주 성장", "전진성 퇴적", "change", "퇴적 전면이 바다 쪽으로 전진하며 삼각주가 성장합니다.", "바다 쪽으로 뻗어 나가는 모습을 지도와 함께 연결하세요.", "삼각주는 왜 바다 쪽으로 커질까요?"),
)

ESTUARY_STAGES = _stages(
    _stage("s1", "하구 침수", "해수면 상승", "change", "강 하구가 바닷물에 잠기며 넓은 만입이 형성됩니다.", "에스추어리는 삼각주와 달리 침수가 핵심입니다.", "하구가 넓게 열리는 까닭은 무엇일까요?"),
    _stage("s2", "조석 혼합", "조석 작용", "transport", "바닷물과 강물이 섞이며 하구 전체의 흐름이 복잡해집니다.", "조석이 수로 모양을 계속 흔든다는 점을 강조하세요.", "왜 하구 안에서 물의 방향이 자주 바뀔까요?"),
    _stage("s3", "퇴적 억제", "재운반", "transport", "퇴적이 생겨도 조석과 해류가 다시 옮겨 버립니다.", "삼각주처럼 앞으로 자라지 않는 이유를 설명하는 단계입니다.", "왜 삼각주처럼 앞으로 자라지 않을까요?"),
    _stage("s4", "깔때기형 하구", "혼합 하구", "change", "넓게 열리는 깔때기형 하구가 안정적으로 나타납니다.", "하천 퇴적보다 조석 혼합이 강한 하구라는 점을 정리하세요.", "에스추어리의 대표적 모양은 어떤 모습일까요?"),
)

GLACIAL_VALLEY_STAGES = _stages(
    _stage("s1", "고산 환경 형성", "설선 형성", "tectonic", "높고 추운 환경에서 눈과 얼음이 오래 남습니다.", "빙하 지형은 먼저 높은 곳과 낮은 기온이 필요하다고 짚어 주세요.", "빙하는 어떤 조건에서 시작될까요?"),
    _stage("s2", "빙하 자리잡기", "빙하 이동", "transport", "얼음 덩어리가 계곡을 따라 천천히 이동합니다.", "빙하는 움직이는 얼음이라는 점을 먼저 확인하세요.", "얼음도 실제로 흐를 수 있을까요?"),
    _stage("s3", "바닥·측벽 동시 침식", "빙하 침식", "erosion", "계곡 바닥과 양쪽 벽이 함께 깎입니다.", "하천 계곡보다 넓고 둥근 이유를 이 단계에서 설명하세요.", "왜 계곡 바닥만이 아니라 양옆도 깎일까요?"),
    _stage("s4", "U자곡 완성", "침식·퇴적 흔적", "change", "넓고 둥근 U자 단면과 빙퇴적 흔적이 남습니다.", "하천의 V자곡과 단면을 꼭 비교해 주세요.", "하천 계곡과 무엇이 가장 다를까요?"),
)

CIRQUE_STAGES = _stages(
    _stage("s1", "눈웅덩이 형성", "적설 축적", "tectonic", "산 정상 부근 움푹한 곳에 눈이 쌓입니다.", "권곡은 빙하의 출발점이라는 점을 먼저 보여 주세요.", "왜 산꼭대기 가까운 곳에 눈이 오래 남을까요?"),
    _stage("s2", "소빙하 발달", "빙하 이동", "transport", "쌓인 눈이 얼음으로 바뀌어 작은 빙하가 됩니다.", "권곡은 U자곡보다 상류 쪽의 초기 지형임을 설명하세요.", "권곡은 어디에서 발달하기 시작할까요?"),
    _stage("s3", "반원형 침식", "권곡 침식", "erosion", "벽과 바닥이 함께 깎이며 반원형 움푹한 지형이 커집니다.", "권곡 바닥과 급사면을 같이 보게 하세요.", "왜 권곡은 그릇처럼 움푹할까요?"),
    _stage("s4", "권곡 완성", "빙하 기원 분지", "change", "그릇 모양 분지와 가파른 벽이 분명해집니다.", "빙하의 상류 기원 지형이라는 점을 정리하세요.", "권곡은 U자곡의 어느 부분과 연결될까요?"),
)

HORN_STAGES = _stages(
    _stage("s1", "여러 권곡 발달", "다방향 빙하 침식", "erosion", "여러 방향의 권곡이 산꼭대기를 둘러싸기 시작합니다.", "호른은 한 방향이 아니라 여러 방향 침식의 결과라고 설명하세요.", "여러 방향에서 깎이면 산 정상은 어떻게 될까요?"),
    _stage("s2", "능선 첨예화", "측면 침식", "change", "권곡 사이 능선이 점점 더 날카로워집니다.", "아레트와 함께 비교하면 이해가 빠릅니다.", "권곡 사이 능선은 왜 날카로워질까요?"),
    _stage("s3", "정상 집중 침식", "집중 침식", "erosion", "정상 주변이 여러 방향에서 깎여 뾰족해집니다.", "피라미드형 정상의 원인을 과정으로 설명하세요.", "정상이 피라미드처럼 되는 까닭은 무엇일까요?"),
    _stage("s4", "호른 완성", "빙하 조각", "change", "뾰족한 피라미드형 봉우리가 남습니다.", "최종 지형을 여러 권곡의 교차 결과로 정리하세요.", "호른은 어떤 지형들이 만나서 만들어졌을까요?"),
)

FJORD_STAGES = _stages(
    _stage("s1", "빙하곡 형성", "빙하 침식", "erosion", "먼저 깊고 넓은 U자 빙하곡이 만들어집니다.", "피오르는 바다 지형이 아니라 빙하곡에서 시작한다고 설명하세요.", "피오르는 무엇이 먼저 만들어 놓은 계곡일까요?"),
    _stage("s2", "깊은 골 확대", "심곡 침식", "erosion", "빙하가 계곡을 매우 깊게 깎아 놓습니다.", "길고 깊은 만입의 바탕이 되는 단계입니다.", "왜 일반 하천곡보다 훨씬 깊게 파일까요?"),
    _stage("s3", "해수 침입", "해수면 변화", "change", "빙하가 물러난 뒤 바닷물이 계곡 안으로 들어옵니다.", "해수면 상승 또는 지반 침수를 함께 연결해 주세요.", "바닷물은 왜 그 계곡 안까지 들어올까요?"),
    _stage("s4", "피오르 완성", "침수된 빙하곡", "change", "깊고 좁으며 측벽이 급한 만입 해안이 완성됩니다.", "U자곡과 연결해서 설명하면 이해가 쉽습니다.", "피오르는 어떤 육상 지형이 바다와 연결된 것일까요?"),
)

SHIELD_VOLCANO_STAGES = _stages(
    _stage("s1", "마그마 공급", "용암 공급", "tectonic", "유동성이 큰 현무암질 마그마가 올라옵니다.", "순상화산의 출발점은 묽은 용암 공급입니다.", "왜 어떤 화산은 용암이 멀리 퍼질까요?"),
    _stage("s2", "완만한 분출", "유동성 큰 용암", "tectonic", "묽은 용암이 넓게 퍼지며 흘러내립니다.", "점성이 낮아 멀리 흐른다는 점을 강조하세요.", "용암이 묽으면 화산체 모양은 어떻게 될까요?"),
    _stage("s3", "넓은 확산", "반복 분출", "change", "반복된 분출이 넓고 완만한 사면을 만듭니다.", "높이보다 폭이 커지는 지형이라는 점을 짚어 주세요.", "높은 원뿔보다 넓은 방패 모양이 되는 이유는 무엇일까요?"),
    _stage("s4", "순상화산 완성", "광범위 축적", "change", "경사가 완만한 넓은 화산체가 남습니다.", "성층화산과 반드시 비교해 주세요.", "성층화산과 가장 다른 점은 무엇일까요?"),
)

STRATOVOLCANO_STAGES = _stages(
    _stage("s1", "점성 큰 마그마", "규산질 마그마", "tectonic", "점성이 큰 마그마가 상승합니다.", "순상화산과 달리 점성이 높다는 점부터 시작하세요.", "점성이 큰 마그마는 쉽게 퍼질까요?"),
    _stage("s2", "폭발적 분출", "화산쇄설물 분출", "tectonic", "화산재와 화산암 조각이 함께 분출합니다.", "폭발성 분출이 층을 만든다는 점을 연결하세요.", "왜 화산재가 많이 쌓일까요?"),
    _stage("s3", "층상 축적", "분출물 교호", "change", "용암과 화산쇄설물이 번갈아 쌓입니다.", "성층화산의 이름 그대로 층이 쌓이는 단계입니다.", "화산체 안에는 어떤 층이 쌓일까요?"),
    _stage("s4", "성층화산 완성", "가파른 원뿔형", "change", "높고 가파른 원뿔형 화산이 완성됩니다.", "점성, 분출 양상, 화산체 경사를 함께 정리하세요.", "왜 사면이 순상화산보다 더 가팔라질까요?"),
)

CALDERA_STAGES = _stages(
    _stage("s1", "대규모 마그마 방 형성", "마그마 축적", "tectonic", "큰 마그마 방이 지하에 형성됩니다.", "칼데라는 큰 규모의 마그마 방과 연결된다고 설명하세요.", "지하에 큰 빈 공간이 생기면 어떤 일이 일어날까요?"),
    _stage("s2", "대규모 분출", "폭발적 분출", "tectonic", "많은 분출물과 가스가 한꺼번에 방출됩니다.", "보통 화구보다 훨씬 큰 사건임을 짚어 주세요.", "왜 분출 후 화산 꼭대기가 비게 될까요?"),
    _stage("s3", "정상부 함몰", "함몰", "change", "비어 있는 마그마 방 위가 무너지며 큰 분지가 생깁니다.", "칼데라는 함몰 지형이라는 점을 분명히 하세요.", "칼데라는 왜 폭발구보다 훨씬 넓을까요?"),
    _stage("s4", "칼데라·화구호 발달", "함몰 후 변화", "change", "함몰 분지 안에 호수가 생기거나 재분출 흔적이 남습니다.", "칼데라와 화구호를 연결해서 보여 주세요.", "함몰 뒤에는 어떤 지형이 더 생길 수 있을까요?"),
)

LAVA_PLATEAU_STAGES = _stages(
    _stage("s1", "균열 분출 준비", "광역 마그마 공급", "tectonic", "넓은 균열대를 따라 마그마가 공급됩니다.", "점상 분출이 아니라 넓은 틈 분출이라는 점이 중요합니다.", "왜 하나의 꼭대기 대신 넓은 지역에서 분출할까요?"),
    _stage("s2", "대량 용암 분출", "범람성 분출", "tectonic", "많은 용암이 넓은 지역으로 흘러나옵니다.", "화산체보다 넓은 용암 덮개를 먼저 보게 하세요.", "용암이 넓게 퍼지면 지형은 어떻게 달라질까요?"),
    _stage("s3", "층상 용암 축적", "반복 피복", "change", "용암이 여러 번 덮이며 넓은 평탄면이 만들어집니다.", "계단식 절벽은 이후 침식의 결과라는 점도 연결하세요.", "왜 평탄한 고원이 만들어질까요?"),
    _stage("s4", "용암대지 완성", "광역 용암 피복", "change", "넓고 평탄한 용암대지가 남습니다.", "순상화산·성층화산과 다른 공간 규모를 비교하세요.", "화산인데도 왜 뚜렷한 원뿔이 없을까요?"),
)

KARST_DOLINE_STAGES = _stages(
    _stage("s1", "석회암 용식 시작", "용식", "erosion", "빗물과 지하수가 석회암을 천천히 녹입니다.", "카르스트는 깎는 것보다 녹이는 작용으로 설명하세요.", "물은 암석을 깎기만 할까요, 녹이기도 할까요?"),
    _stage("s2", "지하 배수 발달", "지하수 이동", "transport", "물이 지하로 스며들며 지표 배수가 줄어듭니다.", "지표 하천이 약한 대신 지하 배수가 강한 지형임을 짚어 주세요.", "왜 물이 지표에 오래 머물지 않을까요?"),
    _stage("s3", "함몰 확대", "용식·함몰", "change", "녹아 빈 공간이 커지며 움푹한 분지가 발달합니다.", "돌리네와 우발라를 연결하는 과정 단계입니다.", "왜 특정 지점만 더 깊게 꺼질까요?"),
    _stage("s4", "돌리네·우발라 완성", "함몰 지형", "change", "작은 돌리네에서 더 큰 우발라까지 단계적으로 이어집니다.", "지표와 지하 배수의 연결을 정리하세요.", "작은 함몰 지형이 어떻게 더 큰 함몰로 이어질까요?"),
)

TOWER_KARST_STAGES = _stages(
    _stage("s1", "광범위 용식", "용식", "erosion", "지표와 지하에서 석회암이 차별적으로 녹기 시작합니다.", "모든 곳이 같은 속도로 녹지 않는다는 점이 핵심입니다.", "왜 어떤 곳은 낮아지고 어떤 곳은 남을까요?"),
    _stage("s2", "평탄면 확대", "차별 용식", "change", "주변은 낮아지고 상대적으로 단단한 부분이 남습니다.", "탑 카르스트는 남은 부분을 보는 지형이라고 설명하세요.", "왜 일부 지형만 탑처럼 남을까요?"),
    _stage("s3", "잔구 분리", "잔류 지형 형성", "change", "남은 석회암 덩어리가 주변 평탄면과 분리됩니다.", "돌리네처럼 움푹 파인 지형과 비교해 주세요.", "깎인 지형과 남은 지형 중 무엇을 보고 있나요?"),
    _stage("s4", "탑 카르스트 완성", "잔구 경관", "change", "주변은 낮고 탑 모양의 잔구가 우뚝 남습니다.", "구이린처럼 평야 위 탑상 봉우리를 연결해 설명하세요.", "탑 카르스트는 깎인 결과일까요, 남은 결과일까요?"),
)

DUNE_STAGES = _stages(
    _stage("s1", "모래 공급", "풍적 물질 공급", "transport", "건조한 환경에서 모래가 바람에 실릴 준비를 합니다.", "사구는 먼저 운반될 모래가 있어야 한다는 점을 짚어 주세요.", "사구를 만들 모래는 어디에서 올까요?"),
    _stage("s2", "바람 운반", "풍적 작용", "transport", "바람이 모래를 끌고 가며 낮은 둔덕을 만듭니다.", "운반 방향을 먼저 읽게 하세요.", "바람 방향이 사구 모양에 왜 중요할까요?"),
    _stage("s3", "사면 차별 형성", "사면 이동", "change", "완만한 바람받이사면과 급한 활락사면이 분화됩니다.", "바람받이사면과 활락사면을 꼭 비교하세요.", "왜 한쪽은 완만하고 다른 쪽은 급할까요?"),
    _stage("s4", "사구 유형 완성", "풍적 지형 안정화", "change", "바르한·횡사구·성상사구처럼 바람 조건에 따라 모양이 달라집니다.", "바람 방향의 일정함과 복잡함을 연결해서 정리하세요.", "바람 방향이 달라지면 사구 모양도 달라질까요?"),
)

MESA_STAGES = _stages(
    _stage("s1", "수평 지층 형성", "퇴적 기반", "change", "넓은 퇴적층이 쌓여 평탄한 지층이 만들어집니다.", "메사·뷰트는 먼저 층이 수평으로 놓인 상태에서 시작한다고 설명하세요.", "왜 윗부분이 평평할까요?"),
    _stage("s2", "차별 침식", "건조 지역 침식", "erosion", "약한 층이 먼저 깎이며 절벽이 드러납니다.", "단단한 캡록이 남는 구조를 짚어 주세요.", "모든 층이 같은 속도로 깎일까요?"),
    _stage("s3", "잔류 지형 분리", "후퇴 침식", "change", "절벽이 뒤로 물러나며 남은 부분이 분리됩니다.", "메사에서 뷰트로 줄어드는 과정을 설명할 수 있는 단계입니다.", "왜 큰 평탄지형이 작은 잔구로 나뉠까요?"),
    _stage("s4", "메사·뷰트·기암 발달", "잔류 지형", "change", "평평한 상부와 급한 절벽을 가진 건조 지형이 남습니다.", "남겨진 지형이라는 관점으로 정리하세요.", "이 지형은 쌓인 결과일까요, 남은 결과일까요?"),
)

WADI_STAGES = _stages(
    _stage("s1", "건조 환경 준비", "간헐 하천 조건", "change", "평소에는 마르지만 비가 오면 급류가 흐를 환경이 만들어집니다.", "와디는 상시 하천이 아니라는 점을 먼저 확인하세요.", "왜 평소에는 말라 있을까요?"),
    _stage("s2", "집중호우 흐름", "급류 운반", "transport", "짧은 시간 강한 비가 내리면 급류가 흐릅니다.", "평소 정적인 모습과 폭우 때의 동적 모습을 대비해 주세요.", "비가 오면 와디는 어떻게 달라질까요?"),
    _stage("s3", "침식과 퇴적 반복", "플래시 플러드", "erosion", "급류가 바닥을 깎고 일부 물질을 하류로 옮깁니다.", "간헐적인 사건이 지형을 바꾼다는 점을 강조하세요.", "짧은 홍수도 지형을 바꿀 수 있을까요?"),
    _stage("s4", "건조 협곡 형성", "간헐 하천 지형", "change", "건기에는 마른 수로가 남고 우기에는 다시 흐릅니다.", "건기와 우기의 대비가 핵심입니다.", "물이 없는데도 왜 하천 흔적이 남아 있을까요?"),
)

PLAYA_STAGES = _stages(
    _stage("s1", "폐쇄 분지 형성", "내륙 배수", "change", "물이 바다로 빠져나가지 못하는 분지가 형성됩니다.", "플라야는 바다와 연결되지 않는 분지라는 점이 핵심입니다.", "왜 물이 밖으로 빠져나가지 못할까요?"),
    _stage("s2", "일시적 집수", "일시적 호수", "transport", "비가 오면 낮은 곳에 물이 잠시 고입니다.", "평소 마른 바닥과 비 온 뒤 얕은 호수를 대비해 보게 하세요.", "비가 오면 이 분지에는 어떤 일이 생길까요?"),
    _stage("s3", "증발과 염류 침전", "증발", "deposition", "물이 증발하며 미세한 퇴적물과 염류가 남습니다.", "증발이 지형 형성의 핵심 작용입니다.", "왜 물이 사라진 뒤 하얀 흔적이 남을까요?"),
    _stage("s4", "플라야 완성", "건조 분지 평탄화", "change", "평평하고 단단한 분지 바닥이 남습니다.", "와디와 달리 물이 모이는 낮은 바닥이라는 점을 비교하세요.", "플라야와 와디의 가장 큰 차이는 무엇일까요?"),
)

COASTAL_CLIFF_STAGES = _stages(
    _stage("s1", "파랑 집중", "파랑 침식", "erosion", "파도가 해안 절벽의 아랫부분을 반복해서 깎습니다.", "절벽 밑이 먼저 약해진다는 점이 핵심입니다.", "왜 절벽 아래쪽이 먼저 깎일까요?"),
    _stage("s2", "해식 노치 형성", "해식 노치", "erosion", "아랫부분에 파인 노치가 생깁니다.", "노치를 먼저 보여 주면 절벽 후퇴가 이해됩니다.", "노치가 생기면 위쪽 절벽은 어떻게 될까요?"),
    _stage("s3", "붕괴와 후퇴", "절벽 붕괴", "change", "윗부분이 무너지며 절벽선이 뒤로 물러납니다.", "해식애는 한 번에 생기는 절벽이 아니라 후퇴하는 절벽입니다.", "왜 절벽선이 뒤로 밀릴까요?"),
    _stage("s4", "해식애·파식대 발달", "침식 해안 안정화", "change", "해안 앞에는 파식대가 넓어지고 절벽은 더 뒤로 물러납니다.", "절벽과 파식대를 함께 설명해 주세요.", "해식애 앞의 평평한 면은 무엇일까요?"),
)

SPIT_STAGES = _stages(
    _stage("s1", "연안류 형성", "연안류", "transport", "파도가 비스듬히 들어와 모래를 해안선 따라 옮깁니다.", "사주는 연안류를 설명하기 좋은 지형입니다.", "왜 모래가 해안선을 따라 이동할까요?"),
    _stage("s2", "모래 끝단 성장", "연안 퇴적", "deposition", "해안 끝에서 모래가 길게 뻗어나가기 시작합니다.", "연안류가 약해지는 곳에서 퇴적이 일어난다는 점을 짚어 주세요.", "왜 끝부분이 길게 자라날까요?"),
    _stage("s3", "내측 수역 고립", "사주·석호 형성", "deposition", "사주 안쪽 물이 점점 더 갇혀 석호가 발달합니다.", "사주와 석호를 하나의 세트로 보여 주세요.", "안쪽 물은 왜 외해와 점점 분리될까요?"),
    _stage("s4", "사주·석호 완성", "연안 퇴적 지형", "change", "길게 뻗은 사주와 그 안쪽의 석호가 안정됩니다.", "깎이는 해안과 대비되는 대표적인 쌓이는 해안입니다.", "이 해안은 파도에 깎이는 해안일까요, 쌓이는 해안일까요?"),
)

SEA_ARCH_STAGES = _stages(
    _stage("s1", "약한 층 노출", "해안 차별 침식", "erosion", "절리나 약한 층이 드러난 해안을 파도가 공격합니다.", "모든 바위가 똑같이 깎이지 않는다는 점을 먼저 보여 주세요.", "왜 특정 부분만 더 빨리 깎일까요?"),
    _stage("s2", "해식 동굴 발달", "해식 동굴", "erosion", "약한 부분이 먼저 파이며 해식 동굴이 생깁니다.", "해식아치는 동굴 단계와 연결해 설명하면 이해가 쉽습니다.", "동굴이 더 커지면 어떤 모양이 될까요?"),
    _stage("s3", "양쪽 관통", "아치 형성", "change", "동굴이 관통되어 아치 모양이 됩니다.", "절벽 자체가 남고 약한 부분만 빠진 결과를 보여 주세요.", "아치의 빈 공간은 어떻게 만들어졌을까요?"),
    _stage("s4", "붕괴 준비", "침식 지속", "change", "아치는 계속 약해져 나중에는 기둥만 남을 수 있습니다.", "해식아치가 영구적인 지형이 아니라는 점을 짚어 주세요.", "아치는 시간이 지나면 계속 유지될까요?"),
)

RIA_STAGES = _stages(
    _stage("s1", "하천곡 형성", "하천 침식", "erosion", "육지에는 먼저 V자형 하천곡이 형성됩니다.", "리아스식 해안은 하천곡이 출발점입니다.", "리아스식 해안은 원래 어떤 육상 지형이었을까요?"),
    _stage("s2", "해수면 상승", "침수", "change", "해수면이 상승하거나 육지가 침강하며 하천곡이 잠깁니다.", "해수면 변화와 침강 둘 다 연결해 설명할 수 있습니다.", "왜 골짜기 안으로 바닷물이 들어올까요?"),
    _stage("s3", "만입 해안 발달", "침수 해안", "change", "깊이 들어간 하천곡을 따라 복잡한 만입 해안이 만들어집니다.", "삼각주처럼 쌓이는 해안과 반대 개념으로 설명하세요.", "왜 해안선이 들쭉날쭉 복잡할까요?"),
    _stage("s4", "리아스식 해안 완성", "침수 하천곡 해안", "change", "좁고 긴 만입이 반복되는 침수 해안이 완성됩니다.", "하천곡이 바다에 잠긴 해안이라는 정의로 마무리하세요.", "리아스식 해안은 어떤 지형이 바다에 잠긴 결과일까요?"),
)


TOPIC_SPECS: tuple[TopicSpec, ...] = (
    _topic("v_valley", "river", "V자곡", RIVER, "v_valley", "river", "erosion", "계곡 바닥을 따라 침식이 집중되고 양옆 사면이 뒤따라 반응합니다.", "하천의 하방 침식이 깊고 좁은 V자 단면을 만든다는 점을 이해한다.", "계곡 바닥이 먼저 깊어지고 이후 양옆 사면이 조정되는 순서를 본다.", "U자곡과 단면을 비교하며 하천 침식 지형이라는 점을 설명한다.", "valley_profile", _case("alpine_v_valley", "알프스 상류 V자곡", "스위스 알프스", 46.57, 8.43, "valley_profile", "왜 바닥의 깊이가 먼저 커질까요?", "하천 침식과 사면 조정이 함께 V자곡을 만든다는 점을 강조하세요."), V_VALLEY_STAGES, 0.90),
    _topic("waterfall", "river", "폭포", RIVER, "waterfall", "river", "erosion", "낙차가 큰 구간 아래에서 침식이 강해지고 폭포가 상류로 후퇴합니다.", "차별 침식과 두부 침식으로 폭포가 뒤로 물러나는 과정을 이해한다.", "폭포 아래의 침식 웅덩이와 상류 쪽 후퇴를 함께 관찰한다.", "V자곡처럼 하천이 만든 지형이지만 지층 차이가 더 강하게 드러난다고 비교한다.", "valley_profile", _case("victoria_falls", "빅토리아 폭포", "잠비아·짐바브웨", -17.92, 25.86, "valley_profile", "폭포는 왜 제자리에서만 깎이지 않을까요?", "폭포의 낙차와 후퇴 방향을 함께 설명하세요."), WATERFALL_STAGES, 0.90),
    _topic("alluvial_fan", "river", "선상지", RIVER, "alluvial_fan", "river", "deposition", "산지 출구에서 유속이 줄며 부채꼴 퇴적이 넓어집니다.", "산지 출구에서 운반력이 감소할 때 선상지가 만들어진다는 점을 이해한다.", "좁은 골짜기에서 넓은 평지로 바뀌는 지점을 중심으로 본다.", "깎인 지형이 아니라 쌓인 지형임을 강조하며 곡류하천과 대비한다.", "planform_front", _case("death_valley_alluvial_fan", "데스밸리 선상지", "미국 데스밸리", 36.24, -116.82, "planform_front", "왜 산지 출구에서 갑자기 퇴적이 시작될까요?", "선상지는 감속-분산-퇴적의 순서로 설명하면 학생이 이해하기 쉽습니다."), ALLUVIAL_FAN_STAGES, 0.95),
    _topic("braided_river", "river", "망상하천", RIVER, "braided_river", "river", "transport", "운반물이 많아 하도가 여러 갈래로 갈라졌다 합쳐집니다.", "운반물 과잉 공급이 하도를 여러 갈래로 나누는 과정을 이해한다.", "중앙 사주와 반복되는 수로 분기를 함께 본다.", "곡류하천처럼 한 줄로 휘는 하천과 다르게 불안정한 분기 수로라는 점을 비교한다.", "planform_front", _case("canterbury_braided", "캔터베리 망상하천", "뉴질랜드 캔터베리 평야", -43.60, 172.10, "planform_front", "왜 물길이 한 줄로 유지되지 않을까요?", "사주 형성과 수로 분기를 묶어 설명하세요."), BRAIDED_RIVER_STAGES, 0.88),
    _topic("free_meander", "river", "곡류하천", RIVER, "free_meander", "river", "transport", "바깥쪽은 침식되고 안쪽은 퇴적되어 굽이가 점점 커집니다.", "같은 수로 안에서도 침식과 퇴적이 다른 위치에서 동시에 일어난다는 점을 이해한다.", "굽이 바깥쪽과 안쪽의 차이를 비교한다.", "망상하천과 달리 하나의 수로가 옆으로 이동한다는 점을 비교한다.", "planform_front", _case("mississippi_meander", "미시시피 곡류 평야", "미국 미시시피 평야", 33.10, -91.10, "planform_front", "왜 한쪽은 깎이고 다른 쪽은 쌓일까요?", "바깥쪽 침식, 안쪽 퇴적, 하도 이동을 하나의 세트로 설명하세요."), MEANDER_STAGES, 0.92),

    _topic("delta", "delta", "삼각주", DELTA, "delta", "coastal", "deposition", "하구 앞쪽에서 퇴적이 전진하며 삼각주가 성장합니다.", "하구에서 유속이 줄어 퇴적 전면이 바다 쪽으로 전진하는 과정을 이해한다.", "하구 전면과 분류 하천의 발달을 함께 본다.", "에스추어리와 비교하며 퇴적 우세 하구라는 점을 설명한다.", "planform_front", _case("nile_delta", "나일 삼각주", "이집트 북부", 31.20, 31.10, "planform_front", "왜 하구 앞에서 새로운 땅이 만들어질까요?", "강과 바다가 함께 만드는 지형이라는 점을 연결해 주세요."), DELTA_STAGES, 0.90),
    _topic("bird_foot_delta", "delta", "조족삼각주", DELTA, "bird_foot_delta", "coastal", "transport", "분류 하천이 길게 뻗으며 새 발 모양의 전면을 만듭니다.", "하천 공급이 매우 강할 때 조족삼각주가 발달한다는 점을 이해한다.", "길게 뻗는 분류 하천과 좁은 전면부를 관찰한다.", "호상삼각주보다 하천 영향이 더 강한 형태라고 비교한다.", "planform_front", _case("mississippi_bird_foot", "미시시피 조족삼각주", "미국 루이지애나", 29.00, -89.20, "planform_front", "왜 물길이 새 발처럼 길게 뻗을까요?", "파랑보다 하천 공급이 우세한 삼각주라는 점을 설명하세요."), DELTA_STAGES, 0.88),
    _topic("arcuate_delta", "delta", "호상삼각주", DELTA, "arcuate_delta", "coastal", "deposition", "전면이 부드럽게 휘어진 호 모양으로 자랍니다.", "하천 퇴적과 파랑 재가공이 균형을 이룬 삼각주 형태를 이해한다.", "부드럽게 둥근 전면부를 중심으로 본다.", "조족삼각주나 첨두삼각주와 전면 형태를 비교한다.", "planform_front", _case("nile_arcuate", "나일 호상삼각주", "이집트 북부", 31.15, 31.30, "planform_front", "왜 전면이 둥글게 휘어 있을까요?", "파랑의 재가공이 전면 모양을 다듬는다는 점을 짚어 주세요."), DELTA_STAGES, 0.88),
    _topic("cuspate_delta", "delta", "첨두삼각주", DELTA, "cuspate_delta", "coastal", "deposition", "파랑의 집중 재가공으로 삼각주 전면이 뾰족하게 정리됩니다.", "파랑의 영향이 강한 삼각주에서 첨두형 전면이 나타난다는 점을 이해한다.", "뾰족하게 나온 전면과 양옆 해안을 함께 본다.", "조족·호상 삼각주와 전면 모양을 비교한다.", "planform_front", _case("tiber_cuspate", "티베르 첨두삼각주", "이탈리아 서부", 41.74, 12.24, "planform_front", "왜 삼각주 끝이 뾰족해질까요?", "파랑이 삼각주 전면을 깎고 다듬는 과정도 함께 설명하세요."), DELTA_STAGES, 0.88),
    _topic("estuary", "delta", "에스추어리", DELTA, "estuary", "coastal", "transport", "하구가 넓게 열리고 조석이 강해 퇴적보다 혼합이 우세합니다.", "삼각주와 달리 조석과 해류가 강한 침수 하구를 이해한다.", "넓게 열린 하구와 강·바다 혼합대를 함께 본다.", "삼각주처럼 앞으로 자라지 않는 하구라는 점을 비교한다.", "planform_front", _case("thames_estuary", "템스 에스추어리", "영국 런던 동부", 51.50, 0.80, "planform_front", "왜 하구가 넓게 열리고 삼각주가 없을까요?", "조석 혼합이 강한 하구라는 점을 분명히 해 주세요."), ESTUARY_STAGES, 0.86),

    _topic("u_valley", "glacial", "U자곡", GLACIAL, "u_valley", "glacial", "erosion", "빙하가 바닥과 측벽을 함께 깎아 넓고 둥근 계곡을 만듭니다.", "하천 계곡과 달리 빙하가 넓은 U자 단면을 만든다는 점을 이해한다.", "넓은 바닥과 급한 측벽이 함께 드러나는 단면을 본다.", "V자곡과 단면 비교를 통해 빙하 지형임을 설명한다.", "valley_profile", _case("alps_u_valley", "알프스 U자곡", "스위스 고산 지역", 46.50, 8.00, "valley_profile", "왜 계곡 바닥만이 아니라 양옆도 함께 깎일까요?", "빙하는 넓고 둥글게 깎는다는 점을 꼭 비교하세요."), GLACIAL_VALLEY_STAGES, 0.92),
    _topic("cirque", "glacial", "권곡", GLACIAL, "cirque", "glacial", "erosion", "산 정상 부근에서 시작된 빙하가 그릇 모양 분지를 남깁니다.", "권곡이 빙하의 시작점에 해당하는 상류 지형임을 이해한다.", "반원형 분지와 급한 벽을 함께 본다.", "U자곡보다 상류의 초기 빙하 지형이라는 점을 비교한다.", "basin_overlook", _case("pyrenees_cirque", "피레네 권곡", "프랑스·스페인 피레네", 42.69, 0.03, "basin_overlook", "왜 산 위쪽에 그릇 모양 분지가 생길까요?", "적설, 소빙하, 반원형 침식의 연결을 설명하세요."), CIRQUE_STAGES, 0.90),
    _topic("horn", "glacial", "호른", GLACIAL, "horn", "glacial", "change", "여러 방향의 빙하 침식이 만나 뾰족한 피라미드형 봉우리를 남깁니다.", "여러 권곡이 둘러싸며 형성한 뾰족한 봉우리를 이해한다.", "권곡 사이 능선과 뾰족한 정상의 관계를 본다.", "아레트와 함께 여러 방향 빙하 침식의 결과로 설명한다.", "relief_oblique", _case("matterhorn_horn", "마테호른", "스위스·이탈리아 국경", 45.98, 7.66, "relief_oblique", "왜 산 정상만 유독 뾰족하게 남을까요?", "여러 권곡이 만나는 지점의 잔류 지형이라고 설명하세요."), HORN_STAGES, 0.92),
    _topic("arete", "glacial", "아레트", GLACIAL, "arete", "glacial", "change", "권곡 사이 능선이 날카롭게 남아 칼날 모양 능선을 이룹니다.", "두 권곡 사이의 날카로운 능선이 아레트임을 이해한다.", "칼날 같은 능선과 양옆의 권곡 위치를 함께 본다.", "호른이 봉우리라면 아레트는 능선이라는 점을 비교한다.", "relief_oblique", _case("sierra_arete", "시에라 네바다 아레트", "미국 시에라 네바다", 37.70, -119.57, "relief_oblique", "왜 능선이 칼날처럼 날카로워질까요?", "양쪽에서 동시에 깎이는 과정을 강조하세요."), HORN_STAGES, 0.90),
    _topic("fjord", "glacial", "피오르", GLACIAL, "fjord", "glacial", "change", "깊은 빙하곡에 바닷물이 들어와 좁고 긴 만입 해안이 됩니다.", "빙하곡이 해수 침수와 만나 피오르가 되는 과정을 이해한다.", "깊고 긴 만입과 양쪽 급사면을 함께 본다.", "U자곡이 바다와 연결된 해안이라는 점을 설명한다.", "coastal_front", _case("norway_fjord", "노르웨이 피오르", "노르웨이 서해안", 61.10, 6.80, "coastal_front", "왜 바닷물이 계곡 안 깊숙이 들어왔을까요?", "먼저 U자곡을 떠올리게 한 뒤 해수 침수를 연결하세요."), FJORD_STAGES, 0.94),

    _topic("shield_volcano", "volcanic", "순상화산", VOLCANIC, "shield_volcano", "volcanic", "tectonic", "묽은 현무암질 용암이 넓게 퍼져 낮고 넓은 화산체를 만듭니다.", "유동성이 큰 용암이 완만한 순상화산을 만든다는 점을 이해한다.", "넓은 폭과 완만한 경사를 중심으로 본다.", "성층화산보다 낮고 넓은 이유를 용암 점성과 연결한다.", "relief_oblique", _case("hawaii_shield", "하와이 순상화산", "미국 하와이", 19.47, -155.59, "relief_oblique", "왜 화산이 높은 원뿔 대신 넓은 방패 모양일까요?", "묽은 용암이 멀리 흐른다는 점을 강조하세요."), SHIELD_VOLCANO_STAGES, 0.90),
    _topic("stratovolcano", "volcanic", "성층화산", VOLCANIC, "stratovolcano", "volcanic", "tectonic", "점성 큰 용암과 화산쇄설물이 층을 이루며 가파른 원뿔형 화산을 만듭니다.", "폭발적 분출과 층상 축적으로 성층화산이 만들어진다는 점을 이해한다.", "가파른 사면과 뚜렷한 원뿔형을 중심으로 본다.", "순상화산과 분출 양상과 경사를 비교한다.", "relief_oblique", _case("fuji_stratovolcano", "후지산", "일본 혼슈", 35.36, 138.73, "relief_oblique", "왜 후지산은 높고 가파른 원뿔형일까요?", "점성, 분출 양상, 층상 축적을 묶어서 설명하세요."), STRATOVOLCANO_STAGES, 0.90),
    _topic("caldera", "volcanic", "칼데라", VOLCANIC, "caldera", "volcanic", "change", "대규모 분출 뒤 정상부가 함몰되어 큰 분지가 남습니다.", "칼데라가 폭발구보다 큰 함몰 분지라는 점을 이해한다.", "넓은 함몰 분지와 가장자리 테두리를 함께 본다.", "보통 화구와 달리 함몰 지형이라는 점을 비교한다.", "basin_overlook", _case("yellowstone_caldera", "옐로스톤 칼데라", "미국 와이오밍", 44.43, -110.67, "basin_overlook", "왜 화산 정상부가 넓게 꺼졌을까요?", "마그마 방이 비고 함몰되는 순서를 설명하세요."), CALDERA_STAGES, 0.88),
    _topic("crater_lake", "volcanic", "화구호", VOLCANIC, "crater_lake", "volcanic", "change", "함몰 분지나 화구에 물이 고여 호수가 됩니다.", "화산 활동 뒤 형성된 분지에 물이 차는 과정을 이해한다.", "분지 모양과 호수 채움 상태를 함께 본다.", "칼데라와 연결된 후속 지형이라는 점을 설명한다.", "basin_overlook", _case("crater_lake_oregon", "크레이터 레이크", "미국 오리건", 42.94, -122.10, "basin_overlook", "왜 화산 분지 안에 호수가 생겼을까요?", "함몰과 배수 조건을 함께 연결해 주세요."), CALDERA_STAGES, 0.88),
    _topic("lava_plateau", "volcanic", "용암대지", VOLCANIC, "lava_plateau", "volcanic", "change", "넓은 균열 분출이 반복되어 평탄한 용암 대지가 만들어집니다.", "점상 분출이 아니라 넓은 균열 분출로 용암대지가 형성된다는 점을 이해한다.", "넓고 평탄한 대지와 절벽을 함께 본다.", "화산인데도 원뿔형이 아닌 이유를 설명한다.", "planform_oblique", _case("deccan_traps", "데칸 용암대지", "인도 데칸 고원", 19.00, 73.00, "planform_oblique", "왜 화산인데도 넓은 평탄면처럼 보일까요?", "넓은 균열 분출과 반복 용암 피복을 연결해 주세요."), LAVA_PLATEAU_STAGES, 0.88),

    _topic("karst_doline", "karst", "돌리네", KARST, "karst_doline", "karst", "erosion", "석회암이 녹아 작은 함몰 지형이 여러 곳에 생깁니다.", "용식과 지하 배수로 돌리네가 발달하는 과정을 이해한다.", "작은 함몰과 배수 집중 지점을 본다.", "우발라보다 작은 기본 카르스트 함몰이라는 점을 비교한다.", "basin_overlook", _case("slovenia_doline", "슬로베니아 돌리네", "슬로베니아 카르스트", 45.80, 14.20, "basin_overlook", "왜 지표 곳곳이 움푹하게 꺼질까요?", "용식과 지하 배수의 연결을 꼭 설명하세요."), KARST_DOLINE_STAGES, 0.90),
    _topic("uvala", "karst", "우발라", KARST, "uvala", "karst", "change", "여러 돌리네가 합쳐져 더 큰 함몰 지형이 됩니다.", "작은 함몰 지형이 결합해 우발라로 발달하는 과정을 이해한다.", "작은 돌리네와 더 큰 함몰을 함께 비교해 본다.", "돌리네보다 더 넓은 카르스트 함몰이라는 점을 비교한다.", "basin_overlook", _case("dinaric_uvala", "디나릭 우발라", "크로아티아 디나릭 카르스트", 44.80, 15.30, "basin_overlook", "작은 함몰이 어떻게 큰 함몰로 이어질까요?", "돌리네의 결합이라는 점을 정리해 주세요."), KARST_DOLINE_STAGES, 0.90),
    _topic("tower_karst", "karst", "탑 카르스트", KARST, "tower_karst", "karst", "change", "주변은 낮아지고 잔류 석회암이 탑 모양으로 남습니다.", "차별 용식으로 남은 잔구가 탑 카르스트를 이룬다는 점을 이해한다.", "낮은 평탄면과 높은 잔구의 대조를 본다.", "돌리네처럼 움푹한 지형이 아니라 남겨진 지형임을 비교한다.", "relief_oblique", _case("guilin_tower_karst", "구이린 탑 카르스트", "중국 광시 구이린", 25.28, 110.29, "relief_oblique", "왜 주변은 낮아지고 일부만 탑처럼 남을까요?", "차별 용식으로 남은 지형이라는 점을 강조하세요."), TOWER_KARST_STAGES, 0.92),
    _topic("karren", "karst", "카렌", KARST, "karren", "karst", "erosion", "석회암 표면에 미세한 홈과 골이 발달합니다.", "카르스트 용식이 가장 작은 규모에서 시작된다는 점을 이해한다.", "표면의 홈과 골 패턴을 본다.", "탑 카르스트보다 작은 규모의 초기 용식 지형이라는 점을 비교한다.", "basin_overlook", _case("slovenia_karren", "슬로베니아 카렌", "슬로베니아 카르스트", 45.75, 14.10, "basin_overlook", "왜 암석 표면에 홈이 촘촘하게 생길까요?", "작은 용식 지형이 더 큰 카르스트로 이어진다는 점을 설명하세요."), TOWER_KARST_STAGES, 0.88),

    _topic("barchan", "arid", "바르한", ARID, "barchan", "arid", "transport", "한 방향 바람에 의해 초승달 모양 사구가 이동합니다.", "일정한 바람 방향과 제한된 모래 공급이 바르한을 만든다는 점을 이해한다.", "완만한 바람받이 사면과 급한 활락사면을 비교한다.", "횡사구·성상사구와 바람 조건을 비교한다.", "relief_oblique", _case("namib_barchan", "나미브 바르한", "나미비아 나미브 사막", -24.90, 15.00, "relief_oblique", "왜 사구가 초승달 모양일까요?", "바람 방향과 사면 차이를 함께 설명하세요."), DUNE_STAGES, 0.90),
    _topic("transverse_dune", "arid", "횡사구", ARID, "transverse_dune", "arid", "transport", "풍향과 직각으로 길게 이어지는 능선형 사구가 발달합니다.", "모래 공급이 많고 풍향이 일정할 때 횡사구가 만들어진다는 점을 이해한다.", "평행하게 이어지는 긴 능선 배열을 본다.", "바르한보다 모래 공급이 많을 때 나타난다고 비교한다.", "relief_oblique", _case("sahara_transverse", "사하라 횡사구", "알제리 사하라", 26.00, 8.00, "relief_oblique", "왜 사구 능선이 길게 나란할까요?", "풍향과 능선 방향의 관계를 짚어 주세요."), DUNE_STAGES, 0.88),
    _topic("star_dune", "arid", "성상사구", ARID, "star_dune", "arid", "change", "여러 방향 바람이 만나 중심에서 여러 능선이 뻗습니다.", "풍향이 복잡할 때 성상사구가 형성된다는 점을 이해한다.", "중심에서 방사형으로 뻗는 능선을 본다.", "바르한처럼 한쪽으로만 이동하지 않는 점을 비교한다.", "relief_oblique", _case("badain_jaran_star", "바다인자란 성상사구", "중국 바다인자란 사막", 40.30, 102.50, "relief_oblique", "왜 능선이 여러 방향으로 뻗을까요?", "복잡한 풍향 조건을 지형 모양과 연결해 설명하세요."), DUNE_STAGES, 0.88),
    _topic("mesa_butte", "arid", "메사·뷰트", ARID, "mesa_butte", "arid", "erosion", "건조 지역의 차별 침식으로 평평한 윗면과 급한 절벽을 가진 잔류 지형이 남습니다.", "수평 지층의 차별 침식이 메사와 뷰트를 만든다는 점을 이해한다.", "평평한 윗면과 급한 절벽의 대조를 본다.", "침식으로 남은 지형이라는 점에서 선상지 같은 퇴적 지형과 비교한다.", "relief_oblique", _case("monument_valley_mesa", "모뉴먼트밸리 메사", "미국 애리조나-유타", 36.99, -110.10, "relief_oblique", "왜 윗면은 평평하고 옆은 급할까요?", "단단한 층이 남는 차별 침식 지형이라고 설명하세요."), MESA_STAGES, 0.90),
    _topic("wadi", "arid", "와디", ARID, "wadi", "arid", "transport", "평소에는 마르지만 폭우가 오면 급류가 흐르는 건조 지역 하도가 남습니다.", "간헐 하천이 건조 지역 협곡과 하도를 만든다는 점을 이해한다.", "마른 하도와 폭우 시 급류 흔적을 함께 본다.", "상시 하천과 달리 건기에는 말라 있다는 점을 비교한다.", "planform_oblique", _case("sinai_wadi", "시나이 와디", "이집트 시나이 반도", 28.80, 33.60, "planform_oblique", "물이 없는데도 왜 하천 모양이 남아 있을까요?", "폭우 때만 흐르는 하천이라는 점을 강조하세요."), WADI_STAGES, 0.88),
    _topic("playa", "arid", "플라야", ARID, "playa", "arid", "deposition", "폐쇄 분지 바닥에 일시적 호수와 염류 평탄면이 발달합니다.", "내륙 배수 분지와 증발 작용으로 플라야가 형성된다는 점을 이해한다.", "평탄한 분지 바닥과 염류 흔적을 본다.", "와디처럼 흐르는 수로가 아니라 물이 모였다 사라지는 분지라는 점을 비교한다.", "planform_front", _case("bonneville_playa", "보네빌 플라야", "미국 유타", 40.75, -113.80, "planform_front", "왜 낮은 곳 바닥만 유난히 평평할까요?", "증발과 염류 침전을 함께 설명하세요."), PLAYA_STAGES, 0.88),
    _topic("pedestal_rock", "arid", "버섯바위", ARID, "pedestal_rock", "arid", "erosion", "바람이 아래쪽을 더 강하게 깎아 버섯 모양 기암이 남습니다.", "풍식이 바위의 아래쪽을 더 빠르게 침식할 수 있다는 점을 이해한다.", "좁아진 아래쪽과 넓은 윗부분을 비교한다.", "메사보다 훨씬 작은 규모의 풍식 지형이라는 점을 비교한다.", "relief_oblique", _case("white_desert_pedestal", "백사막 버섯바위", "이집트 백사막", 27.30, 28.00, "relief_oblique", "왜 바위 아래쪽이 더 빨리 깎였을까요?", "모래를 실은 바람이 지표 가까이서 더 강하게 작용한다고 설명하세요."), MESA_STAGES, 0.88),
    _topic("pediment", "arid", "페디먼트", ARID, "pediment", "arid", "change", "산록 앞에 완만한 암반 평탄면이 발달합니다.", "건조 지역 산록에서 페디먼트가 만들어지는 과정을 이해한다.", "산록과 이어지는 완만한 경사면을 본다.", "선상지와 달리 퇴적이 아니라 기반암 평탄면이라는 점을 비교한다.", "planform_front", _case("basin_range_pediment", "베이슨 앤 레인지 페디먼트", "미국 네바다", 38.50, -117.00, "planform_front", "왜 산 앞에 완만한 평탄면이 생길까요?", "선상지와 비교해 기반암이 드러난 면이라는 점을 설명하세요."), MESA_STAGES, 0.88),

    _topic("coastal_cliff", "coastal", "해식애", COASTAL, "coastal_cliff", "coastal", "erosion", "파랑 침식으로 절벽이 후퇴하고 앞에는 파식대가 넓어집니다.", "파랑 침식이 해안 절벽을 후퇴시키는 과정을 이해한다.", "절벽 하단의 노치와 앞쪽 파식대를 함께 본다.", "사주처럼 쌓이는 해안과 정반대인 깎이는 해안으로 비교한다.", "coastal_front", _case("pacific_cliff", "태평양 해식애", "칠레·캘리포니아형 해안", -33.45, -71.68, "coastal_front", "왜 절벽 아래쪽이 먼저 깎일까요?", "절벽 하단 노치와 후퇴 방향을 함께 설명하세요."), COASTAL_CLIFF_STAGES, 0.90),
    _topic("spit_lagoon", "coastal", "사주·석호", COASTAL, "spit_lagoon", "coastal", "deposition", "연안류가 옮긴 모래가 해안 끝에서 길게 자라 사주와 석호를 만듭니다.", "연안류와 퇴적으로 사주·석호가 발달하는 과정을 이해한다.", "길게 뻗는 사주와 안쪽의 잔잔한 수역을 본다.", "해식애처럼 깎이는 해안과 비교해 쌓이는 해안이라는 점을 설명한다.", "planform_front", _case("curonian_spit", "쿠로니안 사주", "리투아니아·러시아", 55.30, 20.95, "planform_front", "왜 모래가 해안선을 따라 길게 쌓일까요?", "연안류와 입구 차단을 연결해 설명하세요."), SPIT_STAGES, 0.88),
    _topic("tombolo", "coastal", "육계사주", COASTAL, "tombolo", "coastal", "deposition", "퇴적물이 쌓여 섬과 육지가 모래줄로 연결됩니다.", "파랑 굴절과 퇴적으로 육계사주가 만들어지는 과정을 이해한다.", "섬과 육지를 잇는 모래 연결부를 본다.", "사주·석호와 달리 섬을 연결하는 지형이라는 점을 비교한다.", "planform_oblique", _case("chesil_tombolo", "체실 육계사주", "영국 남부 해안", 50.63, -2.58, "planform_oblique", "왜 섬과 육지가 모래로 이어질까요?", "섬 뒤쪽의 에너지 약화와 퇴적을 설명하세요."), SPIT_STAGES, 0.88),
    _topic("sea_arch", "coastal", "해식아치", COASTAL, "sea_arch", "coastal", "erosion", "약한 층이 먼저 깎여 바위 곶에 아치형 구멍이 생깁니다.", "차별 침식으로 해식동굴이 관통해 해식아치가 된다는 점을 이해한다.", "아치의 빈 공간과 남아 있는 상부를 함께 본다.", "해식애보다 더 국지적인 차별 침식 지형으로 비교한다.", "coastal_front", _case("durdle_door_arch", "더들 도어", "영국 도싯 해안", 50.62, -2.28, "coastal_front", "왜 바위 곶에 구멍이 뚫렸을까요?", "해식동굴에서 해식아치로 이어지는 과정을 설명하세요."), SEA_ARCH_STAGES, 0.88),
    _topic("coastal_dune", "coastal", "해안사구", COASTAL, "coastal_dune", "coastal", "transport", "해변의 모래가 바람에 날려 해안 뒤쪽에 사구를 만듭니다.", "해안에서도 바람이 강하면 사구가 형성된다는 점을 이해한다.", "해변과 그 뒤쪽 사구의 연결을 본다.", "사막 사구와 달리 모래 공급원이 해변이라는 점을 비교한다.", "planform_oblique", _case("maspalomas_dune", "마스팔로마스 해안사구", "스페인 카나리아", 27.74, -15.59, "planform_oblique", "해변 모래가 왜 뒤쪽 사구가 될까요?", "모래 공급원이 해변이라는 점을 꼭 짚어 주세요."), DUNE_STAGES, 0.88),
    _topic("ria_coast", "coastal", "리아스식 해안", COASTAL, "ria_coast", "coastal", "change", "하천곡이 바다에 잠겨 복잡한 만입 해안이 만들어집니다.", "침수된 하천곡이 리아스식 해안을 만든다는 점을 이해한다.", "길게 들어온 만입과 복잡한 해안선을 본다.", "삼각주처럼 쌓이는 해안이 아니라 잠긴 해안이라는 점을 비교한다.", "planform_front", _case("galicia_ria", "갈리시아 리아스", "스페인 북서부", 42.43, -8.84, "planform_front", "왜 해안선이 이렇게 복잡할까요?", "하천곡이 침수된 결과라는 점을 설명하세요."), RIA_STAGES, 0.88),
)


TOPICS = {topic.topic_id: topic for topic in TOPIC_SPECS}


def _serialize_stage(stage: TeachingStage) -> dict[str, object]:
    return asdict(stage)


def _serialize_world_case(case: WorldCase) -> dict[str, object]:
    return asdict(case)


def _serialize_topic(topic: TopicSpec) -> dict[str, object]:
    group = _group(topic.group_id)
    return {
        "topic_id": topic.topic_id,
        "group_id": topic.group_id,
        "badge": group["badge"],
        "title": topic.title,
        "category": topic.category,
        "landform_key": topic.landform_key,
        "landform_type": topic.landform_type,
        "curriculum_unit": topic.curriculum_unit,
        "classroom_goal": topic.classroom_goal,
        "observation_focus": topic.observation_focus,
        "compare_hint": topic.compare_hint,
        "primary_overlay": topic.primary_overlay,
        "overlay_caption": topic.overlay_caption,
        "preview_stage": topic.preview_stage,
        "camera_profile": topic.camera_profile,
        "recommended_view": topic.world_case.recommended_view,
        "student_question": topic.world_case.student_question,
        "teacher_note": topic.world_case.teacher_note,
        "world_case": _serialize_world_case(topic.world_case),
        "stages": [_serialize_stage(stage) for stage in topic.stages],
    }


def get_high_school_world_groups() -> list[dict[str, object]]:
    return [dict(group) for group in GROUPS]


def get_high_school_world_group(group_id: str) -> dict[str, object] | None:
    for group in GROUPS:
        if group["group_id"] == group_id:
            return dict(group)
    return None


def get_high_school_world_topics(group_id: str | None = None) -> list[dict[str, object]]:
    topics: Iterable[TopicSpec] = TOPIC_SPECS
    if group_id is not None:
        topics = (topic for topic in TOPIC_SPECS if topic.group_id == group_id)
    return [_serialize_topic(topic) for topic in topics]


def get_high_school_world_topic(topic_id: str) -> dict[str, object] | None:
    topic = TOPICS.get(topic_id)
    if topic is None:
        return None
    return _serialize_topic(topic)


def _normalize(field: np.ndarray) -> np.ndarray:
    finite = np.nan_to_num(np.asarray(field, dtype=float), nan=0.0, posinf=0.0, neginf=0.0)
    max_value = float(np.max(finite))
    min_value = float(np.min(finite))
    if max_value - min_value < 1e-9:
        return np.zeros_like(finite)
    return (finite - min_value) / (max_value - min_value)


def _grid(shape: tuple[int, int]) -> tuple[np.ndarray, np.ndarray]:
    rows, cols = shape
    y, x = np.mgrid[0:rows, 0:cols]
    x = x / max(cols - 1, 1)
    y = y / max(rows - 1, 1)
    return x, y


def build_high_school_process_fields(topic_id: str, elevation: np.ndarray) -> dict[str, np.ndarray]:
    elev = np.asarray(elevation, dtype=float)
    x, y = _grid(elev.shape)
    high = _normalize(elev)
    low = 1.0 - high
    gy, gx = np.gradient(elev)
    slope = _normalize(np.hypot(gx, gy))
    centerline = np.exp(-((x - 0.5) ** 2) / 0.02)
    fan_toe = np.exp(-((y - 0.82) ** 2) / 0.03)
    coastal_front = np.exp(-((y - 0.88) ** 2) / 0.02)
    basin_center = np.exp(-(((x - 0.5) ** 2) + ((y - 0.5) ** 2)) / 0.08)
    ridge = _normalize(high * (0.5 + np.abs(x - 0.5)))

    erosion = _normalize(slope * (0.65 + 0.35 * low))
    deposition = _normalize(low * (1.0 - 0.6 * slope))
    transport = _normalize((0.55 * slope) + (0.45 * centerline))
    tectonic = _normalize(high)
    change = _normalize(np.abs(elev - np.mean(elev)))

    if topic_id in {"v_valley", "waterfall"}:
        erosion = _normalize(erosion * (0.55 + centerline))
        transport = _normalize(transport * (0.4 + centerline))
    elif topic_id == "alluvial_fan":
        deposition = _normalize((0.5 + fan_toe) * (0.5 + low) * (1.0 - 0.4 * slope))
        transport = _normalize(centerline * (1.0 - 0.5 * y))
    elif topic_id in {"delta", "bird_foot_delta", "arcuate_delta", "cuspate_delta"}:
        deposition = _normalize((0.55 + fan_toe) * (0.55 + low))
        transport = _normalize(centerline * (0.5 + y))
    elif topic_id in {"free_meander", "braided_river", "estuary", "ria_coast", "spit_lagoon", "tombolo"}:
        transport = _normalize((0.45 + centerline) * (0.6 + slope))
        deposition = _normalize(deposition * (0.4 + np.abs(x - 0.5)))
    elif topic_id in {"u_valley", "cirque", "horn", "arete", "fjord"}:
        erosion = _normalize(erosion * (0.45 + centerline + basin_center))
        change = _normalize(change * (0.45 + basin_center))
    elif topic_id in {"shield_volcano", "stratovolcano", "caldera", "crater_lake", "lava_plateau"}:
        tectonic = _normalize(0.65 * high + 0.35 * basin_center)
        change = _normalize(0.55 * ridge + 0.45 * basin_center)
    elif topic_id in {"karst_doline", "uvala", "tower_karst", "karren"}:
        erosion = _normalize((0.55 + low) * (0.45 + basin_center))
        transport = _normalize(0.45 * centerline + 0.55 * low)
        change = _normalize((0.5 + ridge) * (0.5 + low))
    elif topic_id in {"barchan", "transverse_dune", "star_dune", "coastal_dune"}:
        transport = _normalize(0.45 + np.sin((x + y) * np.pi) ** 2)
        deposition = _normalize((0.45 + low) * (0.45 + np.cos(x * np.pi) ** 2))
    elif topic_id in {"mesa_butte", "pedestal_rock", "pediment"}:
        erosion = _normalize(slope * (0.55 + low))
        change = _normalize((0.6 + ridge) * (0.4 + slope))
    elif topic_id in {"wadi", "playa"}:
        transport = _normalize((0.55 + centerline) * (0.45 + low))
        deposition = _normalize((0.55 + low) * (0.45 + fan_toe))
    elif topic_id in {"coastal_cliff", "sea_arch"}:
        erosion = _normalize((0.5 + coastal_front) * (0.5 + slope))
        tectonic = _normalize(0.55 * high + 0.45 * coastal_front)

    return {
        "erosion": erosion,
        "deposition": deposition,
        "transport": transport,
        "tectonic": tectonic,
        "change": change,
    }
