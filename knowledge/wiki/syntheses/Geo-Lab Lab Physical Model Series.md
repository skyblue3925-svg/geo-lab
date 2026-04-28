---
id: geo-lab-lab-physical-model-series
type: synthesis
layer: curated
status: active
created: 2026-04-27
updated: 2026-04-27
tags:
  - terrain-lab
  - physical-model
  - geomorphology
aliases:
  - Lab Physical Model Series
---

# Geo-Lab Lab Physical Model Series

## 현재 결정

Lab의 장기 방향은 지형별 전용 코드를 계속 늘리는 것이 아니라, 내적·외적 작용 모듈을 공통 물리엔진으로 쌓고 지형은 초기조건과 프리셋으로 다루는 것이다. 학생용 GIF 갤러리는 설명용 산출물이고, Lab은 조작 가능한 지형 형성 모델로 분리한다.

## 현재 구현

- `projects/terrain-lab/src/app/services/geomorphic_engine.py`가 공통 엔진의 핵심이다.
- `projects/terrain-lab/src/app/services/terrain_physics_lab.py`가 Lab 시나리오, 이론 설명, UI용 메타데이터를 묶는다.
- 2026-04-27 작업에서 `ForceModuleSpec` 레지스트리를 추가했다.
- Lab 화면은 선택 지형에 대해 적용되는 작용 모듈, 대표식, 교육적 의미, 출력 필드를 표시한다.

## 작용 모듈 기준

- 하천 침식·운반: `E = K A^m S^n`
- 사면 확산: `∂z/∂t = D∇²z`
- 파랑·해안 작용: 해수면, 파랑 에너지, 퇴적물 수지 기반 해안선 후퇴와 퇴적
- 빙하 침식·퇴적: 빙하 두께와 속도 기반 바닥 침식 및 모레인 퇴적
- 바람·모래 이동: 풍속, 모래 공급, 풍상면 침식, 풍하면 퇴적
- 화산체 성장: 분출률, 점성, 냉각 제한 확산
- 폭발성 화산 작용: 폭발 에너지, 마그마-지하수 접촉, 화산쇄설물 퇴적
- 카르스트·지하수: 물 공급, 암석 용해도, 균열 밀도, 지하 배수
- 융기·침강 기준면: 구조운동과 해수면/기준면 조건

## 다음 구현 단위

1. Lab UI에서 학생용/교사용/연구자용 모드를 명확히 나눈다.
2. 재생 방식은 자동 애니메이션보다 수동 단계 이동을 기본으로 두고, 카메라 상태가 유지되는 실험 흐름을 우선한다.
3. 연구자용 DEM 입력은 업로드, 전처리, 초기조건 변환, 관측 DEM과 모델 DEM의 차이 계산 흐름부터 설계한다.
4. 각 작용 모듈은 출력 필드 존재 여부뿐 아니라 방향성, 민감도, 지형별 비활성 조건을 테스트한다.

## 검증 기준

- Lab 공통 출력 계약: `history`, `times`, `process_history`, `stats_history`, `kernel`, `config` 또는 `parameters`
- 대표 지형은 계속 `geomorphic_engine_v2`로 라우팅
- 지형별 프리셋은 초기 표면과 파라미터 조합만 담당
- 작용 모듈은 `ForceModuleSpec`와 엔진 출력 필드가 함께 유지되어야 한다.
