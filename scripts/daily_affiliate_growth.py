#!/usr/bin/env python3
"""Daily page-growth runner for SkincareThai.

The cron name still says "affiliate growth", but the live rule from Robin is:
grow the site by adding new published pages equal to about 5% of the current
page count. This script turns the next draft ideas into static HTML pages,
updates the sitemap, refreshes the homepage latest-posts block, and marks the
used calendar rows as published.
"""

from __future__ import annotations

import argparse
import html
import json
import math
import re
import subprocess
import sys
from collections import OrderedDict
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SITE_BASE = "https://skincarethai.com"
REPORT_PATH = ROOT / "reports" / "daily_page_growth.md"
CALENDAR_PATH = ROOT / "reports" / "content_calendar.md"
QUEUE_PATH = ROOT / "reports" / "draft_idea_queue.md"
SITEMAP_PATH = ROOT / "sitemap.xml"
HOMEPAGE_PATH = ROOT / "index.html"
METADATA_SCRIPT = ROOT / "scripts" / "update_metadata.py"


@dataclass(frozen=True)
class DraftItem:
    title: str
    topic: str
    sources: str = ""
    source_hint: str = ""


TOPIC_PROFILES: dict[str, dict[str, object]] = {
    "centella": {
        "slug": "centella-cica",
        "path": ["topics"],
        "subtitle": "สรุปแบบเข้าใจง่ายว่าทำไม Centella / Cica ถึงถูกใช้บ่อยในผิวแพ้ง่าย",
        "summary": "Centella / Cica คือกลุ่มส่วนผสมที่คนไทยมักมองหาเวลาผิวระคายง่าย แดงง่าย หรืออยากได้ตัวช่วยปลอบผิวแบบไม่ซับซ้อน",
        "best_for": ["ผิวแพ้ง่าย", "คนที่ผิวแดงง่าย", "คนที่อยากเริ่มรูทีนแบบอ่อนโยน"],
        "cautions": ["ถ้าผิวมีอาการแพ้บ่อยควร patch test ก่อน", "อย่าคาดหวังผลลัพธ์แบบเร่งด่วนทันที"],
        "what_to_look_for": ["อ่านส่วนผสมให้ดูว่ามีสารปลอบผิวจริง", "ดูเนื้อสัมผัสให้เหมาะกับสภาพผิว", "เลือกคู่กับกันแดดและมอยเจอร์ไรเซอร์ที่สบายผิว"],
        "related": [("/acne.html", "รีวิวสกินแคร์สำหรับคนเป็นสิว"), ("/moisturizer.html", "รีวิวมอยเจอร์ไรเซอร์และครีมบำรุง"), ("/whitening.html", "รีวิวผิวกระจ่างใสและลดรอยคล้ำ")],
        "faq": [
            ("Centella / Cica เหมาะกับใคร?", "เหมาะกับคนที่ผิวระคายง่าย ต้องการตัวช่วยปลอบผิว และอยากได้รูทีนที่ไม่รกเกินไป"),
            ("ใช้ทุกวันได้ไหม?", "โดยทั่วไปใช้ได้ แต่ควรดูความเข้ากันกับผลิตภัณฑ์อื่นในรูทีนของคุณ"),
        ],
    },
    "leg scars": {
        "slug": "leg-scars",
        "path": ["topics"],
        "subtitle": "ไกด์ดูแลขาลายแบบคนอ่านแล้วเอาไปใช้ต่อได้จริง",
        "summary": "ขาลายมักเกิดจากรอยดำ รอยแผลเก่า ผิวแห้ง หรือการเสียดสีซ้ำๆ การดูแลที่ดีต้องเน้นฟื้นผิวและลดการระคายเคืองพร้อมกัน",
        "best_for": ["คนที่มีรอยดำตามขา", "คนที่ผิวไม่สม่ำเสมอ", "คนที่อยากแต่งขาให้ดูเนียนขึ้น"],
        "cautions": ["ถ้ามีแผลอักเสบหรือผื่นควรรักษาสาเหตุหลักก่อน", "อย่าขัดผิวแรงเกินไปจนรอยหนักกว่าเดิม"],
        "what_to_look_for": ["เลือกสารที่ช่วยเรื่องรอยและความชุ่มชื้น", "ใช้กันแดดกับผิวที่โดนแดด", "ดูพฤติกรรมที่ทำให้เกิดการเสียดสีซ้ำ"],
        "related": [("/whitening.html", "รีวิวผิวกระจ่างใสและลดรอยคล้ำ"), ("/moisturizer.html", "รีวิวมอยเจอร์ไรเซอร์และครีมบำรุง"), ("/beauty-sleep.html", "รีวิวบิวตี้สลีปและการฟื้นผิวตอนกลางคืน")],
        "faq": [
            ("ขาลายหายยากเพราะอะไร?", "เพราะรอยมักสะสมหลายชั้น ทั้งสีผิว ความแห้ง และพฤติกรรมที่กระตุ้นซ้ำ"),
            ("ควรเริ่มจากอะไร?", "เริ่มจากบำรุงให้ผิวชุ่มชื้น ลดการเสียดสี และใช้กันแดดเมื่อขาโดนแดด"),
        ],
    },
    "niacinamide": {
        "slug": "niacinamide",
        "path": ["topics"],
        "subtitle": "สรุปการใช้ Niacinamide แบบไม่ยัดศัพท์ให้เวียนหัว",
        "summary": "Niacinamide เป็นส่วนผสมสายอเนกประสงค์ที่หลายคนใช้เพื่อช่วยเรื่องความมัน รูขุมขน และรอยหมองคล้ำ แต่ต้องใช้ให้เหมาะกับผิวจริง",
        "best_for": ["คนผิวมัน", "คนมีรอยสิว", "คนที่อยากเริ่ม active แบบไม่แรงเกิน"],
        "cautions": ["บางคนระคายเคืองถ้าใช้ความเข้มข้นสูงทันที", "อย่าซ้อนหลายตัวจนรูทีนหนักเกิน"],
        "what_to_look_for": ["ดูความเข้มข้นและความสม่ำเสมอในการใช้", "เช็กว่าผลิตภัณฑ์เข้ากับผิวมันหรือผิวแพ้ง่าย", "จับคู่กับมอยเจอร์ไรเซอร์เพื่อคุมความแห้ง"],
        "related": [("/acne.html", "รีวิวสกินแคร์สำหรับคนเป็นสิว"), ("/whitening.html", "รีวิวผิวกระจ่างใสและลดรอยคล้ำ"), ("/sunscreen.html", "รีวิวกันแดดและไอเท็มปกป้องผิว")],
        "faq": [
            ("Niacinamide ใช้เช้าได้ไหม?", "ใช้ได้ถ้าผลิตภัณฑ์ที่เลือกเหมาะกับการใช้ตอนเช้าและตามด้วยกันแดด"),
            ("ต้องใช้เยอะแค่ไหนถึงเห็นผล?", "สม่ำเสมอสำคัญกว่าการลงเยอะในครั้งเดียว"),
        ],
    },
    "retinol": {
        "slug": "retinol",
        "path": ["topics"],
        "subtitle": "คู่มือเริ่มเรตินอลแบบปลอดภัยสำหรับมือใหม่",
        "summary": "Retinol เป็น active ที่คนพูดถึงเยอะเพราะช่วยเรื่องผิวดูเรียบและริ้วรอย แต่ก็เป็นตัวที่ต้องเริ่มอย่างมีระบบเพื่อไม่ให้ผิวลอกหรือระคายเคืองเกินไป",
        "best_for": ["มือใหม่ที่อยากเริ่มดูแล anti-aging", "คนที่มีปัญหาผิวไม่เรียบ", "คนที่รับมือกับรูทีนสม่ำเสมอได้"],
        "cautions": ["เริ่มถี่น้อยก่อน", "ต้องทากันแดดทุกวัน", "อย่าจับคู่กับหลาย active แรงๆ ตั้งแต่วันแรก"],
        "what_to_look_for": ["เลือกความแรงที่เหมาะกับประสบการณ์", "ใช้ร่วมกับมอยเจอร์ไรเซอร์", "ดูปฏิกิริยาผิว 2-4 สัปดาห์แรก"],
        "related": [("/anti-aging.html", "รีวิวสกินแคร์ลดเลือนริ้วรอย"), ("/moisturizer.html", "รีวิวมอยเจอร์ไรเซอร์และครีมบำรุง"), ("/sunscreen.html", "รีวิวกันแดดและไอเท็มปกป้องผิว")],
        "faq": [
            ("เริ่ม Retinol ยังไงให้ไม่พัง?", "เริ่มจากความถี่ต่ำ ใช้ปริมาณน้อย และเน้นกันแดดกับมอยเจอร์ไรเซอร์"),
            ("ถ้าผิวลอกต้องหยุดไหม?", "ควรลดความถี่หรือพักตามอาการ แล้วค่อยกลับมาแบบค่อยเป็นค่อยไป"),
        ],
    },
    "vitamin c": {
        "slug": "vitamin-c",
        "path": ["topics"],
        "subtitle": "วิธีเลือกวิตามินซีทาหน้าให้ใช้ได้จริงในชีวิตประจำวัน",
        "summary": "วิตามินซีเป็นตัวเลือกยอดนิยมสำหรับคนที่อยากได้ผิวดูสว่างขึ้น แต่การเลือกสูตรและการจับคู่กับผลิตภัณฑ์อื่นสำคัญมากกว่าชื่อส่วนผสมอย่างเดียว",
        "best_for": ["คนที่อยากดูแลผิวหมองคล้ำ", "คนที่อยากจัดรูทีนเช้าให้ครบ", "คนที่อยากได้ active ที่เข้ากับกันแดด"],
        "cautions": ["บางสูตรแสบหรือไม่เสถียร", "ควรเริ่มทีละน้อยถ้าผิวไว", "อย่าลืมกันแดดเพราะใช้วิตซีแล้วไม่ได้แปลว่าผิวทนแดดขึ้น"],
        "what_to_look_for": ["ดูสูตรที่เหมาะกับสภาพผิว", "เช็กความเสถียรของแพ็กเกจจิ้ง", "ใช้คู่กับกันแดดทุกวัน"],
        "related": [("/whitening.html", "รีวิวผิวกระจ่างใสและลดรอยคล้ำ"), ("/sunscreen.html", "รีวิวกันแดดและไอเท็มปกป้องผิว"), ("/moisturizer.html", "รีวิวมอยเจอร์ไรเซอร์และครีมบำรุง")],
        "faq": [
            ("วิตามินซีใช้เช้าหรือเย็น?", "หลายสูตรใช้ได้ทั้งสองช่วง แต่ถ้าใช้ตอนเช้าควรตามด้วยกันแดด"),
            ("ต้องเลี่ยงอะไรไหม?", "เลี่ยงการซ้อน active แรงหลายตัวพร้อมกันถ้าผิวยังไม่คุ้น"),
        ],
    },
}


def page_count() -> int:
    return sum(1 for path in ROOT.rglob("*.html") if path.is_file())


def format_date(value: date | None = None) -> str:
    value = value or date.today()
    return value.strftime("%d %b %Y")


def normalize(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^0-9a-zก-๙]+", "-", text)
    text = re.sub(r"-{2,}", "-", text)
    return text.strip("-")


def parse_markdown_items(path: Path) -> list[DraftItem]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    items: list[DraftItem] = []
    blocks = re.split(r"\n(?=## )", text)
    for block in blocks:
        title_match = re.match(r"##\s+(.+)", block)
        topic_match = re.search(r"- Topic hint:\s*(.+)", block)
        if not title_match or not topic_match:
            continue
        raw_title = title_match.group(1).strip()
        title = raw_title.split("·", 1)[-1].strip() if "·" in raw_title else raw_title
        topic = topic_match.group(1).strip()
        sources_match = re.search(r"- Sources:\s*(.+)", block)
        source_match = re.search(r"- Latest source:\s*(.+)", block)
        items.append(
            DraftItem(
                title=title,
                topic=topic,
                sources=(sources_match.group(1).strip() if sources_match else ""),
                source_hint=(source_match.group(1).strip() if source_match else ""),
            )
        )
    return items


def parse_queue_items(path: Path) -> list[DraftItem]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    items: list[DraftItem] = []
    for block in re.split(r"\n(?=## )", text):
        title_match = re.match(r"##\s+(.+)", block)
        topic_match = re.search(r"- Topic hint:\s*(.+)", block)
        if not title_match or not topic_match:
            continue
        raw_title = title_match.group(1).strip()
        title = raw_title.split("·", 1)[-1].strip() if "·" in raw_title else raw_title
        items.append(
            DraftItem(
                title=title,
                topic=topic_match.group(1).strip(),
                sources=re.search(r"- Sources:\s*(.+)", block).group(1).strip() if re.search(r"- Sources:\s*(.+)", block) else "",
            )
        )
    return items


def topic_key(topic: str, title: str) -> str:
    text = f"{topic} {title}".lower()
    if "centella" in text or "cica" in text:
        return "centella"
    if "leg scars" in text or "ขาลาย" in text:
        return "leg scars"
    if "niacinamide" in text:
        return "niacinamide"
    if "retinol" in text or "เรตินอล" in text:
        return "retinol"
    if "vitamin c" in text or "วิตามินซี" in text or "vit c" in text:
        return "vitamin c"
    return "centella"


def build_fallback_profile(title: str, topic: str) -> dict[str, object]:
    slug = normalize(title)[:80] or normalize(topic) or "page"
    return {
        "slug": slug,
        "path": ["topics"],
        "subtitle": f"สรุปประเด็นสำคัญของ {title} แบบอ่านง่าย",
        "summary": f"หน้าใหม่นี้สรุปหัวข้อ {title} พร้อมแนวทางอ่านต่อและข้อควรพิจารณาในมุมที่ใช้งานได้จริง",
        "best_for": ["คนที่กำลังหาข้อมูลเรื่องนี้", "คนที่อยากได้สรุปสั้นและชัด", "คนที่อยากอ่านต่อแบบเป็นระบบ"],
        "cautions": ["ควรเทียบข้อมูลกับสภาพผิวและเป้าหมายของตัวเอง", "ถ้าผิวไวควรเริ่มจากสิ่งที่อ่อนโยนก่อน"],
        "what_to_look_for": ["อ่านภาพรวมก่อนลงรายละเอียด", "เช็กว่ามีคำเตือนหรือไม่", "ดูว่ามีลิงก์ไปหน้าที่เกี่ยวข้องหรือไม่"],
        "related": [("/index.html", "หน้าแรก"), ("/sitemap.xml", "แผนผังเว็บไซต์")],
        "faq": [
            (f"{title} เหมาะกับใคร?", "เหมาะกับคนที่กำลังมองหาคำตอบแบบตรงประเด็นและเอาไปใช้ต่อได้"),
            ("ควรอ่านหน้าไหนต่อ?", "อ่านหน้าที่เกี่ยวกับหมวดเดียวกันเพื่อเทียบมุมมองและบริบท"),
        ],
    }


def profile_for(item: DraftItem) -> dict[str, object]:
    key = topic_key(item.topic, item.title)
    profile = TOPIC_PROFILES.get(key)
    if profile:
        return profile
    return build_fallback_profile(item.title, item.topic)


def make_page_slug(item: DraftItem, profile: dict[str, object]) -> str:
    title_slug = normalize(item.title)
    return title_slug or str(profile.get("slug") or "page")


def make_page_path(item: DraftItem, profile: dict[str, object]) -> Path:
    folder = ROOT.joinpath(*[str(part) for part in profile["path"]])
    slug = make_page_slug(item, profile)
    candidate = folder / slug / "index.html"
    suffix = 2
    while candidate.exists():
        candidate = folder / f"{slug}-{suffix}" / "index.html"
        suffix += 1
    return candidate


def relative_url(path: Path) -> str:
    rel = path.relative_to(ROOT).as_posix()
    if rel.endswith("/index.html"):
        return "/" + rel[:-10]
    if rel == "index.html":
        return "/"
    if rel.endswith(".html"):
        return "/" + rel
    return "/" + rel.rstrip("/")


def page_title(item: DraftItem) -> str:
    return item.title.strip()


def page_description(item: DraftItem, profile: dict[str, object]) -> str:
    summary = str(profile["summary"])
    return f"{page_title(item)} | SkincareThai. {summary}"


def build_html(item: DraftItem, profile: dict[str, object], canonical: str) -> str:
    title = page_title(item)
    description = page_description(item, profile)
    subtitle = str(profile["subtitle"])
    summary = str(profile["summary"])
    best_for = "".join(f"<li>{html.escape(text)}</li>" for text in profile["best_for"])
    cautions = "".join(f"<li>{html.escape(text)}</li>" for text in profile["cautions"])
    look_for = "".join(f"<li>{html.escape(text)}</li>" for text in profile["what_to_look_for"])
    faq_html = "".join(
        f"""
        <details>
            <summary>{html.escape(question)}</summary>
            <p>{html.escape(answer)}</p>
        </details>
        """
        for question, answer in profile["faq"]
    )
    related = "".join(
        f'<li><a href="{href}">{html.escape(label)}</a></li>'
        for href, label in profile["related"]
    )
    source_line = f"<strong>แหล่งที่ใช้ในรอบนี้:</strong> {html.escape(item.sources or item.source_hint or 'content calendar')}"
    return f"""<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="description" content="{html.escape(description)}">
    <link rel="canonical" href="{html.escape(canonical)}">
    <meta property="og:site_name" content="SkincareThai">
    <meta property="og:title" content="{html.escape(title)} | SkincareThai">
    <meta property="og:description" content="{html.escape(description)}">
    <meta property="og:url" content="{html.escape(canonical)}">
    <meta property="og:type" content="article">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{html.escape(title)} | SkincareThai">
    <meta name="twitter:description" content="{html.escape(description)}">
    <meta name="theme-color" content="#f5efe9">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(title)} | SkincareThai</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif; line-height: 1.7; color: #1d1d1f; background: linear-gradient(180deg, #fffaf6 0%, #ffffff 40%, #fff 100%); }}
        a {{ color: #0d6efd; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        .nav {{ position: sticky; top: 0; backdrop-filter: blur(18px); background: rgba(255, 255, 255, 0.78); border-bottom: 1px solid rgba(0, 0, 0, 0.08); z-index: 10; }}
        .nav-inner {{ max-width: 1080px; margin: 0 auto; padding: 18px 24px; display: flex; justify-content: space-between; align-items: center; }}
        .brand {{ font-size: 20px; font-weight: 700; color: #1d1d1f; }}
        .shell {{ max-width: 1080px; margin: 0 auto; padding: 36px 24px 72px; }}
        .hero {{ background: linear-gradient(135deg, #f8efe6, #fff); border: 1px solid #f0e1d3; border-radius: 28px; padding: 40px; box-shadow: 0 24px 60px rgba(120, 82, 50, 0.08); }}
        .eyebrow {{ display: inline-block; font-size: 12px; letter-spacing: .12em; text-transform: uppercase; color: #8b5e3c; margin-bottom: 18px; }}
        h1 {{ font-size: clamp(34px, 5vw, 56px); line-height: 1.05; margin: 0 0 14px; letter-spacing: -0.03em; }}
        .subtitle {{ font-size: 20px; color: #5f5b57; margin: 0; max-width: 760px; }}
        .meta {{ margin-top: 20px; color: #7a736d; font-size: 14px; }}
        .grid {{ display: grid; grid-template-columns: 1.15fr .85fr; gap: 24px; margin-top: 28px; }}
        .card {{ background: rgba(255,255,255,.9); border: 1px solid #eee2d8; border-radius: 24px; padding: 28px; box-shadow: 0 18px 44px rgba(0,0,0,.04); }}
        .card h2 {{ margin-top: 0; font-size: 24px; }}
        .card h3 {{ font-size: 18px; margin-top: 28px; margin-bottom: 10px; }}
        ul {{ margin: 12px 0 0 20px; padding: 0; }}
        li {{ margin-bottom: 8px; }}
        details {{ border-top: 1px solid #eee2d8; padding: 16px 0; }}
        details summary {{ cursor: pointer; font-weight: 600; }}
        .related {{ background: #fff7ef; border-color: #f0d2b8; }}
        .footer-note {{ margin-top: 18px; color: #6a625c; font-size: 14px; }}
        .cta {{ display: inline-block; margin-top: 10px; padding: 12px 18px; background: #1d1d1f; color: #fff; border-radius: 999px; font-weight: 600; }}
        .cta:hover {{ text-decoration: none; opacity: .92; }}
        @media (max-width: 860px) {{
            .hero {{ padding: 28px; }}
            .grid {{ grid-template-columns: 1fr; }}
        }}
    </style>
    <script type="application/ld+json">{json.dumps({
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "url": canonical,
        "description": description,
        "inLanguage": "th-TH",
        "datePublished": date.today().isoformat(),
        "dateModified": date.today().isoformat(),
        "author": {"@type": "Organization", "name": "SkincareThai", "url": SITE_BASE},
        "publisher": {"@type": "Organization", "name": "SkincareThai", "url": SITE_BASE},
    }, ensure_ascii=False)}</script>
</head>
<body>
    <nav class="nav"><div class="nav-inner"><a class="brand" href="/">SkincareThai</a><a href="/sitemap.xml">Sitemap</a></div></nav>
    <main class="shell">
        <section class="hero">
            <span class="eyebrow">Published {format_date()}</span>
            <h1>{html.escape(title)}</h1>
            <p class="subtitle">{html.escape(subtitle)}</p>
            <p class="meta">อ่านเร็ว: หน้าใหม่นี้เป็นส่วนหนึ่งของ daily page growth และตั้งใจให้เป็นสรุปที่ช่วยตัดสินใจได้จริง</p>
        </section>

        <section class="grid">
            <article class="card">
                <h2>สรุปเร็ว</h2>
                <p>{html.escape(summary)}</p>
                <h3>เหมาะกับใคร</h3>
                <ul>{best_for}</ul>
                <h3>สิ่งที่ควรดู</h3>
                <ul>{look_for}</ul>
                <h3>ข้อควรระวัง</h3>
                <ul>{cautions}</ul>
                <p class="footer-note">{source_line}</p>
            </article>

            <aside class="card related">
                <h2>อ่านต่อ</h2>
                <ul>{related}</ul>
                <h3>แนวทางใช้หน้า</h3>
                <p>ใช้หน้านี้เป็นจุดเริ่ม แล้วค่อยไล่ไปอ่านหน้าหมวดใกล้เคียงเพื่อเทียบมุมมองก่อนตัดสินใจ</p>
                <a class="cta" href="/sitemap.xml">ดูแผนผังเว็บไซต์</a>
            </aside>
        </section>

        <section class="card" style="margin-top:24px;">
            <h2>คำถามที่พบบ่อย</h2>
            {faq_html}
        </section>
    </main>
</body>
</html>
"""


def page_title_card(item: DraftItem, url: str) -> str:
    return f"""
        <div class="post-card">
            <div class="post-card-content">
                <h3 class="post-card-title"><a href="{html.escape(url)}">{html.escape(item.title)}</a></h3>
                <p class="post-card-date">อัปเดตเมื่อ: {format_date()}</p>
            </div>
        </div>
    """


def update_homepage(new_pages: list[tuple[DraftItem, str]]) -> bool:
    if not HOMEPAGE_PATH.exists():
        return False
    text = HOMEPAGE_PATH.read_text(encoding="utf-8")
    block_match = re.search(r"(<!-- Latest Posts -->\s*<main class=\"section\">\s*<h2 class=\"section-title\">บทความล่าสุด</h2>\s*<div class=\"post-grid\">)(.*?)(\s*</div>\s*</main>)", text, flags=re.S)
    if not block_match:
        return False
    existing_cards = block_match.group(2)
    cards = "".join(page_title_card(item, url) for item, url in new_pages)
    new_block = block_match.group(1) + "\n" + cards + "\n" + existing_cards.strip() + block_match.group(3)
    updated = text[: block_match.start()] + new_block + text[block_match.end() :]
    if updated != text:
        HOMEPAGE_PATH.write_text(updated, encoding="utf-8")
        return True
    return False


def update_sitemap(new_urls: list[str]) -> bool:
    if not SITEMAP_PATH.exists():
        return False
    text = SITEMAP_PATH.read_text(encoding="utf-8")
    existing = set(re.findall(r"<loc>(.*?)</loc>", text))
    additions = []
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    for url in new_urls:
        if url in existing:
            continue
        additions.append(f"<url><loc>{html.escape(url)}</loc><lastmod>{now}</lastmod><priority>0.8</priority></url>")
    if not additions:
        return False
    updated = text.replace("</urlset>", "\n" + "\n".join(additions) + "\n</urlset>")
    SITEMAP_PATH.write_text(updated, encoding="utf-8")
    return True


def mark_calendar_published(selected_titles: set[str]) -> bool:
    if not CALENDAR_PATH.exists():
        return False
    text = CALENDAR_PATH.read_text(encoding="utf-8")
    updated = text
    for title in selected_titles:
        pattern = re.compile(rf"(##\s+.*?{re.escape(title)}.*?\n(?:- .*\n)*?- Status:\s*)draft", flags=re.S)
        updated = pattern.sub(r"\1published", updated)
    if updated != text:
        CALENDAR_PATH.write_text(updated, encoding="utf-8")
        return True
    return False


def collect_candidates(limit: int) -> list[DraftItem]:
    calendar_items = parse_markdown_items(CALENDAR_PATH)
    queue_items = parse_queue_items(QUEUE_PATH)
    seen: set[str] = set()
    candidates: list[DraftItem] = []
    for item in calendar_items + queue_items:
        key = item.title.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        candidates.append(item)
        if len(candidates) >= limit:
            break
    return candidates


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--growth-rate", type=float, default=0.05)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    current_pages = page_count()
    target_files = max(1, math.ceil(current_pages * args.growth_rate))
    candidates = collect_candidates(max(target_files, 10))
    selected = candidates[:target_files]

    published: list[tuple[DraftItem, str]] = []
    created_paths: list[Path] = []
    created_urls: list[str] = []

    for item in selected:
        profile = profile_for(item)
        page_path = make_page_path(item, profile)
        url = SITE_BASE + relative_url(page_path)
        if not args.dry_run:
            page_path.parent.mkdir(parents=True, exist_ok=True)
            page_path.write_text(build_html(item, profile, url), encoding="utf-8")
        created_paths.append(page_path)
        created_urls.append(url)
        published.append((item, url))

    sitemap_changed = False
    homepage_changed = False
    calendar_changed = False
    if not args.dry_run:
        sitemap_changed = update_sitemap(created_urls)
        homepage_changed = update_homepage(published)
        calendar_changed = mark_calendar_published({item.title for item, _ in published})
        subprocess.run([sys.executable, str(METADATA_SCRIPT)], cwd=ROOT, check=True)

    report_lines = [
        "# Daily Page Growth",
        "",
        f"- Growth rate target: {args.growth_rate:.0%}",
        f"- Page count before: {current_pages}",
        f"- New pages targeted: {target_files}",
        f"- New pages published: {0 if args.dry_run else len(published)}",
        f"- Sitemap updated: {'yes' if sitemap_changed else 'no'}",
        f"- Homepage updated: {'yes' if homepage_changed else 'no'}",
        f"- Calendar updated: {'yes' if calendar_changed else 'no'}",
        f"- Metadata backfill: {'yes' if not args.dry_run else 'no'}",
        "",
        "## Published Pages",
        "",
    ]
    if published:
        for item, url in published:
            report_lines.append(f"- {item.title} -> {url}")
    else:
        report_lines.append("- No draft pages available.")
    report_lines.append("")

    if args.dry_run:
        report_lines.append("## Dry Run")
        report_lines.append("")
        report_lines.append("No files were written.")
        report_lines.append("")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(report_lines), encoding="utf-8")
    print("\n".join(report_lines))
    print(f"Saved report to {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
