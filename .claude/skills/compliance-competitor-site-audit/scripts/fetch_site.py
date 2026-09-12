#!/usr/bin/env python3
"""Fetch a site's pages for offline auditing.

Discovers URLs from robots.txt -> sitemap(s), falling back to homepage link
crawling. Caches raw HTML plus a manifest so the other scripts can run
repeatedly without re-hitting the target. Being polite matters here: these are
live businesses, so keep concurrency low and identify honestly.
"""
import argparse, concurrent.futures as cf, hashlib, json, os, re, subprocess, sys
import urllib.parse as up

UA = "Mozilla/5.0 (compatible; SiteAuditBot/1.0; +compliance-review)"


def curl(url, timeout=45):
    """Fetch a URL. Returns (body_text, status, headers_text)."""
    try:
        p = subprocess.run(
            ["curl", "-sSL", "--compressed", "--max-time", str(timeout),
             "-A", UA, "-w", "\n__STATUS__%{http_code}", "-D", "-", url],
            capture_output=True, timeout=timeout + 15)
        raw = p.stdout.decode("utf8", "replace")
        status = "0"
        m = re.search(r"\n__STATUS__(\d+)$", raw)
        if m:
            status = m.group(1)
            raw = raw[:m.start()]
        # Split trailing header block(s) from body
        parts = re.split(r"\r?\n\r?\n", raw, maxsplit=0)
        headers, body = "", raw
        for i, part in enumerate(parts):
            if part.lower().startswith("http/"):
                headers = part
                body = "\n\n".join(parts[i + 1:])
        return body, status, headers
    except Exception as e:
        sys.stderr.write(f"  ! fetch failed {url}: {e}\n")
        return "", "0", ""


def discover_sitemaps(base):
    """Find sitemap URLs via robots.txt, then common conventional paths."""
    found = []
    robots, _, _ = curl(up.urljoin(base, "/robots.txt"))
    found += re.findall(r"(?im)^\s*sitemap:\s*(\S+)", robots)
    for path in ("/sitemap_index.xml", "/sitemap.xml", "/wp-sitemap.xml",
                 "/sitemap-index.xml", "/page-sitemap.xml"):
        u = up.urljoin(base, path)
        if u not in found:
            body, status, _ = curl(u)
            if status == "200" and "<" in body and ("urlset" in body or "sitemapindex" in body):
                found.append(u)
    return list(dict.fromkeys(found))


def expand_sitemaps(sitemap_urls, host, depth=0):
    """Recursively resolve sitemap indexes into page URLs."""
    urls = []
    for sm in sitemap_urls:
        body, _, _ = curl(sm)
        locs = re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", body)
        if "<sitemapindex" in body and depth < 2:
            nested = [l for l in locs if l.endswith(".xml")]
            urls += expand_sitemaps(nested, host, depth + 1)
            locs = [l for l in locs if not l.endswith(".xml")]
        urls += [l for l in locs if up.urlparse(l).netloc == host]
    return list(dict.fromkeys(urls))


def crawl_links(home_html, base, host, limit):
    """Fallback discovery: same-host links off the homepage."""
    out = []
    for m in re.finditer(r'href="([^"#?]+)"', home_html):
        u = up.urljoin(base, m.group(1))
        p = up.urlparse(u)
        if p.netloc == host and p.scheme in ("http", "https"):
            if not re.search(r"\.(jpg|jpeg|png|gif|svg|webp|pdf|zip|css|js|ico|mp4)$", p.path, re.I):
                out.append(u.split("#")[0])
    return list(dict.fromkeys(out))[:limit]


def main():
    ap = argparse.ArgumentParser(description="Fetch a site for offline auditing")
    ap.add_argument("url")
    ap.add_argument("--out", required=True, help="output directory")
    ap.add_argument("--max-pages", type=int, default=40)
    ap.add_argument("--workers", type=int, default=4,
                    help="keep low; these are live business sites")
    args = ap.parse_args()

    base = args.url if args.url.startswith("http") else "https://" + args.url
    host = up.urlparse(base).netloc
    os.makedirs(args.out, exist_ok=True)
    pages_dir = os.path.join(args.out, "pages")
    os.makedirs(pages_dir, exist_ok=True)

    print(f"[fetch] {base}")
    home, status, headers = curl(base)
    if not home:
        print("  ! homepage unreachable — aborting", file=sys.stderr)
        return 1
    print(f"  homepage {status}, {len(home)} bytes")

    sitemaps = discover_sitemaps(base)
    print(f"  sitemaps found: {len(sitemaps)}")
    urls = expand_sitemaps(sitemaps, host) if sitemaps else []
    sitemap_total = len(urls)
    print(f"  sitemap URLs: {sitemap_total}")
    if not urls:
        urls = crawl_links(home, base, host, args.max_pages)
        print(f"  fell back to link crawl: {len(urls)} URLs")

    # Always include the homepage; prioritise it.
    urls = [base] + [u for u in urls if u.rstrip("/") != base.rstrip("/")]
    targets = urls[:args.max_pages]

    manifest = {"base": base, "host": host, "homepage_status": status,
                "homepage_headers": headers, "sitemaps": sitemaps,
                "sitemap_url_total": sitemap_total, "all_sitemap_urls": urls,
                "fetched": []}

    def grab(u):
        body, st, _ = curl(u)
        if not body:
            return None
        name = hashlib.md5(u.encode()).hexdigest()[:12] + ".html"
        with open(os.path.join(pages_dir, name), "w", encoding="utf8") as f:
            f.write(body)
        return {"url": u, "status": st, "file": name, "bytes": len(body)}

    with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
        for rec in ex.map(grab, targets):
            if rec:
                manifest["fetched"].append(rec)

    with open(os.path.join(args.out, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    print(f"  fetched {len(manifest['fetched'])} pages -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
