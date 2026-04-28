---
id: multi-vault-wiki-pattern
type: synthesis
layer: curated
status: active
created: 2026-04-12
updated: 2026-04-12
tags:
  - synthesis
  - pattern
  - obsidian
  - telegram
  - automation
aliases:
  - multi-vault-pattern
  - 硫??蹂쇳듃 ?꾪궎 ?⑦꽩
---

# Multi-Vault Wiki Pattern

## 紐⑹쟻

??note??`Geo-lab` ?먯꽌 ?뺤갑??Obsidian + LLM wiki + Telegram daily brief ?댁쁺 ?⑦꽩???ㅻⅨ repo?먮룄 ?댁떇?섍린 ?꾪븳 portable reference??
?ㅼ쓬 ??곸? `Project Archipelago` vault??

## ?듭떖 洹쒖튃

- repo root瑜?Obsidian vault root濡?蹂몃떎.
- `knowledge/raw/` ??immutable source layer濡??붾떎.
- `knowledge/raw/snapshots/` ??committed / working tree瑜?遺꾨━??immutable snapshot layer濡??붾떎.
- `knowledge/wiki/` ??curated layer濡??붾떎.
- 湲곗〈 note 媛깆떊????note ?앹꽦蹂대떎 ?곗꽑?쒕떎.
- durable note瑜?留뚮뱾嫄곕굹 ?ш쾶 諛붽씀硫?`Knowledge Index` ? `Knowledge Log` 瑜?媛숈씠 媛깆떊?쒕떎.
- user-facing wiki prose???쒓뎅??湲곕낯?쇰줈 ?대떎.

## 泥ル궇 理쒖냼 scaffold

- `AGENTS.md`
- `knowledge/LLM Wiki Home.md`
- `knowledge/LLM Wiki Schema.md`
- `knowledge/Knowledge Index.md`
- `knowledge/Knowledge Log.md`
- `knowledge/wiki/sources/repository-baseline.md` ?먮뒗 baseline digest
- `knowledge/wiki/maps/project-map.md`
- `knowledge/wiki/syntheses/current-state.md`
- `knowledge/skills/wiki-snapshot/SKILL.md`
- `knowledge/skills/wiki-sync/SKILL.md`
- `knowledge/skills/wiki-query/SKILL.md`
- `knowledge/skills/wiki-lint/SKILL.md`

## ?댁쁺 ?쒖꽌

1. baseline source note瑜?留뚮뱺??
2. baseline digest瑜?留뚮뱺??
3. project map??留뚮뱺??
4. current-state synthesis瑜?留뚮뱺??
5. ??紐⑤뱢??蹂댁씠硫?entity? current-shape note瑜?seed?쒕떎.
6. ?댄썑?먮뒗 `snapshot ?섍퀬 wiki sync ?댁쨾` 瑜?湲곕낯 ?댁쁺 紐낅졊?쇰줈 ?대떎.

## Snapshot / Sync ?댁꽍 洹쒖튃

- raw snapshot note?먮뒗 command-derived fact留??대떎.
- curated snapshot note?먮뒗 `吏湲??꾪궎媛 臾댁뾿??current濡?蹂쇱?` 瑜??대떎.
- `snapshot ?섍퀬 wiki sync ?댁쨾` ??蹂댄넻 ?꾨옒 ?살씠??
  1. raw snapshot ?앹꽦
  2. latest snapshot digest 媛깆떊
  3. affected current-state, current-shape, map, entity note ?숆린??  4. index / log 諛섏쁺

## Daily Brief ?꾨떖 ?⑦꽩

- ?꾩껜 蹂닿퀬?쒕뒗 Obsidian note濡??④릿??
- 理쒖떊 ?ъ씤??note??`knowledge/wiki/syntheses/Daily Brief Latest.md` 濡??붾떎.
- ?좎쭨蹂??꾩뭅?대툕??`knowledge/wiki/syntheses/daily-briefs/` ?꾨옒???볥뒗??
- Telegram ?먮뒗 吏㏃? ?붿빟蹂몃쭔 蹂대궦??
- 蹂닿퀬????κ낵 Telegram ?꾩넚? 遺꾨━?섍퀬, Telegram ?ㅽ뙣 ?쒖뿉??note ??μ? 癒쇱? ?앸궡???쒕떎.

## Telegram shared config

- 怨듭슜 Telegram ?ㅼ젙 ?뚯씪:
  - `C:\Users\HANSOL\.codex\telegram-daily-brief.env`
- ?뺤떇:

```env
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
```

- ?쎄린 ?곗꽑?쒖쐞:
  1. OS env
  2. repo root `.env`
  3. `C:\Users\HANSOL\.codex\telegram-daily-brief.env`

利? ?щ윭 vault瑜?媛숈? Telegram 梨꾨꼸濡?蹂대궡?ㅻ㈃ shared env瑜?湲곕낯?쇰줈 ?먭퀬, ?뱀젙 repo留??ㅻⅨ 梨꾨꼸???곌퀬 ?띠쓣 ?뚮쭔 repo `.env` 濡?override ?쒕떎.

## ?꾩슂???뚯씪

- `scripts/publish_daily_brief.py`
  - full report瑜?Obsidian note濡???ν븯怨?Telegram summary瑜??꾩넚
- `docs/TELEGRAM_DAILY_BRIEF_SETUP.md`
  - token / chat id / shared env 寃쎈줈 ?ㅻ챸
- `knowledge/wiki/syntheses/Daily Brief Delivery Workflow.md`
  - daily brief ?앹꽦怨??꾨떖 寃쎈줈 ?ㅻ챸

## ?ㅻⅨ repo濡??댁떇????泥댄겕由ъ뒪??
1. repo root瑜?vault root濡??곌쾶 `.obsidian/` ? root 吏꾩엯 note瑜?留욎텣??
2. `knowledge/` scaffold瑜?留뚮뱺??
3. baseline / current-state / project-map / latest snapshot 異뺤쓣 留뚮뱺??
4. `publish_daily_brief.py` ? setup doc瑜??ｋ뒗??
5. shared env 寃쎈줈瑜?洹몃?濡??곌쾶 ?쒕떎.
6. daily brief automation??留뚮뱺??
7. 泥??뚯뒪???꾩넚?쇰줈 Telegram 怨?latest brief note瑜?媛숈씠 寃利앺븳??

## ?ㅻⅨ ?몄뀡??諛붾줈 以??꾨＼?꾪듃

```text
??repo root瑜?Obsidian vault 寃?LLM wiki repo濡?留뚮뱾怨??띕떎.
`knowledge/raw` ??immutable source layer, `knowledge/wiki` ??curated layer濡??댁쁺?댁쨾.
baseline, current-state, project-map, current-shape 泥닿퀎瑜?癒쇱? 留뚮뱾怨? 湲곗〈 note媛 ?덉쑝硫?媛깆떊???곗꽑?댁쨾.
??daily brief ?먮룞?붾룄 遺숈뿬以?
?꾩껜 蹂닿퀬?쒕뒗 Obsidian note濡???ν븯怨? Telegram ?붿빟蹂몄? shared env `C:\Users\HANSOL\.codex\telegram-daily-brief.env` 瑜??쎌뼱 蹂대궡寃??댁쨾.
repo蹂?`.env` 媛 ?덉쑝硫?shared env蹂대떎 ?곗꽑?섍쾶 ?댁쨾.
```

## Archipelago ?곸슜 硫붾え

- `Project Archipelago` ?먮룄 媛숈? shared Telegram env瑜??ъ궗?⑺븷 ???덈떎.
- Geo-lab 履?note ?대쫫??洹몃?濡?蹂듭젣?섏? 留먭퀬, Archipelago ?꾨찓?몄뿉 留욌뒗 baseline / map / current-shape ?대쫫?쇰줈 諛붽씀???몄씠 ?ル떎.
- 洹몃옒???댁쁺 洹쒖튃怨??꾨떖 ?⑦꽩? 嫄곗쓽 ?숈씪?섍쾶 ?좎??섎뒗 寃껋씠 醫뗫떎.

## 愿??note

- [[LLM Wiki Home]]
- [[Daily Brief Delivery Workflow]]
- [[Daily Brief Latest]]
- [[Current State Synthesis]]
