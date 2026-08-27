"""
sitemap_rules.py
────────────────
Site-specific rules for discovering lesson URLs on esldiscussions.com.

esldiscussions.com has NO sitemap.xml (returns 403) and lesson pages carry NO
publish date. Lessons are listed as links on the homepage. All lesson URLs
follow the pattern:  https://esldiscussions.com/{letter}/{topic}.html

These rules are consumed by sitemap_scraper.py.
"""

# Base site URL
BASE_URL = "https://esldiscussions.com"

# Only anchors whose href matches this pattern are treated as lessons.
# e.g. /a/abortion.html, /z/zambia.html
LESSON_URL_PATTERN = r"^https?://esldiscussions\.com/[a-z0-9]/[a-z0-9_\-]+\.html$"

# Utility / non-lesson pages to exclude explicitly.
EXCLUDE_PATHS = {
    "/copyright.html",
    "/privacy.html",
    "/links.html",
    "/index.html",
}

# This site provides no publish dates → sitemap_scraper falls back to today.
HAS_PUBLISH_DATES = False
