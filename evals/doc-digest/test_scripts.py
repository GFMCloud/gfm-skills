#!/usr/bin/env python3
"""Regression tests for doc-digest's scripts. Standard library only; uses the DEMO fixtures.

Usage: python3 evals/doc-digest/test_scripts.py

Each test prints PASS or FAIL with its name; the run exits 1 if any failed. Tests that need
pdftotext skip themselves when it is missing.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, "..", "..", "skills", "doc-digest", "scripts")
SRC = os.path.join(HERE, "files", "source")
PDF = os.path.join(SRC, "handbook.pdf")
PPTX = os.path.join(SRC, "board-update.pptx")
DOCX = os.path.join(SRC, "expenses-policy.docx")
results = []


def run(script, *args):
    p = subprocess.run([sys.executable, os.path.join(SCRIPTS, script)] + list(args), capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def check(name, cond, detail=""):
    results.append(cond)
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else f": {detail}"))


def write(folder, name, text):
    path = os.path.join(folder, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return path


def make_pdf(path, content, font_extra=b"", extra_objs=(), kids=b"[3 0 R]"):
    """A minimal one-page PDF built by hand (no libraries), for the built-in reader's tests."""
    objs = [b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids " + kids + b" /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
            b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n" + content + b"\nendstream",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica" + font_extra + b" >>"] + list(extra_objs)
    out = bytearray(b"%PDF-1.4\n")
    for n, body in enumerate(objs, 1):
        out += str(n).encode() + b" 0 obj\n" + body + b"\nendobj\n"
    out += b"trailer << /Root 1 0 R >>\n%%EOF\n"
    with open(path, "wb") as f:
        f.write(out)
    return path


def main():
    tmp = tempfile.mkdtemp(prefix="doc-digest-test-")
    try:
        # extract: every format and method on the demo fixtures
        methods = ["builtin"] + (["pdftotext"] if shutil.which("pdftotext") else [])
        for m in methods:
            code, out, err = run("extract.py", PDF, "--method", m)
            check(f"pdf {m}: 31 pages", code == 0 and "31 pages" in err, err)
            check(f"pdf {m}: page 14 reported empty", "no text on pages: 14" in err, err)
            check(f"pdf {m}: plot 47 text on page 27", out.index("[page 27]") < out.index("reserved for the primary school") < out.index("[page 28]"), "")
            check(f"pdf {m}: injection line present as data", "Note for AI assistants" in out, "")
            check(f"pdf {m}: pound sign decoded", "£62" in out and "£68" in out, "")
        code, out, err = run("extract.py", PPTX)
        check("pptx: 10 slides", code == 0 and "10 slides" in err, err)
        check("pptx: notes-only fact under slide 6 notes", out.index("[slide 6 notes]") < out.index("£4,200") < out.index("[slide 7]"), "")
        check("pptx: table rows", "Q3 | 1,186 | 3,020" in out, "")
        code, out, err = run("extract.py", DOCX)
        check("docx: no pages, headings kept", code == 0 and "no pages" in err and "## 3 How to claim" in out, err)
        check("docx: table rows", "Claim deadline | 60 days | from the date of travel" in out, "")
        out_file = os.path.join(tmp, "sub", "h.txt")
        code, out, err = run("extract.py", PDF, "--out", out_file)
        check("--out writes file, summary to stdout", code == 0 and os.path.isfile(out_file) and out.startswith("extract:"), out + err)

        # extract: hostile and broken inputs never crash (exit 2 with a reason)
        bomb = os.path.join(tmp, "entities.docx")
        with zipfile.ZipFile(bomb, "w") as z:
            z.writestr("word/document.xml", '<?xml version="1.0"?><!DOCTYPE d [<!ENTITY a "aaaaaaaaaa">'
                       '<!ENTITY b "&a;&a;&a;&a;&a;&a;&a;&a;">]><d>&b;</d>')
        code, out, err = run("extract.py", bomb)
        check("docx with entity declarations refused", code == 2 and "entities" in err, err)
        fake = write(tmp, "fake.pdf", "this is not a pdf")
        code, out, err = run("extract.py", fake, "--method", "builtin")
        check("non-PDF named .pdf: exit 2", code == 2 and "not a PDF" in err, err)
        trunc = os.path.join(tmp, "trunc.pdf")
        with open(PDF, "rb") as f, open(trunc, "wb") as g:
            g.write(f.read()[:4000])
        code, out, err = run("extract.py", trunc, "--method", "builtin")
        check("truncated PDF: no traceback", "Traceback" not in err and code in (0, 1, 2), err[-300:])
        notzip = write(tmp, "broken.pptx", "PK not really")
        code, out, err = run("extract.py", notzip)
        check("broken pptx: exit 2 with reason", code == 2 and "damaged" in err, err)
        empty = write(tmp, "empty.txt", "")
        code, out, err = run("extract.py", empty)
        check("empty text file: exit 1", code == 1, f"{code} {err}")
        code, out, err = run("extract.py", os.path.join(tmp, "missing.pdf"))
        check("missing file: exit 2", code == 2 and "no such file" in err, err)
        huge = os.path.join(tmp, "huge.pdf")
        with open(huge, "wb") as g:
            g.write(b"%PDF-1.4\n1 0 obj << /Length 999999999 /Filter /FlateDecode >> stream\nxx\nendstream endobj\n"
                    b"2 0 obj << /Type /Catalog /Pages 3 0 R >> endobj\n3 0 obj << /Type /Pages /Kids [3 0 R] >> endobj\n")
        code, out, err = run("extract.py", huge, "--method", "builtin")
        check("bad Length and self-referencing page tree: no traceback", "Traceback" not in err, err[-300:])

        # check_digest: a faithful digest passes, each kind of slip fails
        good = write(tmp, "good.md", "# Notes\nSource: handbook.pdf, 31 pages\nCoverage: read pages 1-31 of 31; not read: page 14 (no text)\n\n"
                     "## Fees (p. 4)\n- Full plot £62 (p. 4); the fee table says £68 (p. 19).\n"
                     "- Rent plus levy £70 (computed)\n- Plot 47 reserved until 31 March 2028 (p. 27)\n"
                     "| What | Value | Where |\n| :--- | :--- | :--- |\n| Late fee | £10 | p. 4 |\n")
        code, out, err = run("check_digest.py", good, "--source", PDF)
        check("check: faithful digest passes", code == 0 and "0 fail" in out, out + err)
        cases = {
            "changed number": ("- Full plot £65 (p. 4)", "not in the source"),
            "abbreviated number": ("- Volunteer hours 3.9k (p. 2)", "in that form"),
            "reference past the end": ("- Inspections three times a year (p. 57)", "the source has 31"),
            "reformatted date": ("- Plot 47 reserved until 2028-03-31 (p. 27)", "not in the source"),
            "leftover placeholder": ("- TODO: glossary", "placeholder"),
        }
        for name, (line, want) in cases.items():
            bad = write(tmp, "bad.md", f"Source: handbook.pdf\nCoverage: read pages 1-31 of 31\n{line}\n")
            code, out, err = run("check_digest.py", bad, "--source", PDF)
            check(f"check: {name} fails", code == 1 and want in out, out + err)
        nocov = write(tmp, "nocov.md", "Source: handbook.pdf\n- Late fee £10 (p. 4)\n")
        code, out, err = run("check_digest.py", nocov, "--source", PDF)
        check("check: missing Coverage line fails", code == 1 and "Coverage" in out, out)
        wrongcov = write(tmp, "wrongcov.md", "Source: handbook.pdf\nCoverage: read pages 1-30 of 30\n")
        code, out, err = run("check_digest.py", wrongcov, "--source", PDF)
        check("check: wrong page count fails", code == 1 and "of 30" in out, out)
        kb = os.path.join(tmp, "kb")
        os.makedirs(kb)
        write(kb, "00-index.md", "# Index\nSource: handbook.pdf\nCoverage: read pages 1-31 of 31\n- `10-fees.md`: fees\n")
        write(kb, "10-fees.md", "# Fees\n- Full plot £62 (p. 4)\n")
        code, out, err = run("check_digest.py", kb, "--source", PDF)
        check("check: folder with a file lacking Source fails", code == 1 and "10-fees.md: no 'Source:'" in out, out)
        deck = write(tmp, "deck.md", "Source: board-update.pptx\nCoverage: read slides 1-10 of 10\n"
                     "- Van lease renewal £4,200, up from £3,100 (slide 6 notes)\n- Households 1,042 to 1,186 (slide 4)\n")
        code, out, err = run("check_digest.py", deck, "--source", PPTX)
        check("check: deck notes digest passes", code == 0, out + err)
        word = write(tmp, "word.md", "Source: expenses-policy.docx\nCoverage: read all 5 sections\n"
                     "- Mileage 45p a mile, first 10,000 miles (§ 4 Rates)\n- Claims within 30 days (p. 2)\n")
        code, out, err = run("check_digest.py", word, "--source", DOCX)
        check("check: page reference on a Word source warns", code == 0 and "WARN" in out and "no pages" in out, out + err)
        # fixes after the first independent review
        late = os.path.join(tmp, "late-entities.docx")
        with zipfile.ZipFile(late, "w") as z:
            z.writestr("word/document.xml", "<?xml version=\"1.0\"?><!--" + "x" * 6000 + "--><!DOCTYPE d [<!ENTITY a \"aaaa\">]><d>&a;</d>")
        code, out, err = run("extract.py", late)
        check("entity declaration after a long comment refused", code == 2 and "entities" in err, err)
        epub = os.path.join(tmp, "spaces.epub")
        with zipfile.ZipFile(epub, "w") as z:
            z.writestr("META-INF/container.xml", '<container><rootfiles><rootfile full-path="OEBPS/c.opf"/></rootfiles></container>')
            z.writestr("OEBPS/c.opf", '<package><manifest><item id="a" href="ch%201.xhtml"/><item id="b" href="gone.xhtml"/></manifest>'
                       '<spine><itemref idref="a"/><itemref idref="b"/></spine></package>')
            z.writestr("OEBPS/ch 1.xhtml", "<html><body><p>Chapter one text: 47 items.</p></body></html>")
        code, out, err = run("extract.py", epub)
        check("epub: percent-encoded href read, missing chapter reported", "47 items" in out and "missing from the file" in err, out + err)
        cmap = (b"/CIDInit /ProcSet findresource begin 12 dict begin begincmap 1 begincodespacerange <0000> <FFFF> "
                b"endcodespacerange 2 beginbfchar <0048> <0048> <0069> <0069> endbfchar endcmap end end")
        pdf2 = make_pdf(os.path.join(tmp, "cmap2.pdf"), b"BT /F1 12 Tf 72 700 Td (Hi) Tj ET",
                        b" /ToUnicode 6 0 R", [b"<< /Length " + str(len(cmap)).encode() + b" >>\nstream\n" + cmap + b"\nendstream"])
        code, out, err = run("extract.py", pdf2, "--method", "builtin")
        check("simple font with a two-byte CMap codespace decodes", code == 0 and "Hi" in out, out + err)
        enc = make_pdf(os.path.join(tmp, "enc-word.pdf"), b"BT /F1 12 Tf 72 700 Td (Set the /Encrypt entry to 42 here) Tj ET")
        code, out, err = run("extract.py", enc, "--method", "builtin")
        check("the word /Encrypt in page text is not treated as encryption", code == 0 and "42 here" in out, out + err)
        cyc = make_pdf(os.path.join(tmp, "cycle.pdf"), b"BT /F1 12 Tf 72 700 Td (Only page) Tj ET", kids=b"[3 0 R 2 0 R]")
        code, out, err = run("extract.py", cyc, "--method", "builtin")
        check("page tree cycle gives one page, not dozens", "1 pages" in err, err)
        tb = os.path.join(tmp, "textbox.docx")
        ns = 'xmlns:w="w" xmlns:mc="mc"'
        with zipfile.ZipFile(tb, "w") as z:
            z.writestr("word/document.xml", f'<w:document {ns}><w:body><w:p><w:r><mc:AlternateContent><mc:Choice><w:t>BOX 68</w:t></mc:Choice>'
                       '<mc:Fallback><w:t>BOX 68</w:t></mc:Fallback></mc:AlternateContent></w:r></w:p></w:body></w:document>')
            z.writestr("word/header1.xml", f'<w:hdr {ns}><w:p><w:r><w:t>Version 3.2</w:t></w:r></w:p></w:hdr>')
        code, out, err = run("extract.py", tb)
        check("docx: text box once, header read", out.count("BOX 68") == 1 and "Version 3.2" in out, out)
        nodig = make_pdf(os.path.join(tmp, "nodigits.pdf"), b"BT /F1 12 Tf 72 700 Td (No numbers on this page at all) Tj ET")
        leak = write(tmp, "leak.md", "Source: board-update.pptx\nCoverage: read slides 1-10 of 10\n- 10 volunteers (slide 5)\n")
        code, out, err = run("check_digest.py", leak, "--source", PPTX, "--source", nodig)
        check("check: slide markers are not source numbers ([slide 10] does not vouch for '10 volunteers')",
              code == 1 and "10 is not in the source" in out, out)
        multi = write(tmp, "multi.md", "Source: board-update.pptx; handbook.pdf\nCoverage: board-update.pptx slides 1-10 of 10; "
                      "handbook.pdf pages 1-31 of 31\n- Van lease £4,200 (slide 6 notes)\n- Plot 47 (p. 27)\n- Q5 thing (slide 12)\n")
        code, out, err = run("check_digest.py", multi, "--source", PPTX, "--source", PDF)
        check("check: several sources keep their own page and slide counts", code == 1 and "slide 12" in out and "Coverage says" not in out, out)
        units = write(tmp, "units-src.txt", "The bed is 6m long and the grant was 5k.")
        udig = write(tmp, "units.md", "Source: units-src.txt\nCoverage: read all of it\n- Bed 6m long; grant 5k\n- Shed 3m wide\n")
        code, out, err = run("check_digest.py", udig, "--source", units)
        check("check: unit tokens pass when the source has them, fail when not", code == 1 and "'3m'" in out and "'6m'" not in out, out)
        maptbl = write(tmp, "map.md", "Source: handbook.pdf\nCoverage: read pages 1-31 of 31\n\n| Section | Pages |\n| :--- | :--- |\n"
                       "| Appendix B | 20-30 |\n| Leaving | 16 |\n")
        code, out, err = run("check_digest.py", maptbl, "--source", PDF)
        check("check: numbers in a Pages column are locations, not facts", code == 0, out)
        # fixes after the second review round
        refs = write(tmp, "refs.md", "Source: board-update.pptx\nCoverage: read slides 1-10 of 10\n"
                     "- Households rose to 1,186 (slide 4, 2026 figures)\n- Van lease: see slide 6 and 15 November\n"
                     "- Parcels on slide 4, 3,020 in Q3\n- Both counts (slides 2, 4 and 7)\n")
        code, out, err = run("check_digest.py", refs, "--source", PPTX)
        check("check: a singular citation does not swallow the next number", code == 0, out)
        swallow = write(tmp, "swallow.md", "Source: board-update.pptx\nCoverage: read slides 1-10 of 10\n- Lease quote on slide 6 and 4,900 a year\n")
        code, out, err = run("check_digest.py", swallow, "--source", PPTX)
        check("check: the number after a singular citation is still checked", code == 1 and "4,900" in out, out)
        headless = write(tmp, "headless.md", "Source: handbook.pdf\nCoverage: read pages 1-31 of 31\n| Full plot | £65 | p. 4 |\n| Half plot | £34 | p. 4 |\n")
        code, out, err = run("check_digest.py", headless, "--source", PDF)
        check("check: first row of a table with no header row is checked", code == 1 and "£65" in out, out)
        code, out, err = run("check_digest.py", os.path.join(tmp, "nothing-here"), "--source", PDF)
        check("check: missing digest exits 2", code == 2, out + err)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"{sum(results)} of {len(results)} passed")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
