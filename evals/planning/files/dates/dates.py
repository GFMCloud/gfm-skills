"""DEMO fixture for the planning skill evals: date parsing for a made-up shop's tools."""
from datetime import date, datetime

FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%d %b %Y")


def parse_date(text):
    """Parse a date written in any of FORMATS."""
    for fmt in FORMATS:
        try:
            return datetime.strptime(text.strip(), fmt).date()
        except ValueError:
            pass
    raise ValueError(f"unrecognised date: {text!r}")
