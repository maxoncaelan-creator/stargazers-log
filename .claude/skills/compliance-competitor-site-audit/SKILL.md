---
name: compliance-competitor-site-audit
description: >-
  Audit Australian health-sector marketing agencies and clinic prospects across four
  dimensions — technical build quality, content depth, ranking footprint, and AHPRA/TGA
  advertising compliance indicators. Use this whenever the user wants to size up a
  competitor agency, evaluate a health/medical/dental/allied-health/cosmetic clinic
  website, test whether an agency's "AHPRA compliant" claim holds up against its real
  client work, or generate a breach-indicator report to use as sales outreach. Trigger it
  for any request mentioning competitor analysis, site audit, AHPRA, TGA, Section 133,
  testimonial rules, prescription-drug advertising, health marketing compliance, clinic
  website review, or "what is this site built with" — even when the user does not name
  this skill, and even when they only ask for one of the four dimensions.
---

# Compliance & Competitor Site Audit

This skill audits a website four ways and produces a report a person can act on:

1. **Technical** — what it is built with, how it is delivered, what is specifically broken
2. **Content depth** — how much indexable substance exists and how well it interlinks
3. **Ranking footprint** — the structural causes of ranking, measured without a paid SEO API
4. **Compliance** — AHPRA / TGA advertising breach *indicators* for Australian health services

It exists because in this market the compliance dimension is the one that actually
separates operators, and nobody can see it from the outside without looking properly.

## The two modes, and why they differ

Everything hinges on what the target is.

**Clinic mode** (`--target-type clinic`) — the target is a regulated health service:
a dental practice, medical or cosmetic clinic, allied health group. The National Law
binds this site directly, so indicators found here are real exposure. Penalties run to
$60,000 per offence for an individual and $120,000 for a body corporate.

**Agency mode** (`--target-type agency`) — the target is a marketing firm. AHPRA and the
TGA do **not** bind a marketing agency's own website. Testimonials, before/after language
and inducements on an agency's site are not breaches, and reporting them as such destroys
your credibility. What matters in agency mode is different:

> An agency's compliance claim is only testable against the client sites it points to.
> Every specialist in this market advertises "AHPRA compliant" — it is table stakes, not
> a differentiator. Meanwhile the TGA's Operation Redress audit found 98 of 100 cosmetic
> clinic websites breaching. Those two facts cannot both be comfortable. Finding the gap
> between an agency's claim and its clients' live pages is the entire point of this skill.

So in agency mode the sequence is: audit the agency, extract its client roster, then
audit those clients in clinic mode. The finding worth having is on the client sites.

## Workflow

Run `fetch_site.py` first — everything else reads its cache, so you can iterate on
analysis without re-hitting a live business. Keep `--workers` low and don't re-fetch
needlessly; these are real businesses, not test fixtures.

```bash
S=.claude/skills/compliance-competitor-site-audit/scripts

# 1. Fetch (discovers sitemaps, falls back to link crawl)
python3 $S/fetch_site.py https://target.com.au/ --out audit_target --max-pages 40

# 2. Technical build + delivery
python3 $S/tech_audit.py https://target.com.au/ --out audit_target/tech.json
#    add --weigh-assets to download every asset and measure real page weight (slower)

# 3. Content depth + ranking-footprint proxies
python3 $S/content_depth.py audit_target --out audit_target/content.json

# 4. Compliance indicators
python3 $S/compliance_scan.py audit_target --target-type clinic --out audit_target/compliance.json

# 5. AGENCY TARGETS ONLY — extract the client roster, then audit those clients
python3 $S/find_client_sites.py audit_target --health-only --out audit_target/clients.json
```

Client discovery returns two things: outbound links, and brand names recovered from logo
imagery. The second matters more than it sounds — most agencies display client logos as
unlinked images, so alt text and filenames are the only trace. Expect to resolve those
names to live domains yourself (a quick search each), then run steps 1–4 on the ones that
are regulated health services.

## Reading the compliance output

Severity reflects how confidently a machine can judge the match, not how bad it is:

| Severity | Meaning | What to do |
|---|---|---|
| `high` | Named S4 medicines, or testimonial/review widgets on a clinic site | Quote it; this is as close to unambiguous as automated detection gets |
| `medium` | Service descriptors, before/after, superlatives, title claims | Read the snippet before asserting anything |
| `review` | Inducements | The offer is legal *with* terms — check whether terms are present before saying a word |
| `info` | The agency's own compliance claims | Positioning intel, not a finding |

**Every match is an indicator requiring human review, never a determination of breach.**
This matters commercially as well as ethically: AHPRA enforcement is risk-based and
context decides. "Best" inside "best practice" is fine. An unsolicited review on a
third-party site the practitioner does not control is treated differently from one
republished as advertising. If you send a clinic a report asserting breaches they do not
have, you have handed them a reason to distrust everything else in it — and exposed
yourself. Report what you found, where, and why it is worth their lawyer's attention.

Read `references/ahpra-tga-context.md` before writing up compliance findings — it explains
what each category actually prohibits, so the report says something more useful than
"your site contains the word Botox".

## Interpreting the technical output

The script flags specific defects rather than scoring the site, because a named broken
thing is persuasive and a score is not. The checks that reliably find real problems:

- **Staging/dev domain in production markup** — assets served from a staging host. Usually
  means the staging site is also live and indexable, which is a duplicate-content problem
  as well as a performance one.
- **Duplicate scripts** — the same JS loaded twice under different query strings. Widget
  embeds cause this constantly because the loader attaches to a `<div data-src>` rather
  than a `<script>`, so it survives normal review.
- **Dual-origin fonts** — self-hosted *and* Google-hosted copies of the same families,
  usually from a caching plugin that localised fonts without removing the originals.
- **Preload mismatch** — a high-priority preloaded image that a media query then overrides,
  so one breakpoint downloads a wasted image and gets its LCP image late.

## Report structure

Use this shape. Lead with the finding that changes what the reader does.

```markdown
# Audit: [target] — [date]
## Verdict
[2-4 sentences. What this target is, and the single most important thing found.]
## Stack
[builder, CMS, plugins, hosting/CDN — with the evidence that identified each]
## Compliance indicators
[table by severity; quote snippets; state the review caveat once, plainly]
## Content depth & ranking footprint
[indexable URLs, sections, internal links per URL, schema present/missing, publishing cadence]
## Technical findings
[named defects, each with the measurement that proves it]
## What this means competitively
[where the target is strong, where it is exposed, what it implies for the reader]
```

Where a number came from a measurement, say so. Where it is an estimate or a proxy, say
that too — `content_depth.py`'s orphan count undercounts when only part of a site was
crawled, and saying so costs nothing while overstating it costs the whole report.

## Limits worth stating in the output

- Lighthouse is not run here. Chrome cannot always reach external sites from sandboxed
  environments, and PageSpeed Insights is rate-limited without an API key. If real Core
  Web Vitals matter, tell the user to run PageSpeed Insights themselves for CrUX field
  data, and use `tech_audit.py --weigh-assets` for byte-level evidence in the meantime.
- Ranking footprint here is structural (URLs, interlinking, schema), not keyword-level.
  Actual ranking and backlink data needs Ahrefs or Semrush — recommend it rather than
  implying this substitutes for it.
- Term lists need maintenance. Australian advertising rules move; `references/regulated_terms.json`
  carries a `last_reviewed` date, and the categories explain their own reasoning so terms
  can be added without guessing at intent.

## Ethical guardrails

Auditing public websites is legitimate competitive and sales research. Two lines keep it
that way: **report only what you actually measured**, and **never assert a legal
conclusion you are not qualified to make**. Findings are indicators; a lawyer or the
practitioner's indemnity insurer determines breach. Do not fabricate counts, do not
inflate severity to make outreach land harder, and do not target individual practitioners
personally rather than the business's published advertising.
