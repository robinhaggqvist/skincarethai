#!/usr/bin/env python3
"""Print a quick Markdown report for the source-watch database."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "source_watch.db"
REPORT_PATH = ROOT / "reports" / "source_watch_report.md"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--topic-limit", type=int, default=15)
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

        topic_rows = conn.execute(
            """
            WITH topic_counts AS (
                SELECT
                    p.topic_label,
                    COUNT(*) AS post_count,
                    COUNT(DISTINCT p.source_id) AS source_count,
                    GROUP_CONCAT(DISTINCT s.source_name) AS sources
                FROM source_posts p
                JOIN sources s ON s.id = p.source_id
                WHERE p.is_new_topic = 1
                GROUP BY p.topic_label
            ), latest_example AS (
                SELECT
                    p.topic_label,
                    p.post_title,
                    p.post_url,
                    s.source_name,
                    ROW_NUMBER() OVER (
                        PARTITION BY p.topic_label
                        ORDER BY COALESCE(p.published_at, p.discovered_at, p.id) DESC, p.id DESC
                    ) AS rn
                FROM source_posts p
                JOIN sources s ON s.id = p.source_id
                WHERE p.is_new_topic = 1
            )
            SELECT
                c.topic_label,
                c.post_count,
                c.source_count,
                c.sources,
                e.post_title AS example_title,
                e.post_url AS example_url,
                e.source_name AS example_source
            FROM topic_counts c
            LEFT JOIN latest_example e
                ON e.topic_label = c.topic_label AND e.rn = 1
            ORDER BY c.post_count DESC, c.source_count DESC, c.topic_label ASC
            LIMIT ?
            """,
            (args.topic_limit,),
        ).fetchall()

        lines: list[str] = ["# Source Watch Report", ""]
        for row in rows:
            lines.append(f"## {row['source_name']}")
            lines.append(f"- URL: {row['website_url']}")
            if row["rss_feed_url"]:
                lines.append(f"- RSS: {row['rss_feed_url']}")
            lines.append(f"- Posts stored: {row['post_count'] or 0}")
            lines.append(f"- New topics: {row['new_topic_count'] or 0}")
            if row["topics"]:
                lines.append(f"- Topics: {row['topics']}")
            if row["last_checked"]:
                lines.append(f"- Last checked: {row['last_checked']}")
            if row["last_seen_post_at"]:
                lines.append(f"- Last seen post: {row['last_seen_post_at']}")
            lines.append("")

        lines.append("## New Topics To Cover")
        lines.append("")
        if topic_rows:
            for row in topic_rows:
                lines.append(f"- **{row['topic_label']}**: {row['post_count']} new post(s) across {row['source_count']} source(s)")
                if row["sources"]:
                    lines.append(f"  - Sources: {row['sources']}")
                if row["example_source"]:
                    lines.append(f"  - Latest source: {row['example_source']}")
                if row["example_title"]:
                    lines.append(f"  - Example: {row['example_title']}")
                if row["example_url"]:
                    lines.append(f"  - URL: {row['example_url']}")
        else:
            lines.append("- No new-topic signals yet.")
        lines.append("")

        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")

        print("\n".join(lines))
        print(f"\nSaved report to {REPORT_PATH}")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
