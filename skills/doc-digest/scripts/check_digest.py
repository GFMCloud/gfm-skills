#!/usr/bin/env python3
"""Check a digest (one notes file or a folder of knowledge files) against its source documents.

Usage: python3 check_digest.py <digest.md or folder> --source <file> [--source <file> ...]

Standard library only (Python 3.9+); uses extract.py from the same folder to read the sources.

Checks, each printed as "FAIL <file>:<line> ..." or "WARN ...":
  numbers   Every amount, percentage, date and other number of 10 or more (or with a decimal
            point, currency sign or percent sign) appears in the source text as written. Lines
            that contain "(computed" are skipped and counted, so a total the digest worked out
            itself must say so.
  refs      Page and slide references (p. 12, pages 3-5, slide 4) exist in the source.
  coverage  At least one file has a "Coverage:" line, and any "of N" in it matches the source's
            page or slide count.
  source    Every file has a "Source:" line.
  leftovers No TODO, TBD, placeholder or lorem ipsum text.
  unref     WARN when a number sits on a line with no page, slide or heading reference while
            the file cites locations elsewhere (notes should cite every fact).

Exit 0 when nothing failed, 1 when something failed, 2 when the inputs could not be read. Warnings
never fail the run. A pass means the numbers and references are consistent with the source text;
it does not mean the digest is complete or that its wording is faithful.
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract  # noqa: E402

NUM = re.compile(r"(?<![\w.])([£$€¥]?)(\d[\d,]*(?:\.\d+)?)(\s?%|p\b|k\b|m\b|bn\b)?")
# A range may follow any keyword; a comma or "and" list only a plural one ("pp. 4, 19", not "p. 4, 2026").
REF = re.compile(r"\b(pp\.|pages|slides|p\.|page|slide|sl\.)\s*(\d{1,4}(?:\s*(?:-|\u2013|to)\s*\d{1,4})?)"
                 r"((?:\s*(?:,|and|&)\s*\d{1,3}(?!,\d)(?:\s*(?:-|\u2013|to)\s*\d{1,3})?\b)*)", re.I)
PLURAL = ("pp.", "pages", "slides")
LOC_HEADER = re.compile(r"page|slide|where|section|source|location", re.I)
LEFTOVER = re.compile(r"\bTODO\b|\bTBD\b|\bFIXME\b|lorem ipsum|\[placeholder\]|\[insert ", re.I)
COMPUTED = re.compile(r"\(computed", re.I)
DATE = re.compile(r"(?<![\w.])(?:\d{4}-\d{1,2}-\d{1,2}|\d{1,2}[/.]\d{1,2}[/.]\d{2,4})(?![\w])")
SOURCE_LINE = re.compile(r"^\W*source[s]?\W*:", re.I)
COVERAGE_LINE = re.compile(r"^\W*coverage\W*:", re.I)


def norm_number(s):
    return s.replace(",", "")


def source_numbers(text):
    """Set of number strings in the source, with thousands separators removed."""
    found = set()
    for m in re.finditer(r"\d[\d,]*(?:\.\d+)?", text):
        n = norm_number(m.group(0)).rstrip(".")
        found.add(n)
        if "." in n:
            found.update(n.split("."))
    return found



def ref_matches(line):
    """(kind, numbers, span) for each page or slide reference. A list after a singular keyword
    ("slide 4, 2026 figures") ends at the first number, so what follows is checked as a fact."""
    out = []
    for m in REF.finditer(line):
        plural = m.group(1).lower() in PLURAL
        text = m.group(2) + (m.group(3) if plural else "")
        end = m.end() if plural else m.end(2)
        kind = "slide" if m.group(1).lower().startswith(("slide", "sl")) else "page"
        out.append((kind, [int(x) for x in re.findall(r"\d+", text)], (m.start(), end)))
    return out


def ref_spans(line):
    """Character spans of page/slide references, so their numbers are not checked as facts."""
    return [span for _, _, span in ref_matches(line)]


def in_spans(pos, spans):
    return any(a <= pos < b for a, b in spans)


def digest_files(path):
    if os.path.isfile(path):
        return [path]
    out = []
    for dp, dirs, fs in os.walk(path):
        dirs[:] = sorted(d for d in dirs if not d.startswith("."))
        out += [os.path.join(dp, f) for f in sorted(fs) if f.lower().endswith((".md", ".markdown", ".txt"))]
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="Check a digest against its source documents.")
    ap.add_argument("digest", help="a notes file, or a folder of knowledge files")
    ap.add_argument("--source", action="append", required=True, help="a source document (repeat for several)")
    a = ap.parse_args(argv)

    files = digest_files(a.digest)
    if not files:
        print(f"check: no .md or .txt files at {a.digest}", file=sys.stderr)
        return 2

    texts, counts, notes = [], {"page": 0, "slide": 0}, []
    all_counts = set()
    for src in a.source:
        try:
            res = extract.extract(src)
        except extract.ExtractError as e:
            print(f"check: could not read source {src}: {e}", file=sys.stderr)
            return 2
        texts.append("\n".join(body for _, body in res.parts))   # bodies only: markers are not facts
        n = sum(1 for label, _ in res.parts if label.startswith(("page ", "slide ")) and "notes" not in label)
        if n:
            counts[res.unit] = max(counts.get(res.unit, 0), n)
            all_counts.add(n)
        notes.append(f"{os.path.basename(src)}: " + (f"{n} {res.unit}s" if n else "no pages") + f", method={res.method}")
    src_text = "\n".join(texts)
    known = source_numbers(src_text)
    weak = len(re.sub(r"\s", "", src_text)) < 200

    fails, warns, computed_lines, checked = [], [], 0, 0
    has_coverage = False
    for path in files:
        rel = os.path.relpath(path, a.digest) if os.path.isdir(a.digest) else os.path.basename(path)
        try:
            with open(path, encoding="utf-8") as f:
                lines = f.read().splitlines()
        except (OSError, UnicodeDecodeError) as e:
            fails.append(f"FAIL {rel}: could not read ({e})")
            continue
        if not any(SOURCE_LINE.match(l) for l in lines):
            fails.append(f"FAIL {rel}: no 'Source:' line (say which document and pages this file comes from)")
        file_cites = any(ref_spans(l) for l in lines)
        heading_ref = False
        in_code = False
        table_header = None
        for i, line in enumerate(lines, 1):
            if line.lstrip().startswith("|"):
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                nxt = lines[i] if i < len(lines) else ""
                if table_header is None and re.match(r"^\s*\|[\s:|-]+\|?\s*$", nxt):
                    table_header = cells
                    continue
                if re.match(r"^\s*\|[\s:|-]+\|?\s*$", line):
                    continue
                if table_header is None:
                    table_header = []
            else:
                table_header = None
            if line.lstrip().startswith("```"):
                in_code = not in_code
                continue
            if in_code:
                continue
            if line.lstrip().startswith("#"):
                heading_ref = bool(ref_spans(line))
            if LEFTOVER.search(line):
                fails.append(f"FAIL {rel}:{i}: leftover placeholder text")
            if COVERAGE_LINE.match(line):
                has_coverage = True
                for m in re.finditer(r"\bof\s+(\d+)\b", line):
                    if all_counts and int(m.group(1)) not in all_counts:
                        have = ", ".join(f"{v} {k}s" for k, v in counts.items() if v)
                        fails.append(f"FAIL {rel}:{i}: Coverage says of {m.group(1)}, the source has {have}")
            for kind, nums, _ in ref_matches(line):
                limit = counts[kind]
                for g in nums:
                    if limit and g > limit:
                        fails.append(f"FAIL {rel}:{i}: reference to {kind} {g}, the source has {limit} {kind}s")
                    elif not limit:
                        warns.append(f"WARN {rel}:{i}: {kind} reference, but no source has {kind}s; cite headings or the right unit")
                        break
            if COMPUTED.search(line):
                computed_lines += 1
                continue
            if SOURCE_LINE.match(line) or COVERAGE_LINE.match(line) or re.match(r"^\W*check\W*:", line, re.I):
                continue
            body = line
            if table_header is not None and line.lstrip().startswith("|"):
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                body = "|".join(c for k, c in enumerate(cells)
                                if not (k < len(table_header) and LOC_HEADER.search(table_header[k])))
            body = re.sub(r"\]\([^)]*\)", "]", body)                     # link targets
            body = re.sub(r"`[^`]*`", "", body)                            # inline code, file names
            body = re.sub(r"^\s*(?:[-*+]|\d+[.)])\s+", "", body)          # list markers
            body = re.sub(r"\b\d{2}-[a-z][\w-]*\.md\b", "", body)          # 00-index.md style names
            spans = ref_spans(body)
            line_numbers = []
            for m in DATE.finditer(body):
                spans.append(m.span())
                checked += 1
                line_numbers.append(m.group(0))
                if m.group(0) not in src_text:
                    fails.append(f"FAIL {rel}:{i}: date {m.group(0)} is not in the source in that form (write dates as the source does)")
            for m in NUM.finditer(body):
                if in_spans(m.start(2), spans):
                    continue
                cur, raw, suffix = m.group(1), m.group(2), (m.group(3) or "").strip()
                raw = raw.rstrip(",")
                n = norm_number(raw).rstrip(".")
                if not n:
                    continue
                plain_small = not cur and not suffix and "." not in n and len(n) < 2
                if plain_small:
                    continue
                if suffix in ("k", "m", "bn") and m.group(0).strip().lower() not in src_text.lower():
                    fails.append(f"FAIL {rel}:{i}: '{m.group(0).strip()}' is not in the source in that form; give the number as the source writes it")
                    continue
                if suffix in ("k", "m", "bn"):
                    checked += 1
                    continue
                checked += 1
                line_numbers.append(n)
                if n not in known:
                    fails.append(f"FAIL {rel}:{i}: {m.group(0).strip()} is not in the source (copy numbers and dates exactly, or mark a worked-out value '(computed)')")
            if line_numbers and file_cites and not spans and not heading_ref and not line.lstrip().startswith(("|", "#")):
                warns.append(f"WARN {rel}:{i}: numbers with no page or slide reference on the line or its heading")
    if not has_coverage:
        fails.append("FAIL: no 'Coverage:' line in any file (say which pages or slides were read, of how many)")

    fails = list(dict.fromkeys(fails))
    warns = list(dict.fromkeys(warns))
    for line in fails + warns:
        print(line)
    if weak:
        print("note: the source gave almost no text, so the numbers check proves little; say so")
    print(f"check: {len(files)} file(s); {checked} numbers checked, {computed_lines} computed line(s) skipped; "
          f"{len(fails)} fail, {len(warns)} warn; " + "; ".join(notes))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
