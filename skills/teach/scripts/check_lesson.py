#!/usr/bin/env python3
"""Check one teach lesson file. Usage: check_lesson.py <lessons/NNNN-slug.html>

FAIL lines must be fixed; WARN lines are worth a look. Ends with PASS (exit 0) or FAIL (exit 1);
exit 2 for bad usage or an unreadable file.
Checks the shape only (sections, one primary source, practice, self-contained), not whether the
teaching is any good.
"""
import os
import re
import sys
from html.parser import HTMLParser

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
NEEDED = ("win", "practice", "source")


class Lesson(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.parts, self.external, self.primary = [], set(), [], []
        self.questions, self.words, self.prev_links = [], 0, []
        self.q = self.opt = None
        self.qstack, self.nested, self.has_score = [], False, False
        self.skip = self.code = 0
        self.css, self.scripts, self.refresh = [], [], []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        src = a.get("src") or (a.get("href") if tag == "link" else None)
        if tag in ("script", "img", "iframe", "video", "audio", "source", "embed", "link") and src \
                and not src.startswith("data:"):
            self.external.append(f"<{tag}> {src}")
        if tag == "object":
            self.external.append("<object>")
        if a.get("srcset") and not a["srcset"].startswith("data:"):
            self.external.append(f"<{tag}> srcset {a['srcset']}")
        ref = a.get("href") or a.get("xlink:href")
        if tag in ("image", "use", "feimage") and ref and not ref.startswith(("data:", "#")):
            self.external.append(f"<{tag}> {ref}")
        if tag == "meta" and (a.get("http-equiv") or "").lower() == "refresh":
            self.refresh.append(a.get("content", ""))
        if a.get("style"):
            self.css.append(a["style"])
        if a.get("id") == "score":
            self.has_score = True
        if "data-part" in a:
            self.parts.add(a["data-part"])
        if tag == "a" and "data-primary" in a:
            self.primary.append(a.get("href", ""))
        if tag == "a" and re.match(r"\d{4}-[\w-]+\.html$", a.get("href", "")):
            self.prev_links.append(a["href"])
        if "data-q" in a:
            if self.q is not None:
                self.nested = True
            self.q = {"recall": "data-recall" in a, "reveal": False, "opts": [], "part": self.part()}
            self.questions.append(self.q)
            self.qstack.append(self.q)
        if tag == "details" and self.q is not None:
            self.q["reveal"] = True
        if "data-opt" in a and self.q is not None:
            self.opt = {"correct": "data-correct" in a, "text": ""}
            self.q["opts"].append(self.opt)
        if tag in ("script", "style"):
            self.skip += 1
        if tag in ("pre", "table"):
            self.code += 1
        if tag not in VOID:
            self.stack.append((tag, a))

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.skip = max(0, self.skip - 1)
        if tag in ("pre", "table"):
            self.code = max(0, self.code - 1)
        if tag == "button":
            self.opt = None
        while self.stack:
            t, a = self.stack.pop()
            if "data-q" in a and self.qstack:
                self.qstack.pop()
                self.q = self.qstack[-1] if self.qstack else None
            if t == tag:
                break

    def handle_data(self, data):
        if self.skip:
            inner = self.stack[-1][0] if self.stack else ""
            (self.css if inner == "style" else self.scripts).append(data)
            return
        if not self.code:
            self.words += len(data.split())
        if self.opt is not None:
            self.opt["text"] += data

    def part(self):
        for _, a in reversed(self.stack):
            if "data-part" in a:
                return a["data-part"]
        return None


def main(path):
    try:
        text = open(path, encoding="utf-8", errors="replace").read()
    except OSError as e:
        print(f"ERROR cannot read {path}: {e.strerror}")
        return 2
    p = Lesson()
    p.feed(text)
    fails, warns = [], []
    m = re.match(r"(\d{4})-[a-z0-9-]+\.html$", os.path.basename(path))
    num = int(m.group(1)) if m else None
    if not m:
        fails.append("file name is not NNNN-slug.html (four digits, lowercase slug)")
    # Placeholders anywhere but code samples; CSS loads only in <style> and style="".
    outside_code = re.sub(r"<(pre|code)\b.*?</\1\s*>", "", text, flags=re.S | re.I)
    if "{{" in outside_code or "}}" in outside_code:
        fails.append("template placeholders left ({{...}})")
    for e in p.external:
        fails.append(f"not self-contained: {e}")
    for css in re.findall(r"@import[^;]*|url\((?!\s*['\"]?data:)[^)]*\)", "\n".join(p.css)):
        fails.append(f"not self-contained: {css.strip()}")
    for r in p.refresh:
        if "url=" in r.lower():
            fails.append(f"not self-contained: meta refresh to {r}")
    js = "\n".join(p.scripts)
    if re.search(r"\bimport\s*\(|\bfetch\s*\(|XMLHttpRequest|\.src\s*=|https?://", js):
        warns.append("inline script may load outside code (import(), fetch, .src= or a web address)")
    for need in NEEDED:
        if need not in p.parts:
            fails.append(f'missing section data-part="{need}"')
    if num == 1 and "warmup" in p.parts:
        warns.append("lesson 0001 has a warm-up section; there is nothing earlier to recall")
    if num and num >= 2:
        if "warmup" not in p.parts:
            fails.append('lesson 0002 on needs a warm-up (data-part="warmup") on earlier lessons')
        if not p.prev_links:
            warns.append("no link to an earlier lesson")
    if len(p.primary) != 1:
        fails.append(f"needs exactly one primary source link (data-primary), found {len(p.primary)}")
    elif not re.match(r"https?://", p.primary[0]):
        fails.append(f"primary source is not a web link: {p.primary[0]}")
    practice = [q for q in p.questions if q["part"] == "practice"]
    if len(practice) < 2:
        fails.append(f"practice needs at least 2 questions (data-q), found {len(practice)}")
    if not any(q["recall"] for q in practice):
        fails.append("practice has no recall question (data-recall): answer before reveal")
    if p.nested:
        fails.append("a question (data-q) sits inside another question; keep them side by side")
    for q in p.questions:
        if q["recall"] and not q["reveal"]:
            fails.append("a recall question has no <details> reveal: the answer must stay hidden until asked for")
    if p.questions and not p.has_score:
        fails.append('questions but no score line (id="score"): the learner has nothing to bring back')
    mcs = [q for q in p.questions if q["opts"]]
    for i, q in enumerate(mcs, 1):
        right = [o for o in q["opts"] if o["correct"]]
        if len(right) != 1:
            fails.append(f"multiple-choice question {i} has {len(right)} correct options, needs 1")
            continue
        lens = [len(o["text"].strip()) for o in q["opts"]]
        r = len(right[0]["text"].strip())
        others = [n for o, n in zip(q["opts"], lens) if not o["correct"]]
        if others and r > 1.3 * max(others) and r - max(others) > 5:
            warns.append(f"multiple-choice question {i}: the right option is clearly the longest")
    positions = [next(i for i, o in enumerate(q["opts"]) if o["correct"]) for q in mcs
                 if sum(o["correct"] for o in q["opts"]) == 1]
    if len(positions) >= 3 and len(set(positions)) == 1:
        warns.append("the right option is in the same position in every multiple-choice question")
    if p.words > 900:
        warns.append(f"{p.words} words of prose: long for one short lesson (aim under about 600)")
    for f in fails:
        print("FAIL", f)
    for w in warns:
        print("WARN", w)
    print("FAIL" if fails else "PASS", f"{path}: {len(p.questions)} questions, {p.words} words of prose")
    return 1 if fails else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__.strip())
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
