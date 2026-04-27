# Geo-lab 지형 이미지 제작 오케스트레이션
이 문서는 `docs/TERRAIN_GPT_IMAGE_PROMPT_PLAYBOOK.md`를 실제 이미지 제작과 애니메이션 제작으로 넘기기 위한 팀 운영 패킷이다. 현재 저장소는 큰 dirty worktree 상태이므로, 이번 단계에서는 코드 변경을 피하고 문서와 산출물 경로를 분리한다.

## 이번 실행에서 구성한 병렬 팀

서브에이전트는 지형군 기준으로 나누었다.

| 팀 | 담당 범위 | 산출물 |
| --- | --- | --- |
| River/Delta Team | V자곡, 폭포, 선상지, 망상하천, 곡류하천, 삼각주 계열, 에스추어리 | 10개 지형의 내적/외적 작용, 4단계 키프레임, 4패널 이미지 프롬프트 |
| Glacial/Volcanic Team | U자곡, 권곡, 호른, 아레트, 피오르, 순상화산, 성층화산, 칼데라, 화구호, 용암대지 | 10개 지형의 내적/외적 작용, 4단계 키프레임, 4패널 이미지 프롬프트 |
| Karst/Arid/Coastal Team | 돌리네, 우발라, 탑 카르스트, 카렌, 사구·건조·해안 지형 | 18개 지형의 내적/외적 작용, 4단계 키프레임, 4패널 이미지 프롬프트 |
| Image QA/Orchestration Team | 공통 프롬프트 문법, 오버레이 규칙, 병렬 제작 로스터, 품질 게이트 | 통합 제작 규칙과 검수 기준 |

통합자는 네 팀 결과를 `docs/TERRAIN_GPT_IMAGE_PROMPT_PLAYBOOK.md`와 이 문서로 병합한다.

## 모델 사용 기준

API 직접 생성 경로에서는 OpenAI 공식 모델명 `gpt-image-2`를 사용한다.

권장 기본값:

| 단계 | model | size | quality | 목적 |
| --- | --- | --- | --- | --- |
| draft | `gpt-image-2` | `2048x1152` | `low` 또는 `medium` | 구도와 과정 오류 확인 |
| classroom final | `gpt-image-2` | `2048x1152` | `high` | 수업용 4패널 스토리보드 |
| app thumbnail | `gpt-image-2` | `1536x1024` | `medium` | Gallery/Atlas 썸네일 |

주의:

- `gpt-image-2`는 투명 배경을 지원하지 않는다고 공식 문서에 명시되어 있으므로, 앱 합성용 투명 PNG가 필요하면 별도 후처리나 다른 모델 경로를 써야 한다.
- 긴 한국어 문장을 이미지 안에 많이 넣지 않는다. GPT Image 모델도 텍스트 배치와 정확성에는 한계가 있으므로 라벨은 짧게 유지한다.
- 4패널 이미지의 라벨은 앱에서 HTML/Plotly overlay로 다시 올릴 수 있게, 이미지 자체에는 최소 텍스트만 넣는다.

## 파일 산출물 규칙

실제 이미지 파일을 만들 때는 아래 경로를 쓴다.

```text
output/terrain-animation-assets/
  river_delta/
    v_valley/
      v_valley_storyboard_draft.png
      v_valley_storyboard_final.png
      v_valley_stage_01.png
      v_valley_stage_02.png
      v_valley_stage_03.png
      v_valley_stage_04.png
  glacial_volcanic/
  karst_arid_coastal/
```

이름 규칙:

- 4패널 스토리보드: `{topic_id}_storyboard_{draft|final}.png`
- 개별 키프레임: `{topic_id}_stage_01.png` ~ `{topic_id}_stage_04.png`
- 앱 썸네일: `{topic_id}_thumbnail.png`
- 프롬프트 기록: `{topic_id}_prompt.md`

## 제작 순서

1. 프롬프트 잠금
   - `docs/TERRAIN_GPT_IMAGE_PROMPT_PLAYBOOK.md`에서 대상 지형의 프롬프트를 복사한다.
   - 지형별 오개념 방지 문장을 negative constraints로 함께 넣는다.

2. 저해상도 초안 생성
   - `quality=low` 또는 `quality=medium`으로 먼저 만든다.
   - 장면이 과학적으로 틀리면 프롬프트를 고친 뒤 다시 생성한다.

3. 과학/수업 QA
   - 내적 작용이 직접 원인인지 조건인지 확인한다.
   - 외적 작용의 순서가 실제 형성 과정과 맞는지 확인한다.
   - 학생이 패널 1에서 4로 원인과 결과를 읽을 수 있는지 확인한다.

4. 최종 이미지 생성
   - 수업용 최종본은 `quality=high`로 만든다.
   - 4패널 스토리보드를 먼저 확정하고, 필요한 경우 같은 프롬프트를 패널별로 분해해 개별 키프레임을 만든다.

5. 앱 연결
   - Gallery/High School Geography Atlas에는 스토리보드 또는 썸네일을 연결한다.
   - Lab/Animation Renderer에는 개별 키프레임 또는 GIF/MP4로 연결한다.

## 팀별 작업 패킷

### River/Delta Team

대상:

- `v_valley`
- `waterfall`
- `alluvial_fan`
- `braided_river`
- `free_meander`
- `delta`
- `bird_foot_delta`
- `arcuate_delta`
- `cuspate_delta`
- `estuary`

중점:

- 하천 작용은 `침식`, `운반`, `퇴적`을 장면별로 분리한다.
- 삼각주는 하천 공급과 파랑/조석의 균형을 형태 차이로 보여준다.
- 곡류는 바깥쪽 침식과 안쪽 퇴적을 한 장면에 과밀하게 넣지 않고 단계별로 분리한다.

### Glacial/Volcanic Team

대상:

- `u_valley`
- `cirque`
- `horn`
- `arete`
- `fjord`
- `shield_volcano`
- `stratovolcano`
- `caldera`
- `crater_lake`
- `lava_plateau`

중점:

- 빙하 지형은 내적 작용을 직접 원인보다 고도/산지 조건으로 다룬다.
- U자곡과 피오르는 반드시 `빙하 침식 -> 후속 침수` 순서를 분리한다.
- 화산 지형은 `마그마 성질 -> 분출 양상 -> 화산체 형태`를 순서대로 보여준다.

### Karst/Arid/Coastal Team

대상:

- `karst_doline`
- `uvala`
- `tower_karst`
- `karren`
- `barchan`
- `transverse_dune`
- `star_dune`
- `mesa_butte`
- `wadi`
- `playa`
- `pedestal_rock`
- `pediment`
- `coastal_cliff`
- `spit_lagoon`
- `tombolo`
- `sea_arch`
- `coastal_dune`
- `ria_coast`

중점:

- 카르스트는 표면 변화만이 아니라 지하 배수와 용식을 반드시 보인다.
- 건조 지형은 바람만이 아니라 일시적 폭우와 차별 침식까지 구분한다.
- 해안 지형은 파랑 침식, 연안류 퇴적, 침수 해안을 서로 섞지 않는다.

### Image QA Team

검수 항목:

- 한 패널에 주도 작용이 하나만 있는가.
- 내적 작용과 외적 작용 색상이 섞이지 않는가.
- 지형 이름과 형성 과정이 논리적으로 맞는가.
- 최종 지형만 예쁘고 과정이 비어 있지 않은가.
- 오개념 방지 문장이 이미지에 반영되었는가.

## 품질 게이트

### 과학 품질

- 지형 변화가 실제 작용 순서와 맞아야 한다.
- 내적 작용과 외적 작용을 혼동하면 안 된다.
- 결과 지형만 보이고 과정이 숨겨지면 실패다.
- 한 장면에 여러 원인이 뒤섞여 오해를 만들면 실패다.

### 수업 품질

- 고등학생이 1차 설명 없이도 큰 흐름을 읽을 수 있어야 한다.
- 단계별 차이가 문장으로 설명 가능해야 한다.
- 질문은 결과 암기가 아니라 과정 이해를 물어야 한다.
- 교사용 노트는 학생용 문장을 반복하지 않고 원인을 설명해야 한다.

### 시각 품질

- 배경과 오버레이가 충돌하면 안 된다.
- 카메라가 과하게 움직이면 안 된다.
- 핵심 지형 요소가 프레임에서 잘리면 안 된다.
- 전후 비교가 한눈에 보여야 한다.
- 고채도 요소를 남발하지 않는다.

## 서브에이전트 실행 템플릿

```text
당신은 {team_name} 이미지 제작팀입니다.
대상 지형: {topic_ids}

먼저 아래 자료를 읽으세요.
- AGENTS.md
- docs/TERRAIN_GPT_IMAGE_PROMPT_PLAYBOOK.md
- app/utils/high_school_world_geography.py
- 관련 지형 spec 문서

각 지형별로 아래를 납품하세요.
1. 핵심 학습목표
2. 내적 작용
3. 외적 작용
4. 4단계 키프레임
5. gpt-image-2용 4패널 프롬프트
6. 피해야 할 오개념 2개
7. QA 판정: pass / revise

파일을 수정한다면 본인 팀 ownership 경로만 수정하고, 다른 팀 결과를 되돌리지 마세요.
```
