#!/usr/bin/env python3
"""Get the text out of a document, with a location marker before each page, slide or chapter.

Usage: python3 extract.py <file> [--out FILE] [--method auto|pdftotext|pypdf|builtin]

Standard library only (Python 3.9+). Handles .pdf, .docx, .pptx, .epub, .html/.htm, .txt and .md.
For other formats (.doc, .rtf, .odt, .xlsx and so on) it tries a converter already on the machine
(anydoc, markitdown, textutil on macOS) and otherwise says what to do.

Markers in the text: [page N], [slide N], [slide N notes], [chapter N: name]. Word files have no
pages, so headings are kept as "## Heading" lines to cite instead. Word and PowerPoint tables come
out as "a | b | c"; PDF tables come out as spaced text.

With --out, the text goes to that file and the summary to standard output. Without it, the text
goes to standard output and the summary to standard error. The summary's first line starts with
"extract:" and gives the unit count, word count, method and any pages with no text.

PDF methods, tried in order by "auto": pdftotext (poppler), the pypdf module if installed, then a
built-in reader that handles ordinary text PDFs but not every font encoding. Exit 0 when text came
out, 1 when the file was read but holds no text, 2 when it could not be read.
"""
import argparse
import base64
import html
import html.parser
import os
import re
import shutil
import subprocess
import sys
import urllib.parse
import xml.etree.ElementTree as ET
import zipfile
import zlib

MAX_MEMBER = 200 * 1024 * 1024   # largest zip member or decompressed stream we will expand
MAX_STREAMS = 20000              # cap on PDF objects scanned, for hostile files


class ExtractError(Exception):
    pass


class Result:
    def __init__(self, kind, unit, method):
        self.kind = kind          # pdf, docx, ...
        self.unit = unit          # page, slide, chapter, section
        self.method = method
        self.parts = []           # list of (label, text)
        self.notes = []           # warnings for the summary

    def add(self, label, text):
        self.parts.append((label, text))

    def text(self):
        out = []
        for label, body in self.parts:
            if label:
                out.append(f"[{label}]")
            out.append(body.rstrip())
            out.append("")
        return "\n".join(out).rstrip() + "\n"


# ---------------------------------------------------------------- zip and XML helpers

def read_member(z, name):
    info = z.getinfo(name)
    if info.file_size > MAX_MEMBER:
        raise ExtractError(f"{name} inside the file is too large to expand safely")
    return z.read(name)


def parse_xml(data):
    if b"<!DOCTYPE" in data or b"<!ENTITY" in data or b"<\x00!\x00D" in data or b"\x00<\x00!" in data:
        raise ExtractError("the file's XML declares entities, which this script refuses to expand")
    return ET.fromstring(data)


def local(tag):
    return tag.rsplit("}", 1)[-1]


# ---------------------------------------------------------------- Word

def extract_docx(path):
    res = Result("docx", "section", "builtin-docx")
    with zipfile.ZipFile(path) as z:
        names = set(z.namelist())
        if "word/document.xml" not in names:
            raise ExtractError("not a Word .docx file (no word/document.xml)")
        root = parse_xml(read_member(z, "word/document.xml"))
        body = next((el for el in root if local(el.tag) == "body"), None)
        lines = []
        docx_blocks(body if body is not None else [], lines, 0)
        res.add("", "\n".join(lines))
        hf = sorted(n for n in names if re.match(r"word/(header|footer)\d*\.xml$", n))
        extras = [(hf, "headers and footers"), (["word/footnotes.xml"], "footnotes"),
                  (["word/endnotes.xml"], "endnotes"), (["word/comments.xml"], "comments")]
        for members, label in extras:
            paras = []
            for extra in members:
                if extra in names:
                    r = parse_xml(read_member(z, extra))
                    for p in iter_skip_fallback(r):
                        if local(p.tag) == "p":
                            text = docx_para(p)
                            if text.strip() and text not in paras:
                                paras.append(text)
            if paras:
                res.add(label, "\n".join(paras))
    return res


def iter_skip_fallback(el):
    """Like el.iter(), but leaves out mc:Fallback copies (text boxes are stored twice)."""
    yield el
    for child in el:
        if local(child.tag) != "Fallback":
            yield from iter_skip_fallback(child)


def docx_blocks(container, lines, depth):
    """Paragraphs and tables in document order, looking inside wrappers (sdt, customXml, ...)."""
    for el in container:
        t = local(el.tag)
        if t == "p":
            try:
                lines.append(docx_para(el))
            except RecursionError:
                lines.append("[a paragraph nested too deeply to read]")
        elif t == "tbl":
            lines.extend(docx_table(el))
            lines.append("")
        elif depth < 20 and t not in ("sectPr", "Fallback"):
            docx_blocks(el, lines, depth + 1)


def docx_para(p):
    style, buf = "", []
    for el in iter_skip_fallback(p):
        t = local(el.tag)
        if t == "pStyle":
            style = next((v for k, v in el.attrib.items() if local(k) == "val"), "")
        elif t == "t":
            buf.append(el.text or "")
        elif t == "tab":
            buf.append("\t")
        elif t in ("br", "cr"):
            buf.append("\n")
    text = "".join(buf)
    s = style.lower()
    if text.strip() and (s.startswith("heading") or s in ("title", "subtitle")):
        level = re.sub(r"\D", "", s) or "1"
        return "#" * min(int(level) + 1, 6) + " " + text.strip()
    return text


def docx_table(tbl):
    rows = []
    for tr in tbl:
        if local(tr.tag) != "tr":
            continue
        cells = []
        for tc in tr:
            if local(tc.tag) != "tc":
                continue
            paras = [docx_para(p) for p in tc.iter() if local(p.tag) == "p"]
            cells.append(" ".join(x.strip() for x in paras if x.strip()))
        rows.append(" | ".join(cells))
    return rows


# ---------------------------------------------------------------- PowerPoint

def extract_pptx(path):
    res = Result("pptx", "slide", "builtin-pptx")
    with zipfile.ZipFile(path) as z:
        names = set(z.namelist())
        if "ppt/presentation.xml" not in names:
            raise ExtractError("not a PowerPoint .pptx file (no ppt/presentation.xml)")
        rels = rel_targets(z, "ppt/_rels/presentation.xml.rels", "ppt/")
        pres = parse_xml(read_member(z, "ppt/presentation.xml"))
        order = []
        for el in pres.iter():
            if local(el.tag) == "sldId":
                rid = next((v for k, v in el.attrib.items() if local(k) == "id" and "relationships" in k), None)
                if rid in rels:
                    order.append(rels[rid])
        if not order:
            order = sorted((n for n in names if re.match(r"ppt/slides/slide\d+\.xml$", n)),
                           key=lambda n: int(re.findall(r"\d+", n)[-1]))
        for i, slide in enumerate(order, 1):
            if slide not in names:
                res.notes.append(f"slide {i}: {slide} is missing from the file")
                continue
            root = parse_xml(read_member(z, slide))
            hidden = root.attrib.get("show") == "0"
            res.add(f"slide {i}" + (" (hidden)" if hidden else ""), pptx_text(root, skip_placeholders=()))
            srels = rel_targets(z, slide.replace("slides/", "slides/_rels/") + ".rels", "ppt/slides/")
            notes = [t for t in srels.values() if "notesSlide" in t]
            if notes and notes[0] in names:
                ntext = pptx_text(parse_xml(read_member(z, notes[0])), skip_placeholders=("sldNum", "sldImg", "hdr", "ftr", "dt"))
                if ntext.strip():
                    res.add(f"slide {i} notes", ntext)
    return res


def rel_targets(z, rels_path, base):
    out = {}
    if rels_path not in z.namelist():
        return out
    for el in parse_xml(read_member(z, rels_path)):
        target = el.attrib.get("Target", "")
        if el.attrib.get("TargetMode") == "External":
            continue
        out[el.attrib.get("Id")] = os.path.normpath(os.path.join(base, target)).replace(os.sep, "/") \
            if not target.startswith("/") else target.lstrip("/")
    return out


def pptx_text(root, skip_placeholders):
    lines = []
    for sp in root.iter():
        t = local(sp.tag)
        if t == "sp":
            ph = next((e for e in sp.iter() if local(e.tag) == "ph"), None)
            if ph is not None and ph.attrib.get("type") in skip_placeholders:
                continue
            body = next((e for e in sp if local(e.tag) == "txBody"), None)
            if body is None:
                continue
            for p in body:
                if local(p.tag) == "p":
                    line = "".join(e.text or "" for e in p.iter() if local(e.tag) == "t")
                    if line.strip():
                        lines.append(line)
        elif t == "tbl":
            for tr in sp:
                if local(tr.tag) != "tr":
                    continue
                cells = []
                for tc in tr:
                    if local(tc.tag) == "tc":
                        cells.append(" ".join("".join(e.text or "" for e in p.iter() if local(e.tag) == "t")
                                              for p in tc.iter() if local(p.tag) == "p").strip())
                lines.append(" | ".join(cells))
    return "\n".join(lines)


# ---------------------------------------------------------------- HTML, EPUB, text

class TextHTML(html.parser.HTMLParser):
    BLOCK = {"p", "div", "br", "li", "tr", "section", "article", "h1", "h2", "h3", "h4", "h5", "h6",
             "blockquote", "pre", "table", "ul", "ol"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.skip, self.cell = [], 0, False

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "head", "template", "noscript"):
            self.skip += 1
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.out.append("\n" + "#" * (int(tag[1]) + 1) + " ")
        elif tag in ("td", "th"):
            self.out.append(" | " if self.cell else "")
            self.cell = True
        elif tag == "tr":
            self.out.append("\n")
            self.cell = False
        elif tag in self.BLOCK:
            self.out.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style", "head", "template", "noscript"):
            self.skip = max(0, self.skip - 1)
        elif tag in self.BLOCK:
            self.out.append("\n")

    def handle_data(self, data):
        if not self.skip:
            self.out.append(re.sub(r"\s+", " ", data))

    def text(self):
        t = "".join(self.out)
        return re.sub(r"\n\s*\n\s*\n+", "\n\n", re.sub(r"[ \t]+\n", "\n", t)).strip()


def html_to_text(data):
    p = TextHTML()
    p.feed(data)
    return p.text()


def extract_html(path):
    res = Result("html", "section", "builtin-html")
    with open(path, "rb") as f:
        res.add("", html_to_text(f.read().decode("utf-8", "replace")))
    return res


def extract_epub(path):
    res = Result("epub", "chapter", "builtin-epub")
    with zipfile.ZipFile(path) as z:
        cont = parse_xml(read_member(z, "META-INF/container.xml"))
        opf = next((e.attrib["full-path"] for e in cont.iter() if local(e.tag) == "rootfile"), None)
        if not opf:
            raise ExtractError("EPUB has no package file")
        root = parse_xml(read_member(z, opf))
        base = os.path.dirname(opf)
        items = {e.attrib.get("id"): e.attrib.get("href") for e in root.iter() if local(e.tag) == "item"}
        spine = [e.attrib.get("idref") for e in root.iter() if local(e.tag) == "itemref"]
        for i, idref in enumerate(spine, 1):
            href = items.get(idref)
            if not href:
                continue
            target = urllib.parse.unquote(html.unescape(href).split("#")[0])
            name = os.path.normpath(os.path.join(base, target)).replace(os.sep, "/")
            if name not in z.namelist():
                res.notes.append(f"chapter {i}: {href} is listed but missing from the file")
                continue
            res.add(f"chapter {i}: {os.path.basename(name)}", html_to_text(read_member(z, name).decode("utf-8", "replace")))
    return res


def extract_plain(path):
    res = Result("text", "section", "builtin-text")
    with open(path, "rb") as f:
        res.add("", f.read().decode("utf-8", "replace"))
    return res


# ---------------------------------------------------------------- PDF: external tools

def pdf_pdftotext(path):
    exe = shutil.which("pdftotext")
    if not exe:
        return None
    try:
        out = subprocess.run([exe, "-enc", "UTF-8", path, "-"], capture_output=True, timeout=300)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if out.returncode != 0:
        return None
    pages = out.stdout.decode("utf-8", "replace").split("\f")
    if pages and not pages[-1].strip():
        pages = pages[:-1]
    res = Result("pdf", "page", "pdftotext")
    for i, t in enumerate(pages, 1):
        res.add(f"page {i}", t)
    return res


def pdf_pypdf(path):
    try:
        import pypdf  # noqa: F401  (optional, used only when the user already has it)
    except ImportError:
        return None
    try:
        reader = pypdf.PdfReader(path)
        res = Result("pdf", "page", "pypdf")
        for i, page in enumerate(reader.pages, 1):
            res.add(f"page {i}", page.extract_text() or "")
        return res
    except Exception:  # pypdf raises many types on damaged files
        return None


# ---------------------------------------------------------------- PDF: built-in reader

class Ref:
    __slots__ = ("num",)

    def __init__(self, num):
        self.num = num


class Name(str):
    pass


TOKEN = re.compile(rb"\s*(?:%[^\r\n]*[\r\n]?\s*)*")
DELIM = b"()<>[]{}/%"


class Lexer:
    def __init__(self, data, pos=0):
        self.d, self.p = data, pos

    def skip_ws(self):
        m = TOKEN.match(self.d, self.p)
        self.p = m.end()

    def value(self):
        """Parse one PDF value; returns (value, is_operator)."""
        self.skip_ws()
        d, p = self.d, self.p
        if p >= len(d):
            raise ExtractError("unexpected end of PDF data")
        c = d[p:p + 1]
        if c == b"/":
            m = re.compile(rb"/([^\s()<>\[\]{}/%]*)").match(d, p)
            self.p = m.end()
            return Name(re.sub(rb"#([0-9a-fA-F]{2})", lambda x: bytes([int(x.group(1), 16)]), m.group(1)).decode("latin-1")), False
        if d.startswith(b"<<", p):
            self.p += 2
            out = {}
            while True:
                self.skip_ws()
                if self.d.startswith(b">>", self.p):
                    self.p += 2
                    return out, False
                k, _ = self.value()
                v, _ = self.value()
                out[str(k)] = v
        if c == b"<":
            end = d.index(b">", p)
            hexs = re.sub(rb"\s", b"", d[p + 1:end])
            if len(hexs) % 2:
                hexs += b"0"
            self.p = end + 1
            return bytes.fromhex(hexs.decode("ascii", "replace")), False
        if c == b"(":
            return self.literal(), False
        if c == b"[":
            self.p += 1
            out = []
            while True:
                self.skip_ws()
                if self.d[self.p:self.p + 1] == b"]":
                    self.p += 1
                    return out, False
                v, op = self.value()
                if op:
                    raise ExtractError("operator inside array")
                out.append(v)
        m = re.compile(rb"[+-]?(?:\d+\.?\d*|\.\d+)").match(d, p)
        if m:
            self.p = m.end()
            s = m.group(0)
            r = re.compile(rb"\s+(\d+)\s+R(?![^\s()<>\[\]{}/%])").match(d, self.p)
            if r and b"." not in s and not s.startswith((b"+", b"-")):
                self.p = r.end()
                return Ref(int(s)), False
            return (float(s) if b"." in s else int(s)), False
        m = re.compile(rb"[^\s()<>\[\]{}/%]+").match(d, p)
        if not m:
            self.p += 1
            return None, False
        self.p = m.end()
        w = m.group(0)
        if w == b"true":
            return True, False
        if w == b"false":
            return False, False
        if w == b"null":
            return None, False
        return w.decode("latin-1"), True

    def literal(self):
        d, p = self.d, self.p + 1
        depth, out = 1, bytearray()
        esc = {ord("n"): 10, ord("r"): 13, ord("t"): 9, ord("b"): 8, ord("f"): 12}
        while p < len(d):
            ch = d[p]
            if ch == 0x5C:  # backslash
                p += 1
                if p >= len(d):
                    break
                nx = d[p]
                if nx in esc:
                    out.append(esc[nx])
                elif 0x30 <= nx <= 0x37:
                    m = re.compile(rb"[0-7]{1,3}").match(d, p)
                    out.append(int(m.group(0), 8) & 0xFF)
                    p = m.end() - 1
                elif nx in (0x0A, 0x0D):
                    if nx == 0x0D and d[p + 1:p + 2] == b"\n":
                        p += 1
                else:
                    out.append(nx)
            elif ch == 0x28:
                depth += 1
                out.append(ch)
            elif ch == 0x29:
                depth -= 1
                if depth == 0:
                    self.p = p + 1
                    return bytes(out)
                out.append(ch)
            else:
                out.append(ch)
            p += 1
        self.p = p
        return bytes(out)


class PDF:
    OBJ = re.compile(rb"(?<![0-9])(\d+)\s+(\d+)\s+obj\b")

    def __init__(self, data):
        self.d = data
        self.objs = {}
        self.streams = {}
        self.truncated = False
        self.scan()

    def scan(self):
        count = 0
        for m in self.OBJ.finditer(self.d):
            count += 1
            if count > MAX_STREAMS:
                self.truncated = True
                break
            num = int(m.group(1))
            lx = Lexer(self.d, m.end())
            try:
                val, _ = lx.value()
            except (ExtractError, ValueError, IndexError, RecursionError):
                continue
            lx.skip_ws()
            if isinstance(val, dict) and self.d.startswith(b"stream", lx.p):
                start = lx.p + 6
                if self.d[start:start + 2] == b"\r\n":
                    start += 2
                elif self.d[start:start + 1] in (b"\n", b"\r"):
                    start += 1
                length = val.get("Length")
                end = start + length if isinstance(length, int) else -1
                if end < 0 or self.d[end:end + 30].strip()[:9] != b"endstream":
                    end = self.d.find(b"endstream", start)
                    if end < 0:
                        continue
                self.streams[num] = self.d[start:end]
            self.objs[num] = val
        for num, val in list(self.objs.items()):
            if isinstance(val, dict) and val.get("Type") == "ObjStm":
                self.unpack_objstm(num, val)

    def unpack_objstm(self, num, val):
        try:
            raw = self.decode(num)
            n, first = int(val.get("N", 0)), int(val.get("First", 0))
            lx = Lexer(raw)
            pairs = []
            for _ in range(n):
                on, _ = lx.value()
                off, _ = lx.value()
                pairs.append((on, off))
            for on, off in pairs:
                if on not in self.objs:
                    v, _ = Lexer(raw, first + off).value()
                    self.objs[on] = v
        except (ExtractError, ValueError, IndexError, TypeError):
            pass

    def get(self, v, depth=0):
        while isinstance(v, Ref) and depth < 32:
            v = self.objs.get(v.num)
            depth += 1
        return v

    def decode(self, num):
        raw = self.streams.get(num)
        if raw is None:
            return b""
        d = self.get(self.objs.get(num)) or {}
        filters = self.get(d.get("Filter"))
        filters = filters if isinstance(filters, list) else ([filters] if filters else [])
        for f in filters:
            f = str(self.get(f))
            if f in ("FlateDecode", "Fl"):
                dec = zlib.decompressobj()
                raw = dec.decompress(raw, MAX_MEMBER)
                if dec.unconsumed_tail:
                    raise ExtractError("a stream expands past the safety limit")
            elif f in ("ASCIIHexDecode", "AHx"):
                raw = bytes.fromhex(re.sub(rb"[^0-9a-fA-F]", b"", raw.split(b">")[0]).decode() + ("0" if len(re.sub(rb"[^0-9a-fA-F]", b"", raw.split(b">")[0])) % 2 else ""))
            elif f in ("ASCII85Decode", "A85"):
                body = raw.strip()
                if body.startswith(b"<~"):
                    body = body[2:]
                raw = base64.a85decode(body.split(b"~>")[0] + b"~>", adobe=True) if body else b""
            else:
                raise ExtractError(f"stream filter {f} is not supported by the built-in reader")
        return raw

    def pages(self):
        cat = next((v for v in self.objs.values() if isinstance(v, dict) and v.get("Type") == "Catalog"), None)
        out = []
        if cat:
            self.walk(self.get(cat.get("Pages")), {}, out, 0, set())
        if not out:
            out = [(v, self.get(v.get("Resources")) or {}) for v in self.objs.values()
                   if isinstance(v, dict) and v.get("Type") == "Page"]
        return out

    def walk(self, node, inherited, out, depth, seen):
        if not isinstance(node, dict) or depth > 64 or id(node) in seen:
            return
        seen.add(id(node))
        res = self.get(node.get("Resources")) or inherited
        if node.get("Type") == "Pages" or "Kids" in node:
            for kid in self.get(node.get("Kids")) or []:
                self.walk(self.get(kid), res, out, depth + 1, seen)
        else:
            out.append((node, res))

    def content(self, page):
        c = page.get("Contents")
        items = c if isinstance(c, list) else [c]
        data = b""
        for it in items:
            if isinstance(it, Ref):
                data += self.decode(it.num) + b"\n"
        if isinstance(c, Ref) and isinstance(self.get(c), list):
            for it in self.get(c):
                if isinstance(it, Ref):
                    data += self.decode(it.num) + b"\n"
        return data


class Font:
    def __init__(self, pdf, fdict):
        self.map, self.width = {}, 1
        fdict = fdict if isinstance(fdict, dict) else {}
        sub = fdict.get("Subtype")
        self.simple = sub != "Type0"
        if sub == "Type0":
            self.width = 2
        tu = fdict.get("ToUnicode")
        if isinstance(tu, Ref):
            try:
                self.parse_cmap(pdf.decode(tu.num))
            except (ExtractError, ValueError, zlib.error):
                pass
        if self.simple:
            self.width = 1  # simple fonts use one-byte codes whatever the CMap's codespace says
        self.diffs = {}
        self.codec = "cp1252"
        enc = pdf.get(fdict.get("Encoding"))
        base = enc.get("BaseEncoding") if isinstance(enc, dict) else enc
        if str(pdf.get(base)) == "MacRomanEncoding":
            self.codec = "mac_roman"
        if isinstance(enc, dict):
            code = 0
            for item in pdf.get(enc.get("Differences")) or []:
                if isinstance(item, int):
                    code = item
                else:
                    self.diffs[code] = glyph(str(item))
                    code += 1

    def parse_cmap(self, data):
        text = data.decode("latin-1")
        m = re.search(r"begincodespacerange\s*<([0-9a-fA-F]+)>", text)
        if m:
            self.width = max(1, len(m.group(1)) // 2)
        for block in re.findall(r"beginbfchar(.*?)endbfchar", text, re.S):
            for src, dst in re.findall(r"<([0-9a-fA-F]+)>\s*<([0-9a-fA-F]*)>", block):
                self.map[int(src, 16)] = utf16(dst)
        for block in re.findall(r"beginbfrange(.*?)endbfrange", text, re.S):
            for m in re.finditer(r"<([0-9a-fA-F]+)>\s*<([0-9a-fA-F]+)>\s*(<[0-9a-fA-F]*>|\[[^\]]*\])", block):
                lo, hi, dst = int(m.group(1), 16), int(m.group(2), 16), m.group(3)
                if hi - lo > 65536:
                    continue
                if dst.startswith("["):
                    for i, d in enumerate(re.findall(r"<([0-9a-fA-F]*)>", dst)):
                        self.map[lo + i] = utf16(d)
                else:
                    base = int(dst[1:-1] or "0", 16)
                    nbytes = len(dst[1:-1]) // 2
                    for i in range(hi - lo + 1):
                        self.map[lo + i] = utf16(format(base + i, "0%dx" % (nbytes * 2)))

    def decode(self, b):
        out = []
        w = self.width
        for i in range(0, len(b) - w + 1, w):
            code = int.from_bytes(b[i:i + w], "big")
            if code in self.map:
                out.append(self.map[code])
            elif self.simple and self.diffs.get(code):
                out.append(self.diffs[code])
            elif self.simple and code < 256:
                out.append(bytes([code]).decode(self.codec, "replace"))
            else:
                out.append("�")
        return "".join(out)


GLYPHS = {"space": " ", "hyphen": "-", "period": ".", "comma": ",", "colon": ":", "semicolon": ";",
          "quoteright": "'", "quoteleft": "'", "quotedblleft": '"', "quotedblright": '"',
          "endash": "-", "emdash": "-", "bullet": "*", "sterling": "£", "Euro": "€",
          "fi": "fi", "fl": "fl", "ff": "ff", "ffi": "ffi", "ffl": "ffl", "percent": "%", "dollar": "$", "ampersand": "&",
          "parenleft": "(", "parenright": ")", "slash": "/", "zero": "0", "one": "1", "two": "2",
          "three": "3", "four": "4", "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9"}
GLYPHS.update({c: c for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"})


def glyph(name):
    """Unicode text for a glyph name from a font's Differences array ("" if unknown)."""
    name = name.split(".")[0]
    if name in GLYPHS:
        return GLYPHS[name]
    m = re.match(r"^uni([0-9A-Fa-f]{4})+$", name)
    if m:
        return "".join(chr(int(name[i:i + 4], 16)) for i in range(3, len(name), 4))
    m = re.match(r"^u([0-9A-Fa-f]{4,6})$", name)
    if m and int(m.group(1), 16) <= 0x10FFFF:
        return chr(int(m.group(1), 16))
    return ""


def utf16(hexstr):
    try:
        return bytes.fromhex(hexstr).decode("utf-16-be")
    except (ValueError, UnicodeDecodeError):
        return ""


def run_content(pdf, data, resources, depth=0):
    """Text from one content stream. Tracks the text line's vertical position so a new line starts
    only when the text moves up or down, not at every text object."""
    fonts = pdf.get(resources.get("Font")) or {}
    xobjs = pdf.get(resources.get("XObject")) or {}
    cache, font = {}, None
    lx = Lexer(data)
    stack, out = [], []
    y, scale, leading = 0.0, 1.0, 0.0
    last_y = None

    def emit(text):
        nonlocal last_y
        if not text:
            return
        if last_y is not None and abs(y - last_y) > 0.5:
            out.append("\n")
        elif out and not out[-1].endswith((" ", "\n")) and not text.startswith(" "):
            out.append(" " if pending_gap[0] else "")
        pending_gap[0] = False
        out.append(text)
        last_y = y

    pending_gap = [False]
    while True:
        try:
            lx.skip_ws()
            if lx.p >= len(data):
                break
            if data.startswith(b"BI", lx.p) and data[lx.p + 2:lx.p + 3].isspace():
                end = data.find(b"EI", lx.p)
                lx.p = len(data) if end < 0 else end + 2
                continue
            val, is_op = lx.value()
        except (ExtractError, ValueError, IndexError):
            break
        if not is_op:
            stack.append(val)
            continue
        op = val
        nums = [v for v in stack if isinstance(v, (int, float))]
        if op == "Tf" and len(stack) >= 2:
            name = str(stack[-2])
            if name not in cache:
                cache[name] = Font(pdf, pdf.get(fonts.get(name)) if isinstance(fonts, dict) else None)
            font = cache[name]
        elif op in ("Tj", "'", '"') and stack and isinstance(stack[-1], bytes):
            if op != "Tj":
                y -= leading * scale
            emit((font or Font(pdf, None)).decode(stack[-1]))
        elif op == "TJ" and stack and isinstance(stack[-1], list):
            parts = []
            for item in stack[-1]:
                if isinstance(item, bytes):
                    parts.append((font or Font(pdf, None)).decode(item))
                elif isinstance(item, (int, float)) and item < -200:
                    parts.append(" ")
            emit("".join(parts))
        elif op in ("Td", "TD") and len(nums) >= 2:
            if op == "TD":
                leading = -nums[-1]
            y += nums[-1] * scale
            pending_gap[0] = True
        elif op == "TL" and nums:
            leading = nums[-1]
        elif op == "Tm" and len(nums) >= 6:
            scale = nums[-3] or 1.0
            y = nums[-1]
            pending_gap[0] = True
        elif op == "T*":
            y -= leading * scale
        elif op == "BT":
            y, scale = 0.0, 1.0
            pending_gap[0] = True
        elif op == "Do" and stack and depth < 3 and isinstance(xobjs, dict):
            ref = xobjs.get(str(stack[-1]))
            x = pdf.get(ref)
            if isinstance(ref, Ref) and isinstance(x, dict) and x.get("Subtype") == "Form":
                try:
                    sub = run_content(pdf, pdf.decode(ref.num), pdf.get(x.get("Resources")) or resources, depth + 1)
                    if sub.strip():
                        out.append("\n" + sub + "\n")
                        last_y = None
                except (ExtractError, zlib.error):
                    pass
        stack = []
    text = "".join(out)
    return re.sub(r"[ \t]+\n", "\n", re.sub(r"\n{3,}", "\n\n", text))


def pdf_builtin(path):
    with open(path, "rb") as f:
        data = f.read()
    if not data.startswith(b"%PDF"):
        raise ExtractError("not a PDF file")
    if re.search(rb"/Encrypt\s*(?:\d+\s+\d+\s+R|<<)", data):
        raise ExtractError("the PDF is encrypted; the built-in reader can't open it")
    pdf = PDF(data)
    res = Result("pdf", "page", "builtin-pdf")
    for i, (page, resources) in enumerate(pdf.pages(), 1):
        try:
            res.add(f"page {i}", run_content(pdf, pdf.content(page), resources if isinstance(resources, dict) else {}))
        except Exception as e:  # one damaged page must not cost the whole file
            res.add(f"page {i}", "")
            res.notes.append(f"page {i}: could not decode ({type(e).__name__})")
    if pdf.truncated:
        res.notes.append(f"more than {MAX_STREAMS} objects: stopped scanning, so later pages may be missing")
    res.notes.append("built-in PDF reader: fine for ordinary text PDFs; check a page or two against the PDF itself")
    return res


def extract_pdf(path, method):
    tried = []
    order = ["pdftotext", "pypdf", "builtin"] if method == "auto" else [method]
    for m in order:
        fn = {"pdftotext": pdf_pdftotext, "pypdf": pdf_pypdf, "builtin": pdf_builtin}[m]
        r = fn(path)
        if r is not None:
            r.notes.extend(f"{t} not available" for t in tried)
            return r
        tried.append(m)
    raise ExtractError("no PDF method worked: " + ", ".join(tried))


# ---------------------------------------------------------------- other formats

def extract_converter(path):
    for exe, args in (("anydoc", [path]), ("markitdown", [path]),
                      ("textutil", ["-convert", "txt", "-stdout", path])):
        tool = shutil.which(exe)
        if not tool:
            continue
        try:
            out = subprocess.run([tool] + args, capture_output=True, timeout=300)
        except (OSError, subprocess.TimeoutExpired):
            continue
        text = out.stdout.decode("utf-8", "replace")
        if out.returncode == 0 and text.strip():
            res = Result(os.path.splitext(path)[1].lstrip(".") or "file", "section", exe)
            res.add("", text)
            return res
    raise ExtractError("no reader for this format on this machine; save it as PDF, .docx or text, "
                       "or for spreadsheets use a spreadsheet tool")


def extract(path, method="auto"):
    ext = os.path.splitext(path)[1].lower()
    if not os.path.isfile(path):
        raise ExtractError(f"no such file: {path}")
    try:
        if ext == ".pdf":
            return extract_pdf(path, method)
        if ext in (".docx", ".docm", ".dotx", ".dotm"):
            return extract_docx(path)
        if ext in (".pptx", ".pptm"):
            return extract_pptx(path)
        if ext == ".epub":
            return extract_epub(path)
        if ext in (".html", ".htm", ".xhtml"):
            return extract_html(path)
        if ext in (".txt", ".md", ".markdown", ".text", ".csv", ".rst"):
            return extract_plain(path)
        return extract_converter(path)
    except zipfile.BadZipFile:
        raise ExtractError("the file is damaged or not the format its name says")
    except ET.ParseError as e:
        raise ExtractError(f"the file's XML is damaged ({e})")
    except (KeyError, zlib.error, ValueError, RecursionError) as e:
        raise ExtractError(f"could not read the file ({type(e).__name__})")


def summary(path, res):
    units = [(label, body) for label, body in res.parts if label and not label.endswith("notes")
             and label.split(" ")[0] in ("page", "slide", "chapter")]
    words = sum(len(body.split()) for _, body in res.parts)
    empty = [label.split(" ")[1] for label, body in units if len(body.strip()) < 20]
    junk = sum(body.count("�") for _, body in res.parts)
    chars = sum(len(body) for _, body in res.parts) or 1
    count = f"{len(units)} {res.unit}s" if units else "no pages (cite headings)"
    lines = [f"extract: {os.path.basename(path)}, {res.kind}, {count}, {words} words, method={res.method}"]
    if empty:
        lines.append(f"no text on {res.unit}s: {', '.join(empty)} (scanned, image-only or blank; read them as images or say they were not read)")
    tokens = [w for _, body in res.parts for w in body.split()]
    singles = sum(1 for w in tokens if len(w) == 1 and w.isalpha() and w not in ("a", "A", "I"))
    if res.method == "builtin-pdf" and tokens and singles / len(tokens) > 0.04:
        lines.append("warning: many words look split by stray spaces (\"e xit\"); quote from the PDF itself, or install pdftotext")
    if junk / chars > 0.02:
        lines.append("warning: much of the text did not decode (font or character encoding); read the document directly or use another method")
    lines += [f"note: {n}" for n in res.notes]
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Extract text from a document with page or slide markers.")
    ap.add_argument("file")
    ap.add_argument("--out", help="write the text here; the summary goes to standard output")
    ap.add_argument("--method", default="auto", choices=["auto", "pdftotext", "pypdf", "builtin"])
    a = ap.parse_args(argv)
    try:
        res = extract(a.file, a.method)
    except ExtractError as e:
        print(f"extract: {os.path.basename(a.file)}: could not read: {e}", file=sys.stderr)
        return 2
    text = res.text()
    info = summary(a.file, res)
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(text)
        print(info)
        print(f"text: {a.out}")
    else:
        sys.stdout.write(text)
        print(info, file=sys.stderr)
    return 0 if len(re.sub(r"\[[^\]]*\]|\s", "", text)) > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
