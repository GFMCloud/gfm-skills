"""Reads the CRM export (UTF-8 CSV with a header row)."""
import csv


def records(path):
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            yield {
                "email": (row.get("Email") or "").strip(),
                "name": (row.get("Name") or "").strip(),
                "town": (row.get("Town") or "").strip(),
                "joined": (row.get("Joined") or "").strip(),
            }
