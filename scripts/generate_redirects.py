#!/usr/bin/env python3
"""Generate htaccess 301 redirects from old numbered topic URLs to clean ones."""
import os, re

REPO = "/home/robin/.openclaw/workspace/skincarethai-repo"

# Get all actual topic directories
topic_data = {}
for d in os.listdir(os.path.join(REPO, "topics")):
    topic_dir = os.path.join(REPO, "topics", d)
    if not os.path.isdir(topic_dir):
        continue
    topic_data[d] = {"dir": d}

# Get old numbered URLs from git history (before fix)
index_before = os.popen("cd /home/robin/.openclaw/workspace/skincarethai-repo && git show main~1:index.html 2>/dev/null").read()

# Extract all old numbered URLs and map them
old_urls = set(re.findall(r'href="https://skincarethai\.com/topics/([^"]+-\d+)/"', index_before))

print(f"Found {len(old_urls)} old numbered URLs")

# Build mapping: base name -> clean real slug
# E.g. "serum-pantip-ในมุมที่คนไทยกำลังสนใจ-18" -> "serum-pantip-ในมุมที่คนไทยกำลังสนใจ"
redirects = []  # (old_url, new_url)
matched = 0
unmatched = []

for old in sorted(old_urls):
    # Strip the trailing "-NUMBER"
    match = re.match(r'^(.+?)-(\d+)$', old)
    if not match:
        unmatched.append(old)
        continue
    base = match.group(1)
    num = match.group(2)
    
    # Check if this base matches a real topic dir
    found = None
    for real_dir in topic_data:
        # Try exact match
        if real_dir == base:
            found = real_dir
            break
        # Some have the base within them
        if real_dir.startswith(base) or base.startswith(real_dir):
            found = real_dir
            break
    
    if found:
        redirects.append((old, found))
        matched += 1
    else:
        # Try to find a real topic whose slug is the base stripped of language pattern
        # E.g. "whitening-cream-review-ในมุมที่คนไทยกำลังสนใจ" is the base
        for real_dir in topic_data:
            # Get the name part without "-ในมุมที่คนไทยกำลังสนใจ" or similar
            clean_base = re.sub(r'-ในมุมที่คนไทยกำลังสนใจ$', '', base)
            clean_real = re.sub(r'-ในมุมที่คนไทยกำลังสนใจ$', '', real_dir)
            if clean_base == clean_real:
                found = real_dir
                redirects.append((old, found))
                matched += 1
                break
        if not found:
            unmatched.append(old)

print(f"Matched: {matched}")
print(f"Unmatched: {len(unmatched)}")
for u in unmatched[:20]:
    print(f"  UNMATCHED: {u}")

# Now build unique redirects
unique_redirects = {}
for old, new in redirects:
    unique_redirects[old] = new

# Generate .htaccess content
htaccess_lines = []
htaccess_lines.append("# Auto-generated 301 redirects from old numbered topic pages to clean URLs")
htaccess_lines.append(f"# Generated: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
htaccess_lines.append(f"# {len(unique_redirects)} old URLs -> {len(set(unique_redirects.values()))} clean topic pages")
htaccess_lines.append("")

for old_path, new_path in sorted(unique_redirects.items()):
    htaccess_lines.append(f'Redirect 301 /topics/{old_path}/ https://skincarethai.com/topics/{new_path}/')

# Write to repo
htaccess_content = "\n".join(htaccess_lines) + "\n"
ht_path = os.path.join(REPO, ".htaccess")
with open(ht_path, 'w', encoding='utf-8') as f:
    f.write(htaccess_content)

print(f"\nWritten: {ht_path} ({len(unique_redirects)} redirect rules)")
print(f"\nRedirect distribution:")
from collections import Counter
target_counts = Counter(unique_redirects.values())
for target, count in target_counts.most_common():
    print(f"  /topics/{target}/ -> {count} old URLs")
