# evaluate.py: run questions.judge over items with known answers and report agreement.
#
#   python3 evaluate.py split                 # set sizes and ids; no API call
#   python3 evaluate.py tuning --dry-run      # build every state, print sizes and one sample; no call
#   python3 evaluate.py tuning                # iterate on this set
#   python3 evaluate.py tuning --trials 3     # same items three times, to see run-to-run noise
#   python3 evaluate.py heldout               # once, after the questions are settled
#
# Known answers are someone's past decisions, not ground truth, so this reports AGREEMENT,
# never accuracy. Replace load_items() with the project's own loader; leave the split alone.
import hashlib
import json
import os
import statistics
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import questions as q

# From the provider's pricing page, dated. Input tokens are what is billed.
PRICE_PER_M_INPUT = None  # e.g. 0.0 -> fill in: USD per million input tokens, checked <DATE> at <URL>
SPEND_CEILING_USD = 1.00  # per run of this script; it stops once spend reaches this. Agree it with the user
HELDOUT_SHARE = 0.4       # share of items held out; the split is by a hash of each id, so it never moves


def load_items():
    """Return [{"id": str, "expected": <route the past decision corresponds to>, ...evidence}].
    Build the evidence here, in full, as it stood when each past decision was made.
    Leave out every item whose text appears as an example in QUESTIONS' criteria."""
    raise NotImplementedError("write load_items() for this project's labelled items")


def which_set(item_id):
    h = int(hashlib.sha256(str(item_id).encode()).hexdigest()[:8], 16) / 0xFFFFFFFF
    return "heldout" if h < HELDOUT_SHARE else "tuning"


def split(items):
    ids = [str(i["id"]) for i in items]
    dupes = [k for k, n in Counter(ids).items() if n > 1]
    if dupes:
        sys.exit(f"duplicate item ids: {dupes[:5]}")
    sets = {"tuning": [], "heldout": []}
    for it in items:
        sets[which_set(it["id"])].append(it)
    return sets


def _has_rows(path):
    """True when a results file holds at least one judged item. A run that stopped before
    judging anything does not use up the held-out set."""
    try:
        return bool(json.loads(path.read_text()).get("rows"))
    except (OSError, ValueError, AttributeError):
        return path.exists()


def refuse_real_call():
    """Reasons not to spend money or send data yet; empty means go."""
    problems = []
    if not os.environ.get("TYPESAFE_API_KEY", "").strip():
        problems.append("TYPESAFE_API_KEY is not set: the user stores it (never paste it into chat or a file)")
    if not q.DATA_RULE.strip():
        problems.append("DATA_RULE in questions.py is empty: check the data rule first")
    if q.MODEL.startswith("<") or "latest" in q.MODEL or "preview" in q.MODEL:
        problems.append(f"MODEL {q.MODEL!r} is not a pinned version")
    if not isinstance(PRICE_PER_M_INPUT, (int, float)) or PRICE_PER_M_INPUT <= 0:
        problems.append("PRICE_PER_M_INPUT is not set from the pricing page")
    return problems


def main(argv):
    trials, rest, i = 1, [], 0
    while i < len(argv):
        a = argv[i]
        if a == "--trials" or a.startswith("--trials="):
            value = a.split("=", 1)[1] if "=" in a else (argv[i + 1] if i + 1 < len(argv) else "")
            i += 1 if "=" in a else 2
            if not value.isdigit() or int(value) < 1:
                sys.exit("--trials needs a whole number of 1 or more, e.g. --trials 3")
            trials = int(value)
            continue
        rest.append(a)
        i += 1
    argv = rest
    args = [a for a in argv if not a.startswith("--")]
    which = args[0] if args else "tuning"
    sets = split(load_items())
    if which == "split":
        for name, items in sets.items():
            print(f"{name}: {len(items)} items: {[i['id'] for i in items]}")
        return 0
    if which not in sets:
        sys.exit("usage: evaluate.py split | tuning | heldout [--dry-run] [--trials N] [--again]")
    items = sets[which]
    print(f"{which}: {len(items)} items, {trials} trial(s); expected {dict(Counter(i['expected'] for i in items))}")

    if "--dry-run" in argv:
        sizes = [len(json.dumps(q.build_state(i), default=str)) for i in items]
        if sizes:
            print(f"state size in characters: min {min(sizes)}, median {statistics.median(sizes)}, max {max(sizes)}")
            print("sample state (check every record the decision needs is present, in full):")
            print(json.dumps(q.build_state(items[0]), indent=2, default=str)[:4000])
        return 0

    problems = refuse_real_call()
    if problems:
        sys.exit("not calling the API:\n  " + "\n  ".join(problems))
    out = Path(f"evaluate-{which}.json")
    if which == "heldout" and _has_rows(out) and "--again" not in argv:
        sys.exit(f"{out} exists: the held-out set was already run. Rerunning after a revision means it is no "
                 "longer a clean hold-out; pass --again and say so in the report.")

    from typesafe_sdk import TypeSafeClient  # only real runs need the SDK

    rows, tokens, latencies, stopped, error = [], 0, [], False, None
    try:
        with TypeSafeClient() as client:
            for t in range(trials):
                for it in items:
                    if tokens / 1e6 * PRICE_PER_M_INPUT >= SPEND_CEILING_USD:
                        stopped = True
                        break
                    t0 = time.perf_counter()
                    res = q.judge(client, it)  # raises on any bad response; nothing is guessed
                    latencies.append((time.perf_counter() - t0) * 1000)
                    tokens += res["input_tokens"]
                    rows.append({"trial": t, "id": it["id"], "expected": it["expected"], "got": res["route"],
                                 "answers": res["answers"]})
                if stopped:
                    break
    except Exception as e:  # a failed gate or a refused call ends the run; it is never retried here
        error = e
    if not rows:
        print(f"STOPPED before any item was judged: {error!r}. Nothing was written; the {which} set is untouched.")
        return 1
    out.write_text(json.dumps({"set": which, "model": q.MODEL, "run_at": datetime.now(timezone.utc).isoformat(),
                               "again": "--again" in argv, "error": repr(error) if error else None,
                               "rows": rows}, indent=2, default=str))

    for t in range(trials):
        r = [x for x in rows if x["trial"] == t]
        if not r:
            continue
        decided = [x for x in r if x["got"] != "review"]
        agree = sum(x["got"] == x["expected"] for x in r)
        agree_decided = sum(x["got"] == x["expected"] for x in decided)
        print(f"trial {t}: agreement with past decisions {agree}/{len(r)}; sent to review {len(r) - len(decided)}; "
              f"of the decided, {agree_decided}/{len(decided)} agree")
    for (exp, got), n in sorted(Counter((x["expected"], x["got"]) for x in rows if x["trial"] == 0).items()):
        print(f"  expected {exp!s:24} got {got!s:24} {n}")
    if trials > 1:
        changed = sorted({x["id"] for x in rows if len({y["got"] for y in rows if y["id"] == x["id"]}) > 1})
        print(f"route changed between trials on {len(changed)} items: {changed}")
    if latencies:
        print(f"median latency {statistics.median(latencies):.0f} ms")
    print(f"input tokens {tokens}; spend ${tokens / 1e6 * PRICE_PER_M_INPUT:.5f} (ceiling ${SPEND_CEILING_USD:.2f} per run; the call that crosses it completes)")
    if stopped:
        print("STOPPED at the spend ceiling: results cover only the items above")
    if error:
        print(f"STOPPED by an error after {len(rows)} answers: {error!r}")
    print(f"thresholds stay PROVISIONAL until a held-out run supports them; results in {out}")
    return 1 if error else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
