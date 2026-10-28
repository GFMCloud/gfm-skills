"""DEMO FIXTURE for the grill skill evals: emails last week's scores. Not a real script."""
import sqlite3

def last_week(conn):
    return conn.execute(
        "SELECT player, SUM(points) FROM scores WHERE played_on >= date('now', '-7 days') GROUP BY player"
    ).fetchall()

def main():
    conn = sqlite3.connect("scores.db")
    rows = last_week(conn)
    body = "\n".join(f"{p}: {s}" for p, s in rows)
    print(body)  # the real version would email this

if __name__ == "__main__":
    main()
