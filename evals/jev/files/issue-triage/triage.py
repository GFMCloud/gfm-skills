"""Label new issues with keyword rules (demo project)."""
import json
import sys

RULES = [
    ("docs", ["typo", "documentation", "docs", "readme", "example in"]),
    ("bug", ["error", "crash", "traceback", "wrong", "broken", "fails"]),
    ("feature", ["add", "support", "would be nice", "feature", "option to"]),
]


def label(issue):
    text = (issue["title"] + " " + issue["body"]).lower()
    for name, words in RULES:
        if any(w in text for w in words):
            return name
    return "question"


if __name__ == "__main__":
    for line in sys.stdin:
        issue = json.loads(line)
        print(issue["number"], label(issue))
