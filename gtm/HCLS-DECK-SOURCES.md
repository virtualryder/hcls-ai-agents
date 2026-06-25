# HCLS AI Agent Suite — Deck Sources

> **Verified June 2026.** Every figure on a suite sales deck must trace to an entry below. These are *documented results applied to a reference organization*, not guarantees — outcomes depend on the customer's baseline volumes, portfolio, data quality, and process design. **Vendor-reported figures are explicitly labeled `[vendor]`** and should never be the lead stat on a slide. Prefer `[gov/peer-reviewed]` and `[industry-research]` figures for headline claims. Where a figure is older than 2023 and no newer authoritative replacement exists, it is flagged `[older]`.
>
> **Source-class tags:** `[gov/peer-reviewed]` · `[industry-research]` · `[sector-press/estimate]` · `[vendor]` · `[modeled]`
>
> **Two myths we deliberately avoid** so the deck stays defensible: (1) the "$4–8M/day clinical-trial delay" figure — Tufts CSDD's 2024 study supersedes it with ~$800K/day in lost/delayed sales + phase-specific direct cost; (2) the bare "80% of analyst time on data wrangling" rule of thumb — Anaconda's measured ~45% is used instead.

---

## Suite-wide proof points

**Market / economic context**
- Generative AI could create **$60B–$110B/year in economic value** for pharma and medical-product companies. — *McKinsey, 2023* `[industry-research]` — https://www.mckinsey.com/industries/life-sciences/our-insights/generative-ai-in-the-pharmaceutical-industry-moving-from-hype-to-reality
- Adoption is early: nearly all surveyed commercial life-sciences companies have experimented with gen AI, but **only ~5%** had turned it into a competitive differentiator producing consistent financial value; more than two-thirds plan to significantly increase investment. — *McKinsey, 2024* `[industry-research]` — https://www.mckinsey.com/industries/life-sciences/our-insights/early-adoption-of-generative-ai-in-commercial-life-sciences
- *Caution:* the widely-quoted "AI-in-pharma market $1.9B (2025) → $16.5B (2034), ~27% CAGR" traces to commercial market-research vendors, not a tier-1 firm. `[sector-press/estimate — do not lead with it]`

**Regulatory backdrop (the reason governance is the product)**
- **FDA draft guidance, "Considerations for the Use of Artificial Intelligence To Support Regulatory Decision-Making for Drug and Biological Products"** — published **Jan 7, 2025** (Docket FDA-2024-D-4689). Establishes a **risk-based 7-step credibility-assessment framework** keyed to the model's context of use. — *FDA/CDER, 2025* `[gov/peer-reviewed]` — https://www.fda.gov/regulatory-information/search-fda-guidance-documents/considerations-use-artificial-intelligence-support-regulatory-decision-making-drug-and-biological (PDF: https://www.fda.gov/media/184830/download)
- **EMA "Reflection paper on the use of AI in the medicinal product lifecycle"** — **draft 19 July 2023** (EMA/CHMP/CVMP/83833/2023), **finalized Sept 2024**. Calls for a human-centric, GxP-traceable approach. Cite both dates. — *EMA, 2023/2024* `[gov/peer-reviewed]` — https://www.ema.europa.eu/en/use-artificial-intelligence-ai-medicinal-product-lifecycle-scientific-guideline
- **21 CFR Part 11** sets when FDA treats **electronic records and signatures as equivalent to paper** — requiring system validation, audit trails, access controls, and e-signature controls whenever GxP (cGMP/GLP/GCP) records are kept electronically. — *FDA / eCFR* `[gov/peer-reviewed]` — https://www.ecfr.gov/current/title-21/chapter-I/subchapter-A/part-11

**Named pharma GenAI-on-AWS deployments** `[vendor — support only, never a lead stat]`
- **AstraZeneca "Development Assistant"** — multi-agent gen AI on **Amazon Bedrock Agents** (supervisor routing to clinical / regulatory / safety subagents; RAG + text-to-SQL). Concept-to-production in **6 months**, scaled to **1,000+ users**; hours-long insight tasks now take minutes. — *AWS, 2025* `[vendor]` — https://aws.amazon.com/solutions/case-studies/astrazeneca-case-study/
- **Pfizer–AWS "PACT"** — across 14 projects, gen AI/ML reportedly **saved ~16,000 hours of scientist search time annually**; SageMaker + Bedrock. — *AWS, 2024* `[vendor]` — https://aws.amazon.com/solutions/case-studies/pfizer-PACT-case-study/
- **Bristol Myers Squibb, Sanofi, and Pfizer** are named users of **Amazon Bedrock AgentCore** (GA Oct 13, 2025; Sanofi "SWEL" platform). — *AWS Industries blog, 2025–2026* `[vendor]` — https://aws.amazon.com/blogs/industries/aws-reinvent-2025-a-transformative-moment-for-healthcare-and-life-sciences/
- **Gap:** no verified standalone gen-AI-on-AWS case study found for Gilead or Moderna — do not assert one. Anchor on AstraZeneca / Pfizer / BMS / Sanofi.

**Status-quo cost anchors used across multiple agents**
- **One day of development delay ≈ $800,000 in lost/delayed peak sales**, plus direct trial cost per day by phase — **Phase III $55,716; Phase II $23,737; Phase I $7,829; Phase IV $14,091**. — *Tufts CSDD, 2024 (645 drugs; peer-reviewed companion)* `[industry-research / gov/peer-reviewed]` — https://csdd.tufts.edu/sites/default/files/2025-02/Aug2024%20Day%20of%20Delay%20White%20Paper%20Final.pdf · journal: https://pubmed.ncbi.nlm.nih.gov/38773058/
- **$2.6B** average capitalized cost to develop one approved drug ($2.9B incl. post-approval; 2013 $). — *DiMasi et al., Tufts CSDD, J. Health Economics, 2016* `[gov/peer-reviewed] [older — canonical board anchor]` — https://www.sciencedirect.com/science/article/abs/pii/S0167629616000291

---

## 01 — Regulatory Writing & Intelligence

- **HEADLINE:** **$2.6B** average capitalized cost per approved drug — the value at stake behind every submission document. — *DiMasi et al., Tufts CSDD, 2016* `[gov/peer-reviewed] [older]` — https://www.sciencedirect.com/science/article/abs/pii/S0167629616000291
- **COST OF DOING NOTHING:** **~$60M NPV lost per month of submission delay** for a $1B-peak-sales asset (~$180M from a ~12-week slip). — *McKinsey, Aug 2025* `[industry-research]` — https://www.mckinsey.com/industries/life-sciences/our-insights/rewiring-pharmas-regulatory-submissions-with-ai-and-zero-based-design
- **$4,682,003** FY2026 PDUFA fee for an NDA/BLA with clinical data — the hard cost just to file. — *FDA Federal Register, July 2025* `[gov/peer-reviewed]` — https://www.federalregister.gov/documents/2025/07/30/2025-14413/prescription-drug-user-fee-rates-for-fiscal-year-2026
- **PAIN:** ~80% of top pharma are modernizing RIMS, but **only ~13%** automate table/listing/figure formatting at scale — assembly is still manual. — *McKinsey, Aug 2025* `[industry-research]` — (URL above)
- **PAIN:** FDA's own gen-AI tool **"Elsa" reportedly hallucinated nonexistent studies**; the Commissioner acknowledged it "could hallucinate like any LLM" — the case-in-point for grounding + human-in-the-loop. — *2025 trade coverage* `[sector-press/estimate]` — https://www.engadget.com/ai/fda-employees-say-the-agencys-elsa-generative-ai-hallucinates-entire-studies-203547157.html
- **OUTCOME/ROI:** First-draft CSR writing cut **180 → 80 hrs (~55%)** with **50% fewer errors**. — *Merck + McKinsey, 2025* `[vendor — Merck-reported]` — https://www.merck.com/news/merck-expands-innovative-internal-generative-ai-solutions-helping-to-deliver-medicines-to-patients-faster/
- **OUTCOME/ROI:** Gen-AI medical writing reduces CSR cycle time **~40%** in early pilots. — *McKinsey, Jan 2025* `[industry-research]` — https://www.mckinsey.com/industries/life-sciences/our-insights/unlocking-peak-operational-performance-in-clinical-development-with-artificial-intelligence
- **Gap:** no primary-source "retrieval vs. reasoning" time split for medical writers — any such claim must be labeled `[modeled]`.

---

## 02 — Pharmacovigilance / ICSR Case Intake

- **HEADLINE:** FAERS surpassed **~28M cumulative reports (>20M unique) by end-2023**; quarterly extract volume has roughly tripled since 2007. — *FDA FAERS Quarterly Data Extract + FAERS Essentials (PMC), 2025* `[gov/peer-reviewed]` — https://fis.fda.gov/extensions/FPD-QDE-FAERS/FPD-QDE-FAERS.html · dashboard: https://fis.fda.gov/extensions/FPD/FPD.html
- **COST OF DOING NOTHING:** case intake/processing consumes **40–85% of PV budgets** — the single largest internal PV cost driver. — *The Pharma Letter via IntuitionLabs, 2026* `[sector-press/estimate — flag on slide]` — https://intuitionlabs.ai/articles/ai-roi-pharmacovigilance-business-case
- **COST OF DOING NOTHING (modeled):** outsourced intake ~$15–$25/case; 100,000 cases/yr × ~$20 = **~$2.0M/yr** before internal labor. `[modeled — per-case input is a practitioner estimate]`
- **PAIN:** ICSR volumes growing **~8–15%/year**. — *PMC6590385 via IntuitionLabs* `[industry-research]` — https://pmc.ncbi.nlm.nih.gov/articles/PMC6590385/
- **PAIN:** median **69 minutes** background processing per adverse-reaction report. — *Int. J. Pharmacy Practice, 2017* `[gov/peer-reviewed] [older]` — https://academic.oup.com/ijpp/article/29/5/521/6321141
- **PAIN:** case processing consumes **up to two-thirds of internal PV resources**. — *Schmider et al., Clin Pharmacol Ther, 2019* `[gov/peer-reviewed]` — https://pmc.ncbi.nlm.nih.gov/articles/PMC6590385/
- **OUTCOME/ROI:** Pfizer AI/RPA pilot — **~40–70% reduction in manual data-entry time** across ICSR fields. — *Schmider et al., 2019* `[gov/peer-reviewed] [older — cleanest peer-reviewed ROI anchor]` — https://ascpt.onlinelibrary.wiley.com/doi/full/10.1002/cpt.1255
- **OUTCOME/ROI:** PV-specific expectation of **10–30% cost savings** with GenAI/automation fully deployed. — *Indegene survey via IntuitionLabs, 2026* `[industry-research]`

---

## 03 — Clinical Trial Ops & TMF

- **HEADLINE:** **One day of trial delay ≈ $800,000 in lost/delayed sales** + **~$40,000/day in direct trial cost** — the strongest single figure in the suite. — *Tufts CSDD, 2024 (645 drugs)* `[industry-research / gov/peer-reviewed]` — https://csdd.tufts.edu/sites/default/files/2025-02/Aug2024%20Day%20of%20Delay%20White%20Paper%20Final.pdf · https://pubmed.ncbi.nlm.nih.gov/38773058/
- **COST OF DOING NOTHING (modeled):** a 30-day database-lock / TMF slip on one Phase III ≈ 30 × ($800K + $55,716) ≈ **~$25.7M**. `[modeled — Tufts day-of-delay × Phase III direct cost]`
- **PAIN:** pivotal (mostly Phase III) trial cost = **$19.0M median** (IQR $12.2M–$33.1M). — *Moore et al., JAMA Internal Medicine, 2018* `[gov/peer-reviewed]` — https://pubmed.ncbi.nlm.nih.gov/30264133/
- **PAIN:** **57% of TMF owners still rely on paper/simple e-file systems**; advanced-eTMF users report inspection readiness 56% vs. 25%. — *Veeva TMF Survey* `[vendor / industry-research]` — https://www.veeva.com/resources/largest-ever-tmf-survey-reveals-lagging-technology-adoption-and-manual-processes-significantly-impacting-clinical-trial-operations/
- **PAIN:** "failure to maintain adequate/accurate case histories" is among the **most common FDA BIMO Form 483 findings**. — *Goodwin Law on FY23 FDA BIMO data* `[industry-research]` — https://www.goodwinlaw.com/en/insights/publications/2024/07/alerts-lifesciences-common-fda-bioresearch-monitoring-violations
- **OUTCOME/ROI:** Veeva Vault TMF Bot auto-classified **1M+ documents, saving "tens of thousands of hours."** — *Veeva, 2021* `[vendor]` — https://www.veeva.com/resources/veevas-tmf-bot-automates-processes-for-faster-clinical-trials/
- **Gap:** no independently verified "% accuracy / % cycle-time" benchmark for AI TMF automation — avoid an unsourced "% faster" claim.

---

## 04 — Site Selection & Patient Matching

- **HEADLINE:** **~80% of trials miss their original enrollment timeline; ~20% of sites enroll zero patients and ~30% under-enroll.** — *CenterWatch / industry benchmark via Applied Clinical Trials* `[sector-press/estimate — present as benchmark, flag on slide]` — https://www.appliedclinicaltrialsonline.com/view/enrollment-performance-weighing-facts
- **COST OF DOING NOTHING:** **~$800,000/day in lost/delayed sales** + Phase III **$55,716/day** direct cost. — *Tufts CSDD, 2024* `[gov/peer-reviewed]` — https://doi.org/10.1007/s43441-024-00667-w
- **COST OF DOING NOTHING (modeled):** compressing enrollment by 30 days ≈ 30 × $800K = **~$24M** accelerated/recovered revenue per launch. `[modeled]`
- **PAIN:** cost per patient recruited commonly **$1,500–$10,000**; recruitment is ~20–30% of trial budget. — *industry benchmark* `[sector-press/estimate]` — https://www.withpower.com/guides/clinical-trial-cost-per-patient
- **PAIN:** average screen-failure rate **~36%** (CNS/rare disease 70–85%). — *audit via PMC* `[sector-press/estimate]` — https://pmc.ncbi.nlm.nih.gov/articles/PMC9934872/
- **COMPLIANCE DRIVER:** **FDA Diversity Action Plans** became a statutory requirement under FDORA §3602; draft guidance June 26, 2024 — **status is shifting** (revised/removed following a 2025 executive order). Present as a live-but-moving driver. — *Federal Register, 2024* `[gov/peer-reviewed]` — https://www.federalregister.gov/documents/2024/06/28/2024-14284
- **Gap:** no clean independent ROI benchmark for AI patient-matching — state "independent ROI benchmark not established"; vendor case studies are support-only.

---

## 05 — Quality / CAPA & Complaints

- **HEADLINE:** **CAPA (21 CFR 820.100) is consistently the most-cited clause in FDA device 483 inspections**; CAPA, complaint handling (820.198), and MDR are the perennial top three. Pull the exact tally from FDA's official Inspection Observations datasets. — *FDA Inspection Observations* `[gov/peer-reviewed]` — https://www.fda.gov/inspections-compliance-enforcement-and-criminal-investigations/inspection-references/inspection-observations (FY2024 file: https://www.fda.gov/media/185090/download)
- **COST OF DOING NOTHING:** average pharma recall **~$10M–$100M** depending on scope; non-routine quality events cost the device industry an estimated **$2.5B–$5B/year**. — *industry analysis (verify McKinsey primary if used as lead)* `[industry-research]` — https://www.spartasystems.com/resources/the-rising-cost-of-product-recalls-why-prevention-matters/
- **PAIN:** FY2024 drug-program **483s: 561 issued**; most-cited drug GMP observation 21 CFR 211.22(d) (~184 cites); 211.192 citations up ~171% YoY. — *trade analysis; counts verifiable in FDA Excel* `[sector-press/estimate + gov/peer-reviewed]` — https://www.pharmaceuticalonline.com/doc/trends-in-fda-fy-2024-inspection-based-warning-letters-0001
- **PAIN:** FDA issued **47 device-related warning letters in FY2024 vs. 24 in FY2023**. — *trade analysis* `[sector-press/estimate]` — https://www.meddeviceonline.com/doc/the-warning-letter-wake-up-call-in-what-fda-enforcement-is-really-telling-us-0001
- **Gap:** no independent ROI benchmark for AI CAPA/complaint automation — use a transparent `[modeled]` estimate or labeled vendor figures only.

---

## 06 — Clinical Protocol Design & Feasibility

- **HEADLINE:** **~57% of protocols incur ≥1 substantial amendment; ~45% of those are avoidable.** — *Tufts CSDD (Getz et al.), Ther Innov Regul Sci, 2016* `[industry-research / peer-reviewed] [older]` — https://link.springer.com/article/10.1177/2168479016632271
- **HEADLINE (newer):** Phase III protocols with ≥1 substantial amendment rose to **~82%** (from 66% in 2013–2015). — *benchmarking preprint, 2023* `[industry-research]` — https://www.researchsquare.com/article/rs-3168679/v1
- **COST OF DOING NOTHING:** median direct cost of a substantial amendment **$141K (Phase II), $535K (Phase III)** — matches the "~$500K" figure. — *Tufts CSDD, 2016* `[industry-research] [older; 2016 $]` — https://link.springer.com/article/10.1177/2168479016632271
- **COST OF DOING NOTHING (modeled):** preventing one avoidable Phase III amendment ≈ **$535K direct** + the ~60–80-day delay valued at ~$800K/day lost sales. `[modeled — Tufts 2016 amendment cost + Tufts 2024 delay-day]`
- **PAIN:** protocol complexity climbing — mean distinct Phase II/III procedures up **~44% since 2009**. — *Tufts CSDD, 2021* `[industry-research]` — https://www.globenewswire.com/news-release/2021/01/12/2157143/0/en/Rising-Protocol-Design-Complexity-Is-Driving-Rapid-Growth-in-Clinical-Trial-Data-Volume-According-to-Tufts-Center-for-the-Study-of-Drug-Development.html
- **Gap:** no independent AI ROI benchmark for protocol design — value framing = avoided-amendment cost + avoided delay days, both Tufts, labeled modeled.

---

## 07 — Real-World Evidence / HEOR

- **HEADLINE:** analysts spend the **largest single share of time on data prep, not analysis** — measured at **~39–45%** (more than model training, selection, and deployment combined). Lead with this, not the bare "80%" rule of thumb. — *Anaconda, 2020–2021* `[sector-press/estimate]` — https://www.bigdatawire.com/2020/07/06/data-prep-still-dominates-data-scientists-time-survey-finds/
- **COST OF DOING NOTHING:** a retrospective RWE database study can take **~6 months of manual build** before analysis begins. — *sector estimate, 2024* `[sector-press/estimate]` — https://www.quanticate.com/blog/real-world-data-analysis-in-clinical-trials
- **COST OF DOING NOTHING (modeled):** analyst ~$150K fully loaded × ~45% on wrangling = **~$67K/yr/analyst** of non-analytic labor; a 20-person RWE team ≈ **~$1.3M/yr**. `[modeled]`
- **COMPLIANCE DRIVER:** the **21st Century Cures Act (2016)** required FDA to build an RWE program; FDA delivered the **Framework for FDA's RWE Program in Dec 2018**, with follow-on RWD/RWE guidances (2023–2024). FDA evaluation hinges on data fitness-for-purpose and study-design adequacy — both demanding auditable data lineage. — *FDA, 2018–2024* `[gov/peer-reviewed]` — https://www.fda.gov/media/120060/download · https://www.fda.gov/science-research/science-and-research-special-topics/real-world-evidence
- **OUTCOME/ROI:** AstraZeneca's Bedrock assistant lets data scientists "focus on high-value analysis rather than data preparation," turning hours into minutes. — *AWS, 2025* `[vendor]` — https://aws.amazon.com/solutions/case-studies/astrazeneca-case-study/

---

## 08 — Medical Affairs / MSL Copilot

- **HEADLINE:** **MLR (medical-legal-regulatory) review is the single biggest bottleneck** to content release, with cycles routinely stretching **from weeks into months** and causing missed launch windows. — *Datapharm / Improvado, 2025–2026* `[sector-press/estimate]` — https://www.datapharm.com/resource-hub/webinar-summary-how-mlr-reviews-can-be-cut-from-weeks-to-days/
- **COST OF DOING NOTHING:** **off-label promotion is among the highest-dollar compliance risks in pharma** — record False Claims Act settlements include **GSK $3B (2012), Pfizer $2.3B (2009), J&J $2.2B, AstraZeneca $520M**. — *DOJ* `[gov/peer-reviewed + sector-press] [older]` — https://www.justice.gov/archives/opa/pr/pharmaceutical-giant-astrazeneca-pay-520-million-label-drug-marketing
- **COST OF DOING NOTHING (currency anchor):** DOJ recovered **$6.8B in total FY2025 False Claims Act recoveries** (healthcare a leading category). — *K&L Gates summarizing DOJ, 2026* `[sector-press/estimate, summarizing gov]` — https://www.klgates.com/US-Department-of-Justice-Announces-US68-Billion-in-Fiscal-Year-2025-False-Claims-Act-Recoveries-1-21-2026
- **PAIN:** Medical Information teams field **tens of thousands of HCP/consumer inquiries per year** — high-volume, response-time-sensitive. — *Anju Software, 2024* `[sector-press/estimate]` — https://www.anjusoftware.com/insights/medical-affairs/msl-pharma-information/
- **OUTCOME/ROI:** gen AI can deliver a **50–70% reduction in time-to-deliver for medical-legal reviews** and **20–30% medical-writing cost savings**, plus **~$3–5B/yr** potential Medical Affairs efficiency industry-wide. — *McKinsey, 2023–2025* `[industry-research]` — https://www.mckinsey.com/industries/life-sciences/our-insights/generative-ai-in-the-pharmaceutical-industry-moving-from-hype-to-reality

---

## 09 — Manufacturing Batch-Review  *(built agent — flagship depth)*

- **HEADLINE:** **62% of US drug shortages trace to manufacturing / product-quality problems** — the single leading root cause. — *FDA, Drug Shortages: Root Causes and Potential Solutions (2019; 2013–2017 data)* `[gov/peer-reviewed]` — https://www.fda.gov/media/159480/download · confirmed still top driver: *HHS ASPE, Analysis of Drug Shortages 2018–2023 (2025)* — https://aspe.hhs.gov/sites/default/files/documents/efa332939da2064fa2c132bb8e842bb5/Drug%20Shortages_Data%20Brief_Final_2025.01.10.pdf
- **COST OF DOING NOTHING:** routine internal quality failures ≈ **2.1% of annual sales**; remediation (investigations, CAPAs, complaints, field actions) ≈ **0.4–0.7% of annual sales**. — *McKinsey, Capturing the value of good quality (life sciences)* `[industry-research — device/LS quality-cost proxy]` — https://www.mckinsey.com/industries/life-sciences/our-insights/capturing-the-value-of-good-quality-in-medical-devices
- **COST OF DOING NOTHING (modeled):** 200 batches/yr × ~15% deviating (85% RFT) ≈ 30 investigations × ~$14K labor ≈ **~$420K/yr** — before any scrapped batch ($1–2M+ each) or delayed-release carrying cost. `[modeled — deviation-investigation cost × batch volume]`
- **PAIN:** **21 CFR 211.192** (production-record review / discrepancy investigation) was the **#2 most-cited regulation in FDA Warning Letters, 523 times across FY2017–FY2021** — the agent's exact workflow. — *The FDA Group; eCFR* `[gov/peer-reviewed]` — https://www.thefdagroup.com/blog/21-cfr-211-192 · https://www.ecfr.gov/current/title-21/chapter-I/subchapter-C/part-211/subpart-J/section-211.192
- **PAIN:** average review **~48 hrs per batch report** (up to ~500 hrs for complex paper-based). — *Réalta / BioPharm International* `[sector-press/estimate]` — https://realtatechnologies.com/batch-reports-review-by-exception-pharma/
- **PAIN:** a single biologics **batch failure = tens of millions** in losses; raw materials alone often exceed **$1–2M**. — *European Pharmaceutical Manufacturer; BioPharm International* `[sector-press/estimate]` — https://pharmaceuticalmanufacturer.media/pharmaceutical-industry-insights/pharmaceutical-manufacturing-insights/batch-failures-and-the-hidden-costs-of-contamination/
- **OUTCOME/ROI:** **review by exception cuts batch-release time ~80%** (a ~150-page record → a ~3-page exception report). — *iFactory / Tulip* `[sector-press/estimate — vendor-adjacent]` — https://tulip.co/blog/review-by-exception/
- **OUTCOME/ROI:** a benchmarked biopharma facility cut product deviations **>50%** and waste **~75%**; a generics maker raised RFT **83% → >92%**. — *McKinsey, Manufacturing quality today (2017)* `[industry-research]` — https://www.mckinsey.com/capabilities/operations/our-insights/manufacturing-quality-today-higher-quality-output-lower-cost-of-quality
- **Gap:** no gov/peer-reviewed per-batch review-cost figure exists — use the modeled estimate; the ~80% RBE figure is vendor/trade-press (illustrative, not audited).

---

## 10 — Scientific Intelligence & Target Discovery  *(roadmap / expansion agent — note: R&D / research-informatics buyer)*

- **HEADLINE:** only **~13.8% of programs entering clinical testing reach approval (~86% fail)**; lack of efficacy / wrong target leads. — *Wong, Siah & Lo, Biostatistics 20(2):273–286 (2019); 185,994 trials* `[gov/peer-reviewed]` — https://academic.oup.com/biostatistics/article/20/2/273/4817524 · https://pmc.ncbi.nlm.nih.gov/articles/PMC6409418/
- **PAIN (target validation):** ~40–50% of clinical failures attributed to lack of efficacy. — *Sun et al., Acta Pharm Sin B (2022)* `[industry-research / peer-reviewed]` — https://www.sciencedirect.com/science/article/pii/S2211383522000521
- **COST OF DOING NOTHING:** **~$2.6B capitalized cost per approved drug** (incl. failures), ~10+ years; a typical preclinical program is **~$430M out-of-pocket over 3–6 years**. — *DiMasi/Tufts CSDD (2014/2016); PhRMA/KnowledgePortalia* `[industry-research] [older]` — https://www.appliedclinicaltrialsonline.com/view/tufts-csdd-cost-develop-new-drug-26b · https://www.knowledgeportalia.org/cost-of-r-d
- **PAIN (reproducibility):** Amgen reproduced only **11% of 53 landmark preclinical cancer studies**. — *Begley & Ellis, Nature 483:531–533 (2012)* `[gov/peer-reviewed] [older — the canonical citation]` — https://www.nature.com/articles/483531a · corroborated: *eLife Reproducibility Project: Cancer Biology (2021)* — https://elifesciences.org/articles/71601
- **PAIN (overload):** PubMed holds **>35M citations and grows >1M/year (~3,000/day)** — no team can read it all. — *Jin et al., PubMed and beyond (2024); NLM* `[gov/peer-reviewed]` — https://pmc.ncbi.nlm.nih.gov/articles/PMC10850402/
- **OUTCOME/ROI:** Insilico Medicine took a **novel target → preclinical candidate in ~18 months for ~$2.6M**, and target-discovery → Phase I in **<30 months**. — *Insilico Medicine (2022, company-reported); precedent: Nature Biotech 2019 (21-day DDR1 hit)* `[vendor — company-reported]` — https://insilico.com/phase1 · https://www.nature.com/articles/s41587-019-0224-x
- **OUTCOME/ROI:** AstraZeneca cut tissue-sample analysis time **~50%** on AWS and ran **51B statistical tests in <24h** feeding 40+ discovery projects. — *AWS case study* `[vendor]` — https://aws.amazon.com/solutions/case-studies/innovators/astrazeneca/
- **Gap:** no authoritative breakout of pure target-ID-to-validation dollar cost; AI-discovery timeline claims are company-reported (label clearly), never the lead stat.

---

## Deck-author cheat sheet

**Lead-safe headline stats:** Tufts **$800K/day delay + $40K/day** (agents 03/04/06); DiMasi **$2.6B/drug** (01); FDA **CAPA-is-top-cited** + official datasets (05); Tufts **$535K Phase III amendment + 45% avoidable** (06); **FAERS volume + Schmider 40–70%** (02).

**Flag before use (sector estimates, not hard data):** "20% sites enroll zero / 30% under-enroll," "36% screen-fail," "40–85% of PV budget," and all MLR / medical-information figures.

**Confirmed gaps — do NOT fabricate:** independent AI ROI benchmarks for patient-matching (04), CAPA/complaints (05), and protocol design (06) are not established — use the labeled modeled math or labeled vendor figures only. No verified standalone Gilead/Moderna gen-AI-on-AWS case study exists; anchor on AstraZeneca / Pfizer / BMS / Sanofi.
