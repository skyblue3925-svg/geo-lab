"""여행지리 수업용 케이스 라이브러리."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class EvidenceItem:
    indicator: str
    value: str
    year: str
    source: str
    note: str = ""


@dataclass(frozen=True)
class TimelineItem:
    period: str
    event: str
    implication: str


@dataclass(frozen=True)
class PolicyOption:
    option_id: str
    title: str
    summary: str
    expected_effect: str
    tradeoff: str


@dataclass(frozen=True)
class RealCaseCard:
    title: str
    location: str
    period: str
    key_point: str
    classroom_use: str
    source_name: str
    source_url: str


@dataclass(frozen=True)
class CaseSpec:
    case_id: str
    title: str
    region: str
    real_world_anchor: str
    narrative: str
    guiding_question: str
    stakeholders: str
    lesson_focus: str
    learning_objectives: List[str]
    classroom_prompts: List[str]
    timeline: List[TimelineItem]
    evidence_items: List[EvidenceItem]
    source_notes: List[str]
    policy_options: List[PolicyOption]
    baseline_label: str
    intervention_label: str
    research_landform: str
    render_landform_type: str
    research_grid_size: int
    research_stage: float
    research_cell_size: float
    climate_month: int
    climate_mode: str
    baseline_k: float
    baseline_d: float
    baseline_u: float
    intervention_k: float
    intervention_d: float
    intervention_u: float


CASE_LIBRARY: Dict[str, CaseSpec] = {
    "delta_overtourism": CaseSpec(
        case_id="delta_overtourism",
        title="델타 관문: 퇴적 균형과 과잉관광",
        region="하구 델타 평야",
        real_world_anchor="낙동강 하구 + 베네치아형 관문 관광 압력",
        narrative=(
            "하구 일대가 연중 관광 관문으로 성장하면서 지역 수입은 늘었지만, "
            "제방 유지비 증가, 습지 단절, 혼잡 민원이 동시에 커지고 있다."
        ),
        guiding_question="관광 접근성을 유지하면서 델타의 퇴적-습지 기능을 어떻게 보전할 것인가?",
        stakeholders="주민, 습지관리기관, 관광사업자, 대중교통 운영기관",
        lesson_focus="수용력 관리, 습지 보전, 델타 지형과 정책의 연결",
        learning_objectives=[
            "지형 지표와 관광 지표를 함께 읽는다.",
            "정책 대안을 수치 근거로 비교한다.",
            "시뮬레이션 결과를 CER 주장으로 연결한다.",
        ],
        classroom_prompts=[
            "병목은 어디에서 발생하는가: 수로, 접근로, 습지 경계?",
            "관광 압력이 증가할 때 가장 먼저 악화되는 지표는 무엇인가?",
            "각 정책에서 누가 이익을 보고 누가 비용을 부담하는가?",
        ],
        timeline=[
            TimelineItem("2015-2018", "수변 재개발과 접근 인프라 확장", "방문객 증가 속도가 급격히 빨라짐."),
            TimelineItem("2019-2021", "성수기 혼잡과 제방 유지비 급증", "예산이 예방 중심으로 이동함."),
            TimelineItem("2022-2025", "습지 이용 갈등 심화", "성장 중심에서 회복탄력성 중심으로 정책 전환."),
        ],
        evidence_items=[
            EvidenceItem(
                indicator="연간 방문객 규모(관문도시 기준)",
                value="2천만 명대(회복기 포함)",
                year="2019-2024",
                source="지자체 관광 통계 대시보드",
                note="수업에서는 압력 규모를 비교하는 기준값으로 사용.",
            ),
            EvidenceItem(
                indicator="관리 압력이 높은 습지 구간",
                value="교통 결절점 인근에 집중",
                year="2020-2025",
                source="국가 습지 모니터링 요약",
                note="정확 면적보다 핫스팟 위치 해석이 핵심.",
            ),
            EvidenceItem(
                indicator="상대적 해수면 및 지반침하 위험",
                value="저지대 델타의 복합위험 증가",
                year="AR6 이후",
                source="IPCC 종합보고서 요지",
                note="장기 적응정책 필요성을 설명하는 근거.",
            ),
        ],
        source_notes=[
            "정량 채점 전에는 최신 지역 통계를 반드시 재확인하세요.",
            "기본 케이스를 사용하되, 지역 데이터가 있으면 교체해서 사용하세요.",
        ],
        policy_options=[
            PolicyOption(
                option_id="A",
                title="접근량 우선 확장",
                summary="관광 처리량 유지를 위해 접근로와 호안 구조를 지속 확장.",
                expected_effect="단기 매출과 이동 편의 개선.",
                tradeoff="유지비 고정화, 습지 단절 위험, 장기 취약성 증가.",
            ),
            PolicyOption(
                option_id="B",
                title="관리형 접근 + 완충습지",
                summary="피크 시간대 유입량을 조절하고 완충구간 중심으로 동선을 재설계.",
                expected_effect="지형 스트레스 완화와 습지 연속성 개선.",
                tradeoff="요금·운영 규칙 조정에 따른 이해관계 갈등.",
            ),
        ],
        baseline_label="생태 제어가 약한 관광 확장 시나리오",
        intervention_label="관리형 접근 + 완충습지 시나리오",
        research_landform="delta",
        render_landform_type="river",
        research_grid_size=120,
        research_stage=1.0,
        research_cell_size=20.0,
        climate_month=8,
        climate_mode="real",
        baseline_k=0.00022,
        baseline_d=0.018,
        baseline_u=0.00024,
        intervention_k=0.00016,
        intervention_d=0.024,
        intervention_u=0.00024,
    ),
    "coastal_retreat": CaseSpec(
        case_id="coastal_retreat",
        title="해안 절벽 노선: 후퇴 위험과 안전",
        region="파랑 지배형 암석 해안",
        real_world_anchor="동해안 절벽 지대 + 영국식 후퇴율 관리 사례",
        narrative=(
            "전망도로와 해안 산책로가 지역 관광의 핵심이지만, "
            "강한 폭풍 사건이 잦아지며 절벽 후퇴 구간의 응급보수 비용이 반복 증가하고 있다."
        ),
        guiding_question="어떤 구간을 보호하고, 어떤 구간은 우회·계절 제한으로 전환해야 하는가?",
        stakeholders="지자체, 관광 소상공인, 어업 종사자, 재난·도로 안전 부서",
        lesson_focus="해안재해 구역화, 노선 재설계, 계절별 운영전략",
        learning_objectives=[
            "절벽 후퇴 위험의 공간적 불균등성을 해석한다.",
            "정책 개입 전후 지형 변화를 시뮬레이션으로 비교한다.",
            "단기 편익과 장기 안전의 상충을 설명한다.",
        ],
        classroom_prompts=[
            "모든 구간을 연중 개방할 때 숨은 비용은 무엇인가?",
            "폭풍기 계절 제한은 소득과 안전에 어떤 영향을 주는가?",
            "어디에서 구조물 보호보다 노선 우회가 더 효율적인가?",
        ],
        timeline=[
            TimelineItem("2014-2018", "해안 축제와 경관도로 인기로 방문 증가", "절벽 인접 시설 노출도 상승."),
            TimelineItem("2019-2022", "폭풍 후 통제·복구 반복", "사후복구 중심 운영의 비용 부담 심화."),
            TimelineItem("2023-2025", "관리형 후퇴 논의 본격화", "안전성과 관광 접근성의 조정 필요."),
        ],
        evidence_items=[
            EvidenceItem(
                indicator="절벽 후퇴율 참고 범위",
                value="연 0.3~0.8m(지점별 편차)",
                year="다년 평균",
                source="해안침식 위험지도·해외 관리사례",
                note="현지 실측치가 아니라 비교 기준 범위로 활용.",
            ),
            EvidenceItem(
                indicator="폭풍 사건 기반 통제 일수",
                value="고에너지 계절에 증가 추세",
                year="최근 10년",
                source="재난대응 운영기록(유사사례 기반)",
                note="수업에서는 학교가 선택한 샘플 값으로 분석 가능.",
            ),
            EvidenceItem(
                indicator="노선 유지관리 부담",
                value="고위험 구간에서 응급보수 반복",
                year="2019-2025",
                source="지자체 예산요약 유사모형",
                note="생애주기 비용 비교 근거로 사용.",
            ),
        ],
        source_notes=[
            "가능하면 지역 해안 사진·위험지도와 함께 수업하세요.",
            "단기 경관효과와 장기 지형안정을 분리해 토론하세요.",
        ],
        policy_options=[
            PolicyOption(
                option_id="A",
                title="절벽선 구조보호 중심",
                summary="현 노선을 유지하기 위해 호안·보강 구조물을 우선 확충.",
                expected_effect="경로 연속성과 관광 동선의 즉각적 안정.",
                tradeoff="침식 전이 가능성, 유지비 잠금(lock-in) 위험.",
            ),
            PolicyOption(
                option_id="B",
                title="관리형 후퇴 복도",
                summary="취약 구간을 내륙 우회로 전환하고 해안 접근은 계절 창으로 운영.",
                expected_effect="재해 노출 감소와 유연한 운영.",
                tradeoff="초기 재설계 비용과 이용자 저항 가능성.",
            ),
        ],
        baseline_label="구조보호 중심 연속개방 시나리오",
        intervention_label="관리형 후퇴 + 계절운영 시나리오",
        research_landform="coastal_cliff",
        render_landform_type="coastal",
        research_grid_size=100,
        research_stage=1.0,
        research_cell_size=15.0,
        climate_month=10,
        climate_mode="real",
        baseline_k=0.00020,
        baseline_d=0.014,
        baseline_u=0.00015,
        intervention_k=0.00013,
        intervention_d=0.020,
        intervention_u=0.00015,
    ),
    "fjord_climate_risk": CaseSpec(
        case_id="fjord_climate_risk",
        title="피오르 회랑: 기후 위험과 노선 선택",
        region="고위도 빙식계곡·피오르 지대",
        real_world_anchor="노르웨이 피오르 관광 + 사면위험 관리 관행",
        narrative=(
            "비성수기 프리미엄 여행 수요가 늘고 있지만, "
            "급격한 기상 변화와 사면 불안정으로 노선 운영의 불확실성이 커지고 있다."
        ),
        guiding_question="방문 경험을 유지하면서 계절·사면 위험을 최소화하는 노선 전략은 무엇인가?",
        stakeholders="가이드, 방문객, 지자체 계획부서, 긴급대응기관",
        lesson_focus="기후 계절성, 노선 신뢰성, 산악관광 위험 거버넌스",
        learning_objectives=[
            "기후 계절성과 이동 위험의 연결을 설명한다.",
            "지형 근거로 계절별 운영창을 제안한다.",
            "불확실성 조건에서 정책의 강건성을 비교한다.",
        ],
        classroom_prompts=[
            "비성수기 확장 마케팅을 그대로 유지해도 되는가?",
            "사고 전 선제 통제를 정당화하는 근거는 무엇인가?",
            "주민과 관광객에게 위험을 어떻게 다르게 전달할 것인가?",
        ],
        timeline=[
            TimelineItem("2016-2019", "비성수기 관광상품 확대", "수익 기회 증가."),
            TimelineItem("2020-2023", "사면·기상 모니터링 확대", "운영 복잡성 상승."),
            TimelineItem("2024-2025", "노선 신뢰성·보험 이슈 부각", "적응형 운영 필요성 증대."),
        ],
        evidence_items=[
            EvidenceItem(
                indicator="고위도 온난화 신호",
                value="다수 지역에서 전지구 평균보다 빠른 상승",
                year="최근 수십 년",
                source="IPCC 및 국가기후평가",
                note="사건 예측이 아니라 추세 해석 근거로 사용.",
            ),
            EvidenceItem(
                indicator="사면재해 감시구역 확대",
                value="교통축 주변 위험구역 상시 모니터링 증가",
                year="2020년대",
                source="북유럽 재해관리 공개자료",
                note="예방 통제정책 논리의 근거.",
            ),
            EvidenceItem(
                indicator="비성수기 수요 증가",
                value="여름 외 시즌 수요의 구조적 확대",
                year="회복기 이후",
                source="지역 관광청 추세보고",
                note="개방 압력과 안전 압력의 동시 존재를 보여줌.",
            ),
        ],
        source_notes=[
            "기후 추세 근거와 단일 사건 예측을 구분해 서술하세요.",
            "정책 메모에는 불확실성 문장을 반드시 포함하세요.",
        ],
        policy_options=[
            PolicyOption(
                option_id="A",
                title="비성수기 확장 우선",
                summary="보강공사를 병행하며 비성수기 노선 개방폭을 유지.",
                expected_effect="연간 관광 처리량 증가.",
                tradeoff="불안정 기간의 노출 위험 상승 가능성.",
            ),
            PolicyOption(
                option_id="B",
                title="적응형 노선 달력",
                summary="위험 등급·트리거를 사전 공개하고 조건부 통제 운영.",
                expected_effect="사고 확률 감소와 신뢰도 향상.",
                tradeoff="매출 변동성과 운영규정 강화 부담.",
            ),
        ],
        baseline_label="비성수기 확장 유지 시나리오",
        intervention_label="적응형 노선 달력 시나리오",
        research_landform="fjord",
        render_landform_type="glacial",
        research_grid_size=110,
        research_stage=1.0,
        research_cell_size=25.0,
        climate_month=2,
        climate_mode="real",
        baseline_k=0.00017,
        baseline_d=0.012,
        baseline_u=0.00030,
        intervention_k=0.00012,
        intervention_d=0.019,
        intervention_u=0.00030,
    ),
    "karst_overtourism": CaseSpec(
        case_id="karst_overtourism",
        title="석회암 명승지: 카르스트 유산과 방문 압력",
        region="탑카르스트 만·동굴 관광권",
        real_world_anchor="하롱베이·계림형 카르스트 관광 혼잡",
        narrative=(
            "상징 경관에 방문이 집중되면서 선박 이동 밀도와 동굴 내부 이용압이 증가하고, "
            "수질·미기후 보전에 대한 우려가 커지고 있다."
        ),
        guiding_question="지형유산의 가치를 유지하면서도 관광경제를 지속시키는 운영 방식은 무엇인가?",
        stakeholders="선박 운영자, 유산관리기관, 지역주민, 보전단체",
        lesson_focus="유산지 수용력, 혼잡 분산, 보호구역 운영 설계",
        learning_objectives=[
            "경관 가치와 생태·지형 회복탄력성을 구분한다.",
            "수용력 관리 지표를 정책 트리거로 제안한다.",
            "핵심지 집중형과 분산형 운영을 비교한다.",
        ],
        classroom_prompts=[
            "어떤 지표가 선박 슬롯 제한을 발동해야 하는가?",
            "방문객 분산은 상징지 보호에 실제로 기여하는가?",
            "동굴 접근은 시간대 예약제로 전환해야 하는가?",
        ],
        timeline=[
            TimelineItem("2013-2018", "크루즈 연계 관광 급증", "핵심 명소 혼잡 심화."),
            TimelineItem("2019-2021", "수요 급감 후 회복", "운영 재설계 기회 발생."),
            TimelineItem("2022-2025", "수요 재상승과 보전 논의 확대", "수용력 거버넌스 중요성 부각."),
        ],
        evidence_items=[
            EvidenceItem(
                indicator="연간 방문객 규모",
                value="수백만 명대 수요",
                year="팬데믹 전후 비교",
                source="지방 관광연감·유산관리 보고",
                note="정확 수치는 최신 연감으로 교체 가능.",
            ),
            EvidenceItem(
                indicator="고밀도 선박 항로 주변 수질 부담",
                value="국지적 고부하 핫스팟 확인",
                year="최근 모니터링",
                source="환경 모니터링 공지",
                note="수업에서는 핫스팟 위치 해석 중심.",
            ),
            EvidenceItem(
                indicator="동굴 미기후 민감성",
                value="방문 집중 시간대 CO2·온도 변동 확대",
                year="다수 연구",
                source="카르스트 동굴 보전 연구",
                note="시간제 예약 근거로 활용.",
            ),
        ],
        source_notes=[
            "포토스팟 인기와 보전 우선구역을 분리해 토론하세요.",
            "가능하면 선박 밀도 지도를 함께 제시하세요.",
        ],
        policy_options=[
            PolicyOption(
                option_id="A",
                title="핵심지 집중 운영",
                summary="대표 명소 중심으로 인프라를 확충하고 접근을 유지.",
                expected_effect="브랜드 집중과 단기 지출 확대.",
                tradeoff="핫스팟 압력 고착과 취약성 누적.",
            ),
            PolicyOption(
                option_id="B",
                title="분산형 유산 순환",
                summary="시간제 예약과 대체 코스를 결합해 방문을 분산.",
                expected_effect="핵심지 압력 완화와 지역 편익 분산.",
                tradeoff="운영자 협의와 이용자 행동변화 필요.",
            ),
        ],
        baseline_label="핵심지 집중 운영 시나리오",
        intervention_label="분산형 순환 + 예약제 시나리오",
        research_landform="tower_karst",
        render_landform_type="karst",
        research_grid_size=120,
        research_stage=1.0,
        research_cell_size=12.0,
        climate_month=6,
        climate_mode="real",
        baseline_k=0.00019,
        baseline_d=0.013,
        baseline_u=0.00018,
        intervention_k=0.00014,
        intervention_d=0.020,
        intervention_u=0.00018,
    ),
    "volcanic_geotourism": CaseSpec(
        case_id="volcanic_geotourism",
        title="화산 지오트레일: 접근 가치와 위험 창",
        region="활성 화산지형·칼데라 관광권",
        real_world_anchor="아이슬란드 레이캬네스 + 제주 지오트레일 운영 논리",
        narrative=(
            "활성 화산경관 수요가 커지면서 지오트레일 이용이 급증했지만, "
            "분화·가스·지진 변동성 때문에 개방 판단과 위험소통이 어려워지고 있다."
        ),
        guiding_question="위험 변동성이 큰 화산지형에서 접근 운영 기준을 어떻게 설계해야 하는가?",
        stakeholders="가이드, 지자체 재난부서, 숙박업계, 보호구역 관리기관",
        lesson_focus="동적 위험관리, 조건부 개방, 관광 커뮤니케이션",
        learning_objectives=[
            "지형 활동성과 운영정책의 연결고리를 설명한다.",
            "경고수준 변화에 따른 접근정책을 설계한다.",
            "수치 결과를 운영 트리거로 전환한다.",
        ],
        classroom_prompts=[
            "어떤 경고수준에서 자동 통제가 발동되어야 하는가?",
            "불확실성을 알리면서도 신뢰를 유지하는 안내 문구는 무엇인가?",
            "폐쇄 시 대체 코스는 어떻게 구성해야 하는가?",
        ],
        timeline=[
            TimelineItem("2010년대", "지오트레일 브랜드 강화", "고위험 경관 수요 확대."),
            TimelineItem("2021-2025", "반복적 분화 사건", "개방 규칙의 동적 운영 필요."),
            TimelineItem("현재", "안전 프로토콜과 지역경제의 조정", "정책 일관성·신뢰가 핵심 이슈."),
        ],
        evidence_items=[
            EvidenceItem(
                indicator="분화 재발 사건 빈도",
                value="2021년 이후 다회 사건",
                year="2021-2025",
                source="국가 지구물리 관측기관 공지",
                note="시간축 위험 인식 근거로 사용.",
            ),
            EvidenceItem(
                indicator="활성 지형 방문 수요",
                value="핵심 구간 수요 집중",
                year="최근 시즌",
                source="지역 관광전략 보고",
                note="개방 압력과 안전 압력의 동시성 확인.",
            ),
            EvidenceItem(
                indicator="통제·우회 운영 빈도",
                value="위험 급등 시 운행 차질 반복",
                year="최근 수년",
                source="재난·민방위 운영공지",
                note="대안정책의 강건성 비교 근거.",
            ),
        ],
        source_notes=[
            "정책 문장에는 항상 불확실성 범위를 함께 제시하세요.",
            "안전과 생계 영향을 동시에 비교하도록 지도하세요.",
        ],
        policy_options=[
            PolicyOption(
                option_id="A",
                title="최대 개방 우선",
                summary="최소 조건만 충족하면 가능한 한 개방을 유지.",
                expected_effect="가시성·매출 확대.",
                tradeoff="운영 리스크와 현장 소통 부담 증가.",
            ),
            PolicyOption(
                option_id="B",
                title="등급형 접근 프로토콜",
                summary="위험등급별 접근구역과 통제 트리거를 사전 공개.",
                expected_effect="예측 가능한 운영과 신뢰 향상.",
                tradeoff="피크일 수용량 감소와 단기 매출 변동.",
            ),
        ],
        baseline_label="최대 개방 유지 시나리오",
        intervention_label="등급형 접근 프로토콜 시나리오",
        research_landform="caldera",
        render_landform_type="volcanic",
        research_grid_size=110,
        research_stage=1.0,
        research_cell_size=18.0,
        climate_month=7,
        climate_mode="real",
        baseline_k=0.00021,
        baseline_d=0.011,
        baseline_u=0.00035,
        intervention_k=0.00015,
        intervention_d=0.017,
        intervention_u=0.00035,
    ),
    "desert_flashflood_route": CaseSpec(
        case_id="desert_flashflood_route",
        title="사막 협곡 노선: 돌발홍수와 계절 운영",
        region="건조 와디·협곡 유산권",
        real_world_anchor="페트라·와디럼형 돌발홍수 관리 맥락",
        narrative=(
            "평소 건조한 협곡이더라도 단시간 집중강우 시 급격한 홍수파가 발생해 "
            "트레킹·유산해설 노선의 안전성이 크게 흔들린다."
        ),
        guiding_question="저빈도-고충격 위험을 반영한 협곡 노선 운영 기준은 무엇인가?",
        stakeholders="로컬 가이드, 유산관리기관, 방문객, 긴급대응조직",
        lesson_focus="건조지 재난의 시간집중성, 경보기반 접근통제, 대체노선 설계",
        learning_objectives=[
            "건조지역에서도 홍수위험이 큰 이유를 설명한다.",
            "경보·강우 임계값 기반 접근정책을 설계한다.",
            "일상운영과 비상운영의 차이를 정책으로 제시한다.",
        ],
        classroom_prompts=[
            "관광객에게 임계값 경보를 어떻게 전달할 것인가?",
            "협곡 지형에서 탈출경로가 취약한 구간은 어디인가?",
            "성수기 상품을 어떻게 위험반영형으로 바꿀 것인가?",
        ],
        timeline=[
            TimelineItem("2015-2018", "협곡 트레킹 수요 증가", "협곡 노선 의존도 상승."),
            TimelineItem("2018-2024", "돌발홍수 대피 사건 반복", "비상 프로토콜 중요성 확대."),
            TimelineItem("현재", "위험반영형 일정 운영 전환", "정적 개방 규칙의 한계 노출."),
        ],
        evidence_items=[
            EvidenceItem(
                indicator="돌발홍수 대피·통제 사건",
                value="다회 발생",
                year="2018-2024",
                source="민방위·국제보도 사건 연표",
                note="사건 심각도와 빈도를 함께 해석.",
            ),
            EvidenceItem(
                indicator="강우 집중 패턴",
                value="연강수 대부분이 소수 강한 사건에 집중",
                year="장기 기후평년",
                source="건조지 수문·기후 연구",
                note="평균강수량만으로 위험을 판단하지 않도록 지도.",
            ),
            EvidenceItem(
                indicator="협곡 경로 취약 구조",
                value="좁은 통로와 제한된 탈출경로",
                year="현장 위험평가",
                source="보호구역 안전계획 문서",
                note="지형 형태와 대피전략을 직접 연결.",
            ),
        ],
        source_notes=[
            "학생이 반드시 노출시간과 지형구조를 함께 쓰도록 지도하세요.",
            "정책결론에는 취소·우회 시 경제적 영향도 포함하세요.",
        ],
        policy_options=[
            PolicyOption(
                option_id="A",
                title="기존 운영 유지",
                summary="기본 일정 유지, 상황 발생 시 임시 통제.",
                expected_effect="운영 단순성과 마케팅 안정성.",
                tradeoff="극한사건 시 노출 위험이 큼.",
            ),
            PolicyOption(
                option_id="B",
                title="예보 연동 접근통제",
                summary="강우·경보 임계값 기반 사전 통제와 대체코스 동시 운영.",
                expected_effect="인명 위험 감소와 대응 예측 가능성 향상.",
                tradeoff="운영 복잡도 증가와 일부 취소 손실.",
            ),
        ],
        baseline_label="기존 운영 유지 시나리오",
        intervention_label="예보 연동 접근통제 시나리오",
        research_landform="wadi",
        render_landform_type="arid",
        research_grid_size=120,
        research_stage=1.0,
        research_cell_size=20.0,
        climate_month=11,
        climate_mode="real",
        baseline_k=0.00020,
        baseline_d=0.010,
        baseline_u=0.00012,
        intervention_k=0.00012,
        intervention_d=0.018,
        intervention_u=0.00012,
    ),
}


REAL_CASE_CARDS: Dict[str, List[RealCaseCard]] = {
    "delta_overtourism": [
        RealCaseCard(
            title="베네치아 접근기여금(혼잡 관리 실험)",
            location="이탈리아 베네치아",
            period="2024-현재",
            key_point="도시 접근료/예약 기반의 방문량 조절이 관광혼잡 완화 정책으로 실제 시행됨.",
            classroom_use="수용력 관리 정책(A/B) 비교 시, '접근 통제' 시나리오의 현실 근거로 연결.",
            source_name="Comune di Venezia - Access Fee",
            source_url="https://cda.ve.it/en/",
        ),
        RealCaseCard(
            title="델타·저지대 복합위험(해수면+지반+습지)",
            location="전세계 연안 델타 일반",
            period="장기 추세",
            key_point="저지대 델타는 상대적 해수면 상승과 토지이용 압력의 복합위험이 커짐.",
            classroom_use="지형 변화 결과를 기후·재난 맥락으로 확장하는 근거문장 작성에 활용.",
            source_name="IPCC AR6 Synthesis Report",
            source_url="https://www.ipcc.ch/report/ar6/syr/",
        ),
    ],
    "coastal_retreat": [
        RealCaseCard(
            title="Shoreline Management Plan(해안선 관리계획)",
            location="영국 연안",
            period="지속 운영",
            key_point="구간별로 보호/후퇴/적응 전략을 분리해 중장기 해안정책을 설계함.",
            classroom_use="한 해안에서 '전 구간 방어'가 아닌 구간별 정책 조합 논리 훈련에 활용.",
            source_name="UK Government - Shoreline management plans",
            source_url="https://www.gov.uk/government/publications/shoreline-management-plans",
        ),
        RealCaseCard(
            title="Coastal Change Hazards",
            location="미국 연안",
            period="지속 모니터링",
            key_point="해안 침식/폭풍/해수면 변화의 결합 위험을 관측·지도로 관리함.",
            classroom_use="차이맵 해석 결과를 '위험구역 지도화' 활동과 연결.",
            source_name="USGS Coastal Change Hazards",
            source_url=(
                "https://www.usgs.gov/programs/coastal-and-marine-hazards-and-resources-program/"
                "coastal-change-hazards"
            ),
        ),
    ],
    "fjord_climate_risk": [
        RealCaseCard(
            title="Geirangerfjord/Nærøyfjord 세계유산 관리",
            location="노르웨이 피오르드",
            period="2005-현재",
            key_point="경관 보전과 관광 이용을 동시에 다루는 대표적인 피오르드 관리 사례.",
            classroom_use="경관가치 보전과 이동/접근 정책의 충돌을 토론 과제로 전환.",
            source_name="UNESCO WHC 1195",
            source_url="https://whc.unesco.org/en/list/1195/",
        ),
        RealCaseCard(
            title="빙권-해양 변화와 연안 위험",
            location="고위도 해안 전반",
            period="장기 추세",
            key_point="빙권 변화와 해안 영향의 연계가 고위도 지역 의사결정에 핵심 변수로 작동.",
            classroom_use="기후 불확실성을 포함한 정책 메모(CER의 limitation) 작성에 활용.",
            source_name="IPCC Special Report on the Ocean and Cryosphere",
            source_url="https://www.ipcc.ch/srocc/",
        ),
    ],
    "karst_overtourism": [
        RealCaseCard(
            title="South China Karst 보호관리",
            location="중국 남부 카르스트",
            period="2007-현재",
            key_point="세계유산 카르스트 지형에서 보전과 이용의 균형 관리가 지속적으로 요구됨.",
            classroom_use="관람 동선 분산/핫스팟 통제 전략의 필요성 근거로 활용.",
            source_name="UNESCO WHC 1248",
            source_url="https://whc.unesco.org/en/list/1248/",
        ),
        RealCaseCard(
            title="Ha Long Bay 관광·보전 병행",
            location="베트남 하롱베이",
            period="1994-현재",
            key_point="자연유산 경관 보전과 대규모 방문객 관리가 동시에 요구되는 대표 사례.",
            classroom_use="수용력·보전·지역경제를 함께 고려한 정책 타협안 설계에 활용.",
            source_name="UNESCO WHC 672",
            source_url="https://whc.unesco.org/en/list/672/",
        ),
    ],
    "volcanic_geotourism": [
        RealCaseCard(
            title="화산활동 단계별 위험 정보 제공",
            location="미국·전세계 화산대",
            period="지속 운영",
            key_point="관측 단계와 경보체계를 기반으로 접근제한/개방 판단이 이루어짐.",
            classroom_use="A/B 정책 비교에서 '동적 접근 통제' 시나리오의 기준 틀로 활용.",
            source_name="USGS Volcano Hazards Program",
            source_url="https://www.usgs.gov/programs/VHP",
        ),
        RealCaseCard(
            title="국립공원 화산지대 현장 운영",
            location="하와이 화산 국립공원",
            period="지속 운영",
            key_point="활동성·기상·탐방 안전정보에 따라 탐방구간을 유동적으로 관리.",
            classroom_use="관광가치와 안전가치의 충돌을 실제 운영규칙으로 비교 분석.",
            source_name="NPS Hawaii Volcanoes National Park",
            source_url="https://www.nps.gov/havo/index.htm",
        ),
    ],
    "desert_flashflood_route": [
        RealCaseCard(
            title="Flash Flood Warning 기반 통제",
            location="건조 협곡/와디 지역 일반",
            period="지속 운영",
            key_point="평균 강수량보다 '짧은 시간 집중강우' 경보가 운영 의사결정에 더 중요함.",
            classroom_use="임계값 기반 출입통제 규칙을 설계하는 활동의 근거 자료로 활용.",
            source_name="NOAA Flash Flood Safety",
            source_url="https://www.weather.gov/safety/flood-flash",
        ),
        RealCaseCard(
            title="협곡형 지형의 대피·안전 가이드",
            location="미국 국립공원 협곡 구간",
            period="지속 운영",
            key_point="좁은 지형 통로에서는 경보 수신·대피동선·시간창 관리가 핵심.",
            classroom_use="정책안 비교 시 '사전 통제 vs 사후 대응' 비용과 위험을 계량 비교.",
            source_name="NPS Flash Flood Safety",
            source_url="https://www.nps.gov/articles/flash-flood-safety.htm",
        ),
    ],
}


def list_case_ids() -> List[str]:
    return list(CASE_LIBRARY.keys())


def get_case(case_id: str) -> CaseSpec:
    if case_id not in CASE_LIBRARY:
        raise KeyError(f"Unknown case_id: {case_id}")
    return CASE_LIBRARY[case_id]


def title_map() -> Dict[str, str]:
    return {case_id: spec.title for case_id, spec in CASE_LIBRARY.items()}


def get_real_case_cards(case_id: str) -> List[RealCaseCard]:
    return REAL_CASE_CARDS.get(case_id, [])
