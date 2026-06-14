import sqlite3
from datetime import date, timedelta
from contextlib import contextmanager

DB_PATH = "rankings.db"


def init_db():
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS rankings (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                platform    TEXT NOT NULL,
                category    TEXT NOT NULL,
                country     TEXT NOT NULL,
                rank        INTEGER NOT NULL,
                app_id      TEXT NOT NULL,
                app_name    TEXT NOT NULL,
                developer   TEXT,
                icon_url    TEXT,
                fetch_date  TEXT NOT NULL
            )
        """)
        c.execute("""
            CREATE INDEX IF NOT EXISTS idx_fetch
            ON rankings(fetch_date, platform, category, country)
        """)


@contextmanager
def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def save_rankings(platform, category, country, apps, fetch_date=None):
    if fetch_date is None:
        fetch_date = str(date.today())
    with _conn() as c:
        c.execute(
            "DELETE FROM rankings WHERE platform=? AND category=? AND country=? AND fetch_date=?",
            (platform, category, country, fetch_date),
        )
        c.executemany(
            """INSERT INTO rankings
               (platform, category, country, rank, app_id, app_name, developer, icon_url, fetch_date)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            [
                (
                    platform, category, country, i + 1,
                    a["app_id"], a["app_name"],
                    a.get("developer", ""), a.get("icon_url", ""),
                    fetch_date,
                )
                for i, a in enumerate(apps)
            ],
        )


def get_rankings(platform, category, country, fetch_date=None):
    if fetch_date is None:
        fetch_date = str(date.today())
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM rankings WHERE platform=? AND category=? AND country=? AND fetch_date=? ORDER BY rank",
            (platform, category, country, fetch_date),
        ).fetchall()
        return [dict(r) for r in rows]


def get_prev_rankings(platform, category, country):
    yesterday = str(date.today() - timedelta(days=1))
    return get_rankings(platform, category, country, yesterday)


def last_fetch_date(platform, category, country):
    with _conn() as c:
        row = c.execute(
            "SELECT MAX(fetch_date) as d FROM rankings WHERE platform=? AND category=? AND country=?",
            (platform, category, country),
        ).fetchone()
        return row["d"] if row else None
