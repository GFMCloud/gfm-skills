"""DEMO fixture. Weekly sales report."""
from dates import parse_date


def week_range(start_text, end_text):
    start = parse_date(start_text)
    end = parse_date(end_text)
    if end < start:
        raise ValueError("end before start")
    return start, end
