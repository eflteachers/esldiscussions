#!/usr/bin/env python3
"""
esldiscussions_scraper.py
─────────────────────────
Main scraper for esldiscussions.com (source_code=000022).

Scrapes lesson pages from urls.txt (oldest first), extracts metadata,
downloads PDF + Word assets, and populates the SQLite database.

Usage:
    python3 esldiscussions_scraper.py                    # Full scrape
    python3 esldiscussions_scraper.py --resume           # Resume from last
    python3 esldiscussions_scraper.py --limit 5          # First 5 only
    python3 esldiscussions_scraper.py --update           # Update mode (skip existing)
    python3 esldiscussions_scraper.py --refresh-body     # Re-fetch body_html in place
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
from bs4 import BeautifulSoup, NavigableString

# ── Paths ───────────────────────────────────────────────────────────────────
# This scraper lives in series/series_01/. The project root is two levels up.
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CORE_DIR = REPO_ROOT / "core"

# Make core/ importable (shared global scripts)
sys.path.insert(0, str(CORE_DIR))
sys.path.insert(0, str(Path(__file__).resolve().parent))  # local series modules

from global_db import DB
from global_uuid7 import uuid7
from global_sanitization import sanitize_filename, sanitize_folder_name
from global_resource_code_generator import ResourceCodeGenerator
from global_source_registry import SOURCE_REGISTRY
from config import URL_OVERRIDES

# ── Source identity (from SOURCE_REGISTRY) ──────────────────────────────────
SITE_CODE = "000022"
SERIES_CODE = "01"
SOURCE_NAME = SOURCE_REGISTRY[SITE_CODE]["display_name"]
BASE_URL = SOURCE_REGISTRY[SITE_CODE]["urls"]["canonical"]

# Data lives under data/{series}/ ; DB under database/
DATA_DIR = REPO_ROOT / "data" / SERIES_CODE
DOWNLOAD_DIR = DATA_DIR / "downloads"
REPORTS_DIR = DATA_DIR / "reports"
URLS_FILE = DATA_DIR / "urls.txt"
DB_FILE = str(REPO_ROOT / "database" / f"{SOURCE_NAME}.db")
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
    "server": "premium",
    "status": "active",
    "activity_type": "discussion",
    "activity_type_local": "discussion",
    "age_group": "Teens, Adults",
    "audience": "teachers",
    "author_local": "Sean Banville",
    "content_type_local": "Discussion",
    "domain": "ESL",
    "english_variety": "british",
    "focus": "speaking",
    "function": None,
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
    "lesson_topic_a1_locked": 0,
    "lesson_topic_locked": 0,
    "media_type": "text",
    "material_origin": "pedagogic",
    "purpose": "ge",
    "skill": "speaking",
    "situation_locked": 0,
    "stage": None,
    "source_code": SITE_CODE,
    "source_name": SOURCE_NAME,
    "source_series_code": SERIES_CODE,
    "objective": None,
    "notes_local": None,
    "overview": None,
    "function": None,
}


def extract_topic(source_url: str) -> str:
    """Extract topic name from URL like /z/zambia.html → 'Zambia'."""
    path = urlparse(source_url).path
    name = path.rstrip(".html").rsplit("/", 1)[-1]
    name = name.replace("-", " ").replace("_", " ").title()
    return name


def extract_title(soup: BeautifulSoup, topic: str) -> str:
    """Extract title from page."""
    return f"English Discussion on {topic}"


def extract_lesson_topic(topic: str) -> str:
    """lesson_topic = just the topic name (per mapping: 'Zambia')."""
    return topic


def extract_tags(topic: str) -> str:
    """Generate tags value."""
    return f"{topic}, culture, geography, history, travel, tourism, discussion questions"


def find_article(body):
    """Locate the <article> holding the discussion, with a legacy fallback."""
    article = body.find("article")
    if article:
        return article
    for el in body.find_all(["h3", "h2", "strong"]):
        if "THE DISCUSSION ON" in el.get_text(strip=True).upper():
            parent = el.find_parent(["div", "td", "section"])
            if parent:
                return parent
    return None


def normalise_whitespace(html: str) -> str:
    """Collapse runs of whitespace in a serialized HTML fragment."""
    return re.sub(r"\s+", " ", html.replace("\xa0", " ")).strip()


def text_after(node, child) -> str:
    """Plain text of `node` that follows `child`."""
    parts = []
    for sibling in child.next_siblings:
        parts.append(sibling.get_text() if hasattr(sibling, "get_text") else str(sibling))
    return "".join(parts)


def extract_body_html(soup: BeautifulSoup) -> str:
    """
    Extract the discussion as restricted HTML, preserving document structure.

    Source markup (identical on every lesson page) is:

        <p><strong>STUDENT A's QUESTIONS</strong> (Do not show these to Student B.)</p>
        <table>... one <tr> per question, number cell + question cell ...</table>
        <p><strong>STUDENT B's QUESTIONS</strong> ...</p>
        <table>...</table>

    It is converted to the RF structure (see body_html.txt):

        <h3>STUDENT A's QUESTIONS</h3>
        <p><strong>Do not show these to Student B.</strong></p>
        <ol>
        <li>question</li>
        ...
        </ol>

    * section heading  -> <h3>, its parenthetical note -> own <p><strong>
    * question table   -> <ol>/<li>; the (n) number cell is dropped
    * inline tags (<em>, <strong>, real <a>) are preserved; <em> -> <i>
    * only a, p, strong, li, i, ul, ol, h1, h2, h3 are emitted
    """
    body = soup.find("body")
    if not body:
        return ""

    article = find_article(body)
    if not article:
        return ""

    work = BeautifulSoup(str(article), "lxml").find("article")
    if work is None:
        return ""

    # <br> separates inline content — replace with a space rather than dropping it
    for br in work.find_all("br"):
        br.replace_with(" ")

    # Remove non-content elements entirely
    for tag in work.find_all(["script", "iframe", "style", "img"]):
        tag.decompose()

    # <em> becomes <i> (allowed)
    for em in work.find_all("em"):
        em.name = "i"
        em.attrs = {}

    # Keep real links; drop dead MS-Word bookmarks (anchors with no href)
    for a in work.find_all("a"):
        href = a.get("href")
        if href:
            a.attrs = {
                "href": href,
                "target": "_blank",
                "rel": "nofollow noopener noreferrer",
            }
        else:
            a.unwrap()

    # Section header: <p><strong>TITLE</strong> (note)</p>
    #              -> <h3>TITLE</h3> + <p><strong>note</strong></p>
    for p in list(work.find_all("p")):
        strong = p.find("strong")
        if strong is None:
            continue
        title = strong.get_text(" ", strip=True)
        if "QUESTIONS" not in title.upper():
            continue
        note = normalise_whitespace(text_after(p, strong)).strip("()").strip()
        heading = work.new_tag("h3")
        heading.string = title
        if note:
            note_p = work.new_tag("p")
            note_strong = work.new_tag("strong")
            note_strong.string = note
            note_p.append(note_strong)
            p.replace_with(heading, note_p)
        else:
            p.replace_with(heading)

    # Question tables: one <tr> per question -> <ol><li>...</li></ol>
    for table in list(work.find_all("table")):
        ordered = work.new_tag("ol")
        for tr in table.find_all("tr"):
            cells = tr.find_all("td")
            if not cells:
                continue
            question_cell = cells[-1]
            # Unwrap inner <p> wrappers; the <li> takes their place
            for inner_p in question_cell.find_all("p"):
                inner_p.insert_after(NavigableString(" "))
                inner_p.unwrap()
            li = work.new_tag("li")
            for content in list(question_cell.contents):
                li.append(content.extract())
            ordered.append(li)
        table.replace_with(ordered)

    # Drop empty paragraphs left behind by the source markup
    for p in work.find_all("p"):
        if not p.get_text(strip=True) and not p.find("a"):
            p.decompose()

    # Enforce the allow-list: anything else is unwrapped (text kept)
    allowed = {"a", "p", "strong", "li", "i", "ul", "ol", "h1", "h2", "h3"}
    for tag in work.find_all(True):
        if tag.name not in allowed:
            tag.unwrap()

    # Render blocks in document order
    blocks = []
    for child in work.children:
        name = getattr(child, "name", None)
        if name in ("h1", "h2", "h3"):
            if blocks:
                blocks.append("")
            blocks.append(f"<{name}>{normalise_whitespace(child.decode_contents())}</{name}>")
        elif name == "p":
            if child.get_text(strip=True):
                blocks.append(f"<p>{normalise_whitespace(child.decode_contents())}</p>")
        elif name in ("ol", "ul"):
            items = [
                f"<li>{normalise_whitespace(li.decode_contents())}</li>"
                for li in child.find_all("li", recursive=False)
            ]
            if items:
                blocks.append("<ol>\n" + "\n".join(items) + "\n</ol>")
    return "\n".join(blocks)


def build_download_folder_name(topic: str, resource_code: str) -> str:
    """
    Build folder name per mapping: {sanitized_topic}_discussion_{resource_code}
    Example: 'zambia_discussion_00002201000001'
    """
    sanitized = sanitize_folder_name(topic)
    return f"{sanitized}_discussion_{resource_code}"


def build_file_name(component_type: str, folder_name: str, resource_code: str) -> str:
    """
    Build file name base per Scraping Guidelines:
        file_name = component_type_{download_folder_name minus resource_code}
    The file base MUST match the folder's title base (only the resource_code
    suffix is dropped) so folder and file share one consistent title.

    folder_name = 'zambia_discussion_00002201000688'
    → base      = 'zambia_discussion'
    → returns     'student_zambia_discussion'  (extension appended separately)
    """
    base = folder_name
    suffix = f"_{resource_code}"
    if base.endswith(suffix):
        base = base[: -len(suffix)]
    return f"{component_type}_{base}"


def extract_asset_urls(soup: BeautifulSoup, page_url: str) -> dict:
    """
    Find PDF and DOC download URLs from the page.

    NOTE: URL_OVERRIDES applies to LESSON PAGE urls (urls.txt), never to asset
    URLs. Applying it here would rewrite russia.pdf → russia.html and destroy a
    perfectly valid PDF asset.
    """
    assets = {"pdf": None, "doc": None}
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        text = a_tag.get_text(strip=True).lower()
        full_url = urljoin(page_url, href)
        if full_url.lower().endswith(".pdf"):
            assets["pdf"] = full_url
        elif full_url.lower().endswith(".doc") and "pdf" not in text:
            assets["doc"] = full_url
    return assets


def download_asset(url: str, dest_path: Path) -> dict:
    """
    Download a single asset file to .part, validate, rename.

    Some esldiscussions asset links use a capitalised filename (e.g. June.pdf)
    while the file on the server is lowercase (june.pdf); the CDN answers 403 for
    the wrong case. On 403/404 we retry once with a lowercased filename.
    """
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

    # Build candidate URLs: as-linked, then lowercase-filename fallback
    candidates = [url]
    parts = url.rsplit("/", 1)
    if len(parts) == 2 and parts[1] != parts[1].lower():
        candidates.append(f"{parts[0]}/{parts[1].lower()}")

    temp_path = dest_path.with_suffix(dest_path.suffix + ".part")
    for candidate in candidates:
        try:
            resp = requests.get(candidate, headers={"User-Agent": USER_AGENT}, timeout=60, stream=True)
            result["http_status"] = resp.status_code
            if resp.status_code != 200:
                result["download_status"] = "failed"
                continue

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
                continue

            temp_path.rename(dest_path)
            result["checksum"] = sha256.hexdigest()
            result["file_exists"] = 1
            result["download_status"] = "success"
            result["final_url"] = candidate
            return result
        except Exception as e:
            temp_path.unlink(missing_ok=True)
            result["download_status"] = "failed"
            result["validation_notes"] = str(e)
    return result


def scrape_lesson(url: str, db: DB, code_gen: ResourceCodeGenerator, session: requests.Session) -> dict:
    """Scrape a single lesson page and return all field values."""
    print(f"  Scraping: {url}")

    try:
        resp = session.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"    ERROR: {e}")
        return {"error": str(e), "http_status": getattr(e.response, "status_code", None)}

    # Parse bytes, not resp.text: the response carries no charset so requests
    # would fall back to ISO-8859-1 and mangle the site's UTF-8 content.
    soup = BeautifulSoup(resp.content, "lxml")
    http_status = resp.status_code

    topic = extract_topic(url)
    topic_slug = url.rstrip(".html").rsplit("/", 1)[-1]

    title = extract_title(soup, topic)
    resource_uuid = uuid7()
    resource_code = code_gen.get_next_resource_code()
    sequence = resource_code[-6:]

    # Build folder and file names
    folder_name = build_download_folder_name(topic, resource_code)
    download_folder = DOWNLOAD_DIR / folder_name

    # Asset URLs
    asset_urls = extract_asset_urls(soup, url)

    # Body HTML (restricted tags only)
    body_html = extract_body_html(soup)

    # Build resource data
    resource_data = {
        "uuid": resource_uuid,
        "resource_code": resource_code,
        "source_code": SITE_CODE,
        "source_name": SOURCE_NAME,
        "source_series_code": SERIES_CODE,
        "sequence": sequence,
        "source_url": url,
        "title": title,
        "date": TODAY,  # source has no publish date → fallback to today
        "date_1st_scraped": TODAY,
        "download_folder_name": folder_name,
        "body_html": body_html,
        "lesson_topic": None,
        "lesson_topic_local": extract_lesson_topic(topic),
        "tags": None,
        "file_extension": None,
        "count_audio": 0,
        "count_document": 0,
        "count_presentation": 0,
        "count_total": 0,
        "count_video": 0,
        "size_doc": None,
        "size_doc_bytes": None,
        "size_files": None,
        "size_files_bytes": None,
    }
    resource_data.update(CONSTANTS)

    # Download assets
    assets = []
    total_size = 0
    extensions = set()

    for asset_type, asset_url in [("pdf", asset_urls["pdf"]), ("doc", asset_urls["doc"])]:
        if not asset_url:
            continue

        ext = asset_type
        extensions.add(ext)

        asset_uuid = uuid7()
        asset_code = f"{resource_code}_AS{(len(assets) + 1):02d}"

        # File name per Guidelines: component_type_{download_folder_name minus resource_code}.ext
        file_base = build_file_name("student", folder_name, resource_code)
        final_filename = f"{file_base}.{ext}"
        dest_path = download_folder / final_filename

        dl_result = download_asset(asset_url, dest_path)
        total_size += dl_result.get("size_bytes", 0)

        mime_map = {"pdf": "application/pdf", "doc": "application/msword"}
        mime = mime_map.get(ext, "application/octet-stream")

        orig_filename = f"{topic_slug}.{ext}"

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
            "title": sanitize_filename(orig_filename),
            "title_local": orig_filename,
            "type": "document",
            "url": asset_url,
            "url_local": dl_result.get("final_url", asset_url),
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

    # ── Counters ─────────────────────────────────────────────────────────────
    # Per RF guidelines the four counters mean different things:
    #   expected   = what a generic detector thinks the page offers
    #   scraped    = rows actually inserted into the child table
    #   downloaded = files really downloaded and healthy
    #   count      = rows that are valid + usable for the RF user
    doc_expected = len([u for u in (asset_urls["pdf"], asset_urls["doc"]) if u])
    doc_scraped = len(assets)
    doc_downloaded = len([a for a in assets if a["download_status"] == "success"])
    doc_valid = len([a for a in assets if a["validation_status"] == "valid"])

    resource_data["count_document"] = doc_valid
    resource_data["count_total"] = 1
    # File extension in mapping order: pdf, doc (not alphabetical); only valid files
    valid_exts = {a["extension"] for a in assets if a["validation_status"] == "valid"}
    resource_data["file_extension"] = ", ".join(e for e in ("pdf", "doc") if e in valid_exts)
    resource_data["size_doc"] = f"{total_size / 1024:.2f} KB" if total_size else None
    resource_data["size_doc_bytes"] = total_size
    resource_data["size_files"] = resource_data["size_doc"]
    resource_data["size_files_bytes"] = total_size

    # Overall statuses derived from the child rows, never hardcoded
    if doc_scraped == 0:
        download_status = "not_downloadable"
    elif doc_downloaded == doc_scraped:
        download_status = "success"
    elif doc_downloaded == 0:
        download_status = "failed"
    else:
        download_status = "partial"

    if doc_valid == doc_scraped:
        validation_status = "passed"
    elif doc_valid == 0 and doc_scraped > 0:
        validation_status = "failed"
    else:
        validation_status = "partial"

    needs_review = 0 if validation_status == "passed" else 1
    resource_data["validation_status"] = validation_status
    resource_data["needs_review"] = needs_review

    if validation_status == "passed":
        validation_notes = (
            f"Page returned HTTP {http_status}; all {doc_valid} document(s) downloaded and validated."
        )
    else:
        failed_titles = ", ".join(
            a["title"] for a in assets if a["validation_status"] != "valid"
        )
        validation_notes = (
            f"Page returned HTTP {http_status}; "
            f"{doc_downloaded}/{doc_scraped} document(s) downloaded. Failed: {failed_titles}."
        )

    # Insert into DB
    try:
        db.insert_resource(resource_data)
        for asset in assets:
            db.insert_asset(asset)

        validation_data = {
            "resource_uuid": resource_uuid,
            "source_url": url,
            "final_url": resp.url or url,
            "download_status": download_status,
            "http_status": http_status,
            "needs_review": needs_review,
            "scrape_error": "none" if validation_status == "passed" else "download_link_not_found",
            "scrape_status": "success",
            "validation_status": validation_status,
            "validated_at": NOW,
            "validation_notes": validation_notes,
            "count_audio_expected": 0,
            "count_audio_scraped": 0,
            "count_audio_downloaded": 0,
            "count_audio": 0,
            "count_document_expected": doc_expected,
            "count_document_scraped": doc_scraped,
            "count_document_downloaded": doc_downloaded,
            "count_document": doc_valid,
            "count_presentation_expected": 0,
            "count_presentation_scraped": 0,
            "count_presentation_downloaded": 0,
            "count_presentation": 0,
            "count_total_expected": doc_expected,
            "count_total_scraped": doc_scraped,
            "count_total_downloaded": doc_downloaded,
            "count_total": doc_valid,
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


def refresh_lesson_body(url: str, db: DB, session: requests.Session) -> dict:
    """
    Re-fetch an existing lesson and update ONLY its body_html in place.

    Used by --refresh-body: no assets are downloaded and no rows are inserted,
    so re-running can never duplicate resources.
    """
    try:
        resp = session.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        return {"status": "failed", "error": str(e)}

    body_html = extract_body_html(BeautifulSoup(resp.content, "lxml"))

    row = db.conn.execute(
        "SELECT uuid FROM resource WHERE source_url = ?", (url,)
    ).fetchone()
    if row is None:
        return {"status": "failed", "error": "not in DB"}

    db.update_resource(row["uuid"], {"body_html": body_html, "date_updated": NOW})
    return {"status": "success", "uuid": row["uuid"]}


def main():
    parser = argparse.ArgumentParser(description="esldiscussions.com scraper")
    parser.add_argument("--resume", action="store_true", help="Resume from last scraped")
    parser.add_argument("--limit", type=int, help="Max lessons to scrape")
    parser.add_argument("--update", action="store_true", help="Update mode (skip existing)")
    parser.add_argument(
        "--refresh-body",
        action="store_true",
        help="Re-fetch body_html for lessons already in DB (no downloads, no duplicates)",
    )
    args = parser.parse_args()

    # Ensure output dirs exist
    Path(DB_FILE).parent.mkdir(parents=True, exist_ok=True)
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    db = DB(DB_FILE)
    code_gen = ResourceCodeGenerator(SITE_CODE, SERIES_CODE, db.conn)

    if not os.path.exists(URLS_FILE):
        print(f"ERROR: {URLS_FILE} not found")
        sys.exit(1)

    with open(URLS_FILE) as f:
        lines = [line.strip() for line in f if line.strip()]

    urls = []
    for line in lines:
        parts = line.split()
        if parts:
            url = URL_OVERRIDES.get(parts[0], parts[0])
            urls.append(url)

    print(f"esldiscussions scraper (source_code={SITE_CODE})")
    print(f"  URLs loaded: {len(urls)}")
    print(f"  DB: {DB_FILE}")
    print(f"  Downloads: {DOWNLOAD_DIR}/")

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

    existing_urls = set()
    if args.update:
        cur = db.conn.execute("SELECT source_url FROM resource")
        for row in cur.fetchall():
            existing_urls.add(row["source_url"])
        print(f"  Existing URLs in DB: {len(existing_urls)}")

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    success = 0
    failed = 0
    skipped = 0
    max_retries = 3

    for i, url in enumerate(urls[start_idx:], start=start_idx + 1):
        if args.limit and (i - start_idx) > args.limit:
            break

        if args.refresh_body:
            result = refresh_lesson_body(url, db, session)
            if result.get("status") == "success":
                success += 1
                print(f"  [{i}/{len(urls)}] refreshed body_html: {url}")
            else:
                failed += 1
                print(f"  [{i}/{len(urls)}] FAILED: {url} ({result.get('error')})")
            time.sleep(random.uniform(0.2, 0.6))
            continue

        if args.update and url in existing_urls:
            print(f"  [{i}/{len(urls)}] SKIP (already in DB): {url}")
            skipped += 1
            continue

        print(f"\n[{i}/{len(urls)}] ", end="")

        for attempt in range(1, max_retries + 1):
            result = scrape_lesson(url, db, code_gen, session)
            if result.get("status") == "success":
                success += 1
                break
            else:
                if attempt < max_retries:
                    wait = 5 * attempt
                    print(f"    ⚠ Attempt {attempt}/{max_retries} failed, retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    print(f"    ✗ FAILED after {max_retries} attempts: {result.get('error', 'unknown')}")
                    failed += 1

        sleep_time = random.uniform(0.5, 1.5)
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
    print(f"  Downloads: {str(DOWNLOAD_DIR)}/")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()