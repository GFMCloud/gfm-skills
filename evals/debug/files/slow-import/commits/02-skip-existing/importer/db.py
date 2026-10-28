"""SQLite storage."""
import logging
import sqlite3

log = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY,
    email TEXT NOT NULL,
    name TEXT NOT NULL,
    town TEXT,
    joined TEXT
);
CREATE INDEX IF NOT EXISTS customers_email ON customers (email);
"""


def connect(path):
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    return conn


def exists(conn, email):
    """True if this email is already stored, ignoring case (the CRM mixes cases)."""
    row = conn.execute(
        "SELECT 1 FROM customers WHERE lower(email) = lower(?) LIMIT 1", (email,)
    ).fetchone()
    return row is not None


def insert(conn, rec):
    log.debug("insert %s", rec["email"])
    conn.execute(
        "INSERT INTO customers (email, name, town, joined) VALUES (?, ?, ?, ?)",
        (rec["email"], rec["name"], rec["town"], rec["joined"]),
    )
