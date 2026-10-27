"""Invoice export (demo material for a skill trial)."""
import csv
import json


def load(path):
    with open(path) as f:
        return json.load(f)


def total(inv):
    return sum(line["qty"] * line["price"] for line in inv["lines"])


def export(invoices, path):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["number", "customer", "total"])
        for inv in invoices:
            w.writerow([inv["number"], inv["customer"], f"{total(inv):.2f}"])


def main():
    export(load("invoices.json"), "build/export.csv")
