#!/usr/bin/env python3
"""Detect analytics, advertising and session-recording tags, and extract their IDs.

Two questions this answers that matter commercially:

1. Is the money being measured? A clinic paying for Google Ads with no conversion
   tag (AW-) is buying clicks it cannot attribute. That is the single most common
   and most expensive gap in small-practice marketing.

2. Is sensitive data leaking? Health information is 'sensitive information' under
   the Australian Privacy Act. Session recorders and ad pixels on pages carrying
   symptom pickers, booking forms or intake fields can transmit health-related
   data to third parties. This is a privacy exposure, distinct from AHPRA
   advertising rules, and it is largely invisible to the practice owner.
"""
import argparse, json, os, re, subprocess, sys
from collections import Counter, defaultdict

# GTM serialises each configured tag as "function":"__<type>". These codes are the
# only reliable way to tell a configured tag from the container's boilerplate —
# the string "conversion" appears dozens of times in every container regardless.
GTM_TAG_TYPES = {
    "awct": "Google Ads Conversion Tracking", "sp": "Google Ads Remarketing",
    "gclidw": "Conversion Linker", "gaawc": "GA4 Configuration",
    "gaawe": "GA4 Event", "googtag": "Google Tag", "ua": "Universal Analytics",
    "flc": "Floodlight Counter", "fls": "Floodlight Sales", "html": "Custom HTML",
    "img": "Custom Image Pixel", "fsl": "Form Submit trigger",
    "lcl": "Link Click trigger", "cl": "Click trigger", "sdl": "Scroll Depth",
    "jel": "Element Visibility", "ytl": "YouTube trigger", "tl": "Timer trigger",
}


def inspect_gtm(container_id):
    """Fetch a public GTM container and report which tags are actually configured."""
    url = f"https://www.googletagmanager.com/gtm.js?id={container_id}"
    try:
        js = subprocess.run(["curl", "-sSL", "--compressed", "--max-time", "45",
                             "-A", "Mozilla/5.0", url],
                            capture_output=True, timeout=60).stdout.decode("utf8", "replace")
    except Exception:
        return None
    if len(js) < 1000:
        return None
    counts = Counter(re.findall(r'"function"\s*:\s*"__([a-z0-9_]+)"', js))
    return {
        "container": container_id,
        "bytes": len(js),
        "tags": {GTM_TAG_TYPES.get(t, t): n for t, n in counts.most_common()},
        "ga4_ids": sorted(set(re.findall(r"\bG-[A-Z0-9]{8,}\b", js))),
        "ads_ids": sorted(set(re.findall(r"AW-\d{9,}(?:/[\w-]+)?", js))),
        "has_ads_conversion": "awct" in counts,
        "has_remarketing": "sp" in counts,
        "has_conversion_linker": "gclidw" in counts,
        "has_ga4": bool({"gaawc", "gaawe", "googtag"} & set(counts)),
    }

# name -> (detection regexes, id regex or None, category)
TAGS = {
    "Google Tag Manager":   ([r"googletagmanager\.com/gtm\.js", r"GTM-[A-Z0-9]+"], r"GTM-[A-Z0-9]{4,}", "tag-manager"),
    "Google Analytics 4":   ([r"gtag/js\?id=G-", r"\bG-[A-Z0-9]{8,}\b"], r"\bG-[A-Z0-9]{8,}\b", "analytics"),
    "Google Ads":           ([r"gtag/js\?id=AW-", r"\bAW-\d{9,}", r"googleadservices\.com"], r"AW-\d{9,}(?:/[\w-]+)?", "ads"),
    "Google Ads Remarketing": ([r"googleads\.g\.doubleclick\.net", r"google_conversion", r"/pagead/viewthroughconversion/"], r"viewthroughconversion/(\d+)", "ads"),
    "Google Floodlight":    ([r"fls\.doubleclick\.net"], None, "ads"),
    "Universal Analytics (legacy)": ([r"\bUA-\d{4,}-\d+"], r"UA-\d{4,}-\d+", "analytics"),
    "Google Optimize":      ([r"optimize\.js\?id=OPT-"], r"OPT-[A-Z0-9]+", "testing"),
    "Meta (Facebook) Pixel": ([r"connect\.facebook\.net/[^/]+/fbevents\.js", r"\bfbq\s*\(", r"facebook\.com/tr\?id="], r"fbq\s*\(\s*['\"]init['\"]\s*,\s*['\"](\d{10,})['\"]", "ads"),
    "TikTok Pixel":         ([r"analytics\.tiktok\.com", r"\bttq\."], r"ttq\.load\(\s*['\"]([A-Z0-9]+)['\"]", "ads"),
    "LinkedIn Insight":     ([r"snap\.licdn\.com", r"_linkedin_partner_id"], r"_linkedin_partner_id\s*=\s*['\"](\d+)['\"]", "ads"),
    "Microsoft/Bing UET":   ([r"bat\.bing\.com", r"\buetq\b"], r"ti\s*:\s*['\"](\d+)['\"]", "ads"),
    "Pinterest Tag":        ([r"\bpintrk\b", r"ct\.pinterest\.com"], r"pintrk\('load'\s*,\s*['\"](\d+)['\"]", "ads"),
    "Snap Pixel":           ([r"sc-static\.net/scevent", r"\bsnaptr\b"], None, "ads"),
    "X (Twitter) Pixel":    ([r"static\.ads-twitter\.com", r"\btwq\b"], None, "ads"),
    "Reddit Pixel":         ([r"redditstatic\.com/ads", r"\brdt\("], None, "ads"),
    "Hotjar":               ([r"static\.hotjar\.com", r"\bhjid\b"], r"hjid\s*:\s*(\d+)", "session-recording"),
    "Microsoft Clarity":    ([r"clarity\.ms"], r"clarity\.ms/tag/([a-z0-9]+)", "session-recording"),
    "Mouseflow":            ([r"mouseflow\.com"], None, "session-recording"),
    "FullStory":            ([r"fullstory\.com/s/fs\.js", r"\bFS\.identify"], None, "session-recording"),
    "Lucky Orange":         ([r"luckyorange\.com"], None, "session-recording"),
    "Smartlook":            ([r"smartlook\.com"], None, "session-recording"),
    "VWO":                  ([r"visualwebsiteoptimizer\.com"], None, "testing"),
    "CallRail":             ([r"callrail\.com"], None, "call-tracking"),
    "CallTrackingMetrics":  ([r"calltrackingmetrics\.com"], None, "call-tracking"),
    "HubSpot":              ([r"js\.hs-scripts\.com", r"js\.hsforms\.net"], r"hs-scripts\.com/(\d+)", "crm"),
    "ActiveCampaign":       ([r"prism\.app-us1\.com", r"trackcmp\.net"], None, "crm"),
    "Klaviyo":              ([r"static\.klaviyo\.com"], None, "crm"),
    "Intercom":             ([r"widget\.intercom\.io"], None, "chat"),
    "Tawk.to":              ([r"embed\.tawk\.to"], None, "chat"),
    "Drift":                ([r"js\.driftt\.com"], None, "chat"),
    "Podium":               ([r"connect\.podium\.com"], None, "chat"),
    "Cloudflare Insights":  ([r"static\.cloudflareinsights\.com"], None, "analytics"),
    "Hyros":                ([r"hyros\.com", r"\bhyrosTrack"], None, "ads"),
    "Segment":              ([r"cdn\.segment\.com"], None, "analytics"),
}

# Pages where a visitor is likely to disclose health information.
SENSITIVE_PAGE = re.compile(
    r"(contact|book|booking|appointment|enquir|inquir|referral|intake|new-patient|"
    r"consult|assessment|form|telehealth)", re.I)

CONSENT_HINT = re.compile(
    r"(cookieyes|cookiebot|onetrust|osano|termly|complianz|cookie-?consent|"
    r"cookie-?notice|iubenda|usercentrics|klaro|civic ?cookie|gdpr|"
    r"consent ?mode|gtag\(\s*['\"]consent['\"])", re.I)


def main():
    ap = argparse.ArgumentParser(description="Detect tracking pixels and analytics tags")
    ap.add_argument("fetched_dir")
    ap.add_argument("--out")
    ap.add_argument("--target-type", choices=["clinic", "agency"], default="clinic")
    ap.add_argument("--inspect-gtm", action="store_true",
                    help="fetch any GTM container found and list the tags actually "
                         "configured inside it — settles whether Ads conversion "
                         "tracking exists when raw HTML cannot")
    args = ap.parse_args()

    man = json.load(open(os.path.join(args.fetched_dir, "manifest.json")))
    pages_dir = os.path.join(args.fetched_dir, "pages")

    found = defaultdict(lambda: {"pages": set(), "ids": set(), "category": ""})
    consent_pages, sensitive_pages = set(), set()
    forms_on = defaultdict(int)

    for rec in man["fetched"]:
        p = os.path.join(pages_dir, rec["file"])
        if not os.path.exists(p):
            continue
        html = open(p, encoding="utf8", errors="replace").read()
        url = rec["url"]
        if CONSENT_HINT.search(html):
            consent_pages.add(url)
        if SENSITIVE_PAGE.search(url) or re.search(r"<form\b", html, re.I):
            n = len(re.findall(r"<form\b", html, re.I))
            if n:
                forms_on[url] = n
            if SENSITIVE_PAGE.search(url):
                sensitive_pages.add(url)

        for name, (pats, idpat, cat) in TAGS.items():
            if any(re.search(pt, html, re.I) for pt in pats):
                f = found[name]
                f["pages"].add(url)
                f["category"] = cat
                if idpat:
                    for m in re.findall(idpat, html):
                        f["ids"].add(m if isinstance(m, str) else m[0])

    out = {
        "target": man["base"],
        "pages_scanned": len(man["fetched"]),
        "tags": {k: {"category": v["category"], "ids": sorted(v["ids"]),
                     "page_count": len(v["pages"]), "pages": sorted(v["pages"])[:5]}
                 for k, v in sorted(found.items())},
        "consent_tool_pages": sorted(consent_pages),
        "sensitive_pages": sorted(sensitive_pages),
        "pages_with_forms": dict(sorted(forms_on.items(), key=lambda kv: -kv[1])[:10]),
    }

    gtm_reports = []
    if args.inspect_gtm:
        for cid in out["tags"].get("Google Tag Manager", {}).get("ids", []):
            r = inspect_gtm(cid)
            if r:
                gtm_reports.append(r)
    out["gtm_containers"] = gtm_reports

    cats = defaultdict(list)
    for k, v in out["tags"].items():
        cats[v["category"]].append(k)

    # --- findings a human should act on ---
    notes = []
    has_ads = "Google Ads" in found or "Google Ads Remarketing" in found
    if gtm_reports:                      # container contents beat raw-HTML inference
        has_ads = has_ads or any(g["has_ads_conversion"] for g in gtm_reports)
    has_ga = "Google Analytics 4" in found or "Universal Analytics (legacy)" in found
    if gtm_reports:
        has_ga = has_ga or any(g["has_ga4"] for g in gtm_reports)
    has_gtm = "Google Tag Manager" in found
    recorders = cats.get("session-recording", [])

    if not has_ads and not has_gtm:
        notes.append(("HIGH", "No Google Ads conversion tag (AW-) and no Tag Manager found. "
                              "If this business is paying for Google Ads, it cannot attribute "
                              "conversions — spend is being optimised blind."))
    elif not has_ads and has_gtm and gtm_reports:
        notes.append(("HIGH", "Tag Manager container inspected and it contains NO Google Ads "
                              "Conversion Tracking tag. If this business runs Google Ads, "
                              "conversions are not being measured client-side. Absence of the "
                              "Conversion Linker tag compounds it: that tag is what turns the "
                              "gclid into an attributable cookie, so attribution degrades even "
                              "where conversions are imported from GA4."))
    elif not has_ads and has_gtm:
        notes.append(("REVIEW", "Tag Manager is present but no Google Ads tag is visible in the "
                                "raw HTML. GTM injects tags at runtime — re-run with "
                                "--inspect-gtm to read the container and settle it."))
    if not has_ga and not has_gtm:
        notes.append(("HIGH", "No analytics tag found at all — no GA4, no GTM. The site's traffic "
                              "is effectively unmeasured."))
    if "Universal Analytics (legacy)" in found and not has_ga:
        notes.append(("HIGH", "Only legacy Universal Analytics found. UA stopped processing data "
                              "in 2023 — this site is collecting nothing."))
    if recorders and args.target_type == "clinic":
        notes.append(("HIGH", f"Session recording active ({', '.join(recorders)}) on a health "
                              "service site. These tools capture keystrokes and form interactions. "
                              "Health information is 'sensitive information' under the Privacy Act; "
                              "recording intake or booking forms without explicit consent and field "
                              "masking is a privacy exposure, separate from AHPRA advertising rules."))
    if "Meta (Facebook) Pixel" in found and args.target_type == "clinic":
        overlap = sorted(set(found["Meta (Facebook) Pixel"]["pages"]) & sensitive_pages)
        if overlap:
            notes.append(("HIGH", f"Meta Pixel is present on {len(overlap)} page(s) where a visitor "
                                  "discloses health details (e.g. booking/contact). Transmitting "
                                  "health-adjacent behaviour to Meta has been the subject of "
                                  "significant regulatory and litigation action overseas. Review "
                                  "what events fire and what parameters they carry."))
        else:
            notes.append(("REVIEW", "Meta Pixel present. On a health site, check which events fire "
                                    "and whether any carry condition or treatment detail."))
    if found and not consent_pages:
        notes.append(("REVIEW", "Tracking tags found but no consent-management tool detected. "
                                "Australia does not mandate cookie banners the way the EU does, but "
                                "sensitive-information handling still needs a defensible basis — and "
                                "Google Consent Mode affects ad measurement quality."))

    if args.out:
        json.dump({**out, "notes": notes}, open(args.out, "w"), indent=1)

    print(f"\n=== TRACKING & PIXELS: {man['base']} ===")
    print(f"pages scanned: {out['pages_scanned']}\n")
    if not out["tags"]:
        print("  No tracking tags detected in raw HTML.")
    for cat in ("tag-manager", "analytics", "ads", "session-recording", "testing",
                "call-tracking", "crm", "chat"):
        if cat not in cats:
            continue
        print(f"--- {cat} ---")
        for name in cats[cat]:
            v = out["tags"][name]
            ids = f"  ids: {', '.join(v['ids'][:4])}" if v["ids"] else ""
            print(f"  {name:<28} on {v['page_count']}/{out['pages_scanned']} pages{ids}")
        print()
    for g in gtm_reports:
        print(f"--- GTM container {g['container']} ({g['bytes']:,} bytes) ---")
        for t, n in g["tags"].items():
            print(f"  {t} x{n}")
        print(f"  GA4 ids: {g['ga4_ids'] or 'none'} | Ads ids: {g['ads_ids'] or 'none'}")
        print(f"  Ads conversion tag: {'YES' if g['has_ads_conversion'] else 'NO'}"
              f" | Remarketing: {'YES' if g['has_remarketing'] else 'NO'}"
              f" | Conversion Linker: {'YES' if g['has_conversion_linker'] else 'NO'}")
        print()
    if consent_pages:
        print(f"  consent tool detected on {len(consent_pages)} page(s)")
    if forms_on:
        print(f"  pages with forms: {len(forms_on)} "
              f"(e.g. {', '.join(list(forms_on)[:2])})")
    if notes:
        print("\n--- FINDINGS ---")
        for sev, text in notes:
            print(f"  [{sev}] {text}\n")
    print("Note: tags injected at runtime by a tag manager are not visible in raw HTML. "
          "Confirm with Google Tag Assistant or browser devtools before concluding a tag "
          "is absent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
