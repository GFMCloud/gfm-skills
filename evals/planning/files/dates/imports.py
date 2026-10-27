"""DEMO fixture. Reads the till's nightly export (orders.csv) into order records."""
import csv

from dates import parse_date


def load_orders(path):
    with open(path, newline="") as f:
        return [
            {"id": row["order_id"], "day": parse_date(row["date"]), "total": float(row["total"])}
            for row in csv.DictReader(f)
        ]
