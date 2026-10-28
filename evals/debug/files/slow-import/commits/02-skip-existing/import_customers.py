"""Load the CRM customer export into SQLite."""
import argparse
import logging
import os
import sys

from importer import db, read, validate


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("csv")
    p.add_argument("--db", default="out/customers.db")
    p.add_argument("--debug", action="store_true")
    args = p.parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.WARNING)

    os.makedirs(os.path.dirname(args.db) or ".", exist_ok=True)
    conn = db.connect(args.db)
    added = skipped = dupes = 0
    for rec in read.records(args.csv):
        problem = validate.problem(rec)
        if problem:
            skipped += 1
            continue
        if db.exists(conn, rec["email"]):
            dupes += 1
            continue
        db.insert(conn, rec)
        added += 1
    conn.commit()
    print(f"added {added}, skipped {skipped}, already there {dupes}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
