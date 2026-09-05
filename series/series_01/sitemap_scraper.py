#!/usr/bin/env python3
"""
sitemap_scraper.py
──────────────────
Link scraper for esldiscussions.com (source_code=000022, series 01).

Discovery strategy (per RF guidelines: sitemap first, then fallback), verified
against the live site:

  1. Fetch the GZIPPED sitemap at /sitemap.xml.gz (the plain /sitemap.xml is
     403 on this host). Extract every lesson <loc>.
  2. Also scan the homepage for lesson links, because the sitemap is stale
     (all <lastmod> = 2016-02-16) and misses ~24 lessons added after 2016.
  3. UNION both sources, filter to real lesson pages, drop utility pages.

The sitemap's <lastmod> is the file's generation date (identical for every
entry), so it is NOT used. Since lesson pages carry no publish date either,
every URL is written with today's date.

Output: data/01/urls.txt — one "<url> <YYYY-MM-DD>" per line, sorted, oldest
line first (here the order is alphabetical since no real dates exist).

Update mode (default): reads existing urls.txt, skips already-listed URLs,
appends only new ones to the END of the file so resource_code sequence is
never disturbed.

Invoke through the terminal tool:
    python3 series/series_01/sitemap_scraper.py
"""

import gzip
import os
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import URL_OVERRIDES
from sitemap_rules import (
    BASE_URL,
    SITEMAP_GZ_URL,
    normalise_url,
    is_lesson_url,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_FILE = str(REPO_ROOT / "data" / "01" / "urls.txt")

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)
HEADERS = {"User-Agent": USER_AGENT}


def from_sitemap() -> set[str]:
    """Return lesson URLs from the gzipped sitemap (empty set on failure)."""
    try:
        resp = requests.get(SITEMAP_GZ_URL, headers=HEADERS, timeout=30)
        if resp.status_code != 200:
            print(f"  sitemap.xml.gz → HTTP {resp.status_code}, skipping")
            return set()
        xml = gzip.decompress(resp.content).decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  sitemap.xml.gz → error: {e}, skipping")
        return set()

    soup = BeautifulSoup(xml, "xml")
    urls = set()
    for loc in soup.find_all("loc"):
        u = normalise_url(loc.get_text())
        u = URL_OVERRIDES.get(u, u)
        if is_lesson_url(u):
            urls.add(u)
    print(f"  sitemap.xml.gz → {len(urls)} lesson URLs")
    return urls


def from_homepage() -> set[str]:
    """Return lesson URLs discovered on the homepage."""
    resp = requests.get(BASE_URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")

    urls = set()
    for a in soup.find_all("a", href=True):
        u = urljoin(BASE_URL + "/", a["href"])
        u = normalise_url(u)
        u = URL_OVERRIDES.get(u, u)
        if is_lesson_url(u):
            urls.add(u)
    print(f"  homepage       → {len(urls)} lesson URLs")
    return urls


def load_existing(path: str) -> list[str]:
    """Return existing URLs in file order (to preserve sequence)."""
    if not os.path.exists(path):
        return []
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(line.split()[0])
    return out


def main():
    today = date.today().isoformat()
    print("[esldiscussions sitemap scraper]")

    # 1 + 2: union of sitemap and homepage
    discovered = from_sitemap() | from_homepage()
    print(f"  union          → {len(discovered)} unique lesson URLs")

    existing = load_existing(OUTPUT_FILE)
    existing_set = set(existing)
    new_urls = sorted(discovered - existing_set)

    print(f"  already listed : {len(existing)}")
    print(f"  new to append  : {len(new_urls)}")

    if not new_urls:
        print("  nothing new — exiting")
        return

    Path(OUTPUT_FILE).parent.mkdir(parents=True, exist_ok=True)
    # Append new URLs to the END so existing resource_code sequence is preserved.
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        for u in new_urls:
            f.write(f"{u} {today}\n")

    total = len(existing) + len(new_urls)
    print(f"  appended {len(new_urls)} URLs; total now {total}")


if __name__ == "__main__":
    main()
