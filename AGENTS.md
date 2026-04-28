# Project Agent Rules

This repository root is the Obsidian vault. Treat `knowledge/` as the LLM-wiki layer and the rest of the repository as source material unless a task explicitly edits product code or docs.

Canonical vault config lives in root `.obsidian/`. The older `GEO-LAB/` folder is a legacy wrapper vault and should not be treated as the primary wiki root.

## Read First

1. `knowledge/LLM Wiki Home.md`
2. `knowledge/LLM Wiki Schema.md`
3. `knowledge/Knowledge Index.md`
4. `knowledge/wiki/syntheses/Current State Synthesis.md`
5. The latest snapshot note and current-shape notes

## Core Invariants

- `knowledge/raw/` is immutable source material.
- `knowledge/raw/snapshots/` stores immutable repository snapshots.
- `knowledge/wiki/` is the curated layer.
- Prefer updating an existing note over creating a near-duplicate.
- Durable wiki work should usually update both `knowledge/Knowledge Index.md` and `knowledge/Knowledge Log.md`.
- Durable answers should usually be saved into `knowledge/wiki/syntheses/`.
- Write user-facing wiki prose in Korean by default unless asked otherwise.
- Do not present unverified claims as confirmed facts.

## Snapshot And Sync

- Repository change tracking should separate `committed` and `working tree`.
- Raw snapshot capture and curated wiki interpretation must live in separate notes.
- A raw snapshot note should preserve command-derived facts only.
- A curated snapshot note should summarize the latest raw snapshot and state what the wiki should trust as current.
- The phrase `snapshot 하고 wiki sync 해줘` should normally mean:
  1. create a new raw snapshot under `knowledge/raw/snapshots/`
  2. update the latest curated snapshot note
  3. sync affected `current-state`, `current-shape`, map, and entity notes
  4. update `Knowledge Index` and `Knowledge Log` if durable notes changed

## Daily Brief Delivery

- Daily automated reports should be written to `knowledge/wiki/syntheses/daily-briefs/`.
- The latest-pointer note should be `knowledge/wiki/syntheses/Daily Brief Latest.md`.
- Telegram delivery should use `scripts/publish_daily_brief.py`.
- Telegram credentials should come from `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in OS env, repo-local `.env`, or shared `C:\Users\HANSOL\.codex\telegram-daily-brief.env`.
- If Telegram credentials are missing, still write the Obsidian report and mark Telegram delivery as skipped.

## Routing

- For wiki snapshot, ingest, sync, query, and lint tasks, use the matching skill under `knowledge/skills/`.
- A project-specific runtime or doc entrypoint should be checked first when answering codebase questions.

## Scope

- Keep wikilinks dense enough that Graph, Backlinks, and Outgoing Links remain useful.
- Avoid unnecessary note proliferation.
- Keep raw facts, curated interpretation, and forward-looking synthesis separate.
