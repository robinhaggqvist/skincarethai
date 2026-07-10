#!/usr/bin/env python3
"""Generate LiteSpeed-compatible 301 redirects for old numbered boilerplate topic URLs.
Only redirect URLs that had NO corresponding real directory on disk."""
import os, re
from datetime import datetime

REPO = "/home/robin/.openclaw/workspace/skincarethai-repo"

# Get all actual topic directories
real_dirs = set()
for d in os.listdir(os.path.join(REPO, "topics")):
    if os.path.isdir(os.path.join(REPO, "topics", d)):
        real_dirs.add(d)

# Get old numbered URLs from git history (before the homepage fix)
index_before = os.popen("cd /home/robin/.openclaw/workspace/skincarethai-repo && git show main~1:index.html 2>/dev/null").read()
old_urls = set(re.findall(r'href="https://skincarethai\.com/topics/([^"]+-\d+)/"', index_before))

print(f"Old URLs from git history: {len(old_urls)}")
print(f"Real directories: {len(real_dirs)}")

# Only create redirects for URLs whose path does NOT exist as a real directory
valid_redirects = {}
unmatched = []

for old in sorted(old_urls):
    # If the old URL path actually exists on disk, skip it
    if old in real_dirs:
        continue
    
    # Strip the trailing "-NUMBER"
    match = re.match(r'^(.+?)-(\d+)$', old)
    if not match:
        unmatched.append(old)
        continue
    base = match.group(1)
    
    # Find the best matching real directory
    # Priority: exact match, then common prefix match
    candidates = []
    for real in real_dirs:
        if real == base:
            candidates.append((0, real))
        elif real.startswith(base):
            candidates.append((1, real))
        elif base.startswith(real):
            candidates.append((2, real))
        else:
            # Try fuzzy: strip the common Thai suffix
            clean_base = re.sub(r'-ในมุมที่คนไทยกำลังสนใจ$', '', base)
            clean_real = re.sub(r'-ในมุมที่คนไทยกำลังสนใจ$', '', real)
            if clean_base == clean_real:
                candidates.append((3, real))
    
    if candidates:
        candidates.sort()
        valid_redirects[old] = candidates[0][1]
    else:
        unmatched.append(old)

print(f"Valid redirects: {len(valid_redirects)}")
print(f"Unmatched (skipped): {len(unmatched)}")
for u in unmatched:
    print(f"  SKIP: {u}")

# Generate .htaccess content
htaccess_lines = [
    "# LiteSpeed-compatible 301 redirects from old numbered topic pages to clean URLs",
    f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    "#",
    "# REQUIRED: RewriteEngine must be On in LiteSpeed context for these to work",
    "RewriteEngine On",
    "",
    "# Redirect old numbered topic pages to clean URLs",
]

count = 0
for old_path, new_path in sorted(valid_redirects.items()):
    old_regex = "^" + re.escape("topics/" + old_path + "/") + "$"
    new_url = f"https://skincarethai.com/topics/{new_path}/"
    htaccess_lines.append(f"RewriteRule {old_regex} {new_url} [R=301,L]")
    count += 1

htaccess_lines.append(f"")
htaccess_lines.append(f"# {count} redirect rules generated")

ht_path = os.path.join(REPO, ".htaccess")
with open(ht_path, 'w', encoding='utf-8') as f:
    f.write("\n".join(htaccess_lines) + "\n")

print(f"\nWritten: {ht_path} ({count} RewriteRule redirects)")
