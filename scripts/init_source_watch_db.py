#!/usr/bin/env python3
"""Initialize the Thai blogger source-watch SQLite database.

This keeps the first version intentionally small:
- sources we want to watch
- pages/posts discovered from those sources
- stored article text for style analysis
- notes about topic coverage and new topics
"""

from __future__ import annotations

import csv
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "source_watch.db"
SOURCES_CSV = ROOT / "data" / "sources.csv"


SCHEMA = """
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT NOT NULL,
    website_url TEXT NOT NULL UNIQUE,
    rss_feed_url TEXT,
    notes TEXT,
    content_type TEXT,
    topic_coverage TEXT,
    last_checked TEXT,
    last_seen_post_at TEXT,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS source_posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL,
    post_url TEXT NOT NULL UNIQUE,
    post_title TEXT,
    published_at TEXT,
    discovered_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    topic_label TEXT,
    intent_label TEXT,
    is_new_topic INTEGER NOT NULL DEFAULT 0,
    raw_html TEXT,
    extracted_text TEXT,
    summary TEXT,
    style_notes TEXT,
    FOREIGN KEY(source_id) REFERENCES sources(id)
);

CREATE TABLE IF NOT EXISTS source_terms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL,
    term TEXT NOT NULL,
    term_type TEXT NOT NULL DEFAULT 'topic',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_id, term, term_type),
    FOREIGN KEY(source_id) REFERENCES sources(id)
);

CREATE TABLE IF NOT EXISTS source_checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL,
    checked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL DEFAULT 'ok',
    note TEXT,
    FOREIGN KEY(source_id) REFERENCES sources(id)
);

CREATE INDEX IF NOT EXISTS idx_source_posts_source_id ON source_posts(source_id);
CREATE INDEX IF NOT EXISTS idx_source_terms_source_id ON source_terms(source_id);
CREATE INDEX IF NOT EXISTS idx_source_checks_source_id ON source_checks(source_id);
"""


def load_sources_csv(conn: sqlite3.Connection) -> int:
    if not SOURCES_CSV.exists():
        return 0

    inserted = 0
    with SOURCES_CSV.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            source_name = (row.get("source_name") or "").strip()
            website_url = (row.get("website_url") or "").strip()
            rss_feed_url = (row.get("rss_feed_url") or "").strip() or None
            notes = (row.get("notes") or "").strip() or None
            if not source_name or not website_url:
                continue
            conn.execute(
                """
                INSERT INTO sources (source_name, website_url, rss_feed_url, notes, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(website_url) DO UPDATE SET
                    source_name=excluded.source_name,
                    rss_feed_url=excluded.rss_feed_url,
                    notes=excluded.notes,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (source_name, website_url, rss_feed_url, notes),
            )
            inserted += 1
    return inserted


def main() -> int:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.executescript(SCHEMA)
        count = load_sources_csv(conn)
        conn.commit()
        print(f"Initialized {DB_PATH}")
        print(f"Imported/updated {count} sources")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
