# Competitive Analysis: Would Out-Building Indi Creative's Website Win You Business?

**Subject:** indicreativeagency.com.au
**Prepared for:** A prospective competing digital marketing agency (Bricks Builder stack)
**Date:** 12 September 2026
**Question:** *If I build a similar site in Bricks that doesn't have the 10 identified issues, is that a competitive advantage — or does it not meaningfully matter?*

---

## Verdict

**It does not meaningfully matter.** Build the site well anyway — doing it right costs you nothing extra on a greenfield build — but do not mistake it for strategy.

Three reasons, in order of weight:

1. **Eight of the ten issues are invisible to customers and near-invisible to Google.** The site already scores 100/100 SEO and 91/100 Accessibility. You would be optimising a competitor's B+ into your A-, in a subject the buyer never grades.
2. **Every one of the ten is cheap for them to fix.** Total remediation is roughly one developer-day. An advantage your competitor can erase in an afternoon — without even changing page builders — is not a moat.
3. **Website technical quality is not the binding constraint in agency client acquisition.** It is a credibility check, not a differentiator. Nobody has ever chosen an agency because its Largest Contentful Paint was 1.3 seconds quicker.

There is a real advantage available in this market. It is just not in the ten issues. It is in items #9 and #10 — and in the content gap sitting behind them. That is covered in Part 4.

---

## Part 1: Do the Ten Issues Actually Matter?

Each issue is scored on what it moves, not on how bad it looks in an audit tool.

| # | Issue | Ranking impact | Conversion impact | Their cost to fix |
|---|---|---|---|---|
| 1 | Duplicate Trustindex loader (186 KiB) | Negligible | Low | ~10 min |
| 2 | Font stack chaos (~330 KiB, 28 `@font-face`, dual origin) | Negligible | Low | ~2 hrs |
| 3 | Mobile hero preload mismatch (wrong LCP image) | Negligible | Low–Moderate | ~15 min |
| 4 | Logos served from staging domain | Negligible | Low | ~30 min |
| 5 | 20 images missing `width`/`height` (CLS) | Negligible | Low | ~1 hr |
| 6 | jQuery + jQuery Migrate (~85 KiB) | Negligible | Negligible | ~30 min |
| 7 | **Staging site fully indexable** | **Moderate** | None | ~15 min |
| 8 | `og:locale` set to `en_US` | Negligible | Negligible | ~2 min |
| 9 | **No `AggregateRating` / `Service` / `FAQPage` schema** | **Moderate** | Moderate (CTR) | ~4 hrs |
| 10 | **Thin internal linking (19 links vs 52 pages)** | **Moderate–High** | Low | Ongoing |

### The pattern that matters

Read the table column-wise rather than row-wise and the strategic picture inverts:

> **The issues that are easiest to fix are the ones that matter least. The issues that matter most (#9, #10) are the ones requiring sustained editorial effort — which is precisely why they are the only ones capable of producing a durable advantage.**

Issues #1–#6 and #8 are *hygiene*. They are worth zero as strategy and are table stakes on any competent new build.

### On performance specifically

Core Web Vitals is a confirmed Google ranking signal, but a deliberately weak one — Google has consistently described page experience as a tiebreaker between results of comparable relevance, not a lever that promotes weaker content over stronger. Two agency sites competing for *"digital marketing agency melbourne"* will be separated by content depth, topical authority, backlinks and Google Business Profile signals long before either one's LCP is consulted.

The conversion argument is more honest but still small. Moving mobile LCP from ~3.3 s to ~2.0 s plausibly yields a **single-digit relative improvement in conversion rate**. Note that the widely cited speed-conversion elasticities come from retail and travel, where purchase intent is fragile. A business owner who has actively searched for a marketing agency, clicked through, and is evaluating a shortlist is a far more patient visitor. Expect the low end of the range, if any.

On a site of this footprint — 52 pages, 8 blog posts — a few percent on conversion is a rounding error against the traffic you are not yet getting.

**Calibration note:** the 91 Performance score in the source audit was measured against a local mirror with no real network latency and third-party scripts largely inert. Their true field performance is probably worse than 91, given 2.4 MB across four origins. So there is more headroom here than the lab number implies — it is just headroom in the wrong metric.

---

## Part 2: The Moat Problem

This is the decisive argument, and it is worth stating plainly.

Total engineering time for Indi Creative to close all ten issues: **roughly one developer-day.** Six of them are under an hour each. The duplicate Trustindex loader is a ten-minute fix by someone who notices it.

So the strategy *"I will win by not having their bugs"* has a structural flaw:

- If they never notice, you hold an advantage the market cannot perceive.
- If they do notice — or a prospect mentions it, or they run their own PageSpeed check — the advantage evaporates in a day.

**An advantage that a competitor can neutralise faster than you can build it is not an advantage.** It is a maintenance standard.

Compare with the two genuinely defensible items:

- **#10 (internal linking / site architecture)** cannot be fixed in a day because the underlying problem is that there are only 60 URLs to link between. Fixing it properly means *producing more of substance*, which takes months.
- **#9 (schema, and the review/service infrastructure behind it)** is partially cheap — but the `AggregateRating` markup is only as good as the review volume backing it. That is accumulated, not configured.

Durable advantage lives in the things that take time. That is the entire principle.

---

## Part 3: Does Choosing Bricks Change the Answer?

**Partially, and less than you would hope.**

### What Bricks genuinely gives you

- **Materially cleaner markup.** Bricks emits far less wrapper-div nesting than Elementor. Real, and it compounds across a large site.
- **No jQuery dependency.** This directly eliminates issue #6 by default rather than by remediation.
- **Lighter core payload** and a faster editor, with better semantic-element control (you choose the actual tag).
- **One-time licence pricing** rather than Elementor Pro's annual renewal — a margin consideration if you are deploying this stack across client sites.

### The critical caveat

**Elementor did not cause eight of the ten issues.** Look at the origins:

| Issue | Actual cause |
|---|---|
| 1 — Duplicate Trustindex loader | Plugin double-embed (shortcode *and* auto-inject) |
| 2 — Font chaos | WP Rocket "host fonts locally" left the original Google `@font-face` rules in place |
| 3 — Hero preload mismatch | Hand-written custom CSS overriding a hand-written preload |
| 4 — Staging-domain logos | Human error during launch — content never re-pointed |
| 5 — Missing `width`/`height` | Hand-written custom HTML blocks |
| 7 — Staging indexable | DevOps oversight |
| 8 — `og:locale` | Rank Math setting left at default |
| 9, 10 — Schema, internal linking | Content and SEO strategy |
| **6 — jQuery** | **Genuinely Elementor** |

Note the recurring phrase: *hand-written*. The header, hero and mobile drawer on this site are bespoke HTML/CSS dropped into custom-code blocks, not builder widgets. **Most of the defects live in the custom code, not in Elementor's output.**

The honest conclusion: **Bricks gives you a better starting floor, not immunity.** A carelessly built Bricks site — wrong preload, duplicated third-party embeds, an indexable staging environment — reproduces nine of these ten issues exactly. The page builder is not the variable that determines the outcome. Implementation discipline is.

Choose Bricks because it is a better tool for you to work in. Do not choose it expecting the market to notice.

---

## Part 4: Where the Advantage Actually Is

The audit surfaced one genuinely exploitable weakness, and it is not a performance issue.

### Their content footprint is thin

- **52 pages, 8 blog posts** total
- **19 unique internal links** on the homepage — meaning most of those 52 pages are orphaned or near-orphaned
- **No `Service` schema** on a site selling four distinct services
- **No `FAQPage` schema** anywhere
- **No `AggregateRating`** — despite their own meta description advertising *"Rated 4.9 on Google"* and a Trustindex widget full of unmarked-up review data

That last one is the tell. They are running review-collection infrastructure and failing to convert it into rich results. It is free SERP real estate — star ratings in search listings measurably lift click-through — and they are leaving it on the floor.

### What would actually take share

Ranked by expected return:

1. **Out-publish them on service × location.** A structured set of 150–250 genuinely useful service/location pages with correct `Service` schema and disciplined internal linking will outrank a 60-URL site regardless of which builder either of you used, and regardless of whose LCP is faster. This is the single highest-leverage move available.
2. **Ship the schema they are missing** from day one — `AggregateRating`, `Service`, `FAQPage`, `BreadcrumbList`. Cheap, immediate, and it compounds with #1.
3. **Build review velocity deliberately.** Their 4.9 rating is a real asset. Match it, mark it up, and you have neutralised their strongest visible proof point.
4. **Niche down.** *"Digital marketing for Australian service businesses"* is a broad claim competing against every agency in the country. *"Google Ads for trades businesses doing $2M–$10M"* is a narrower claim you can genuinely own, rank for, and charge more for.
5. **Publish proof with numbers.** Their case studies are their best content (*"$10k in Meta ads, $350k in work"*). Beat them on volume and specificity of proof, not on milliseconds.

### Three things you should verify before committing

This analysis is technical, not commercial. The following are unknown and each could change the calculus:

- **Their traffic and keyword footprint.** Run them through Ahrefs or Semrush. If they rank for very little, the website is not what is winning them business — and out-websiting them targets a channel where no competition is occurring.
- **Their backlink profile.** If they have meaningful authority, out-publishing takes longer than it appears.
- **Where their revenue actually comes from.** Most small agencies win predominantly on referral and outbound. If that is true here, the entire website question is close to irrelevant to competing with them, and your effort belongs in sales motion rather than site build.

---

## Part 5: Recommendation

**Build the site clean — then stop thinking about it.**

Fixing the ten issues on your own build costs you approximately nothing, because on a greenfield project you are not *fixing* anything; you are simply not introducing the defects. Preload the correct hero image, load each third-party script once, subset your fonts, `noindex` your staging environment. That is an afternoon of discipline, not a project.

Then redirect the energy you were going to spend on a performance arms race into content depth, schema, reviews and positioning — the things that cannot be neutralised in a day.

### One strategic caution

The framing of the original question contains the real risk: *"creating a similar website that does not have the stated issues."*

**A similar website that is 20% faster is not a competitive position.** It is imitation with a rounding error attached, and no prospective client will ever perceive it. The agencies that take share do so by being *visibly different* — sharper niche, better proof, clearer offer — not by being marginally better at the same thing.

Use Bricks. Build it properly. Compete on something the buyer can actually see.

### Where a fast site genuinely does pay off

One legitimate exception, and it is a sales asset rather than a traffic asset: **you are a marketing agency, so your own site is a work sample.** A prospect who checks — or a competitor you are pitching against — can run PageSpeed Insights in ten seconds. Being demonstrably fast is worth something in the room, and being demonstrably slow is a credibility problem for anyone selling digital performance.

That is a reason to build it well. It is not a reason to believe it will win you the market.

---

## Appendix: Measured Data

All figures independently measured against the live site on 12 September 2026.

### Their stack

| Layer | Technology |
|---|---|
| CMS | WordPress 7.1 |
| Page builder | **Elementor Pro 4.2.3** (confirmed via generator meta; 1,175 `elementor-*` class occurrences) |
| Theme | Hello Elementor |
| SEO | Rank Math |
| Performance | WP Rocket 3.23.3.3 (delay-JS, unused-CSS removal, local font hosting) |
| Analytics | Google Site Kit + GTM |
| Reviews | Trustindex |
| Hosting | Kinsta, behind Cloudflare |

No trace of Bricks, Divi, WPBakery, Oxygen, Breakdance, Beaver Builder or SiteOrigin.

### Lighthouse 13.4.1 (mobile)

| Category | Score |
|---|---|
| Performance | 91 ⚠️ |
| Accessibility | 91 |
| Best Practices | 96 |
| SEO | 100 |

⚠️ *Measured against a local mirror of all 63 assets. Headless Chrome could not complete TLS 1.3 handshakes through the audit environment's egress proxy, and the PageSpeed Insights API was rate-limited. The mirror removes real network latency and collapses four origins into one, so **the Performance figure is an optimistic ceiling, not a field reading**. The DOM-based SEO and Accessibility scores are accurate. For authoritative field data, run PageSpeed Insights directly to obtain CrUX real-user metrics.*

Lab metrics: FCP 1.8 s · LCP 3.3 s · Speed Index 3.0 s · CLS 0

### Production measurements (real network)

| Metric | Value |
|---|---|
| HTML size | 209 KB raw → **42 KB brotli** |
| TTFB (cache HIT) | **~60 ms** |
| Total page weight | **~2.4 MB** across 63 assets |
| Origins | 4 (main, staging, cdn.trustindex.io, fonts.gstatic.com) |

Asset breakdown:

| Type | Files | Size |
|---|---|---|
| WebP images | 33 | 1,644.7 KiB |
| JavaScript | 18 | 492.2 KiB |
| Fonts (woff2) | 6 | 211.0 KiB |
| PNG | 6 | 111.6 KiB |

Their caching and hosting layer is genuinely well configured. The weight problem is entirely in assets.

### Accessibility failures (4)

- `aria-label` on a plain `<label>` element (prohibited ARIA usage) — mobile menu toggle
- Both skip links unfocusable (`.skip-link` and `.skip`) — keyboard users cannot bypass the mega-menu
- Contrast failures on `.kick` elements (3 instances)
- 6 "Read more" links whose `aria-label` does not contain their visible text (breaks voice control)

---

*Technical findings measured directly. Strategic assessment is judgement, and depends on commercial variables — their traffic, backlink profile and actual lead sources — that were outside the scope of this analysis and are flagged in Part 4.*
