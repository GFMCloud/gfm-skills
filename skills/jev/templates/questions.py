# questions.py: every Jev question and threshold for <DECISION>, in one file a person reviews.
#
# Made from the jev skill's template. Fill every <ANGLE> placeholder, delete the example
# question you don't need, and keep the contract test_questions.py checks:
#   evidence (the state): <WHAT IT HOLDS, AND WHERE CODE GETS EACH FIELD>
#   Jev decides: <THE ONE NARROW JUDGMENT>. Code or a person decides: <EVERYTHING ELSE>
#   thresholds: PROVISIONAL until a held-out run supports them: <DATE, ITEM COUNT, RESULTS FILE>
#
# Only two functions touch the TypeSafe SDK: to_sdk() and ask(). Check both against the
# provider's current Python SDK docs before the first real call; everything else is plain
# Python and is tested offline.
import math

# A versioned model id, never an alias such as jev-latest: an alias moves when a new
# release ships and the thresholds below stop meaning anything. Take it from the provider's
# models page and note the date you checked. Changing it means re-running the held-out set.
MODEL = "<PINNED_MODEL_ID>"  # checked <DATE> at <MODELS PAGE URL>

# The data rule this project's items were checked against before any call: where it came
# from and when, e.g. "public data only; ~/.agents/jev/data-decision.md; checked <DATE>".
# evaluate.py refuses to call the API while this is empty.
DATA_RULE = ""

QUESTIONS = {
    # Example yes/no (Noul): one property the state can answer; a high value means yes.
    "<noul_id>": {
        "type": "noul",
        "instructions": {
            "question": "Is `item` the same <THING> as `reference`?",
            "focus": "<WHAT TO COMPARE, AND WHAT TO IGNORE>",
        },
        "criteria": {
            "true": "<WHAT COUNTS AS YES, CONCRETELY>",
            "false": "<WHAT COUNTS AS NO, INCLUDING THE NEAR MISS THAT IS STILL NO>",
        },
    },
    # Example pick-one (Choice): every option defined, including where it stops, plus a way out.
    "<choice_id>": {
        "type": "choice",
        "instructions": {"question": "Which <OPTION> fits `item`?", "focus": "<WHAT TO JUDGE>"},
        "criteria": {
            "<option_a>": {"what": "<COVERS>", "not_for": "<BELONGS ELSEWHERE>", "examples": ["<REAL PAST CASE>"]},
            "<option_b>": {"what": "<COVERS>", "not_for": "<BELONGS ELSEWHERE>", "examples": ["<REAL PAST CASE>"]},
            "none": "None of the options above fit",
        },
    },
    # A Score is {"type": "score", "instructions": ..., "criteria": [<lowest level>, ..., <highest>]},
    # each level a situation, not a degree. Its answer is read like a Choice's (value, confidence).
}

# Thresholds. The middle band is never guessed: it goes to review.
YES_FROM = 0.80           # Noul at or above: act on yes
NO_BELOW = 0.20           # Noul below: act on no
CHOICE_CONFIDENCE = 0.60  # Choice or Score confidence below this: review


def build_state(item):
    """The evidence packet: the item and every record the decision is really made against,
    in full, as each stood when the past decision was made. Never a summary or a title."""
    return {"item": item["item"], "reference": item["reference"]}


def route(answers):
    """Map checked answers to what code does next. Replace with the project's own branches."""
    noul = answers["<noul_id>"]["value"]
    choice = answers["<choice_id>"]
    if NO_BELOW <= noul < YES_FROM or choice["confidence"] < CHOICE_CONFIDENCE:
        return "review"
    return f"{'yes' if noul >= YES_FROM else 'no'}:{choice['value']}"


# ---- SDK boundary: check these two against the provider's current docs ----

def to_sdk(questions):
    """Turn QUESTIONS into SDK question objects."""
    from typesafe_sdk import Choice, Noul, NoulCriteria, Score

    out = {}
    for qid, q in questions.items():
        if q["type"] == "noul":
            crit = q.get("criteria")
            out[qid] = Noul(instructions=q["instructions"],
                            criteria=NoulCriteria(**crit) if crit else None)
        elif q["type"] == "choice":
            out[qid] = Choice(instructions=q["instructions"], criteria=q["criteria"])
        elif q["type"] == "score":
            out[qid] = Score(instructions=q["instructions"], criteria=q["criteria"])
        else:
            raise ValueError(f"{qid}: unknown question type {q['type']!r}")
    return out


def ask(client, state):
    """One call. Returns a plain dict; reads only the response fields named here."""
    r = client.system_one(model=MODEL, state=state, questions=to_sdk(QUESTIONS))
    answers = {}
    for qid, a in (getattr(r, "answers", None) or {}).items():
        kind = getattr(a, "type", None)
        if kind == "noul":
            answers[qid] = {"type": kind, "value": getattr(a, "noul", None)}
        elif kind in ("choice", "score"):
            answers[qid] = {"type": kind, "value": getattr(a, kind, None),
                            "confidence": getattr(a, "confidence", None)}
        else:
            answers[qid] = {"type": kind}
    usage = getattr(r, "usage", None)
    return {"model": getattr(r, "model", None), "answers": answers,
            "input_tokens": getattr(usage, "input_tokens", None)}

# ---- end of SDK boundary ----


def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _prob(x):
    return _num(x) and 0 <= x <= 1


def check(resp):
    """Fail closed: raise on anything that is not a complete answer from the pinned model.
    Nothing here defaults to a safe-looking value."""
    if not isinstance(resp, dict):
        raise RuntimeError(f"response is {type(resp).__name__}, not a dict")
    if resp.get("model") != MODEL:
        raise RuntimeError(f"answered by {resp.get('model')!r}; thresholds were set on {MODEL!r}")
    tokens = resp.get("input_tokens")
    if not isinstance(tokens, int) or isinstance(tokens, bool) or tokens < 0:
        raise RuntimeError(f"input_tokens is {tokens!r}; spend cannot be counted")
    answers = resp.get("answers")
    if not isinstance(answers, dict):
        raise RuntimeError(f"answers is {type(answers).__name__}, not a dict")
    missing, extra = set(QUESTIONS) - set(answers), set(answers) - set(QUESTIONS)
    if missing or extra:
        raise RuntimeError(f"missing answers {sorted(missing)}; unexpected answers {sorted(map(str, extra))}")
    for qid, q in QUESTIONS.items():
        a = answers[qid]
        if not isinstance(a, dict):
            raise RuntimeError(f"{qid}: answer is {type(a).__name__}, not a dict")
        if a.get("type") != q["type"]:
            raise RuntimeError(f"{qid}: asked a {q['type']}, got {a.get('type')!r}")
        value = a.get("value")
        if q["type"] == "noul" and not _prob(value):
            raise RuntimeError(f"{qid}: noul {value!r} is not a probability")
        if q["type"] in ("choice", "score") and not _prob(a.get("confidence")):
            raise RuntimeError(f"{qid}: confidence {a.get('confidence')!r} is not a probability")
        if q["type"] == "choice" and not (isinstance(value, str) and value in q["criteria"]):
            raise RuntimeError(f"{qid}: {value!r} is not one of the options")
        # A Score's value is the expected level, counted from 0 for the first criterion.
        if q["type"] == "score" and not (_num(value) and 0 <= value <= len(q["criteria"]) - 1):
            raise RuntimeError(f"{qid}: score {value!r} is not between 0 and {len(q['criteria']) - 1}")
    return resp


def judge(client, item):
    """Ask, check, route. Raises rather than guess."""
    resp = check(ask(client, build_state(item)))
    return {"route": route(resp["answers"]), **resp}
