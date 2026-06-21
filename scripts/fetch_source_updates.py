#!/usr/bin/env python3
"""Fetch Thai beauty sources and store newly discovered posts.

This script is intentionally lightweight:
- RSS feeds first
- homepage link discovery if no RSS exists
- store new posts and extracted text in SQLite
- log each check so we know when a source was last scanned
"""

from __future__ import annotations

import argparse
import html
import re
import sqlite3
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "source_watch.db"
USER_AGENT = "Mozilla/5.0 (compatible; SkincareThaiSourceBot/1.0)"
MAX_BODY_CHARS = 120_000
TOPIC_HINTS = [
    ("personal color", ["personal color", "personalcolour", "personal colour", "พีซี", "สีส่วนตัว", "คัลเลอร์" ]),
    ("kids sunscreen", ["กันแดดเด็ก", "kids sunscreen", "กันแดดสำหรับเด็ก"]),
    ("sachet sunscreen", ["กันแดดซอง", "sachet sunscreen", "ครีมกันแดดซอง"]),
    ("pore tightening", ["รูขุมขน", "pore", "กระชับรูขุมขน"]),
    ("hair loss shampoo", ["ผมร่วง", "hair loss", "แชมพูแก้ผมร่วง", "ผมบาง"]),
    ("acne sunscreen", ["กันแดดคนเป็นสิว", "sunscreen for acne", "กันแดดสิว", "กันแดดสำหรับคนเป็นสิว"]),
    ("leg scars", ["ขาลาย", "รอยที่ขา", "scar", "แผลเป็นที่ขา"]),
    ("retinol", ["retinol", "เรตินอล"]),
    ("niacinamide", ["niacinamide", "ไนอะซินาไมด์"]),
    ("centella", ["centella", "cica", "ซีคา", "ใบบัวบก"]),
    ("pdrn", ["pdrn"]),
    ("vitamin c", ["vitamin c", "วิตามินซี"]),
    ("moisturizer", ["moisturizer", "มอยเจอร์ไรเซอร์", "ครีมบำรุง"]),
    ("cleanser", ["cleanser", "คลีนเซอร์", "คลีนซิ่ง", "cleansing oil"]),
    ("serum", ["serum", "เซรั่ม"]),
    ("sunscreen", ["sunscreen", "กันแดด"]),
    ("acne", ["acne", "สิว"]),
    ("dark spots", ["รอยดำ", "จุดด่างดำ", "ฝ้า", "กระ"]),
]


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript", "svg", "iframe", "form", "nav", "footer", "header", "aside", "button"}:
            self._skip_depth += 1
        elif tag in {"p", "br", "div", "li", "section", "article", "h1", "h2", "h3"}:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript", "svg", "iframe", "form", "nav", "footer", "header", "aside", "button"} and self._skip_depth:
            self._skip_depth -= 1
        elif tag in {"p", "div", "li", "section", "article"}:
            self.parts.append("\n")

    def handle_data(self, data):
        if self._skip_depth:
            return
        chunk = html.unescape(data)
        if chunk.strip():
            self.parts.append(chunk)

    def text(self) -> str:
        joined = "".join(self.parts)
        joined = re.sub(r"[ \t]+\n", "\n", joined)
        joined = re.sub(r"\n{3,}", "\n\n", joined)
        joined = re.sub(r"[ \t]{2,}", " ", joined)
        return joined.strip()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def fetch(url: str, timeout: int = 25) -> tuple[str, bytes, str]:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=timeout) as response:
        final_url = response.geturl()
        body = response.read()
        content_type = response.headers.get("Content-Type", "")
    return final_url, body[:MAX_BODY_CHARS], content_type


def decode_body(body: bytes) -> str:
    for encoding in ("utf-8", "utf-16", "cp874", "latin-1"):
        try:
            return body.decode(encoding)
        except UnicodeDecodeError:
            continue
    return body.decode("utf-8", errors="replace")


def extract_text_from_html(raw_html: str) -> str:
    main_match = re.search(r"<(article|main)[^>]*>(.*?)</\1>", raw_html, flags=re.I | re.S)
    if main_match:
        raw_html = main_match.group(2)
    body_match = re.search(r"<body[^>]*>(.*?)</body>", raw_html, flags=re.I | re.S)
    if body_match:
        raw_html = body_match.group(1)
    parser = TextExtractor()
    parser.feed(raw_html)
    text = parser.text()
    lines = []
    seen = set()
    for line in (part.strip() for part in text.splitlines()):
        if not line:
            continue
        if len(line) < 3:
            continue
        if line.lower() in seen:
            continue
        seen.add(line.lower())
        lines.append(line)
    return "\n".join(lines).strip()


def extract_title(raw_html: str) -> str | None:
    match = re.search(r"<title[^>]*>(.*?)</title>", raw_html, flags=re.I | re.S)
    if match:
        title = re.sub(r"\s+", " ", html.unescape(match.group(1))).strip()
        return title or None
    return None


def extract_description(raw_html: str) -> str | None:
    match = re.search(
        r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)["\']',
        raw_html,
        flags=re.I,
    )
    if match:
        return html.unescape(match.group(1)).strip()
    return None


def parse_rss_urls(raw_xml: str, base_url: str) -> list[dict[str, str]]:
    root = ET.fromstring(raw_xml)
    channel = root.find("channel")
    if channel is None:
        return []

    items = []
    for item in channel.findall("item"):
        link = (item.findtext("link") or "").strip()
        title = (item.findtext("title") or "").strip()
        published = (item.findtext("pubDate") or item.findtext("{http://purl.org/dc/elements/1.1/}date") or "").strip()
        if not link and title:
            link = title
        if link and not urlparse(link).scheme:
            link = urljoin(base_url, link)
        if link:
            items.append({"url": link, "title": title, "published_at": published})
    return items


def discover_links(raw_html: str, base_url: str) -> list[dict[str, str]]:
    hrefs: list[dict[str, str]] = []
    for href, title in re.findall(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', raw_html, flags=re.I | re.S):
        link = urljoin(base_url, html.unescape(href))
        if not urlparse(link).scheme.startswith("http"):
            continue
        text = re.sub(r"<[^>]+>", " ", html.unescape(title))
        text = re.sub(r"\s+", " ", text).strip()
        if not text:
            continue
        hrefs.append({"url": link, "title": text, "published_at": ""})
    seen = set()
    unique = []
    for item in hrefs:
        if item["url"] in seen:
            continue
        seen.add(item["url"])
        unique.append(item)
    return unique


def classify_topic(title: str, content: str) -> str:
    blob = f"{title} {content}".lower()
    mapping = [
        ("sunscreen", "sunscreen"),
        ("กันแดด", "sunscreen"),
        ("acne", "acne"),
        ("สิว", "acne"),
        ("moistur", "moisturizer"),
        ("ชุ่มชื้น", "moisturizer"),
        ("cleanser", "cleanser"),
        ("คลีน", "cleanser"),
        ("serum", "serum"),
        ("เซรั่ม", "serum"),
        ("ingredient", "ingredient"),
        ("ส่วนผสม", "ingredient"),
        ("routine", "routine"),
        ("รูทีน", "routine"),
        ("review", "review"),
        ("รีวิว", "review"),
        ("compare", "compare"),
        ("เทียบ", "compare"),
        ("brand", "brand"),
        ("แบรนด์", "brand"),
        ("launch", "news"),
        ("เปิดตัว", "news"),
    ]
    for needle, label in mapping:
        if needle in blob:
            return label
    return "other"


def extract_topic_hints(title: str, content: str) -> list[str]:
    blob = f"{title} {content}".lower()
    hints: list[str] = []
    for canonical, needles in TOPIC_HINTS:
        if any(needle.lower() in blob for needle in needles):
            hints.append(canonical)
    # Keep the list short and stable.
    unique: list[str] = []
    seen = set()
    for hint in hints:
        key = hint.lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(hint)
    return unique[:5]


def get_source_rows(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM sources WHERE active = 1 ORDER BY id ASC"
    ).fetchall()
    return rows


def source_id_for_url(conn: sqlite3.Connection, website_url: str) -> int | None:
    row = conn.execute(
        "SELECT id FROM sources WHERE website_url = ?",
        (website_url,),
    ).fetchone()
    return int(row[0]) if row else None


def exists_post(conn: sqlite3.Connection, post_url: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM source_posts WHERE post_url = ?",
        (post_url,),
    ).fetchone()
    return row is not None


def store_check(conn: sqlite3.Connection, source_id: int, status: str, note: str | None = None) -> None:
    conn.execute(
        "INSERT INTO source_checks (source_id, checked_at, status, note) VALUES (?, ?, ?, ?)",
        (source_id, now_iso(), status, note),
    )
    conn.execute(
        "UPDATE sources SET last_checked = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (now_iso(), source_id),
    )


def store_post(
    conn: sqlite3.Connection,
    source_id: int,
    post_url: str,
    post_title: str | None,
    published_at: str | None,
    topic_label: str,
    raw_html: str,
    extracted_text: str,
    is_new_topic: bool,
) -> None:
    summary = extracted_text[:500] if extracted_text else None
    conn.execute(
        """
        INSERT INTO source_posts (
            source_id, post_url, post_title, published_at, topic_label, intent_label,
            is_new_topic, raw_html, extracted_text, summary, style_notes
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
            summary=excluded.summary
        """,
        (
            source_id,
            post_url,
            post_title,
            published_at,
            topic_label,
            classify_topic(post_title or "", extracted_text),
            1 if is_new_topic else 0,
            raw_html,
            extracted_text,
            summary,
            None,
        ),
    )


def remember_topic_hints(conn: sqlite3.Connection, source_id: int, title: str, content: str) -> None:
    for hint in extract_topic_hints(title, content):
        remember_term(conn, source_id, hint, "topic_hint")


def source_knows_term(conn: sqlite3.Connection, source_id: int, term: str, term_type: str = "topic") -> bool:
    row = conn.execute(
        "SELECT 1 FROM source_terms WHERE source_id = ? AND term = ? AND term_type = ?",
        (source_id, term, term_type),
    ).fetchone()
    return row is not None


def remember_term(conn: sqlite3.Connection, source_id: int, term: str, term_type: str = "topic") -> None:
    conn.execute(
        """
        INSERT INTO source_terms (source_id, term, term_type)
        VALUES (?, ?, ?)
        ON CONFLICT(source_id, term, term_type) DO NOTHING
        """,
        (source_id, term, term_type),
    )


def process_source(conn: sqlite3.Connection, source: sqlite3.Row, limit: int) -> dict[str, int]:
    discovered = 0
    stored = 0
    notes = []
    source_url = source["website_url"]
    rss_url = source["rss_feed_url"] or ""

    try:
        target = rss_url or source_url
        final_url, body, content_type = fetch(target)
        raw_text = decode_body(body)

        if "xml" in content_type.lower() or rss_url:
            items = parse_rss_urls(raw_text, final_url)
        else:
            items = discover_links(raw_text, final_url)

        for item in items[:limit]:
            discovered += 1
            post_url = item["url"]
            if exists_post(conn, post_url):
                continue

            try:
                post_final, post_body, post_type = fetch(post_url)
                post_html = decode_body(post_body)
                extracted = extract_text_from_html(post_html)
                title = item["title"] or extract_title(post_html)
                if not title:
                    title = extract_description(post_html) or post_url
                topic = classify_topic(title or "", extracted)
                is_new_topic = not source_knows_term(conn, int(source["id"]), topic, "topic")
                store_post(
                    conn,
                    int(source["id"]),
                    post_final,
                    title,
                    item.get("published_at"),
                    topic,
                    post_html,
                    extracted,
                    is_new_topic,
                )
                remember_term(conn, int(source["id"]), topic, "topic")
                remember_topic_hints(conn, int(source["id"]), title or "", extracted)
                stored += 1
                if title:
                    notes.append(title)
            except Exception as exc:  # noqa: BLE001
                notes.append(f"post-fail:{post_url}:{exc}")

        if notes:
            note_text = "; ".join(notes[:5])
        else:
            note_text = f"checked {discovered} links"
        store_check(conn, int(source["id"]), "ok", note_text)
        last_seen = now_iso()
        conn.execute(
            "UPDATE sources SET last_seen_post_at = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (last_seen, int(source["id"])),
        )
        return {"discovered": discovered, "stored": stored}
    except Exception as exc:  # noqa: BLE001
        store_check(conn, int(source["id"]), "error", str(exc))
        return {"discovered": discovered, "stored": stored}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=10, help="Max links to inspect per source")
    parser.add_argument("--source", action="append", help="Optional source URL to process instead of all sources")
    args = parser.parse_args(argv)

    conn = sqlite3.connect(DB_PATH)
    try:
        sources = get_source_rows(conn)
        if args.source:
            wanted = set(args.source)
            sources = [row for row in sources if row["website_url"] in wanted]

        total_discovered = 0
        total_stored = 0
        for source in sources:
            result = process_source(conn, source, args.limit)
            total_discovered += result["discovered"]
            total_stored += result["stored"]
            conn.commit()
            print(f"{source['source_name']}: discovered={result['discovered']} stored={result['stored']}")

        print(f"done: discovered={total_discovered} stored={total_stored}")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
