#!/usr/bin/env python3
"""Review saved non-published drafts without silently publishing duplicates."""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

from daily_affiliate_growth import ROOT, UNPUBLISHED_PATH, make_page_path, profile_for, DraftItem

REPORT = ROOT / "reports" / "monthly_unpublished_review.md"


def main() -> int:
    rows = []
    if UNPUBLISHED_PATH.exists():
        for line in UNPUBLISHED_PATH.read_text(encoding="utf-8").splitlines():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    due = []
    existing = []
    for row in rows:
        item = DraftItem(
            title=str(row.get("title", "")),
            topic=str(row.get("topic", "")),
            sources=str(row.get("sources", "")),
            source_hint=str(row.get("source_hint", "")),
            priority=int(row.get("priority", 0) or 0),
        )
        page = make_page_path(item, profile_for(item))
        if page.exists():
            existing.append((item, "matching page now exists; consider improving or consolidating it"))
            row["status"] = "existing_page"
            row["last_reviewed"] = date.today().isoformat()
            continue
        first_seen = str(row.get("first_seen", date.today().isoformat()))
        try:
            age = (date.today() - datetime.strptime(first_seen, "%Y-%m-%d").date()).days
        except ValueError:
            age = 0
        if age >= 30:
            due.append((item, row.get("reason", "saved draft"), age))
            row["status"] = "review_due"
        else:
            row["status"] = "pending"
        row["last_reviewed"] = date.today().isoformat()

    if UNPUBLISHED_PATH.exists():
        UNPUBLISHED_PATH.write_text(
            "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
            encoding="utf-8",
        )

    lines = [
        "# Monthly Unpublished Draft Review",
        "",
        f"- Reviewed: {date.today().isoformat()}",
        f"- Saved drafts examined: {len(rows)}",
        f"- Review due (30+ days): {len(due)}",
        f"- Already represented by a live page: {len(existing)}",
        "",
        "## Review Due",
        "",
    ]
    if due:
        for item, reason, age in due:
            lines.append(f"- {item.title} — {age} days saved — {reason}")
    else:
        lines.append("- None")
    lines.extend(["", "## Existing Pages / Consolidation Candidates", ""])
    if existing:
        for item, reason in existing:
            lines.append(f"- {item.title} — {reason}")
    else:
        lines.append("- None")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
