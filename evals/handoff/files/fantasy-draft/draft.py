"""Draft helper (demo material for a skill trial). Ranks players for the next pick."""
import csv
from config import LEAGUE, OWNER_EMAIL, ROSTER_FILE


def ranked(path):
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    return sorted(rows, key=lambda r: float(r["points"]), reverse=True)


if __name__ == "__main__":
    print(f"League: {LEAGUE} (owner {OWNER_EMAIL})")
    for r in ranked(ROSTER_FILE)[:3]:
        print(r["player"], r["points"])
