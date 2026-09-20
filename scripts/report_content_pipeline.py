#!/usr/bin/env python3
"""Classify the content queue into new, update, already-live, and hold lanes."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from daily_affiliate_growth import (  # noqa: E402
    assess_quality,
    collect_candidates,
    live_sitemap_urls,
    make_page_path,
    page_url,
    profile_for,
)


REPORT = ROOT / "reports" / "content_pipeline_backlog.md"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quality-threshold", type=int, default=80)
    args = parser.parse_args()

    live_urls = live_sitemap_urls(False)
    if live_urls is None:
        raise SystemExit("Could not fetch the live sitemap; refusing to classify publishing lanes")

    lanes: dict[str, list[tuple[object, int, str]]] = {
        "new": [],
        "update": [],
        "already_live": [],
        "hold": [],
    }
    for item in collect_candidates():
        assessment = assess_quality(item, args.quality_threshold)
        path = make_page_path(item, profile_for(item))
        url = page_url(path)
        if not assessment.eligible:
            lanes["hold"].append((item, assessment.score, f"quality score {assessment.score}/100 below threshold"))
        elif path.exists() and url in live_urls:
            if assessment.item.seed_sources >= 3 or assessment.item.seed_hints >= 7:
                lanes["update"].append((item, assessment.score, "live page has substantial source support; review for a meaningful update"))
            else:
                lanes["already_live"].append((item, assessment.score, "already live; no strong update signal"))
        elif path.exists():
            lanes["new"].append((item, assessment.score, "local page exists but is absent from the live sitemap; deploy it"))
        else:
            lanes["new"].append((item, assessment.score, "no local/live page exists"))

    lines = [
        "# Content Pipeline Backlog",
        "",
        f"- Generated: {date.today().isoformat()}",
        f"- Quality threshold: {args.quality_threshold}/100",
        f"- Candidates reviewed: {sum(len(v) for v in lanes.values())}",
        f"- New/deploy lane: {len(lanes['new'])}",
        f"- Update lane: {len(lanes['update'])}",
        f"- Already live: {len(lanes['already_live'])}",
        f"- Hold lane: {len(lanes['hold'])}",
        "",
        "## New / deploy",
        "",
    ]
    for item, score, reason in lanes["new"]:
        lines.append(f"- {score}/100 · {item.title} · {reason}")
    if not lanes["new"]:
        lines.append("- None currently queued. New source-backed topics are needed before new pages can be published.")

    lines.extend(["", "## Update candidates", ""])
    for item, score, reason in lanes["update"]:
        lines.append(f"- {score}/100 · {item.title} · {reason}")
    if not lanes["update"]:
        lines.append("- None")

    lines.extend(["", "## Already live", ""])
    for item, score, reason in lanes["already_live"]:
        lines.append(f"- {score}/100 · {item.title} · {reason}")
    if not lanes["already_live"]:
        lines.append("- None")

    lines.extend(["", "## Holds", ""])
    for item, score, reason in lanes["hold"]:
        lines.append(f"- {score}/100 · {item.title} · {reason}")
    if not lanes["hold"]:
        lines.append("- None")

    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(f"Saved report to {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
