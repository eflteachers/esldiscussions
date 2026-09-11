#!/usr/bin/env python3
"""
test_body_html.py
─────────────────
Regression tests for extract_body_html(): the scraper must CONVERT the source
markup into the restricted body_html structure (see body_html.txt), not merely
strip disallowed tags.

Run through the terminal tool:
    python3 -m pytest tests/ -v
    python3 tests/test_body_html.py
"""
import sys
from pathlib import Path

from bs4 import BeautifulSoup

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "core"))
sys.path.insert(0, str(REPO_ROOT / "series" / "series_01"))

from scraper import extract_body_html

# Mirrors a real lesson page: a <p><strong> header with a parenthetical note,
# then a question <table> whose cells are sometimes wrapped in <p>, plus an
# inline <em> that must become <i> and a dead MS-Word bookmark <a> (no href).
SOURCE = """
<html><body><article>
<p><strong>STUDENT A's QUESTIONS</strong> (Do not show these to Student B.)</p>
<table>
  <tr><td width="6%"><p>1)</p></td><td width="93%"><p>Are you <em>ready</em>?</p></td></tr>
  <tr><td width="6%"><p>2)</p></td><td width="93%"><p>Do you ever <a id="OLE_LINK1" name="OLE_LINK1">wonder</a> why?</p></td></tr>
</table>
<br>
<p><strong>STUDENT B's QUESTIONS</strong> (Do not show these to Student A.)</p>
<table>
  <tr><td width="6%">(1)</td><td width="93%">What is the difference?</td></tr>
  <tr><td width="6%">(2)</td><td width="93%">How many do you know?<br>Tell me.</td></tr>
</table>
</article></body></html>
"""

ALLOWED = {"a", "p", "strong", "li", "i", "ul", "ol", "h1", "h2", "h3"}


def _out():
    return extract_body_html(BeautifulSoup(SOURCE, "lxml"))


def test_section_heading_becomes_h3():
    out = _out()
    soup = BeautifulSoup(out, "lxml")
    headings = [h.get_text(strip=True) for h in soup.find_all("h3")]
    assert headings == ["STUDENT A's QUESTIONS", "STUDENT B's QUESTIONS"]


def test_note_becomes_strong_paragraph():
    out = _out()
    assert "<p><strong>Do not show these to Student B.</strong></p>" in out
    assert "<p><strong>Do not show these to Student A.</strong></p>" in out


def test_table_rows_become_ordered_list():
    out = _out()
    soup = BeautifulSoup(out, "lxml")
    lists = soup.find_all("ol")
    assert len(lists) == 2
    assert [li.get_text(strip=True) for li in lists[1].find_all("li")] == [
        "What is the difference?",
        "How many do you know? Tell me.",
    ]


def test_number_cells_are_dropped():
    out = _out()
    assert "<li>1)</li>" not in out
    assert "<li>(1)</li>" not in out


def test_em_becomes_i_and_dead_anchor_unwrapped():
    out = _out()
    assert "<em>" not in out
    assert "<i>ready</i>" in out
    assert "wonder</a>" not in out  # dead bookmark anchor is unwrapped
    assert "Do you ever wonder why?" in BeautifulSoup(out, "lxml").get_text(" ")


def test_only_allowed_tags_are_emitted():
    out = _out()
    soup = BeautifulSoup(out, "lxml")
    assert {t.name for t in soup.find_all(True)} - {"html", "body"} <= ALLOWED


def test_br_is_not_dropped_mid_sentence():
    out = _out()
    assert "How many do you know? Tell me." in BeautifulSoup(out, "lxml").get_text(" ")


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"PASS {name}")
