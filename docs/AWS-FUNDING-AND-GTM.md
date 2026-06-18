# AWS Funding Programs & GTM Mechanics
### How to fund the Assessment, POC, and Pilot — and who pays

> **For account teams and SI engagement managers.** This document answers "who pays for the pilot?" and explains how to route an HCLS AI Agent engagement through AWS funding programs, co-sell mechanics, and partner motions. Share selectively — it is an internal reference, not a customer-facing leave-behind.

---

## 1. The Three Programs That Matter

### 1.1 Migration Acceleration Program (MAP)

MAP was designed for cloud migrations but has been extended to **AI/ML modernization workloads** when the project moves regulated workflows from on-premises or legacy SaaS to AWS.

| Item | Detail |
|---|---|
| **What it funds** | AWS infrastructure credits (EC2, Bedrock inference tokens, S3, DynamoDB, Step Functions) — not SI labor |
| **Typical credit range** | $25K–$200K+ depending on TCV and AWS account spend commitment |
| **Qualification bar** | Customer must commit to a spend path (MAP baseline); engagement must involve measurable workload migration |
| **How to apply** | AWS account team files through the AWS Partner Network (APN) MAP tool; SI co-applies as the "delivery partner" |
| **HCLS fit** | Strong when the customer is migrating from on-prem PV, QMS, or clinical data systems to cloud-native |
| **Timeline** | 4–6 weeks for approval; align with deal stages, not the last week before SOW signature |

**Framing for the customer:** "AWS has a program that can offset your Bedrock inference and infrastructure costs during the pilot. We work with the AWS account team to apply — no separate procurement action required from you."

---

### 1.2 Partner Originated Assistance (PoA) / AWS Partner Credits

PoA credits are **AWS-funded, SI-facilitated** credits granted when the SI sources the opportunity and AWS validates the technical use case.

| Item | Detail |
|---|---|
| **What it funds** | AWS service consumption credits — Bedrock inference, AgentCore calls, Step Functions state transitions, DynamoDB, CloudWatch |
| **Typical amount** | $10K–$50K for a POC; up to $150K for a Pilot with committed pipeline |
| **Qualification bar** | Opportunity must be registered in APN Opportunity Management (AOM); SI must be the sourcing partner |
| **How to apply** | Register the opportunity early (at Assessment stage, not POC close); AWS Solutions Architect validates the architecture; credits flow after approval |
| **HCLS fit** | Best fit for net-new Bedrock + AgentCore workloads; Agent 02 (PV/ICSR) and Agent 01 (Regulatory) have strong signal for AWS Healthcare & Life Sciences team interest |
| **Key contact** | AWS HCLS specialist SA or PDM (Partner Development Manager) assigned to your SI |

**Do this at Assessment stage, not POC signature.** Credits take weeks to process and must pre-date the consumption period.

---

### 1.3 ISV Accelerate / AWS Marketplace Private Offer

If the SI intends to **resell or co-sell** the HCLS Agent Suite (or a customer-specific derivative) via AWS Marketplace, ISV Accelerate is the relevant program.

| Item | Detail |
|---|---|
| **What it does** | AWS co-sells alongside the SI/ISV, with Marketplace private offers enabling the customer to consume the engagement against their AWS committed spend (EDP/MOSA) |
| **Why it matters** | Customers with Enterprise Discount Program (EDP) contracts can pay for the SI engagement + AWS services in a single Marketplace transaction, consuming against their committed spend |
| **Qualification bar** | SI must be enrolled in ISV Accelerate or ISV Partner Path; product must be listed (or in-process) on AWS Marketplace |
| **HCLS Agent Suite path** | List the accelerator as a professional services offer or SaaS-based managed service; see `docs/AWS-MARKETPLACE-PATH.md` for the listing mechanics |
| **Revenue split** | AWS takes a Marketplace fee (typically 3–13%); negotiated separately; offset by EDP drawdown value to the customer |

---

## 2. The AWS Co-Sell Motion

Co-sell is **not automatic** — it requires registration and an AWS field sponsor. The mechanics:

```
SI registers opportunity in APN Opportunity Management (AOM)
  → AWS HCLS PDM validates and assigns to field SA
    → AWS SA co-presents architecture / runs WAFR
      → AWS account team co-sponsors funding (MAP/PoA)
        → Deal closes with AWS Marketplace private offer or direct PO
```

**What the SI needs to do:**
1. Register every qualified opportunity in AOM at Assessment stage (not later).
2. Attach the AWS HCLS SA to the deal — they run the WAFR, which also validates the architecture for the customer's SA/CISO audience.
3. Request a "joint customer briefing" with the AWS account team for enterprise accounts — AWS field will co-present if the opportunity is registered and the deal size justifies it.

---

## 3. Funding by Engagement Stage

| Stage | Who pays | AWS program | Typical size |
|---|---|---|---|
| **Discovery / scoping call** | SI absorbs | None | — |
| **Assessment** (4–6 wk) | Customer pays SI fees | PoA credits offset AWS costs | $5K–$15K AWS credits |
| **POC** (8–12 wk) | Customer pays SI + AWS | MAP or PoA; Bedrock/AgentCore credits | $20K–$75K AWS credits |
| **Pilot** (12–20 wk) | Customer pays SI + AWS | MAP (migration framing); larger credit envelope | $50K–$200K AWS credits |
| **Managed Service** | Recurring (monthly) | EDP/MOSA + Marketplace | Ongoing |

---

## 4. Objection: "The Customer Won't Pay for the POC"

This is common in life sciences. The plays:

**Play A — AWS-funded POC.** Use MAP/PoA to zero out the AWS infrastructure cost; SI reduces or defers fees in exchange for a committed Pilot SOW contingent on POC success. Document the go/no-go criteria in writing (see `offerings/SOW-TEMPLATE.md`).

**Play B — AWS-co-invest POC.** AWS HCLS team has discretionary "customer investment" budget for strategic accounts. Requires the AWS account team to be engaged early and the customer to be a target account in AWS's healthcare vertical plan.

**Play C — Assessment → joint business case.** Run the Assessment (smaller spend, defined deliverables), use it to build the business case, and let the ROI model (see `offerings/TCO-MODEL.md`) justify the POC budget internally. Many regulated-industry finance teams will approve a $200K POC if the business case shows $3M+ annual benefit.

---

## 5. Internal Checklist — Before the First Customer Meeting

- [ ] Opportunity registered in APN Opportunity Management (AOM)
- [ ] AWS HCLS PDM / account team notified and invited to co-sell
- [ ] AWS SA identified for WAFR co-presentation
- [ ] MAP/PoA application timeline noted against expected POC start date
- [ ] EDP/MOSA status of customer account checked (determines Marketplace viability)
- [ ] ISV Accelerate enrollment confirmed if Marketplace private offer is in scope

---

## 6. Who to Call at AWS

| Role | When to engage | What they do |
|---|---|---|
| **HCLS Industry Specialist SA** | Assessment → POC | Validates architecture, co-presents to customer SA/CISO, supports WAFR |
| **Partner Development Manager (PDM)** | Deal registration | Manages co-sell motion, MAP/PoA applications, Marketplace enrollment |
| **AWS Account Executive** | Strategic accounts | Co-sponsors joint briefings, escalates funding approvals |
| **AWS ProServe** | If customer prefers AWS-direct delivery | Can subcontract SI or run parallel engagement; coordinate early to avoid channel conflict |

---

*For Marketplace listing mechanics, see `docs/AWS-MARKETPLACE-PATH.md`.
For WAFR pillar mapping, see `docs/WELL-ARCHITECTED-REVIEW.md`.
For engagement SOW shells, see `offerings/SOW-TEMPLATE.md`.*
