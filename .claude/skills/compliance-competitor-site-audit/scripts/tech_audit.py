#!/usr/bin/env python3
"""Technical audit: stack fingerprint, delivery, and asset-level waste.

The checks here are the ones that actually surfaced real defects in practice —
duplicated third-party scripts, fonts declared twice across two origins,
preload/media-query mismatches that break mobile LCP, and staging domains
leaking into production markup. Generic "score the site" output is much less
useful than naming a specific broken thing.
"""
import argparse, json, os, re, subprocess, sys, time
import urllib.parse as up
from collections import defaultdict

UA = "Mozilla/5.0 (Linux; Android 11) AppleWebKit/537.36 Chrome/141 Mobile Safari/537.36"

BUILDERS = [
    ("Elementor", [r"elementor-element", r"plugins/elementor", r'content="Elementor']),
    ("Bricks", [r"\bbrxe-", r"themes/bricks"]),
    ("Divi", [r"\bet_pb_", r"themes/Divi"]),
    ("WPBakery", [r"\bvc_row\b", r"js_composer"]),
    ("Oxygen", [r"\bct-section\b", r"oxygen-"]),
    ("Breakdance", [r"\bbde-", r"breakdance"]),
    ("Beaver Builder", [r"\bfl-builder", r"\bfl-node-"]),
    ("SiteOrigin", [r"siteorigin-panels"]),
    ("Gutenberg blocks", [r"wp-block-"]),
    ("Webflow", [r"\.webflow\.", r"w-container"]),
    ("Squarespace", [r"squarespace", r"sqs-block"]),
    ("Wix", [r"wixstatic", r"_wixCssImports"]),
    ("Shopify", [r"cdn\.shopify\.com"]),
    ("Duda", [r"\bdmBody\b", r"duda"]),
    ("HubSpot CMS", [r"hs-scripts\.com", r"hubspotusercontent"]),
]

PLUGINS = [
    ("Rank Math", r"rank-?math"), ("Yoast", r"yoast"), ("AIOSEO", r"aioseo|all-in-one-seo"),
    ("WP Rocket", r"wp-rocket"), ("LiteSpeed Cache", r"litespeed"),
    ("WP Super Cache", r"wp-super-cache"), ("W3 Total Cache", r"w3-total-cache"),
    ("Site Kit", r"google-site-kit"), ("Gravity Forms", r"gravityforms"),
    ("Contact Form 7", r"contact-form-7"), ("WooCommerce", r"woocommerce"),
    ("HotDoc", r"hotdoc"), ("HealthEngine", r"healthengine"), ("Cliniko", r"cliniko"),
    ("Nookal", r"nookal"), ("Halaxy", r"halaxy"), ("Timely", r"gettimely"),
]


def sh(cmd, timeout=60, retries=3):
    """Run a command, retrying on empty output.

    Transient connection resets otherwise abort an audit on a site that is
    perfectly reachable a second later.
    """
    for attempt in range(retries):
        try:
            out = subprocess.run(cmd, capture_output=True, timeout=timeout).stdout.decode("utf8", "replace")
        except Exception:
            out = ""
        if out:
            return out
        if attempt < retries - 1:
            time.sleep(1.5 * (attempt + 1))
    return ""


def timing(url, runs=3):
    out = []
    fmt = "%{time_namelookup} %{time_connect} %{time_appconnect} %{time_starttransfer} %{time_total} %{size_download} %{http_code}"
    for _ in range(runs):
        r = sh(["curl", "-sS", "-o", "/dev/null", "--compressed", "-A", UA,
                "-w", fmt, "--max-time", "45", url]).split()
        if len(r) == 7:
            out.append({"dns": float(r[0]), "connect": float(r[1]), "tls": float(r[2]),
                        "ttfb": float(r[3]), "total": float(r[4]),
                        "bytes": int(r[5]), "status": r[6]})
    return out


def main():
    ap = argparse.ArgumentParser(description="Technical site audit")
    ap.add_argument("url")
    ap.add_argument("--html", help="use an already-fetched homepage file instead of refetching")
    ap.add_argument("--out")
    ap.add_argument("--weigh-assets", action="store_true",
                    help="download every asset to measure real transfer weight (slower)")
    args = ap.parse_args()

    url = args.url if args.url.startswith("http") else "https://" + args.url
    host = up.urlparse(url).netloc

    html = open(args.html, encoding="utf8", errors="replace").read() if args.html else \
        sh(["curl", "-sSL", "--compressed", "-A", UA, "--max-time", "45", url])
    if not html:
        print("! could not retrieve HTML", file=sys.stderr)
        return 1

    res = {"url": url, "host": host, "html_bytes": len(html)}

    # --- stack ---
    res["generators"] = re.findall(r'<meta name="generator" content="([^"]*)"', html, re.I)
    res["builders"] = [name for name, pats in BUILDERS
                       if sum(len(re.findall(p, html, re.I)) for p in pats) > 0]
    res["builder_hit_counts"] = {
        name: sum(len(re.findall(p, html, re.I)) for p in pats)
        for name, pats in BUILDERS
        if sum(len(re.findall(p, html, re.I)) for p in pats) > 0}
    res["plugins"] = [n for n, p in PLUGINS if re.search(p, html, re.I)]
    res["wp_paths"] = sorted(set(re.findall(r"wp-content/(?:plugins|themes)/[A-Za-z0-9_.-]+", html)))

    # --- delivery ---
    hdr = sh(["curl", "-sS", "-o", "/dev/null", "-D", "-", "--compressed",
              "-A", UA, "--max-time", "30", url])
    res["headers"] = {k.lower(): v.strip() for k, v in
                      re.findall(r"(?m)^([A-Za-z0-9-]+):\s*(.+)$", hdr)}
    res["timing_runs"] = timing(url)
    if res["timing_runs"]:
        best = min(res["timing_runs"], key=lambda t: t["total"])
        res["best_run"] = best

    # --- origins & scripts ---
    srcs = re.findall(r'(?:src|href|data-rocket-src|data-src)="(https?://[^"]+)"', html)
    origins = defaultdict(int)
    for s in srcs:
        origins[up.urlparse(s).netloc] += 1
    res["origins"] = dict(sorted(origins.items(), key=lambda kv: -kv[1]))

    js_refs = re.findall(
        r'(?:src|data-src|data-rocket-src|data-cfsrc)="([^"]+?\.js(?:\?[^"]*)?)"', html)
    base_counts = defaultdict(list)
    for s in js_refs:
        base_counts[s.split("?")[0]].append(s)
    res["js_refs_total"] = len(js_refs)
    res["duplicate_scripts"] = {b: v for b, v in base_counts.items() if len(v) > 1}

    # --- staging / dev leakage: a strong and very common real defect ---
    leak = set()
    for s in srcs:
        n = up.urlparse(s).netloc
        if n and n != host and re.search(r"(staging|stg|dev|test|uat|mockup|preview|\.local)", n, re.I):
            leak.add(n)
    res["staging_leakage"] = sorted(leak)

    # --- fonts ---
    faces = re.findall(r"font-family:\s*'?\"?([A-Za-z0-9 ]+)'?\"?\s*;font-style", html)
    res["font_face_count"] = len(re.findall(r"@font-face", html))
    res["font_families"] = dict(sorted(
        ((f, faces.count(f)) for f in set(faces)), key=lambda kv: -kv[1]))
    res["font_origins"] = {
        "self_hosted_refs": len(re.findall(r"wp-content/(?:cache/)?fonts", html)),
        "google_gstatic_refs": len(re.findall(r"fonts\.gstatic\.com", html)),
        "google_apis_refs": len(re.findall(r"fonts\.googleapis\.com", html)),
    }

    # --- LCP preload sanity: preloaded image vs. responsive override ---
    preloads = re.findall(r'<link[^>]+rel="preload"[^>]*>', html)
    res["preloads"] = preloads[:10]
    def basename(u):
        return u.strip("'\"").split("?")[0].rstrip("/").split("/")[-1]

    pre_imgs = {basename(u) for u in re.findall(
        r'rel="preload"[^>]*?href="([^"]+?\.(?:webp|jpg|jpeg|png|avif))"', html)}
    pre_imgs |= {basename(u) for u in re.findall(
        r'href="([^"]+?\.(?:webp|jpg|jpeg|png|avif))"[^>]*?rel="preload"', html)}
    media_bgs = {basename(b) for b in re.findall(
        r"@media[^{]*\{(?:[^{}]*\{)?[^}]*?background-image:\s*url\(([^)]+)\)", html)}
    mismatch = sorted(media_bgs - pre_imgs) if pre_imgs else []
    res["preload_images"] = sorted(pre_imgs)  # basenames
    res["responsive_bg_images"] = sorted(media_bgs)
    res["preload_mismatch"] = sorted(mismatch)

    # --- images ---
    imgs = re.findall(r"<img [^>]*>", html)
    res["img_total"] = len(imgs)
    res["img_missing_alt"] = sum(1 for i in imgs if "alt=" not in i)
    res["img_missing_dims"] = sum(1 for i in imgs
                                  if not (re.search(r"\bwidth=", i) and re.search(r"\bheight=", i)))
    res["img_lazy"] = sum(1 for i in imgs if "loading=" in i)

    # --- optional real asset weights ---
    if args.weigh_assets:
        assets = sorted({s for s in srcs if re.search(
            r"\.(css|js|png|jpe?g|webp|avif|gif|svg|woff2?|ttf)(\?|$)", s, re.I)})
        weights, by_type, by_origin = [], defaultdict(int), defaultdict(int)
        for a in assets[:120]:
            n = len(sh(["curl", "-sSL", "--compressed", "-A", UA, "--max-time", "30", a], timeout=45).encode("utf8", "replace"))
            if n:
                ext = re.sub(r"\?.*", "", a).rsplit(".", 1)[-1].lower()
                weights.append({"url": a, "bytes": n, "ext": ext})
                by_type[ext] += n
                by_origin[up.urlparse(a).netloc] += n
        weights.sort(key=lambda w: -w["bytes"])
        res["asset_count"] = len(weights)
        res["asset_total_bytes"] = sum(w["bytes"] for w in weights)
        res["asset_by_type"] = dict(sorted(by_type.items(), key=lambda kv: -kv[1]))
        res["asset_by_origin"] = dict(sorted(by_origin.items(), key=lambda kv: -kv[1]))
        res["heaviest_assets"] = weights[:20]

    if args.out:
        json.dump(res, open(args.out, "w"), indent=1)

    # --- report ---
    print(f"\n=== TECHNICAL AUDIT: {url} ===")
    print(f"HTML: {res['html_bytes']:,} bytes raw")
    for g in res["generators"]:
        print(f"  generator: {g[:110]}")
    if res["builder_hit_counts"]:
        print("  builders:", ", ".join(f"{k} ({v} hits)" for k, v in
                                       sorted(res["builder_hit_counts"].items(), key=lambda kv: -kv[1])))
    if res["plugins"]:
        print("  plugins/platforms:", ", ".join(res["plugins"]))
    if res.get("best_run"):
        b = res["best_run"]
        print(f"  best run: TTFB {b['ttfb']:.3f}s, total {b['total']:.3f}s, "
              f"{b['bytes']:,} bytes compressed, HTTP {b['status']}")
    h = res["headers"]
    print(f"  encoding: {h.get('content-encoding','none')} | cache: {h.get('cache-control','-')[:50]}")
    print(f"  origins referenced: {len(res['origins'])} -> "
          f"{', '.join(list(res['origins'])[:6])}")
    if res["staging_leakage"]:
        print(f"  !! STAGING/DEV DOMAIN IN PRODUCTION MARKUP: {', '.join(res['staging_leakage'])}")
    if res["duplicate_scripts"]:
        print(f"  !! DUPLICATE SCRIPTS ({len(res['duplicate_scripts'])}):")
        for b, v in list(res["duplicate_scripts"].items())[:5]:
            print(f"       {b.split('/')[-1]} loaded {len(v)}x  ({', '.join(x.split('/')[-1] for x in v)})")
    print(f"  @font-face rules: {res['font_face_count']} | families: "
          f"{', '.join(f'{k}({v})' for k, v in list(res['font_families'].items())[:6])}")
    fo = res["font_origins"]
    if fo["self_hosted_refs"] and (fo["google_gstatic_refs"] or fo["google_apis_refs"]):
        print(f"  !! FONTS DUAL-ORIGIN: {fo['self_hosted_refs']} self-hosted refs AND "
              f"{fo['google_gstatic_refs'] + fo['google_apis_refs']} Google refs — likely double-loading")
    if res["preload_mismatch"]:
        print(f"  !! PRELOAD MISMATCH: responsive background(s) not preloaded: "
              f"{res['preload_mismatch']}")
        print(f"     preloaded instead: {res['preload_images']}")
        print("     On the breakpoint using the un-preloaded image this delays LCP and "
              "wastes the preloaded download.")
    print(f"  images: {res['img_total']} total, {res['img_missing_alt']} missing alt, "
          f"{res['img_missing_dims']} missing width/height")
    if args.weigh_assets and res.get("asset_total_bytes"):
        print(f"  measured assets: {res['asset_count']} files, "
              f"{res['asset_total_bytes']/1024:.0f} KiB")
        for k, v in list(res["asset_by_type"].items())[:6]:
            print(f"     .{k}: {v/1024:.0f} KiB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
