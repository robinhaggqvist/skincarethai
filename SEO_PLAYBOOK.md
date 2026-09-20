# SkincareThai SEO Playbook

## Operating model

The site uses an evidence-led loop:

`Search Console query → intent cluster → new/update/hold decision → source-backed draft → quality gate → deploy → live verification → Search Console review`

The publisher must report new pages, updates, already-live pages, and holds separately. An already-live page is never reported as a failed publication.

## Intent clusters

- **How-to:** ใช้ตอนไหน, วิธีใช้, เริ่มอย่างไร
- **Problem:** สิว, รูขุมขนกว้าง, รอยสิว, ผิวแพ้ง่าย
- **Audience/skin type:** ผิวมัน, ผิวแห้ง, เด็ก, sensitive skin
- **Budget/value:** ราคา, งบไม่เกิน, คุ้มไหม
- **Product review:** product name plus รีวิว, ส่วนผสม, เหมาะกับใคร
- **Treatment:** Thermage or other procedures; hold unless this editorial category is deliberately maintained.

## Title formulas

- `[Ingredient] ใช้ตอนไหน? ใช้เช้าหรือเย็น และควรใช้คู่กับอะไร`
- `[Concern] แก้ยังไง? วิธีดูแลตามสภาพผิวและสิ่งที่ควรเลี่ยง`
- `กันแดดสำหรับ[ผิว/ปัญหา]: วิธีเลือก เนื้อสัมผัส และการทาซ้ำ`
- `[Product] รีวิว: เหมาะกับใคร ส่วนผสม จุดเด่น และข้อควรระวัง`
- `[Category] งบไม่เกิน [amount]: เทียบความคุ้มต่อการใช้จริง`

## Publishing thresholds

- New article: quality score ≥80, three or more credible sources, distinct intent, and no live page for the same intent.
- Existing-page update: new evidence or a clear CTR/position opportunity; record the update separately.
- Hold: duplicate intent, weak evidence, off-topic query, or boilerplate content.

## Search Console review

- Use the lagged latest snapshot, not today's incomplete data.
- Prioritise impressions before clicks.
- For position 1–20 with weak CTR, improve title and description first.
- For position 20–80 with meaningful impressions, improve intent match and depth.
- For broad terms with no clicks, create a specific supporting angle instead of another generic page.
- Recheck a new page after enough data has accumulated; do not overwrite it based on one impression.

## Reports and commands

```bash
python3 scripts/seo_keyword_plan.py
python3 scripts/report_content_pipeline.py --quality-threshold 80
python3 scripts/daily_affiliate_growth.py --quality-threshold 80
```

Outputs:

- `reports/seo_keyword_plan.md` — current query opportunities and recommended lanes.
- `reports/content_pipeline_backlog.md` — new, update, already-live, and hold candidates.
- `reports/daily_page_growth.md` — the actual publishing run and live verification state.

## Guardrails

- Never manufacture search volume, product performance, reviews, or medical claims.
- Never publish a page solely because a keyword is different by one word.
- Keep broad or treatment-related queries in a separate review lane when they do not fit the site's core purpose.
