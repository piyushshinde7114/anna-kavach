"""SQLite storage (MVP). The schema maps 1:1 to PostgreSQL for the pilot."""
import json
import os
import sqlite3
import threading
import time
import secrets
from .data import seed

DB_PATH = os.environ.get("ANNAKAVACH_DB", os.path.join(os.path.dirname(__file__), "..", "annakavach.db"))
_lock = threading.Lock()

SCHEMA = """
CREATE TABLE IF NOT EXISTS films (id TEXT PRIMARY KEY, data TEXT NOT NULL, updated REAL);
CREATE TABLE IF NOT EXISTS foods (id TEXT PRIMARY KEY, data TEXT NOT NULL, updated REAL);
CREATE TABLE IF NOT EXISTS projects (id TEXT PRIMARY KEY, created REAL, title TEXT, food_id TEXT, kind TEXT,
    input TEXT, result TEXT, trace_code TEXT UNIQUE);
CREATE TABLE IF NOT EXISTS batches (id INTEGER PRIMARY KEY AUTOINCREMENT, project_id TEXT, lot TEXT, packed_on TEXT,
    quantity INTEGER, created REAL);
CREATE TABLE IF NOT EXISTS feedback (id INTEGER PRIMARY KEY AUTOINCREMENT, project_id TEXT, food_id TEXT, structure TEXT,
    predicted_days REAL, observed_days REAL, outcome TEXT, notes TEXT, created REAL);
CREATE TABLE IF NOT EXISTS climate_cache (city TEXT PRIMARY KEY, data TEXT, source TEXT, fetched REAL);
"""


def conn():
    c = sqlite3.connect(DB_PATH, check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c


def init():
    with _lock, conn() as c:
        c.executescript(SCHEMA)
        if c.execute("SELECT COUNT(*) FROM films").fetchone()[0] == 0:
            c.executemany("INSERT INTO films VALUES (?,?,?)", [(f["id"], json.dumps(f), time.time()) for f in seed.FILMS])
        if c.execute("SELECT COUNT(*) FROM foods").fetchone()[0] == 0:
            c.executemany("INSERT INTO foods VALUES (?,?,?)", [(f["id"], json.dumps(f, ensure_ascii=False), time.time()) for f in seed.FOODS])


def films():
    with conn() as c:
        return {r["id"]: json.loads(r["data"]) for r in c.execute("SELECT * FROM films")}


def foods():
    with conn() as c:
        return [json.loads(r["data"]) for r in c.execute("SELECT * FROM foods")]


def put(table, id, data):
    with _lock, conn() as c:
        c.execute(f"INSERT OR REPLACE INTO {table} VALUES (?,?,?)", (id, json.dumps(data, ensure_ascii=False), time.time()))


def save_project(title, food_id, kind, inp, result):
    pid = secrets.token_hex(4)
    code = "AK-" + secrets.token_hex(3).upper()
    with _lock, conn() as c:
        c.execute("INSERT INTO projects VALUES (?,?,?,?,?,?,?,?)",
                  (pid, time.time(), title, food_id, kind, json.dumps(inp, ensure_ascii=False), json.dumps(result, ensure_ascii=False), code))
    return pid, code


def get_project(pid=None, code=None):
    with conn() as c:
        r = c.execute("SELECT * FROM projects WHERE id=? OR trace_code=?", (pid, code)).fetchone()
    if not r:
        return None
    d = dict(r)
    d["input"], d["result"] = json.loads(d["input"]), json.loads(d["result"])
    return d


def list_projects(limit=50):
    with conn() as c:
        rows = c.execute("SELECT id, created, title, food_id, kind, trace_code FROM projects ORDER BY created DESC LIMIT ?", (limit,))
        return [dict(r) for r in rows]


def delete_project(pid):
    with _lock, conn() as c:
        c.execute("DELETE FROM projects WHERE id=?", (pid,))


def add_batch(pid, lot, packed_on, qty):
    with _lock, conn() as c:
        c.execute("INSERT INTO batches (project_id, lot, packed_on, quantity, created) VALUES (?,?,?,?,?)", (pid, lot, packed_on, qty, time.time()))


def batches(pid):
    with conn() as c:
        return [dict(r) for r in c.execute("SELECT * FROM batches WHERE project_id=? ORDER BY created DESC", (pid,))]


def add_feedback(pid, food_id, structure, predicted, observed, outcome, notes):
    with _lock, conn() as c:
        c.execute("INSERT INTO feedback (project_id, food_id, structure, predicted_days, observed_days, outcome, notes, created) VALUES (?,?,?,?,?,?,?,?)",
                  (pid, food_id, structure, predicted, observed, outcome, notes, time.time()))


def feedback(food_id=None, pid=None):
    q, a = "SELECT * FROM feedback WHERE 1=1", []
    if food_id:
        q += " AND food_id=?"; a.append(food_id)
    if pid:
        q += " AND project_id=?"; a.append(pid)
    with conn() as c:
        return [dict(r) for r in c.execute(q + " ORDER BY created DESC", a)]


def calibration(food_id, prior_n=3):
    """Shrunk geometric-mean correction factor from field reports: k = exp(sum(ln(obs/pred)) / (n + prior_n))."""
    import math
    rows = [r for r in feedback(food_id) if r["predicted_days"] and r["observed_days"]]
    if not rows:
        return dict(factor=1.0, n=0)
    s = sum(math.log(max(r["observed_days"], 1) / max(r["predicted_days"], 1)) for r in rows)
    return dict(factor=round(math.exp(s / (len(rows) + prior_n)), 3), n=len(rows))


def climate_get(city):
    with conn() as c:
        r = c.execute("SELECT * FROM climate_cache WHERE city=?", (city,)).fetchone()
    return (json.loads(r["data"]), r["source"]) if r else (None, None)


def climate_put(city, data, source):
    with _lock, conn() as c:
        c.execute("INSERT OR REPLACE INTO climate_cache VALUES (?,?,?,?)", (city, json.dumps(data), source, time.time()))
