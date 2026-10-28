"""SQLite storage."""
import sqlite3

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


def insert(conn, rec):
    conn.execute(
        "INSERT INTO customers (email, name, town, joined) VALUES (?, ?, ?, ?)",
        (rec["email"], rec["name"], rec["town"], rec["joined"]),
    )
