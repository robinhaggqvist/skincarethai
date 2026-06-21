#!/usr/bin/env python3
"""Run the source-watch refresh, reports, draft queue, and calendar."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(args: list[str]) -> None:
    subprocess.run([sys.executable, *args], cwd=ROOT, check=True)


def main() -> int:
    run(["scripts/fetch_source_updates.py", "--limit", "10"])
    run(["scripts/report_source_watch.py", "--limit", "10", "--topic-limit", "10"])
    run(["scripts/generate_draft_queue.py", "--limit", "15"])
    run(["scripts/build_content_calendar.py", "--limit", "7"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
