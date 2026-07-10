#!/usr/bin/env python3
"""Generate a redesigned homepage for SkincareThai with proper Thai beauty blog aesthetics."""
import os, re

REPO = "/home/robin/.openclaw/workspace/skincarethai-repo"

# Collect topic data
topic_data = {}
for d in os.listdir(os.path.join(REPO, "topics")):
    topic_dir = os.path.join(REPO, "topics", d)
    if not os.path.isdir(topic_dir):
        continue
    index_file = os.path.join(topic_dir, "index.html")
    if not os.path.exists(index_file):
        continue
    with open(index_file, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    title_match = re.search(r'<title>(.*?)</title>', content)
    title = title_match.group(1).strip() if title_match else d
    title = re.sub(r'\s*\|\s*SkincareThai\s*$', '', title, flags=re.IGNORECASE)
    title = title.strip()
    # Get excerpt from meta description
    desc_match = re.search(r'<meta name="description" content="([^"]+)"', content)
    snippet = desc_match.group(1) if desc_match else ""
    # Truncate snippet
    if len(snippet) > 150:
        snippet = snippet[:147] + "..."
    topic_data[d] = {'dir': d, 'title': title, 'snippet': snippet}

# Categorize
categories = {
    "ผิวหน้า": [],
    "กันแดด": [],
    "ผม": [],
    "ผิวกาย": [],
}
for slug, data in sorted(topic_data.items(), key=lambda x: x[1]['title']):
    t = data['title']
    if 'กันแดด' in t:
        categories["กันแดด"].append(data)
    elif 'ผมร่วง' in t or 'แชมพู' in t:
        categories["ผม"].append(data)
    elif 'ขาลาย' in t:
        categories["ผิวกาย"].append(data)
    else:
        categories["ผิวหน้า"].append(data)

# Category icons/emojis
cat_emoji = {
    "ผิวหน้า": "✨",
    "กันแดด": "☀️",
    "ผม": "💇‍♀️",
    "ผิวกาย": "🦵",
}

# Build topic cards per category
def build_category_section(cat_name, items):
    cards_html = ""
    for item in items:
        cards_html += f'''            <a href="/topics/{item['dir']}/" class="topic-card">
                <div class="topic-card-body">
                    <h3 class="topic-card-title">{item['title']}</h3>
                    <p class="topic-card-snippet">{item['snippet']}</p>
                </div>
            </a>
'''
    return f'''        <section class="category-section" id="{cat_name}">
            <div class="section-header">
                <span class="section-emoji">{cat_emoji.get(cat_name, '📋')}</span>
                <h2 class="section-title">{cat_name}</h2>
                <span class="section-count">{len(items)} บทความ</span>
            </div>
            <div class="topic-grid">
{cards_html}            </div>
        </section>'''

category_html = ""
for cat_name in ["ผิวหน้า", "กันแดด", "ผิวกาย", "ผม"]:
    if categories[cat_name]:
        category_html += build_category_section(cat_name, categories[cat_name]) + "\n"

# Build hub links for footer (sitemap-compliant)
hub_links = [
    ("หน้าแรก", "/"),
    ("บทความทั้งหมด", "/sitemap.xml"),
    ("Whitening", "/whitening.html"),
    ("Sunscreen", "/sunscreen.html"),
    ("Acne", "/acne.html"),
    ("Anti-Aging", "/anti-aging.html"),
    ("Cleanser", "/cleanser.html"),
    ("Moisturizer", "/moisturizer.html"),
    ("Makeup", "/makeup.html"),
    ("Lip", "/lip.html"),
    ("Perfume", "/perfume.html"),
    ("Hair Care", "/hair-care.html"),
    ("Biore", "/biore.html"),
    ("Cetaphil", "/cetaphil.html"),
    ("SK-II", "/sk-ii.html"),
    ("Laneige", "/laneige.html"),
    ("Lancôme", "/lanc%C3%B4me.html"),
    ("Senka", "/senka.html"),
    ("Yanhee", "/yanhee.html"),
    ("None", "/none.html"),
]

# EMOJI / visual icons for hub pages
hub_icons = {
    "หน้าแรก": "🏠", "บทความทั้งหมด": "📚",
    "Whitening": "✨", "Sunscreen": "☀️", "Acne": "🔴", "Anti-Aging": "⏳",
    "Cleanser": "🧴", "Moisturizer": "💧", "Makeup": "💄", "Lip": "💋",
    "Perfume": "🌸", "Hair Care": "💇‍♀️",
    "Biore": "🧼", "Cetaphil": "🧴", "SK-II": "💎",
    "Laneige": "💙", "Lancôme": "🌹", "Senka": "🧪",
    "Yanhee": "🏥", "None": "🛡️",
}

footer_links_html = ""
for name, path in hub_links:
    icon = hub_icons.get(name, "📋")
    footer_links_html += f'                <a href="{path}" class="footer-link">{icon} {name}</a>\n'

# --- BUILD THE FULL HTML ---
html = '''<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="description" content="SkincareThai รวมรีวิวสกินแคร์ เครื่องสำอาง และไอเท็มบิวตี้จากหลายแหล่ง พร้อมสรุปภาษาไทยที่อ่านง่าย ใช้ตัดสินใจได้จริง และเหมาะกับคนไทย">
    <link rel="canonical" href="https://skincarethai.com/">
    <meta property="og:site_name" content="SkincareThai">
    <meta property="og:title" content="SkincareThai | รีวิวสกินแคร์ เครื่องสำอาง และบิวตี้ภาษาไทย">
    <meta property="og:description" content="SkincareThai รวมรีวิวสกินแคร์ เครื่องสำอาง และไอเท็มบิวตี้จากหลายแหล่ง พร้อมสรุปภาษาไทยที่อ่านง่าย ใช้ตัดสินใจได้จริง และเหมาะกับคนไทย">
    <meta property="og:url" content="https://skincarethai.com/">
    <meta property="og:type" content="website">
    <meta property="og:image" content="https://skincarethai.com/assets/images/social/home.svg">
    <meta property="og:image:alt" content="SkincareThai | รีวิวสกินแคร์ เครื่องสำอาง และบิวตี้ภาษาไทย">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="SkincareThai | รีวิวสกินแคร์ เครื่องสำอาง และบิวตี้ภาษาไทย">
    <meta name="twitter:description" content="SkincareThai รวมรีวิวสกินแคร์ เครื่องสำอาง และไอเท็มบิวตี้จากหลายแหล่ง พร้อมสรุปภาษาไทยที่อ่านง่าย ใช้ตัดสินใจได้จริง และเหมาะกับคนไทย">
    <meta name="twitter:image" content="https://skincarethai.com/assets/images/social/home.svg">
    <meta name="twitter:image:alt" content="SkincareThai | รีวิวสกินแคร์ เครื่องสำอาง และบิวตี้ภาษาไทย">
    <meta name="theme-color" content="#f5efe9">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SkincareThai | รีวิวสกินแคร์ เครื่องสำอาง และบิวตี้ภาษาไทย</title>
<style>
/* ===== RESET & BASE ===== */
*, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Sarabun', 'IBM Plex Sans Thai', -apple-system, BlinkMacSystemFont, 'Helvetica Neue', sans-serif; line-height: 1.7; color: #2d2d2d; background: #faf8f5; -webkit-font-smoothing: antialiased; }

/* ===== NAV ===== */
.nav { position: sticky; top: 0; background: rgba(250, 248, 245, 0.92); backdrop-filter: blur(12px); border-bottom: 1px solid rgba(0,0,0,0.06); padding: 14px 0; z-index: 1000; }
.nav-content { max-width: 1100px; margin: 0 auto; padding: 0 24px; display: flex; justify-content: space-between; align-items: center; }
.logo { font-size: 22px; font-weight: 700; color: #b07d6e; text-decoration: none; letter-spacing: -0.3px; }
.logo:hover { color: #8c5f52; }
.nav-links { display: flex; gap: 24px; }
.nav-links a { font-size: 14px; color: #6e6e73; text-decoration: none; transition: color 0.2s; font-weight: 500; }
.nav-links a:hover { color: #b07d6e; }

/* ===== HERO ===== */
.hero { min-height: 60vh; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 100px 24px 80px; background: linear-gradient(135deg, #faf8f5 0%, #f5ede8 50%, #efe4dc 100%); text-align: center; position: relative; overflow: hidden; }
.hero::before { content: ''; position: absolute; inset: 0; background: radial-gradient(ellipse at 80% 20%, rgba(176,125,110,0.08) 0%, transparent 60%), radial-gradient(ellipse at 20% 80%, rgba(176,125,110,0.06) 0%, transparent 60%); pointer-events: none; }
.hero-content { position: relative; z-index: 1; max-width: 800px; }
.hero-badge { display: inline-block; background: rgba(176,125,110,0.12); color: #b07d6e; font-size: 13px; font-weight: 600; padding: 6px 16px; border-radius: 100px; margin-bottom: 24px; letter-spacing: 0.5px; }
.hero-title { font-size: clamp(36px, 6vw, 56px); font-weight: 700; line-height: 1.2; margin-bottom: 20px; color: #2d2d2d; letter-spacing: -1px; }
.hero-subtitle { font-size: clamp(17px, 2.5vw, 22px); color: #6e6e73; max-width: 640px; margin: 0 auto 32px; line-height: 1.6; }
.hero-stats { display: flex; gap: 40px; justify-content: center; flex-wrap: wrap; }
.stat-item { text-align: center; }
.stat-number { font-size: 28px; font-weight: 700; color: #b07d6e; }
.stat-label { font-size: 13px; color: #8e8e93; margin-top: 2px; }

/* ===== CATEGORY SECTIONS ===== */
.category-section { max-width: 1100px; margin: 0 auto; padding: 48px 24px; }
.section-header { display: flex; align-items: center; gap: 12px; margin-bottom: 28px; padding-bottom: 16px; border-bottom: 2px solid #e8ddd6; }
.section-emoji { font-size: 28px; line-height: 1; }
.section-title { font-size: 24px; font-weight: 700; color: #2d2d2d; }
.section-count { font-size: 13px; color: #8e8e93; background: #f0ebe6; padding: 3px 12px; border-radius: 100px; margin-left: auto; }

/* ===== TOPIC CARDS ===== */
.topic-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px; }
.topic-card { display: block; background: #fff; border-radius: 14px; border: 1px solid #ece5de; padding: 20px 24px; text-decoration: none; transition: all 0.25s ease; }
.topic-card:hover { transform: translateY(-3px); box-shadow: 0 8px 24px rgba(176,125,110,0.10); border-color: #d6c5bb; }
.topic-card-title { font-size: 16px; font-weight: 600; color: #2d2d2d; margin-bottom: 6px; line-height: 1.4; }
.topic-card-title:hover { color: #b07d6e; }
.topic-card-snippet { font-size: 14px; color: #8e8e93; line-height: 1.5; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }

/* ===== CALL TO ACTION ===== */
.cta-section { max-width: 1100px; margin: 0 auto; padding: 48px 24px 64px; text-align: center; }
.cta-card { background: linear-gradient(135deg, #f5ede8, #efe4dc); border-radius: 20px; padding: 48px 32px; }
.cta-title { font-size: 24px; font-weight: 700; color: #2d2d2d; margin-bottom: 12px; }
.cta-desc { font-size: 16px; color: #6e6e73; margin-bottom: 24px; max-width: 500px; margin-left: auto; margin-right: auto; }
.cta-links { display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; }
.cta-link { display: inline-block; padding: 10px 24px; background: #b07d6e; color: #fff; border-radius: 100px; font-size: 15px; font-weight: 600; text-decoration: none; transition: all 0.2s; }
.cta-link:hover { background: #8c5f52; transform: translateY(-2px); }
.cta-link-outline { display: inline-block; padding: 10px 24px; background: transparent; color: #b07d6e; border: 2px solid #b07d6e; border-radius: 100px; font-size: 15px; font-weight: 600; text-decoration: none; transition: all 0.2s; }
.cta-link-outline:hover { background: rgba(176,125,110,0.08); transform: translateY(-2px); }

/* ===== FOOTER ===== */
.footer { background: #2d2d2d; padding: 56px 24px 32px; margin-top: 0; }
.footer-content { max-width: 1100px; margin: 0 auto; display: grid; grid-template-columns: 2fr 1fr; gap: 40px; }
.footer-logo { font-size: 20px; font-weight: 700; color: #f0ebe6; text-decoration: none; margin-bottom: 12px; display: inline-block; }
.footer-desc { color: #a8a8a8; font-size: 14px; line-height: 1.7; max-width: 360px; }
.footer-heading { font-size: 12px; font-weight: 700; text-transform: uppercase; color: #8e8e93; letter-spacing: 1.5px; margin-bottom: 16px; }
.footer-links { display: grid; grid-template-columns: 1fr 1fr; gap: 6px 20px; }
.footer-link { color: #c8c8c8; font-size: 13px; text-decoration: none; transition: color 0.2s; padding: 3px 0; }
.footer-link:hover { color: #f0ebe6; }
.footer-bottom { max-width: 1100px; margin: 40px auto 0; padding-top: 20px; border-top: 1px solid rgba(255,255,255,0.08); text-align: center; color: #6e6e73; font-size: 12px; }

/* ===== RESPONSIVE ===== */
@media (max-width: 768px) {
    .nav-links { display: none; }
    .footer-content { grid-template-columns: 1fr; gap: 32px; }
    .footer-links { grid-template-columns: 1fr 1fr; }
    .hero-stats { gap: 24px; }
    .topic-grid { grid-template-columns: 1fr; }
}

@media (max-width: 480px) {
    .hero { padding: 80px 20px 60px; }
    .category-section { padding: 32px 16px; }
    .cta-card { padding: 32px 20px; }
}
</style>
    <script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "WebSite",
  "name": "SkincareThai",
  "url": "https://skincarethai.com/",
  "description": "SkincareThai รวมรีวิวสกินแคร์ เครื่องสำอาง และไอเท็มบิวตี้จากหลายแหล่ง พร้อมสรุปภาษาไทยที่อ่านง่าย ใช้ตัดสินใจได้จริง และเหมาะกับคนไทย",
  "inLanguage": "th-TH",
  "image": "https://skincarethai.com/assets/images/social/home.svg",
  "publisher": {
    "@type": "Organization",
    "name": "SkincareThai",
    "url": "https://skincarethai.com"
  }
}
    </script>
</head>
<body>
    <nav class="nav">
        <div class="nav-content">
            <a href="/" class="logo">SkincareThai</a>
            <div class="nav-links">
                <a href="/">หน้าแรก</a>
                <a href="/whitening.html">Whitening</a>
                <a href="/sunscreen.html">Sunscreen</a>
                <a href="/acne.html">Acne</a>
                <a href="/sitemap.xml">ทั้งหมด</a>
            </div>
        </div>
    </nav>

    <section class="hero">
        <div class="hero-content">
            <div class="hero-badge">✦ รีวิวสกินแคร์สำหรับคนไทย</div>
            <h1 class="hero-title">รีวิวสกินแคร์และบิวตี้<br>ที่อ่านง่ายและใช้ตัดสินใจได้จริง</h1>
            <p class="hero-subtitle">รวมรีวิว เครื่องสำอาง สกินแคร์ และไอเท็มบิวตี้จากหลายแหล่ง พร้อมสรุปแบบไทยร่วมสมัยสำหรับคนที่อยากเลือกของให้ตรงผิวและงบ</p>
            <div class="hero-stats">
                <div class="stat-item">
                    <div class="stat-number">18</div>
                    <div class="stat-label">บทความรีวิว</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">4</div>
                    <div class="stat-label">หมวดหมู่</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">40+</div>
                    <div class="stat-label">แบรนด์ที่รีวิว</div>
                </div>
            </div>
        </div>
    </section>

''' + category_html + '''
    <section class="cta-section">
        <div class="cta-card">
            <h2 class="cta-title">🔍 กำลังมองหารีวิวแบรนด์ไหนอยู่?</h2>
            <p class="cta-desc">ดูรีวิวสินค้าตามแบรนด์ที่คุณสนใจ พร้อมข้อมูลส่วนผสมและความคิดเห็นจากผู้ใช้จริง</p>
            <div class="cta-links">
                <a href="/whitening.html" class="cta-link">Whitening ✨</a>
                <a href="/sunscreen.html" class="cta-link">Sunscreen ☀️</a>
                <a href="/acne.html" class="cta-link">Acne 🔴</a>
                <a href="/anti-aging.html" class="cta-link-outline">Anti-Aging ⏳</a>
            </div>
        </div>
    </section>

    <footer class="footer">
        <div class="footer-content">
            <div class="footer-column">
                <a href="/" class="footer-logo">SkincareThai</a>
                <p class="footer-desc">แหล่งรวมรีวิวสกินแคร์ เครื่องสำอาง และไอเท็มบิวตี้จากข้อมูลจริง พร้อมสรุปภาษาไทยที่อ่านง่ายและช่วยให้เลือกซื้อได้ตรงกับผิวมากขึ้น</p>
            </div>
            <div class="footer-column">
                <h4 class="footer-heading">หมวดหมู่สินค้า</h4>
                <div class="footer-links">
''' + footer_links_html + '''                </div>
            </div>
        </div>
        <div class="footer-bottom">
            <p>© 2026 SkincareThai — Professional Skincare Curation</p>
        </div>
    </footer>
</body>
</html>'''

# Write it
index_path = os.path.join(REPO, "index.html")
with open(index_path, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"Written: {index_path} ({len(html)} bytes, {len(topic_data)} topics)")
print(f"\nCategories:")
for cat_name in ["ผิวหน้า", "กันแดด", "ผิวกาย", "ผม"]:
    items = categories[cat_name]
    print(f"  {cat_name}: {len(items)} topics")
