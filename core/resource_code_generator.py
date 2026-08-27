#!/usr/bin/env python3
"""
resource_code_generator.py
──────────────────────────
Generates sequential 14-char resource codes:
  {site_code:0>6}{type_code:0>2}{sequence:0>6}

Example: site="006", type="01", seq=1 → "00000601000001"
         site="002", type="01", seq=11 → "00000201000011"
"""
import sqlite3


class ResourceCodeGenerator:
    def __init__(self, site_code: str, type_code: str, conn: sqlite3.Connection):
        self.site_code = site_code.zfill(6)   # 006 → 000006
        self.type_code = type_code.zfill(2)   # 01 → 01
        self.conn = conn

    def get_next_resource_code(self) -> str:
        """Return the next unused resource_code for this site+type."""
        prefix = f"{self.site_code}{self.type_code}"
        row = self.conn.execute(
            "SELECT MAX(resource_code) FROM resource WHERE resource_code LIKE ?",
            (f"{prefix}%",)
        ).fetchone()

        if row and row[0]:
            seq_str = row[0][len(prefix):]      # extract last 6 digits
            next_seq = int(seq_str) + 1
        else:
            next_seq = 1

        return f"{prefix}{next_seq:06d}"