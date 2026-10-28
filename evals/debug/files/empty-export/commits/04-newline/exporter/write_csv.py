"""Writes the export file."""
import csv
import os


def write(path, columns, rows):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    # newline="" stops the csv module writing blank lines between rows on Windows.
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
