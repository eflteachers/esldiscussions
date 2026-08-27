#!/usr/bin/env python3
"""
test_resource_codes.py
──────────────────────
Basic tests for the RF resource_code generator: format, sequence increment,
and per-source isolation. Invoke through the terminal tool:
    python3 -m pytest tests/ -v
"""
import sqlite3
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "core"))

from resource_code_generator import ResourceCodeGenerator


def _mem_db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("CREATE TABLE resource (resource_code TEXT)")
    return conn


def test_first_code_is_sequence_one():
    conn = _mem_db()
    gen = ResourceCodeGenerator("000022", "01", conn)
    assert gen.get_next_resource_code() == "00002201000001"


def test_code_is_14_chars():
    conn = _mem_db()
    gen = ResourceCodeGenerator("000022", "01", conn)
    assert len(gen.get_next_resource_code()) == 14


def test_sequence_increments():
    conn = _mem_db()
    gen = ResourceCodeGenerator("000022", "01", conn)
    c1 = gen.get_next_resource_code()
    conn.execute("INSERT INTO resource (resource_code) VALUES (?)", (c1,))
    c2 = gen.get_next_resource_code()
    assert c1 == "00002201000001"
    assert c2 == "00002201000002"


def test_series_isolation():
    conn = _mem_db()
    g1 = ResourceCodeGenerator("000022", "01", conn)
    c1 = g1.get_next_resource_code()
    conn.execute("INSERT INTO resource (resource_code) VALUES (?)", (c1,))
    g2 = ResourceCodeGenerator("000022", "02", conn)
    assert g2.get_next_resource_code() == "00002202000001"


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"PASS {name}")
