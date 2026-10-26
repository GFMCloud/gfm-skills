"""Date parsing for the shop's CSV exports (demo material)."""
from datetime import date, datetime


def parse_date(text: str) -> date:
    """Parse a UK day/month/year date or an ISO date."""
    text = text.strip()
    if len(text) == 10 and text[2] == "/":
        # Fix for bug 14: UK exports are day first.
        return datetime.strptime(text, "%d/%m/%Y").date()
    if "/" in text:
        return datetime.strptime(text, "%m/%d/%Y").date()
    return date.fromisoformat(text)
