"""
🎓 Geo-Lab Learning Interactives

"AI가 학습 스펙을 제안하고, 교사가 검수하고, 검증된 지형 엔진이 렌더링한다."

구글 리서치의 learning interactives(생성형 UI로 교사 맞춤 연습 활동 생성)에서
학습 구조(학습목표 → 단계 → 과제 → 힌트 → 피드백 → 풀이)를 가져오되,
시뮬레이션 본체는 LLM이 아니라 engine/ideal_landforms.py 의 검증된 생성기를 쓴다.

구성:
- schema.py   : 스펙(JSON) 형식 정의와 검증
- bridge.py   : 스펙의 landform 키 → 엔진 생성기 호출 (고도 + 메타데이터)
- checks.py   : 메타데이터 기반 과제 판정 (예: 우각호가 형성되었는가)
- specs/      : 교사 검수를 거친 스펙 JSON 모음
"""
from .schema import SPEC_VERSION, validate_spec, load_spec, list_specs, spec_to_json
from .bridge import generate_stage, available_landforms
from .checks import evaluate_check

__all__ = [
    "SPEC_VERSION",
    "validate_spec",
    "load_spec",
    "list_specs",
    "spec_to_json",
    "generate_stage",
    "available_landforms",
    "evaluate_check",
]
