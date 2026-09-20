# SkincareThai Keyword SOP

## Purpose

Choose topics from real Search Console demand while avoiding thin duplicate pages. The goal is useful, source-backed content that earns impressions first and clicks over time.

## Weekly workflow

1. Run the publisher or `python3 scripts/seo_keyword_plan.py`.
2. Review `reports/seo_keyword_plan.md`.
3. Sort each query into one lane:
   - **New article:** distinct intent, useful angle, no matching live page.
   - **Update:** same intent as an existing page, but new evidence or weak CTR.
   - **Support/internal link:** broad or low-volume term that should support a stronger page.
   - **Hold:** duplicate, thin variation, off-topic, or insufficient evidence.
4. Require at least three credible source signals before publishing a new article.
5. Give every article one primary query and three to six closely related terms.
6. Write a title that answers the query directly; do not repeat the same title pattern.
7. Include original practical analysis, clear sourcing, cautions, and a useful next step.
8. Run the quality gate, publish, verify HTTP 200, verify the canonical URL, and confirm sitemap inclusion.
9. Recheck Search Console after the data lag; do not judge a new page on the same day.

## Keyword decision rules

### Create a new article when

- The query has a different problem, audience, budget, skin type, use case, or product-review intent.
- The proposed page would have a different title, outline, conclusion, and product set.
- It adds substantial information rather than replacing product names in a template.

### Update an existing article when

- The query asks the same question as an existing page.
- New source evidence improves the answer.
- The page receives impressions but has weak CTR or a position above 10.

### Hold when

- It is only a spelling, plural, numbered, or product-swap variation.
- It has weak or unrelated source support.
- It is outside the site's skincare scope unless a treatment category is intentionally approved.

## Minimum quality checklist

- [ ] Primary query is explicit.
- [ ] Search intent is documented.
- [ ] At least three credible sources support the angle.
- [ ] The page is materially different from existing pages.
- [ ] Title and meta description promise a specific answer.
- [ ] No unsupported medical, safety, efficacy, or ranking claims.
- [ ] Internal links point to relevant existing pages.
- [ ] Canonical, sitemap, and HTTP 200 verified.
- [ ] Status recorded as `discovered`, `researched`, `drafted`, `quality_passed`, `deployed`, or `live`.

## Current priority clusters

1. Niacinamide usage and routines
2. Enlarged pores and oily skin
3. Acne sunscreen
4. Sensitive-skin skincare
5. Vitamin C and acne marks
6. Evidence-based product reviews and comparisons

Broad terms such as `สกินแคร์`, `เวชสำอาง`, and `เครื่องสำอาง` are supporting themes, not primary article targets until they have a specific angle.
