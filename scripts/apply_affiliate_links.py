#!/usr/bin/env python3
"""Apply verified affiliate links to matching review pages.

The script keeps affiliate placement conservative:
- only pages with a clear product-name match are updated
- only product links that still resolve to the expected product are used
- pages without a strong match stay link-free
"""

from __future__ import annotations

import argparse
import csv
import html
import math
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
PRODUCTS_CSV = ROOT / "data" / "products.csv"
USER_AGENT = "Mozilla/5.0 (compatible; SkincareThaiAffiliateBot/1.0)"
STOPWORDS = {
    "and",
    "all",
    "for",
    "of",
    "the",
    "with",
    "versions",
    "version",
    "รุ่น",
    "ต่างๆ",
    "ต่าง",
    "หลายสูตร",
    "สูตร",
    "แบบ",
    "และ",
    "ที่",
    "ตัว",
    "ของ",
    "ใหม่",
}


class TitleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title_parts: list[str] = []
        self.in_title = False
        self.og_title: str | None = None

    def handle_starttag(self, tag, attrs):
        if tag == "title":
            self.in_title = True
        if tag == "meta":
            attr = {k.lower(): v for k, v in attrs}
            if attr.get("property", "").lower() == "og:title" and attr.get("content"):
                self.og_title = html.unescape(attr["content"]).strip()

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title_parts.append(data)

    def title(self) -> str:
        return re.sub(r"\s+", " ", html.unescape("".join(self.title_parts))).strip()


def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^0-9a-zก-๙]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def product_terms(product: str) -> list[str]:
    product = product.split(",", 1)[0].strip()
    if ":" in product:
        brand, name = product.split(":", 1)
        raw = f"{brand} {name}"
    else:
        raw = product
    tokens = []
    for token in normalize(raw).split():
        if len(token) < 2:
            continue
        if token in STOPWORDS:
            continue
        tokens.append(token)
    return list(dict.fromkeys(tokens))


def product_phrase(product: str) -> str:
    product = product.split(",", 1)[0].strip()
    if ":" in product:
        _, name = product.split(":", 1)
    else:
        name = product
    return normalize(name)


def extract_page_blob(path: Path) -> str:
    return normalize(path.read_text(encoding="utf-8", errors="ignore"))


def fetch_title(url: str, timeout: int = 25) -> tuple[str, str]:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=timeout) as response:
        final_url = response.geturl()
        body = response.read(150_000)
        content_type = response.headers.get("Content-Type", "")
    encoding = "utf-8"
    match = re.search(r"charset=([A-Za-z0-9._-]+)", content_type, flags=re.I)
    if match:
        encoding = match.group(1)
    raw = body.decode(encoding, errors="replace")
    parser = TitleParser()
    parser.feed(raw)
    title = parser.og_title or parser.title()
    return final_url, title


def validate_link(product: str, url: str) -> tuple[bool, str]:
    url = (url or "").strip()
    if not url or url.lower() in {"none", "#"}:
        return False, "missing URL"
    try:
        final_url, title = fetch_title(url)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        return False, f"fetch failed: {exc}"

    blob = normalize(f"{final_url} {title}")
    terms = product_terms(product)
    if not terms:
        return False, "no product terms"

    matched = [term for term in terms if term in blob]
    threshold = max(2, math.ceil(len(terms) * 0.6))
    if len(matched) < threshold:
        return False, f"title mismatch: matched {len(matched)}/{len(terms)} terms"
    return True, f"final url={final_url} | title={title}"


def load_products() -> list[dict[str, str]]:
    with PRODUCTS_CSV.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for row in reader:
            product = (row.get("product") or "").strip()
            web = (row.get("affiliate website link") or "").strip()
            app = (row.get("affiliate app link") or "").strip()
            if product:
                rows.append(
                    {
                        "product": product,
                        "web": web,
                        "app": app,
                        "notes": (row.get("notes") or "").strip(),
                    }
                )
        return rows


def update_file(path: Path, product: str, web: str, app: str) -> int:
    text = path.read_text(encoding="utf-8")
    normalized_blob = normalize(text)
    phrase = product_phrase(product)
    if not phrase:
        return 0
    if phrase not in normalized_blob:
        return 0
    if 'href="None"' not in text and 'data-app-link="None"' not in text:
        return 0

    pattern = re.compile(r'<a\b[^>]*class="[^"]*aff-link-btn[^"]*"[^>]*>', flags=re.I)

    if not pattern.search(text):
        return 0

    def replace_anchor(match: re.Match[str]) -> str:
        tag = match.group(0)
        if 'href="None"' not in tag and 'data-app-link="None"' not in tag:
            return tag
        tag = re.sub(r'href="[^"]*"', f'href="{web}"', tag, count=1)
        tag = re.sub(r'data-app-link="[^"]*"', f'data-app-link="{app}"', tag, count=1)
        return tag

    new_text, count = pattern.subn(replace_anchor, text)
    if count:
        path.write_text(new_text, encoding="utf-8")
    return count


def candidate_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("index.html"):
        if path.parent == ROOT:
            continue
        files.append(path)
    return sorted(files)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Validate and report without editing files")
    parser.add_argument(
        "--max-files",
        type=int,
        default=None,
        help="Maximum number of page files to update in one run",
    )
    args = parser.parse_args()

    products = load_products()
    files = candidate_files()

    verified: list[dict[str, str]] = []
    skipped: list[dict[str, str]] = []
    for row in products:
        ok, reason = validate_link(row["product"], row["web"])
        if ok:
            verified.append({**row, "validation": reason})
        else:
            skipped.append({**row, "validation": reason})

    print(f"Verified {len(verified)} product links")
    for row in verified:
        print(f"- {row['product']}: {row['validation']}")

    if skipped:
        print(f"\nSkipped {len(skipped)} product links")
        for row in skipped:
            print(f"- {row['product']}: {row['validation']}")

    if args.dry_run:
        return 0

    total_replacements = 0
    touched_files: list[str] = []
    max_files = args.max_files if args.max_files and args.max_files > 0 else None
    for file_path in files:
        if max_files is not None and len(touched_files) >= max_files:
            break
        file_hits = 0
        for row in verified:
            if not row["app"]:
                continue
            file_hits += update_file(file_path, row["product"], row["web"], row["app"])
        if file_hits:
            total_replacements += file_hits
            touched_files.append(str(file_path.relative_to(ROOT)))

    print(f"\nUpdated {total_replacements} affiliate CTA(s) across {len(touched_files)} file(s)")
    for rel in touched_files:
        print(f"- {rel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
