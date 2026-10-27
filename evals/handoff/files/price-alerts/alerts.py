"""Price alerts (demo material for a skill trial). Prints items whose price dropped."""
import csv
import sys


def load(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def drops(rows):
    return [r for r in rows if float(r["today"]) < float(r["yesterday"])]


if __name__ == "__main__":
    for r in drops(load(sys.argv[1] if len(sys.argv) > 1 else "prices.csv")):
        print(f"{r['item']}: {r['yesterday']} -> {r['today']}")
