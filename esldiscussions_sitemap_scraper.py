#!/usr/bin/env python3
"""
esldiscussions_sitemap_scraper.py
─────────────────────────────────
Sitemap scraper for esldiscussions.com.

This site has NO sitemap.xml (returns 403) and NO publish dates on lesson pages.
Strategy: scrape all lesson URLs from the homepage, use today's date for each.

Output: urls.txt — one URL per line with date (URL YYYY-MM-DD), sorted alphabetically.

Update mode: reads existing urls.txt, skips already-listed URLs, appends new ones.
"""

import os
import re
import sys
from datetime import date
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://esldiscussions.com"
OUTPUT_FILE = "urls.txt"

# Static/utility pages to skip
SKIP_PATHS = {
    "/",
    "/copyright.html",
    "/privacy.html",
    "/links.html",
    "/faqs.html",
    "/book.html",
    "/help.html",
}


def get_lesson_links() -> set[str]:
    """Scrape homepage and return all lesson URLs."""
    resp = requests.get(BASE_URL, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")

    links = set()
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]

        # Must start with esldiscussions.com
        if href.startswith("https://esldiscussions.com"):
            path = href.replace("https://esldiscussions.com", "")
        elif href.startswith("http://esldiscussions.com"):
            path = href.replace("http://esldiscussions.com", "")
        elif href.startswith("/"):
            path = href
        else:
            continue

        # Skip utility pages
        if path in SKIP_PATHS:
            continue
        # Must be .html
        if not path.endswith(".html"):
            continue

        full_url = f"https://esldiscussions.com{path}"
        links.add(full_url)

    return links


def load_existing_urls(path: str) -> set[str]:
    """Load URLs already in urls.txt."""
    if not os.path.exists(path):
        return set()
    existing = set()
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                url = line.split()[0]
                existing.add(url)
    return existing


def main():
    today = date.today().isoformat()

    print(f"[esldiscussions sitemap scraper]")
    print(f"  scraping {BASE_URL} ...")

    all_links = get_lesson_links()
    print(f"  found {len(all_links)} URLs on homepage")

    existing = load_existing_urls(OUTPUT_FILE)
    new_links = all_links - existing
    old_links = all_links & existing

    print(f"  {len(old_links)} already in {OUTPUT_FILE}")
    print(f"  {len(new_links)} new URLs to append")

    if not new_links:
        print("  nothing new — exiting")
        return

    # Append new links at the end
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        for url in sorted(new_links):
            f.write(f"{url} {today}\n")

    print(f"  appended {len(new_links)} URLs to {OUTPUT_FILE}")

    # Summary
    with open(OUTPUT_FILE) as f:
        total = sum(1 for _ in f)
    print(f"  total lines in {OUTPUT_FILE}: {total}")


if __name__ == "__main__":
    main()