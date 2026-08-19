#!/usr/bin/env python3
"""
global_db.py
────────────
Shared SQLite schema for RF scrapers (new schema with resource_code).

Fields are grouped by table and listed in the exact insertion order
expected by WordPress / JetEngine.
"""
import sqlite3
from pathlib import Path


class DB:
    def __init__(self, db_path: str = "rf_scraper.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._ensure_tables()

    # ── Table creation ──────────────────────────────────────────────────────────
    def _ensure_tables(self):
        c = self.conn.cursor()

        # ── resource ─────────────────────────────────────────────────────────────
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS resource (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uuid TEXT NOT NULL UNIQUE,
                resource_code TEXT,
                parent_uuid TEXT,
                source_url TEXT,
                validation_status TEXT,
                needs_review INTEGER,
                source_id TEXT,
                title TEXT,
                level TEXT,
                resource_type TEXT,
                resource_form TEXT,
                assessment_type TEXT,
                directory_type TEXT,
                input_genre TEXT,
                resource_form_local TEXT,
                pd_type TEXT,
                reference_type TEXT,
                research_type TEXT,
                tool_type TEXT,
                is_learning_path INTEGER,
                server TEXT,
                status TEXT,
                wordpress_post_id INTEGER,
                activity_type TEXT,
                activity_type_local TEXT,
                age_group TEXT,
                age_group_local TEXT,
                audience TEXT,
                audience_local TEXT,
                audio_duration_cat TEXT,
                author_local TEXT,
                body_html TEXT,
                body_wp TEXT,
                buy_collection TEXT,
                category_local TEXT,
                content_type TEXT,
                content_type_local TEXT,
                count_audio INTEGER,
                count_document INTEGER,
                count_presentation INTEGER,
                count_total INTEGER,
                count_video INTEGER,
                date TEXT,
                date_1st_scraped TEXT,
                date_scraped TEXT,
                date_updated TEXT,
                dl_audio TEXT,
                dl_docs TEXT,
                dl_files TEXT,
                dl_folder TEXT,
                dl_video1080 TEXT,
                dl_video720 TEXT,
                domain TEXT,
                domain_local TEXT,
                download_folder_name TEXT,
                english_variety TEXT,
                esp TEXT,
                event TEXT,
                event_local TEXT,
                exam_local TEXT,
                exam TEXT,
                featured_image TEXT,
                featured_image_local TEXT,
                file_extension TEXT,
                focus TEXT,
                focus_local TEXT,
                format TEXT,
                format_local TEXT,
                framework TEXT,
                function TEXT,
                function_local TEXT,
                function_locked INTEGER,
                grammar TEXT,
                grammar_local TEXT,
                grammar_locked INTEGER,
                has_answer INTEGER,
                has_audio INTEGER,
                has_presentation INTEGER,
                has_teacher INTEGER,
                has_video INTEGER,
                html_created_local INTEGER,
                interaction_pattern TEXT,
                interactivity TEXT,
                interactive_platform TEXT,
                is_ai_generated TEXT,
                is_collection INTEGER,
                is_deleted INTEGER,
                is_free INTEGER,
                is_game INTEGER,
                is_printable INTEGER,
                language TEXT,
                lesson_time TEXT,
                lesson_topic_a1 TEXT,
                lesson_topic_a1_local TEXT,
                lesson_topic_a1_locked INTEGER,
                lesson_topic TEXT,
                lesson_topic_local TEXT,
                lesson_topic_locked INTEGER,
                lesson_type TEXT,
                lesson_type_local TEXT,
                media_type TEXT,
                media_type_local TEXT,
                material_origin TEXT,
                notes_local TEXT,
                objective TEXT,
                overview TEXT,
                popularity_score INTEGER,
                popularity_rate_local REAL,
                popularity_rate_max_local REAL,
                popularity_likes_local INTEGER,
                presentation_downloaded_local INTEGER,
                presentation_url TEXT,
                presentation_url_local TEXT,
                purpose TEXT,
                situation TEXT,
                situation_local TEXT,
                situation_locked INTEGER,
                size_1080 TEXT,
                size_1080_bytes INTEGER,
                size_720 TEXT,
                size_720_bytes INTEGER,
                size_audio TEXT,
                size_audio_bytes INTEGER,
                size_doc TEXT,
                size_doc_bytes INTEGER,
                size_files TEXT,
                size_files_bytes INTEGER,
                skill TEXT,
                skill_local TEXT,
                stage TEXT,
                tags_local TEXT,
                tags TEXT,
                video_downloaded_local INTEGER,
                video_duration_cat TEXT,
                website TEXT,
                whiteboard_url TEXT,
                whiteboard_url_local TEXT
            )
            """
        )

        # ── resource_validation ──────────────────────────────────────────────────
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS resource_validation (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resource_uuid TEXT,
                source_url TEXT,
                final_url TEXT,
                download_status TEXT,
                http_status INTEGER,
                needs_review INTEGER,
                scrape_error TEXT,
                scrape_status TEXT,
                validation_status TEXT,
                validated_at TEXT,
                validation_notes TEXT,
                count_audio_expected INTEGER,
                count_audio_scraped INTEGER,
                count_audio_downloaded INTEGER,
                count_audio INTEGER,
                count_document_expected INTEGER,
                count_document_scraped INTEGER,
                count_document_downloaded INTEGER,
                count_document INTEGER,
                count_presentation_expected INTEGER,
                count_presentation_scraped INTEGER,
                count_presentation_downloaded INTEGER,
                count_presentation INTEGER,
                count_total_expected INTEGER,
                count_total_scraped INTEGER,
                count_total_downloaded INTEGER,
                count_total INTEGER,
                count_video_expected INTEGER,
                count_video_scraped INTEGER,
                count_video_downloaded INTEGER,
                count_video INTEGER
            )
            """
        )

        # ── audio ────────────────────────────────────────────────────────────────
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS audio (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resource_uuid TEXT,
                resource_code TEXT,
                uuid TEXT,
                sort_order INTEGER,
                description TEXT,
                duration TEXT,
                duration_seconds INTEGER,
                extension TEXT,
                extension_local TEXT,
                file TEXT,
                file_local TEXT,
                mime_type TEXT,
                notes_local TEXT,
                size TEXT,
                source TEXT,
                source_url TEXT,
                title TEXT,
                transcript TEXT,
                checksum_original TEXT,
                checksum_final TEXT,
                download_status TEXT,
                file_exists INTEGER,
                http_status INTEGER,
                size_bytes INTEGER,
                validated_at TEXT,
                validation_notes TEXT,
                validation_status TEXT
            )
            """
        )

        # ── video ────────────────────────────────────────────────────────────────
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS video (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resource_uuid TEXT,
                resource_code TEXT,
                uuid TEXT,
                sort_order INTEGER,
                cover TEXT,
                cover_local TEXT,
                description TEXT,
                duration TEXT,
                duration_seconds INTEGER,
                extension TEXT,
                extension_local TEXT,
                file TEXT,
                file_local TEXT,
                has_subtitle INTEGER,
                mime_type TEXT,
                notes_local TEXT,
                size TEXT,
                source TEXT,
                source_url TEXT,
                subtitle_language TEXT,
                title TEXT,
                transcript TEXT,
                type TEXT,
                checksum_original TEXT,
                checksum_final TEXT,
                download_status TEXT,
                file_exists INTEGER,
                http_status INTEGER,
                size_bytes INTEGER,
                validated_at TEXT,
                validation_notes TEXT,
                validation_status TEXT
            )
            """
        )

        # ── asset ────────────────────────────────────────────────────────────────
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS asset (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resource_uuid TEXT,
                resource_code TEXT,
                asset_code TEXT,
                uuid TEXT,
                sort_order INTEGER,
                component_type TEXT,
                extension TEXT,
                extension_local TEXT,
                mime_type TEXT,
                notes_local TEXT,
                printable INTEGER,
                size TEXT,
                source TEXT,
                title TEXT,
                title_local TEXT,
                type TEXT,
                url TEXT,
                url_local TEXT,
                checksum_original TEXT,
                checksum_final TEXT,
                download_status TEXT,
                file_exists INTEGER,
                http_status INTEGER,
                size_bytes INTEGER,
                validated_at TEXT,
                validation_notes TEXT,
                validation_status TEXT
            )
            """
        )

        # ── resource_relationship (new table per client point 14) ────────────────
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS resource_relationship (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_resource_uuid TEXT,
                to_url TEXT,
                relationship_type TEXT,
                relationship_data TEXT,
                created_at TEXT
            )
            """
        )

        self.conn.commit()

    # ── Field lists (must match CREATE TABLE column order) ──────────────────────
    RESOURCE_FIELDS = [
        "uuid", "resource_code", "parent_uuid", "source_url",
        "validation_status", "needs_review", "source_id", "title",
        "level", "resource_type", "resource_form", "assessment_type", "directory_type", "input_genre", "resource_form_local", "pd_type", "reference_type", "research_type", "tool_type", "is_learning_path", "server", "status",
        "wordpress_post_id", "activity_type", "activity_type_local",
        "age_group", "age_group_local", "audience", "audience_local",
        "audio_duration_cat", "author_local", "body_html", "body_wp",
        "buy_collection", "category_local", "content_type", "content_type_local",
        "count_audio", "count_document", "count_presentation", "count_total",
        "count_video", "date", "date_1st_scraped", "date_scraped",
        "date_updated", "dl_audio", "dl_docs", "dl_files", "dl_folder",
        "dl_video1080", "dl_video720", "domain", "domain_local",
        "download_folder_name", "english_variety", "esp", "event",
        "event_local", "exam_local", "exam", "featured_image",
        "featured_image_local", "file_extension", "focus", "focus_local",
        "format", "format_local", "framework", "function",
        "function_local", "function_locked", "grammar", "grammar_local",
        "grammar_locked", "has_answer", "has_audio", "has_presentation",
        "has_teacher", "has_video", "html_created_local", "interaction_pattern",
        "interactivity", "interactive_platform", "is_ai_generated",
        "is_collection", "is_deleted", "is_free", "is_game",
        "is_printable", "language", "lesson_time", "lesson_topic_a1",
        "lesson_topic_a1_local", "lesson_topic_a1_locked", "lesson_topic",
        "lesson_topic_local", "lesson_topic_locked", "lesson_type",
        "lesson_type_local", "media_type", "media_type_local",
        "material_origin", "notes_local", "objective", "overview",
        "popularity_score", "popularity_rate_local", "popularity_rate_max_local",
        "popularity_likes_local", "presentation_downloaded_local",
        "presentation_url", "presentation_url_local", "purpose",
        "situation", "situation_local", "situation_locked",
        "size_1080", "size_1080_bytes", "size_720", "size_720_bytes",
        "size_audio", "size_audio_bytes", "size_doc", "size_doc_bytes",
        "size_files", "size_files_bytes", "skill", "skill_local",
        "stage", "tags_local", "tags", "video_downloaded_local",
        "video_duration_cat", "website", "whiteboard_url", "whiteboard_url_local",
    ]

    RESOURCE_VALIDATION_FIELDS = [
        "resource_uuid", "source_url", "final_url", "download_status",
        "http_status", "needs_review", "scrape_error", "scrape_status",
        "validation_status", "validated_at", "validation_notes",
        "count_audio_expected", "count_audio_scraped", "count_audio_downloaded", "count_audio",
        "count_document_expected", "count_document_scraped", "count_document_downloaded", "count_document",
        "count_presentation_expected", "count_presentation_scraped", "count_presentation_downloaded", "count_presentation",
        "count_total_expected", "count_total_scraped", "count_total_downloaded", "count_total",
        "count_video_expected", "count_video_scraped", "count_video_downloaded", "count_video",
    ]

    AUDIO_FIELDS = [
        "resource_uuid", "resource_code", "uuid", "sort_order", "description",
        "duration", "duration_seconds", "extension", "extension_local",
        "file", "file_local", "mime_type", "notes_local", "size",
        "source", "source_url", "title", "transcript",
        "checksum_original", "checksum_final", "download_status",
        "file_exists", "http_status", "size_bytes", "validated_at",
        "validation_notes", "validation_status",
    ]

    VIDEO_FIELDS = [
        "resource_uuid", "resource_code", "uuid", "sort_order", "cover",
        "cover_local", "description", "duration", "duration_seconds",
        "extension", "extension_local", "file", "file_local",
        "has_subtitle", "mime_type", "notes_local", "size", "source",
        "source_url", "subtitle_language", "title", "transcript",
        "type", "checksum_original", "checksum_final", "download_status",
        "file_exists", "http_status", "size_bytes", "validated_at",
        "validation_notes", "validation_status",
    ]

    ASSET_FIELDS = [
        "resource_uuid", "resource_code", "asset_code", "uuid", "sort_order",
        "component_type", "extension", "extension_local", "mime_type",
        "notes_local", "printable", "size", "source", "title",
        "title_local", "type", "url", "url_local",
        "checksum_original", "checksum_final", "download_status",
        "file_exists", "http_status", "size_bytes", "validated_at",
        "validation_notes", "validation_status",
    ]

    # ── Generic insert helpers ──────────────────────────────────────────────────
    def insert_resource(self, data: dict):
        cols = [f for f in self.RESOURCE_FIELDS if f in data]
        placeholders = ", ".join(["?"] * len(cols))
        sql = f"INSERT INTO resource ({', '.join(cols)}) VALUES ({placeholders})"
        self.conn.execute(sql, [data[c] for c in cols])
        self.conn.commit()

    def update_resource(self, uuid: str, data: dict):
        cols = [f for f in self.RESOURCE_FIELDS if f in data and f != "uuid"]
        set_clause = ", ".join([f"{c} = ?" for c in cols])
        sql = f"UPDATE resource SET {set_clause} WHERE uuid = ?"
        self.conn.execute(sql, [data[c] for c in cols] + [uuid])
        self.conn.commit()

    def get_resource_by_uuid(self, uuid: str):
        cur = self.conn.execute("SELECT * FROM resource WHERE uuid = ?", (uuid,))
        row = cur.fetchone()
        return dict(row) if row else None

    def delete_resource_children(self, resource_uuid: str):
        for tbl in ("audio", "video", "asset", "resource_validation"):
            self.conn.execute(f"DELETE FROM {tbl} WHERE resource_uuid = ?", (resource_uuid,))
        self.conn.execute(
            "DELETE FROM resource_relationship WHERE from_resource_uuid = ?",
            (resource_uuid,)
        )
        self.conn.commit()

    def insert_resource_validation(self, data: dict):
        cols = [f for f in self.RESOURCE_VALIDATION_FIELDS if f in data]
        placeholders = ", ".join(["?"] * len(cols))
        sql = f"INSERT INTO resource_validation ({', '.join(cols)}) VALUES ({placeholders})"
        self.conn.execute(sql, [data[c] for c in cols])
        self.conn.commit()

    def insert_audio(self, data: dict):
        cols = [f for f in self.AUDIO_FIELDS if f in data]
        placeholders = ", ".join(["?"] * len(cols))
        sql = f"INSERT INTO audio ({', '.join(cols)}) VALUES ({placeholders})"
        self.conn.execute(sql, [data[c] for c in cols])
        self.conn.commit()

    def insert_video(self, data: dict):
        cols = [f for f in self.VIDEO_FIELDS if f in data]
        placeholders = ", ".join(["?"] * len(cols))
        sql = f"INSERT INTO video ({', '.join(cols)}) VALUES ({placeholders})"
        self.conn.execute(sql, [data[c] for c in cols])
        self.conn.commit()

    def insert_asset(self, data: dict):
        cols = [f for f in self.ASSET_FIELDS if f in data]
        placeholders = ", ".join(["?"] * len(cols))
        sql = f"INSERT INTO asset ({', '.join(cols)}) VALUES ({placeholders})"
        self.conn.execute(sql, [data[c] for c in cols])
        self.conn.commit()


if __name__ == "__main__":
    import sys
    db_path = sys.argv[1] if len(sys.argv) > 1 else "rf_scraper.db"
    db = DB(db_path)
    print(f"Database initialized: {db_path}")