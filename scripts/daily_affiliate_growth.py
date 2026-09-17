#!/usr/bin/env python3
"""Quality-gated daily publisher for SkincareThai."""

from __future__ import annotations

import argparse
import html
import json
import math
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SITE_BASE = "https://skincarethai.com"
REPORT_PATH = ROOT / "reports" / "daily_page_growth.md"
UNPUBLISHED_PATH = ROOT / "reports" / "unpublished_drafts.jsonl"
CALENDAR_PATH = ROOT / "reports" / "content_calendar.md"
QUEUE_PATH = ROOT / "reports" / "draft_idea_queue.md"
SITEMAP_PATH = ROOT / "sitemap.xml"
HOMEPAGE_PATH = ROOT / "index.html"
METADATA_SCRIPT = ROOT / "scripts" / "update_metadata.py"
REMOTE_HOST = "root@5.181.217.86"
REMOTE_KEY = Path("/home/robin/.ssh/homemodsau_server")
REMOTE_ROOT = "/home/skincarethai.com/public_html"


@dataclass(frozen=True)
class DraftItem:
    title: str
    topic: str
    sources: str = ""
    source_hint: str = ""
    seed_hints: int = 0
    seed_sources: int = 0
    suggested_angle: str = ""
    priority: int = 0


@dataclass(frozen=True)
class QualityAssessment:
    item: DraftItem
    score: int
    reasons: list[str]
    eligible: bool


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

GENERIC_ANGLE = "Compare what Thai readers want with the source writer's details, then add our own practical verdict."


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


def page_url(path: Path) -> str:
    rel = path.relative_to(ROOT).as_posix()
    if rel == "index.html":
        return SITE_BASE + "/"
    if rel.endswith("/index.html"):
        return SITE_BASE + "/" + rel[:-10]
    return SITE_BASE + "/" + rel


def social_asset_path(page_path: Path) -> Path:
    rel = page_path.relative_to(ROOT)
    if rel.as_posix() == "index.html":
        return ROOT / "assets" / "images" / "social" / "home.svg"
    if rel.name == "index.html":
        return ROOT / "assets" / "images" / "social" / rel.parent / "cover.svg"
    if rel.suffix.lower() == ".html":
        return ROOT / "assets" / "images" / "social" / rel.with_suffix(".svg")
    return ROOT / "assets" / "images" / "social" / rel / "cover.svg"


def parse_markdown_items(path: Path) -> dict[str, DraftItem]:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    items: dict[str, DraftItem] = {}
    for block in re.split(r"\n(?=## )", text):
        title_match = re.match(r"##\s+(.+)", block)
        topic_match = re.search(r"- Topic hint:\s*(.+)", block)
        if not title_match or not topic_match:
            continue
        raw_title = title_match.group(1).strip()
        title = raw_title.split("·", 1)[-1].strip() if "·" in raw_title else raw_title
        priority_match = re.search(r"- Priority:\s*(\d+)\s*/", block)
        items[title.lower()] = DraftItem(
            title=title,
            topic=topic_match.group(1).strip(),
            sources=(re.search(r"- Sources:\s*(.+)", block).group(1).strip() if re.search(r"- Sources:\s*(.+)", block) else ""),
            source_hint=(re.search(r"- Latest source:\s*(.+)", block).group(1).strip() if re.search(r"- Latest source:\s*(.+)", block) else ""),
            priority=(int(priority_match.group(1)) if priority_match else 0),
        )
    return items


def parse_queue_items(path: Path) -> dict[str, DraftItem]:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    items: dict[str, DraftItem] = {}
    for block in re.split(r"\n(?=## )", text):
        title_match = re.match(r"##\s+(.+)", block)
        topic_match = re.search(r"- Topic hint:\s*(.+)", block)
        if not title_match or not topic_match:
            continue
        raw_title = title_match.group(1).strip()
        title = raw_title.split("·", 1)[-1].strip() if "·" in raw_title else raw_title
        seed_match = re.search(r"- Seed idea:\s*(\d+)\s+hint\(s\)\s+from\s+(\d+)\s+source\(s\)", block)
        draft_match = re.search(r"- Draft idea:\s*(\d+)\s+hint\(s\)\s+from\s+(\d+)\s+source\(s\)", block)
        support_hints_match = re.search(r"- Supporting hints:\s*(\d+)", block)
        support_sources_match = re.search(r"- Supporting sources:\s*(\d+)", block)
        angle_match = re.search(r"- Suggested angle:\s*(.+)", block)
        items[title.lower()] = DraftItem(
            title=title,
            topic=topic_match.group(1).strip(),
            sources=re.search(r"- Sources:\s*(.+)", block).group(1).strip() if re.search(r"- Sources:\s*(.+)", block) else "",
            seed_hints=(
                int(support_hints_match.group(1))
                if support_hints_match
                else int((seed_match or draft_match).group(1)) if (seed_match or draft_match) else 0
            ),
            seed_sources=(
                int(support_sources_match.group(1))
                if support_sources_match
                else int((seed_match or draft_match).group(2)) if (seed_match or draft_match) else 0
            ),
            suggested_angle=(angle_match.group(1).strip() if angle_match else ""),
        )
    return items


def collect_candidates() -> list[DraftItem]:
    calendar_items = parse_markdown_items(CALENDAR_PATH)
    queue_items = parse_queue_items(QUEUE_PATH)
    ordered: list[DraftItem] = []
    seen: set[str] = set()

    for key, item in calendar_items.items():
        queue_item = queue_items.get(key)
        merged = DraftItem(
            title=item.title,
            topic=item.topic,
            sources=item.sources,
            source_hint=item.source_hint,
            seed_hints=(queue_item.seed_hints if queue_item else 0),
            seed_sources=(queue_item.seed_sources if queue_item else 0),
            suggested_angle=(queue_item.suggested_angle if queue_item else ""),
            priority=item.priority,
        )
        ordered.append(merged)
        seen.add(key)

    for key, item in queue_items.items():
        if key in seen:
            continue
        ordered.append(item)
    return ordered


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
    return TOPIC_PROFILES.get(topic_key(item.topic, item.title)) or build_fallback_profile(item.title, item.topic)


def make_page_slug(item: DraftItem, profile: dict[str, object]) -> str:
    title_slug = normalize(item.title)
    return title_slug or str(profile.get("slug") or "page")


def make_page_path(item: DraftItem, profile: dict[str, object]) -> Path:
    folder = ROOT.joinpath(*[str(part) for part in profile["path"]])
    slug = make_page_slug(item, profile)
    candidate = folder / slug / "index.html"
    return candidate


def page_description(item: DraftItem, profile: dict[str, object]) -> str:
    return f"{item.title.strip()} | SkincareThai. {str(profile['summary'])}"


def build_html(item: DraftItem, profile: dict[str, object], canonical: str) -> str:
    title = item.title.strip()
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
    related = "".join(f'<li><a href="{href}">{html.escape(label)}</a></li>' for href, label in profile["related"])
    evidence = item.sources or item.source_hint or "ยังไม่มีแหล่งอ้างอิงที่ชัดพอสำหรับการเผยแพร่"
    source_line = f"<strong>แหล่งที่ใช้ในรอบนี้:</strong> {html.escape(evidence)}"
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
</head>
<body>
    <nav class="nav"><div class="nav-inner"><a class="brand" href="/">SkincareThai</a><a href="/sitemap.xml">Sitemap</a></div></nav>
    <main class="shell">
        <section class="hero">
            <span class="eyebrow">Published {format_date()}</span>
            <h1>{html.escape(title)}</h1>
            <p class="subtitle">{html.escape(subtitle)}</p>
            <p class="meta">หน้านี้จะถูกเผยแพร่ก็ต่อเมื่อผ่านเกณฑ์คุณภาพ 90/100 ขึ้นไปเท่านั้น</p>
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


def save_unpublished(items: list[tuple[DraftItem, str, str]]) -> int:
    """Persist every non-published candidate with a reason for the next review."""
    existing: dict[str, dict[str, object]] = {}
    if UNPUBLISHED_PATH.exists():
        for line in UNPUBLISHED_PATH.read_text(encoding="utf-8").splitlines():
            try:
                row = json.loads(line)
                existing[str(row.get("key"))] = row
            except json.JSONDecodeError:
                continue
    for item, reason, status in items:
        key = f"{item.title.strip().lower()}|{item.topic.strip().lower()}"
        row = existing.get(key, {"key": key, "first_seen": date.today().isoformat()})
        row.update({
            "title": item.title,
            "topic": item.topic,
            "sources": item.sources,
            "source_hint": item.source_hint,
            "priority": item.priority,
            "reason": reason,
            "status": status,
            "last_seen": date.today().isoformat(),
        })
        existing[key] = row
    UNPUBLISHED_PATH.parent.mkdir(parents=True, exist_ok=True)
    UNPUBLISHED_PATH.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in existing.values()),
        encoding="utf-8",
    )
    return len(items)


def assess_quality(item: DraftItem, threshold: int) -> QualityAssessment:
    score = 45
    reasons: list[str] = []

    if item.sources:
        score += 12
        reasons.append("calendar has named sources")
    elif item.source_hint:
        score += 8
        reasons.append("calendar has latest source hint")
    else:
        reasons.append("no explicit source listed in calendar")

    if item.seed_sources >= 3:
        score += 14
        reasons.append(f"queue is backed by {item.seed_sources} sources")
    elif item.seed_sources >= 1:
        score += 9
        reasons.append(f"queue is backed by {item.seed_sources} source")
    else:
        reasons.append("queue has 0 source backing")

    if item.seed_hints >= 3:
        score += 10
        reasons.append(f"queue has {item.seed_hints} topic hints")
    elif item.seed_hints >= 1:
        score += 6
        reasons.append(f"queue has {item.seed_hints} topic hint")
    else:
        reasons.append("queue has 0 topic hints")

    if item.suggested_angle and item.suggested_angle != GENERIC_ANGLE:
        score += 8
        reasons.append("angle is custom instead of boilerplate")
    else:
        reasons.append("angle is still boilerplate")

    if re.search(r"[ก-๙]", item.title):
        score += 5
        reasons.append("title is Thai-first")
    if "?" in item.title or "อย่างไร" in item.title or "ยังไง" in item.title or "ดีไหม" in item.title:
        score += 4
        reasons.append("title reads like a real query")

    if item.priority >= 5:
        score += 2
        reasons.append("high-priority draft")

    score = min(score, 100)
    return QualityAssessment(item=item, score=score, reasons=reasons, eligible=score >= threshold)


def run_metadata(paths: list[Path], dry_run: bool) -> tuple[bool, list[Path]]:
    if dry_run or not paths:
        return False, []
    relative_paths = [str(path.relative_to(ROOT)) for path in paths]
    subprocess.run([sys.executable, str(METADATA_SCRIPT), *relative_paths], cwd=ROOT, check=True)
    assets = [social_asset_path(path) for path in paths if social_asset_path(path).exists()]
    return True, assets


def ssh_base() -> list[str]:
    return [
        "ssh",
        "-i",
        str(REMOTE_KEY),
        "-o",
        "BatchMode=yes",
        "-o",
        "StrictHostKeyChecking=accept-new",
        REMOTE_HOST,
    ]


def deploy_files(paths: list[Path], dry_run: bool) -> bool:
    if dry_run or not paths:
        return False
    unique_paths = sorted({path.resolve() for path in paths if path.exists()})
    for path in unique_paths:
        rel = path.relative_to(ROOT).as_posix()
        remote_dir = str(Path(REMOTE_ROOT, rel).parent)
        subprocess.run([*ssh_base(), f"mkdir -p {remote_dir!r}"], check=True)
        subprocess.run(
            [
                "rsync",
                "-az",
                "--chmod=Du=rwx,Dgo=rx,Fu=rw,Fgo=r",
                "-e",
                f"ssh -i {REMOTE_KEY} -o BatchMode=yes -o StrictHostKeyChecking=accept-new",
                str(path),
                f"{REMOTE_HOST}:{REMOTE_ROOT}/{rel}",
            ],
            check=True,
        )
    return True


def verify_live(page_urls: list[str], dry_run: bool) -> tuple[bool, bool]:
    if dry_run or not page_urls:
        return False, False
    sitemap = subprocess.run(
        ["curl", "-fsS", SITE_BASE + "/sitemap.xml"],
        check=False,
        capture_output=True,
        text=True,
    )
    sitemap_ok = sitemap.returncode == 0 and page_urls[0] in sitemap.stdout
    page = subprocess.run(
        ["curl", "-fsS", "-L", "-o", "/dev/null", "-w", "%{http_code}", page_urls[0]],
        check=False,
        capture_output=True,
        text=True,
    )
    page_ok = page.returncode == 0 and page.stdout.strip() == "200"
    return sitemap_ok, page_ok


def render_report(
    growth_rate: float,
    threshold: int,
    before_count: int,
    assessments: list[QualityAssessment],
    published: list[tuple[DraftItem, str]],
    local_generated: bool,
    live_uploaded: bool,
    sitemap_verified: bool,
    page_verified: bool,
    homepage_changed: bool,
    calendar_changed: bool,
    metadata_backfill: bool,
    dry_run: bool,
    saved_count: int,
) -> str:
    lines = [
        "# Daily Page Growth",
        "",
        f"- Growth rate target: {growth_rate:.0%}",
        f"- Quality threshold: {threshold}/100",
        f"- Page count before: {before_count}",
        f"- Drafts reviewed: {len(assessments)}",
        f"- Drafts eligible: {sum(1 for item in assessments if item.eligible)}",
        f"- New pages published: {0 if dry_run else len(published)}",
        f"- local generated: {'yes' if local_generated else 'no'}",
        f"- live files uploaded: {'yes' if live_uploaded else 'no'}",
        f"- live sitemap verified: {'yes' if sitemap_verified else 'no'}",
        f"- live page spot-check passed: {'yes' if page_verified else 'no'}",
        f"- Homepage updated: {'yes' if homepage_changed else 'no'}",
        f"- Calendar updated: {'yes' if calendar_changed else 'no'}",
        f"- Metadata backfill: {'yes' if metadata_backfill else 'no'}",
        f"- Unpublished drafts saved for review: {saved_count}",
        "",
        "## Quality Review",
        "",
    ]
    if assessments:
        for assessment in assessments:
            status = "PASS" if assessment.eligible else "HOLD"
            lines.append(
                f"- {status} {assessment.score}/100 · {assessment.item.title} · {'; '.join(assessment.reasons)}"
            )
    else:
        lines.append("- No draft pages available.")

    lines.extend(["", "## Published Pages", ""])
    if published:
        for item, url in published:
            lines.append(f"- {item.title} -> {url}")
    else:
        lines.append("- No new page was published this run; see the saved review queue for the exact reason.")

    if dry_run:
        lines.extend(["", "## Dry Run", "", "No files were written or uploaded."])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--growth-rate", type=float, default=0.05)
    parser.add_argument("--quality-threshold", type=int, default=90)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    before_count = page_count()
    target_files = max(1, math.ceil(before_count * args.growth_rate))
    candidates = collect_candidates()
    assessments = [assess_quality(item, args.quality_threshold) for item in candidates]
    eligible_assessments = [
        assessment
        for assessment in assessments
        if assessment.eligible and not make_page_path(assessment.item, profile_for(assessment.item)).exists()
    ]
    selected_assessments = eligible_assessments[:target_files]
    eligible = [assessment.item for assessment in selected_assessments]

    saved_items: list[tuple[DraftItem, str, str]] = []
    selected_keys = {f"{item.title.strip().lower()}|{item.topic.strip().lower()}" for item in eligible}
    for assessment in assessments:
        item = assessment.item
        key = f"{item.title.strip().lower()}|{item.topic.strip().lower()}"
        page_path = make_page_path(item, profile_for(item))
        if key in selected_keys:
            continue
        if not assessment.eligible:
            reason = f"quality score {assessment.score}/100 below threshold"
        elif page_path.exists():
            reason = "matching page already exists; review for update or consolidation"
        else:
            reason = "eligible but held by the monthly growth cap"
        saved_items.append((item, reason, "pending"))

    published: list[tuple[DraftItem, str]] = []
    created_paths: list[Path] = []

    for item in eligible:
        profile = profile_for(item)
        page_path = make_page_path(item, profile)
        url = page_url(page_path)
        if not args.dry_run:
            page_path.parent.mkdir(parents=True, exist_ok=True)
            page_path.write_text(build_html(item, profile, url), encoding="utf-8")
        created_paths.append(page_path)
        published.append((item, url))

    homepage_changed = False
    sitemap_changed = False
    calendar_changed = False
    metadata_backfill = False
    deployed = False
    sitemap_verified = False
    page_verified = False

    if not args.dry_run and published:
        sitemap_changed = update_sitemap([url for _, url in published])
        homepage_changed = update_homepage(published)
        calendar_changed = mark_calendar_published({item.title for item, _ in published})
        metadata_backfill, asset_paths = run_metadata(created_paths + [HOMEPAGE_PATH], args.dry_run)
        deploy_list = created_paths + [SITEMAP_PATH, HOMEPAGE_PATH]
        deploy_list.extend(asset_paths)
        deployed = deploy_files(deploy_list, args.dry_run)
        sitemap_verified, page_verified = verify_live([url for _, url in published], args.dry_run)

    saved_count = 0 if args.dry_run else save_unpublished(saved_items)

    report = render_report(
        growth_rate=args.growth_rate,
        threshold=args.quality_threshold,
        before_count=before_count,
        assessments=assessments,
        published=published,
        local_generated=bool(published) and not args.dry_run,
        live_uploaded=deployed,
        sitemap_verified=sitemap_verified,
        page_verified=page_verified,
        homepage_changed=homepage_changed,
        calendar_changed=calendar_changed,
        metadata_backfill=metadata_backfill,
        dry_run=args.dry_run,
        saved_count=saved_count,
    )
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(report.rstrip())
    print(f"Saved report to {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
