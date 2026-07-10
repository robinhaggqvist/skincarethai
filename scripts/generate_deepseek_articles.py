#!/usr/bin/env python3
"""
Generate unique Thai skincare article pages using DeepSeek via OpenRouter.
Takes a list of draft topics and writes them as individual topic/ pages.

Usage:
    python3 scripts/generate_deepseek_articles.py [--all | --topic "topic name"]
"""

import os
import sys
import json
import time
import glob
import re
import urllib.request
import urllib.error

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOPICS_DIR = os.path.join(BASE_DIR, "topics")
TRASH_DIR = os.path.join(BASE_DIR, ".trash", "topics_boilerplate")

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

DRAFT_TOPICS = [
    {
        "slug": "รีวิวครีมหน้าใส-ในมุมที่คนไทยกำลังสนใจ",
        "title": "รีวิวครีมหน้าใส ในมุมที่คนไทยกำลังสนใจ",
        "subtitle": "รวมรีวิวครีมหน้าใส ที่คนไทยพูดถึงจริง ทั้งสูตรดังและตัวเทรนด์",
        "hint": "whitening cream, brightening cream",
        "faq_qs": ["ครีมหน้าใสกับครีมหน้าขาวต่างกันยังไง", "ครีมหน้าใสราคาถูกได้ผลไหม", "ใช้ครีมหน้าใสแล้วต้องใช้กันแดดทุกวันไหม"]
    },
    {
        "slug": "whitening-cream-review-ในมุมที่คนไทยกำลังสนใจ",
        "title": "whitening cream review ในมุมที่คนไทยกำลังสนใจ",
        "subtitle": "Whitening cream ตัวไหนที่คนไทยรีวิวแล้วเห็นผลจริง",
        "hint": "whitening cream, brightening, ครีมหน้าขาว",
        "faq_qs": ["Whitening cream ใช้ทุกวันได้ไหม", "Whitening cream กับคนผิวแพ้ง่ายอันตรายไหม", "ใช้ whitening cream แล้วต้องหยุดใช้ตัวอื่นไหม"]
    },
    {
        "slug": "serum-pantip-ในมุมที่คนไทยกำลังสนใจ",
        "title": "serum pantip ในมุมที่คนไทยกำลังสนใจ",
        "subtitle": "เซรั่มที่คน Pantip พูดถึงบ่อย รวมมาให้ละเอียดทั้งข้อดีและข้อเสีย",
        "hint": "serum, เซรั่ม, Pantip รีวิว",
        "faq_qs": ["เซรั่มตัวไหนที่คน Pantip รีวิวดีที่สุด", "เซรั่มราคาหลักร้อยเทียบกับหลักพันต่างกันไหม", "เซรั่มที่คน Pantip บอกว่าใช้แล้วเห็นผลจริง"]
    },
    {
        "slug": "ครีมหน้าใสไหนดี-ในมุมที่คนไทยกำลังสนใจ",
        "title": "ครีมหน้าใสไหนดี ในมุมที่คนไทยกำลังสนใจ",
        "subtitle": "เปรียบเทียบครีมหน้าใสยอดนิยม ว่าตัวไหนเหมาะกับผิวคุณ",
        "hint": "ครีมหน้าใส เปรียบเทียบ, whitening cream comparison",
        "faq_qs": ["ครีมหน้าใสยี่ห้ออะไรดี", "ครีมหน้าใสของญี่ปุ่นกับเกาหลีต่างกันไหม", "ครีมหน้าใสที่ผู้ชายใช้ได้มีตัวไหนบ้าง"]
    },
    {
        "slug": "ครีมหน้าใสราคา-ในมุมที่คนไทยกำลังสนใจ",
        "title": "ครีมหน้าใสราคา ในมุมที่คนไทยกำลังสนใจ",
        "subtitle": "ครีมหน้าใสแต่ละช่วงราคา ใช้งบเท่าไหร่ถึงคุ้ม",
        "hint": "ครีมหน้าใส ราคา, budget skincare",
        "faq_qs": ["ครีมหน้าใสราคาไม่เกิน 500 มีตัวไหนดี", "ครีมหน้าใสราคาหลักพันกับหลักร้อยต่างกันมากไหม", "ครีมหน้าใสราคาถูกที่คนไทยรีวิวเยอะ"]
    },
    {
        "slug": "personal-color-คืออะไร-วิธีเช็กโทนที่เหมาะกับผิวคนไทย",
        "title": "Personal Color คืออะไร? วิธีเช็กโทนที่เหมาะกับผิวคนไทย",
        "subtitle": "Personal color ไขข้อสงสัย คนไทยควรเช็กโทนสียังไง",
        "hint": "personal color, skin tone, โทนสีผิว",
        "faq_qs": ["Personal color จำเป็นไหม", "คนไทยส่วนใหญ่เป็น personal color โทนอะไร", "รู้ personal color แล้วเลือกสกินแคร์ต่างกันยังไง"]
    },
    {
        "slug": "กันแดดเด็กเลือกยังไง-รวมแนวทางเลือกแบบปลอดภัยและใช้จริง",
        "title": "กันแดดเด็กเลือกยังไง? รวมแนวทางเลือกแบบปลอดภัยและใช้จริง",
        "subtitle": "วิธีเลือกกันแดดสำหรับเด็ก ให้ปลอดภัยและใช้แล้วไม่ระคาย",
        "hint": "kids sunscreen, กันแดดเด็ก, baby sunscreen",
        "faq_qs": ["กันแดดเด็กต้อง SPF เท่าไหร่", "กันแดดแบบกายภาพกับเคมีต่างกันยังไง", "กันแดดเด็กต้องเช็ดออกยังไง"]
    },
    {
        "slug": "กันแดดซองตัวไหนดี-ตัวเลือกคุ้มๆ-สำหรับพกง่ายและใช้ทุกวัน",
        "title": "กันแดดซองตัวไหนดี? ตัวเลือกคุ้มๆ สำหรับพกง่ายและใช้ทุกวัน",
        "subtitle": "กันแดดซองที่คนไทยใช้จริง รีวิวทั้งเนื้อและความคุ้ม",
        "hint": "sachet sunscreen, กันแดดซอง, travel sunscreen",
        "faq_qs": ["กันแดดซองใช้ได้นานไหม", "กันแดดซองยี่ห้อไหนเนื้อดี", "กันแดดซองแพงกับถูกต่างกันไหม"]
    },
    {
        "slug": "รูขุมขนกว้างแก้ยังไง-วิธีดูแลผิวให้ดูเรียบขึ้นแบบไม่เวอร์",
        "title": "รูขุมขนกว้างแก้ยังไง? วิธีดูแลผิวให้ดูเรียบขึ้นแบบไม่เวอร์",
        "subtitle": "วิธีดูแลรูขุมขนกว้างที่ใช้ได้ผลจริง ไม่ใช่แค่คำพูดสวยหรู",
        "hint": "pore tightening, รูขุมขน, pore care",
        "faq_qs": ["รูขุมขนกว้างรักษาให้หายขาดได้ไหม", "เซรั่มลดรูขุมขนตัวไหนดี", "ร้อยไหมกับลดรูขุมขนต่างกันยังไง"]
    },
    {
        "slug": "แชมพูแก้ผมร่วงเลือกยังไง-สิ่งที่ควรดูและตัวอย่างแนวทางดูแล",
        "title": "แชมพูแก้ผมร่วงเลือกยังไง? สิ่งที่ควรดูและตัวอย่างแนวทางดูแล",
        "subtitle": "วิธีเลือกแชมพูแก้ผมร่วงที่เหมาะกับปัญหาและงบของคุณ",
        "hint": "hair loss shampoo, ผมร่วง, hair care",
        "faq_qs": ["แชมพูแก้ผมร่วงใช้แล้วเห็นผลจริงไหม", "แชมพูแก้ผมร่วงกับยาปลูกผมต่างกันยังไง", "แชมพูแก้ผมร่วงยี่ห้อไหนดี"]
    },
    {
        "slug": "กันแดดคนเป็นสิวควรเลือกแบบไหน-เนื้อสัมผัสและส่วนผสมที่ควรมองหา",
        "title": "กันแดดคนเป็นสิวควรเลือกแบบไหน? เนื้อสัมผัสและส่วนผสมที่ควรมองหา",
        "subtitle": "กันแดดสำหรับคนเป็นสิว เลือกยังไงให้ไม่มัน ไม่อุดตัน",
        "hint": "acne sunscreen, กันแดดคนเป็นสิว, sunscreen for acne",
        "faq_qs": ["คนเป็นสิวใช้กันแดดได้ไหม", "กันแดดแบบไหนไม่อุดตัน", "กันแดดคนเป็นสิวที่คนรีวิวเยอะ"]
    },
    {
        "slug": "ขาลายแก้ยังไง-วิธีดูแลรอยและผิวไม่สม่ำเสมอ",
        "title": "ขาลายแก้ยังไง? วิธีดูแลรอยและผิวไม่สม่ำเสมอ",
        "subtitle": "ไกด์ดูแลขาลายแบบคนอ่านแล้วเอาไปใช้ต่อได้จริง",
        "hint": "leg scars, ขาลาย, skin discoloration leg",
        "faq_qs": ["ขาลายหายยากเพราะอะไร", "ควรเริ่มจากอะไร", "ครีมลดรอยดำที่ขาตัวไหนดี"]
    }
]

TEMPLATE_HTML = """<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="description" content="{meta_desc}">
    <link rel="canonical" href="https://skincarethai.com/topics/{slug}/">
    <meta property="og:site_name" content="SkincareThai">
    <meta property="og:title" content="{og_title}">
    <meta property="og:description" content="{meta_desc}">
    <meta property="og:url" content="https://skincarethai.com/topics/{slug}/">
    <meta property="og:type" content="article">
    <meta property="og:image" content="https://skincarethai.com{og_img}">
    <meta property="og:image:alt" content="{og_title}">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{og_title}">
    <meta name="twitter:description" content="{meta_desc}">
    <meta name="twitter:image" content="https://skincarethai.com{og_img}">
    <meta name="twitter:image:alt" content="{og_title}">
    <meta name="theme-color" content="#f5efe9">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{page_title}</title>
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
        .content-body {{ margin-top: 24px; }}
        .content-body p {{ margin: 0 0 16px; }}
        .content-body h3 {{ margin-top: 28px; }}
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
    <script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "CollectionPage",
  "name": "{page_title}",
  "url": "https://skincarethai.com/topics/{slug}/",
  "description": "{meta_desc}",
  "inLanguage": "th-TH",
  "image": "https://skincarethai.com{og_img}",
  "isPartOf": {{
    "@type": "WebSite",
    "name": "SkincareThai",
    "url": "https://skincarethai.com"
  }},
  "about": "{about}"
}}
    </script>
</head>
<body>
    <nav class="nav"><div class="nav-inner"><a class="brand" href="/">SkincareThai</a><a href="/sitemap.xml">Sitemap</a></div></nav>
    <main class="shell">
        <section class="hero">
            <span class="eyebrow">Published {date}</span>
            <h1>{title}</h1>
            <p class="subtitle">{subtitle}</p>
        </section>

        <section class="grid">
            <article class="card">
                <h2>สรุปเร็ว</h2>
                <div class="content-body">
{summary_html}
                </div>
            </article>

            <aside class="card related">
                <h2>อ่านต่อ</h2>
                <ul>
{related_links}
                </ul>
                <h3>แนวทางใช้หน้า</h3>
                <p>ใช้หน้านี้เป็นจุดเริ่ม แล้วค่อยไล่ไปอ่านหน้าหมวดใกล้เคียงเพื่อเทียบมุมมองก่อนตัดสินใจ</p>
                <a class="cta" href="/sitemap.xml">ดูแผนผังเว็บไซต์</a>
            </aside>
        </section>

        <section class="card" style="margin-top:24px;">
            <h2>คำถามที่พบบ่อย</h2>
{faq_html}
        </section>

        <section class="card" style="margin-top:24px;">
            <h2>รีวิวและความคิดเห็นจากผู้ใช้จริง</h2>
            <div class="content-body">
{reviews_html}
            </div>
        </section>
    </main>
</body>
</html>"""


def call_deepseek(prompt, max_retries=3):
    """Call DeepSeek via OpenRouter."""
    data = json.dumps({
        "model": "deepseek/deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 2000,
        "temperature": 0.7,
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "https://skincarethai.com",
        },
    )

    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read())
                return result["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"  API call failed (attempt {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(5)
    return None


def sanitize_text(text):
    """Clean up text for use in HTML."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&#39;")


def generate_summary(topic):
    """Generate the summary section content."""
    prompt =  f"""เขียนเนื้อหาสกินแคร์สำหรับหน้าเว็บภาษาไทย หัวข้อ: "{topic['title']}"

สไตล์การเขียน: เป็นธรรมชาติ เหมือนบล็อกเกอร์ไทยทั่วไป เขียนแบบคนใช้จริง ไม่ใช่เว็บทางการแพทย์
- ใช้ภาษาไทยธรรมชาติ เหมือนคนไทยเขียนรีวิวบน Pantip หรือ Jeban
- เขียนแบบเข้าใจง่าย ไม่ต้องใช้ศัพท์เทคนิคเวอร์
- มีความเห็นส่วนตัวแทรกเล็กน้อยให้ดูสมจริง
- ประมาณ 200-300 คำภาษาไทย

ต้องการเนื้อหาสำหรับส่วนเหล่านี้:
1. **สรุปเร็ว** (1 ย่อหน้า สั้นกระชับ ว่าเนื้อหานี้เกี่ยวกับอะไร)
2. **เหมาะกับใคร** (3-4 ข้อ bullet points, ว่าเนื้อหานี้เหมาะกับคนแบบไหน)
3. **สิ่งที่ควรดู/ข้อดี** (2-3 ข้อ bullet points, จุดเด่นหรือสิ่งที่ควรรู้)
4. **ข้อควรระวัง** (2 ข้อ bullet points)
5. **เนื้อหาเพิ่มเติม** (1-2 ย่อหน้า อธิบายรายละเอียดเพิ่มเติม)

รูปแบบผลลัพธ์: ให้คืนเฉพาะ JSON format นี้เท่านั้น ไม่ต้องมีข้อความอื่น:
{{
  "summary_quick": "...",
  "who_is_it_for": ["...", "...", "..."],
  "key_points": ["...", "...", "..."],
  "cautions": ["...", "..."],
  "extra_content": ["...", "..."]
}}

อย่าเติมข้อความอื่นนอกเหนือจาก JSON"""
    return call_deepseek(prompt)


def generate_reviews(topic):
    """Generate reviews/user opinions section."""
    prompt = f"""เขียนส่วน "รีวิวและความคิดเห็นจากผู้ใช้จริง" สำหรับเว็บสกินแคร์ไทย หัวข้อ: "{topic['title']}"

สไตล์: เหมือนความคิดเห็นจากผู้ใช้จริงบน Pantip/Jeban แบบสั้นๆ
- ใช้ภาษาไทยที่คนทั่วไปใช้
- ความยาวรวม 150-250 คำ
- เขียน 3-4 ความคิดเห็นจำลอง แต่ละอัน 1-2 ประโยค
- ให้ความรู้สึกเป็นจริง ไม่เหมือนโฆษณา

รูปแบบผลลัพธ์: JSON array เท่านั้น:
["ความคิดเห็นที่ 1...", "ความคิดเห็นที่ 2...", "ความคิดเห็นที่ 3..."]

อย่าเติมข้อความอื่นนอกเหนือจาก JSON"""
    return call_deepseek(prompt)


def generate_faq_html(topic):
    """Generate FAQ section."""
    faq_parts = []
    for q in topic["faq_qs"]:
        prompt = f"""ตอบคำถามสั้นๆ 1-2 ประโยค ภาษาไทย เป็นธรรมชาติ ไม่เป็นทางการเกินไป:

คำถาม: {q}
หัวข้อ: {topic['title']}

ตอบสั้น กระชับ เข้าใจง่าย"""
        answer = call_deepseek(prompt)
        if answer:
            answer = answer.strip().strip('"').strip("'")
            faq_parts.append(f'        <details>\n            <summary>{sanitize_text(q)}</summary>\n            <p>{sanitize_text(answer)}</p>\n        </details>')
        time.sleep(2)

    return "\n".join(faq_parts) if faq_parts else ""


def slugify(text):
    """Create URL-safe slug (simple - keep Thai chars)."""
    # Keep Thai characters, hyphens, numbers
    return re.sub(r'[^\u0E00-\u0E7Fa-zA-Z0-9\-]', '-', text.lower()).strip('-').replace('--', '-')


def ensure_og_image(slug):
    """Check if OG image cover exists, return path."""
    img_dir = os.path.join(BASE_DIR, "assets", "images", "social", "topics")
    # Look for existing cover.svg
    for root, dirs, files in os.walk(img_dir):
        for f in files:
            if slug in root.replace(img_dir, "").lstrip("/") and f == "cover.svg":
                return f"/assets/images/social/topics/{os.path.relpath(os.path.join(root, f), img_dir)}"
    # Return default
    return f"/assets/images/social/{slug}.svg"


def generate_topic(topic):
    """Generate a single topic page."""
    slug = topic["slug"]
    title = topic["title"]
    subtitle = topic["subtitle"]
    date = "10 Jul 2026"

    print(f"\n{'='*60}")
    print(f"Generating: {title}")
    print(f"Slug: {slug}")
    print(f"{'='*60}")

    # Step 1: Generate summary section
    print("  [1/3] Generating summary content...")
    summary_json = generate_summary(topic)
    if not summary_json:
        print("  FAILED: Could not generate summary")
        return False

    # Parse JSON
    try:
        # Find JSON in response (it might have markdown fences)
        json_match = re.search(r'```(?:json)?\s*\n?({.*?})\n?\s*```', summary_json, re.DOTALL)
        if json_match:
            summary_data = json.loads(json_match.group(1))
        else:
            summary_data = json.loads(summary_json)
    except json.JSONDecodeError:
        print(f"  Failed to parse JSON response: {summary_json[:200]}")
        # Try to clean it up
        try:
            cleaned = summary_json.strip()
            if cleaned.startswith("{") and cleaned.endswith("}"):
                summary_data = json.loads(cleaned)
            else:
                print("  Could not extract JSON")
                return False
        except Exception:
            print("  Could not parse response")
            return False

    # Build summary HTML
    summary_parts = []
    summary_parts.append(f"<p>{sanitize_text(summary_data.get('summary_quick', ''))}</p>")
    
    who_for = summary_data.get("who_is_it_for", [])
    if who_for:
        summary_parts.append("<h3>เหมาะกับใคร</h3><ul>")
        for item in who_for:
            summary_parts.append(f"<li>{sanitize_text(item)}</li>")
        summary_parts.append("</ul>")

    key_pts = summary_data.get("key_points", [])
    if key_pts:
        summary_parts.append("<h3>สิ่งที่ควรดู</h3><ul>")
        for item in key_pts:
            summary_parts.append(f"<li>{sanitize_text(item)}</li>")
        summary_parts.append("</ul>")

    cautions = summary_data.get("cautions", [])
    if cautions:
        summary_parts.append("<h3>ข้อควรระวัง</h3><ul>")
        for item in cautions:
            summary_parts.append(f"<li>{sanitize_text(item)}</li>")
        summary_parts.append("</ul>")

    extra = summary_data.get("extra_content", [])
    if extra:
        for para in extra:
            summary_parts.append(f"<p>{sanitize_text(para)}</p>")

    summary_html = "\n".join(summary_parts)

    # Step 2: Generate reviews section
    print("  [2/3] Generating review/user opinions...")
    reviews_raw = generate_reviews(topic)
    reviews_html = ""
    if reviews_raw:
        try:
            json_match = re.search(r'```(?:json)?\s*\n?(\[.*?\])\n?\s*```', reviews_raw, re.DOTALL)
            if json_match:
                reviews_list = json.loads(json_match.group(1))
            else:
                reviews_list = json.loads(reviews_raw.strip())
            if isinstance(reviews_list, list):
                review_items = []
                for r in reviews_list:
                    review_items.append(f"<p>💬 {sanitize_text(r)}</p>")
                reviews_html = "\n".join(review_items)
        except (json.JSONDecodeError, Exception) as e:
            print(f"  Could not parse reviews: {e}")
            reviews_html = ""

    if not reviews_html:
        reviews_html = "<p>ยังไม่มีความคิดเห็นในส่วนนี้</p>"

    # Step 3: Generate FAQ
    print("  [3/3] Generating FAQ...")
    faq_html = generate_faq_html(topic)

    # Step 4: Assemble page
    meta_desc = sanitize_text(f"{title} | SkincareThai สรุปแบบภาษาไทยจากหลายแหล่งข้อมูล พร้อมประเด็นสำคัญ ข้อดี ข้อควรระวัง และคำแนะนำว่าเหมาะกับใคร")
    
    # Generate OG image path
    og_img = ensure_og_image(slug)
    if og_img == f"/assets/images/social/{slug}.svg":
        # Use default generic skincare cover
        og_img = "/assets/images/social/none.svg"

    about = sanitize_text(title)
    page_title = f"{title} | SkincareThai"
    og_title = sanitize_text(f"{title} | SkincareThai")

    # Related links
    related = [
        ("/whitening.html", "รีวิวผิวกระจ่างใสและลดรอยคล้ำ"),
        ("/sunscreen.html", "รีวิวกันแดดและไอเท็มปกป้องผิว"),
        ("/sitemap.xml", "ดูแผนผังเว็บไซต์"),
    ]
    related_links = "\n".join(f'<li><a href="{url}">{text}</a></li>' for url, text in related)

    # Fill template
    html = TEMPLATE_HTML.format(
        slug=slug,
        title=title,
        subtitle=subtitle,
        date=date,
        meta_desc=meta_desc,
        og_title=og_title,
        og_img=og_img,
        page_title=page_title,
        about=about,
        summary_html=summary_html,
        faq_html=faq_html,
        reviews_html=reviews_html,
        related_links=related_links,
    )

    # Write output
    topic_dir = os.path.join(TOPICS_DIR, slug)
    os.makedirs(topic_dir, exist_ok=True)
    with open(os.path.join(topic_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)

    print(f"  ✓ Written to topics/{slug}/index.html")
    return True


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="Generate all draft topics")
    parser.add_argument("--topic", type=str, help="Generate a specific topic by slug/name")
    args = parser.parse_args()

    os.chdir(BASE_DIR)
    os.makedirs(TOPICS_DIR, exist_ok=True)

    if args.topic:
        # Find by partial name
        matching = [t for t in DRAFT_TOPICS if args.topic.lower() in t["slug"].lower() or args.topic.lower() in t["title"].lower()]
        if not matching:
            print(f"No topic matching '{args.topic}'")
            sys.exit(1)
        topics = matching
    elif args.all:
        topics = DRAFT_TOPICS
    else:
        print("Specify --all or --topic <name>")
        sys.exit(1)

    successful = 0
    for topic in topics:
        ok = generate_topic(topic)
        if ok:
            successful += 1
        # Rate limit: 30s between calls to DeepSeek
        print("  Waiting 30 seconds before next API call...")
        time.sleep(30)

    print(f"\n{'='*60}")
    print(f"Done: {successful}/{len(topics)} pages generated")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
