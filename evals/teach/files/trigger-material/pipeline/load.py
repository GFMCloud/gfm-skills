"""DEMO FIXTURE"""
import json

from ingest import read
from transform import clean, total

rows = clean(read("orders.csv"))
json.dump({"orders": len(rows), "total": total(rows)}, open("daily.json", "w"))
