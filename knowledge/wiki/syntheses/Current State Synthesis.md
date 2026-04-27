---
id: current-state-synthesis
type: synthesis
layer: curated
status: active
created: 2026-04-12
updated: 2026-04-12
tags:
  - synthesis
  - state
aliases:
  - current-state
---

# Current State Synthesis

## 상위 진단

현재 Geo-lab은 `고등학교 수업 우선 Streamlit core` 를 중심에 두되, 그 주변에 `Gallery / Overview / Climate / Higher Ed` 같은 교육용 안내 및 확장 surface와 `Koppen Climate Lab`, `School Neighborhood GIS` 같은 별도 앱을 함께 운영하는 상태다.

## 확인된 현재 상태

- `app.py` 가 현재 canonical Streamlit entrypoint고, 메인 진입은 `app/home_view.py` 로 구성된다.
- `pages/` 는 현재 8개 surface를 가진다.
  - Overview
  - Gallery
  - Lab
  - Research
  - Climate
  - Case Mode
  - Higher Ed
  - High School Geography
- Streamlit core는 이제 최소 8개의 2차 줄기로 구조 파악이 가능하다.
  - [[Geo-Lab Overview Guide]]
  - [[Geo-Lab Gallery]]
  - [[Geo-Lab Lab]]
  - [[Geo-Lab Research Lab]]
  - [[Geo-Lab Climate Lab]]
  - [[Geo-Lab Case Mode]]
  - [[Geo-Lab High School Geography Atlas]]
  - [[Geo-Lab Higher Ed Portal]]
- `engine/` 는 ideal geometry, SimpleLEM, unified EarthSystem, river / climate / analysis 모듈이 공존하는 폭넓은 엔진 층이다.
- `apps/` 아래의 두 side app은 Streamlit core와 같은 repo 안에 있지만 배포 및 운영의 결이 일부 다르다.
- `knowledge/` 는 baseline, snapshot, map, current-shape, concept note까지 갖춘 최소 LLM wiki 골격을 확보했다.

## 현재 중요한 개념 축

- [[합성 DEM과 관측 DEM]]
- [[Provenance와 해석 경계]]
- [[Session-State Handoff]]

이 세 축은 Gallery, Lab, Research, Climate, Case Mode 사이를 해석할 때 반복적으로 등장한다.

## 구조적 긴장

- 현재 shell은 다층 surface 체계로 진화했지만, 일부 과거 simulator 파일과 서사가 여전히 공존한다.
- README가 설명하는 프로젝트 범위보다 현재 working tree의 실제 표면적이 더 넓다.
- session-state handoff가 실용적이지만, provenance 설명이 약하면 사용자가 합성 결과와 관측 결과를 같은 수준의 사실처럼 읽을 위험이 있다.
- dirty worktree 상태라 최신 commit history만으로는 current shape를 충분히 설명할 수 없다.

## 현재 작업의 해석 기준

- 제품 의도는 README와 docs를 먼저 따른다.
- 현재 구현 상태는 코드와 working tree를 우선한다.
- 변화 추세는 recent git log와 snapshot note를 보조 근거로 쓴다.
- raw source와 curated 해석을 분리해 note를 읽는다.

## 우선 canonical note

- [[Project Map]]
- [[Geo-Lab Streamlit Surface Map]]
- [[Latest Repository Snapshot]]
- [[Geo-Lab Streamlit App Current Shape]]
- [[Terrain Engine Current Shape]]
- [[School Neighborhood GIS Current Shape]]
- [[Koppen Climate Lab Current Shape]]

## 다음 갱신 후보

- Streamlit surface 간 handoff를 더 세밀하게 분리한 flow map
- test 및 deploy 축의 map note
- docs source digest를 `수업`, `운영`, `배포`, `runbook` 기준으로 재분류
