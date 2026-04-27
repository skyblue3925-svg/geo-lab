# Telegram Daily Brief Setup

## 목적

매일 정해진 시간에 Geo-lab 위키를 읽고:

1. Obsidian 보고서를 `knowledge/wiki/syntheses/daily-briefs/` 아래에 남기고
2. 최신 포인터 note를 `knowledge/wiki/syntheses/Daily Brief Latest.md` 에 갱신하고
3. 요약본을 Telegram 으로 보내기 위한 설정 문서다.

## 관련 파일

- `scripts/publish_daily_brief.py`
- `.env.example`
- `knowledge/wiki/syntheses/Daily Brief Latest.md`
- `knowledge/wiki/syntheses/daily-briefs/`

## Telegram 준비

1. Telegram 에서 `@BotFather` 로 새 bot을 만든다.
2. 발급된 bot token을 복사한다.
3. 메세지를 받을 개인 chat 또는 그룹 chat의 `chat_id` 를 확인한다.
4. 설정을 어디에 둘지 정한다.

### 방식 A. 이 repo에서만 쓸 때

repo root에 `.env` 파일을 만들고 아래 값을 넣는다.

```env
TELEGRAM_BOT_TOKEN=123456789:example-token
TELEGRAM_CHAT_ID=123456789
```

### 방식 B. 여러 Obsidian vault에서 공용으로 쓸 때

`C:\Users\HANSOL\.codex\telegram-daily-brief.env` 파일을 만들고 아래 값을 넣는다.

```env
TELEGRAM_BOT_TOKEN=123456789:example-token
TELEGRAM_CHAT_ID=123456789
```

이 방식이면 다른 vault repo에서도 같은 스크립트를 쓸 때 별도 `.env` 없이 공용 Telegram 설정을 재사용할 수 있다.

### 우선순위

값은 아래 순서로 읽는다.

1. OS 환경변수
2. repo root `.env`
3. `C:\Users\HANSOL\.codex\telegram-daily-brief.env`

즉, 공용 파일을 기본으로 두고 특정 repo에서만 다른 chat으로 보내고 싶으면 그 repo의 `.env` 로 덮어쓸 수 있다.

## 동작 방식

- 자동화 또는 수동 작업이 먼저 daily brief 본문 markdown 파일과 Telegram 요약 텍스트 파일을 만든다.
- 그 다음 아래 명령으로 보고서를 publish 한다.

```powershell
C:\Users\HANSOL\AppData\Local\Programs\Python\Python311\python.exe scripts\publish_daily_brief.py --report-file output\daily-brief-report.md --summary-file output\daily-brief-summary.txt
```

- 이 스크립트는:
  - 날짜별 note를 `knowledge/wiki/syntheses/daily-briefs/YYYY-MM-DD Daily Brief.md` 에 저장한다.
  - 최신 note 포인터를 `knowledge/wiki/syntheses/Daily Brief Latest.md` 에 덮어쓴다.
  - Telegram 값이 있으면 요약본을 Telegram 으로 보낸다.
  - env 값이 없으면 note만 저장하고 Telegram 전송은 건너뛴다.

## PowerShell로 빠르게 파일 만들기

### 공용 파일 만들기

```powershell
@"
TELEGRAM_BOT_TOKEN=여기에_봇_토큰
TELEGRAM_CHAT_ID=여기에_채팅_ID
"@ | Set-Content -Path "$HOME\.codex\telegram-daily-brief.env" -Encoding utf8
```

### 이 repo 전용 `.env` 만들기

```powershell
@"
TELEGRAM_BOT_TOKEN=여기에_봇_토큰
TELEGRAM_CHAT_ID=여기에_채팅_ID
"@ | Set-Content -Path ".env" -Encoding utf8
```

## 권장 자동화 내용

- `[$wiki-snapshot](C:/Users/HANSOL/OneDrive/Desktop/Geo-lab/knowledge/skills/wiki-snapshot/SKILL.md)` 실행
- `[$wiki-sync](C:/Users/HANSOL/OneDrive/Desktop/Geo-lab/knowledge/skills/wiki-sync/SKILL.md)` 실행
- 전체 보고서 본문 생성
- Telegram 요약본 생성
- `scripts/publish_daily_brief.py` 실행
