"""Flag urgent support emails with keyword rules (demo project)."""
import json
import sys

URGENT = ["refund", "charged twice", "not arrived", "broken", "cancel", "complaint", "asap"]


def urgency(mail):
    text = (mail["subject"] + " " + mail["body"]).lower()
    return "urgent" if any(w in text for w in URGENT) else "normal"


if __name__ == "__main__":
    for line in sys.stdin:
        m = json.loads(line)
        print(m["id"], urgency(m))
