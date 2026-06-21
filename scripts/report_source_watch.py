#!/usr/bin/env python3
"""Print a quick Markdown report for the source-watch database."""

from __future__ import annotations

import argparse
import html
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from fetch_source_updates import classify_topic, extract_topic_hints


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "source_watch.db"
REPORT_PATH = ROOT / "reports" / "source_watch_report.md"


def parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    cleaned = value.strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(cleaned)
    except ValueError:
        return None


def recency_score(value: str | None, max_points: int) -> int:
    parsed = parse_iso(value)
    if parsed is None:
        return 0
    now = datetime.now(timezone.utc)
    delta = now - parsed.astimezone(timezone.utc)
    days = max(delta.total_seconds() / 86400.0, 0.0)
    if days <= 1:
        return max_points
    if days <= 3:
        return int(max_points * 0.8)
    if days <= 7:
        return int(max_points * 0.6)
    if days <= 14:
        return int(max_points * 0.4)
    if days <= 30:
        return int(max_points * 0.2)
    return 0


def freshness_score(row: sqlite3.Row) -> int:
    score = 0
    if row["rss_feed_url"]:
        score += 15
    if (row["post_count"] or 0) > 0:
        score += 10
    if (row["new_topic_count"] or 0) > 0:
        score += 10
    score += recency_score(row["last_checked"], 20)
    score += recency_score(row["last_seen_post_at"], 15)
    if row["topic_coverage"]:
        score += 5
    if row["notes"]:
        score += 5
    return min(score, 100)


def extract_html_title(raw_html: str) -> str | None:
    match = re.search(r"<title[^>]*>(.*?)</title>", raw_html, flags=re.I | re.S)
    if match:
        title = re.sub(r"\s+", " ", html.unescape(match.group(1))).strip()
        if title:
            return title
    match = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']', raw_html, flags=re.I)
    if match:
        title = re.sub(r"\s+", " ", html.unescape(match.group(1))).strip()
        if title:
            return title
    match = re.search(r"<h1[^>]*>(.*?)</h1>", raw_html, flags=re.I | re.S)
    if match:
        title = re.sub(r"<[^>]+>", " ", html.unescape(match.group(1)))
        title = re.sub(r"\s+", " ", title).strip()
        if title:
            return title
    return None


def scan_site_coverage() -> set[str]:
    coverage: set[str] = set()
    for path in ROOT.rglob("*.html"):
        if REPORT_PATH in path.parents:
            continue
        if ".git" in path.parts:
            continue
        try:
            raw_html = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        title = extract_html_title(raw_html) or path.stem.replace("-", " ").replace("_", " ")
        title = re.sub(r"\s+", " ", title).strip()
        if not title:
            continue
        coverage.add(classify_topic(title, ""))
        for hint in extract_topic_hints(title, ""):
            coverage.add(hint)
    coverage.discard("other")
    return coverage


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
                s.topic_coverage,
                s.notes,
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

        creator_rows = []
        for row in rows:
            data = dict(row)
            data["freshness_score"] = freshness_score(row)
            creator_rows.append(data)
        creator_rows.sort(key=lambda item: (-item["freshness_score"], -(item["new_topic_count"] or 0), -(item["post_count"] or 0), item["source_name"]))

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

        site_coverage = scan_site_coverage()
        uncovered_rows = conn.execute(
            """
            SELECT
                st.term,
                COUNT(*) AS hit_count,
                COUNT(DISTINCT st.source_id) AS source_count,
                GROUP_CONCAT(DISTINCT s.source_name) AS sources
            FROM source_terms st
            JOIN sources s ON s.id = st.source_id
            WHERE st.term_type = 'topic_hint'
            GROUP BY st.term
            ORDER BY hit_count DESC, source_count DESC, st.term ASC
            """,
        ).fetchall()
        uncovered_rows = [
            row
            for row in uncovered_rows
            if row["term"] and row["term"].lower() not in site_coverage
        ]

        lines: list[str] = ["# Source Watch Report", ""]
        lines.append("## Top Creators To Watch")
        lines.append("")
        if creator_rows:
            for row in creator_rows[: args.limit]:
                lines.append(f"- **{row['source_name']}** · freshness {row['freshness_score']}/100")
                lines.append(f"  - URL: {row['website_url']}")
                if row["rss_feed_url"]:
                    lines.append(f"  - RSS: {row['rss_feed_url']}")
                lines.append(f"  - Posts stored: {row['post_count'] or 0}")
                lines.append(f"  - New topics: {row['new_topic_count'] or 0}")
                if row["topics"]:
                    lines.append(f"  - Topics: {row['topics']}")
                if row["last_checked"]:
                    lines.append(f"  - Last checked: {row['last_checked']}")
                if row["last_seen_post_at"]:
                    lines.append(f"  - Last seen post: {row['last_seen_post_at']}")
        else:
            lines.append("- No sources yet.")
        lines.append("")

        lines.append("## Topics Not Yet Covered By Us")
        lines.append("")
        if uncovered_rows:
            for row in uncovered_rows[: args.topic_limit]:
                lines.append(f"- **{row['term']}**: {row['hit_count']} hint(s) from {row['source_count']} source(s)")
                if row["sources"]:
                    lines.append(f"  - Sources: {row['sources']}")
        else:
            lines.append("- No uncovered topic hints yet.")
        lines.append("")

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
