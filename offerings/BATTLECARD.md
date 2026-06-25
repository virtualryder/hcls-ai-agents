# HCLS AI Agent Suite — Sales Battlecard
### One-page reference for sellers, AEs, and BDMs

---

## What It Is (30-second version)

A governed, auditable AI agent accelerator for pharma, biotech, medtech, and CROs — nine agents covering the highest-value regulated workflows (PV/ICSR, regulatory writing, clinical trial ops, quality/CAPA, protocol design, RWE/HEOR, site/patient matching, medical affairs, manufacturing batch-review). Built on AWS with 21 CFR Part 11 controls and human-in-the-loop gates baked in, not bolted on. Designed for SI delivery — not a product you hand a customer unchanged.

---

## Qualifying Questions

**Ask these in the first call. A "yes" to 2+ means pursue.**

1. "Do you have a team manually processing adverse event reports or ICSR narratives today?" *(PV volume + timeline pressure = Agent 02)*
2. "Are your medical writers spending significant time retrieving evidence from Vault or internal systems before drafting?" *(Agent 01)*
3. "When was your last TMF inspection finding, and how long did it take to remediate?" *(Agent 03)*
4. "Do you have an active FDA or EU AI/ML SaMD or AIMD program, or are you being asked by Quality to govern your AI tools?" *(platform story)*
5. "Are you already on AWS or have you made a cloud commitment to AWS?" *(deal qualification)*
6. "Has Legal or your CISO flagged concerns about AI generating regulated artifacts?" *(compliance pain = platform value)*
7. "Who owns your 21 CFR Part 11 validated systems — is that an internal team or an SI?" *(identifies champion + decision authority)*

---

## Discovery Cheat Sheet

| Theme | Question | What you're listening for |
|---|---|---|
| **Volume & pain** | How many ICSRs / submissions / queries does your team process per month? | >200/month = strong ROI case |
| **Cycle time** | What's your average ICSR cycle time from report receipt to submission? | >5 days = meaningful improvement opportunity |
| **Error rate** | What percentage of your PV or submission artifacts require rework? | >15% = grounding + consistency value |
| **Compliance posture** | Have you had a 483 or Warning Letter related to documentation quality or data integrity? | Yes = elevated urgency |
| **AI readiness** | Do you have an AI governance policy today? | No = sell the platform first |
| **Budget cycle** | When is your next capital planning cycle? | Align POC close to budget approval |
| **AWS relationship** | Do you have an EDP commitment with AWS? | Yes = Marketplace private offer opportunity |

---

## Objection One-Liners

| Objection | One-liner response |
|---|---|
| *"AI will hallucinate — we can't use it for submissions."* | "The grounding layer verifies every claim against source documents before it reaches a reviewer — the same check your medical writers do manually, but deterministic and logged." |
| *"We'll build this ourselves."* | "You can. Most teams underestimate the compliance scaffolding — the audit trail, human gates, PHI masking, and prompt version control. This accelerator is that scaffolding; your team builds the workflows on top." |
| *"We already have Copilot / ChatGPT / [other tool]."* | "Those tools assist humans on a screen. This platform automates regulated workflows with a deny-by-default authorization layer and an audit trail that satisfies Part 11. Different category." |
| *"Our CISO won't approve LLMs touching PHI."* | "PHI is masked at the audit boundary before any LLM sees it. The architecture was designed for that conversation — we have a CISO briefing deck and a TPRM packet ready." |
| *"We're not ready — we need to sort out our data first."* | "The Assessment engagement is specifically designed to tell you what's ready and what isn't, so you don't invest in a POC on a bad foundation. That's the right starting point." |
| *"It's too expensive."* | "The ROI model for Agent 02 alone shows payback in under 6 months at 300+ ICSRs/month. We can run your numbers in 30 minutes with the TCO tool." |
| *"We're waiting for our Part 11 validation framework to be approved."* | "The platform generates the IQ/OQ/PQ documentation as a deliverable of the Pilot. Your validation team reviews it — they don't build it from scratch." |
| *"Anthropic / Claude isn't on our approved vendor list."* | "Bedrock abstracts the model — your data stays in your AWS account. We can also configure the platform to use Amazon Titan or a Bedrock-accessible model your team has already approved." |

---

## Competitor One-Liners

| Competitor / alternative | How to position |
|---|---|
| **Veeva Vault AI / Vault CoPilot** | Veeva AI assists inside Vault workflows. This platform governs agents that span multiple systems (Vault, Argus, Medidata, TrackWise) and produces auditable outputs — it complements Vault rather than replacing it. |
| **Microsoft Azure OpenAI + Copilot Studio** | Azure is a capable platform; this accelerator is AWS-native with Bedrock GuardRails and AgentCore Identity for regulated HCLS. Customers who are AWS-committed shouldn't rebuild the compliance scaffolding in Azure. |
| **Custom LangChain/LangGraph build** | That's what this is — a production-hardened LangGraph implementation with the governance layer already built and tested. Why start from zero? |
| **Palantir AIP** | Palantir requires significant platform adoption. This is an open accelerator delivered as SI code the customer owns, deployed in their AWS account, with no ongoing platform license dependency. |
| **Inovalon / IQVIA AI** | Domain-specific SaaS with limited customization. This accelerator is customizable by design — it's a starting point for an SI engagement, not a fixed product. |
| **"Wait for AWS to build it"** | AWS builds the infrastructure (Bedrock, AgentCore, Step Functions). They don't build domain-specific, Part 11-compliant ICSR or regulatory workflows. That's the SI's role — and this accelerator gives the SI a credible starting point. |

---

## Deal Stages and Milestones

| Stage | Exit criteria | Key action |
|---|---|---|
| **Qualify** | 2+ qualifying questions answered yes; AWS account confirmed; economic buyer identified | Register in APN AOM; request HCLS SA |
| **Assessment** | SOW signed; discovery workshop scheduled | Apply for PoA credits; schedule WAFR |
| **POC** | POC SOW signed; agent selected; go/no-go criteria documented | MAP application in flight; Cognito and Bedrock access confirmed |
| **Pilot** | Pilot SOW signed; live connector agreed; validation scope scoped | ISV Accelerate enrollment; Marketplace private offer drafted |
| **Managed Service** | MS contract signed; SLAs agreed; operations team transitioned | Marketplace private offer executed; EDP drawdown confirmed |

---

## Leave-Behind References

| Need | Document |
|---|---|
| Executive overview | `HCLS-Agentic-AI-Suite-Executive-Overview.pdf` (16-slide deck) |
| Customer-facing teaser | `HCLS-Customer-Teaser-5slide.pptx` |
| One-pager | `HCLS-One-Pager.pdf` |
| Per-agent deployment detail | `deliverables/agent-handbooks/HCLS-Deployment-Handbook-<agent>.pdf` |
| TPRM / CISO packet | `offerings/TPRM-DUE-DILIGENCE-PACKET.md` |
| ROI / business case | `offerings/TCO-MODEL.md` |
| Objection handling (detailed) | `offerings/OBJECTION-HANDLING.md` |
| AWS funding guide | `docs/AWS-FUNDING-AND-GTM.md` |
| Shared responsibility matrix | `docs/SHARED-RESPONSIBILITY-MATRIX.md` |

---

*This battlecard is an internal reference — not for direct distribution to customers. Use `HCLS-Customer-Teaser-5slide.pptx` and `HCLS-One-Pager.pdf` as customer-facing materials.*
