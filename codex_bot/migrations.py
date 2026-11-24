from __future__ import annotations

import sqlite3


MIGRATIONS: tuple[tuple[int, str], ...] = (
    (1, """
    CREATE TABLE IF NOT EXISTS business_profiles (
        id INTEGER PRIMARY KEY, name TEXT NOT NULL, industry TEXT NOT NULL, market TEXT NOT NULL,
        business_model TEXT NOT NULL, languages_json TEXT NOT NULL, timezone TEXT NOT NULL DEFAULT 'Asia/Manila',
        brand_personality TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE, category TEXT NOT NULL DEFAULT '',
        description TEXT NOT NULL DEFAULT '', ingredients_json TEXT NOT NULL DEFAULT '[]',
        features_json TEXT NOT NULL DEFAULT '[]', variants_json TEXT NOT NULL DEFAULT '[]', price REAL,
        currency TEXT NOT NULL DEFAULT 'PHP', stock_status TEXT, links_json TEXT NOT NULL DEFAULT '{}',
        policies TEXT, verified INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS marketing_tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT, request_text TEXT NOT NULL, skill TEXT NOT NULL,
        platform TEXT, product_id INTEGER REFERENCES products(id) ON DELETE SET NULL,
        input_json TEXT NOT NULL DEFAULT '{}', status TEXT NOT NULL DEFAULT 'running', error TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS generated_content (
        id INTEGER PRIMARY KEY AUTOINCREMENT, task_id INTEGER REFERENCES marketing_tasks(id) ON DELETE SET NULL,
        platform TEXT NOT NULL DEFAULT '', product_id INTEGER REFERENCES products(id) ON DELETE SET NULL,
        content_type TEXT NOT NULL, title TEXT NOT NULL, hook TEXT NOT NULL DEFAULT '', caption TEXT NOT NULL DEFAULT '',
        hashtags_json TEXT NOT NULL DEFAULT '[]', call_to_action TEXT NOT NULL DEFAULT '', visual_prompt TEXT NOT NULL DEFAULT '',
        suggested_publication_date TEXT, language TEXT NOT NULL DEFAULT 'English', structured_json TEXT NOT NULL DEFAULT '{}',
        approval_status TEXT NOT NULL DEFAULT 'pending_approval'
          CHECK(approval_status IN ('draft','pending_approval','approved','rejected','scheduled','published')),
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS campaigns (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, objective TEXT NOT NULL,
        platforms_json TEXT NOT NULL DEFAULT '[]', start_date TEXT, end_date TEXT, status TEXT NOT NULL DEFAULT 'draft',
        strategy_json TEXT NOT NULL DEFAULT '{}', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS content_calendars (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, duration_days INTEGER NOT NULL,
        start_date TEXT NOT NULL, end_date TEXT NOT NULL, timezone TEXT NOT NULL DEFAULT 'Asia/Manila',
        campaign_id INTEGER REFERENCES campaigns(id) ON DELETE SET NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS calendar_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT, calendar_id INTEGER NOT NULL REFERENCES content_calendars(id) ON DELETE CASCADE,
        content_id INTEGER REFERENCES generated_content(id) ON DELETE SET NULL, publication_date TEXT NOT NULL,
        platform TEXT NOT NULL, objective TEXT NOT NULL DEFAULT '', product_id INTEGER REFERENCES products(id) ON DELETE SET NULL,
        content_type TEXT NOT NULL, hook TEXT NOT NULL DEFAULT '', caption TEXT NOT NULL DEFAULT '',
        hashtags_json TEXT NOT NULL DEFAULT '[]', call_to_action TEXT NOT NULL DEFAULT '', visual_concept TEXT NOT NULL DEFAULT '',
        approval_status TEXT NOT NULL DEFAULT 'draft'
    );
    CREATE TABLE IF NOT EXISTS approval_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT, content_id INTEGER NOT NULL REFERENCES generated_content(id) ON DELETE CASCADE,
        previous_status TEXT, new_status TEXT NOT NULL, note TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS marketing_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT, metric_date TEXT NOT NULL, platform TEXT NOT NULL,
        content_id INTEGER REFERENCES generated_content(id) ON DELETE SET NULL, followers INTEGER, reach INTEGER,
        impressions INTEGER, engagements INTEGER, clicks INTEGER, inquiries INTEGER, orders INTEGER,
        sales REAL, source TEXT NOT NULL DEFAULT 'manual', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS activity_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, event_type TEXT NOT NULL, entity_type TEXT,
        entity_id INTEGER, message TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_generated_content_status ON generated_content(approval_status, id DESC);
    CREATE INDEX IF NOT EXISTS idx_calendar_entries_date ON calendar_entries(publication_date, platform);
    """),
)


def apply_migrations(connection: sqlite3.Connection) -> None:
    connection.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)")
    applied = {row[0] for row in connection.execute("SELECT version FROM schema_migrations")}
    for version, sql in MIGRATIONS:
        if version in applied:
            continue
        connection.executescript(sql)
        connection.execute("INSERT INTO schema_migrations(version) VALUES (?)", (version,))
