#!/usr/bin/env python3
"""Validate a diagram built from assets/template.html before handing it over.

Usage: python3 scripts/validate.py <diagram.html> [--shots]

Checks, in order:
  1. The file is complete: ends with </html>, script tags balance, the engine is intact.
  2. The brand slot was filled by scripts/apply_brand.py (a brand-source marker is present).
  3. Cross-references: every FLOWS edge and node exists, every node has a DETAIL entry, every
     edge label points at a real edge, every chip has a FLOWS entry, ids are unique, at most one
     hero node.
--shots also writes <name>-light.png and <name>-dark-flow.png with playwright. If screenshots were
asked for and not written, that is a FAIL, never a skip.

Standard library only (playwright only for --shots). Exit code 1 on any FAIL.
"""
import pathlib
import re
import sys

ENGINE = ["function setFlow(key)", "localStorage.setItem('diagram-theme'", "</body>"]


def structural(raw):
    problems = []
    if not raw.rstrip().endswith("</html>"):
        problems.append("file does not end with </html>; it was probably cut off while being written")
    if raw.count("<script") != raw.count("</script>"):
        problems.append("script tags do not balance; the engine block is not closed")
    for s in ENGINE:
        if s not in raw:
            problems.append(f"engine marker missing: {s!r}; copy the template again and edit only the slots")
    return problems


def brand(raw):
    m = re.search(r'<style id="brand">(.*?)</style>', raw, re.S)
    if not m:
        return ["no brand slot; start from assets/template.html"]
    if "brand-source:" not in m.group(1):
        return ["brand slot not filled; run python3 scripts/apply_brand.py on this file"]
    return []


def cross_refs(raw):
    html = re.sub(r"<!--.*?-->", "", raw, flags=re.S)
    edge_ids = re.findall(r'<path class="edge[^"]*"\s+id="([^"]+)"', html)
    node_ks = re.findall(r'<g class="node[^"]*"\s+data-k="([^"]+)"', html)
    heroes = re.findall(r'<g class="node[^"]*\bhero\b', html)
    labels = re.findall(r'class="elbl"\s+data-e="([^"]+)"', html)
    chips = [c for c in re.findall(r'class="chip[^"]*"\s+data-flow="([^"]+)"', html) if c != "all"]
    try:
        detail_block = html.split("const DETAIL = {", 1)[1].split("\n};", 1)[0]
        flows_block = html.split("const FLOWS = {", 1)[1].split("\n};", 1)[0]
    except IndexError:
        return ["DETAIL or FLOWS object not found"], [], {}
    detail_keys = set(re.findall(r'^\s*"?([\w-]+)"?\s*:\s*\{', detail_block, re.M))
    flow_keys = set(re.findall(r'^\s{2}"?([\w-]+)"?\s*:\s*\{', flows_block, re.M))
    flow_edges, flow_nodes = set(), set()
    for grp in re.findall(r"edges:\s*\[([^\]]*)\]", flows_block):
        flow_edges |= set(re.findall(r'"([\w-]+)"', grp))
    for grp in re.findall(r"nodes:\s*\[([^\]]*)\]", flows_block):
        flow_nodes |= set(re.findall(r'"([\w-]+)"', grp))
    problems, warnings = [], []
    for kind, items in (("edge id", edge_ids), ("node data-k", node_ks)):
        dupes = sorted({i for i in items if items.count(i) > 1})
        if dupes:
            problems.append(f"duplicate {kind}: {dupes}")
    checks = [
        (flow_edges - set(edge_ids), "FLOWS use edges that are not in the SVG"),
        (flow_nodes - set(node_ks), "FLOWS use nodes that are not in the SVG"),
        (set(labels) - set(edge_ids), "edge labels point at missing edges"),
        (set(node_ks) - detail_keys, "nodes without a DETAIL entry"),
        (set(chips) - flow_keys, "chips without a FLOWS entry"),
        (flow_keys - set(chips) - {"all"}, "FLOWS entries without a chip"),
    ]
    for missing, msg in checks:
        if missing:
            problems.append(f"{msg}: {sorted(missing)}")
    if "all" in flow_keys:
        problems.append('FLOWS must not define "all"; the engine provides it')
    if len(heroes) > 1:
        problems.append(f"{len(heroes)} hero nodes; use the hero class once at most")
    if not node_ks:
        problems.append("no nodes; fill the slots")
    unused = set(edge_ids) - flow_edges
    if unused:
        warnings.append(f"edges no flow lights (leftover?): {sorted(unused)}")
    extra = detail_keys - set(node_ks)
    if extra:
        warnings.append(f"DETAIL entries with no node: {sorted(extra)}")
    stats = dict(nodes=len(node_ks), edges=len(edge_ids), labels=len(labels), flows=len(flow_keys))
    return problems, warnings, stats


def shots(path):
    p = pathlib.Path(path)
    pngs = [p.with_name(p.stem + "-light.png"), p.with_name(p.stem + "-dark-flow.png")]
    for png in pngs:
        if png.exists():
            png.unlink()
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return ["--shots asked for but playwright is not installed; no screenshots were taken"]
    try:
        with sync_playwright() as pw:
            b = pw.chromium.launch()
            page = b.new_page(viewport={"width": 1560, "height": 900})
            page.goto(p.resolve().as_uri())
            page.wait_for_timeout(500)
            page.screenshot(path=str(pngs[0]))
            page.evaluate("document.documentElement.classList.add('dark')")
            chip = page.query_selector('.chip[data-flow]:not([data-flow="all"])')
            if chip:
                chip.click()
                page.wait_for_timeout(400)
            page.screenshot(path=str(pngs[1]))
            b.close()
    except Exception as e:
        return [f"--shots asked for but the capture failed: {type(e).__name__}: {e}"]
    missing = [str(x) for x in pngs if not x.is_file() or x.stat().st_size == 0]
    if missing:
        return [f"screenshots not written: {missing}"]
    print(f"  wrote {pngs[0].name} and {pngs[1].name}; open them and look before handing over")
    return []


def main():
    if len(sys.argv) < 2 or sys.argv[1].startswith("-"):
        print(__doc__)
        sys.exit(2)
    path = sys.argv[1]
    raw = pathlib.Path(path).read_text(encoding="utf-8")
    print(path)
    problems = structural(raw)
    if problems:
        for pr in problems:
            print(f"  FAIL  {pr}")
        sys.exit(1)
    problems = brand(raw)
    more, warnings, stats = cross_refs(raw)
    problems += more
    if stats:
        print(f"  {stats['nodes']} nodes, {stats['edges']} edges, {stats['labels']} labels, {stats['flows']} flows")
    for w in warnings:
        print(f"  warn  {w}")
    if "--shots" in sys.argv:
        problems += shots(path)
    for pr in problems:
        print(f"  FAIL  {pr}")
    if not problems:
        print("  pass  complete, branded, and every reference resolves")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
