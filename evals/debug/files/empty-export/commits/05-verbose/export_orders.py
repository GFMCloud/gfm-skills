"""Export orders from the shop feed to CSV for the accounts team."""
import argparse
import sys

from exporter import config, filters, load, transform, write_csv


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--feed", default="data/orders.jsonl")
    p.add_argument("--config", default="config.ini")
    p.add_argument("--out", default="out/orders.csv")
    p.add_argument("--verbose", action="store_true", help="print row counts to stderr")
    args = p.parse_args(argv)

    cfg = config.read(args.config)
    rows = load.read_feed(args.feed)
    kept = [r for r in rows if filters.keep(r, cfg.statuses, cfg.since)]
    out_rows = [transform.to_export(r) for r in kept]
    write_csv.write(args.out, cfg.columns, out_rows)
    if args.verbose:
        print(f"wrote {len(out_rows)} rows to {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
