import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from .models import Settings


def now():
    return datetime.now(timezone.utc).isoformat()


def new_id():
    return uuid.uuid4().hex


JSON_FIELDS = {"zones", "metadata", "config", "metrics", "payload", "details"}


def decode(row):
    if row is None:
        return None
    result = dict(row)
    for key in JSON_FIELDS & result.keys():
        result[key] = json.loads(result[key])
    return result


class Store:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        for name in ("uploads", "sources", "jobs", "backups"):
            (self.root/name).mkdir(exist_ok=True)
        self.path = self.root/"curb.sqlite3"
        with self.connect() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.executescript("""
            CREATE TABLE IF NOT EXISTS sources (
              id TEXT PRIMARY KEY, name TEXT NOT NULL, kind TEXT NOT NULL,
              uri TEXT NOT NULL, location TEXT NOT NULL DEFAULT '', notes TEXT NOT NULL DEFAULT '',
              zones TEXT NOT NULL DEFAULT '[]', metadata TEXT NOT NULL DEFAULT '{}',
              archived INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS jobs (
              id TEXT PRIMARY KEY, source_id TEXT NOT NULL REFERENCES sources(id),
              source_name TEXT NOT NULL, status TEXT NOT NULL, config TEXT NOT NULL,
              progress REAL NOT NULL DEFAULT 0, frames INTEGER NOT NULL DEFAULT 0,
              source_seconds REAL NOT NULL DEFAULT 0, fps REAL NOT NULL DEFAULT 0,
              event_count INTEGER NOT NULL DEFAULT 0, error TEXT NOT NULL DEFAULT '',
              metrics TEXT NOT NULL DEFAULT '{}', created_at TEXT NOT NULL,
              started_at TEXT, finished_at TEXT, updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS events (
              id TEXT PRIMARY KEY, job_id TEXT NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
              source_id TEXT NOT NULL REFERENCES sources(id), source_name TEXT NOT NULL,
              zone_name TEXT NOT NULL, class_name TEXT NOT NULL, severity TEXT NOT NULL,
              status TEXT NOT NULL DEFAULT 'pending', version INTEGER NOT NULL DEFAULT 0,
              payload TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS reviews (
              id INTEGER PRIMARY KEY AUTOINCREMENT, event_id TEXT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
              status TEXT NOT NULL, note TEXT NOT NULL, operator TEXT NOT NULL, created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS settings (id INTEGER PRIMARY KEY CHECK(id=1), value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS audit (
              id INTEGER PRIMARY KEY AUTOINCREMENT, action TEXT NOT NULL, subject TEXT NOT NULL,
              details TEXT NOT NULL, created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS event_status_time ON events(status, created_at DESC);
            CREATE INDEX IF NOT EXISTS event_job ON events(job_id);
            CREATE INDEX IF NOT EXISTS job_status_time ON jobs(status, created_at);
            PRAGMA user_version=1;
            """)
            db.execute("INSERT OR IGNORE INTO settings VALUES(1,?)", (Settings().model_dump_json(),))

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        try:
            with db:
                yield db
        finally:
            db.close()

    def all(self, sql, params=()):
        with self.connect() as db:
            return [decode(r) for r in db.execute(sql, params).fetchall()]

    def one(self, sql, params=()):
        with self.connect() as db:
            return decode(db.execute(sql, params).fetchone())

    def execute(self, sql, params=()):
        with self.connect() as db:
            return db.execute(sql, params).rowcount

    def settings(self):
        return Settings.model_validate_json(self.one("SELECT value FROM settings WHERE id=1")["value"])

    def audit(self, action, subject, details=None):
        self.execute("INSERT INTO audit(action,subject,details,created_at) VALUES(?,?,?,?)", (action,subject,json.dumps(details or {},ensure_ascii=False),now()))

    def add_source(self, name, kind, uri, location="", notes="", metadata=None, zones=None, source_id=None):
        sid, stamp = source_id or new_id(), now()
        self.execute("INSERT INTO sources(id,name,kind,uri,location,notes,metadata,zones,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?)", (sid,name,kind,str(uri),location,notes,json.dumps(metadata or {}),json.dumps(zones or []),stamp,stamp))
        self.audit("source.created",sid,{"kind":kind,"name":name})
        return self.source(sid)

    def source(self, sid):
        return self.one("SELECT * FROM sources WHERE id=?",(sid,))

    def job(self, jid):
        return self.one("SELECT * FROM jobs WHERE id=?",(jid,))

    def update_job(self, jid, **fields):
        allowed = {"status","progress","frames","source_seconds","fps","event_count","error","metrics","started_at","finished_at"}
        if not fields.keys() <= allowed:
            raise ValueError("Unknown job fields")
        fields["updated_at"] = now()
        if "metrics" in fields:
            fields["metrics"] = json.dumps(fields["metrics"],ensure_ascii=False)
        self.execute("UPDATE jobs SET "+",".join(f"{k}=?" for k in fields)+" WHERE id=?",(*fields.values(),jid))

    def add_event(self, job, payload):
        eid, stamp = new_id(), now()
        payload = {**payload,"id":eid}
        self.execute("INSERT INTO events(id,job_id,source_id,source_name,zone_name,class_name,severity,payload,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?)",(eid,job["id"],job["source_id"],job["source_name"],payload["zone_name"],payload["class_name"],payload["severity"],json.dumps(payload),stamp,stamp))
        return payload

    def public_source(self, source):
        result = {k:v for k,v in source.items() if k != "uri"}
        result["archived"] = bool(result["archived"])
        result["connection"] = "Video đã nhập" if result["kind"] == "video" else "Camera đã cấu hình · địa chỉ được giữ kín"
        result["has_preview"] = bool(result["metadata"].get("width")) and (self.root/"sources"/result["id"]/"preview.jpg").is_file()
        return result
