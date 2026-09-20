#!/usr/bin/env python3
"""Build an evidence-based Search Console keyword plan for SkincareThai."""

from __future__ import annotations

import argparse
import sqlite3
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = Path("/home/robin/.openclaw/workspace/ops/gsc_stats.sqlite")
REPORT = ROOT / "reports" / "seo_keyword_plan.md"
PROPERTY = "sc-domain:skincarethai.com"


def cluster(query: str) -> tuple[str, str]:
    q = query.lower()
    if "thermage" in q or "หัตถการ" in q:
        return "treatment", "Hold or review scope before expanding treatment content"
    if any(x in q for x in ("niacinamide", "วิตามินซี", "retinol", "เรตินอล")):
        return "ingredient/how-to", "New article or update with a direct use-and-routine answer"
    if any(x in q for x in ("กันแดด", "sunscreen")):
        return "sunscreen", "New article by skin type, audience, budget, or use case"
    if any(x in q for x in ("รูขุมขน", "สิว", "รอยสิว", "ผิวแพ้ง่าย", "ผิวมัน", "ผิวแห้ง")):
        return "skin concern", "New problem-solving article or meaningful update"
    if any(x in q for x in ("cetaphil", "เซตาฟิล", "รีวิว")):
        return "product/review", "Product-specific review or comparison with evidence"
    if len(q.split()) <= 2 or q in {"สกินแคร์", "เครื่องสำอาง", "เวชสำอาง"}:
        return "broad", "Use as a supporting theme; do not make another generic page"
    return "other", "Review manually against existing intent"


def lane(query: str, impressions: int, position: float | None) -> str:
    c, _ = cluster(query)
    if c == "treatment":
        return "hold/scope"
    if c == "broad":
        return "support/internal-link"
    if impressions >= 3 and position is not None and position <= 20:
        return "update CTR"
    if impressions >= 3:
        return "new or update"
    return "watch"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=str(DEFAULT_DB))
    parser.add_argument("--days", type=int, default=120)
    parser.add_argument("--limit", type=int, default=30)
    args = parser.parse_args()

    start = (date.today() - timedelta(days=args.days)).isoformat()
    conn = sqlite3.connect(args.db)
    rows = conn.execute(
        """
        SELECT r.query, SUM(r.clicks), SUM(r.impressions),
               SUM(r.position*r.impressions)/NULLIF(SUM(r.impressions), 0)
        FROM performance_rows r
        JOIN sweeps s ON s.id=r.sweep_id
        JOIN collections c ON c.id=s.collection_id
        JOIN properties p ON p.id=c.property_id
        WHERE p.property=? AND c.target_date>=? AND s.sweep_name='queries'
          AND r.query IS NOT NULL AND r.query != ''
        GROUP BY r.query
        ORDER BY SUM(r.impressions) DESC
        LIMIT ?
        """,
        (PROPERTY, start, args.limit),
    ).fetchall()
    conn.close()

    lines = [
        "# SEO Keyword Plan",
        "",
        f"- Property: `{PROPERTY}`",
        f"- Window: last {args.days} days from {start}",
        f"- Queries reviewed: {len(rows)}",
        "- Data source: Google Search Console SQLite history",
        "",
        "## Priority queries",
        "",
    ]
    if not rows:
        lines.append("- No query rows available yet.")
    for query, clicks, impressions, position in rows:
        category, recommendation = cluster(query)
        action = lane(query, impressions, position)
        ctr = (100 * clicks / impressions) if impressions else 0
        position_text = f"{position:.1f}" if position is not None else "n/a"
        lines.append(
            f"- **{query}** — {impressions} impressions, {clicks} clicks, "
            f"CTR {ctr:.2f}%, position {position_text}; "
            f"cluster=`{category}`, lane=`{action}`. {recommendation}."
        )

    lines.extend([
        "",
        "## Decision for this run",
        "",
        "Use the query list as evidence for topic selection, not as permission to publish keyword variations automatically.",
        "Create a new page only when the angle has a distinct audience/problem/use case and source support.",
        "Update an existing page when the query matches its intent but the page needs better depth, title, or evidence.",
        "",
        "## Next actions",
        "",
        "1. Prioritise specific ingredient, skin-concern, sunscreen, and product-review queries.",
        "2. Rewrite titles/meta descriptions for high-impression, zero-click pages.",
        "3. Keep broad terms as internal-link/supporting themes.",
        "4. Hold treatment queries unless the editorial scope explicitly includes them.",
    ])
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(REPORT.read_text(encoding="utf-8"), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
