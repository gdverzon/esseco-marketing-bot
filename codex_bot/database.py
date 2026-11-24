from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from codex_bot.migrations import apply_migrations


SCHEMA = """
CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS approvals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action_type TEXT NOT NULL,
    payload TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','approved','rejected','completed','failed')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    decided_at TEXT,
    result TEXT
);
CREATE TABLE IF NOT EXISTS marketing_content (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_type TEXT NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    brief TEXT NOT NULL DEFAULT '',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'draft'
        CHECK(status IN ('draft','pending_approval','approved','rejected')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id, id);
CREATE INDEX IF NOT EXISTS idx_marketing_content_status ON marketing_content(status, id DESC);
CREATE INDEX IF NOT EXISTS idx_marketing_content_type ON marketing_content(content_type, id DESC);
"""


class Database:
    def __init__(self, path: Path | str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(SCHEMA)
            apply_migrations(connection)

    def create_conversation(self, title: str) -> int:
        with self.connect() as connection:
            cursor = connection.execute("INSERT INTO conversations(title) VALUES (?)", (title[:100],))
            return int(cursor.lastrowid)

    def list_conversations(self, limit: int = 50) -> list[dict]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM conversations ORDER BY updated_at DESC, id DESC LIMIT ?", (limit,)
            ).fetchall()
            return [dict(row) for row in rows]

    def add_message(self, conversation_id: int, role: str, content: str) -> int:
        if role not in {"user", "assistant"}:
            raise ValueError("role must be user or assistant")
        with self.connect() as connection:
            cursor = connection.execute(
                "INSERT INTO messages(conversation_id, role, content) VALUES (?, ?, ?)",
                (conversation_id, role, content),
            )
            connection.execute(
                "UPDATE conversations SET updated_at=CURRENT_TIMESTAMP WHERE id=?", (conversation_id,)
            )
            return int(cursor.lastrowid)

    def get_messages(self, conversation_id: int, limit: int | None = None) -> list[dict]:
        query = "SELECT * FROM messages WHERE conversation_id=? ORDER BY id"
        params: tuple = (conversation_id,)
        if limit:
            query = "SELECT * FROM (SELECT * FROM messages WHERE conversation_id=? ORDER BY id DESC LIMIT ?) ORDER BY id"
            params = (conversation_id, limit)
        with self.connect() as connection:
            return [dict(row) for row in connection.execute(query, params).fetchall()]

    def delete_conversation(self, conversation_id: int) -> None:
        with self.connect() as connection:
            connection.execute("DELETE FROM conversations WHERE id=?", (conversation_id,))

    def create_approval(self, action_type: str, payload: str) -> int:
        with self.connect() as connection:
            cursor = connection.execute(
                "INSERT INTO approvals(action_type, payload) VALUES (?, ?)", (action_type, payload)
            )
            return int(cursor.lastrowid)

    def set_approval(self, approval_id: int, status: str, result: str | None = None) -> None:
        if status not in {"approved", "rejected", "completed", "failed"}:
            raise ValueError("invalid approval status")
        with self.connect() as connection:
            connection.execute(
                "UPDATE approvals SET status=?, decided_at=CURRENT_TIMESTAMP, result=? WHERE id=?",
                (status, result, approval_id),
            )

    def list_approvals(self, status: str | None = None) -> list[dict]:
        query, params = "SELECT * FROM approvals", ()
        if status:
            query, params = query + " WHERE status=?", (status,)
        query += " ORDER BY id DESC"
        with self.connect() as connection:
            return [dict(row) for row in connection.execute(query, params).fetchall()]

    def create_marketing_content(
        self,
        content_type: str,
        title: str,
        body: str,
        brief: str = "",
        metadata_json: str = "{}",
    ) -> int:
        if not content_type.strip() or not title.strip() or not body.strip():
            raise ValueError("Content type, title, and body are required")
        with self.connect() as connection:
            cursor = connection.execute(
                """INSERT INTO marketing_content
                   (content_type, title, body, brief, metadata_json)
                   VALUES (?, ?, ?, ?, ?)""",
                (content_type.strip(), title.strip()[:200], body.strip(), brief.strip(), metadata_json),
            )
            return int(cursor.lastrowid)

    def get_marketing_content(self, content_id: int) -> dict | None:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT * FROM marketing_content WHERE id=?", (content_id,)
            ).fetchone()
            return dict(row) if row else None

    def list_marketing_content(
        self, status: str | None = None, content_type: str | None = None, limit: int = 100
    ) -> list[dict]:
        conditions: list[str] = []
        params: list[object] = []
        if status:
            conditions.append("status=?")
            params.append(status)
        if content_type:
            conditions.append("content_type=?")
            params.append(content_type)
        query = "SELECT * FROM marketing_content"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        with self.connect() as connection:
            return [dict(row) for row in connection.execute(query, tuple(params)).fetchall()]

    def transition_marketing_content(self, content_id: int, new_status: str) -> None:
        transitions = {
            "draft": {"pending_approval"},
            "pending_approval": {"approved", "rejected"},
            "rejected": {"draft"},
            "approved": set(),
        }
        with self.connect() as connection:
            row = connection.execute(
                "SELECT status FROM marketing_content WHERE id=?", (content_id,)
            ).fetchone()
            if not row:
                raise ValueError("Marketing content was not found")
            current = str(row["status"])
            if new_status not in transitions[current]:
                raise ValueError(f"Cannot change content from {current} to {new_status}")
            reviewed = ", reviewed_at=CURRENT_TIMESTAMP" if new_status in {"approved", "rejected"} else ""
            connection.execute(
                f"UPDATE marketing_content SET status=?, updated_at=CURRENT_TIMESTAMP{reviewed} WHERE id=?",
                (new_status, content_id),
            )

    def upsert_business_profile(self, data: dict) -> None:
        import json
        with self.connect() as connection:
            connection.execute("""INSERT INTO business_profiles
              (id,name,industry,market,business_model,languages_json,timezone,brand_personality)
              VALUES (1,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name,
              industry=excluded.industry,market=excluded.market,business_model=excluded.business_model,
              languages_json=excluded.languages_json,timezone=excluded.timezone,
              brand_personality=excluded.brand_personality,updated_at=CURRENT_TIMESTAMP""",
              (data['name'], data['industry'], data['market'], data['business_model'],
               json.dumps(data['languages']), data.get('timezone','Asia/Manila'), data['brand_personality']))

    def get_business_profile(self) -> dict | None:
        with self.connect() as connection:
            row = connection.execute("SELECT * FROM business_profiles WHERE id=1").fetchone()
            return dict(row) if row else None

    def save_product(self, data: dict, product_id: int | None = None) -> int:
        import json
        values = (data['name'].strip(), data.get('category','').strip(), data.get('description','').strip(),
                  json.dumps(data.get('ingredients',[])), json.dumps(data.get('features',[])),
                  json.dumps(data.get('variants',[])), data.get('price'), data.get('currency','PHP'),
                  data.get('stock_status'), json.dumps(data.get('product_links',{})), data.get('policies'),
                  int(bool(data.get('verified',False))))
        with self.connect() as connection:
            if product_id:
                connection.execute("""UPDATE products SET name=?,category=?,description=?,ingredients_json=?,
                  features_json=?,variants_json=?,price=?,currency=?,stock_status=?,links_json=?,policies=?,verified=?,
                  updated_at=CURRENT_TIMESTAMP WHERE id=?""", values + (product_id,))
                return product_id
            cursor = connection.execute("""INSERT INTO products(name,category,description,ingredients_json,
              features_json,variants_json,price,currency,stock_status,links_json,policies,verified)
              VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""", values)
            return int(cursor.lastrowid)

    def list_products(self) -> list[dict]:
        with self.connect() as connection:
            return [dict(r) for r in connection.execute("SELECT * FROM products ORDER BY name").fetchall()]

    def create_task(self, request_text: str, skill: str, platform: str = '', product_id: int | None = None, input_json: str = '{}') -> int:
        with self.connect() as connection:
            cur = connection.execute("INSERT INTO marketing_tasks(request_text,skill,platform,product_id,input_json) VALUES (?,?,?,?,?)", (request_text,skill,platform,product_id,input_json))
            return int(cur.lastrowid)

    def finish_task(self, task_id: int, status: str, error: str | None = None) -> None:
        with self.connect() as connection:
            connection.execute("UPDATE marketing_tasks SET status=?,error=?,updated_at=CURRENT_TIMESTAMP WHERE id=?", (status,error,task_id))

    def create_generated_content(self, task_id: int, data: dict, product_id: int | None = None) -> int:
        import json
        with self.connect() as connection:
            cur = connection.execute("""INSERT INTO generated_content(task_id,platform,product_id,content_type,title,
              hook,caption,hashtags_json,call_to_action,visual_prompt,suggested_publication_date,language,structured_json)
              VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""", (task_id,data.get('platform',''),product_id,data['content_type'],
              data['title'],data.get('hook',''),data.get('caption',''),json.dumps(data.get('hashtags',[])),
              data.get('call_to_action',''),data.get('visual_prompt',''),data.get('suggested_publication_date'),
              data.get('language','English'),json.dumps(data,ensure_ascii=False)))
            cid=int(cur.lastrowid)
            connection.execute("INSERT INTO approval_history(content_id,new_status,note) VALUES (?,?,?)", (cid,'pending_approval','Generated and validated'))
            return cid

    def list_generated_content(self, status: str | None = None, platform: str | None = None, limit: int = 200) -> list[dict]:
        conditions=[]; params=[]
        if status: conditions.append('approval_status=?'); params.append(status)
        if platform: conditions.append('platform=?'); params.append(platform)
        query='SELECT * FROM generated_content' + ((' WHERE '+' AND '.join(conditions)) if conditions else '') + ' ORDER BY id DESC LIMIT ?'
        params.append(limit)
        with self.connect() as connection:
            return [dict(r) for r in connection.execute(query,tuple(params)).fetchall()]

    def transition_generated_content(self, content_id: int, new_status: str, note: str = '') -> None:
        allowed={'pending_approval':{'approved','rejected'},'rejected':{'draft'},'draft':{'pending_approval'},'approved':{'scheduled'},'scheduled':{'published'}}
        with self.connect() as connection:
            row=connection.execute('SELECT approval_status FROM generated_content WHERE id=?',(content_id,)).fetchone()
            if not row or new_status not in allowed.get(row[0],set()): raise ValueError('Invalid content status transition')
            connection.execute('UPDATE generated_content SET approval_status=?,updated_at=CURRENT_TIMESTAMP WHERE id=?',(new_status,content_id))
            connection.execute('INSERT INTO approval_history(content_id,previous_status,new_status,note) VALUES (?,?,?,?)',(content_id,row[0],new_status,note))

    def overview_counts(self) -> dict[str, int]:
        with self.connect() as connection:
            return {name: connection.execute(sql).fetchone()[0] for name,sql in {
              'products':'SELECT COUNT(*) FROM products','content':'SELECT COUNT(*) FROM generated_content',
              'pending':'SELECT COUNT(*) FROM generated_content WHERE approval_status="pending_approval"',
              'approved':'SELECT COUNT(*) FROM generated_content WHERE approval_status="approved"',
              'campaigns':'SELECT COUNT(*) FROM campaigns','calendar_entries':'SELECT COUNT(*) FROM calendar_entries'}.items()}

    def update_generated_content(self, content_id: int, title: str, caption: str) -> None:
        with self.connect() as connection:
            row=connection.execute('SELECT approval_status FROM generated_content WHERE id=?',(content_id,)).fetchone()
            if not row or row[0] not in {'draft','pending_approval','rejected'}: raise ValueError('Only unapproved content can be edited')
            connection.execute('UPDATE generated_content SET title=?,caption=?,updated_at=CURRENT_TIMESTAMP WHERE id=?',(title.strip(),caption.strip(),content_id))

    def list_metrics(self) -> list[dict]:
        with self.connect() as connection:
            return [dict(r) for r in connection.execute('SELECT * FROM marketing_metrics ORDER BY metric_date DESC,id DESC').fetchall()]

    def add_metric(self, data: dict) -> int:
        with self.connect() as connection:
            cur=connection.execute('''INSERT INTO marketing_metrics(metric_date,platform,followers,reach,impressions,
              engagements,clicks,inquiries,orders,sales,source) VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
              (data['metric_date'],data['platform'],data.get('followers'),data.get('reach'),data.get('impressions'),
               data.get('engagements'),data.get('clicks'),data.get('inquiries'),data.get('orders'),data.get('sales'),'manual'))
            return int(cur.lastrowid)

    def create_calendar(self, name: str, start_date: str, duration_days: int, entries: list[dict], content_id: int | None = None) -> int:
        import json
        from datetime import date, timedelta
        end_date=(date.fromisoformat(start_date)+timedelta(days=duration_days-1)).isoformat()
        with self.connect() as connection:
            cur=connection.execute('INSERT INTO content_calendars(name,duration_days,start_date,end_date) VALUES (?,?,?,?)',(name,duration_days,start_date,end_date))
            calendar_id=int(cur.lastrowid)
            for entry in entries:
                connection.execute('''INSERT INTO calendar_entries(calendar_id,content_id,publication_date,platform,objective,
                  content_type,hook,caption,hashtags_json,call_to_action,visual_concept) VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
                  (calendar_id,content_id,entry['date'],entry['platform'],entry['objective'],entry['content_type'],entry['hook'],
                   entry['caption'],json.dumps(entry['hashtags']),entry['call_to_action'],entry['visual_concept']))
            return calendar_id

    def list_calendar_entries(self, platform: str | None = None, status: str | None = None) -> list[dict]:
        conditions=[]; params=[]
        if platform: conditions.append('platform=?'); params.append(platform)
        if status: conditions.append('approval_status=?'); params.append(status)
        query='SELECT * FROM calendar_entries'+((' WHERE '+' AND '.join(conditions)) if conditions else '')+' ORDER BY publication_date,id'
        with self.connect() as connection:
            return [dict(r) for r in connection.execute(query,tuple(params)).fetchall()]

