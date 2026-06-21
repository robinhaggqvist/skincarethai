#!/usr/bin/env python3
"""Store a fetched source page and its extracted text in SQLite.

Usage:
  python scripts/store_source_page.py \
    --source-url https://example.com \
    --post-url https://example.com/post \
    --title "Post title" \
    --text-file /tmp/extracted.txt \
    [--html-file /tmp/raw.html]
"""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "source_watch.db"


def read_text(path: str | None) -> str | None:
    if not path:
        return None
    p = Path(path)
    if not p.exists():
        return None
    return p.read_text(encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--post-url", required=True)
    parser.add_argument("--title")
    parser.add_argument("--published-at")
    parser.add_argument("--topic-label")
    parser.add_argument("--intent-label")
    parser.add_argument("--is-new-topic", action="store_true")
    parser.add_argument("--text-file")
    parser.add_argument("--html-file")
    parser.add_argument("--summary")
    parser.add_argument("--style-notes")
    args = parser.parse_args()

    extracted_text = read_text(args.text_file)
    raw_html = read_text(args.html_file)

    conn = sqlite3.connect(DB_PATH)
    try:
        conn.row_factory = sqlite3.Row
        source = conn.execute(
            "SELECT id FROM sources WHERE website_url = ?",
            (args.source_url,),
        ).fetchone()
        if not source:
            raise SystemExit(f"Source not found in DB: {args.source_url}")

        conn.execute(
            """
            INSERT INTO source_posts (
                source_id, post_url, post_title, published_at, topic_label,
                intent_label, is_new_topic, raw_html, extracted_text, summary, style_notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(post_url) DO UPDATE SET
                post_title=excluded.post_title,
                published_at=excluded.published_at,
                topic_label=excluded.topic_label,
                intent_label=excluded.intent_label,
                is_new_topic=excluded.is_new_topic,
                raw_html=excluded.raw_html,
                extracted_text=excluded.extracted_text,
                summary=excluded.summary,
                style_notes=excluded.style_notes
            """,
            (
                source["id"],
                args.post_url,
                args.title,
                args.published_at,
                args.topic_label,
                args.intent_label,
                1 if args.is_new_topic else 0,
                raw_html,
                extracted_text,
                args.summary,
                args.style_notes,
            ),
        )
        conn.commit()
        print(f"Stored {args.post_url}")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
