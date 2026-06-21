#!/usr/bin/env python3
"""Build a short editorial calendar from the draft idea queue.

The calendar is intentionally lightweight: it assigns the next ideas to the
next few days and writes the result to reports/content_calendar.md.
"""

from __future__ import annotations

import argparse
from datetime import date, timedelta
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "reports" / "content_calendar.md"

sys.path.insert(0, str(ROOT / "scripts"))
from generate_draft_queue import build_queue, load_seed_queue  # noqa: E402
import sqlite3  # noqa: E402


DB_PATH = ROOT / "data" / "source_watch.db"


def load_queue(limit: int) -> list[dict[str, object]]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        queue = build_queue(conn, limit)
        if not queue:
            queue = load_seed_queue(limit)
        return queue
    finally:
        conn.close()


def render_calendar(items: list[dict[str, object]], days: int) -> str:
    lines = ["# Content Calendar", ""]
    if not items:
        lines.append("- No draft ideas available yet.")
        lines.append("")
        return "\n".join(lines)

    start = date.today() + timedelta(days=1)
    for index in range(days):
        item = items[index % len(items)]
        day = start + timedelta(days=index)
        lines.append(f"## {day.isoformat()} · {item['idea_title']}")
        lines.append(f"- Topic hint: {item['term']}")
        lines.append(f"- Priority: {days - index} / {days}")
        if item.get("sources"):
            lines.append(f"- Sources: {item['sources']}")
        if item.get("example_titles"):
            lines.append(f"- Example posts: {item['example_titles']}")
        lines.append("- Status: draft")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=7)
    args = parser.parse_args()

    items = load_queue(max(args.limit, 1))
    text = render_calendar(items, max(args.limit, 1))
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(text, encoding="utf-8")
    print(text)
    print(f"\nSaved calendar to {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
