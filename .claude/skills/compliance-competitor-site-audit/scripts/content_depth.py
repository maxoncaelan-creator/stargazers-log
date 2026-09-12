#!/usr/bin/env python3
"""Content depth and ranking-footprint proxies.

No paid SEO API here, so this measures the things that *cause* rankings and are
visible without one: how many indexable URLs exist, how densely they link to
each other, whether structured data is present, and how recently anything was
published. Orphaned pages and absent schema are the two findings that most
often separate a site that looks busy from one that actually ranks.
"""
import argparse, json, os, re, sys
import urllib.parse as up
from collections import Counter, defaultdict

SCHEMA_VALUE = {
    "AggregateRating": "star ratings in SERPs — high CTR value, commonly absent",
    "Service": "names what is actually sold; missing on most service sites",
    "FAQPage": "SERP real estate for long-tail questions",
    "BreadcrumbList": "cleaner SERP display, helps crawl understanding",
    "LocalBusiness": "local pack relevance",
    "MedicalBusiness": "health-specific local relevance",
    "Physician": "practitioner entity",
    "Dentist": "practitioner entity",
    "MedicalClinic": "clinic entity",
    "Organization": "entity basics",
    "WebSite": "sitelinks searchbox",
    "Review": "CAUTION for regulated health services — review markup on a clinic site "
              "may republish testimonials as advertising (s.133(1)(c))",
}


def visible(html):
    h = re.sub(r"(?is)<(script|style|noscript)\b.*?</\1>", " ", html)
    h = re.sub(r"(?s)<[^>]+>", " ", h)
    return re.sub(r"\s+", " ", h)


def main():
    ap = argparse.ArgumentParser(description="Content depth + ranking footprint proxies")
    ap.add_argument("fetched_dir")
    ap.add_argument("--out")
    args = ap.parse_args()

    man = json.load(open(os.path.join(args.fetched_dir, "manifest.json")))
    pages_dir = os.path.join(args.fetched_dir, "pages")
    host = man["host"]

    all_urls = man.get("all_sitemap_urls", [])
    res = {"target": man["base"],
           "sitemaps": man.get("sitemaps", []),
           "indexable_urls": man.get("sitemap_url_total", 0) or len(all_urls),
           "pages_analysed": len(man["fetched"])}

    # URL shape — tells you what kind of content footprint exists
    seg = Counter()
    for u in all_urls:
        parts = [p for p in up.urlparse(u).path.strip("/").split("/") if p]
        seg[parts[0] if parts else "(root)"] += 1
    res["url_sections"] = dict(seg.most_common(15))

    schema_types, internal, external = Counter(), Counter(), Counter()
    headings, word_counts, titles, metas, canonicals = [], [], [], [], []
    dates = []
    thin_pages = []

    for rec in man["fetched"]:
        p = os.path.join(pages_dir, rec["file"])
        if not os.path.exists(p):
            continue
        html = open(p, encoding="utf8", errors="replace").read()

        schema_types.update(re.findall(r'"@type"\s*:\s*"([^"]+)"', html))
        t = re.search(r"<title[^>]*>([^<]*)</title>", html, re.I)
        if t:
            titles.append(t.group(1).strip())
        m = re.search(r'<meta name="description" content="([^"]*)"', html, re.I)
        metas.append(m.group(1).strip() if m else "")
        c = re.search(r'<link rel="canonical" href="([^"]*)"', html, re.I)
        if c:
            canonicals.append(c.group(1))

        hs = re.findall(r"<(h[1-6])[^>]*>", html, re.I)
        headings.append(Counter(x.lower() for x in hs))

        txt = visible(html)
        wc = len(txt.split())
        word_counts.append(wc)
        if wc < 300:
            thin_pages.append({"url": rec["url"], "words": wc})

        for href in re.findall(r'href="([^"#]+)"', html):
            absu = up.urljoin(rec["url"], href)
            netloc = up.urlparse(absu).netloc
            if not netloc:
                continue
            if netloc == host:
                internal[absu.split("?")[0]] += 1
            else:
                external[netloc] += 1

        dates += re.findall(r'(?:datePublished|article:published_time)"[^"]*"?\s*[:=]\s*"(\d{4}-\d{2})', html)

    res["schema_types"] = dict(schema_types.most_common())
    res["schema_missing_high_value"] = [
        k for k in ("AggregateRating", "Service", "FAQPage", "BreadcrumbList")
        if k not in schema_types]
    res["schema_notes"] = {k: SCHEMA_VALUE[k] for k in schema_types if k in SCHEMA_VALUE}
    res["internal_link_targets"] = len(internal)
    res["internal_links_total"] = sum(internal.values())
    res["most_linked_internal"] = internal.most_common(12)
    res["external_domains"] = external.most_common(20)
    res["avg_words_per_page"] = round(sum(word_counts) / max(1, len(word_counts)))
    res["thin_pages"] = sorted(thin_pages, key=lambda x: x["words"])[:15]
    res["publish_months"] = Counter(dates).most_common(12)
    res["missing_meta_description"] = sum(1 for m in metas if not m)
    res["duplicate_titles"] = [t for t, n in Counter(titles).items() if n > 1]

    h1s = sum(h.get("h1", 0) for h in headings)
    res["pages_without_h1"] = sum(1 for h in headings if h.get("h1", 0) == 0)
    res["pages_multiple_h1"] = sum(1 for h in headings if h.get("h1", 0) > 1)
    res["total_h1"] = h1s

    # Orphan proxy: indexable URLs that nothing we crawled links to.
    linked = set(internal)
    res["unlinked_sitemap_urls"] = len(
        [u for u in all_urls if u.split("?")[0] not in linked])
    if res["indexable_urls"]:
        res["internal_links_per_url"] = round(
            res["internal_links_total"] / res["indexable_urls"], 1)

    if args.out:
        json.dump(res, open(args.out, "w"), indent=1)

    print(f"\n=== CONTENT DEPTH: {man['base']} ===")
    print(f"  indexable URLs (sitemap): {res['indexable_urls']}")
    print(f"  pages analysed: {res['pages_analysed']}")
    print(f"  sections: {', '.join(f'{k} ({v})' for k, v in list(res['url_sections'].items())[:8])}")
    print(f"  avg words/page: {res['avg_words_per_page']}")
    print(f"  internal links: {res['internal_links_total']} total across "
          f"{res['internal_link_targets']} distinct targets"
          + (f" ({res['internal_links_per_url']}/URL)" if "internal_links_per_url" in res else ""))
    print(f"  sitemap URLs never linked from crawled pages: {res['unlinked_sitemap_urls']}"
          " (orphan proxy — undercounts if only part of the site was crawled)")
    print(f"  schema present: {', '.join(list(res['schema_types'])[:14]) or 'NONE'}")
    if res["schema_missing_high_value"]:
        print(f"  !! high-value schema MISSING: {', '.join(res['schema_missing_high_value'])}")
    if "Review" in res["schema_types"] or "AggregateRating" in res["schema_types"]:
        print("  ** Review/AggregateRating markup present — on a regulated health service "
              "site this may itself be a s.133(1)(c) testimonial issue. Check target type.")
    print(f"  H1: {res['total_h1']} total | {res['pages_without_h1']} pages with none, "
          f"{res['pages_multiple_h1']} with multiple")
    print(f"  missing meta descriptions: {res['missing_meta_description']}")
    if res["duplicate_titles"]:
        print(f"  duplicate titles: {len(res['duplicate_titles'])}")
    if res["thin_pages"]:
        print(f"  thinnest pages: " + ", ".join(
            f"{t['words']}w {t['url'].split('/')[-2] or '/'}" for t in res["thin_pages"][:5]))
    if res["publish_months"]:
        print(f"  publishing activity: {res['publish_months'][:6]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
