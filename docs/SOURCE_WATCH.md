# Source Watch

Use this system to track Thai beauty bloggers, magazines, clinics, and community sources.

## What To Save

- source name
- source URL
- RSS URL when available
- topic coverage
- last checked date
- whether anything new was published
- raw page text for style analysis

## Database

The SQLite database lives at:

- `data/source_watch.db`

It stores:

- `sources`
- `source_posts`
- `source_terms`
- `source_checks`

## How To Use

1. Initialize the DB:

```bash
python scripts/init_source_watch_db.py
```

2. Add a fetched post and its extracted text:

```bash
python scripts/store_source_page.py \
  --source-url https://example.com \
  --post-url https://example.com/post \
  --title "Sample post" \
  --text-file /tmp/extracted.txt
```

3. Run the feed/link watcher:

```bash
python scripts/fetch_source_updates.py --limit 10
```

You can also target one source at a time:

```bash
python scripts/fetch_source_updates.py --source https://example.com --limit 20
```

## Citation Rule

- Prefer RSS feeds first.
- If a source has no RSS, track the main site URL or category URL.
- When writing about a source, link back to the page and quote only a short detail.
- If the page supports a text fragment, `#:~:text=` can jump to the exact text.

## Style Mining Rule

- Store raw or extracted text only for internal analysis and writing style study.
- Use the text as reference material for tone, structure, and vocabulary.
- Do not copy long passages into SkincareThai pages.

## Topic Learning

- Each new post can add a topic term to the database.
- Over time, the DB becomes a map of what each blogger covers well.
- That lets us spot genuinely new topics instead of guessing from the site description.
