#!/usr/bin/env python3
"""Generate a draft-idea queue from the source-watch database.

This turns uncovered topic hints into candidate article ideas for SkincareThai.
The output is written to reports/draft_idea_queue.md and printed to stdout.
"""

from __future__ import annotations

import argparse
import csv
import sqlite3
from pathlib import Path

from fetch_source_updates import extract_topic_hints
from report_source_watch import scan_site_coverage


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "source_watch.db"
REPORT_PATH = ROOT / "reports" / "draft_idea_queue.md"
KEYWORDS_PATH = ROOT / "data" / "keywords.csv"


IDEA_TEMPLATES: dict[str, str] = {
    "personal color": "Personal Color คืออะไร? วิธีเช็กโทนที่เหมาะกับผิวคนไทย",
    "kids sunscreen": "กันแดดเด็กเลือกยังไง? รวมแนวทางเลือกแบบปลอดภัยและใช้จริง",
    "sachet sunscreen": "กันแดดซองตัวไหนดี? ตัวเลือกคุ้มๆ สำหรับพกง่ายและใช้ทุกวัน",
    "pore tightening": "รูขุมขนกว้างแก้ยังไง? วิธีดูแลผิวให้ดูเรียบขึ้นแบบไม่เวอร์",
    "hair loss shampoo": "แชมพูแก้ผมร่วงเลือกยังไง? สิ่งที่ควรดูและตัวอย่างแนวทางดูแล",
    "acne sunscreen": "กันแดดคนเป็นสิวควรเลือกแบบไหน? เนื้อสัมผัสและส่วนผสมที่ควรมองหา",
    "leg scars": "ขาลายแก้ยังไง? วิธีดูแลรอยและผิวไม่สม่ำเสมอ",
    "retinol": "เรตินอลเริ่มยังไงให้ปลอดภัย? คู่มือสำหรับมือใหม่",
    "niacinamide": "Niacinamide ใช้ยังไงให้เห็นผล? เหมาะกับผิวแบบไหน",
    "centella": "Centella / Cica ช่วยอะไร? สรุปแบบเข้าใจง่าย",
    "pdrn": "PDRN คืออะไร? ทำไมถึงเริ่มเป็นที่พูดถึงในสกินแคร์",
    "vitamin c": "วิตามินซีทาหน้าเลือกยังไง? ใช้คู่กับอะไรดีและควรระวังอะไร",
    "moisturizer": "มอยเจอร์ไรเซอร์เลือกยังไงให้ตรงสภาพผิว",
    "cleanser": "คลีนเซอร์แบบไหนเหมาะกับผิวคนไทยในชีวิตประจำวัน",
    "serum": "เซรั่มควรเลือกตามปัญหาผิวยังไง",
    "sunscreen": "กันแดดเลือกเนื้อแบบไหนดี? รวมแนวทางเลือกสำหรับใช้จริง",
    "acne": "คนเป็นสิวควรดูแลผิวยังไงให้ไม่เห่อเพิ่ม",
    "dark spots": "รอยดำและจุดด่างดำดูแลยังไงให้ผิวดูสม่ำเสมอขึ้น",
}

SEED_TERMS = [
    "personal color",
    "kids sunscreen",
    "sachet sunscreen",
    "pore tightening",
    "hair loss shampoo",
    "acne sunscreen",
    "leg scars",
]


def build_queue(conn: sqlite3.Connection, limit: int) -> list[dict[str, object]]:
    site_coverage = scan_site_coverage()
    rows = conn.execute(
        """
        SELECT
            st.term,
            COUNT(*) AS hit_count,
            COUNT(DISTINCT st.source_id) AS source_count,
            GROUP_CONCAT(DISTINCT s.source_name) AS sources,
            GROUP_CONCAT(DISTINCT sp.post_title) AS example_titles,
            GROUP_CONCAT(DISTINCT sp.post_url) AS example_urls
        FROM source_terms st
        JOIN sources s ON s.id = st.source_id
        LEFT JOIN source_posts sp ON sp.source_id = st.source_id AND sp.is_new_topic = 1
        WHERE st.term_type = 'topic_hint'
        GROUP BY st.term
        ORDER BY hit_count DESC, source_count DESC, st.term ASC
        """
    ).fetchall()

    queue: list[dict[str, object]] = []
    for row in rows:
        term = str(row["term"] or "").strip()
        if not term or term.lower() in site_coverage:
            continue
        queue.append(
            {
                "term": term,
                "hit_count": int(row["hit_count"] or 0),
                "source_count": int(row["source_count"] or 0),
                "sources": row["sources"] or "",
                "example_titles": row["example_titles"] or "",
                "example_urls": row["example_urls"] or "",
                "idea_title": IDEA_TEMPLATES.get(term.lower(), f"{term} ในมุมที่คนไทยกำลังสนใจ"),
                "hint_sample": extract_topic_hints(term, "")[:3],
            }
        )
    return queue[:limit]


def load_seed_queue(limit: int) -> list[dict[str, object]]:
    terms: list[str] = []
    if KEYWORDS_PATH.exists():
        with KEYWORDS_PATH.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                keyword = (row.get("keyword") or "").strip()
                if keyword:
                    terms.append(keyword)
    terms.extend(SEED_TERMS)

    queue: list[dict[str, object]] = []
    seen = set()
    for term in terms:
        key = term.lower()
        if key in seen:
            continue
        seen.add(key)
        queue.append(
            {
                "term": term,
                "hit_count": 0,
                "source_count": 0,
                "sources": "",
                "example_titles": "",
                "example_urls": "",
                "idea_title": IDEA_TEMPLATES.get(key, f"{term} ในมุมที่คนไทยกำลังสนใจ"),
                "hint_sample": [],
                "seed": True,
            }
        )
        if len(queue) >= limit:
            break
    return queue


def render(queue: list[dict[str, object]]) -> str:
    lines: list[str] = ["# Draft Idea Queue", ""]
    if not queue:
        lines.append("- No uncovered ideas yet.")
        lines.append("")
        return "\n".join(lines)

    for item in queue:
        prefix = "Seed idea" if item.get("seed") else "Draft idea"
        lines.append(f"## {item['idea_title']}")
        lines.append(f"- Topic hint: {item['term']}")
        lines.append(f"- {prefix}: {item['hit_count']} hint(s) from {item['source_count']} source(s)")
        if item["sources"]:
            lines.append(f"- Sources: {item['sources']}")
        if item["example_titles"]:
            lines.append(f"- Example posts: {item['example_titles']}")
        if item["example_urls"]:
            lines.append(f"- URLs: {item['example_urls']}")
        lines.append("- Suggested angle: Compare what Thai readers want with the source writer's details, then add our own practical verdict.")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        queue = build_queue(conn, args.limit)
        if not queue:
            queue = load_seed_queue(args.limit)
        text = render(queue)
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(text, encoding="utf-8")
        print(text)
        print(f"\nSaved draft queue to {REPORT_PATH}")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
