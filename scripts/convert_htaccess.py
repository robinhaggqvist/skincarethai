#!/usr/bin/env python3
"""Convert Apache Redirect directives to LiteSpeed-compatible RewriteRule format."""
import os, re
from datetime import datetime

REPO = "/home/robin/.openclaw/workspace/skincarethai-repo"

# Read the current .htaccess
ht_path = os.path.join(REPO, ".htaccess")
with open(ht_path, 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.strip().split("\n")

# Keep header comments, replace Redirect rules with RewriteRules
new_lines = [
    "# LiteSpeed-compatible 301 redirects from old numbered topic pages to clean URLs",
    f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    "#",
    "# REQUIRED: RewriteEngine must be On in LiteSpeed context for these to work",
    "RewriteEngine On",
    "",
    "# Redirect old numbered topic pages to clean URLs",
]

count = 0
for line in lines:
    if line.startswith("Redirect 301 "):
        parts = line.split()
        # Format: Redirect 301 /topics/old-path/ https://skincarethai.com/topics/new-path/
        old_path = parts[2]
        new_url = parts[3]
        # LiteSpeed RewriteRule: RewriteRule ^old-path$ new-url [R=301,L]
        old_regex = "^" + re.escape(old_path.lstrip("/")) + "$"
        new_line = f'RewriteRule {old_regex} {new_url} [R=301,L]'
        new_lines.append(new_line)
        count += 1

new_lines.append(f"\n# {count} redirect rules generated")

htaccess_content = "\n".join(new_lines) + "\n"

with open(ht_path, 'w', encoding='utf-8') as f:
    f.write(htaccess_content)

print(f"Written: {ht_path} ({count} RewriteRule redirects)")
