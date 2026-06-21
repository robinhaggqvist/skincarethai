#!/usr/bin/env python3
"""Print a quick Markdown report for the source-watch database."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "source_watch.db"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT
                s.source_name,
                s.website_url,
                s.rss_feed_url,
                s.last_checked,
                s.last_seen_post_at,
                COUNT(DISTINCT p.id) AS post_count,
                SUM(CASE WHEN p.is_new_topic = 1 THEN 1 ELSE 0 END) AS new_topic_count,
                GROUP_CONCAT(DISTINCT p.topic_label) AS topics
            FROM sources s
            LEFT JOIN source_posts p ON p.source_id = s.id
            WHERE s.active = 1
            GROUP BY s.id
            ORDER BY COALESCE(s.last_checked, '') DESC, post_count DESC, s.source_name ASC
            LIMIT ?
            """,
            (args.limit,),
        ).fetchall()

        print("# Source Watch Report")
        print()
        for row in rows:
            print(f"## {row['source_name']}")
            print(f"- URL: {row['website_url']}")
            if row["rss_feed_url"]:
                print(f"- RSS: {row['rss_feed_url']}")
            print(f"- Posts stored: {row['post_count'] or 0}")
            print(f"- New topics: {row['new_topic_count'] or 0}")
            if row["topics"]:
                print(f"- Topics: {row['topics']}")
            if row["last_checked"]:
                print(f"- Last checked: {row['last_checked']}")
            if row["last_seen_post_at"]:
                print(f"- Last seen post: {row['last_seen_post_at']}")
            print()
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
