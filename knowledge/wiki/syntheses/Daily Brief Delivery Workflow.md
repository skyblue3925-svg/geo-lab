---
id: daily-brief-delivery-workflow
type: synthesis
layer: curated
status: active
created: 2026-04-12
updated: 2026-04-12
tags:
  - synthesis
  - automation
  - telegram
aliases:
  - daily-brief-workflow
---

# Daily Brief Delivery Workflow

## 목적

이 note는 Geo-lab 일일 브리프가 어떻게 생성되고 전달되는지 설명한다.

## 출력 경로

- 날짜별 보고서: `knowledge/wiki/syntheses/daily-briefs/YYYY-MM-DD Daily Brief.md`
- 최신 포인터 note: [[Daily Brief Latest]]
- Telegram 요약본: 지정된 chat으로 plain-text 전송

## 입력 축

- [[LLM Wiki Home]]
- [[Current State Synthesis]]
- [[Latest Repository Snapshot]]
- 관련 current-shape / map note

## 실행 흐름

1. `[$wiki-snapshot](C:/Users/HANSOL/OneDrive/Desktop/Geo-lab/knowledge/skills/wiki-snapshot/SKILL.md)` 으로 raw snapshot을 갱신한다.
2. `[$wiki-sync](C:/Users/HANSOL/OneDrive/Desktop/Geo-lab/knowledge/skills/wiki-sync/SKILL.md)` 으로 current-state, current-shape, map note를 맞춘다.
3. 전체 보고서 본문과 Telegram 요약본을 만든다.
4. `scripts/publish_daily_brief.py` 로 Obsidian note를 저장하고 Telegram 으로 요약을 보낸다.

## 운영 규칙

- Telegram 전송이 실패해도 Obsidian 보고서 생성은 먼저 완료되어야 한다.
- Telegram 자격증명은 OS env, repo `.env`, `C:\Users\HANSOL\.codex\telegram-daily-brief.env` 순서의 override 규칙으로 읽는다.
- Telegram 자격증명이 없으면 보고서는 저장하고 전송만 건너뛴다.
- 보고서 본문은 한국어를 기본으로 쓴다.
- 요약본은 짧고 행동 가능한 항목 위주로 쓴다.

## 관련 문서

- [TELEGRAM_DAILY_BRIEF_SETUP.md](C:/Users/HANSOL/OneDrive/Desktop/Geo-lab/docs/TELEGRAM_DAILY_BRIEF_SETUP.md)
- [[Daily Brief Latest]]
