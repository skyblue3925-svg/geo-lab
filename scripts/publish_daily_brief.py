from __future__ import annotations

import argparse
import os
import sys
from datetime import date
from pathlib import Path
from urllib import parse, request


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_NOTE_DIR = ROOT / "knowledge" / "wiki" / "syntheses" / "daily-briefs"
DEFAULT_LATEST_NOTE = ROOT / "knowledge" / "wiki" / "syntheses" / "Daily Brief Latest.md"
DEFAULT_ENV_FILE = ROOT / ".env"
DEFAULT_SHARED_ENV_FILE = Path.home() / ".codex" / "telegram-daily-brief.env"
TELEGRAM_LIMIT = 3900


def load_env_file(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    if not path.exists():
        return data

    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip().strip('"').strip("'")
    return data


def resolve_setting(name: str, env_data: dict[str, str]) -> str | None:
    return os.environ.get(name) or env_data.get(name)


def build_note(note_date: str, body: str) -> str:
    clean_body = body.strip()
    return f"""---
id: daily-brief-{note_date}
type: synthesis
layer: curated
status: active
created: {note_date}
updated: {note_date}
tags:
  - synthesis
  - daily-brief
  - automation
aliases:
  - daily-brief-{note_date}
---

# {note_date} Daily Brief

{clean_body}
"""


def send_telegram_message(token: str, chat_id: str, text: str) -> None:
    message = text.strip()
    if not message:
        raise ValueError("Telegram summary is empty.")
    if len(message) > TELEGRAM_LIMIT:
        message = message[:TELEGRAM_LIMIT].rstrip() + "\n\n[truncated]"

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = parse.urlencode({"chat_id": chat_id, "text": message}).encode("utf-8")
    req = request.Request(url, data=payload, method="POST")
    with request.urlopen(req, timeout=20) as response:
        if response.status >= 400:
            raise RuntimeError(f"Telegram API returned status {response.status}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Publish a daily wiki brief to Obsidian and optionally send a Telegram summary."
    )
    parser.add_argument("--report-file", required=True, help="Path to a markdown body file for the full report.")
    parser.add_argument("--summary-file", required=True, help="Path to a plain-text summary for Telegram.")
    parser.add_argument("--date", default=str(date.today()), help="Brief date in YYYY-MM-DD format.")
    parser.add_argument(
        "--note-dir",
        default=str(DEFAULT_NOTE_DIR),
        help="Directory where dated daily brief notes should be written.",
    )
    parser.add_argument(
        "--latest-note",
        default=str(DEFAULT_LATEST_NOTE),
        help="Path to the latest-pointer note that should be overwritten each run.",
    )
    parser.add_argument(
        "--env-file",
        default=str(DEFAULT_ENV_FILE),
        help="Optional repo-local .env file for TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID.",
    )
    parser.add_argument(
        "--shared-env-file",
        default=str(DEFAULT_SHARED_ENV_FILE),
        help="Optional shared env file used across multiple vaults.",
    )
    args = parser.parse_args()

    report_file = Path(args.report_file)
    summary_file = Path(args.summary_file)
    note_dir = Path(args.note_dir)
    latest_note = Path(args.latest_note)
    env_file = Path(args.env_file)
    shared_env_file = Path(args.shared_env_file)

    if not report_file.exists():
        raise FileNotFoundError(f"Report file not found: {report_file}")
    if not summary_file.exists():
        raise FileNotFoundError(f"Summary file not found: {summary_file}")

    report_body = report_file.read_text(encoding="utf-8")
    summary_text = summary_file.read_text(encoding="utf-8")

    note_dir.mkdir(parents=True, exist_ok=True)
    latest_note.parent.mkdir(parents=True, exist_ok=True)

    note_content = build_note(args.date, report_body)
    dated_note = note_dir / f"{args.date} Daily Brief.md"
    dated_note.write_text(note_content, encoding="utf-8", newline="\n")
    latest_note.write_text(note_content, encoding="utf-8", newline="\n")

    print(f"Wrote Obsidian note: {dated_note}")
    print(f"Updated latest note: {latest_note}")

    env_data: dict[str, str] = {}
    env_data.update(load_env_file(shared_env_file))
    env_data.update(load_env_file(env_file))
    token = resolve_setting("TELEGRAM_BOT_TOKEN", env_data)
    chat_id = resolve_setting("TELEGRAM_CHAT_ID", env_data)

    if not token or not chat_id:
        print("Telegram delivery skipped: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is missing.")
        return 0

    try:
        send_telegram_message(token, chat_id, summary_text)
    except Exception as exc:  # pragma: no cover - operational path
        print(f"Telegram delivery failed: {exc}", file=sys.stderr)
        return 1

    print("Telegram summary sent successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
