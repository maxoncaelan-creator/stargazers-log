#!/usr/bin/env python3
"""Extract an agency's client sites from its own marketing pages.

This is the point of the whole exercise when the target is a competitor agency.
AHPRA and the TGA bind regulated health services, not marketing firms — so an
agency's own website is not where its compliance competence shows. The proof is
in the client work. An agency advertising "AHPRA compliant" whose live client
sites carry prescription-drug brand names is the finding that matters, and it
is only reachable by pivoting from the agency to the clients it names.
"""
import argparse, json, os, re, sys
import urllib.parse as up
from collections import defaultdict

# Hosts that are never clients — platforms, socials, CDNs, tooling.
NOISE = re.compile(
    r"(google|gstatic|googleapis|youtube|facebook|instagram|linkedin|twitter|x\.com|tiktok|"
    r"pinterest|vimeo|wordpress|w3\.org|schema\.org|gmpg\.org|cloudflare|jsdelivr|unpkg|"
    r"cdnjs|jquery|fontawesome|trustindex|trustpilot|bing|yahoo|apple|microsoft|adobe|"
    r"mailchimp|hubspot|calendly|stripe|paypal|xero|shopify|wix|squarespace|godaddy|"
    r"bit\.ly|goo\.gl|gravatar|wp\.com|zoom\.us|whatsapp|messenger|maps\.)", re.I)

# Pages where an agency shows off who it works for.
CLIENT_PAGE_HINT = re.compile(
    r"(case-stud|portfolio|our-work|clients|results|success|projects|testimonial|reviews)", re.I)

HEALTH_HINT = re.compile(
    r"(dental|dentist|ortho|smile|physio|chiro|osteo|podiatr|psycholog|clinic|medical|"
    r"health|surgery|surgeon|skin|cosmetic|aesthetic|laser|derma|vein|eye|optical|"
    r"hearing|audiolog|fertility|ivf|plastic|wellness|therapy|rehab|ndis|vet)", re.I)


def main():
    ap = argparse.ArgumentParser(description="Find an agency's client sites from its own pages")
    ap.add_argument("fetched_dir")
    ap.add_argument("--out")
    ap.add_argument("--health-only", action="store_true",
                    help="keep only domains whose name suggests a health service")
    args = ap.parse_args()

    man = json.load(open(os.path.join(args.fetched_dir, "manifest.json")))
    pages_dir = os.path.join(args.fetched_dir, "pages")
    host = man["host"]
    root = ".".join(host.split(".")[-3:]) if host.count(".") > 1 else host

    candidates = defaultdict(lambda: {"count": 0, "found_on": set(), "anchors": set(),
                                      "from_client_page": False})

    for rec in man["fetched"]:
        p = os.path.join(pages_dir, rec["file"])
        if not os.path.exists(p):
            continue
        html = open(p, encoding="utf8", errors="replace").read()
        on_client_page = bool(CLIENT_PAGE_HINT.search(rec["url"]))

        for m in re.finditer(r'<a[^>]+href="(https?://[^"]+)"[^>]*>(.*?)</a>', html, re.S | re.I):
            link, anchor = m.group(1), re.sub(r"<[^>]+>", "", m.group(2)).strip()
            netloc = up.urlparse(link).netloc.lower().lstrip("www.")
            if not netloc or netloc.endswith(root) or NOISE.search(netloc):
                continue
            c = candidates[netloc]
            c["count"] += 1
            c["found_on"].add(rec["url"])
            if anchor and len(anchor) < 80:
                c["anchors"].add(anchor)
            if on_client_page:
                c["from_client_page"] = True

    # Second pass: brand names carried by logo imagery. Most agencies display client
    # logos as images with no link, so alt text and filenames are the only trace.
    logo_names = defaultdict(lambda: {"sources": set(), "pages": set()})
    # Agencies stamp their own name into client logo filenames; strip it so the
    # client brand is what survives.
    agency_token = re.escape(re.split(r"[.\-]", host.replace("www.", ""))[0]) \
        if len(re.split(r"[.\-]", host.replace("www.", ""))[0]) > 3 else ""
    LOGO_HINT = re.compile(r"(logo|client|brand|partner)", re.I)
    for rec in man["fetched"]:
        p2 = os.path.join(pages_dir, rec["file"])
        if not os.path.exists(p2):
            continue
        html = open(p2, encoding="utf8", errors="replace").read()
        for tag in re.findall(r"<img [^>]*>", html):
            alt = re.search(r'alt="([^"]*)"', tag)
            src = re.search(r'(?:src|data-src|data-lazy-src)="([^"]*)"', tag)
            alt_t = (alt.group(1) if alt else "").strip()
            src_t = (src.group(1) if src else "")
            fname = src_t.split("/")[-1].split("?")[0]
            if not (LOGO_HINT.search(alt_t) or LOGO_HINT.search(fname)):
                continue
            # Alt text is often just the filename, so clean both the same way.
            raw = alt_t or fname
            name = re.sub(r"\.(jpe?g|png|gif|svg|webp|avif)$", "", raw, flags=re.I)
            name = re.sub(r"(?i)[-_\s]*(logo|brand|client|partner)[s]?[-_\s]*", " ", name)
            if agency_token:                                              # agency's own tag
                name = re.sub(rf"(?i)[-_\s]*{agency_token}[-_\s]*", " ", name)
            # Agencies commonly suffix client logos with "<their name> Website".
            name = re.sub(r"(?i)[-_\s]*(\w+[-_\s]+)?(website|site|final|v\d+|copy)\s*$",
                          " ", name)
            name = re.sub(r"[-_]+", " ", name)
            name = re.sub(r"\s*\b\d{1,3}\b\s*$", "", name)               # trailing -01, -04
            name = re.sub(r"\s+", " ", name).strip(" -_|")
            if 2 < len(name) < 60 and not re.fullmatch(r"[\d\s x]+", name):
                logo_names[name]["sources"].add(src_t.split("/")[-1][:60])
                logo_names[name]["pages"].add(rec["url"])

    rows = []
    for dom, c in candidates.items():
        looks_health = bool(HEALTH_HINT.search(dom) or
                            any(HEALTH_HINT.search(a) for a in c["anchors"]))
        if args.health_only and not looks_health:
            continue
        rows.append({
            "domain": dom,
            "links": c["count"],
            "from_client_page": c["from_client_page"],
            "looks_health": looks_health,
            "anchors": sorted(c["anchors"])[:4],
            "found_on": sorted(c["found_on"])[:3],
        })
    # Most likely clients first: named on a case-study/portfolio page, health-shaped, linked often.
    rows.sort(key=lambda r: (not r["from_client_page"], not r["looks_health"], -r["links"]))

    merged = {}
    for k, v in logo_names.items():
        key = re.sub(r"[^a-z0-9]", "", k.lower())
        if not key:
            continue
        if key not in merged or len(k) < len(merged[key]["name"]):
            merged[key] = {"name": k, "looks_health": bool(HEALTH_HINT.search(k)),
                           "files": sorted(v["sources"])[:2], "pages": sorted(v["pages"])[:2]}
    logos = sorted(merged.values(), key=lambda r: (not r["looks_health"], r["name"].lower()))
    out = {"agency": man["base"], "candidates": rows, "logo_brand_names": logos}
    if args.out:
        json.dump(out, open(args.out, "w"), indent=1)

    print(f"\n=== CANDIDATE CLIENT SITES: {man['base']} ===")
    if not rows:
        print("  none found — the agency may not link clients, or may only show logos as images.")
        print("  Try: fetch more pages, or read case-study pages manually for business names.")
    for r in rows[:30]:
        flags = ("client-page " if r["from_client_page"] else "") + ("health" if r["looks_health"] else "")
        print(f"  {r['domain']:<45} links={r['links']:<3} {flags}")
        if r["anchors"]:
            print(f"      anchors: {'; '.join(r['anchors'][:3])[:100]}")
    if logos:
        print(f"\n--- CLIENT BRAND NAMES FROM LOGO IMAGERY ({len(logos)}) ---")
        print("  (agencies usually display client logos unlinked; search these names "
              "to find the live site)")
        for r in logos[:25]:
            print(f"  {r['name']:<45} {'health' if r['looks_health'] else ''}")
    print("\nNext: resolve these to live domains, then run fetch_site.py + "
          "compliance_scan.py --target-type clinic on each. An agency's own site is not "
          "a regulated health service, so its compliance claims are only testable "
          "against the client work it points to.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
