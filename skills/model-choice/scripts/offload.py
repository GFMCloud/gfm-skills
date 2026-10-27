#!/usr/bin/env python3
"""Run a batch of small, bounded items through a local model server and check every answer.

Usage:
  offload.py --check [--api ollama|openai] [--host URL]
  offload.py --model M --prompt PROMPT.txt --input ITEMS.jsonl --out RESULTS.jsonl
             [--api ollama|openai] [--host URL] [--keys a,b,c] [--multiline]
             [--sample N | --only ID,ID,...] [--seed N] [--temperature T] [--timeout S]
             [--allow-remote]
  offload.py --selftest

ITEMS.jsonl: one JSON object per line, {"id": <string or number>, "input": "<text>"}.
PROMPT.txt:  the per-item prompt; {input} is replaced by the item's text.
--keys:      answers must be one JSON object holding these keys. Without it, answers must be
             one line (or any text with --multiline).
An answer of exactly UNSURE is the model escalating the item, never a failure of the run.

Writes one line per item to RESULTS.jsonl as it goes, skips items already answered with the same
prompt and model, then writes RESULTS.escalate.jsonl and prints a summary with spot-check IDs.
Exit codes: 0 done, 2 bad input or arguments, 3 done but escalations over 10 percent,
4 server unreachable or model not available. Standard library only; Python 3.9 or later.
"""
import argparse
import hashlib
import ipaddress
import json
import math
import os
import random
import shutil
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_HOSTS = {"ollama": "http://127.0.0.1:11434", "openai": "http://127.0.0.1:1234"}
ESCALATION_LIMIT = 0.10


class SetupError(Exception):
    """The server or model can't be used; nothing should be sent."""


def _http(method, url, body=None, timeout=120):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8", errors="replace"))
    if not isinstance(data, dict):
        raise ValueError("the server's answer is not a JSON object")
    return data


# Replaced by the self-test.
HTTP = _http


def with_scheme(host):
    return host if "://" in host else "http://" + host


def is_local(host):
    name = urllib.parse.urlparse(host).hostname or ""
    if name == "localhost":
        return True
    try:
        return ipaddress.ip_address(name).is_loopback
    except ValueError:
        return False


def same_model(asked, got, api):
    if asked == got:
        return True
    if api == "ollama" and ":" not in asked:
        return got == asked + ":latest"
    return False


def list_models(api, host, timeout):
    try:
        if api == "ollama":
            data = HTTP("GET", host + "/api/tags", timeout=timeout)
            return [m.get("name", "") for m in data.get("models", [])]
        data = HTTP("GET", host + "/v1/models", timeout=timeout)
        return [m.get("id", "") for m in data.get("data", [])]
    except (urllib.error.URLError, OSError, ValueError) as exc:
        reason = getattr(exc, "reason", exc)
        if isinstance(reason, PermissionError) or getattr(reason, "errno", None) == 1:
            raise SetupError("could not reach %s: the connection was blocked (%s). A sandbox "
                             "that blocks local network does this; it does not show whether a "
                             "server is running. Ask the user to run --check outside the "
                             "sandbox or to allow local connections." % (host, exc))
        raise SetupError("no %s server answering at %s (%s)" % (api, host, exc))


def ask(api, host, model, prompt, temperature, want_json, timeout):
    if api == "ollama":
        body = {"model": model, "prompt": prompt, "stream": False,
                "options": {"temperature": temperature}}
        if want_json:
            body["format"] = "json"
        data = HTTP("POST", host + "/api/generate", body, timeout=timeout)
        return str(data.get("response", "")), str(data.get("model", ""))
    body = {"model": model, "temperature": temperature, "stream": False,
            "messages": [{"role": "user", "content": prompt}]}
    data = HTTP("POST", host + "/v1/chat/completions", body, timeout=timeout)
    choices = data.get("choices") or [{}]
    content = (choices[0].get("message") or {}).get("content") or ""
    return str(content), str(data.get("model", ""))


def strip_fence(text):
    t = text.strip()
    if t.startswith("```") and t.endswith("```") and len(t) >= 6:
        t = t[3:-3]
        if "\n" in t:
            first, rest = t.split("\n", 1)
            if first.strip().isalpha() or not first.strip():
                t = rest
    return t.strip()


def classify(answer, keys, multiline):
    text = answer.strip()
    if text == "UNSURE":
        return "unsure", text
    if not text:
        return "format", text
    if keys:
        try:
            obj = json.loads(strip_fence(text))
        except ValueError:
            return "format", text
        if not isinstance(obj, dict) or any(k not in obj for k in keys):
            return "format", text
        if any(str(obj[k]).strip().upper() == "UNSURE" for k in keys):
            return "unsure", obj
        return "ok", obj
    if "\n" in text and not multiline:
        return "format", text
    return "ok", text


def load_items(path):
    items, problems, seen = [], [], set()
    with open(path, encoding="utf-8", errors="replace") as fh:
        for n, line in enumerate(fh, 1):
            if not line.strip():
                problems.append("line %d: blank line" % n)
                continue
            try:
                obj = json.loads(line)
            except ValueError:
                problems.append("line %d: not JSON" % n)
                continue
            if not isinstance(obj, dict):
                problems.append("line %d: not a JSON object" % n)
                continue
            iid, text = obj.get("id"), obj.get("input")
            if not isinstance(iid, (str, int)) or isinstance(iid, bool) or str(iid) == "":
                problems.append("line %d: missing or bad id" % n)
                continue
            if not isinstance(text, str) or not text.strip():
                problems.append("line %d (id %s): empty or missing input" % (n, iid))
                continue
            if str(iid) in seen:
                problems.append("line %d: duplicate id %s" % (n, iid))
                continue
            seen.add(str(iid))
            items.append((str(iid), text))
    if not items and not problems:
        problems.append("no items")
    return items, problems


def load_done(out_path, prompt_sha, model):
    """Answers already in the results file. Errors are left out so a rerun retries them."""
    done, unreadable = {}, 0
    if not os.path.exists(out_path):
        return done, unreadable
    with open(out_path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                row = json.loads(line)
            except ValueError:
                unreadable += 1
                continue
            if not isinstance(row, dict):
                unreadable += 1
                continue
            if row.get("prompt_sha") != prompt_sha or row.get("model_asked") != model:
                raise SetupError("%s holds results from a different prompt, --keys, "
                                 "--multiline or model; use a new --out file" % out_path)
            if row.get("status") == "error":
                done.pop(str(row.get("id")), None)
                continue
            done[str(row.get("id"))] = row
    return done, unreadable


def run(args):
    api = args.api
    host = with_scheme(args.host or DEFAULT_HOSTS[api]).rstrip("/")
    if not is_local(host) and not args.allow_remote:
        print("Refusing %s: not this machine. Local offload keeps data here; pass "
              "--allow-remote only if the user agreed to send the items there." % host)
        return 2
    if not is_local(host):
        print("WARNING: items will be sent to %s, off this machine." % host)

    if args.check:
        try:
            names = list_models(api, host, args.timeout)
        except SetupError as exc:
            print("Server: %s" % exc)
            return 4
        print("Server: %s (%s) answering; models: %s" % (host, api, ", ".join(names) or "none"))
        return 0

    for flag in ("model", "prompt", "input", "out"):
        if not getattr(args, flag):
            print("--%s is required (or use --check or --selftest)" % flag)
            return 2
    with open(args.prompt, encoding="utf-8", errors="replace") as fh:
        template = fh.read()
    if "{input}" not in template:
        print("The prompt file has no {input} placeholder.")
        return 2
    items, problems = load_items(args.input)
    if problems:
        print("Input problems, nothing sent:")
        for p in problems[:50]:
            print("  " + p)
        if len(problems) > 50:
            print("  ... and %d more" % (len(problems) - 50))
        return 2
    keys = [k.strip() for k in args.keys.split(",") if k.strip()] if args.keys else []
    if args.sample < 0:
        print("--sample must be 1 or more.")
        return 2
    if os.path.isdir(args.out):
        print("--out must be a file, not a folder.")
        return 2

    try:
        names = list_models(api, host, args.timeout)
        if not any(same_model(args.model, n, api) for n in names):
            raise SetupError("model %s is not available on %s (has: %s). Pulling or loading a "
                             "model needs the user's yes." % (args.model, host,
                                                             ", ".join(names) or "none"))
        fingerprint = "\0".join((template, ",".join(keys), str(args.multiline)))
        prompt_sha = hashlib.sha256(fingerprint.encode()).hexdigest()[:16]
        done, unreadable = load_done(args.out, prompt_sha, args.model)
    except SetupError as exc:
        print(str(exc))
        return 4

    rng = random.Random(args.seed)
    chosen = items
    if args.only:
        want = [x.strip() for x in args.only.split(",") if x.strip()]
        known = {i for i, _ in items}
        missing = [w for w in want if w not in known]
        if missing:
            print("--only names IDs not in the input: %s" % ", ".join(missing))
            return 2
        chosen = [it for it in items if it[0] in set(want)]
    elif args.sample:
        chosen = rng.sample(items, min(args.sample, len(items)))

    todo = [it for it in chosen if it[0] not in done]
    errors_in_a_row = 0
    needs_newline = False
    if os.path.exists(args.out) and os.path.getsize(args.out):
        with open(args.out, "rb") as fh:
            fh.seek(-1, os.SEEK_END)
            needs_newline = fh.read(1) != b"\n"
    with open(args.out, "a", encoding="utf-8") as out:
        if needs_newline:
            out.write("\n")
        for iid, text in todo:
            prompt = template.replace("{input}", text)
            started = time.time()
            try:
                answer, got_model = ask(api, host, args.model, prompt, args.temperature,
                                        bool(keys), args.timeout)
                errors_in_a_row = 0
            except (urllib.error.URLError, OSError, ValueError) as exc:
                answer, got_model = "", ""
                status, value = "error", str(exc)
                errors_in_a_row += 1
            else:
                if not same_model(args.model, got_model, api):
                    status, value = "model_mismatch", answer
                else:
                    status, value = classify(answer, keys, args.multiline)
            row = {"id": iid, "status": status, "output": value, "model_asked": args.model,
                   "model_answered": got_model, "prompt_sha": prompt_sha,
                   "ms": int((time.time() - started) * 1000)}
            out.write(json.dumps(row, ensure_ascii=False) + "\n")
            out.flush()
            done[iid] = row
            if errors_in_a_row >= 3:
                print("Three errors in a row; stopping. Is the server still running?")
                break

    ran = [done[i] for i, _ in chosen if i in done]
    counts = {}
    for row in ran:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    escalate = [r for r in ran if r["status"] != "ok"]
    esc_path = os.path.splitext(args.out)[0] + ".escalate.jsonl"
    with open(esc_path, "w", encoding="utf-8") as fh:
        for row in done.values():
            if row["status"] != "ok":
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    ok_ids = [r["id"] for r in ran if r["status"] == "ok"]
    k = min(len(ok_ids), max(10, math.ceil(0.05 * len(ok_ids))))
    spot = sorted(rng.sample(ok_ids, k)) if ok_ids else []
    rate = len(escalate) / len(ran) if ran else 0.0

    print("Model: %s on %s (%s); prompt %s" % (args.model, host, api, prompt_sha))
    print("Items: %d chosen, %d answered, %d not reached" % (len(chosen), len(ran),
                                                             len(chosen) - len(ran)))
    print("Status: " + ", ".join("%s %d" % (s, counts.get(s, 0)) for s in
                                 ("ok", "unsure", "format", "model_mismatch", "error")))
    print("Escalate: %d (%.0f%%) of these; every escalation so far -> %s"
          % (len(escalate), rate * 100, esc_path))
    if unreadable:
        print("Skipped %d unreadable line(s) in %s; those items were run again." % (unreadable,
                                                                                 args.out))
    answered = {r["model_answered"] for r in ran if r["status"] != "error"}
    if ran and counts.get("model_mismatch", 0) == len(ran) and len(answered) == 1:
        print("Every answer came back from model %r, not %r. The server may report this model "
              "under another name; check --check's list before blaming the task."
              % (answered.pop(), args.model))
    print("Spot-check these against the source: %s" % (", ".join(spot) or "none"))
    if len(chosen) - len(ran):
        return 4
    if rate > ESCALATION_LIMIT:
        print("STOP: escalations over 10%. Read them before going on; the task may not suit "
              "a local model, or the prompt needs work.")
        return 3
    return 0


def selftest():
    global HTTP
    real = HTTP
    tmp = tempfile.mkdtemp(prefix="offload-selftest-")
    results = []

    def check(name, cond):
        results.append((name, bool(cond)))

    def write(name, text):
        p = os.path.join(tmp, name)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(text)
        return p

    replies = {}

    def fake(method, url, body=None, timeout=120):
        if url.endswith("/api/tags"):
            return {"models": [{"name": "tiny:latest"}, {"name": "other:7b"}]}
        if url.endswith("/v1/models"):
            return {"data": [{"id": "local-model"}]}
        text = body["prompt"] if "prompt" in body else body["messages"][0]["content"]
        key = text.split("ITEM:", 1)[1].strip()
        answer, model = replies.get(key, ("x", body["model"]))
        if answer is OSError:
            raise OSError("connection refused")
        if url.endswith("/api/generate"):
            return {"response": answer, "model": model}
        return {"choices": [{"message": {"content": answer}}], "model": model}

    def args(**kw):
        base = dict(check=False, api="ollama", host=None, model="tiny", prompt=None, input=None,
                    out=None, keys=None, multiline=False, sample=0, only=None, seed=1,
                    temperature=0.1, timeout=5, allow_remote=False)
        base.update(kw)
        return argparse.Namespace(**base)

    def quiet(a):
        saved = sys.stdout
        sys.stdout = open(os.devnull, "w")
        try:
            return run(a)
        finally:
            sys.stdout.close()
            sys.stdout = saved

    HTTP = fake
    try:
        prompt = write("p.txt", "Extract fields. ITEM: {input}")
        bad = write("bad.jsonl", '{"id": 1, "input": "a"}\n{"id": 2, "input": "  "}\n'
                                 '{"id": 1, "input": "b"}\nnot json\n')
        out = os.path.join(tmp, "r0.jsonl")
        check("empty input, duplicate id and bad line stop the run",
              quiet(args(prompt=prompt, input=bad, out=out)) == 2 and not os.path.exists(out))
        check("prompt without {input} is refused",
              quiet(args(prompt=write("np.txt", "no slot"), input=write("one.jsonl",
                    '{"id": "a", "input": "x"}\n'), out=out)) == 2)
        check("a remote host is refused without --allow-remote",
              quiet(args(check=True, host="http://192.0.2.7:11434")) == 2)
        check("loopback and localhost count as local",
              is_local("http://127.0.0.1:1") and is_local("http://localhost:1")
              and is_local("http://[::1]:1") and not is_local("http://10.0.0.1:1"))
        check("a model that is not pulled stops before sending",
              quiet(args(model="missing", prompt=prompt, input=write("one.jsonl",
                    '{"id": "a", "input": "x"}\n'), out=out)) == 4)
        check("tag-less name matches :latest", same_model("tiny", "tiny:latest", "ollama")
              and not same_model("tiny", "other:7b", "ollama"))

        lines = "".join('{"id": "i%d", "input": "k%d"}\n' % (n, n) for n in range(20))
        items = write("items.jsonl", lines)
        replies.update({"k0": ("UNSURE", "tiny:latest"),
                        "k1": ("not json", "tiny:latest"),
                        "k2": ('{"name": "x"}', "tiny:latest"),
                        "k3": ('{"name": "x", "year": 1}', "other:7b"),
                        "k4": ('```json\n{"name": "y", "year": 2}\n```', "tiny:latest")})
        for n in range(5, 20):
            replies["k%d" % n] = ('{"name": "n", "year": %d}' % n, "tiny:latest")
        out = os.path.join(tmp, "r1.jsonl")
        code = quiet(args(prompt=prompt, input=items, out=out, keys="name,year"))
        rows = {json.loads(l)["id"]: json.loads(l) for l in open(out)}
        check("statuses: UNSURE, bad JSON, missing key, wrong model, fenced JSON",
              rows["i0"]["status"] == "unsure" and rows["i1"]["status"] == "format"
              and rows["i2"]["status"] == "format" and rows["i3"]["status"] == "model_mismatch"
              and rows["i4"]["status"] == "ok")
        check("four escalations of 20 is over 10 percent: exit 3", code == 3)
        esc = [json.loads(l)["id"] for l in open(os.path.splitext(out)[0] + ".escalate.jsonl")]
        check("escalate file lists exactly the four", sorted(esc) == ["i0", "i1", "i2", "i3"])

        calls = []
        HTTP = lambda m, u, b=None, timeout=120: (calls.append(u), fake(m, u, b, timeout))[1]
        quiet(args(prompt=prompt, input=items, out=out, keys="name,year"))
        check("a rerun skips answered items", not any(u.endswith("/api/generate") for u in calls))
        HTTP = fake
        check("a rerun with a changed prompt is refused",
              quiet(args(prompt=write("p2.txt", "Other. ITEM: {input}"), input=items, out=out,
                         keys="name,year")) == 4)

        out = os.path.join(tmp, "r2.jsonl")
        quiet(args(prompt=prompt, input=items, out=out, sample=5, seed=3))
        check("--sample answers only that many", len(open(out).readlines()) == 5)
        out = os.path.join(tmp, "r3.jsonl")
        quiet(args(prompt=prompt, input=items, out=out, only="i7,i9"))
        check("--only answers the named IDs",
              sorted(json.loads(l)["id"] for l in open(out)) == ["i7", "i9"])
        check("--only with an unknown ID is refused",
              quiet(args(prompt=prompt, input=items, out=os.path.join(tmp, "r4.jsonl"),
                         only="nope")) == 2)

        replies.update({"m1": ("two\nlines", "tiny:latest"), "m2": ("one line", "tiny:latest")})
        two = write("two.jsonl", '{"id": "m1", "input": "m1"}\n{"id": "m2", "input": "m2"}\n')
        out = os.path.join(tmp, "r5.jsonl")
        quiet(args(prompt=prompt, input=two, out=out))
        rows = {json.loads(l)["id"]: json.loads(l)["status"] for l in open(out)}
        check("plain answers must be one line", rows == {"m1": "format", "m2": "ok"})

        replies.update({"o1": ("two\nlines", "local-model"), "o2": ("one", "local-model")})
        two = write("two-o.jsonl", '{"id": "o1", "input": "o1"}\n{"id": "o2", "input": "o2"}\n')
        out = os.path.join(tmp, "r6.jsonl")
        quiet(args(api="openai", model="local-model", prompt=prompt, input=two, out=out,
                   multiline=True))
        rows = {json.loads(l)["id"]: json.loads(l)["status"] for l in open(out)}
        check("OpenAI-compatible server path, --multiline", rows == {"o1": "ok", "o2": "ok"})

        replies.update({"e%d" % n: (OSError, "") for n in range(5)})
        errs = write("errs.jsonl", "".join('{"id": "e%d", "input": "e%d"}\n' % (n, n)
                                           for n in range(5)))
        out = os.path.join(tmp, "r7.jsonl")
        code = quiet(args(prompt=prompt, input=errs, out=out))
        check("three errors in a row stop the run (exit 4)",
              code == 4 and len(open(out).readlines()) == 3)

        replies.update({"j1": ('{"name": "UNSURE", "year": 1}', "tiny:latest"),
                        "j2": ('{"name": "a", "year": 2}', "tiny:latest")})
        js = write("js.jsonl", '{"id": "j1", "input": "j1"}\n{"id": "j2", "input": "j2"}\n')
        out = os.path.join(tmp, "r8.jsonl")
        quiet(args(prompt=prompt, input=js, out=out, keys="name,year"))
        rows = {json.loads(l)["id"]: json.loads(l)["status"] for l in open(out)}
        check("a JSON answer holding UNSURE is escalated, not ok",
              rows == {"j1": "unsure", "j2": "ok"})

        replies.update({"r%d" % n: (OSError, "") for n in range(3)})
        rr = write("rr.jsonl", "".join('{"id": "r%d", "input": "r%d"}\n' % (n, n)
                                       for n in range(3)))
        out = os.path.join(tmp, "r9.jsonl")
        quiet(args(prompt=prompt, input=rr, out=out))
        replies.update({"r%d" % n: ("fine", "tiny:latest") for n in range(3)})
        code = quiet(args(prompt=prompt, input=rr, out=out))
        rows = {}
        for l in open(out):
            rows[json.loads(l)["id"]] = json.loads(l)["status"]
        check("a rerun retries items that errored", code == 0
              and rows == {"r0": "ok", "r1": "ok", "r2": "ok"})

        two = write("two-m.jsonl", '{"id": "m1", "input": "m1"}\n{"id": "m2", "input": "m2"}\n')
        out = os.path.join(tmp, "r10.jsonl")
        quiet(args(prompt=prompt, input=two, out=out, multiline=True))
        with open(out, "a") as fh:
            fh.write('{"id": "o9", "status": "ok", "out')
        quiet(args(prompt=prompt, input=two, out=out, multiline=True))
        with open(out) as fh:
            tail = fh.read()
        check("a partial last line is closed before new rows", tail.endswith("\n")
              and quiet(args(prompt=prompt, input=two, out=out, multiline=True)) == 0)
        check("--keys or --multiline change the results file's fingerprint",
              quiet(args(prompt=prompt, input=two, out=out)) == 4)

        out = os.path.join(tmp, "r1.jsonl")
        quiet(args(prompt=prompt, input=items, out=out, keys="name,year", only="i7"))
        esc = [json.loads(l)["id"] for l in open(os.path.splitext(out)[0] + ".escalate.jsonl")]
        check("an --only rerun keeps earlier escalations in the escalate file",
              sorted(esc) == ["i0", "i1", "i2", "i3"])
        check("a host without a scheme is read as http and local",
              is_local(with_scheme("127.0.0.1:11434")) and is_local(with_scheme("localhost:1")))
        check("--sample below 1 and --out as a folder are refused",
              quiet(args(prompt=prompt, input=items, out=os.path.join(tmp, "x.jsonl"),
                         sample=-1)) == 2
              and quiet(args(prompt=prompt, input=items, out=tmp)) == 2)

        def odd(m, u, b=None, timeout=120):
            if u.endswith("/api/tags"):
                return fake(m, u, b, timeout)
            raise ValueError("the server's answer is not a JSON object")
        HTTP = odd
        out = os.path.join(tmp, "r11.jsonl")
        code = quiet(args(prompt=prompt, input=two, out=out))
        check("a non-object server answer is an error row, not a crash",
              {json.loads(l)["status"] for l in open(out)} == {"error"})
        HTTP = fake

        def down(*a, **k):
            raise urllib.error.URLError("refused")
        HTTP = down
        check("no server: exit 4", quiet(args(check=True)) == 4)

        def blocked(*a, **k):
            raise urllib.error.URLError(PermissionError(1, "Operation not permitted"))
        HTTP = blocked
        try:
            list_models("ollama", "http://127.0.0.1:11434", 5)
            said = ""
        except SetupError as exc:
            said = str(exc)
        check("a blocked connection is reported as blocked, not as no server",
              "blocked" in said and "no ollama server" not in said)
    finally:
        HTTP = real

    for name, ok in results:
        print("%s  %s" % ("PASS" if ok else "FAIL", name))
    failed = sum(1 for _, ok in results if not ok)
    if failed:
        print("%d checks, %d failed (scratch files kept in %s)" % (len(results), failed, tmp))
        return 1
    shutil.rmtree(tmp, ignore_errors=True)
    print("%d checks, all passed" % len(results))
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--selftest", action="store_true")
    p.add_argument("--check", action="store_true", help="list the server's models and stop")
    p.add_argument("--api", choices=("ollama", "openai"), default="ollama",
                   help="ollama, or an OpenAI-compatible local server (LM Studio, llama.cpp)")
    p.add_argument("--host", help="default http://127.0.0.1:11434 (ollama) or :1234 (openai)")
    p.add_argument("--model")
    p.add_argument("--prompt")
    p.add_argument("--input")
    p.add_argument("--out")
    p.add_argument("--keys", help="comma-separated keys every JSON answer must hold")
    p.add_argument("--multiline", action="store_true")
    p.add_argument("--sample", type=int, default=0, help="answer N random items only")
    p.add_argument("--only", help="answer only these comma-separated IDs")
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--temperature", type=float, default=0.1)
    p.add_argument("--timeout", type=float, default=120)
    p.add_argument("--allow-remote", action="store_true")
    a = p.parse_args(argv)
    if a.selftest:
        return selftest()
    try:
        return run(a)
    except FileNotFoundError as exc:
        print("File not found: %s" % exc.filename)
        return 2


if __name__ == "__main__":
    sys.exit(main())
