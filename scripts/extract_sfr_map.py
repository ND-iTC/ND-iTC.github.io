#!/usr/bin/env python3
"""Extract the NDcPP v4.0 SFR dependency map from the published HTML.

Reads cPP/NDcPP_v4_0.html (SFR headings + Annex E "SFR Dependencies Analysis")
and SD/ND_Supporting_Document_4_0.html (evaluation-activity anchors), and writes
data/ndcpp_v4_sfr.json for the requirements map page. Standard library only.
The PDFs stay authoritative; this is a navigation aid.

    python3 scripts/extract_sfr_map.py
"""
import html, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CPP = ROOT / "cPP/NDcPP_v4_0.html"
SD = ROOT / "SD/ND_Supporting_Document_4_0.html"
OUT = ROOT / "data/ndcpp_v4_sfr.json"

SFR_RE = re.compile(r"\b[A-Z]{3}_[A-Z]{2,4}(?:_EXT)?\.\d+(?:/[A-Za-z0-9_]+)?")
KINDS = [  # (top-level section id prefix, requirement type)
    ("_mandatory_security_functional_requirements", "mandatory"),
    ("_optional_security_requirements", "optional"),
    ("_selection_based_security_requirements", "selection-based"),
]


def text(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def headings(doc):
    return [(m.start(), int(m.group(1)), m.group(2), text(m.group(3)))
            for m in re.finditer(r'<h([2-6]) id="([^"]+)">(.*?)</h\1>', doc, re.S)]


def dep_groups(items):
    """Annex E dependency lines -> AND-groups of alternatives.

    Each line is one dependency that must be met. "A or B" lists alternatives;
    "A, [B or C]" is two separate dependencies; "None" means no dependencies.
    """
    groups = []
    for line in items:
        if line.strip().lower() == "none":
            continue
        line = re.sub(r",\s*or\b", " or", line)  # "A, or B" is still one alternatives list
        for part in re.split(r",\s*(?![^\[]*\])", line):  # split on commas outside [brackets]
            part = part.strip().strip("[]").strip()
            if part:
                groups.append({"text": part, "any_of": SFR_RE.findall(part)})
    return groups


def cell_items(td):
    """Paragraph texts of one table cell (one dependency / rationale per line)."""
    ps = re.findall(r"<p[^>]*>(.*?)</p>", td, re.S)
    return [text(p) for p in ps if text(p)]


def main():
    cpp = CPP.read_text(encoding="utf-8")
    hs = headings(cpp)

    # --- SFR list, with requirement type from the enclosing top-level section
    sfrs, kind = {}, None
    for pos, lvl, hid, title in hs:
        if lvl == 2:
            kind = next((k for p, k in KINDS if hid.startswith(p)), None)
        m = re.match(r"^[\d.A-Z]+\.?\s+((?:[A-Z]{3}_\w+\.\d+(?:/\w+)?))\s+(.*)$", title)
        if lvl in (4, 5) and m and kind and m.group(1) not in sfrs:
            sid = m.group(1)
            sfrs[sid] = {"id": sid, "title": m.group(2), "type": kind,
                         "family": sid.split("_")[0] + "_" + sid.split("_")[1].split(".")[0],
                         "anchor": hid, "ext": "_EXT" in sid, "deps": [], "rationale": []}
    if not sfrs:
        sys.exit("no SFR headings found: has the cPP HTML structure changed?")

    # --- Annex E dependency table
    i = cpp.find('id="_sfr_dependencies_analysis"')
    seg = cpp[i:]
    nxt = re.search(r"<h[23] id=", seg[40:])
    seg = seg[: nxt.start() + 40] if nxt else seg
    rows, seen_rows, warnings = 0, {}, []
    for tr in re.findall(r"<tr>(.*?)</tr>", seg, re.S):
        tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)
        if len(tds) != 3:
            continue
        sid = text(tds[0])
        deps = cell_items(tds[1])
        if sid not in sfrs:
            # Annex E may list an SFR the heading scan missed: keep it, typed unknown
            sfrs[sid] = {"id": sid, "title": "", "type": "unknown",
                         "family": sid.split("_")[0] + "_" + sid.split("_")[1].split(".")[0],
                         "anchor": None, "ext": "_EXT" in sid, "deps": [], "rationale": []}
        seen_rows[sid] = seen_rows.get(sid, 0) + 1
        new_deps, new_rat = dep_groups(deps), cell_items(tds[2])
        if seen_rows[sid] > 1:  # Annex E lists it twice: keep both rows, flag it for the iTC
            sfrs[sid]["deps"] += [d for d in new_deps if d not in sfrs[sid]["deps"]]
            sfrs[sid]["rationale"] += [r for r in new_rat if r not in sfrs[sid]["rationale"]]
            sfrs[sid]["note"] = "Annex E lists this requirement more than once with different dependencies; all of them are shown."
            warnings.append("%s appears %d times in Annex E" % (sid, seen_rows[sid]))
        else:
            sfrs[sid]["deps"], sfrs[sid]["rationale"] = new_deps, new_rat
        rows += 1

    # --- Resolve SFRs whose own heading is not "<id> <title>": iterations of an SFR
    # share its heading (FCS_COP.1/Hash under FCS_COP.1); family-style headings
    # (e.g. "FCS_NTP_EXT NTP Protocol") are found by the first mention in Annex A/B.
    def section_at(pos):
        cur = None
        for hp, lvl, hid, _ in hs:
            if hp > pos:
                break
            if lvl == 2:
                cur = hid
        return cur, None
    for s in sfrs.values():
        if s["type"] != "unknown":
            continue
        base = s["id"].split("/")[0]
        if "/" in s["id"] and base in sfrs and sfrs[base]["type"] != "unknown":
            s["type"], s["anchor"] = sfrs[base]["type"], sfrs[base]["anchor"]
            s["title"] = s["title"] or sfrs[base]["title"]
            continue
        fam = s["id"].split(".")[0]  # e.g. FCS_NTP_EXT
        cands = []
        for hp, lvl, hid, title in hs:
            top, _ = section_at(hp)
            k = next((k for p, k in KINDS if top and top.startswith(p)), None)
            if k in ("optional", "selection-based") and lvl >= 4 and fam in title:
                cands.append((-lvl, hp, k, hid, title))
        if cands:  # deepest matching heading is the requirement itself, not its parent group
            _, _, k, hid, title = min(cands)
            s["type"], s["anchor"] = k, hid
            s["title"] = s["title"] or re.sub(r"^[\d.A-Z]+\.?\s+|\s*\(.*\)$", "", title)

    # A heading that is only a parent of iterations (FCS_COP.1 -> FCS_COP.1/Hash ...) has no
    # Annex E row; dependencies that name it mean "any iteration", so list the members.
    for s in sfrs.values():
        kids = sorted(k for k in sfrs if k.startswith(s["id"] + "/"))
        if kids and s["id"] not in seen_rows:
            s["members"] = kids
            s["note"] = "Parent heading for the iterations below. A dependency on %s refers to the iterations." % s["id"]

    # --- SD anchors: heading that names the SFR
    sd_anchor = {}
    if SD.exists():
        for _, _, hid, title in headings(SD.read_text(encoding="utf-8")):
            m = SFR_RE.search(title)
            if m and m.group(0) not in sd_anchor:
                sd_anchor[m.group(0)] = hid
    for s in sfrs.values():
        s["sd_anchor"] = sd_anchor.get(s["id"])

    # --- reverse edges (used by) and unresolved dependency names
    for s in sfrs.values():
        s["used_by"] = []
    unresolved = set()
    for s in sfrs.values():
        for d in s["deps"]:
            for t in d["any_of"]:
                if t in sfrs:
                    sfrs[t]["used_by"].append(s["id"])
                else:
                    unresolved.add(t)  # CC component not defined in this cPP (e.g. FPT_STM.1)
    for s in sfrs.values():
        s["used_by"] = sorted(set(s["used_by"]))

    for w in warnings:
        print("WARNING:", w)
    out = {"document": "NDcPP v4.0", "source": "cPP/NDcPP_v4_0.html, Annex E.1",
           "sfrs": sorted(sfrs.values(), key=lambda s: s["id"]),
           "external_components": sorted(unresolved)}
    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    by = {}
    for s in sfrs.values():
        by[s["type"]] = by.get(s["type"], 0) + 1
    print(f"{len(sfrs)} SFRs {by}; {rows} Annex E rows; {len(unresolved)} external components; wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
