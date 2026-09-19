# 🎓 Learning Interactives (학습 모드) 초안

구글 리서치의 *learning interactives*(교사 요청 → 생성형 UI로 맞춤 연습 활동 생성 → 교사 검수)에서
**학습 구조**만 가져오고, **시뮬레이션 본체는 Geo-Lab 의 검증된 지형 엔진**을 그대로 쓴다.

```
교사 주제 요청 ──▶ (LLM) 학습 스펙 JSON 제안 ──▶ 교사 검수·수정 ──▶ 학습 페이지가 렌더링
                                                                  │
                                              engine/ideal_landforms.py (43종, 검증됨)
```

LLM 이 코드를 만들지 않는다. 스펙은 사람이 읽고 고칠 수 있는 JSON 이고, 검증기(`schema.py`)를 통과한
스펙만 학생에게 보인다.

## 구성

| 파일 | 역할 |
|------|------|
| `schema.py` | 스펙 형식 정의(docstring) 와 `validate_spec()` |
| `bridge.py` | `landform` 키 → 엔진 생성기 호출. 고도 배열 + 메타데이터 반환. `_stage` 공통 키 주입 |
| `checks.py` | `slider_target` 과제 판정. 메타데이터 값에 `equals / gte / lte / contains / len_gte / truthy` |
| `specs/*.json` | 검수를 거친 스펙. 파일명 = `id` |
| `pages/5_🎓_Learn.py` | 학습 탭(학생) + 교사용 탭(검수·AI 프롬프트) |
| `tests/test_learning_specs.py` | 스펙 검증, 렌더 가능성, 슬라이더 과제가 "움직여야만" 통과하는지 확인 |

## 한 단계(level)가 학생에게 보이는 순서

1. 안내(`prompt`) 와 해당 단계의 지형 (2D, 3D 버튼, 단계 설명은 엔진 메타데이터에서)
2. 과제
   - `multiple_choice`: 보기 선택 → 정답 확인
   - `slider_target`: 슬라이더로 목표 상태(예: 우각호 형성) 도달 → 그 뒤 객관식이 열림
   - `observe`: 확인 버튼만
3. 계층형 힌트(3단계), 정오답 피드백
4. 두 번 틀리면 풀이(`worked_solution`) 공개, 읽고 넘어갈 수 있음
5. 마지막에 정리, 오개념 목록, 시도·힌트 기록

## 스펙 추가하기

1. 교사용 탭 3) 의 프롬프트를 LLM 에 넣어 초안을 받는다 (또는 `specs/` 의 예시를 복사해 직접 쓴다).
2. 교사용 탭 2) 에 붙여넣고 **검증** → 사이드바에 "(검수 중)" 으로 나타난다.
3. 학습 탭에서 직접 풀어 보며 내용을 검수한다.
4. 통과하면 JSON 을 `learning/specs/<id>.json` 으로 저장하고 `python -m unittest tests.test_learning_specs` 를 돌린다.

`slider_target` 의 판정 키는 지형마다 다르다. 어떤 키를 쓸 수 있는지는 교사용 탭 3) 에서 지형을 고르면 표시된다.
메타데이터가 없는 지형은 `_stage` (형성 단계 0~1) 만 쓸 수 있다.

## 현재 한계와 다음 단계

- **메타데이터 커버리지**: 43종 중 28종만 `return_metadata` 를 지원한다. 나머지는 `_stage` 판정만 가능.
  좋은 판정 키(예: `oxbow_formed`, `stacks_formed`) 를 지형마다 한두 개씩 붙이는 것이 다음 작업.
- **선상지 존 판정**: `zone_mask` 는 어느 단계에서나 세 존이 모두 등장해 판정 기준으로 쓸 수 없었다. 지금은 `_stage ≥ 0.6` 으로 대체.
  `fan_extent` 같은 정규화된 값을 엔진에 추가하면 더 나은 과제를 만들 수 있다.
- **LLM 호출은 아직 수동**: API 키 없이도 쓰도록 프롬프트 복사 방식으로 두었다. 이후 버튼 한 번으로 초안 생성까지 넣을 수 있다.
- **기록 저장 없음**: 진행 상태는 세션에만 있다. 학급 단위 기록이 필요하면 방문자 카운터처럼 Supabase 에 붙일 수 있다.
- **HF Spaces 배포**: 새 페이지는 `pages/` 에만 있다. `app/pages/` 복제본은 만들지 않았다.
