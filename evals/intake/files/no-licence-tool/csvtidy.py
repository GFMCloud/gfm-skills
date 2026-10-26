"""Trim whitespace in every cell and drop duplicate rows. Demo material for an eval."""
import csv
import sys


def tidy(rows):
    seen = set()
    for row in rows:
        clean = tuple(cell.strip() for cell in row)
        if clean not in seen:
            seen.add(clean)
            yield clean


if __name__ == "__main__":
    with open(sys.argv[1], newline="") as f:
        csv.writer(sys.stdout).writerows(tidy(csv.reader(f)))
