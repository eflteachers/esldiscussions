#!/usr/bin/env python3
"""
init_schema.py
──────────────
Initialise an empty SQLite database with the full RF schema (6 tables) from
core/database.py, without running the scraper. Useful for a clean start or to
inspect the schema.

Invoke through the terminal tool:
    python3 init_schema.py                 # creates database/{source_name}.db
    python3 init_schema.py --db path.db    # custom path
"""
import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT / "core"))
sys.path.insert(0, str(REPO_ROOT / "series" / "series_01"))

from global_database import DB
from global_source_registry import SOURCE_REGISTRY

SITE_CODE = "000022"
SOURCE_NAME = SOURCE_REGISTRY[SITE_CODE]["display_name"]


def main():
    parser = argparse.ArgumentParser(description="Initialise RF SQLite schema")
    parser.add_argument("--db", default=str(REPO_ROOT / "database" / f"{SOURCE_NAME}.db"))
    args = parser.parse_args()

    Path(args.db).parent.mkdir(parents=True, exist_ok=True)
    db = DB(args.db)
    tables = [r[0] for r in db.conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()]
    print(f"Initialised {args.db}")
    print(f"Tables: {', '.join(tables)}")


if __name__ == "__main__":
    main()
