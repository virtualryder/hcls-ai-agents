# AWS Marketplace Listing Path & Private Offer Guide
### How to transact the HCLS AI Agent Suite through AWS Marketplace

> **For SI leadership and partnership teams.** This document covers the mechanics of listing the HCLS Agent Suite on AWS Marketplace, structuring private offers so customers can consume against their committed spend, and the enrollment steps for ISV Accelerate co-sell.

---

## Why Marketplace Matters for HCLS Deals

Life sciences enterprises increasingly have **Enterprise Discount Program (EDP)** or **MOSA (Marketplace Offering Subscription Agreement)** commitments to AWS — contracts that require them to run a percentage of their IT spend through AWS or AWS Marketplace. A private offer lets the customer count your SI engagement fees toward that commitment.

The practical effect: **your deal competes with "free money" the customer has already committed to AWS**, and a Marketplace private offer converts that into budget for your engagement.

---

## Listing Options

### Option A — Professional Services Listing (Fastest Path)

A **professional services listing** is the fastest path to Marketplace. It does not require software to be hosted on AWS — it is a catalog entry for a consulting engagement.

| Item | Detail |
|---|---|
| **What it covers** | Assessment, POC, Pilot, and Managed Service engagements priced as fixed-fee or T&M |
| **AWS Marketplace category** | Professional Services → AI/ML → Healthcare & Life Sciences |
| **Listing fee** | AWS charges a Marketplace transaction fee (typically 3–5% of the transaction amount; negotiate with your PDM) |
| **Customer benefit** | Counts toward EDP commitment; single AWS invoice; no separate procurement action |
| **Time to list** | 2–4 weeks once enrolled in AWS Marketplace Seller program |
| **Drawback** | Less discoverability than software listings; customers must be directed to the listing by the SI or AWS account team |

### Option B — SaaS Listing (Managed Service Path)

If the SI operates the HCLS Agent Suite as a **managed service** (SI runs the infrastructure in the customer's account or SI's account), it can be listed as a SaaS product.

| Item | Detail |
|---|---|
| **What it covers** | Recurring managed service subscription — AWS infrastructure + platform operations + HITL queue support |
| **Pricing models** | Per-agent/month, per-seat/month, or usage-based (Bedrock token consumption + platform fee) |
| **AWS Marketplace category** | Software → Machine Learning → Healthcare & Life Sciences |
| **Listing fee** | 3–13% Marketplace fee on transaction amount; negotiated based on committed revenue |
| **Customer benefit** | EDP drawdown; metered billing aligned with AWS invoice; no separate procurement |
| **Time to list** | 6–10 weeks (requires integration with AWS Metering Service if usage-based) |
| **Drawback** | Requires software integration (AWS Marketplace Metering Service API); more implementation work than professional services listing |

### Option C — Private Offer (No Public Listing Required)

A **private offer** can be created and sent directly to a named customer account without a public Marketplace listing. This is the fastest path for a single-customer deal.

| Item | Detail |
|---|---|
| **What it covers** | Any engagement type — fixed-fee POC, Pilot, or Managed Service subscription |
| **Requirement** | SI must be enrolled as a Marketplace seller (independent of ISV Accelerate); enrollment takes 2–4 weeks |
| **How it works** | SI creates the offer in the Marketplace Management Portal, enters the customer's AWS account ID, sets price and duration, and sends the offer link. Customer accepts through their AWS console. |
| **Customer benefit** | EDP drawdown; no public listing required; terms are private between SI and customer |
| **Best for** | First deal while public listing is in progress; strategic accounts where a public listing is premature |

---

## ISV Accelerate Enrollment

**ISV Accelerate** is the AWS program that enables co-sell — AWS field actively promoting your listing to customers. Without enrollment, you can still transact through Marketplace but AWS field will not co-sell.

### Eligibility Requirements

- [ ] Active AWS Partner Network (APN) member at **Select tier or above**
- [ ] At least one Marketplace listing published (or in-review)
- [ ] AWS-validated reference architecture (WAFR completion strongly recommended)
- [ ] At least one customer reference on AWS

### Enrollment Steps

1. Log in to APN Partner Central → Programs → ISV Accelerate → Apply.
2. Submit the application with: company info, listing URL (or draft), primary use case (Healthcare & Life Sciences, AI/ML), and 1–2 customer references.
3. AWS reviews within 2–4 weeks; enrollment includes assignment of a Partner Development Representative (PDR) who manages co-sell pipeline.
4. Once enrolled, register every qualified opportunity in **APN Opportunity Management (AOM)** → ISV Accelerate co-sell pipeline. AWS field receives a notification and can choose to co-sell.

---

## Private Offer — Step-by-Step for an HCLS POC

This walkthrough covers a standard 8–12 week HCLS POC sold as a fixed-fee private offer.

### Step 1 — SI Marketplace Seller Enrollment

- Go to: [aws.amazon.com/marketplace/management](https://aws.amazon.com/marketplace/management) → Register as a seller.
- Provide: company legal name, bank account for payment, tax information.
- AWS reviews and approves (typically 5–10 business days).

### Step 2 — Create the Private Offer

In the Marketplace Management Portal:
1. Navigate to **Offers → Create private offer**.
2. Select **Professional Services** as the product type.
3. Enter:
   - **Offer name:** `HCLS AI Agent Suite POC — [Customer Name]`
   - **Customer AWS account ID:** (get from the customer's IAM console → top right → Account)
   - **Price:** Fixed fee matching the POC SOW amount
   - **Duration:** POC term (e.g., 90 days)
   - **Description:** Summary of POC scope (copy from `offerings/POC-OFFERING.md`)
4. Upload the executed SOW as an attachment (optional but recommended for records).
5. Send the offer — customer receives an email with a link to accept through their AWS console.

### Step 3 — Customer Acceptance

Customer navigates to AWS Marketplace → Private offers → Reviews and accepts. The transaction appears on their next AWS invoice and counts toward EDP commitment.

### Step 4 — Revenue Recognition

AWS disburses payment to the SI (minus Marketplace fee) per the standard disbursement schedule (typically monthly, 45 days after transaction).

---

## Pricing Structures for Marketplace

### POC Engagement (Professional Services)

```
HCLS AI Agent POC — [Agent Name]
  Fixed fee:  $[X00,000]
  Duration:   90 days
  Includes:   SI labor + architecture + go/no-go report
  Excludes:   AWS service consumption (customer's AWS bill)
```

### Managed Service (SaaS or Professional Services Subscription)

```
HCLS AI Agent Suite — Managed Service
  Platform fee:     $[X0,000] / month
  Per-agent fee:    $[X,000] / agent / month (1–8 agents)
  AWS pass-through: Bedrock inference + AgentCore + DynamoDB billed direct to customer
  Minimum term:     12 months
```

Use `offerings/TCO-MODEL.md` to derive the platform fee from estimated Bedrock inference costs, SI operations labor, and target margin.

---

## Common Questions

**Q: Can the customer use AWS credits (from MAP or PoA) to pay for the Marketplace private offer?**
A: AWS credits apply to AWS service consumption (Bedrock inference, DynamoDB, etc.) — **not** to the SI fee component of a professional services private offer. The customer's EDP commitment can cover the SI fee; MAP/PoA credits cover the AWS service consumption separately.

**Q: What if the customer's procurement team won't route through Marketplace?**
A: A direct PO with the SI is always an option. Marketplace is an enabler, not a requirement. Lead with value; offer Marketplace as the "easy procurement path" rather than the only path.

**Q: Do we need a public Marketplace listing before creating a private offer?**
A: No. Private offers do not require a public listing. This is the fastest path for the first deal.

**Q: Does transacting through Marketplace affect the BAA with AWS?**
A: No. The AWS BAA is between the customer and AWS; it covers eligible AWS services regardless of whether the engagement is transacted through Marketplace.

---

## Contacts and Resources

| Resource | Link / Contact |
|---|---|
| AWS Marketplace Management Portal | aws.amazon.com/marketplace/management |
| APN Partner Central (ISV Accelerate enrollment) | partnercentral.aws.amazon.com |
| AWS Marketplace Seller Guide | AWS documentation → Marketplace Seller Guide |
| HCLS PDM (Partner Development Manager) | Contact your AWS alliances lead for the HCLS-assigned PDM |
| ISV Accelerate team | Via Partner Central → Contact your PDR |

---

*Related: `docs/AWS-FUNDING-AND-GTM.md`, `offerings/SOW-TEMPLATE.md`, `offerings/TCO-MODEL.md`*
