"""Classify merged PRs as user-facing and write release notes (demo project)."""
import csv
import anthropic

client = anthropic.Anthropic()

LABEL_PROMPT = """Is this pull request user-facing (it changes behaviour, output, the public API
or the docs a user reads)? Internal refactors, CI, tests and dev tooling are not.
Title: {title}
Description: {body}
Changed files: {files}
Answer only yes or no."""


def is_user_facing(pr):
    msg = client.messages.create(model="<model>", max_tokens=5, messages=[{"role": "user",
        "content": LABEL_PROMPT.format(**pr)}])
    return msg.content[0].text.strip().lower().startswith("yes")


def write_notes(prs):
    listing = "\n".join(f"- {p['title']}: {p['body']}" for p in prs)
    msg = client.messages.create(model="<model>", max_tokens=1500, messages=[{"role": "user",
        "content": "Write friendly release notes grouped by theme from these changes:\n" + listing}])
    return msg.content[0].text


if __name__ == "__main__":
    prs = list(csv.DictReader(open("data/merged_prs.csv")))
    facing = [p for p in prs if is_user_facing(p)]
    print(write_notes(facing))
