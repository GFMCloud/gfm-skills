#!/usr/bin/env python3
"""Match records that mean the same thing, across two files or within one.

Standard library only (Python 3.9+). Reads CSV, TSV or XLSX and never changes its inputs.

  match.py --columns FILE                      column names and counts, no values
  match.py LEFT RIGHT --name COL[=COL] [...]   link LEFT records to RIGHT records
  match.py FILE --name COL [...]               find records listed twice in one file
  match.py --verify OUTDIR                     rerun a past run and compare its outputs

Options for a run:
  --name L[=R]       column holding the name to compare (required)
  --key L[=R]        each record's own ID column (default: spreadsheet row number)
  --id L[=R]         identifier with one value per thing (tax number, account number): equal values
                     match, different values never match; repeat for more, tried in order
  --contact L[=R]    contact detail (email, phone): equal values match unless the names differ;
                     different values say nothing, since one person can have several
  --must-agree L[=R] a fact that never changes (date of birth): different values never match
  --known FILE       earlier answers: a mapping.csv, a filled review.csv, or alias,canonical[,decision]
                     rows; an answer naming both records' keys outranks even an identifier match
  --drop-words LIST  comma list of words to ignore when comparing names (ltd,inc,the)
  --swap-comma       read "Smith, Ada" as "Ada Smith"
  --accept X --reject Y   fuzzy limits, 0 to 1; without both, fuzzy candidates only go to review
  --set-by WHO       who chose the limits: user or agent (recorded in run.json)
  --margin X         top two fuzzy scores closer than this are ambiguous (default 0.03)
  --floor X          lowest score listed when no limits are set (default 0.6)
  --sheet NAME       sheet to read from XLSX files (default: the first)
  --out DIR          output folder (default: matching); refuses a folder that has files in it
  --force            write into a folder that already holds an earlier run
"""
import argparse
import csv
import datetime
import difflib
import hashlib
import io
import json
import os
import re
import shutil
import sys
import tempfile
import unicodedata
import zipfile
from collections import Counter, defaultdict
from xml.etree import ElementTree as ET

VERSION = "1"
PLACEHOLDERS = {"", "n/a", "na", "none", "null", "nil", "-", "--", "0", "unknown", "tbc", "tbd", "?", "x"}
NAME_CHECK = 0.6          # an identifier match whose names score below this gets a flag
FULL_COMPARE_LIMIT = 1_000_000
M = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
R_ID = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"


def die(msg):
    print(f"match.py: {msg}", file=sys.stderr)
    sys.exit(2)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            h.update(block)
    return h.hexdigest()


# ---------- reading ----------

def col_index(ref):
    n = 0
    for ch in ref:
        if not ch.isalpha():
            break
        n = n * 26 + (ord(ch.upper()) - 64)
    return n - 1


DATE_FORMATS = set(range(14, 18)) | {22}
TIME_FORMATS = set(range(18, 22)) | {45, 46, 47}


def date_styles(z, names):
    """Style index -> 'date', 'datetime' or 'time', for cells whose number format shows a date or time."""
    if "xl/styles.xml" not in names:
        return {}
    root = parse_part(z, "xl/styles.xml")
    custom = {}
    for nf in root.iter(f"{M}numFmt"):
        code = re.sub(r'"[^"]*"|\\.|\[[^\]]*\]', "", nf.get("formatCode", "")).lower()
        has_date, has_time = bool(re.search(r"[dy]|m{3,}", code)), bool(re.search(r"[hs]", code))
        if has_date or has_time:
            custom[int(nf.get("numFmtId"))] = ("datetime" if has_time else "date") if has_date else "time"
    xfs = root.find(f"{M}cellXfs")
    out = {}
    for i, xf in enumerate(xfs.findall(f"{M}xf") if xfs is not None else []):
        fid = int(xf.get("numFmtId", "0"))
        kind = custom.get(fid) or ("date" if fid in DATE_FORMATS else "time" if fid in TIME_FORMATS else None)
        if kind:
            out[i] = kind
    return out


def serial_to_text(v, kind):
    days = float(v)
    when = datetime.datetime(1899, 12, 30) + datetime.timedelta(days=days)
    if kind == "time":
        return when.strftime("%H:%M:%S")
    if kind == "datetime" and days % 1:
        return when.strftime("%Y-%m-%dT%H:%M:%S")
    return when.strftime("%Y-%m-%d")


def parse_part(z, name):
    data = z.read(name)
    if b"<!DOCTYPE" in data[:4096] or b"<!ENTITY" in data:
        die(f"{name} in the workbook declares XML entities; refusing to read it")
    return ET.fromstring(data)


def read_xlsx(path, sheet):
    try:
        z = zipfile.ZipFile(path)
    except zipfile.BadZipFile:
        die(f"{path} is not a readable .xlsx file (an old .xls? save it as .xlsx or CSV)")
    try:
        with z:
            names = set(z.namelist())
            shared = []
            if "xl/sharedStrings.xml" in names:
                for si in parse_part(z, "xl/sharedStrings.xml").findall(f"{M}si"):
                    shared.append("".join(t.text or "" for t in si.iter(f"{M}t")))
            styles = date_styles(z, names)
            sheets = [(s.get("name"), s.get(R_ID)) for s in parse_part(z, "xl/workbook.xml").iter(f"{M}sheet")]
            rels = {r.get("Id"): r.get("Target") for r in parse_part(z, "xl/_rels/workbook.xml.rels")}
            pick = sheets[0] if sheet is None else next((s for s in sheets if s[0] == sheet), None)
            if pick is None:
                die(f"{path} has no sheet named {sheet!r}; sheets: {', '.join(s[0] for s in sheets)}")
            target = rels[pick[1]]
            part = target.lstrip("/") if target.startswith("/") else "xl/" + target
            rows, dates = [], 0
            for n, row in enumerate(parse_part(z, part).iter(f"{M}row"), start=1):
                rownum = int(row.get("r")) if row.get("r") else n
                cells = {}
                for i, c in enumerate(row.findall(f"{M}c")):
                    idx = col_index(c.get("r")) if c.get("r") else i
                    kind, v = c.get("t"), c.find(f"{M}v")
                    if kind == "s":
                        val = shared[int(v.text)] if v is not None and v.text else ""
                    elif kind == "inlineStr":
                        val = "".join(t.text or "" for t in c.iter(f"{M}t"))
                    else:
                        val = v.text if v is not None and v.text else ""
                        style = styles.get(int(c.get("s", "0")))
                        if val and style and kind in (None, "n"):
                            val, dates = serial_to_text(val, style), dates + 1
                    cells[idx] = val
                if cells:
                    rows.append((rownum, [cells.get(i, "") for i in range(max(cells) + 1)]))
    except (KeyError, IndexError, ValueError, ET.ParseError, zipfile.BadZipFile) as e:
        die(f"{path} could not be read as a workbook ({type(e).__name__}: {str(e)[:80]}); save it as CSV")
    return rows, f"xlsx sheet {pick[0]}" + (f", {dates} date cells read as dates" if dates else "")


def read_table(path, sheet=None):
    if not os.path.isfile(path):
        die(f"no such file: {path}")
    ext = os.path.splitext(path)[1].lower()
    if ext in (".xlsx", ".xlsm"):
        rows, how = read_xlsx(path, sheet)
    else:
        raw = open(path, "rb").read()
        if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
            try:
                text, how = raw.decode("utf-16"), "utf-16"
            except UnicodeDecodeError:
                die(f"{path} starts like UTF-16 but does not decode; save it as UTF-8 CSV")
        else:
            try:
                text, how = raw.decode("utf-8-sig"), "utf-8"
            except UnicodeDecodeError:
                text, how = raw.decode("cp1252", errors="replace"), "cp1252 (not valid UTF-8)"
        if "\x00" in text:
            die(f"{path} holds NUL characters (a binary file, or an unusual encoding); save it as UTF-8 CSV")
        if ext in (".tsv", ".tab"):
            delim = "\t"
        else:
            try:
                delim = csv.Sniffer().sniff(text[:4096], delimiters=",;\t|").delimiter
            except csv.Error:
                delim = ","
        try:
            rows = list(enumerate(csv.reader(io.StringIO(text, newline=""), delimiter=delim), start=1))
        except csv.Error as e:
            die(f"{path} is not readable as CSV ({e})")
    # row numbers are counted before blank rows are dropped, so they match the spreadsheet
    rows = [(n, r) for n, r in rows if any(c.strip() for c in r)]
    if not rows:
        die(f"{path} has no rows")
    header = [h.strip() for h in rows[0][1]]
    dupes = sorted({h for h in header if header.count(h) > 1})
    if dupes:
        die(f"{path} repeats column names: {', '.join(dupes)}")
    long_rows = sum(1 for _, r in rows[1:] if len(r) > len(header))
    records = []
    for n, r in rows[1:]:
        rec = dict(zip(header, list(r) + [""] * (len(header) - len(r))))
        rec["__row"] = n
        records.append(rec)
    return header, records, how, long_rows


# ---------- normalising and scoring ----------

def norm_name(s, drop, swap_comma):
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(ch for ch in s if not unicodedata.combining(ch)).casefold()
    if swap_comma and s.count(",") == 1:
        last, first = s.split(",")
        s = f"{first} {last}"
    s = s.replace("&", " and ")
    s = re.sub(r"['’`]", "", s)
    s = re.sub(r"[^\w\s]|_", " ", s)
    return " ".join(t for t in s.split() if t not in drop)


def norm_id(s):
    """Emails keep their punctuation; other identifiers (tax numbers, phones) keep letters and digits only."""
    v = re.sub(r"\s+", "", s or "").casefold()
    bare = re.sub(r"[\W_]", "", v)
    # placeholders: n/a, none, 0, 000, xxx, 9999 and the like
    if bare in PLACEHOLDERS or set(bare) <= {"0"} or set(bare) == {"x"} or (len(bare) >= 4 and len(set(bare)) == 1):
        return ""
    return v if "@" in v else bare


def score(a, b):
    if not a or not b:
        return 0.0
    r = difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()
    sa, sb = " ".join(sorted(a.split())), " ".join(sorted(b.split()))
    if (sa, sb) != (a, b):
        r = max(r, difflib.SequenceMatcher(None, sa, sb, autojunk=False).ratio())
    return round(r, 3)


def may_reach(a, b, floor):
    if not a or not b:
        return False
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    return sm.real_quick_ratio() >= floor and sm.quick_ratio() >= floor


def block_keys(n):
    return {t[:2] for t in n.split()}


# ---------- config ----------

def split_spec(spec):
    left, _, right = spec.partition("=")
    return [left.strip(), (right.strip() or left.strip())]


def kind(cfg, i):
    return cfg["ids"][i][2]


def conflicting(cfg, x, y):
    """Columns where both records have a value, the values differ, and that means different things."""
    return [cfg["ids"][i][0] for i in range(len(cfg["ids"]))
            if kind(cfg, i) in ("id", "must-agree") and x["ids"][i] and y["ids"][i] and x["ids"][i] != y["ids"][i]]


def build_records(path, cfg, side):
    header, rows, how, long_rows = read_table(path, cfg["sheet"])
    pick = 0 if side == "left" else 1
    name_col = cfg["name"][pick]
    key_col = cfg["key"][pick] if cfg["key"] else None
    id_cols = [c[pick] for c in cfg["ids"]]
    for col in [name_col] + id_cols + ([key_col] if key_col else []):
        if col not in header:
            die(f"{path} has no column {col!r}; columns: {', '.join(header)}")
    drop = set(cfg["drop_words"])
    recs = []
    for r in rows:
        key = r[key_col].strip() if key_col else f"row{r['__row']}"
        recs.append({"key": key, "name": r[name_col].strip(),
                     "norm": norm_name(r[name_col], drop, cfg["swap_comma"]),
                     "ids": [norm_id(r[c]) for c in id_cols]})
    keys = [x["key"] for x in recs]
    if key_col and not all(keys):
        die(f"{path}: key column {key_col!r} is blank on {keys.count('')} rows; leave out --key to use row numbers")
    if len(set(keys)) != len(keys):
        blank = sum(1 for k in keys if not k)
        die(f"{path}: key column {key_col!r} is not unique ({len(keys) - len(set(keys))} repeats"
            f"{f', {blank} blank' if blank else ''}); leave out --key to use row numbers")
    info = {"path": path, "sha256": sha256(path), "rows": len(recs), "read_as": how}
    if long_rows:
        info["rows_longer_than_header"] = long_rows
    return recs, info


def load_known(paths, cfg):
    """Earlier answers.

    names: normalised name -> {right key or group label: same|different}
    pairs: (key, key) -> (decision, normalised names or None). Record keys can be reused for other
    records in a later export (row numbers are), so a pair answer that carries names applies only
    while the records still have those names. Key-level answers come from a filled review.csv or a
    mapping.csv (left_key,right_key) and from a duplicates review.csv (key_a,key_b).
    """
    names, pairs = defaultdict(dict), {}
    drop = set(cfg["drop_words"])
    for path in paths:
        header, rows, _, _ = read_table(path)
        h = set(header)
        has_decision = "decision" in h
        if {"key_a", "key_b"} <= h:
            shape = "pair"
        elif {"left_key", "right_key", "left_name"} <= h:
            shape, a_col, c_col = "both", "left_name", "right_key"
        elif {"alias", "canonical"} <= h:
            shape, a_col, c_col = "name", "alias", "canonical"
        elif {"left_name", "right_key"} <= h:
            shape, a_col, c_col = "name", "left_name", "right_key"
        else:
            die(f"{path}: known-answers file needs columns alias,canonical or left_name,right_key "
                f"or key_a,key_b,decision; it has {', '.join(header)}")
        for r in rows:
            d = r.get("decision", "").strip().casefold() if has_decision else "same"
            if d == "":
                continue
            if d not in ("same", "different"):
                die(f"{path} row {r['__row']}: decision must be same, different or blank, not {d!r}")
            nn = lambda col: norm_name(r[col], drop, cfg["swap_comma"]) if col in r else None
            if shape == "pair":
                a, b = r["key_a"].strip(), r["key_b"].strip()
                na, nb = nn("name_a"), nn("name_b")
                if a and b:
                    pairs[(a, b) if a <= b else (b, a)] = (d, None if na is None or nb is None
                                                           else tuple(sorted((na, nb))))
                continue
            target, alias = r[c_col].strip(), nn(a_col)
            if not target or target.upper() == "UNRESOLVED":
                continue
            if shape == "both" and r["left_key"].strip():
                pairs[("L:" + r["left_key"].strip(), target)] = (d, alias)
            if alias:  # a blank name would otherwise match every record with no name
                names[alias][target] = d
    return names, pairs


# ---------- linking two files ----------

def link(L, R, cfg, known_names, known_pairs):
    accept, reject = cfg["accept"], cfg["reject"]
    limits = accept is not None
    floor = reject if limits else cfg["floor"]
    by_key = {r["key"]: r for r in R}
    by_norm, by_id = defaultdict(list), [defaultdict(list) for _ in cfg["ids"]]
    for r in R:
        if r["norm"]:
            by_norm[r["norm"]].append(r)
        for i, v in enumerate(r["ids"]):
            if v:
                by_id[i][v].append(r)
    blocking = len(L) * len(R) > FULL_COMPARE_LIMIT
    by_block = defaultdict(list)
    if blocking:
        for r in R:
            for k in block_keys(r["norm"]):
                by_block[k].append(r)
    compared = 0
    out = []

    def conflict(l, r):
        return conflicting(cfg, l, r)

    def key_answer(l, r):
        d = known_pairs.get(("L:" + l["key"], r["key"]))
        return d[0] if d and (d[1] is None or d[1] == l["norm"]) else None

    def different(l, r):
        return known_names.get(l["norm"], {}).get(r["key"]) == "different" or key_answer(l, r) == "different"

    for l in L:
        res = {"l": l, "status": None, "r": None, "rule": "", "score": "", "flag": "", "reason": "", "cands": []}
        out.append(res)
        # 1. identifier or contact detail
        for i, v in enumerate(l["ids"]):
            if not v or kind(cfg, i) == "must-agree":
                continue
            # an answer for this exact pair of records outranks an identifier (a wrong number)
            hits = [r for r in by_id[i].get(v, []) if not conflict(l, r) and key_answer(l, r) != "different"]
            col = cfg["ids"][i][0]
            if len(hits) == 1:
                r = hits[0]
                flags = []
                s = score(l["norm"], r["norm"])
                names_differ = l["norm"] and r["norm"] and s < NAME_CHECK
                if names_differ and kind(cfg, i) == "contact":
                    res.update(status="review", reason=f"same {col} but names differ ({s})", cands=[(r, s)])
                    break
                if names_differ:
                    flags.append(f"names differ ({s})")
                res.update(status="matched", r=r, rule=f"{kind(cfg, i)}:{col}", flag="; ".join([f for f in [res["flag"]] + flags if f]))
                break
            if len(hits) > 1 and kind(cfg, i) == "contact":
                # a shared mailbox (an office, a bookkeeper) can't tell records apart; fall through to names
                res["flag"] = f"{col} shared by {len(hits)} right records: not used"
                continue
            if len(hits) > 1:
                res.update(status="review", reason=f"{len(hits)} right records share this {col}",
                           cands=[(r, score(l["norm"], r["norm"])) for r in hits])
                break
        if res["status"]:
            continue
        ok = lambda r: not conflict(l, r) and not different(l, r)
        # 2. normalised name
        same_name = by_norm.get(l["norm"], []) if l["norm"] else []
        hits = [r for r in same_name if ok(r)]
        if len(hits) == 1:
            res.update(status="matched", r=hits[0], rule="normalised")
            continue
        if len(hits) > 1:
            res.update(status="review", reason=f"{len(hits)} right records have this name", cands=[(r, 1.0) for r in hits])
            continue
        clash = [(r, conflict(l, r)) for r in same_name if conflict(l, r)]
        # 3. known answers
        same = {k for k, d in known_names.get(l["norm"], {}).items() if d == "same"}
        same |= {rk for (lk, rk), _ in known_pairs.items() if lk == "L:" + l["key"] and rk in by_key
                 and key_answer(l, by_key[rk]) == "same"}
        hits = [by_key[k] for k in sorted(same) if k in by_key and not conflict(l, by_key[k])
                and key_answer(l, by_key[k]) != "different"]
        if len(hits) == 1:
            res.update(status="matched", r=hits[0], rule="known")
            continue
        if len(hits) > 1:
            res.update(status="review", reason="known answers point to several records",
                       cands=[(r, score(l["norm"], r["norm"])) for r in hits])
            continue
        # 4. fuzzy
        pool = R
        if blocking:
            seen = {}
            for k in block_keys(l["norm"]):
                for r in by_block.get(k, []):
                    seen[r["key"]] = r
            pool = [seen[k] for k in sorted(seen)]
        cands = []
        for r in pool:
            if not ok(r) or not may_reach(l["norm"], r["norm"], floor):
                continue
            compared += 1
            s = score(l["norm"], r["norm"])
            if s >= floor:
                cands.append((r, s))
        cands.sort(key=lambda c: (-c[1], c[0]["key"]))
        clash_note = "; ".join([f"same name as {r['key']} but {', '.join(cols)} differs" for r, cols in clash]
                               + [f"known different from {k}" for k, d in sorted(known_names.get(l["norm"], {}).items())
                                  if d == "different" and k in by_key])
        if not cands:
            res.update(status="unmatched", reason="; ".join(x for x in [f"no candidate scored {floor} or more", clash_note] if x))
            continue
        top = cands[:3]
        if not limits:
            res.update(status="review", reason="fuzzy candidate; limits not set", cands=top)
        elif cands[0][1] >= accept:
            if len(cands) > 1 and cands[0][1] - cands[1][1] < cfg["margin"]:
                res.update(status="review", reason=f"ambiguous: top two within {cfg['margin']}", cands=top)
            else:
                res.update(status="matched", r=cands[0][0], rule="fuzzy", score=cands[0][1])
        else:
            res.update(status="review", reason="between reject and accept", cands=top)
        if clash_note and res["status"] != "matched":
            res["reason"] += "; " + clash_note
    return out, {"blocking": blocking, "fuzzy_pairs_scored": compared}


def cell(v):
    """Stop a spreadsheet from running a name that starts like a formula."""
    if isinstance(v, str) and v[:1] in ("=", "+", "-", "@", "\t", "\r") and not re.fullmatch(r"-?[\d.]+", v):
        return "'" + v
    return v


def write_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        w.writerows([cell(v) for v in row] for row in rows)


def write_link(outdir, out, R):
    mapping, review, unmatched = [], [], []
    used = set()
    for x in out:
        l = x["l"]
        if x["status"] == "matched":
            used.add(x["r"]["key"])
            mapping.append([l["key"], l["name"], x["r"]["key"], x["r"]["name"], x["rule"], x["score"], x["flag"]])
        elif x["status"] == "review":
            why = "; ".join(f for f in [x["reason"], x["flag"]] if f)
            for r, s in x["cands"]:
                review.append([l["key"], l["name"], r["key"], r["name"], s, why, ""])
        else:
            unmatched.append([l["key"], l["name"], "; ".join(f for f in [x["reason"], x["flag"]] if f)])
    in_review = {r["key"] for x in out if x["status"] == "review" for r, _ in x["cands"]}
    unused = [[r["key"], r["name"], "yes" if r["key"] in in_review else ""] for r in R if r["key"] not in used]
    write_csv(os.path.join(outdir, "mapping.csv"),
              ["left_key", "left_name", "right_key", "right_name", "rule", "score", "flag"], mapping)
    write_csv(os.path.join(outdir, "review.csv"),
              ["left_key", "left_name", "right_key", "right_name", "score", "reason", "decision"], review)
    write_csv(os.path.join(outdir, "unmatched.csv"), ["left_key", "left_name", "reason"], unmatched)
    write_csv(os.path.join(outdir, "right-unused.csv"), ["right_key", "right_name", "in_review"], unused)
    counts = defaultdict(int)
    for x in out:
        counts[x["status"]] += 1
    rules = defaultdict(int)
    for x in out:
        if x["status"] == "matched":
            rules[x["rule"]] += 1
    flagged = sum(1 for x in out if x["flag"])
    return {"left_in": len(out), "matched": counts["matched"], "review": counts["review"],
            "unmatched": counts["unmatched"], "by_rule": dict(sorted(rules.items())), "flagged": flagged,
            "right_in": len(R), "right_unused": len(unused), "right_unused_in_review": sum(1 for u in unused if u[2]),
            "right_used_more_than_once": sum(1 for c in Counter(x["r"]["key"] for x in out
                                                                if x["status"] == "matched").values() if c > 1)}, \
        ["mapping.csv", "review.csv", "unmatched.csv", "right-unused.csv"]


# ---------- finding records listed twice ----------

def dedupe(recs, cfg, known_names, known_pairs):
    accept, reject = cfg["accept"], cfg["reject"]
    limits = accept is not None
    floor = reject if limits else cfg["floor"]
    n = len(recs)
    idx = {r["key"]: i for i, r in enumerate(recs)}
    edges, review = {}, {}
    blocked, pair_same = set(), []
    for (a, b), (d, names) in known_pairs.items():
        if a.startswith("L:") or a not in idx or b not in idx or a == b:
            continue
        i, j = sorted((idx[a], idx[b]))
        if names is not None and names != tuple(sorted((recs[i]["norm"], recs[j]["norm"]))):
            continue  # those keys now belong to records with other names
        if d == "different":
            blocked.add((i, j))
        else:
            pair_same.append((i, j))

    def conflict(i, j):
        return conflicting(cfg, recs[i], recs[j])

    def add(i, j, rule):
        p = (min(i, j), max(i, j))
        if p not in blocked and p not in edges:
            edges[p] = rule

    for c in range(len(cfg["ids"])):
        if kind(cfg, c) == "must-agree":
            continue
        groups = defaultdict(list)
        for i, r in enumerate(recs):
            if r["ids"][c]:
                groups[r["ids"][c]].append(i)
        col = cfg["ids"][c][0]
        for members in groups.values():
            for a in range(len(members)):
                for b in range(a + 1, len(members)):
                    i, j = members[a], members[b]
                    cols = conflict(i, j)
                    if cols:
                        review.setdefault((i, j), f"same {col} but {', '.join(cols)} differs: kept apart")
                        continue
                    s = score(recs[i]["norm"], recs[j]["norm"])
                    if kind(cfg, c) == "contact" and recs[i]["norm"] and recs[j]["norm"] and s < NAME_CHECK:
                        review.setdefault((i, j), f"same {col} but names differ ({s})")
                    else:
                        add(i, j, f"{kind(cfg, c)}:{col}")
    groups = defaultdict(list)
    for i, r in enumerate(recs):
        if r["norm"]:
            groups[r["norm"]].append(i)
    for members in groups.values():
        for a in range(len(members)):
            for b in range(a + 1, len(members)):
                i, j = members[a], members[b]
                cols = conflict(i, j)
                if cols:
                    review.setdefault((i, j), f"same name but {', '.join(cols)} differs: kept apart")
                else:
                    add(i, j, "normalised")
    labels = defaultdict(list)
    for i, r in enumerate(recs):
        for label, d in sorted(known_names.get(r["norm"], {}).items()):
            if d == "same":
                labels[label].append(i)
    for members in labels.values():
        for a in range(len(members)):
            for b in range(a + 1, len(members)):
                if not conflict(members[a], members[b]):
                    add(members[a], members[b], "known")
    for i, j in pair_same:
        add(i, j, "known")
    blocking = n * (n - 1) // 2 > FULL_COMPARE_LIMIT
    if blocking:
        buckets = defaultdict(set)
        for i, r in enumerate(recs):
            for k in block_keys(r["norm"]):
                buckets[k].add(i)
        pairs = sorted({(a, b) for m in buckets.values() for a in m for b in m if a < b})
    else:
        pairs = ((a, b) for a in range(n) for b in range(a + 1, n))
    compared = 0
    scores = {}
    for a, b in pairs:
        if (a, b) in edges or (a, b) in blocked or (a, b) in review or conflict(a, b):
            continue
        if not may_reach(recs[a]["norm"], recs[b]["norm"], floor):
            continue
        compared += 1
        s = score(recs[a]["norm"], recs[b]["norm"])
        scores[(a, b)] = s
        if limits and s >= accept:
            add(a, b, "fuzzy")
        elif s >= floor:
            review[(a, b)] = "fuzzy candidate; limits not set" if not limits else "between reject and accept"
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in sorted(edges):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)
    clusters = defaultdict(list)
    for i in range(n):
        clusters[find(i)].append(i)
    status, group_of, flags = ["unique"] * n, {}, {}
    gnum = 0
    for root in sorted(clusters):
        m = clusters[root]
        if len(m) < 2:
            continue
        gnum += 1
        missing = [(a, b) for x, a in enumerate(m) for b in m[x + 1:] if (a, b) not in edges]
        for i in m:
            group_of[i] = f"G{gnum}"
        if missing:
            for i in m:
                status[i] = "review"
                flags[i] = f"chain: {len(missing)} pair(s) in this group do not match directly"
            for a, b in missing:
                if (a, b) not in review:
                    s = scores.get((a, b), score(recs[a]["norm"], recs[b]["norm"]))
                    why = ("known different" if (a, b) in blocked else f"{', '.join(conflict(a, b))} differs" if conflict(a, b)
                           else "no direct match")
                    review[(a, b)] = f"chain: links only through other records; {why} (score {s})"
        else:
            for i in m:
                status[i] = "merged"
                if len(m) > 2:
                    flags[i] = f"{len(m)} members: look before merging"
    for a, b in review:
        for i in (a, b):
            if status[i] == "unique":
                status[i] = "review"
    return {"status": status, "group_of": group_of, "flags": flags, "edges": edges, "review": review,
            "scores": scores}, {"blocking": blocking, "fuzzy_pairs_scored": compared}


def write_dedupe(outdir, recs, d):
    rows = []
    for i, r in enumerate(recs):
        if i in d["group_of"]:
            links = []
            for (a, b), rule in sorted(d["edges"].items()):
                if i in (a, b):
                    other = recs[b if a == i else a]["key"]
                    links.append(f"{other} {rule}" + (f" {d['scores'][(a, b)]}" if rule == "fuzzy" else ""))
            rows.append([d["group_of"][i], r["key"], r["name"], "; ".join(links), d["status"][i], d["flags"].get(i, "")])
    rows.sort(key=lambda x: (int(x[0][1:]), x[1]))
    write_csv(os.path.join(outdir, "groups.csv"), ["group", "key", "name", "links", "status", "flag"], rows)
    rev = []
    for (a, b), why in sorted(d["review"].items()):
        s = d["scores"].get((a, b), score(recs[a]["norm"], recs[b]["norm"]))
        rev.append([recs[a]["key"], recs[a]["name"], recs[b]["key"], recs[b]["name"], s, why, ""])
    write_csv(os.path.join(outdir, "review.csv"), ["key_a", "name_a", "key_b", "name_b", "score", "reason", "decision"], rev)
    st = d["status"]
    groups = {d["group_of"][i] for i in d["group_of"] if st[i] == "merged"}
    rules = defaultdict(int)
    for rule in d["edges"].values():
        rules[rule] += 1
    return {"records_in": len(recs), "merged": st.count("merged"), "review": st.count("review"),
            "unique": st.count("unique"), "merged_groups": len(groups),
            "review_groups": len({d["group_of"][i] for i in d["group_of"] if st[i] == "review"}),
            "links_by_rule": dict(sorted(rules.items()))}, ["groups.csv", "review.csv"]


# ---------- running ----------

def run(cfg, outdir, base):
    """base: folder that input paths in cfg are relative to."""
    p = lambda x: x if os.path.isabs(x) else os.path.normpath(os.path.join(base, x))
    known_names, known_pairs = load_known([p(k) for k in cfg["known"]], cfg)
    L, linfo = build_records(p(cfg["inputs"][0]), cfg, "left")
    inputs = [linfo]
    if len(cfg["inputs"]) == 2:
        R, rinfo = build_records(p(cfg["inputs"][1]), cfg, "right")
        inputs.append(rinfo)
        out, comp = link(L, R, cfg, known_names, known_pairs)
        counts, files = write_link(outdir, out, R)
        mode = "link"
        adds = counts["matched"] + counts["review"] + counts["unmatched"] == counts["left_in"]
    else:
        d, comp = dedupe(L, cfg, known_names, known_pairs)
        counts, files = write_dedupe(outdir, L, d)
        mode = "dedupe"
        adds = counts["merged"] + counts["review"] + counts["unique"] == counts["records_in"]
    counts["adds_up"] = adds
    return mode, inputs, counts, comp, files


def summary(mode, inputs, counts, comp, cfg, outdir, files):
    lines = []
    tick = "yes" if counts["adds_up"] else "NO"
    if mode == "link":
        lines.append(f"Records: {counts['left_in']} in ({os.path.basename(inputs[0]['path'])}), matched {counts['matched']}, "
                     f"to review {counts['review']}, unmatched {counts['unmatched']} (adds up: {tick})")
        lines.append("By rule: " + (", ".join(f"{k} {v}" for k, v in counts["by_rule"].items()) or "none")
                     + (f"; {counts['flagged']} matched with a flag" if counts["flagged"] else ""))
        lines.append(f"Other side: {counts['right_in']} in ({os.path.basename(inputs[1]['path'])}), "
                     f"{counts['right_unused']} not matched by any record ({counts['right_unused_in_review']} of them are review candidates), "
                     f"{counts['right_used_more_than_once']} matched by more than one record")
    else:
        lines.append(f"Records: {counts['records_in']} in ({os.path.basename(inputs[0]['path'])}), "
                     f"{counts['merged']} in {counts['merged_groups']} duplicate groups, to review {counts['review']}, "
                     f"unique {counts['unique']} (adds up: {tick})")
        lines.append("Links by rule: " + (", ".join(f"{k} {v}" for k, v in counts["links_by_rule"].items()) or "none"))
    if cfg["accept"] is not None:
        lines.append(f"Limits: accept {cfg['accept']}, reject {cfg['reject']} (set by {cfg['set_by'] or 'not recorded'})")
    else:
        lines.append(f"Limits: not set, so no fuzzy match was applied; candidates scoring {cfg['floor']} or more went to review")
    lines.append(("Compared: pairs sharing a two-letter word start (input too large for every pair); "
                  "a match with no such shared start is not found" if comp["blocking"] else "Compared: every pair")
                 + f"; {comp['fuzzy_pairs_scored']} fuzzy scores computed")
    lines.append("Wrote: " + ", ".join(os.path.join(outdir, f) for f in files + ["run.json"]))
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("files", nargs="*")
    ap.add_argument("-h", "--help", action="store_true")
    ap.add_argument("--columns", action="store_true")
    ap.add_argument("--verify")
    ap.add_argument("--name")
    ap.add_argument("--key")
    ap.add_argument("--id", action="append", default=[])
    ap.add_argument("--contact", action="append", default=[])
    ap.add_argument("--must-agree", action="append", default=[])
    ap.add_argument("--known", action="append", default=[])
    ap.add_argument("--drop-words", default="")
    ap.add_argument("--swap-comma", action="store_true")
    ap.add_argument("--accept", type=float)
    ap.add_argument("--reject", type=float)
    ap.add_argument("--set-by", choices=["user", "agent"])
    ap.add_argument("--margin", type=float, default=0.03)
    ap.add_argument("--floor", type=float, default=0.6)
    ap.add_argument("--sheet")
    ap.add_argument("--out", default="matching")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    if a.help:
        print(__doc__)
        return 0
    if a.verify:
        return verify(a.verify)
    if a.columns:
        if not a.files:
            die("--columns needs a file")
        for f in a.files:
            header, rows, how, _ = read_table(f, a.sheet)
            print(f"{f}: {len(rows)} rows, read as {how}")
            for h in header:
                vals = [r[h].strip() for r in rows]
                filled = [v for v in vals if v]
                print(f"  {h}: {len(filled)} filled, {len(set(filled))} distinct")
        return 0
    if len(a.files) not in (1, 2):
        die("give one file (find duplicates) or two (link LEFT to RIGHT); --help for usage")
    if not a.name:
        die("--name is required; run with --columns first to see the column names")
    if (a.accept is None) != (a.reject is None):
        die("give both --accept and --reject, or neither")
    if a.accept is not None:
        if not (0 <= a.reject <= a.accept <= 1):
            die("limits must satisfy 0 <= reject <= accept <= 1")
        if not a.set_by:
            die("say who chose the limits: --set-by user or --set-by agent")
        if a.set_by == "agent" and a.accept < 0.85:
            die("an accept limit below 0.85 needs the user's agreement (--set-by user)")
    for f in a.files + a.known:
        if os.path.abspath(f).startswith(os.path.abspath(a.out) + os.sep):
            die(f"{f} is inside the output folder {a.out}; pick another --out")
    if os.path.exists(a.out) and not os.path.isdir(a.out):
        die(f"{a.out} exists and is not a folder; pick another --out")
    if os.path.isdir(a.out) and os.listdir(a.out):
        old = os.path.join(a.out, "run.json")
        if not (a.force and os.path.isfile(old)):
            die(f"{a.out} already has files; use another --out, or --force to replace an earlier run there")
        try:
            stale = list(json.load(open(old, encoding="utf-8")).get("outputs", {})) + ["run.json"]
        except (ValueError, AttributeError):
            die(f"{old} is not a run.json this script wrote; use another --out")
        for f in stale:
            if os.path.basename(f) == f and os.path.isfile(os.path.join(a.out, f)):
                os.remove(os.path.join(a.out, f))
    os.makedirs(a.out, exist_ok=True)
    outdir = a.out
    rel = lambda f: os.path.relpath(os.path.abspath(f), os.path.abspath(outdir))
    cfg = {"inputs": [rel(f) for f in a.files], "known": [rel(k) for k in a.known],
           "name": split_spec(a.name), "key": split_spec(a.key) if a.key else None,
           "ids": [split_spec(i) + ["id"] for i in a.id] + [split_spec(i) + ["contact"] for i in a.contact]
           + [split_spec(i) + ["must-agree"] for i in a.must_agree],
           "drop_words": sorted({w.strip().casefold() for w in a.drop_words.split(",") if w.strip()}),
           "swap_comma": a.swap_comma, "accept": a.accept, "reject": a.reject, "set_by": a.set_by,
           "margin": a.margin, "floor": a.floor, "sheet": a.sheet}
    mode, inputs, counts, comp, files = run(cfg, outdir, outdir)
    for i, f in zip(inputs, a.files):
        i["path"] = rel(f)
    manifest = {"tool": "data-matching match.py", "version": VERSION, "mode": mode, "config": cfg,
                "inputs": inputs,
                "known_files": [{"path": k, "sha256": sha256(os.path.join(outdir, k))} for k in cfg["known"]],
                "normalisation": ["unicode NFKD, accents removed", "case folded", "& read as and",
                                  "apostrophes removed", "other punctuation read as a space", "spaces collapsed"]
                + (["'Last, First' read as 'First Last'"] if cfg["swap_comma"] else [])
                + ([f"words ignored: {', '.join(cfg['drop_words'])}"] if cfg["drop_words"] else []),
                "identifiers": "spaces removed, case folded; blank and placeholder values never match: "
                + ", ".join(sorted(v for v in PLACEHOLDERS if v)),
                "score": "difflib ratio on normalised names, best of as-written and words-sorted, 3 decimals",
                "comparison": comp, "counts": counts,
                "outputs": {f: sha256(os.path.join(outdir, f)) for f in files}}
    with open(os.path.join(outdir, "run.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")
    print(summary(mode, inputs, counts, comp, cfg, outdir, files))
    return 0 if counts["adds_up"] else 1


def verify(outdir):
    path = os.path.join(outdir, "run.json")
    if not os.path.isfile(path):
        die(f"no run.json in {outdir}")
    m = json.load(open(path, encoding="utf-8"))
    cfg = m["config"]
    changed = [i["path"] for i in m["inputs"] + m["known_files"]
               if not os.path.isfile(os.path.join(outdir, i["path"])) or sha256(os.path.join(outdir, i["path"])) != i["sha256"]]
    if changed:
        print(f"verify: inputs changed or missing since the run: {', '.join(changed)}; not comparable")
        return 1
    tmp = tempfile.mkdtemp(prefix="match-verify-")
    try:
        # inputs are stored relative to outdir; resolve them from there
        _, _, counts, _, files = run({**cfg, "inputs": [os.path.join(os.path.abspath(outdir), x) for x in cfg["inputs"]],
                                      "known": [os.path.join(os.path.abspath(outdir), x) for x in cfg["known"]]}, tmp, tmp)
        diff = [f for f in files if sha256(os.path.join(tmp, f)) != m["outputs"].get(f)]
        diff += [f for f in m["outputs"] if f not in files]
        edited = [f for f in m["outputs"] if f in files and os.path.isfile(os.path.join(outdir, f))
                  and sha256(os.path.join(outdir, f)) != m["outputs"][f]]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if edited:
        print(f"note: edited since the run: {', '.join(edited)} (expected if decisions were filled in)")
    if diff:
        print(f"verify: DIFFERENT: {', '.join(sorted(set(diff)))}")
        return 1
    print(f"verify: same output ({len(files)} files) from the same inputs; counts add up: {'yes' if counts['adds_up'] else 'NO'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
