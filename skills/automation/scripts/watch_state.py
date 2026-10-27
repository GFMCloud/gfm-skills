#!/usr/bin/env python3
"""Remember what a watched source looked like, and say REPORT only when it changes.

Usage:
  python3 watch_state.py STATE SOURCE VALUE           compare VALUE with the last reported state
  python3 watch_state.py STATE SOURCE -               read VALUE from standard input
  python3 watch_state.py STATE SOURCE --unreadable MSG
                                                      the source could not be read this time
  python3 watch_state.py --confirm STATE SOURCE      the pending report was delivered; record it
  python3 watch_state.py --confirm STATE SOURCE VALUE same, and refuse if VALUE is not what is pending
  python3 watch_state.py --show STATE                 print the state file

Options:
  --hash      store and compare a SHA-256 of VALUE instead of VALUE itself (for page text,
              file contents, long command output). Pass it on every reading of that source;
              --unreadable and --confirm work with or without it

What it prints (first word is the verdict, so a job can `case` on it):
  BASELINE  first look at this source; nothing to report
  NO-CHANGE same as the last reported state (or a REPORT for the same change is still pending)
  REPORT    the state changed since the last confirmed report; send the report, then --confirm

A REPORT repeats on every run until --confirm records it, so a report that failed to send is sent
again next time. If the state changes and changes back before a report is confirmed, the REPORT
says so instead of dropping the blip. --unreadable is a state of its own ("UNREADABLE"), so the
first failed read reports once and a recovery reports once; repeated failures stay quiet.

The state file is JSON, one source per file. It is written atomically. A state file that does not
parse, or that names a different source, is never overwritten: the script exits 2 and a person
decides. Readings are compared as bytes decoded as UTF-8 (bad bytes replaced), so the result does
not depend on the locale. A reading over 1,000 characters is refused without --hash.

Not safe to run twice at once on the same state file: the job that calls it holds a lock.

Exit codes: 0 a verdict was printed, 2 usage error, unreadable state file or wrong source.
Standard library only; Python 3.9 or later.
"""
import datetime
import hashlib
import json
import os
import sys
import tempfile

UNREADABLE = "UNREADABLE"
SHOW_MAX = 200
VALUE_MAX = 1000  # longer readings must use --hash


def now():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def fail(msg):
    print("ERROR " + msg, file=sys.stderr)
    sys.exit(2)


def clean(text):
    """Printable, valid UTF-8, one line: safe to store, print and `case` on."""
    text = text.encode("utf-8", errors="replace").decode("utf-8", errors="replace")
    return "".join(c if c.isprintable() else " " for c in text)


def short(value):
    value = clean(value).strip()
    return value if len(value) <= SHOW_MAX else value[:SHOW_MAX] + "..."


def load(path, source):
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            state = json.load(f)
    except (OSError, ValueError) as e:
        fail("state file %s cannot be read (%s); fix or move it by hand, it was not changed" % (path, e))
    if not isinstance(state, dict) or state.get("watch") != 1:
        fail("state file %s is not a watch_state file; it was not changed" % path)
    if source is not None and state.get("source") != source:
        fail("state file %s is for source %r, not %r; it was not changed"
             % (path, state.get("source"), source))
    return state


def save(path, state):
    folder = os.path.dirname(os.path.abspath(path))
    os.makedirs(folder, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".watch-", dir=folder)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, sort_keys=True)
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def parse(argv):
    opts = {"hash": False, "confirm": False, "show": False, "unreadable": None}
    pos = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--hash":
            opts["hash"] = True
        elif a == "--confirm":
            opts["confirm"] = True
        elif a == "--show":
            opts["show"] = True
        elif a == "--unreadable":
            if i + 1 >= len(argv):
                fail("--unreadable needs a message")
            opts["unreadable"] = argv[i + 1]
            i += 1
        elif a in ("-h", "--help"):
            print(__doc__)
            sys.exit(0)
        elif a.startswith("--"):
            fail("unknown option " + a)
        else:
            pos.append(a)
        i += 1
    return opts, pos


def observed_value(opts, raw):
    if opts["unreadable"] is not None:
        return UNREADABLE, UNREADABLE
    if raw == "-":
        data = sys.stdin.buffer.read()
    else:
        data = os.fsencode(raw)
    if opts["hash"]:
        digest = "sha256:" + hashlib.sha256(data).hexdigest()
        return digest, short(data.decode("utf-8", errors="replace"))
    value = clean(data.decode("utf-8", errors="replace")).strip()
    if value == UNREADABLE:
        fail("the value UNREADABLE is reserved; use --unreadable MSG")
    if len(value) > VALUE_MAX:
        fail("reading is %d characters; reduce it to the part that matters, or pass --hash"
             % len(value))
    return value, short(value)


def main(argv):
    opts, pos = parse(argv)
    if opts["show"]:
        if len(pos) != 1:
            fail("usage: --show STATE")
        state = load(pos[0], None)
        print(json.dumps(state, indent=2, sort_keys=True) if state else "no state file yet")
        return 0

    if opts["confirm"]:
        if len(pos) not in (2, 3) or opts["unreadable"] is not None:
            fail("usage: --confirm STATE SOURCE [VALUE]")
        path, source = pos[0], pos[1]
        state = load(path, source)
        if state is None:
            fail("nothing to confirm: no state file for %s yet" % source)
        pending = state.get("pending")
        if pending is None:
            print("NOTHING-PENDING %s %s" % (source, state.get("last_shown")))
            return 0
        if len(pos) == 3 and state.get("hashed"):
            fail("this source is hashed; confirm it without VALUE")
        if len(pos) == 3 and pos[2] != UNREADABLE:
            value, _ = observed_value(opts, pos[2])
            if value != pending:
                fail("pending report is for %r, not %r; nothing recorded"
                     % (state.get("pending_shown"), pos[2]))
        elif len(pos) == 3 and pending != UNREADABLE:
            fail("pending report is for %r, not UNREADABLE; nothing recorded" % state.get("pending_shown"))
        stamp = now()
        state.update(last_state=pending, last_shown=state.get("pending_shown"), last_reported=stamp,
                     pending=None, pending_shown=None, blip=None)
        save(path, state)
        print("CONFIRMED %s %s" % (source, state["last_shown"]))
        return 0

    want = 2 if opts["unreadable"] is not None else 3
    if len(pos) != want:
        fail("usage: STATE SOURCE VALUE (or STATE SOURCE --unreadable MSG); see --help")
    path, source = pos[0], pos[1]
    if not source.strip() or clean(source) != source:
        fail("SOURCE must be a non-empty name with no line breaks or control characters")
    value, shown = observed_value(opts, pos[2] if want == 3 else "")
    state = load(path, source)
    stamp = now()

    if state is None:
        state = {"watch": 1, "source": source, "hashed": opts["hash"], "first_seen": stamp,
                 "last_state": value, "last_shown": shown, "last_reported": "never",
                 "last_seen": stamp, "pending": None, "pending_shown": None, "blip": None,
                 "last_error": opts["unreadable"]}
        save(path, state)
        print("BASELINE %s %s" % (source, shown))
        return 0

    if opts["unreadable"] is None and bool(state.get("hashed")) != opts["hash"]:
        fail("state file %s was made %s --hash; call it the same way every time"
             % (path, "with" if state.get("hashed") else "without"))

    state["last_seen"] = stamp
    if opts["unreadable"] is not None:
        state["last_error"] = opts["unreadable"]
    last, pending = state.get("last_state"), state.get("pending")

    if value == last and pending is None:
        save(path, state)
        print("NO-CHANGE %s %s" % (source, shown))
        return 0

    if value == last:
        # It changed, the report was never confirmed, and now it is back where it was.
        if pending != value:
            state["blip"] = state.get("pending_shown") or pending
            state["pending"], state["pending_shown"] = value, shown
        save(path, state)
        print("REPORT %s %s -> %s -> %s (changed and changed back before it was reported)"
              % (source, state.get("last_shown"), state.get("blip"), shown))
        return 0

    detail = ""
    if pending is not None and pending not in (value, last):
        detail = " (via %s, never reported)" % (state.get("pending_shown") or pending)
    state["pending"], state["pending_shown"], state["blip"] = value, shown, None
    if value == UNREADABLE:
        detail += " (%s)" % short(opts["unreadable"] or "")
    elif last == UNREADABLE:
        detail += " (readable again)"
    save(path, state)
    print("REPORT %s %s -> %s%s" % (source, state.get("last_shown"), shown, detail))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except OSError as e:
        fail("could not write the state file (%s); nothing recorded" % e)
