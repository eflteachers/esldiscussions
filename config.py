"""
config.py
─────────
Site-specific configuration for esldiscussions.com scraper.

Centralises all site-specific constants, URL overrides, and settings.
"""

# ── URL overrides ──────────────────────────────────────────────────────────
# Some lesson pages may link to PDF instead of HTML.
# Map the incorrect URL → the correct HTML URL here.
URL_OVERRIDES = {
    "https://esldiscussions.com/r/russia.pdf": "https://esldiscussions.com/r/russia.html",
}