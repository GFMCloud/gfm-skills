# order-export (DEMO)

Demo project for a debugging eval. Orders, emails and totals are invented.

Nightly job: reads `data/orders.jsonl` (the shop feed) and writes the orders to send to the
accounts team as CSV.

    python3 export_orders.py --out out/orders.csv

Settings are in `config.ini`. Tests: `python3 -m unittest discover -s tests -t .`
