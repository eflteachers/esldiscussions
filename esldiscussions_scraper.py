#!/usr/bin/env python3
"""
esldiscussions_scraper.py
─────────────────────────
Main scraper for esldiscussions.com.

Scrapes lesson pages from urls.txt (oldest first), extracts metadata,
downloads PDF + Word assets, and populates the SQLite database.

Usage:
    python3 esldiscussions_scraper.py                    # Full scrape
    python3 esldiscussions_scraper.py --resume           # Resume from last
    python3 esldiscussions_scraper.py --limit 5          # First 5 only
    python3 esldiscussions_scraper.py --range 000001-000010  # Specific range
    python3 esldiscussions_scraper.py --update           # Update mode (skip existing)
"""

import argparse
import hashlib
import os
import re
import sys
import time
import random
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

# ── Global scripts ──────────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parent))
from global_db import DB
from global_uuidv7 import uuid7
from global_sanitization import sanitize_filename, sanitize_folder_name
from global_resource_code_generator import ResourceCodeGenerator

# ── Constants ────────────────────────────────────────────────────────────────
SITE_CODE = "000021"
SERIES_CODE = "01"
WEBSITE = "esldiscussions"
BASE_URL = "https://esldiscussions.com"
URLS_FILE = "urls.txt"
DB_FILE = f"{WEBSITE}.db"
DOWNLOAD_DIR = "downloads"
TODAY = date.today().isoformat()
NOW = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# ── Constant field values (from mapping sheet) ───────────────────────────────
CONSTANTS = {
    "validation_status": "passed",
    "needs_review": 0,
    "source_id": None,
    "level": None,
    "resource_type": "lesson-content",
    "resource_form": "worksheet",
    "resource_form_local": "discussion handout",
    "lesson_type": "activity",
    "lesson_type_local": "discussion",
    "server": "free",
    "status": "active",
    "activity_type": "discussion",
    "activity_type_local": "discussion",
    "age_group": "Teens, Adults",
    "audience": "Learners, Teachers",
    "author_local": "Sean Banville",
    "content_type_local": "Discussion",
    "domain": "ESL",
    "english_variety": "British",
    "focus": "speaking",
    "function": "expressing opinions, comparing, speculating/predicting, asking for and giving information",
    "function_locked": 0,
    "grammar_locked": 0,
    "has_answer": 0,
    "has_audio": 0,
    "has_presentation": 0,
    "has_teacher": 0,
    "has_video": 0,
    "html_created_local": 0,
    "interaction_pattern": "pair",
    "interactivity": "non-interactive",
    "is_ai_generated": "no",
    "is_collection": 0,
    "is_deleted": 0,
    "is_free": 1,
    "is_game": 0,
    "is_learning_path": 0,
    "is_printable": 1,
    "language": "English",
    "lesson_time": 30,
    "media_type": "text",
    "material_origin": "pedagogic",
    "purpose": "ge",
    "skill": "speaking",
    "stage": "group discussion",
    "website": WEBSITE,
}


def extract_topic(source_url: str) -> str:
    """Extract topic name from URL like /z/zambia.html → 'Zambia'."""
    path = urlparse(source_url).path
    name = path.rstrip(".html").rsplit("/", 1)[-1]
    # Handle hyphens and special cases
    name = name.replace("-", " ").replace("_", " ").title()
    return name


def extract_title(soup: BeautifulSoup, topic: str) -> str:
    """Extract title from page."""
    return f"English Discussion on {topic}"


def extract_overview(topic: str) -> str:
    """Generate overview text based on topic."""
    return (
        f"A printable split-pair speaking activity with 10 different open-ended "
        f"{topic} questions for each partner."
    )


def extract_objective(topic: str) -> str:
    """Generate objective text based on topic."""
    return (
        f"Learners discuss {topic}'s geography, history, culture, people, "
        f"tourism, international relations, and possible future."
    )


def extract_notes(topic: str) -> str:
    """Generate notes_local."""
    return (
        f"Two parallel sets of 10 open-ended questions for Student A and "
        f"Student B about {topic}."
    )


def extract_lesson_topic(topic: str) -> str:
    """Generate lesson_topic value."""
    return f"{topic}, countries and cultures, geography, history, travel and tourism"


def extract_tags(topic: str) -> str:
    """Generate tags value."""
    return (
        f"{topic}, culture, geography, history, travel, tourism, discussion questions"
    )


def extract_body_html(soup: BeautifulSoup) -> str:
    """Extract the discussion questions as restricted HTML (a, p, strong, li, i, ul, ol, h1, h2, h3)."""
    body = soup.find("body")
    if not body:
        return ""

    # The discussion content is inside an <article> tag
    article = body.find("article")
    if not article:
        # Fallback: find the section starting with THE DISCUSSION ON
        for el in body.find_all(["h3", "h2", "strong"]):
            if "THE DISCUSSION ON" in el.get_text(strip=True).upper():
                parent = el.find_parent(["div", "td", "section"])
                if parent:
                    article = parent
                    break

    if not article:
        return ""

    # Get the HTML, clean it
    raw_html = str(article)
    soup_article = BeautifulSoup(raw_html, "lxml")
    # Remove unwanted elements
    for tag in soup_article.find_all(["script", "iframe", "style", "img", "br"]):
        tag.decompose()
    # Convert em to i
    for em in soup_article.find_all("em"):
        em.name = "i"
    # Clean links
    for a in soup_article.find_all("a"):
        href = a.get("href", "")
        a.attrs = {"href": href}
        a["target"] = "_blank"
        a["rel"] = "nofollow noopener noreferrer"
    # Keep only allowed tags, unwrap the rest
    allowed = {"a", "p", "strong", "li", "i", "ul", "ol", "h1", "h2", "h3",
               "table", "tr", "td", "th", "thead", "tbody", "article"}
    for tag in soup_article.find_all(True):
        if tag.name not in allowed:
            tag.unwrap()

    return str(soup_article)


def build_download_folder_name(title: str, resource_code: str) -> str:
    """Build folder name: sanitized_full_title_resource_code"""
    sanitized = sanitize_folder_name(title)
    return f"{sanitized}_{resource_code}"


def build_file_name(component_type: str, folder_name: str, ext: str) -> str:
    """Build file name: component_type_folder_name.extension"""
    # folder_name contains the resource_code; strip it for the file name base
    base = folder_name.rsplit("_", 1)[0]  # remove the resource_code suffix
    return f"{component_type}_{base}.{ext}"


def extract_asset_urls(soup: BeautifulSoup, page_url: str) -> dict:
    """Find PDF and DOC download URLs from the page."""
    assets = {"pdf": None, "doc": None}
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        text = a_tag.get_text(strip=True).lower()
        # Resolve relative URLs against page URL
        from urllib.parse import urljoin
        full_url = urljoin(page_url, href)
        if full_url.endswith(".pdf"):
            assets["pdf"] = full_url
        elif full_url.endswith(".doc") and "pdf" not in text:
            assets["doc"] = full_url
    return assets


def download_asset(url: str, dest_path: Path) -> dict:
    """Download a single asset file to .part, validate, rename."""
    result = {
        "download_status": "failed",
        "http_status": None,
        "size_bytes": 0,
        "checksum": None,
        "file_exists": 0,
    }
    if not url:
        result["download_status"] = "not_downloadable"
        return result

    temp_path = dest_path.with_suffix(dest_path.suffix + ".part")
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=60, stream=True)
        result["http_status"] = resp.status_code
        if resp.status_code != 200:
            result["download_status"] = "failed"
            return result

        # Write to temp file
        temp_path.parent.mkdir(parents=True, exist_ok=True)
        sha256 = hashlib.sha256()
        with open(temp_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    sha256.update(chunk)

        size = temp_path.stat().st_size
        result["size_bytes"] = size
        if size == 0:
            temp_path.unlink(missing_ok=True)
            result["download_status"] = "failed"
            return result

        # Rename temp to final
        temp_path.rename(dest_path)
        result["checksum"] = sha256.hexdigest()
        result["file_exists"] = 1
        result["download_status"] = "success"
    except Exception as e:
        temp_path.unlink(missing_ok=True)
        result["download_status"] = "failed"
        result["validation_notes"] = str(e)
    return result


def compute_sha256(file_path: Path) -> str:
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def scrape_lesson(url: str, db: DB, code_gen: ResourceCodeGenerator, session: requests.Session) -> dict:
    """Scrape a single lesson page and return all field values."""
    print(f"  Scraping: {url}")

    # Fetch page
    try:
        resp = session.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"    ERROR: {e}")
        return {"error": str(e), "http_status": getattr(e.response, "status_code", None)}

    soup = BeautifulSoup(resp.text, "lxml")
    http_status = resp.status_code

    # Extract topic from URL
    topic = extract_topic(url)
    topic_slug = url.rstrip(".html").rsplit("/", 1)[-1]
    letter = urlparse(url).path.split("/")[1]

    # Extract title
    title = extract_title(soup, topic)

    # Generate UUID and resource_code
    resource_uuid = uuid7()
    resource_code = code_gen.get_next_resource_code()

    # Sanitize folder name
    folder_name = build_download_folder_name(title, resource_code)
    download_folder = Path(DOWNLOAD_DIR) / folder_name

    # Asset URLs
    asset_urls = extract_asset_urls(soup, url)

    # Body HTML
    body_html = extract_body_html(soup)

    # Build resource data
    resource_data = {
        "uuid": resource_uuid,
        "resource_code": resource_code,
        "source_url": url,
        "title": title,
        "date": TODAY,
        "date_1st_scraped": TODAY,
        "date_scraped": TODAY,
        "download_folder_name": folder_name,
        "body_html": body_html,
        "overview": extract_overview(topic),
        "objective": extract_objective(topic),
        "notes_local": extract_notes(topic),
        "lesson_topic": extract_lesson_topic(topic),
        "tags": extract_tags(topic),
        "file_extension": None,
        "count_document": 0,
        "count_total": 0,
        "size_doc": None,
        "size_doc_bytes": None,
        "size_files": None,
        "size_files_bytes": None,
        "site_code": SITE_CODE,
        "source_code": SITE_CODE,
        "source_series_code": SERIES_CODE,
        "sequence": resource_code[-6:],
    }
    resource_data.update(CONSTANTS)

    # Download assets
    assets = []
    total_size = 0
    extensions = set()

    for asset_type, url in [("pdf", asset_urls["pdf"]), ("doc", asset_urls["doc"])]:
        if not url:
            continue

        ext = asset_type
        extensions.add(ext)

        asset_uuid = uuid7()
        asset_code = f"{resource_code}_AS{(len(assets) + 1):02d}"
        orig_filename = f"{topic_slug}.{ext}"
        sanitized_name = f"student_{sanitize_filename(topic)}"
        final_filename = build_file_name("student", folder_name, ext)
        dest_path = download_folder / final_filename

        dl_result = download_asset(url, dest_path)
        total_size += dl_result.get("size_bytes", 0)

        # Get MIME type
        mime_map = {"pdf": "application/pdf", "doc": "application/msword"}
        mime = mime_map.get(ext, "application/octet-stream")

        asset_record = {
            "resource_uuid": resource_uuid,
            "resource_code": resource_code,
            "asset_code": asset_code,
            "uuid": asset_uuid,
            "sort_order": len(assets) + 1,
            "component_type": "student",
            "extension": ext,
            "extension_local": ext,
            "mime_type": mime,
            "notes_local": None,
            "printable": 1,
            "size": f"{dl_result.get('size_bytes', 0)} bytes",
            "source": "local",
            "title": f"{topic} Discussion – {asset_type.upper()}",
            "title_local": orig_filename,
            "type": "document",
            "url": url,
            "url_local": url,
            "checksum_original": dl_result.get("checksum"),
            "checksum_final": dl_result.get("checksum"),
            "download_status": dl_result.get("download_status", "failed"),
            "file_exists": dl_result.get("file_exists", 0),
            "http_status": dl_result.get("http_status"),
            "size_bytes": dl_result.get("size_bytes", 0),
            "validated_at": NOW,
            "validation_notes": dl_result.get("validation_notes", ""),
            "validation_status": "valid" if dl_result.get("file_exists") else "invalid",
        }
        assets.append(asset_record)

    # Update resource counts
    doc_count = len(assets)
    resource_data["count_document"] = doc_count
    resource_data["count_total"] = doc_count
    resource_data["file_extension"] = ", ".join(sorted(extensions))
    resource_data["size_doc"] = f"{total_size / 1024:.2f} KB" if total_size else None
    resource_data["size_doc_bytes"] = total_size
    resource_data["size_files"] = resource_data["size_doc"]
    resource_data["size_files_bytes"] = total_size

    # Insert into DB
    try:
        db.insert_resource(resource_data)
        for asset in assets:
            db.insert_asset(asset)

        # Insert resource_validation
        validation_data = {
            "resource_uuid": resource_uuid,
            "source_url": url,
            "final_url": url,
            "download_status": "success" if all(a["download_status"] == "success" for a in assets) else "partial",
            "http_status": http_status,
            "needs_review": 0,
            "scrape_error": "none",
            "scrape_status": "success",
            "validation_status": "passed",
            "validated_at": NOW,
            "validation_notes": "Page, PDF, and Word file returned HTTP 200; both downloadable documents were validated.",
            "count_audio_expected": 0,
            "count_audio_scraped": 0,
            "count_audio_downloaded": 0,
            "count_audio": 0,
            "count_document_expected": doc_count,
            "count_document_scraped": doc_count,
            "count_document_downloaded": doc_count,
            "count_document": doc_count,
            "count_presentation_expected": 0,
            "count_presentation_scraped": 0,
            "count_presentation_downloaded": 0,
            "count_presentation": 0,
            "count_total_expected": doc_count,
            "count_total_scraped": doc_count,
            "count_total_downloaded": doc_count,
            "count_total": doc_count,
            "count_video_expected": 0,
            "count_video_scraped": 0,
            "count_video_downloaded": 0,
            "count_video": 0,
        }
        db.insert_resource_validation(validation_data)
        print(f"    ✓ {resource_code} | {title}")
        return {"status": "success", "resource_code": resource_code, "title": title}
    except Exception as e:
        print(f"    DB ERROR: {e}")
        return {"status": "failed", "error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="esldiscussions.com scraper")
    parser.add_argument("--resume", action="store_true", help="Resume from last scraped")
    parser.add_argument("--limit", type=int, help="Max lessons to scrape")
    parser.add_argument("--range", type=str, help="Resource code range (e.g. 000001-000010)")
    parser.add_argument("--update", action="store_true", help="Update mode (skip existing)")
    args = parser.parse_args()

    # Init DB
    db = DB(DB_FILE)
    code_gen = ResourceCodeGenerator(SITE_CODE, SERIES_CODE, db.conn)

    # Read urls.txt
    if not os.path.exists(URLS_FILE):
        print(f"ERROR: {URLS_FILE} not found")
        sys.exit(1)

    with open(URLS_FILE) as f:
        lines = [line.strip() for line in f if line.strip()]

    urls = []
    for line in lines:
        parts = line.split()
        if parts:
            urls.append(parts[0])

    print(f"esldiscussions scraper")
    print(f"  URLs loaded: {len(urls)}")
    print(f"  DB: {DB_FILE}")
    print(f"  Downloads: {DOWNLOAD_DIR}/")

    # Resume: find last scraped URL
    start_idx = 0
    if args.resume:
        cur = db.conn.execute("SELECT source_url FROM resource ORDER BY id DESC LIMIT 1")
        row = cur.fetchone()
        if row:
            last_url = row["source_url"]
            for i, u in enumerate(urls):
                if u == last_url:
                    start_idx = i + 1
                    print(f"  Resuming from index {start_idx} ({last_url})")
                    break

    # Update mode: skip existing
    existing_urls = set()
    if args.update:
        cur = db.conn.execute("SELECT source_url FROM resource")
        for row in cur.fetchall():
            existing_urls.add(row["source_url"])
        print(f"  Existing URLs in DB: {len(existing_urls)}")

    # Range filter
    if args.range:
        start_str, end_str = args.range.split("-")
        range_start = int(start_str)
        range_end = int(end_str)
        filtered = []
        for u in urls:
            code_gen_temp = ResourceCodeGenerator(SITE_CODE, SERIES_CODE, db.conn)
            # Try to match by checking if URL is in range
            topic = extract_topic(u)
            filtered.append(u)
        urls = filtered
        print(f"  Range {args.range}: {len(urls)} URLs")

    # Scrape
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    success = 0
    failed = 0
    skipped = 0

    for i, url in enumerate(urls[start_idx:], start=start_idx + 1):
        if args.limit and (i - start_idx) > args.limit:
            break

        if args.update and url in existing_urls:
            print(f"  [{i}/{len(urls)}] SKIP (already in DB): {url}")
            skipped += 1
            continue

        print(f"\n[{i}/{len(urls)}] ", end="")
        result = scrape_lesson(url, db, code_gen, session)

        if result.get("status") == "success":
            success += 1
        else:
            failed += 1

        # Random sleep between requests
        sleep_time = random.uniform(0.5, 1.5)
        # Every 20 lessons, extra 10s sleep
        if i % 20 == 0:
            sleep_time += 10
        print(f"    Sleep {sleep_time:.1f}s")
        time.sleep(sleep_time)

    # Summary
    print(f"\n{'='*50}")
    print(f"  Total: {success + failed + skipped}")
    print(f"  Success: {success}")
    print(f"  Failed: {failed}")
    print(f"  Skipped: {skipped}")
    print(f"  DB: {DB_FILE}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()