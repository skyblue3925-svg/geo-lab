---
id: concept-synthetic-vs-observed-dem
type: concept
layer: curated
status: seed
created: 2026-04-12
updated: 2026-04-12
tags:
  - concept
  - dem
  - interpretation
aliases:
  - Synthetic DEM vs Observed DEM
---

# 합성 DEM과 관측 DEM

## 핵심 개념

Geo-lab에서는 `합성 DEM` 과 `관측 DEM` 이 같은 분석 UI에 들어올 수 있지만, 해석 강도는 다르게 가져가야 한다.

## 합성 DEM

- 출처: `ideal_landforms`, `SimpleLEM`, Case Mode 시뮬레이션
- 장점: 과정 이해, 비교 실험, 수업 시연에 유리
- 한계: 실제 지형을 직접 재현한 것으로 보면 안 된다

## 관측 DEM

- 출처: 업로드 파일, 외부 측량/격자 데이터
- 장점: 실제 지형 분석과 비교에 적합
- 한계: 해상도, 좌표계, 범위, 전처리 차이가 해석에 큰 영향을 준다

## 위키에서 중요하게 보는 이유

- [[Geo-Lab Research Lab]] 은 두 종류의 DEM을 모두 받는다.
- [[Geo-Lab Case Mode]] 는 실제 지역 앵커와 합성 DEM 실험을 같이 쓴다.
- 따라서 “이 결과가 실제 지형을 말하는가, 학습용 모델을 말하는가” 를 계속 분리해야 한다.

## 관련 note

- [[Geo-Lab Research Lab Current Shape]]
- [[Geo-Lab Case Mode Current Shape]]
- [[Provenance와 해석 경계]]
