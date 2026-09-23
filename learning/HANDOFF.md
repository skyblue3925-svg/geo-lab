# 인수인계: 학습 모드 (Learning Interactives) 초안

- 브랜치: `claude/geolab-project-review-qwgvq0`
- PR: https://github.com/skyblue3925-svg/geo-lab/pull/2 (드래프트, 리뷰 없음)
- 기준 브랜치: `main` (충돌 없음)

## 무엇을, 왜 만들었나

구글 리서치의 *learning interactives* 글을 보고 시작했다. 그 글은 교사가 요청하면 생성형 UI 로 맞춤 연습 활동을 만들고 교사가 검수하는 흐름을 제시한다.
Geo-Lab 에는 검증된 지형 생성기 43종이 이미 있으므로, **시뮬레이션은 LLM 에게 맡기지 않는다**.
LLM 은 학습 스펙(JSON)만 제안하고, 교사가 검수한 스펙을 기존 엔진이 렌더링한다.

설계 상세, 스펙 형식, 스펙 추가 절차는 `learning/README.md` 에 있다.

## 현재 상태

| 항목 | 상태 |
|------|------|
| 스펙 형식과 검증기 | 완료 (`learning/schema.py`) |
| 엔진 연결과 판정기 | 완료 (`learning/bridge.py`, `learning/checks.py`) |
| 스펙 4종 | 선상지, 자유곡류, 해안절벽, 리아스 해안 |
| 판정 키 | 모든 지형에 공통값 4개, 선상지·리아스 해안 전용 키 추가 |
| 학습 페이지 | 학생 탭, 교사용 탭 (`pages/5_🎓_Learn.py`) |
| 유닛 테스트 | 통과 (생성기 전체 스모크 테스트 포함) |
| 페이지 흐름 테스트 | 통과 (`tests/apptest_learn_flow.py`) |
| CI | `Cloudflare Pages` 만 실패. 이 PR 과 무관 (아래) |

## 검증 방법

```bash
pip install -r requirements.txt
python -m unittest tests.test_learning_specs tests.test_script_engine tests.test_generators_smoke
python tests/apptest_learn_flow.py      # 끝에 "ALL OK" 가 나와야 함
streamlit run app.py                    # 사이드바 '🎓 Learn' 페이지
```

## 알려진 문제

- **Cloudflare Pages 체크 실패.** 저장소에 Cloudflare 빌드 설정이 없고, 4월에 만든 PR #1 에서도 똑같이 실패한다.
  Streamlit 앱이라 정적 빌드 대상이 아니다. 저장소 소유자가 Cloudflare Pages 의 GitHub 연동을 해제하면 사라진다. PR 에 근거를 코멘트로 남겨 두었다.
- **matplotlib 한글 폰트 경고.** 로컬 테스트 환경에 한글 폰트가 없어 그래프 제목이 네모로 보인다. 기존 갤러리 페이지도 같은 상황이다.
- **`app/pages/` 복제본 없음.** 갤러리는 `pages/` 와 `app/pages/` 두 곳에 있지만 학습 페이지는 `pages/` 에만 추가했다. HF Spaces 진입점이 `app.py` 라서 `pages/` 만으로 동작한다.

## 다음 작업 (우선순위 순)

1. **교사 1~2명과 선상지 활동을 실제로 돌려 본다.** 코드보다 스펙 내용과 난이도 피드백이 먼저 필요하다.
2. **남은 지형에 전용 판정 키를 붙인다.** 공통값(`relief` 등)으로 대부분 판정할 수 있게 됐다.
   곡류(`meander`), 버섯바위, 해식아치, 페디먼트처럼 공통값도 단계에 따라 거의 변하지 않는 지형이 남았다.
   교사용 탭 3) 에서 지형을 고르면 쓸 수 있는 키와 단계별 값이 보인다.
3. **스펙을 늘린다.** 교사용 탭 3) 의 프롬프트로 초안을 받고, 2) 에서 검증하고, 학습 탭에서 직접 풀어 본 뒤 `learning/specs/` 에 넣는다.
   `tests/test_learning_specs.py` 가 새 스펙도 자동으로 검사한다.
4. **(예정) 자연재해 단원.** 사용자 요청: 네팔처럼 빙하가 녹아 생기는 산사태·홍수를 다뤄 보고 싶다.
   후보는 빙하호 범람(GLOF)과 산사태 연쇄다. 빙하 후퇴 → 모레인이 막은 빙하호 확대 → 모레인 붕괴 → 홍수·토석류.
   재료는 이미 엔진에 있다. `engine/glacier.py` 의 `GlacierKernel` (빙하 성장·후퇴·모레인 퇴적)과
   `engine/mass_movement.py` 의 `MassMovementKernel` (임계 경사를 넘는 사면의 산사태)이다.
   다만 둘 다 이상적 지형 갤러리나 학습 모드에 연결돼 있지 않다.
   실제 사건을 수업 소재로 쓸 때는 날짜·피해 규모를 신뢰할 만한 보도로 먼저 확인한다.
5. **LLM 호출을 앱 안에 넣을지 결정한다.** 지금은 API 키가 필요 없도록 프롬프트 복사 방식이다.
6. **학습 기록을 저장할지 결정한다.** 지금은 세션에만 남는다. 필요하면 방문자 카운터처럼 Supabase 에 붙일 수 있다.

## 건드릴 때 주의할 점

- 슬라이더 과제는 **범위 시작에서는 실패하고 끝에서는 통과해야** 한다. 테스트가 이것을 강제한다. 시작부터 통과하면 학생이 슬라이더를 움직일 이유가 없다.
- 판정 키는 **해상도와 무관한 값**을 써야 한다. 일부 생성기는 폭을 격자 칸 수로 그려 `water_fraction` 이 해상도에 따라 달라진다.
  테스트가 번들 스펙의 슬라이더 통과 시점을 해상도 40·60·100 에서 비교한다.
- 해안절벽은 애니메이션 레지스트리의 함수가 메타데이터를 돌려주지 않는다. 그래서 스펙에 `"generator": "create_coastal_cliff"` 를 지정했다.
- 교사용 탭의 검증 버튼은 `on_click` 콜백을 쓴다. 본문에서 처리하면 사이드바 목록이 한 번 늦게 갱신된다.
