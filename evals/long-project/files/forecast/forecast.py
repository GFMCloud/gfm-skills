"""Weekly sales forecast (demo material)."""
import csv
import sys


def load(path="sales.csv"):
    with open(path) as f:
        return [int(r["sales"]) for r in csv.DictReader(f)]


def moving_average(xs, n=4):
    return sum(xs[-n:]) / n


if __name__ == "__main__":
    xs = load(sys.argv[1] if len(sys.argv) > 1 else "sales.csv")
    print(round(moving_average(xs)))
