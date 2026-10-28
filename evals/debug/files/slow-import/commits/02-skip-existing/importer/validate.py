"""Row checks. Returns a reason string, or None when the row is fine."""
import logging
import re

log = logging.getLogger(__name__)
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[a-z]{2,}$", re.IGNORECASE)


def problem(rec):
    if not rec["email"]:
        return "no email"
    if not EMAIL.match(rec["email"]):
        log.debug("bad email %r", rec["email"])
        return "bad email"
    if not rec["name"]:
        return "no name"
    return None
