"""Row checks. Returns a reason string, or None when the row is fine."""


def problem(rec):
    if not rec["email"]:
        return "no email"
    if not rec["name"]:
        return "no name"
    return None
