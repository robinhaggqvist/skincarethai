#!/usr/bin/env python3
"""Shared helpers for picking and generating page images."""

from __future__ import annotations

import html
import re
import textwrap
from pathlib import Path
from urllib.parse import quote, urljoin, urlparse


SITE_BASE = "https://skincarethai.com"
SOCIAL_IMAGE_DIR_NAME = "assets/images/social"


ACCENTS: list[tuple[str, tuple[str, str, str]]] = [
    ("centella", ("#eef8ef", "#cfe7d1", "#2f6b4f")),
    ("cica", ("#eef8ef", "#cfe7d1", "#2f6b4f")),
    ("acne", ("#edf9f5", "#cdeee1", "#2d6a4f")),
    ("leg scars", ("#fff2ea", "#f4d2bf", "#b05d37")),
    ("niacinamide", ("#eef7ff", "#d6e6f5", "#40607f")),
    ("retinol", ("#f4f6ff", "#d8ddf5", "#41508b")),
    ("vitamin c", ("#fff6df", "#f4d48e", "#b06d00")),
    ("วิตามินซี", ("#fff6df", "#f4d48e", "#b06d00")),
    ("sunscreen", ("#fff4db", "#f1d28b", "#a56a00")),
    ("กันแดด", ("#fff4db", "#f1d28b", "#a56a00")),
    ("makeup", ("#fff0f4", "#f4c4d2", "#9a4d6f")),
    ("lip", ("#ffe7ec", "#f1bcc8", "#a54c66")),
    ("perfume", ("#f7eef9", "#e0c9ea", "#7a4d8f")),
    ("hair", ("#eef8f0", "#d9eadb", "#4a7d5d")),
    ("anti-aging", ("#f8efe7", "#e6c3a6", "#9a5d3d")),
    ("whitening", ("#fff6e8", "#efd9ae", "#9a6a1d")),
    ("moisturizer", ("#eef4fb", "#d4e2f1", "#476279")),
    ("cleanser", ("#f0f8f7", "#d0e5e1", "#3f6c69")),
]

DEFAULT_ACCENT = ("#f8efe6", "#efd7bf", "#8b5e3c")


def _social_asset_path(root: Path, page_path: Path) -> Path:
    rel = page_path.relative_to(root)
    if rel.as_posix() == "index.html":
        return root / SOCIAL_IMAGE_DIR_NAME / "home.svg"
    if rel.name == "index.html":
        return root / SOCIAL_IMAGE_DIR_NAME / rel.parent / "cover.svg"
    if rel.suffix.lower() == ".html":
        return root / SOCIAL_IMAGE_DIR_NAME / rel.with_suffix(".svg")
    return root / SOCIAL_IMAGE_DIR_NAME / rel / "cover.svg"


def _wrap_lines(text: str, width: int, max_lines: int) -> list[str]:
    text = re.sub(r"\s+", " ", text.strip())
    if not text:
        return []
    lines = textwrap.wrap(
        text,
        width=width,
        break_long_words=True,
        break_on_hyphens=False,
    )
    if len(lines) <= max_lines:
        return lines
    clipped = lines[:max_lines]
    clipped[-1] = clipped[-1].rstrip(" .,-–—") + "…"
    return clipped


def _accent_for(page_path: Path, title: str, description: str) -> tuple[str, str, str]:
    text = f"{page_path.as_posix()} {title} {description}".lower()
    for key, colors in ACCENTS:
        if key in text:
            return colors
    return DEFAULT_ACCENT


def _category_label(root: Path, page_path: Path) -> str:
    rel = page_path.relative_to(root)
    if rel.as_posix() == "index.html":
        return "SkincareThai"
    if rel.name == "index.html" and len(rel.parts) >= 2:
        return rel.parts[0]
    if rel.suffix.lower() == ".html":
        return rel.stem
    return "SkincareThai"


def _build_cover_svg(title: str, description: str, chip: str, colors: tuple[str, str, str]) -> str:
    bg_a, bg_b, accent = colors
    title_lines = _wrap_lines(title, width=22, max_lines=3) or ["SkincareThai"]
    subtitle_lines = _wrap_lines(description, width=40, max_lines=2)
    title_tspans = []
    for idx, line in enumerate(title_lines):
        dy = "0" if idx == 0 else "1.25em"
        title_tspans.append(f'<tspan x="80" dy="{dy}">{html.escape(line)}</tspan>')
    subtitle_tspans = []
    for idx, line in enumerate(subtitle_lines):
        dy = "0" if idx == 0 else "1.1em"
        subtitle_tspans.append(f'<tspan x="80" dy="{dy}">{html.escape(line)}</tspan>')

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630" role="img" aria-label="{html.escape(title)}">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{bg_a}"/>
      <stop offset="55%" stop-color="{bg_b}"/>
      <stop offset="100%" stop-color="#ffffff"/>
    </linearGradient>
    <linearGradient id="glow" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{accent}" stop-opacity="0.92"/>
      <stop offset="100%" stop-color="{accent}" stop-opacity="0.18"/>
    </linearGradient>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="16" stdDeviation="24" flood-color="#3f2d1f" flood-opacity="0.16"/>
    </filter>
  </defs>
  <rect width="1200" height="630" fill="url(#bg)"/>
  <circle cx="1010" cy="122" r="132" fill="url(#glow)"/>
  <circle cx="1028" cy="122" r="74" fill="#ffffff" fill-opacity="0.42"/>
  <circle cx="150" cy="540" r="186" fill="{accent}" fill-opacity="0.10"/>
  <circle cx="228" cy="116" r="90" fill="#ffffff" fill-opacity="0.42"/>
  <rect x="72" y="76" rx="999" ry="999" width="196" height="44" fill="#ffffff" fill-opacity="0.72"/>
  <text x="170" y="105" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="18" font-weight="700" fill="#4f3b2a">SkincareThai</text>
  <text x="80" y="180" font-family="Arial, Helvetica, sans-serif" font-size="24" font-weight="700" fill="{accent}">{html.escape(chip)}</text>
  <text x="80" y="270" font-family="Arial, Helvetica, sans-serif" font-size="56" font-weight="800" fill="#17212b">{''.join(title_tspans)}</text>
  <text x="80" y="394" font-family="Arial, Helvetica, sans-serif" font-size="26" font-weight="500" fill="#5a5f66">{''.join(subtitle_tspans)}</text>
  <g filter="url(#shadow)">
    <rect x="780" y="334" width="334" height="182" rx="28" fill="#ffffff" fill-opacity="0.94"/>
    <rect x="780" y="334" width="334" height="16" rx="8" fill="{accent}"/>
    <text x="816" y="400" font-family="Arial, Helvetica, sans-serif" font-size="24" font-weight="700" fill="#1f1f1f">อ่านง่าย • ใช้ตัดสินใจได้จริง</text>
    <text x="816" y="444" font-family="Arial, Helvetica, sans-serif" font-size="18" font-weight="500" fill="#5d5d66">social image tuned for SEO</text>
    <text x="816" y="486" font-family="Arial, Helvetica, sans-serif" font-size="18" font-weight="500" fill="#5d5d66">skincarethai.com</text>
  </g>
</svg>
"""


def _ensure_social_svg(root: Path, page_path: Path, title: str, description: str) -> Path:
    svg_path = _social_asset_path(root, page_path)
    svg_path.parent.mkdir(parents=True, exist_ok=True)
    chip = _category_label(root, page_path)
    svg = _build_cover_svg(title, description, chip, _accent_for(page_path, title, description))
    svg_path.write_text(svg, encoding="utf-8")
    return svg_path


def _find_first_img_src(content: str) -> str | None:
    img_match = re.search(r"<img\b[^>]*>", content, flags=re.IGNORECASE | re.DOTALL)
    if not img_match:
        return None
    tag = img_match.group(0)
    src_match = re.search(r'\bsrc\s*=\s*"([^"]+)"', tag, flags=re.IGNORECASE)
    if src_match:
        return src_match.group(1).strip()
    src_match = re.search(r"\bsrc\s*=\s*'([^']+)'", tag, flags=re.IGNORECASE)
    if src_match:
        return src_match.group(1).strip()
    return None


def _find_first_img_alt(content: str) -> str | None:
    img_match = re.search(r"<img\b[^>]*>", content, flags=re.IGNORECASE | re.DOTALL)
    if not img_match:
        return None
    tag = img_match.group(0)
    alt_match = re.search(r'\balt\s*=\s*"([^"]*)"', tag, flags=re.IGNORECASE)
    if alt_match:
        return alt_match.group(1).strip()
    alt_match = re.search(r"\balt\s*=\s*'([^']*)'", tag, flags=re.IGNORECASE)
    if alt_match:
        return alt_match.group(1).strip()
    return None


def _resolve_src_to_url(page_path: Path, src: str, root: Path, site_base: str) -> str:
    parsed = urlparse(src)
    if parsed.scheme in {"http", "https"} or src.startswith("//"):
        return src if parsed.scheme else f"https:{src}"
    if src.startswith("/"):
        return urljoin(site_base, src)
    resolved = (page_path.parent / src).resolve()
    try:
        rel = resolved.relative_to(root.resolve()).as_posix()
    except ValueError:
        return src
    return urljoin(site_base + "/", quote(rel))


def select_page_image(
    root: Path,
    page_path: Path,
    content: str,
    title: str,
    description: str,
    site_base: str = SITE_BASE,
) -> tuple[str, str]:
    """Pick a relevant image for SEO/social use.

    Prefer the first inline image from the page body. If the page has no image,
    generate a consistent topic-aware SVG cover and return its absolute URL.
    """

    src = _find_first_img_src(content)
    alt = _find_first_img_alt(content) or title
    if src:
        return _resolve_src_to_url(page_path, src, root, site_base), alt

    svg_path = _ensure_social_svg(root, page_path, title, description)
    rel = svg_path.relative_to(root).as_posix()
    return urljoin(site_base + "/", quote(rel)), title
