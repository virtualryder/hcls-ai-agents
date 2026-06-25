# HCLS AI Agent Suite — Go-to-Market Decks

Eleven PowerPoint decks for the **HCLS AI Agent Suite** — eight governed AI agents for
life-sciences organizations, a suite executive overview, and a board-level CIO/CISO
adoption review. The eight agent decks and the overview are generated from a single
`pptxgenjs` generator ([`build-agent-decks.js`](build-agent-decks.js)) so they share one
AWS-standard layout, palette, and fonts; only the per-agent content object changes. The
adoption review is built by [`build-cio-deck.js`](build-cio-deck.js).

Audience: **CIO / CISO (CSO) / Director of Architecture / VP Quality / Head of Regulatory.**
Board-defensible metrics, an explicit cost of doing nothing, and source-class tags on every stat.

> **Figures are cited.** Every ROI/stat traces to an entry in
> [`../gtm/HCLS-DECK-SOURCES.md`](../gtm/HCLS-DECK-SOURCES.md) and carries its source class
> on-slide: `[gov/peer-reviewed]` · `[industry-research]` · `[sector-press/estimate]` ·
> `[vendor]` · `[modeled]`. Vendor and estimate figures are flagged and never lead.
> Modeled cost-of-doing-nothing figures show their arithmetic on-slide and are substituted
> with the customer's actual volumes — never guaranteed.
>
> **Speaker notes** are on every slide: a `[MM:SS]` timing, a talk-track, how to position
> to a CIO / CISO / Director of Architecture, and — on the architecture and deploy slides —
> exactly what the customer must provide to deploy.

## Index

| Deck | Agent | Headline metric (cited) | Cost of doing nothing |
|------|-------|--------------------------|------------------------|
| `HCLS-01-Regulatory-Writing.pptx`        | 01 Regulatory Writing & Intelligence | $2.6B per approved drug (DiMasi/Tufts) | ~$60M / month of delay (McKinsey) |
| `HCLS-02-Pharmacovigilance.pptx`         | 02 Pharmacovigilance — ICSR Intake | ~28M FAERS reports; 40–70% entry cut (Schmider) | ~$2.0M / yr (modeled) |
| `HCLS-03-Clinical-Trial-Ops-TMF.pptx`    | 03 Clinical Trial Ops & TMF | ~$800K/day delay + ~$40K/day cost (Tufts) | ~$25.7M / 30-day slip (modeled) |
| `HCLS-04-Site-Patient-Matching.pptx`     | 04 Site Selection & Patient Matching | ~80% of trials miss enrollment timeline | ~$24M / launch (modeled) |
| `HCLS-05-Quality-CAPA.pptx`              | 05 Quality / CAPA & Complaints | CAPA = #1-cited FDA device 483 clause | $10M–$100M / recall |
| `HCLS-06-Protocol-Design.pptx`           | 06 Clinical Protocol Design & Feasibility | ~57% amended / ~45% avoidable (Tufts) | ~$535K / amendment (Tufts) |
| `HCLS-07-RWE-HEOR.pptx`                  | 07 Real-World Evidence / HEOR | ~45% of analyst time on data prep (Anaconda) | ~$1.3M / yr / team (modeled) |
| `HCLS-08-Medical-Affairs-MSL.pptx`       | 08 Medical Affairs / MSL Copilot | MLR weeks→months; 50–70% reducible (McKinsey) | Billions in FCA risk (DOJ) |
| `HCLS-Agentic-AI-Suite-Executive-Overview.pptx` | Suite overview (executive) | The governed platform is the product | Suite-level cost-of-inaction summary |
| `HCLS-CIO-Adoption-Review.pptx`          | CIO / CISO / Architecture board review | Verdict: governed accelerator, not turnkey | Go / no-go decision criteria |

## Per-agent deck — 6-slide executive narrative

Every agent deck follows the order **ISSUE → COST OF DOING NOTHING → HOW WE SOLVE IT →
ARCHITECTURE → PROOF**, replicating the AWS-standard reference layout:

1. **Title** *(navy)* — agent name; orange subtitle "A Governed Agentic AI Reference
   Architecture for Life Sciences"; footer "HCLS AI Agent Suite · Built on AWS · June 2026".
2. **The issue at a glance** *(navy stat/hook)* — a punchy "FROM X TO Y" hero headline, an
   italic one-line value prop, and three stat cards (big orange numbers, gray labels, source tags).
3. **The issue & the cost of doing nothing** *(light, two cards + dark callout bar)* — left card
   "THE ISSUE" (navy accent); right card "THE COST OF DOING NOTHING" (orange accent) with the
   CFO dollar figure, the modeled arithmetic in plain text, and hard-risk bullets; a dark bottom
   bar carries the agent's **bright line** (the agent drafts/recommends; a named human owns every
   consequential decision).
4. **How we solve it — a governed pipeline** *(light, numbered flow + 3 cards)* — the 5-step flow
   (retrieve approved content → analyze → draft/recommend → **HITL gate, in red** → audit), plus
   three assurance cards (every action audited · grounded & explainable · AI never decides
   *the consequential thing*).
5. **AWS architecture & traffic flow** *(light diagram)* — the most important slide. Dashed group
   containers (ORG/EXTERNAL; AWS CLOUD — PER-CUSTOMER VPC with EDGE/PUBLIC, PRIVATE/runtime,
   MODEL LAYER, DATA TIER), AWS-category-colored service boxes (compute orange, integration
   magenta, storage olive, model/db teal, networking purple), a dark SECURITY & OPS bar (21 CFR
   Part 11 audit), numbered orange traffic-flow circles (1–8) and a numbered legend. Agent-specific
   blocks are shown per agent (e.g. 02 PHI masker; 03 EventBridge continuous monitoring; 04/07
   gateway-enforced de-identification).
6. **Proof, payback & how to deploy** *(navy)* — left card "MEASURED OUTCOMES" (2×2 stats with
   tags); right card "WHAT IT TAKES TO DEPLOY" (compact 6-step path) ending in the deploy one-liner
   and a pointer to `aws-native-reference/<agent>/DEPLOY.md` and `docs/DEPLOY-QUICKSTART.md`; a dark
   bottom bar carries the takeaway: *the agent isn't the product — the governed platform that makes
   it 21 CFR Part 11 / GxP-defensible and deployable on AWS is.*

## Suite overview deck (~11 slides)

Title · the thesis ("everyone's moving, few are governed") · the **shared AWS architecture &
traffic flow** · the **8-agent portfolio grid** (two slides: land-first 01/02/03/08, then
higher-governance 04/05/06/07) · the **governance/compliance spine** (21 CFR Part 11 · GxP/ALCOA+ ·
GVP/E2B · ICH E6(R3) · HIPAA · FDA AI guidance + NIST AI RMF) · the **maturity ladder** (Documented
→ Demonstrated → Deployable → Production-ready) · the **deployment story** (one platform,
per-customer isolation, six stages) · the **land-and-expand path** · the **suite-level
cost-of-inaction summary** · the takeaway.

## CIO / CISO adoption review deck (12 slides)

A board-ready, honest-broker deck: title (verdict up front) · bottom-line-up-front · the maturity
ladder positioned honestly · why a CISO / QA / regulatory lead can say yes (six gateway controls) ·
where it falls short (open risks) · the due-diligence questions · a three-part **shared-responsibility
matrix** (platform/identity/security/data · model/validation/HITL · operations/change/training) ·
the honest backlog · the recommended phased adoption path · the go/no-go decision summary. Distinct
navy/teal/amber visual language with `react-icons`.

## Design system (AWS standard)

- **Palette:** Squid Ink navy `#232F3E` (dark slides, titles); AWS Orange `#FF9900` (accents, big
  stat numbers, the thin left-edge brand bar on every slide, step numbers); teal/green `#16A085`
  (secondary / positive flow boxes); red `#C0392B` (reserved for the HUMAN-GATE box only); light
  gray `#F2F3F4` content backgrounds; white cards. The architecture diagram uses AWS category
  colors — compute orange, integration magenta `#E7157B`, storage olive `#7AA116`, model/db teal,
  networking purple `#8C4FFF`.
- **Left-edge bar:** a thin (~0.14") AWS-orange bar runs down the far-left edge of **every** agent /
  overview slide — intentional AWS-brand styling from the reference template.
- **Fonts:** Arial bold titles; Cambria italic taglines; Calibri body. Stat numbers 26–40pt orange.

## Regenerating

```bash
# from repo root, with deps installed (npm install)
make decks            # builds all decks + deflate-recompresses (build-agent-decks.js + build-cio-deck.js)
make decks-pdf        # exports every deck to a print-ready PDF leave-behind (needs LibreOffice)

# or run the generators directly:
node decks/build-agent-decks.js     # 8 agent decks + executive overview
node decks/build-cio-deck.js        # CIO / CISO adoption review
```

`pptxgenjs` writes an uncompressed (STORED) ZIP; `make decks` follows the build with a deflate
recompress (`decks/recompress.py`). `make decks-pdf` produces `decks/HCLS-*.pdf` leave-behinds
(8 agent PDFs · 11-page overview · 12-page CIO review) for emailing without PowerPoint. The agent generator is self-contained: one `AGENTS` array of per-agent
content objects drives the eight agent decks, and `buildOverview()` drives the suite deck, all
through shared slide-builder functions so the layout stays identical across all nine.
