#!/usr/bin/env python3
"""Backfill Thai-first SEO metadata across the static site.

This script updates HTML files in place:
- canonical URL
- meta description
- Open Graph tags
- Twitter card tags
- theme color

It avoids external dependencies so it can run on the VPS or locally.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import quote

from seo_images import select_page_image


ROOT = Path(__file__).resolve().parents[1]
SITE_BASE = "https://skincarethai.com"
THEME_COLOR = "#f5efe9"


def html_files(root: Path):
    seen = set()
    for pattern in ("*.html", "index.html"):
        for path in root.rglob(pattern):
            if path.is_file() and path not in seen:
                seen.add(path)
                yield path


def slug_to_label(slug: str) -> str:
    slug = slug.replace("-", " ").strip()
    if not slug:
        return "SkincareThai"
    return slug[:1].upper() + slug[1:]


def normalize_review_title(text: str) -> str:
    if "หยือไม่ใช่" in text:
        return "รองพื้นไม่เกาะผิวทำยังไง? 5 วิธีให้หน้าเนียนกริบ"
    text = re.sub(r"^\s*เจาะลึกรีวิว\s*", "รีวิว ", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*สรุปชัดจากทุกแหล่งโซเชียล\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s{2,}", " ", text)
    text = re.sub(r"\s+:", ":", text)
    return text.strip(" -:|")


CATEGORY_LABELS = {
    "acne": "รีวิวปัญหาสิว",
    "anti-aging": "รีวิวลดเลือนริ้วรอย",
    "beauty-sleep": "รีวิวบิวตี้สลีป",
    "belotelo": "รีวิว BELOTELO",
    "biore": "รีวิว Biore",
    "cetaphil": "รีวิว Cetaphil",
    "cezanne": "รีวิว Cezanne",
    "cleanser": "รีวิวคลีนเซอร์",
    "cutepress": "รีวิว Cute Press",
    "dr.jill": "รีวิว Dr.Jill",
    "dr.wu": "รีวิว DR.WU",
    "galderma": "รีวิว Galderma",
    "hair-care": "รีวิวดูแลผม",
    "innbeauty": "รีวิว INN Beauty",
    "ipsa": "รีวิว IPSA",
    "kanebo": "รีวิว KANEBO",
    "klairs": "รีวิว KLAIRS",
    "laneige": "รีวิว Laneige",
    "lip": "รีวิวลิป",
    "makeup": "รีวิวเมคอัพ",
    "melamii": "รีวิว Melamii",
    "mizumi": "รีวิว MizuMi",
    "moisturizer": "รีวิวมอยเจอร์ไรเซอร์",
    "none": "รีวิวไม่มีชื่อแบรนด์",
    "ocean-skin": "รีวิว Ocean Skin",
    "perfume": "รีวิวน้ำหอม",
    "prada-beauty": "รีวิว Prada Beauty",
    "scagel": "รีวิว Scagel",
    "sekkisei": "รีวิว SEKKISEI",
    "senka": "รีวิว SENKA",
    "sk-ii": "รีวิว SK-II",
    "skintific": "รีวิว Skintific",
    "sunscreen": "รีวิวกันแดด",
    "teoxane": "รีวิว TEOXANE",
    "thermage": "รีวิว THERMAGE",
    "thursday-plantation": "รีวิว Thursday Plantation",
    "whitening": "รีวิวผิวกระจ่างใส",
    "you": "รีวิว YOU",
    "yanhee": "รีวิวยันฮี",
    "ข้อศอกดำ": "ข้อศอกดำแก้ยังไง",
    "ทำจมูก": "รีวิวทำจมูก",
    "บลัช": "รีวิวบลัช",
    "รองพื้น": "รีวิวรองพื้น",
    "รีวิวเครื่องสำอาง": "รีวิวเครื่องสำอาง",
    "ลิปกลอส": "รีวิวลิปกลอส",
    "เซรั่มผิวกาย": "รีวิวเซรั่มผิวกาย",
    "แป้ง": "รีวิวแป้ง",
    "แป้งขาวมณี": "รีวิวแป้งขาวมณี",
    "ไฟฟ้าสถิต": "รีวิวไฟฟ้าสถิต",
}

ROOT_TITLES = {
    "acne.html": "รีวิวสกินแคร์สำหรับคนเป็นสิว",
    "anti-aging.html": "รีวิวสกินแคร์ลดเลือนริ้วรอย",
    "beauty-sleep.html": "รีวิวบิวตี้สลีปและการฟื้นผิวตอนกลางคืน",
    "belotelo.html": "รีวิว BELOTELO และงานผิวสายคลินิก",
    "biore.html": "รีวิว Biore และไอเท็มดูแลผิวประจำวัน",
    "cetaphil.html": "รีวิว Cetaphil สำหรับผิวแพ้ง่าย",
    "cezanne.html": "รีวิว Cezanne เมคอัพสายคุมมัน",
    "cleanser.html": "รีวิวคลีนเซอร์และคลีนซิ่ง",
    "cutepress.html": "รีวิว Cute Press สกินแคร์และเมคอัพ",
    "dr.jill.html": "รีวิว Dr.Jill และซีรั่มสายชุ่มชื้น",
    "dr.wu.html": "รีวิว DR.WU และสกินแคร์สายบำรุง",
    "galderma.html": "รีวิว Galderma และงานผิวเชิงคลินิก",
    "hair-care.html": "รีวิวดูแลผมและแก้ปัญหาผมร่วง",
    "innbeauty.html": "รีวิว Inn Beauty และไอเท็มเซเว่น",
    "ipsa.html": "รีวิว IPSA และกันแดด/บำรุงเนื้อเบา",
    "kanebo.html": "รีวิว KANEBO และงานผิวสายลักชัวรี",
    "klairs.html": "รีวิว KLAIRS สำหรับผิวแพ้ง่าย",
    "lancôme.html": "รีวิว Lancôme สกินแคร์และน้ำหอม",
    "laneige.html": "รีวิว Laneige และงานผิวสายชุ่มชื้น",
    "lip.html": "รีวิวลิปสติกและลิปบาล์ม",
    "makeup.html": "รีวิวเมคอัพและงานผิว",
    "melamii.html": "รีวิว Melamii และไอเท็มดูแลฝ้า",
    "mizumi.html": "รีวิว MizuMi สำหรับผิวแพ้ง่าย",
    "moisturizer.html": "รีวิวมอยเจอร์ไรเซอร์และครีมบำรุง",
    "none.html": "รีวิวไม่มีแบรนด์และตัวเลือกเฉพาะทาง",
    "ocean-skin.html": "รีวิว Ocean Skin และสกินแคร์ราคาดี",
    "perfume.html": "รีวิวน้ำหอมและกลิ่นหอมติดทน",
    "prada-beauty.html": "รีวิว Prada Beauty และงานบิวตี้สายลักชัวรี",
    "scagel.html": "รีวิว Scagel และเจลแต้มสิว",
    "sekkisei.html": "รีวิว SEKKISEI และงานผิวสายชุ่มชื้น",
    "senka.html": "รีวิว SENKA และคลีนเซอร์ญี่ปุ่น",
    "sk-ii.html": "รีวิว SK-II และพิเทร่าในมุมใช้งานจริง",
    "skintific.html": "รีวิว Skintific และงานผิวเนียนกริบ",
    "sunscreen.html": "รีวิวกันแดดและไอเท็มปกป้องผิว",
    "teoxane.html": "รีวิว TEOXANE และฟิลเลอร์งานผิว",
    "thermage.html": "รีวิว Thermage และเทคโนโลยียกกระชับ",
    "thursday-plantation.html": "รีวิว Thursday Plantation และทีทรีออยล์",
    "whitening.html": "รีวิวผิวกระจ่างใสและลดรอยคล้ำ",
    "you.html": "รีวิว YOU และกันแดดสายคุมมัน",
    "yanhee.html": "รีวิวยันฮีและไอเท็มดูแลเส้นผม",
    "ข้อศอกดำ.html": "ข้อศอกดำแก้ยังไง",
    "ทำจมูก.html": "รีวิวทำจมูกและประสบการณ์คลินิก",
    "บลัช.html": "รีวิวบลัชออนและสีแก้ม",
    "รองพื้น.html": "รีวิวรองพื้นและงานผิว",
    "รีวิวเครื่องสำอาง.html": "รีวิวเครื่องสำอางทั้งหมด",
    "ลิปกลอส.html": "รีวิวลิปกลอสและลิปฉ่ำวาว",
    "เซรั่มผิวกาย.html": "รีวิวเซรั่มผิวกาย",
    "แป้ง.html": "รีวิวแป้งและแป้งผสมรองพื้น",
    "แป้งขาวมณี.html": "รีวิวแป้งขาวมณี",
    "ไฟฟ้าสถิต.html": "ไฟฟ้าสถิตเกิดจากอะไร",
}


def category_label(path: Path) -> str | None:
    parts = path.relative_to(ROOT).parts
    if len(parts) < 2:
        return None
    first = parts[0]
    if first in CATEGORY_LABELS:
        return CATEGORY_LABELS[first]
    if first.endswith(".html"):
        stem = first[:-5]
        return CATEGORY_LABELS.get(stem)
    return None


def title_for(path: Path, original: str | None) -> str:
    if path.name == "index.html" and path.parent == ROOT:
        return "SkincareThai | รีวิวสกินแคร์ เครื่องสำอาง และบิวตี้ภาษาไทย"
    if path.name.endswith(".html") and path.parent == ROOT:
        return f"{ROOT_TITLES.get(path.name, slug_to_label(path.stem))} | SkincareThai"
    if path.name == "index.html":
        if path.parent != ROOT and original:
            base = original.split("|")[0].strip()
            base = normalize_review_title(base)
            return f"{base} | SkincareThai"
        parent = path.parent.name
        label = CATEGORY_LABELS.get(parent, slug_to_label(parent))
        return f"{label} | SkincareThai"
    if original:
        return normalize_review_title(original.strip())
    return "SkincareThai"


def description_for(path: Path, title: str) -> str:
    if path.name == "index.html" and path.parent == ROOT:
        return (
            "SkincareThai รวมรีวิวสกินแคร์ เครื่องสำอาง และไอเท็มบิวตี้จากหลายแหล่ง "
            "พร้อมสรุปภาษาไทยที่อ่านง่าย ใช้ตัดสินใจได้จริง และเหมาะกับคนไทย"
        )
    label = category_label(path)
    if label:
        return (
            f"{label} พร้อมสรุปจุดเด่น ข้อควรระวัง และมุมมองแบบภาษาไทยร่วมสมัย "
            "เพื่อช่วยให้เลือกซื้อได้ตรงกับผิวและงบของคุณ"
        )
    return (
        f"{title} สรุปแบบภาษาไทยจากหลายแหล่งข้อมูล พร้อมประเด็นสำคัญ ข้อดี ข้อควรระวัง "
        "และคำแนะนำว่าเหมาะกับใคร"
    )


def canonical_for(path: Path) -> str:
    rel = path.relative_to(ROOT).as_posix()
    if rel == "index.html":
        return f"{SITE_BASE}/"
    if rel.endswith("/index.html"):
        return f"{SITE_BASE}/{rel[:-10]}"
    if rel.endswith(".html"):
        return f"{SITE_BASE}/{rel}"
    return f"{SITE_BASE}/{quote(rel)}"


def schema_for(path: Path, title: str, description: str, canonical: str) -> str | None:
    image_url = None
    if path.exists():
        try:
            image_url, _ = select_page_image(ROOT, path, path.read_text(encoding="utf-8"), title, description, SITE_BASE)
        except Exception:
            image_url = None
    if path.name == "index.html" and path.parent == ROOT:
        payload = {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "name": "SkincareThai",
            "url": canonical,
            "description": description,
            "inLanguage": "th-TH",
            **({"image": image_url} if image_url else {}),
            "publisher": {
                "@type": "Organization",
                "name": "SkincareThai",
                "url": SITE_BASE,
            },
        }
    elif path.name == "index.html":
        parent = path.parent.name
        payload = {
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            "name": title,
            "url": canonical,
            "description": description,
            "inLanguage": "th-TH",
            **({"image": image_url} if image_url else {}),
            "isPartOf": {
                "@type": "WebSite",
                "name": "SkincareThai",
                "url": SITE_BASE,
            },
            "about": CATEGORY_LABELS.get(parent, slug_to_label(parent)),
        }
    else:
        payload = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": title,
            "url": canonical,
            "description": description,
            "inLanguage": "th-TH",
            **({"image": image_url} if image_url else {}),
            "isPartOf": {
                "@type": "WebPage",
                "url": canonical.rsplit("/", 1)[0] + "/",
            },
            "author": {
                "@type": "Organization",
                "name": "SkincareThai",
                "url": SITE_BASE,
            },
            "publisher": {
                "@type": "Organization",
                "name": "SkincareThai",
                "url": SITE_BASE,
            },
        }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def replace_or_insert_schema(content: str, schema: str) -> str:
    block = f'    <script type="application/ld+json">\n{schema}\n    </script>'
    pattern = re.compile(r"\s*<script type=\"application/ld\+json\">.*?</script>\s*", re.IGNORECASE | re.DOTALL)
    if pattern.search(content):
        return pattern.sub("\n" + block + "\n", content, count=1)
    return content.replace("</head>", block + "\n</head>", 1)


def normalize_visible_titles(content: str) -> str:
    content = re.sub(
        r"(<h1 class=\"hero-title\">)(.*?)(</h1>)",
        lambda m: f"{m.group(1)}{normalize_review_title(m.group(2))}{m.group(3)}",
        content,
        flags=re.IGNORECASE | re.DOTALL,
    )
    content = re.sub(
        r"(<h3 class=\"post-card-title\"><a[^>]*>)(.*?)(</a></h3>)",
        lambda m: f"{m.group(1)}{normalize_review_title(re.sub(r'<[^>]+>', '', m.group(2)))}{m.group(3)}",
        content,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return content


def insert_meta_block(head: str, tags: str) -> str:
    if "<meta name=\"description\"" in head:
        head = re.sub(
            r"\s*<meta name=\"description\"[^>]*>\s*",
            "\n",
            head,
            count=1,
            flags=re.IGNORECASE,
        )
    if "<link rel=\"canonical\"" in head:
        head = re.sub(
            r"\s*<link rel=\"canonical\"[^>]*>\s*",
            "\n",
            head,
            count=1,
            flags=re.IGNORECASE,
        )
    if "property=\"og:title\"" in head:
        head = re.sub(
            r"\s*<meta property=\"og:[^\"]+\"[^>]*>\s*",
            "\n",
            head,
            count=0,
            flags=re.IGNORECASE,
        )
    if "name=\"twitter:card\"" in head:
        head = re.sub(
            r"\s*<meta name=\"twitter:[^\"]+\"[^>]*>\s*",
            "\n",
            head,
            count=0,
            flags=re.IGNORECASE,
        )
    if "property=\"og:image\"" in head:
        head = re.sub(
            r"\s*<meta property=\"og:image[^\"]*\"[^>]*>\s*",
            "\n",
            head,
            count=0,
            flags=re.IGNORECASE,
        )
    if "name=\"twitter:image\"" in head:
        head = re.sub(
            r"\s*<meta name=\"twitter:image[^\"]*\"[^>]*>\s*",
            "\n",
            head,
            count=0,
            flags=re.IGNORECASE,
        )
    if "name=\"theme-color\"" in head:
        head = re.sub(
            r"\s*<meta name=\"theme-color\"[^>]*>\s*",
            "\n",
            head,
            count=1,
            flags=re.IGNORECASE,
        )

    anchor = r"(<meta charset=\"UTF-8\">\s*)"
    if re.search(anchor, head, flags=re.IGNORECASE):
        return re.sub(anchor, r"\1" + tags + "\n", head, count=1, flags=re.IGNORECASE)
    anchor = r"(<meta name=\"viewport\"[^>]*>\s*)"
    if re.search(anchor, head, flags=re.IGNORECASE):
        return re.sub(anchor, r"\1" + tags + "\n", head, count=1, flags=re.IGNORECASE)
    return tags + "\n" + head


def update_file(path: Path) -> bool:
    original = path.read_text(encoding="utf-8")
    title_match = re.search(r"<title>(.*?)</title>", original, flags=re.IGNORECASE | re.DOTALL)
    original_title = title_match.group(1).strip() if title_match else None
    title = title_for(path, original_title)
    description = description_for(path, title)
    canonical = canonical_for(path)
    image_url, image_alt = select_page_image(ROOT, path, original, title, description, SITE_BASE)
    og_type = "website" if path == ROOT / "index.html" or (path.name.endswith(".html") and path.parent == ROOT) else "article"

    if "<head>" not in original or "</head>" not in original:
        return False

    tags = "\n".join(
        [
            f'    <meta name="description" content="{description}">',
            f'    <link rel="canonical" href="{canonical}">',
            f'    <meta property="og:site_name" content="SkincareThai">',
            f'    <meta property="og:title" content="{title}">',
            f'    <meta property="og:description" content="{description}">',
            f'    <meta property="og:url" content="{canonical}">',
            f'    <meta property="og:type" content="{og_type}">',
            f'    <meta property="og:image" content="{image_url}">',
            f'    <meta property="og:image:alt" content="{image_alt}">',
            f'    <meta name="twitter:card" content="summary_large_image">',
            f'    <meta name="twitter:title" content="{title}">',
            f'    <meta name="twitter:description" content="{description}">',
            f'    <meta name="twitter:image" content="{image_url}">',
            f'    <meta name="twitter:image:alt" content="{image_alt}">',
            f'    <meta name="theme-color" content="{THEME_COLOR}">',
        ]
    )

    head_match = re.search(r"<head>(.*?)</head>", original, flags=re.IGNORECASE | re.DOTALL)
    if not head_match:
        return False
    head = head_match.group(1)
    new_head = insert_meta_block(head, tags)
    if title_match:
        new_head = re.sub(
            r"<title>.*?</title>",
            f"<title>{title}</title>",
            new_head,
            count=1,
            flags=re.IGNORECASE | re.DOTALL,
        )
    new_content = original[: head_match.start(1)] + new_head + original[head_match.end(1) :]
    new_content = normalize_visible_titles(new_content)
    schema = schema_for(path, title, description, canonical)
    if schema:
        new_content = replace_or_insert_schema(new_content, schema)

    if new_content != original:
        path.write_text(new_content, encoding="utf-8")
        return True
    return False


def main() -> int:
    changed = 0
    for path in html_files(ROOT):
        if update_file(path):
            changed += 1
    print(f"Updated {changed} HTML files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
