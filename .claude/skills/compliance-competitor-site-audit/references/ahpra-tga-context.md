# AHPRA / TGA advertising context

Background for writing up compliance findings so the report explains *why* something is a
problem rather than just reporting that a word appeared. Reviewed September 2026 — verify
current status before relying on it, as this area moves.

**None of this is legal advice.** It is orientation for producing an accurate report.

## Contents
- [The two regimes](#the-two-regimes)
- [AHPRA — National Law s.133](#ahpra--national-law-s133)
- [TGA — prescription-only medicines](#tga--prescription-only-medicines)
- [Why generalist agencies fail here](#why-generalist-agencies-fail-here)
- [Sources](#sources)

## The two regimes

Two separate bodies of law apply to an Australian health clinic's advertising, and they
catch different things. A site can be clean under one and badly exposed under the other.

| | AHPRA | TGA |
|---|---|---|
| Instrument | Health Practitioner Regulation National Law, s.133 | Therapeutic Goods Advertising Code |
| Binds | Registered health practitioners and anyone advertising a regulated health service | Anyone advertising therapeutic goods to the public |
| Catches | Testimonials, misleading claims, unreasonable expectations, inducements without terms | Naming or alluding to prescription-only (Schedule 4) substances |
| Who carries the risk | The practitioner — their registration | The advertiser, including the clinic |

That last row is the commercially important one. When a marketing agency causes a breach,
it is the practitioner's registration at risk, not the agency's. That asymmetry is the
most underused argument in this market.

## AHPRA — National Law s.133

Section 133 prohibits advertising a regulated health service in a way that:

- **(a)** is false, misleading or deceptive, or likely to be
- **(b)** offers a gift, discount or other inducement **without also stating the terms and
  conditions** of that offer
- **(c)** uses **testimonials or purported testimonials** about the service or business
- **(d)** creates an **unreasonable expectation of beneficial treatment**
- **(e)** directly or indirectly encourages **indiscriminate or unnecessary use** of
  regulated health services

Maximum penalty since the 2022 amendments: **$60,000 per offence for an individual,
$120,000 for a body corporate.**

### The testimonial prohibition (the one that matters most)

s.133(1)(c) is where generalist marketers walk clients into trouble, because collecting
and displaying reviews is the default local-SEO playbook and it is largely unavailable
here.

A testimonial is a statement, review or feedback involving recommendations or positive
statements **about the clinical aspects** of a regulated health service. The prohibition
applies in print, on websites, on social media, and on material displayed inside the
practice.

Two distinctions decide most real cases:

1. **Clinical vs non-clinical.** Comments about parking, wait times or reception staff are
   not clinical. Comments about treatment or outcome are.
2. **Controlled vs uncontrolled.** Practitioners are not responsible for unsolicited
   reviews on third-party platforms they do not control. The breach is *using* reviews in
   their own advertising — embedding a widget, quoting reviews on a landing page,
   republishing them as social proof.

This is why an embedded review widget on a clinic site is a high-severity indicator while
the existence of Google reviews about that clinic is not a finding at all.

**Status note:** reform to lift the testimonial ban has been discussed since 2022 and was
*not* included in the National Law amendments that took effect through 2025–26. As of
this review the prohibition stands. Confirm before writing it into client-facing material.

### Before/after imagery

Permitted but tightly conditioned: images must be genuine, comparable (same lighting,
angle, preparation), carry appropriate qualifying information, and not create an
unreasonable expectation. Cosmetic procedures carry additional requirements following the
2023 cosmetic surgery reforms.

### Protected titles

The 2023 reforms tightened specialist title use — "cosmetic surgeon" in particular is now
restricted. US-style credential language such as "board certified" misleads Australian
consumers because the accreditation structure differs.

## TGA — prescription-only medicines

Schedule 4 (prescription-only) medicines **cannot be advertised to the public in
Australia at all**. For clinics this is mostly about cosmetic injectables and, currently,
weight-loss drugs.

Prohibited references include:

- **Brand names** — Botox, Dysport, Juvederm, Ozempic, Wegovy, Mounjaro, and so on
- **Active ingredients** — botulinum toxin, semaglutide, tirzepatide
- **Acronyms, nicknames, abbreviations and hashtags** a consumer would read as referring
  to the substance — including slang such as "brotox" or "traptox"
- **Business names** that themselves reference a prescription-only substance

### The tightening that catches experienced marketers

The TGA historically permitted *indirect* references when promoting a service — generic
non-product phrasing like "wrinkle reducing injections" was acceptable while "Botox" was
not. **That position has changed.** Descriptors like "dermal filler", "cosmetic
injectable" and "anti-wrinkle injection" now sit in contested territory, which is why the
scanner rates them `medium` rather than `high`: they are very likely a problem, but the
snippet needs reading.

### How widespread the problem is

The TGA's Operation Redress audited 100 cosmetic business websites across every state and
territory in March–April 2025:

- **98 of 100** were advertising prescription-only medicine using prohibited terms
- **Over 6,000 pages** across those 98 sites potentially in breach, covering **530 clinics**
- "Dermal filler" appeared **31,874** times, "cosmetic inject\*" **16,671**, "Botox"
  **2,983**, and Botox slang variants **435**
- 40 further advertising channels were identified, including bus advertising and social media

Cite this when a clinic assumes its existing agency has it handled. A 98% failure rate
across a professionally-marketed category means the assumption is usually wrong.

## Why generalist agencies fail here

The standard local-service playbook is almost perfectly wrong for regulated health:

| Standard playbook | Status for a regulated health service |
|---|---|
| Review widgets and star ratings on site | Likely s.133(1)(c) breach |
| Testimonial carousels | Likely s.133(1)(c) breach |
| Before/after ad creative | Permitted only under tight conditions |
| "Best / safest / painless / guaranteed" copy | Likely s.133(1)(d) |
| "Free consultation!" with no terms shown | Likely s.133(1)(b) |
| Naming the treatment drug in ads and on landing pages | TGA breach if Schedule 4 |
| `AggregateRating` schema for rich snippets | May republish testimonials as advertising |

That last row is worth dwelling on, because it is invisible in the rendered page and shows
up only in structured data — a common finding on clinic sites built by generalists chasing
star ratings in search results.

## Sources

- [AHPRA — Guidelines for advertising a regulated health service](https://www.ahpra.gov.au/Resources/Advertising-hub/Advertising-guidelines-and-other-guidance/Advertising-guidelines.aspx)
- [AHPRA — Testimonials in health advertising](https://www.ahpra.gov.au/documents/default.aspx?record=WD18/25238&dbid=AP&chksum=HkXoeYd5QfC7AnDovNpPfg%3D%3D)
- [AHPRA — Advertising compliance and enforcement strategy](https://www.ahpra.gov.au/Resources/Advertising-hub/Advertising-complaints/Advertising-compliance-and-enforcement-strategy.aspx)
- [TGA — Referring to cosmetic injectables in advertising](https://www.tga.gov.au/news/media-releases/referring-cosmetic-injectables-advertising)
- [TGA — Advertising health services and cosmetic injections FAQ](https://www.tga.gov.au/products/regulations-all-products/advertising/specialised-advertising-issues-and-topics/advertising-health-services-and-cosmetic-injections-frequently-asked-questions-and-answers)
- [Operation Redress — Mass breaches of TGA advertising rules by cosmetic injectors](https://www.opred.com.au/10/06/2025/mass-breaches-report)
- [B&T — Audit finds 98% of cosmetics websites breach ad rules](https://www.bandt.com.au/audit-finds-98-of-cosmetics-websites-breach-ad-rules/)
- [Kennedys — From reform to reality: National Law changes now in force (2026)](https://www.kennedyslaw.com/en/thought-leadership/article/2026/from-reform-to-reality-national-law-changes-now-in-force/)
