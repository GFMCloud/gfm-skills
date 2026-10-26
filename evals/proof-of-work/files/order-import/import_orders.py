"""Import the daily orders export into imported.csv (demo material)."""
import csv
from datetime import date


def main():
    kept = []
    with open("orders.csv", newline="") as f:
        for row in csv.DictReader(f):
            try:
                row["date"] = date.fromisoformat(row["date"]).isoformat()
            except ValueError:
                continue
            kept.append(row)
    with open("imported.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["order_id", "date", "customer", "total"])
        w.writeheader()
        w.writerows(kept)
    print("Import complete. Success!")


if __name__ == "__main__":
    main()
