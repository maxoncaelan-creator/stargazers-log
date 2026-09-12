#!/usr/bin/env python3
"""Scan fetched pages for AHPRA / TGA advertising compliance indicators.

Every match is an INDICATOR REQUIRING REVIEW, never a determination of breach.
Context decides: 'best' inside 'best practice' is fine, an inducement with
visible terms is fine, and a review a practitioner does not control on a
third-party site is treated differently from one republished as advertising.
The script's job is to find candidates fast and give a human the snippet
needed to judge them.
"""
import argparse, json, os, re, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_TERMS = os.path.join(HERE, "..", "references", "regulated_terms.json")

SEVERITY_ORDER = {"high": 0, "medium": 1, "review": 2, "info": 3}


def visible_text(html):
    """Strip markup to approximate what a consumer actually reads."""
    h = re.sub(r"(?is)<(script|style|noscript|template)\b.*?</\1>", " ", html)
    h = re.sub(r"(?is)<!--.*?-->", " ", h)
    h = re.sub(r"(?s)<[^>]+>", " ", h)
    h = (h.replace("&nbsp;", " ").replace("&amp;", "&").replace("&#039;", "'")
          .replace("&quot;", '"').replace("&lt;", "<").replace("&gt;", ">"))
    return re.sub(r"\s+", " ", h)


def make_pattern(term):
    """Word-boundary match, tolerant of whitespace runs and simple plurals.

    Two details matter in practice. Terms containing '%' or '#' can't rely on \b
    at that edge, so bound only where a word character actually sits. And clinic
    copy overwhelmingly uses plurals ("anti-wrinkle injections", "lip fillers"),
    so allow an optional trailing s/es rather than needing every plural listed.
    """
    esc = r"\s+".join(re.escape(w) for w in term.split())
    left = r"\b" if term[:1].isalnum() else ""
    if term[-1:].isalnum():
        right = r"(?:es|s)?\b" if not term.endswith("s") else r"\b"
    else:
        right = ""
    return re.compile(left + esc + right, re.I)


def scan_text(text, pattern, term, limit=3):
    hits = []
    for m in pattern.finditer(text):
        if len(hits) < limit:
            s = max(0, m.start() - 70)
            e = min(len(text), m.end() + 70)
            hits.append(("..." + text[s:e].strip() + "...").replace("\n", " "))
    n = len(pattern.findall(text))
    return n, hits


def main():
    ap = argparse.ArgumentParser(description="AHPRA/TGA advertising indicator scan")
    ap.add_argument("fetched_dir", help="directory produced by fetch_site.py")
    ap.add_argument("--terms", default=DEFAULT_TERMS)
    ap.add_argument("--out", help="write findings JSON here")
    ap.add_argument("--target-type", choices=["clinic", "agency"], default="clinic",
                    help="clinic = regulated health service (AHPRA applies to the site "
                         "itself); agency = marketing firm (AHPRA does not bind their own "
                         "site, so weight the findings differently)")
    args = ap.parse_args()

    terms = json.load(open(args.terms))
    manifest = json.load(open(os.path.join(args.fetched_dir, "manifest.json")))
    pages_dir = os.path.join(args.fetched_dir, "pages")

    compiled = {}
    for cat, spec in terms.items():
        if cat == "_meta":
            continue
        compiled[cat] = (spec, [(t, make_pattern(t)) for t in spec["terms"]])

    findings = []
    per_page_counts = defaultdict(int)

    for rec in manifest["fetched"]:
        path = os.path.join(pages_dir, rec["file"])
        if not os.path.exists(path):
            continue
        raw = open(path, encoding="utf8", errors="replace").read()
        vis = visible_text(raw)
        for cat, (spec, pats) in compiled.items():
            haystack = raw if spec.get("scan_raw_html") else vis
            for term, pat in pats:
                n, snips = scan_text(haystack, pat, term)
                if n:
                    findings.append({
                        "category": cat,
                        "severity": spec["severity"],
                        "term": term,
                        "url": rec["url"],
                        "count": n,
                        "snippets": snips,
                    })
                    per_page_counts[rec["url"]] += n

    findings.sort(key=lambda f: (SEVERITY_ORDER.get(f["severity"], 9), -f["count"]))

    summary = defaultdict(lambda: {"terms": set(), "pages": set(), "total": 0})
    for f in findings:
        s = summary[f["category"]]
        s["terms"].add(f["term"])
        s["pages"].add(f["url"])
        s["total"] += f["count"]

    out = {
        "target": manifest["base"],
        "target_type": args.target_type,
        "pages_scanned": len(manifest["fetched"]),
        "disclaimer": ("Indicators requiring human review. Not legal advice and not a "
                       "determination of breach. AHPRA enforcement is risk-based; context "
                       "decides whether any match is actually non-compliant."),
        "summary": {k: {"unique_terms": sorted(v["terms"]),
                        "pages_affected": len(v["pages"]),
                        "total_occurrences": v["total"],
                        "severity": terms[k]["severity"],
                        "why": terms[k]["why"]}
                    for k, v in summary.items()},
        "worst_pages": sorted(per_page_counts.items(), key=lambda kv: -kv[1])[:15],
        "findings": findings,
    }

    if args.out:
        with open(args.out, "w") as f:
            json.dump(out, f, indent=1)

    # Console report
    print(f"\n=== COMPLIANCE INDICATORS: {manifest['base']} ({args.target_type}) ===")
    print(f"pages scanned: {out['pages_scanned']}\n")
    if not summary:
        print("  No indicators matched. Verify the fetch actually captured content.")
    for sev in ("high", "medium", "review", "info"):
        cats = [(k, v) for k, v in out["summary"].items() if v["severity"] == sev]
        if not cats:
            continue
        print(f"--- {sev.upper()} ---")
        for cat, v in sorted(cats, key=lambda kv: -kv[1]["total_occurrences"]):
            print(f"  {cat}: {v['total_occurrences']} occurrences, "
                  f"{v['pages_affected']} pages, {len(v['unique_terms'])} distinct terms")
            print(f"    terms: {', '.join(v['unique_terms'][:12])}"
                  + (" ..." if len(v["unique_terms"]) > 12 else ""))
        print()
    if out["worst_pages"]:
        print("--- PAGES WITH MOST INDICATORS ---")
        for u, n in out["worst_pages"][:8]:
            print(f"  {n:>5}  {u}")
    if args.target_type == "agency":
        claims = out["summary"].get("agency_compliance_claims", {})
        print("\n--- READING THIS AS AN AGENCY AUDIT ---")
        print("  AHPRA and the TGA bind regulated health services, not marketing firms.")
        print("  Testimonials, before/after language and inducements on an AGENCY's own")
        print("  site are therefore not breaches — do not report them as such.")
        if claims:
            print(f"  This agency makes compliance claims on {claims['pages_affected']} "
                  f"of {out['pages_scanned']} pages scanned "
                  f"({claims['total_occurrences']} mentions).")
            print("  Those claims are the thing to test. Run find_client_sites.py, then")
            print("  scan their live client sites with --target-type clinic. A firm")
            print("  advertising compliance whose clients carry S4 drug names is the")
            print("  finding that actually matters.")
        else:
            print("  No explicit compliance claims found — they may not compete on this axis.")
    print(f"\n{out['disclaimer']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
