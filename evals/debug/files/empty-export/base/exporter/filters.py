"""Which feed rows go to accounts."""
from . import dates


def keep(row, statuses, since):
    if row.get("Status") not in statuses:
        return False
    if row.get("Test Order"):
        return False
    return dates.on_or_after(row.get("Created At"), since)
