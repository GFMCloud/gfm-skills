# test_questions.py: proves questions.py fails closed, by deliberate failure. Standard
# library only: no SDK, no network, no spend. Every response below is FAKE fixture data;
# never report its output as a finding. Run before any real call:
#   python3 test_questions.py
# Every line must print PASS; the first FAIL exits 1.
import math
import sys
from types import SimpleNamespace as NS

import questions as q

failures = 0


def report(ok, label, detail=""):
    global failures
    print(f"{'PASS' if ok else 'FAIL'} {label}{': ' + detail if detail else ''}")
    if not ok:
        failures += 1


def good():
    """A complete, valid fake response for the current QUESTIONS."""
    answers = {}
    for qid, spec in q.QUESTIONS.items():
        if spec["type"] == "noul":
            answers[qid] = {"type": "noul", "value": 0.95}
        elif spec["type"] == "choice":
            answers[qid] = {"type": "choice", "value": next(iter(spec["criteria"])), "confidence": 0.9}
        else:
            answers[qid] = {"type": "score", "value": 0.0, "confidence": 0.9}
    return {"model": q.MODEL, "input_tokens": 10, "answers": answers}


def expect_raise(resp, label):
    try:
        q.check(resp)
    except RuntimeError as e:
        report(True, label, f"raised ({e})")
    except Exception as e:  # the gate let it through and something later tripped over it
        report(False, label, f"not caught by the gate; crashed with {e!r}")
    else:
        report(False, label, "a bad response was accepted")


# 0. The file is filled in.
report(not q.MODEL.startswith("<") and "latest" not in q.MODEL and "preview" not in q.MODEL,
       "MODEL is a pinned version, not a placeholder or alias", repr(q.MODEL))
report(not any(k.startswith("<") for k in q.QUESTIONS), "question ids are filled in")

# 1. A good response passes and routes somewhere.
try:
    report(isinstance(q.route(q.check(good())["answers"]), str), "valid response is accepted and routed")
except Exception as e:
    report(False, "valid response is accepted and routed", repr(e))

# 2. Structural failures raise.
for qid in q.QUESTIONS:  # each answer in turn, not just the first
    r = good(); del r["answers"][qid]
    expect_raise(r, f"answer {qid!r} missing")
r = good(); r["answers"]["not_asked"] = {"type": "noul", "value": 0.5}
expect_raise(r, "answer to a question never asked")
r = good(); r["model"] = "some-other-model"
expect_raise(r, "a different model answered")
r = good(); r["input_tokens"] = None
expect_raise(r, "usage missing, so spend can't be counted")
expect_raise(None, "no response at all")
r = good(); r["answers"] = None
expect_raise(r, "answers missing")
for qid, spec in q.QUESTIONS.items():
    r = good(); r["answers"][qid]["type"] = "box"
    expect_raise(r, f"{qid}: wrong answer type")
    if spec["type"] == "noul":
        for bad in (None, 1.5, -0.1, math.nan, True, "0.9"):
            r = good(); r["answers"][qid]["value"] = bad
            expect_raise(r, f"{qid}: noul value {bad!r}")
    else:
        for bad in (None, 2.0, math.nan):
            r = good(); r["answers"][qid]["confidence"] = bad
            expect_raise(r, f"{qid}: confidence {bad!r}")
    if spec["type"] == "score":
        for bad in (None, True, -1, len(spec["criteria"]), 99.0, math.nan, "1"):
            r = good(); r["answers"][qid]["value"] = bad
            expect_raise(r, f"{qid}: score value {bad!r}")
    r = good(); r["answers"][qid] = None
    expect_raise(r, f"{qid}: answer that isn't a dict")
    if spec["type"] == "choice":
        for bad in ("not-an-option", ["a"], None):
            r = good(); r["answers"][qid]["value"] = bad
            expect_raise(r, f"{qid}: choice {bad!r}")

# 3. The unsure middle goes to review, never to a guess.
for qid, spec in q.QUESTIONS.items():
    r = good()
    if spec["type"] == "noul":
        r["answers"][qid]["value"] = (q.NO_BELOW + q.YES_FROM) / 2
    else:
        r["answers"][qid]["confidence"] = q.CHOICE_CONFIDENCE / 2
    try:
        got = q.route(q.check(r)["answers"])
        report(got == "review", f"{qid}: unsure answer routes to review", f"got {got!r}")
    except Exception as e:
        report(False, f"{qid}: unsure answer routes to review", repr(e))

# 4. ask() reads an SDK-shaped response correctly (fake client; SDK classes stubbed out).
class FakeClient:
    def system_one(self, model, state, questions):
        answers = {}
        for qid, a in good()["answers"].items():
            fields = {"type": a["type"], a["type"]: a["value"]}
            if "confidence" in a:
                fields["confidence"] = a["confidence"]
            answers[qid] = NS(**fields)
        return NS(model=model, answers=answers, usage=NS(input_tokens=10, output_tokens=0))


real_to_sdk, q.to_sdk = q.to_sdk, (lambda questions: questions)
try:
    sample = {"item": "fake item", "reference": "fake reference"}
    try:
        state = q.build_state(sample)
    except Exception:
        state = sample  # build_state expects the project's own item shape or files; not tested here
    resp = q.ask(FakeClient(), state)
    report(q.check(resp) is resp, "ask() output passes check() for a well-formed response")
except Exception as e:
    report(False, "ask() output passes check() for a well-formed response", repr(e))
finally:
    q.to_sdk = real_to_sdk

print(f"{failures} failure(s)")
sys.exit(1 if failures else 0)
