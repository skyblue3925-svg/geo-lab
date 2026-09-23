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
| 스펙 3종 | 선상지, 자유곡류, 해안절벽 |
| 학습 페이지 | 학생 탭, 교사용 탭 (`pages/5_🎓_Learn.py`) |
| 유닛 테스트 | 통과 |
| 페이지 흐름 테스트 | 통과 (`tests/apptest_learn_flow.py`) |
| CI | `Cloudflare Pages` 만 실패. 이 PR 과 무관 (아래) |

## 검증 방법

```bash
pip install -r requirements.txt
python -m unittest tests.test_learning_specs tests.test_script_engine
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
2. **판정 키를 엔진에 추가한다.** 메타데이터를 지원하는 지형은 43종 중 28종뿐이다.
   지형마다 `oxbow_formed` 같은 "학생이 도달할 상태" 키를 한두 개씩 붙이면 슬라이더 과제를 만들 수 있다.
   선상지는 `zone_mask` 가 모든 단계에서 세 존을 다 포함해 판정 기준으로 쓸 수 없다. `fan_extent` 같은 0~1 값이 필요하다.
3. **스펙을 늘린다.** 교사용 탭 3) 의 프롬프트로 초안을 받고, 2) 에서 검증하고, 학습 탭에서 직접 풀어 본 뒤 `learning/specs/` 에 넣는다.
   `tests/test_learning_specs.py` 가 새 스펙도 자동으로 검사한다.
4. **LLM 호출을 앱 안에 넣을지 결정한다.** 지금은 API 키가 필요 없도록 프롬프트 복사 방식이다.
5. **학습 기록을 저장할지 결정한다.** 지금은 세션에만 남는다. 필요하면 방문자 카운터처럼 Supabase 에 붙일 수 있다.

## 건드릴 때 주의할 점

- 슬라이더 과제는 **범위 시작에서는 실패하고 끝에서는 통과해야** 한다. 테스트가 이것을 강제한다. 시작부터 통과하면 학생이 슬라이더를 움직일 이유가 없다.
- 해안절벽은 애니메이션 레지스트리의 함수가 메타데이터를 돌려주지 않는다. 그래서 스펙에 `"generator": "create_coastal_cliff"` 를 지정했다.
- 교사용 탭의 검증 버튼은 `on_click` 콜백을 쓴다. 본문에서 처리하면 사이드바 목록이 한 번 늦게 갱신된다.
