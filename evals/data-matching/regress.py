#!/usr/bin/env python3
"""Regression checks for skills/data-matching/scripts/match.py on the demo fixtures.

Usage: python3 evals/data-matching/regress.py   (exits 1 on any failure)
Copies the fixtures to a temp folder, runs the script, and checks the outcomes the evals rely on.
"""
import csv
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
MATCH = os.path.join(HERE, "..", "..", "skills", "data-matching", "scripts", "match.py")
fails = []


def run(cwd, *args, code=0):
    p = subprocess.run([sys.executable, MATCH, *args], cwd=cwd, capture_output=True, text=True,
                       env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    if p.returncode != code:
        fails.append(f"{' '.join(args)[:60]}: exit {p.returncode}, wanted {code}: {p.stderr.strip()[:200]}")
    return p.stdout + p.stderr


def rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def check(name, ok):
    print(("ok   " if ok else "FAIL ") + name)
    if not ok:
        fails.append(name)


tmp = tempfile.mkdtemp(prefix="dm-regress-")
try:
    shutil.copytree(os.path.join(HERE, "files"), os.path.join(tmp, "files"))
    c, m, v, r = (os.path.join(tmp, "files", x) for x in ("customers", "members", "vendors", "rerun"))
    before = {p: open(os.path.join(c, p), "rb").read() for p in ("crm.csv", "billing.csv")}

    out = run(c, "crm.csv", "billing.csv", "--name", "company=account_name", "--key", "crm_id=account_no",
              "--contact", "contact_email=billing_email", "--out", "a")
    check("customers: adds up", "adds up: yes" in out)
    check("customers: no fuzzy match without limits", all(x["rule"] != "fuzzy" for x in rows(f"{c}/a/mapping.csv")))
    rev = rows(f"{c}/a/review.csv")
    check("customers: Northgate Bakery to review", {"B108", "B109"} <= {x["right_key"] for x in rev if x["left_key"] == "C008"})
    check("customers: shared bookkeeper email not used, name matches", any(
        x["left_key"] == "C009" and x["right_key"] == "B110" for x in rows(f"{c}/a/mapping.csv")))
    check("customers: same email, different names goes to review", any(x["left_key"] == "C004" for x in rev))
    check("customers: inputs unchanged", all(open(os.path.join(c, p), "rb").read() == b for p, b in before.items()))
    check("customers: refuses a used output folder", "already has files" in run(
        c, "crm.csv", "billing.csv", "--name", "company=account_name", "--out", "a", code=2))
    check("customers: verify same", "verify: same output" in run(c, "--verify", "a"))
    with open(os.path.join(c, "crm.csv"), "a") as f:
        f.write("C099,Late Addition Ltd,,Hexham\n")
    check("customers: verify sees a changed input", "inputs changed" in run(c, "--verify", "a", code=1))

    out = run(m, "members.csv", "--name", "full_name", "--key", "member_no", "--contact", "email",
              "--must-agree", "date_of_birth", "--swap-comma", "--accept", "0.9", "--reject", "0.75", "--set-by", "user")
    g = {x["key"]: x for x in rows(f"{m}/matching/groups.csv")}
    check("members: adds up", "adds up: yes" in out)
    check("members: Wrenley chain not merged", all(g.get(k, {}).get("status") != "merged" for k in ("M07", "M08", "M09")))
    check("members: Pembertons kept apart", g.get("M05", {}).get("group") is None or g["M05"]["group"] != g.get("M06", {}).get("group"))
    check("members: shared family email not merged", "M12" not in g or g["M12"]["status"] != "merged")
    check("members: Ada Quillon merged", g.get("M01", {}).get("status") == "merged" and g["M01"]["group"] == g.get("M02", {}).get("group"))
    header = open(f"{m}/matching/groups.csv").readline() + open(f"{m}/matching/review.csv").readline()
    check("members: outputs hold no birth dates", "1984-03-12" not in open(f"{m}/matching/groups.csv").read()
          and "date_of_birth" not in header)

    run(v, "invoices.csv", "vendor-master.csv", "--name", "vendor_name=legal_name", "--key", "invoice_no=vendor_id",
        "--id", "vat_no", "--accept", "0.92", "--reject", "0.75", "--set-by", "user")
    mp = {x["left_key"]: x for x in rows(f"{v}/matching/mapping.csv")}
    check("vendors: VAT with spaces and case matches", mp.get("I-1003", {}).get("right_key") == "V02")
    check("vendors: rename matched on VAT and flagged", mp.get("I-1004", {}).get("right_key") == "V03" and "names differ" in mp["I-1004"]["flag"])
    check("vendors: same name, different VAT not matched", "I-1002" not in mp)
    check("vendors: N/A never matches N/A", mp.get("I-1006", {}).get("rule", "") != "id:vat_no")

    run(r, "suppliers.xlsx", "supplier-master.csv", "--name", "supplier=supplier_name", "--key", "ref=supplier_id",
        "--known", "supplier-aliases.csv", "--accept", "0.9", "--reject", "0.7", "--set-by", "user")
    mp = {x["left_key"]: x for x in rows(f"{r}/matching/mapping.csv")}
    check("rerun: xlsx read, known answers used", all(mp.get(k, {}).get("rule") == "known" for k in ("E01", "E02", "E04", "E06")))
    check("rerun: known different respected", "E05" not in mp)
    check("rerun: mapping works as known answers", "adds up: yes" in run(
        r, "suppliers.xlsx", "supplier-master.csv", "--name", "supplier=supplier_name", "--key", "ref=supplier_id",
        "--known", "matching/mapping.csv", "--out", "again"))

    check("limits need both", "both" in run(c, "crm.csv", "billing.csv", "--name", "company=account_name",
                                            "--accept", "0.9", "--out", "b", code=2))
    check("limits need set-by", "set-by" in run(c, "crm.csv", "billing.csv", "--name", "company=account_name",
                                                "--accept", "0.9", "--reject", "0.7", "--out", "b", code=2))
    check("missing column named", "no column" in run(c, "crm.csv", "billing.csv", "--name", "nope", "--out", "b", code=2))

    # one check per item of the first independent review (all values invented)
    x = os.path.join(tmp, "review")
    os.makedirs(x)

    def put(name, text):
        with open(os.path.join(x, name), "w", encoding="utf-8") as f:
            f.write(text)

    put("kl.csv", "inv,vendor,vat\nI1,Blackbird Code,GB1\n")
    put("kr.csv", "vid,legal,vat\nV1,Corvid Software,GB1\n")
    put("kk.csv", "left_key,left_name,right_key,right_name,score,reason,decision\nI1,Blackbird Code,V1,Corvid Software,,,different\n")
    run(x, "kl.csv", "kr.csv", "--name", "vendor=legal", "--key", "inv=vid", "--id", "vat", "--known", "kk.csv", "--out", "o1")
    check("review 1: a pair answered 'different' beats an identifier match", rows(f"{x}/o1/mapping.csv") == [])
    put("kk2.csv", "left_key,left_name,right_key,right_name,score,reason,decision\nI1,Someone Else,V1,Corvid Software,,,different\n")
    run(x, "kl.csv", "kr.csv", "--name", "vendor=legal", "--key", "inv=vid", "--id", "vat", "--known", "kk2.csv", "--out", "o1b")
    check("review 1: a pair answer for a reused key with another name is ignored", len(rows(f"{x}/o1b/mapping.csv")) == 1)

    put("pl.csv", "k,name,vat,phone\n1,Alpha,n.a.,07700-900103\n2,Beta,000,\n")
    put("pr.csv", "k,name,vat,phone\n9,Zulu,n.a.,\n8,Yankee,000,\n7,Alpha Two,GB5,07700900103\n")
    run(x, "pl.csv", "pr.csv", "--name", "name", "--key", "k", "--id", "vat", "--contact", "phone", "--out", "o2")
    mp = {r["left_key"]: r for r in rows(f"{x}/o2/mapping.csv")}
    check("review 2: n.a. and 000 never match", "2" not in mp and mp.get("1", {}).get("right_key") != "9")
    check("review 2: phone punctuation ignored", mp.get("1", {}).get("right_key") == "7")

    put("blank.csv", "name,email\nAlpha Ltd,a@x.example\n\nBeta Ltd,b@x.example\n")
    put("blankr.csv", "name\nAlpha Ltd\nBeta Ltd\n")
    run(x, "blank.csv", "blankr.csv", "--name", "name", "--out", "o3")
    check("review 3: row numbers count blank lines", [r["left_key"] for r in rows(f"{x}/o3/mapping.csv")] == ["row2", "row4"])

    import zipfile
    def xlsx(name, rows_xml, styles=None):
        parts = {
            "[Content_Types].xml": '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>',
            "xl/workbook.xml": '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="S" sheetId="1" r:id="rId1"/></sheets></workbook>',
            "xl/_rels/workbook.xml.rels": '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Target="worksheets/sheet1.xml"/></Relationships>',
            "xl/worksheets/sheet1.xml": '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>' + rows_xml + "</sheetData></worksheet>"}
        if styles:
            parts["xl/styles.xml"] = styles
        with zipfile.ZipFile(os.path.join(x, name), "w") as z:
            for k, v in parts.items():
                z.writestr(k, v)

    def c(ref, v, s=None, text=True):
        st = f' s="{s}"' if s is not None else ""
        return (f'<c r="{ref}" t="inlineStr"{st}><is><t>{v}</t></is></c>' if text else f'<c r="{ref}"{st}><v>{v}</v></c>')
    xlsx("gap.xlsx", '<row r="1">' + c("A1", "name") + '</row><row r="2">' + c("A2", "Alpha Ltd") + '</row><row r="4">'
         + c("A4", "Beta Ltd") + "</row>")
    run(x, "gap.xlsx", "blankr.csv", "--name", "name", "--out", "o3b")
    check("review 3: xlsx row numbers follow the sheet", [r["left_key"] for r in rows(f"{x}/o3b/mapping.csv")] == ["row2", "row4"])

    styles = ('<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><cellXfs count="2">'
              '<xf numFmtId="0"/><xf numFmtId="14"/></cellXfs></styleSheet>')
    xlsx("dob.xlsx", '<row r="1">' + c("A1", "id") + c("B1", "name") + c("C1", "dob") + '</row><row r="2">' + c("A2", "1")
         + c("B2", "Ada Quillon") + c("C2", "30753", 1, text=False) + "</row>", styles)
    put("dobr.csv", "id,name,dob\nX1,Ada Quillon,1984-03-12\n")
    out = run(x, "dob.xlsx", "dobr.csv", "--name", "name", "--key", "id", "--must-agree", "dob", "--out", "o4")
    check("review 4: xlsx date cells read as dates", len(rows(f"{x}/o4/mapping.csv")) == 1)

    put("ba.csv", "alias,canonical,decision\n,S1,same\n")
    put("bl.csv", "ref,name\nE1,\nE2,Something\n")
    put("br.csv", "id,name\nS1,Greenway\n")
    run(x, "bl.csv", "br.csv", "--name", "name", "--key", "ref=id", "--known", "ba.csv", "--out", "o5")
    check("review 5: a blank alias matches nothing", rows(f"{x}/o5/mapping.csv") == [])
    put("bk.csv", "id,name\n1,Alpha\n,Beta\n")
    check("review 5: a blank key is refused", "blank" in run(x, "bk.csv", "--name", "name", "--key", "id", "--out", "o5b", code=2))

    with open(os.path.join(x, "u16.csv"), "wb") as f:
        f.write("name\nAlpha\n".encode("utf-16"))
    check("review 6: UTF-16 CSV is read", "adds up: yes" in run(x, "u16.csv", "--name", "name", "--out", "o6"))
    with open(os.path.join(x, "nul.csv"), "wb") as f:
        f.write(b"name\nAl\x00pha\n")
    check("review 6: NUL bytes refused with a message", "NUL" in run(x, "nul.csv", "--name", "name", "--out", "o6b", code=2))
    xlsx("bad.xlsx", '<row r="1"><c r="A1" t="s"><v>5</v></c></row>')
    check("review 6: a broken workbook gives a message", "could not be read" in run(x, "bad.xlsx", "--name", "x", "--out", "o6c", code=2))
    put("afile", "x")
    check("review 6: --out naming a file is refused", "not a folder" in run(x, "blank.csv", "--name", "name", "--out", "afile", code=2))
    xlsx("bomb.xlsx", '<row r="1">' + c("A1", "name") + "</row>")
    with zipfile.ZipFile(os.path.join(x, "bomb.xlsx"), "a") as z:
        z.writestr("xl/sharedStrings.xml", '<!DOCTYPE x [<!ENTITY a "aaaa">]><sst/>')
    check("review 6: XML entities refused", "entities" in run(x, "--columns", "bomb.xlsx", code=2))

    run(x, "blank.csv", "blankr.csv", "--name", "name", "--out", "o7")
    run(x, "blank.csv", "--name", "name", "--out", "o7", "--force")
    check("review 7: --force removes the earlier run's files", sorted(os.listdir(f"{x}/o7")) == ["groups.csv", "review.csv", "run.json"])

    check("review 8: agent may not set accept below 0.85", "0.85" in run(
        x, "blank.csv", "blankr.csv", "--name", "name", "--accept", "0.7", "--reject", "0.6", "--set-by", "agent", "--out", "o8", code=2))

    put("ml.csv", "k,name\n1,Alpha\n2,ALPHA\n3,=1+2\n")
    put("mr.csv", "k,name\nS1,Alpha\n")
    out = run(x, "ml.csv", "mr.csv", "--name", "name", "--key", "k", "--out", "o10")
    check("review 10: many-to-one counted", "1 matched by more than one record" in out)
    check("review 11: formula-like names written inert", "'=1+2" in open(f"{x}/o10/unmatched.csv").read())
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print(f"{'FAILED: ' + str(len(fails)) if fails else 'all passed'}")
sys.exit(1 if fails else 0)
