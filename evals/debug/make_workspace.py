"""Builds a fresh DEMO workspace for one debug eval case.

    python3 evals/debug/make_workspace.py <case> <dest-folder>

Cases with a history.json get a git repo whose commits are replayed from base/ and commits/*
overlays (author Demo Dev). Data files are generated here with fixed seeds so the
repo stays small. Commit dates are set relative to the build time (history.json "ago"), so
prompts like "since yesterday" and "after my last commit" stay true on any day; the refund log's bearer token is built at run time so no key-shaped string is
ever committed. Everything written is invented demo material.
"""
import json
import os
from datetime import datetime, timedelta
import random
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FILES = os.path.join(HERE, "files")

TOWNS = ["Ashby", "Brill", "Cove", "Dunmore", "Elmsted", "Fairlop", "Gorran", "Hythe"]
FIRST = ["Ann", "Bo", "Cy", "Dee", "Eli", "Fay", "Gus", "Hal", "Ivy", "Jo", "Kit", "Lu"]
LAST = ["Ash", "Birch", "Cole", "Dale", "Eden", "Frost", "Grey", "Hale", "Ince", "Jory"]


def copy_tree(src, dest):
    for root, _dirs, files in os.walk(src):
        rel = os.path.relpath(root, src)
        os.makedirs(os.path.join(dest, rel), exist_ok=True)
        for name in files:
            shutil.copy2(os.path.join(root, name), os.path.join(dest, rel, name))


def gen_orders(dest):
    rng = random.Random(7)
    path = os.path.join(dest, "data", "orders.jsonl")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        for n in range(1, 301):
            month, day = rng.choice([(8, rng.randint(1, 31)), (9, rng.randint(1, 30)), (10, rng.randint(1, 25))])
            rec = {
                "Order ID": f"A-{1000 + n}",
                "Status": rng.choice(["paid"] * 5 + ["shipped"] * 3 + ["cancelled", "refunded"]),
                "Created At": f"2026-{month:02d}-{day:02d}T{rng.randint(0, 23):02d}:{rng.randint(0, 59):02d}:00Z",
                "Customer Email": f"{rng.choice(FIRST)}.{rng.choice(LAST)}{n}@Example.com",
                "Total": f"{rng.randint(3, 1400)}.{rng.randint(0, 99):02d}",
            }
            if n % 37 == 0:
                rec["Test Order"] = True
            f.write(json.dumps(rec) + "\n")


def gen_customers(dest):
    rng = random.Random(11)
    path = os.path.join(dest, "data", "customers.csv")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    emails = []
    with open(path, "w", newline="") as f:
        f.write("Email,Name,Town,Joined\n")
        for n in range(1, 24001):
            if n % 50 == 0 and emails:
                email = rng.choice(emails).upper()  # same customer, different case
            elif n % 333 == 0:
                email = f"broken-address-{n}"
            else:
                email = f"{rng.choice(FIRST).lower()}.{rng.choice(LAST).lower()}{n}@example.org"
                emails.append(email)
            name = f"{rng.choice(FIRST)} {rng.choice(LAST)}"
            f.write(f"{email},{name},{rng.choice(TOWNS)},2025-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}\n")


def gen_refund_log(dest):
    rng = random.Random(5)
    token = "sk_" + "live_" + "".join(rng.choice("abcdef0123456789") for _ in range(32))
    lines = ["# DEMO: invented capture from the production web server, 2026-10-16 to 2026-10-23",
             "# Format: time status method path | headers | body"]
    n = 0
    entries = []
    for day in range(16, 24):
        new_api = day >= 20  # provider moved accounts to the new API version on Tuesday 2026-10-20
        for _ in range(6):
            n += 1
            hour, minute = rng.randint(7, 22), rng.randint(0, 59)
            kind = rng.choice(["payment.succeeded"] * 4 + ["refund.created", "payment.failed"])
            amount = round(rng.uniform(2, 180), 2)
            if kind == "refund.created" and new_api:
                amount = f"{amount:.2f}"
            data = {"order": f"O-{4000 + n}", "customer": f"cust{n}@example.net"}
            if kind != "payment.failed":
                data["amount"] = amount
            body = {"id": f"ev_{n:04d}", "type": kind, "data": data}
            status = 200
            if kind == "refund.created" and new_api:
                status = 500
            elif rng.random() < 0.06:
                status = 401
            sig = "".join(rng.choice("abcdef0123456789") for _ in range(64))
            version = "2026-10-20" if new_api else "2026-06-01"
            entries.append(
                f"2026-10-{day:02d}T{hour:02d}:{minute:02d}:00Z {status} POST /hooks/payment | "
                f"Authorization: Bearer {token}; X-Signature: {sig}; X-Api-Version: {version} | "
                + json.dumps(body)
            )
    lines += sorted(entries)
    path = os.path.join(dest, "incident", "prod-requests.log")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")


GENERATORS = {"orders": gen_orders, "customers": gen_customers}


def git(dest, *args, env=None):
    subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "-c", "commit.gpgsign=false", *args],
                   cwd=dest, check=True, stdout=subprocess.DEVNULL, env=env)


def commit_date(ago, now):
    if "minutes" in ago:
        return (now - timedelta(minutes=ago["minutes"])).strftime("%Y-%m-%dT%H:%M:%S")
    day = (now - timedelta(days=ago["days"])).strftime("%Y-%m-%d")
    return f"{day}T{ago['time']}:00"


def build_history(case_dir, dest, spec):
    now = datetime.now()
    name, email = spec["author"].rsplit(" <", 1)
    email = email.rstrip(">")
    git(dest, "init", "-q", "-b", "main")
    for i, c in enumerate(spec["commits"]):
        copy_tree(os.path.join(case_dir, c["dir"]), dest)
        if i == 0 and spec.get("generate"):
            GENERATORS[spec["generate"]](dest)
        env = dict(os.environ, GIT_AUTHOR_NAME=name, GIT_AUTHOR_EMAIL=email, GIT_COMMITTER_NAME=name,
                   GIT_COMMITTER_EMAIL=email, GIT_AUTHOR_DATE=commit_date(c["ago"], now),
                   GIT_COMMITTER_DATE=commit_date(c["ago"], now))
        git(dest, "add", "-A")
        git(dest, "commit", "-q", "-m", c["msg"], env=env)


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    case, dest = sys.argv[1], os.path.abspath(sys.argv[2])
    case_dir = os.path.join(FILES, case)
    if not os.path.isdir(case_dir):
        sys.exit(f"no such case: {case}")
    if os.path.exists(dest) and os.listdir(dest):
        sys.exit(f"{dest} is not empty")
    os.makedirs(dest, exist_ok=True)
    hist = os.path.join(case_dir, "history.json")
    if os.path.exists(hist):
        with open(hist) as f:
            build_history(case_dir, dest, json.load(f))
    else:
        copy_tree(case_dir, dest)
    if case == "refund-500":
        gen_refund_log(dest)
    print(f"DEMO workspace for {case}: {dest}")


if __name__ == "__main__":
    main()
