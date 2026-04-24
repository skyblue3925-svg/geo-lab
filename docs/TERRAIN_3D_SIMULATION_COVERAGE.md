# 지형 3D 시뮬레이션 커버리지

작성일: 2026-04-24

## 기준

Animation Studio의 3D 뷰어는 모든 지형에 대해 같은 payload 계약을 사용한다. 다만 물리 정확도는 두 단계로 구분한다.

- `direct_simple_lem`: SimpleLEM의 현 물리장과 지형군이 직접 맞는다. 하천 침식, 퇴적, 해안 침식, 빙하 침식, 카르스트 용해, 바람 작용, 화산 분출처럼 엔진 안에 대응 과정이 있다.
- `process_proxy`: 지형의 이상 표면은 해당 지형 generator를 쓰되, 시간 변화 물리장은 가장 가까운 대표 과정으로 근사한다. 예를 들어 해식 아치는 해식애의 해안 침식장, 호른은 U자곡의 빙하 침식장, 메사/뷰트는 건조지 차별 침식 근사장을 사용한다.

이 구분은 UI의 3D 데이터 설명에 노출한다. 따라서 전 지형을 볼 수는 있지만, `process_proxy`는 연구용 수치모델이 아니라 고등학교 수업에서 지배 작용과 형태 변화를 연결하는 시각화로 봐야 한다.

## 38개 매핑

| 수준 | 지형 |
| --- | --- |
| `direct_simple_lem` | `alluvial_fan`, `barchan`, `coastal_cliff`, `delta`, `fjord`, `free_meander`, `karst_doline`, `pediment`, `stratovolcano`, `u_valley`, `v_valley` |
| `process_proxy` | `arcuate_delta`, `arete`, `bird_foot_delta`, `braided_river`, `caldera`, `cirque`, `coastal_dune`, `crater_lake`, `cuspate_delta`, `estuary`, `horn`, `karren`, `lava_plateau`, `mesa_butte`, `pedestal_rock`, `playa`, `ria_coast`, `sea_arch`, `shield_volcano`, `spit_lagoon`, `star_dune`, `tombolo`, `tower_karst`, `transverse_dune`, `uvala`, `wadi`, `waterfall` |

## 다음 보강 순서

1. 하천/삼각주 계열: `braided_river`, `waterfall`, 삼각주 변형 3종의 퇴적장과 유로 분기장을 별도 계산한다.
2. 해안 계열: `sea_arch`, `spit_lagoon`, `tombolo`, `ria_coast`, `estuary`에 파랑 방향, 연안류, 해수면 침수장을 분리한다.
3. 빙하 계열: `cirque`, `arete`, `horn`에 빙하 방향장을 여러 축으로 나누고 능선 sharpen field를 추가한다.
4. 화산 계열: `shield_volcano`, `caldera`, `crater_lake`, `lava_plateau`에 분출, 함몰, 물 채움 단계를 분리한다.
5. 구조/차별 침식 계열: `mesa_butte`, `pedestal_rock`에 암석 경도 mask와 하부 집중 침식장을 추가한다.
