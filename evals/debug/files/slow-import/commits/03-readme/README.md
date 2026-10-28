# customer-import (DEMO)

Demo project for a debugging eval. Every name and email is invented.

Loads the CRM export (`data/customers.csv`) into a SQLite database. Customers already in the
database (same email, any case) are skipped, so the import can be rerun safely.

    python3 import_customers.py data/customers.csv --db out/customers.db

Tests: `python3 -m unittest discover -s tests -t .`
