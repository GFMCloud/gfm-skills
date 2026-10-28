"""DEMO FIXTURE: invented invoicing script, for skill trials only."""
import csv
import sys


def totals(path):
    with open(path) as f:
        rows = list(csv.DictReader(f))
    return sum(float(r["hours"]) * float(r["rate"]) for r in rows)


if __name__ == "__main__":
    print(f"Total to invoice: {totals(sys.argv[1]):.2f}")
