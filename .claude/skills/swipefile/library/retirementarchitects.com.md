# retirementarchitects.com

**Callable as: Retirement Architects** (aliases: retirementarchitects.com)

Independent retirement-planning firm, Littleton CO. Captured 2026-08-13 @ 1440x900
and 390x844, 17 pages of the design surface. Stack: **WordPress 6.9.7 + Divi
4.27.6**. Path: capture only, used as the *content* source for an Adapt that
re-skinned it onto the Systowise (agentwise) system. Not mirrored.

## Why it was captured

Redesign target, not a donor. The value here is the content extraction and the
catalogue of what a dated Divi build looks like when measured rather than
eyeballed.

## Type: four families, no division of labour

Montserrat (59 uses), Lato (10), Oswald (5), plus **ETMODULES**, Divi's icon
font (3). No role separation: headings appear in all three text families at
different points on the same page. Nearly every heading is ALL CAPS with
2-3px letter-spacing.

Body is set **18px / 36px**: a 2.0 line-height, far too loose for long prose.
Heading steps found: 70px H1, 40px/600, 30px, 27px, 26px, 21px, 18px, 16.2px.

## Colour

Navy `rgb(28,45,70)` = `#1C2D46` (structural, and the monogram colour), mid-blue
`rgb(78,143,204)` = `#4E8FCC` (the accent, used for half of all headings), pale
tint `rgb(235,242,249)` = `#EBF2F9`, body grey `#333`. White text is laid over
busy photographs in three places with failing contrast.

## Measured defects (the reason for the rebuild)

- **Hero is ~3000px tall and is one stock photo** of a curved glass office
  building, with a 70px headline in the top-left corner and nothing else.
- **Total page height 12,943px** at 1440; the rebuild lands at 6,757px carrying
  the same content.
- A **~600px empty white gap** mid-page between the testimonial slider and the
  press band.
- A stray **"3" glyph** leaking from the ETMODULES icon font into all three
  "Expand To Read More" controls, the classic Divi icon-font failure.
- Two overlapping headings in the press band ("AS FEATURED ON" over "AS SEEN IN").

## Motion

**Motion fidelity: none**

Not captured this pass, and not worth a pass: the page's only movement is Divi's
default testimonial slider and three accordion toggles. There is no signature
here to borrow. This entry is a content and anti-pattern source, not a motion
donor.

## Structural notes

Yoast sitemap overstates the site ~8x: 241 URLs total, of which **187 are blog
posts** and 24 are tags. The actual design surface is 13 pages + 4 team members +
6 "project" (radio-station logo) entries. Histogram by first path segment before
crawling: same pattern already recorded for WordPress in INDEX.md, now confirmed
on a second WP site.

Forms: Divi's own contact form posting back to WP, plus a **Wufoo iframe** on
/contact/ and a Google Maps embed. The contact form gates submission behind an
**arithmetic captcha** ("6 + 12 = "), which for a 55-75 audience is a pure
conversion tax.

Videos are Vimeo embeds (9 on /videos/).

## Compliance content: the part that must survive any redesign

Four disclosures appear site-wide and are legally required, not decoration. All
four were verified present in the raw captured source before reuse:

1. CFP Board certification-marks licence (long form).
2. "Our appearance on ABC, CBS, FOX, NBC, was a paid advertisement…"
3. "Our appearance in Kiplinger's Magazine was a paid advertisement…"
4. "Investment advisory services provided through Tucker Asset Management LLC, a
   registered investment adviser. Guarantees are subject to the financial
   strength and claims-paying ability of the issuing insurance company…"

On the live site these are set at ~8px grey. Treating them as readable text
instead is a credibility gain, not a cost.

## Gotchas

- **`/dipl-team-member/karlan-tucker/` 404s** but still returns a styled page, so
  a capture of it looks like a real (tiny) page rather than an error. Check
  `docHeight` and heading count before trusting a captured team page.
- The capture's `docHeight` (7,907) disagrees with the full-page screenshot
  height (12,943) because setting the viewport to the document height re-lays-out
  every `100vh`/`min-height` section. See the cross-site note added to INDEX.md.

## What was built from it

`E:\New Claude\Retirement Architects Site`: four pages (home, what we do, our
team, contact), Vite + Tailwind v4 + three.js, Systowise design system, Liquid
Glass functional layer, WebGL income-structure hero. Design gate: 2 of 4 pages
pass clean, 2 carry only deliberate reference-driven overrides.
