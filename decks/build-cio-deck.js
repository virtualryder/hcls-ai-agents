/* HCLS AI Agent Suite — CIO / CISO / Director of Architecture Adoption Review
   Board-ready, honest-broker deck. Navy / teal / amber visual language.
   Run:  node decks/build-cio-deck.js [outfile.pptx]
*/
const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const Fa = require("react-icons/fa");

// ---------- palette ----------
const NAVY   = "1E2761";
const NAVYDK = "12183A";
const NAVY2  = "232C57";
const TEAL   = "00A896";
const TEALDK = "067A6E";
const TEALLT = "7FE3D2";
const AMBER  = "E8A33D";
const AMBERDK = "B5790F";
const SLATE  = "33384F";
const SLATE2 = "5A6485";
const ICE    = "CADCFC";
const BGLT   = "F4F7FC";
const CARD   = "FFFFFF";
const CARDTINT = "EEF2FB";
const WHITE  = "FFFFFF";
const LINE   = "D9E0EF";
const RED    = "C2543B";
const GREEN  = "2E7D5B";

const OWN_USER = "5A6485";
const OWN_CUST = "1E2761";
const OWN_DEV  = "00A896";

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.author = "HCLS AI Agent Suite";
pres.title  = "HCLS AI Agent Suite — Infrastructure & Adoption Review";
const PW = 13.333, PH = 7.5;

const iconCache = {};
async function icon(Comp, color = "FFFFFF", size = 256) {
  const key = Comp.name + color + size;
  if (iconCache[key]) return iconCache[key];
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(Comp, { color: "#" + color, size: String(size) }));
  const png = await sharp(Buffer.from(svg)).png().toBuffer();
  const data = "image/png;base64," + png.toString("base64");
  iconCache[key] = data;
  return data;
}
const shadow = () => ({ type: "outer", color: "000000", blur: 7, offset: 3, angle: 90, opacity: 0.16 });
const softShadow = () => ({ type: "outer", color: "000000", blur: 5, offset: 2, angle: 90, opacity: 0.10 });

async function iconCircle(slide, Comp, cx, cy, d, circleColor, iconColor) {
  slide.addShape(pres.shapes.OVAL, { x: cx, y: cy, w: d, h: d, fill: { color: circleColor }, line: { type: "none" } });
  const ip = d * 0.26;
  slide.addImage({ data: await icon(Comp, iconColor), x: cx + ip, y: cy + ip, w: d - 2 * ip, h: d - 2 * ip });
}
function iconCircleSync(slide, Comp, cx, cy, d, circleColor, iconColor) {
  slide.addShape(pres.shapes.OVAL, { x: cx, y: cy, w: d, h: d, fill: { color: circleColor }, line: { type: "none" } });
  const ip = d * 0.26;
  const key = Comp.name + iconColor + 256;
  slide.addImage({ data: iconCache[key], x: cx + ip, y: cy + ip, w: d - 2 * ip, h: d - 2 * ip });
}
function lightHeader(slide, kicker, title, num) {
  slide.background = { color: BGLT };
  slide.addText(kicker.toUpperCase(), { x: 0.6, y: 0.34, w: 10.5, h: 0.3, fontFace: "Calibri", fontSize: 12, bold: true, color: TEAL, charSpacing: 2, margin: 0 });
  slide.addText(title, { x: 0.6, y: 0.62, w: 11.4, h: 0.7, fontFace: "Cambria", fontSize: 27, bold: true, color: NAVY, margin: 0 });
  slide.addText(String(num), { x: PW - 0.92, y: 0.34, w: 0.5, h: 0.34, align: "center", fontFace: "Calibri", fontSize: 12, bold: true, color: SLATE2, margin: 0 });
}
function footer(slide) {
  slide.addText("HCLS AI Agent Suite  ·  Infrastructure & Adoption Review  ·  Governed accelerator, not a turnkey certified product",
    { x: 0.6, y: PH - 0.36, w: 12.1, h: 0.28, fontFace: "Calibri", fontSize: 8.5, color: SLATE2, margin: 0 });
}

// SLIDE 1 — TITLE
async function slideTitle() {
  const s = pres.addSlide();
  s.background = { color: NAVYDK };
  s.addShape(pres.shapes.OVAL, { x: 10.4, y: -1.4, w: 4.6, h: 4.6, fill: { color: NAVY2 }, line: { type: "none" } });
  s.addShape(pres.shapes.OVAL, { x: 11.6, y: 4.6, w: 3.4, h: 3.4, fill: { color: NAVY }, line: { type: "none" } });
  await iconCircle(s, Fa.FaShieldAlt, 0.7, 0.66, 0.92, TEAL, WHITE);
  s.addText("HCLS AI AGENT SUITE", { x: 1.78, y: 0.74, w: 8, h: 0.4, fontFace: "Calibri", fontSize: 15, bold: true, color: TEALLT, charSpacing: 3, margin: 0 });
  s.addText("Infrastructure &\nAdoption Review", { x: 0.7, y: 2.05, w: 9.2, h: 2.0, fontFace: "Cambria", fontSize: 50, bold: true, color: WHITE, lineSpacingMultiple: 0.98, margin: 0 });
  s.addText("A CIO / CISO / Director of Architecture perspective", { x: 0.72, y: 4.05, w: 10, h: 0.5, fontFace: "Cambria", italic: true, fontSize: 20, color: ICE, margin: 0 });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.7, y: 5.15, w: 11.9, h: 1.2, rectRadius: 0.08, fill: { color: NAVY2 }, line: { color: TEAL, width: 1 } });
  s.addText([
    { text: "THE VERDICT, UP FRONT   ", options: { bold: true, color: TEALLT, fontSize: 12, charSpacing: 1 } },
    { text: "Adopt as a governed accelerator to compress an SI-led build — not as a turnkey, validated product.", options: { color: WHITE, fontSize: 14.5 } },
  ], { x: 1.0, y: 5.34, w: 11.3, h: 0.84, fontFace: "Calibri", valign: "middle", margin: 0 });
  s.addText("8 governed agents · AWS-native · 21 CFR Part 11 / GxP · GVP/E2B · HIPAA · FDA AI guidance (Jan 2025) · NIST AI RMF",
    { x: 0.72, y: 6.62, w: 11.8, h: 0.4, fontFace: "Calibri", fontSize: 12, color: SLATE2, margin: 0 });
  s.addNotes("Frame the room: you are the CIO / CISO / Director of Architecture, and your job is to tell the board honestly what this is and is not. Lead with the verdict so no one waits for the punchline: a governed accelerator that compresses an SI-led build, NOT a shrink-wrapped, computer-system-validated product you switch on. The decision you ask for at the end is approval to fund a Phase-1 pilot on the lowest-risk agents.");
}

// SLIDE 2 — BLUF
async function slideBLUF() {
  const s = pres.addSlide();
  s.background = { color: NAVYDK };
  s.addText("BOTTOM LINE UP FRONT", { x: 0.7, y: 0.5, w: 10, h: 0.4, fontFace: "Calibri", fontSize: 13, bold: true, color: TEAL, charSpacing: 2, margin: 0 });
  s.addText("Adopt it as a governed accelerator — not a finished product", { x: 0.7, y: 0.86, w: 12, h: 0.8, fontFace: "Cambria", fontSize: 29, bold: true, color: WHITE, margin: 0 });
  const cards = [
    { ic: Fa.FaCheckCircle, col: TEAL, h: "What you are buying", b: "A governance spine in code + 536 tests, AWS deployment runbooks, and a reference architecture (dual MCP gateway, private-connectivity Bedrock, HITL, audit). It hands an SI a compliant, auditable starting point across 8 life-sciences workflows." },
    { ic: Fa.FaTools, col: AMBER, h: "What you still build", b: "Live Veeva / Argus / Medidata / QMS connectors, the reviewer UI, IdP federation, computer-system validation (CSV/CSA), and a penetration test. This is an engagement, not an install." },
    { ic: Fa.FaBalanceScale, col: ICE, h: "Why that is the right buy", b: "It moves the hard, slow, risky part — governed access, HITL, audit, PHI masking, grounding — off your critical path. You compress months of SI build while keeping GxP / 21 CFR Part 11 accountability where it belongs: with you." },
  ];
  let x = 0.7; const cw = 3.86, gap = 0.27, cy = 1.95, ch = 3.25;
  for (const c of cards) {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: cy, w: cw, h: ch, rectRadius: 0.1, fill: { color: NAVY2 }, line: { type: "none" }, shadow: shadow() });
    await iconCircle(s, c.ic, x + 0.3, cy + 0.32, 0.78, c.col, NAVYDK);
    s.addText(c.h, { x: x + 0.3, y: cy + 1.22, w: cw - 0.6, h: 0.5, fontFace: "Cambria", fontSize: 16.5, bold: true, color: WHITE, margin: 0 });
    s.addText(c.b, { x: x + 0.3, y: cy + 1.72, w: cw - 0.6, h: ch - 1.9, fontFace: "Calibri", fontSize: 11.5, color: ICE, margin: 0, lineSpacingMultiple: 1.04 });
    x += cw + gap;
  }
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.7, y: 5.5, w: 11.93, h: 1.28, rectRadius: 0.08, fill: { color: TEAL }, line: { type: "none" } });
  s.addText([
    { text: "Recommendation:  ", options: { bold: true, color: NAVYDK, fontSize: 15 } },
    { text: "Approve a funded Phase-1 pilot on the lowest-decision-risk agents. Prove the gateway, audit, PHI masking, and HITL gate in production, then expand. Do not present this to the board as a product you can turn on next week.", options: { color: NAVYDK, fontSize: 13.5 } },
  ], { x: 1.05, y: 5.62, w: 11.2, h: 1.04, fontFace: "Calibri", valign: "middle", margin: 0 });
  s.addNotes("The one slide if you only had one. Three columns: what you buy, what you still build, why the trade is right. Reset the SaaS expectation calmly — the value is acceleration of an SI build, not elimination of one. If pushed 'so it's not finished?' agree plainly: correct, and that is normal for governed AI touching regulated GxP records in 2026.");
}

// SLIDE 3 — MATURITY
async function slideMaturity() {
  const s = pres.addSlide();
  lightHeader(s, "What it actually is", "The maturity ladder — positioned honestly", 3);
  const rungs = [
    { lvl: "Documented", col: SLATE2, txt: "Architecture, workflow & compliance design written and reviewed", reached: true },
    { lvl: "Demonstrated", col: TEAL, txt: "Runs end-to-end in demo mode — deterministic fixtures, no API key (536 tests green)", reached: true },
    { lvl: "Deployable", col: NAVY, txt: "CloudFormation + Terraform + container contract pass CI; needs your AWS account + Bedrock", reached: true },
    { lvl: "Production-ready", col: AMBER, txt: "CSV/CSA validation, IdP, live connectors, pen test — the engagement", reached: false },
  ];
  let y = 1.55; const rh = 1.18, rw = 6.5;
  for (let i = 0; i < rungs.length; i++) {
    const r = rungs[i];
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y, w: rw, h: rh - 0.16, rectRadius: 0.07, fill: { color: r.reached ? CARD : CARDTINT }, line: { color: r.reached ? r.col : LINE, width: r.reached ? 1.25 : 1 }, shadow: r.reached ? softShadow() : undefined });
    s.addShape(pres.shapes.OVAL, { x: 0.82, y: y + 0.21, w: 0.62, h: 0.62, fill: { color: r.col }, line: { type: "none" } });
    s.addText(String(i + 1), { x: 0.82, y: y + 0.21, w: 0.62, h: 0.62, align: "center", valign: "middle", fontFace: "Cambria", fontSize: 18, bold: true, color: WHITE, margin: 0 });
    s.addText([
      { text: r.lvl, options: { bold: true, fontSize: 15, color: r.reached ? NAVY : SLATE2, breakLine: true } },
      { text: r.txt, options: { fontSize: 11, color: SLATE, breakLine: false } },
    ], { x: 1.62, y: y + 0.1, w: rw - 1.25, h: rh - 0.32, fontFace: "Calibri", valign: "middle", margin: 0, lineSpacingMultiple: 1.0 });
    if (!r.reached) s.addText("BRIGHT LINE — the engagement starts here", { x: 0.6, y: y + rh - 0.2, w: rw, h: 0.26, fontFace: "Calibri", fontSize: 9.5, italic: true, bold: true, color: AMBERDK, align: "right", margin: 0 });
    y += rh;
  }
  const rx = 7.4, rwc = 5.3;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: rx, y: 1.55, w: rwc, h: 2.42, rectRadius: 0.09, fill: { color: CARD }, line: { color: TEAL, width: 1.25 }, shadow: softShadow() });
  await iconCircle(s, Fa.FaCheckCircle, rx + 0.26, 1.78, 0.6, TEAL, WHITE);
  s.addText("Real today", { x: rx + 1.0, y: 1.83, w: rwc - 1.2, h: 0.5, fontFace: "Cambria", fontSize: 16, bold: true, color: NAVY, margin: 0 });
  s.addText([
    { text: "Governance spine in code + 536 passing tests (gateway intersection, HITL, PHI masking, grounding, red-team) — no API key", options: { bullet: true, breakLine: true } },
    { text: "Empty-account-to-running CloudFormation quick-deploy: connector Lambdas + dual MCP gateway + native/container agent; Terraform parity", options: { bullet: true, breakLine: true } },
    { text: "Live reference path (Agent 02): real Bedrock + real HTTP connector, end-to-end; Strands + Step Functions waitForTaskToken HITL", options: { bullet: true } },
  ], { x: rx + 0.28, y: 2.42, w: rwc - 0.55, h: 1.5, fontFace: "Calibri", fontSize: 10.3, color: SLATE, margin: 0, paraSpaceAfter: 5, lineSpacingMultiple: 0.98 });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: rx, y: 4.12, w: rwc, h: 2.42, rectRadius: 0.09, fill: { color: CARDTINT }, line: { color: AMBER, width: 1.25 } });
  await iconCircle(s, Fa.FaSeedling, rx + 0.26, 4.35, 0.6, AMBER, WHITE);
  s.addText("A starting point, not finished", { x: rx + 1.0, y: 4.4, w: rwc - 1.2, h: 0.5, fontFace: "Cambria", fontSize: 16, bold: true, color: NAVY, margin: 0 });
  s.addText([
    { text: "Live connectors run on fixtures; production validation against Veeva / Argus / Medidata / QMS is yours", options: { bullet: true, breakLine: true } },
    { text: "AgentCore managed-gateway registration uses customer-supplied custom-resource placeholders; reviewer UI is an SI build", options: { bullet: true, breakLine: true } },
    { text: "No computer-system validation (CSV/CSA) package of its own, no SOC 2 / 3rd-party cert, no pen-tested production surface yet", options: { bullet: true } },
  ], { x: rx + 0.28, y: 5.0, w: rwc - 0.55, h: 1.5, fontFace: "Calibri", fontSize: 10.3, color: SLATE, margin: 0, paraSpaceAfter: 5, lineSpacingMultiple: 0.98 });
  footer(s);
  s.addNotes("Use the ladder to set honest expectations. The suite is genuinely at Demonstrated and Deployable-by-design: code runs, 536 tests pass with no API key, IaC validates. The bright line is rung 4 — Production-ready — explicitly the engagement (CSV/CSA validation, live connectors, pen test), not a day-one deliverable. The 536 passing tests are your strongest credibility point: governance is in code and tested, not slideware.");
}

// SLIDE 4 — WHY A CISO CAN SAY YES
async function slideWhyYes() {
  const s = pres.addSlide();
  lightHeader(s, "The strength", "Why a CISO or QA / regulatory lead can say yes", 4);
  s.addText("Governance-first: the controls are enforced in the gateway, outside the model — a prompt cannot turn them off.", { x: 0.6, y: 1.35, w: 12.1, h: 0.4, fontFace: "Calibri", fontSize: 13, italic: true, color: SLATE2, margin: 0 });
  const items = [
    { ic: Fa.FaLock, h: "Deny-by-default gateway", b: "permitted(tool) = agent-grant ∩ user-entitlement. An agent can never exceed the human it acts for. Denies on a missing subject." },
    { ic: Fa.FaUserCheck, h: "Framework-enforced HITL", b: "Consequential actions block as PENDING_APPROVAL until a named, correctly-roled reviewer binds identity (21 CFR Part 11 e-signature). Fails closed on timeout." },
    { ic: Fa.FaClipboardList, h: "Tamper-evident audit", b: "Append-only DynamoDB + S3 Object Lock WORM. Every ALLOW / DENY / PENDING / ERROR logged with lineage — Part 11 / ALCOA+ recordkeeping." },
    { ic: Fa.FaUserSecret, h: "PHI / PII masking", b: "Patient identifiers replaced with stable pseudonyms before any prompt or audit record. Stateless, runs before every gateway call." },
    { ic: Fa.FaSearch, h: "Grounding verification", b: "Every figure / entity in a regulated artifact must trace to the source corpus; grounding fails fast rather than asserting a hallucinated claim." },
    { ic: Fa.FaBalanceScale, h: "Fairness / diversity screen", b: "Representativeness flags on proposed cohorts (FDA Diversity Action Plan posture); outcomes routed to human review — no automated adverse action." },
  ];
  for (let i = 0; i < items.length; i++) {
    const it = items[i];
    const col = i % 3, row = Math.floor(i / 3);
    const cw = 3.92, ch = 1.62, gx = 0.18, gy = 0.18;
    const cx = 0.6 + col * (cw + gx), cyy = 1.95 + row * (ch + gy);
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: cx, y: cyy, w: cw, h: ch, rectRadius: 0.08, fill: { color: CARD }, line: { color: LINE, width: 1 }, shadow: softShadow() });
    await iconCircle(s, it.ic, cx + 0.24, cyy + 0.24, 0.62, NAVY, WHITE);
    s.addText(it.h, { x: cx + 0.98, y: cyy + 0.22, w: cw - 1.15, h: 0.62, fontFace: "Cambria", fontSize: 13.5, bold: true, color: NAVY, valign: "middle", margin: 0 });
    s.addText(it.b, { x: cx + 0.24, y: cyy + 0.86, w: cw - 0.45, h: ch - 0.96, fontFace: "Calibri", fontSize: 9.6, color: SLATE, margin: 0, lineSpacingMultiple: 0.97 });
  }
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 5.62, w: 12.13, h: 1.18, rectRadius: 0.07, fill: { color: NAVY }, line: { type: "none" } });
  await iconCircle(s, Fa.FaShieldAlt, 0.82, 5.84, 0.74, TEAL, WHITE);
  s.addText([
    { text: "Mapped to the life-sciences regulatory stack:  ", options: { bold: true, color: TEALLT, fontSize: 12 } },
    { text: "21 CFR Part 11 · GxP / ALCOA+ · GVP / ICH E2B(R3) · ICH E6(R3) GCP · HIPAA / de-identification · FDA AI guidance (Jan 2025) · EMA AI reflection paper · NIST AI RMF. The bright line — causality, reportability, what is submitted, CAPA disposition, patient eligibility, what reaches an HCP — is never decided by the agent.", options: { color: WHITE, fontSize: 11 } },
  ], { x: 1.7, y: 5.74, w: 10.85, h: 0.95, fontFace: "Calibri", valign: "middle", margin: 0, lineSpacingMultiple: 0.98 });
  footer(s);
  s.addNotes("The slide that gets your CISO, QA head, and regulatory lead to lean in. Key message: controls live in the gateway, OUTSIDE the model — a prompt injection cannot disable deny-by-default, the HITL gate, the audit trail, or PHI masking. Emphasize the intersection rule and that the HITL gate fails closed. Close on the bright line: the agent never decides causality, reportability, what's submitted, CAPA disposition, patient eligibility, or what reaches an HCP.");
}

// SLIDE 5 — SHORTFALLS
async function slideShortfalls() {
  const s = pres.addSlide();
  lightHeader(s, "The honest part", "Where it falls short — open risks today", 5);
  s.addText("Drawn directly from the deployment reference's own “gaps / what you must add” callouts. None are hidden; all are scoped.", { x: 0.6, y: 1.35, w: 12.1, h: 0.4, fontFace: "Calibri", fontSize: 13, italic: true, color: SLATE2, margin: 0 });
  const gaps = [
    { sev: "STUB", c: NAVY, t: "Live connectors are fixtures", d: "Veeva / Argus / Medidata / QMS run on deterministic fixtures; live validation against your systems is the engagement." },
    { sev: "GAP", c: RED, t: "No CSV/CSA package yet", d: "Computer-system validation (IQ/OQ/PQ) is the regulated production gate; the suite ships the design, not the executed package." },
    { sev: "BUILD", c: NAVY, t: "Reviewer UI is your build", d: "The HITL gate + queue ship; the screen a safety physician / writer / MLR reviewer uses to approve is a customer/SI build." },
    { sev: "PART", c: AMBER, t: "AgentCore = placeholders", d: "Managed Gateway & Runtime register via customer-supplied custom-resource Lambdas; portable gateway mode is the fallback." },
    { sev: "PART", c: AMBER, t: "Observability to author", d: "CloudWatch alarms / dashboards are per-environment; runbooks assume alarms and CloudTrail config you finalize." },
    { sev: "PART", c: AMBER, t: "KB ingestion partial", d: "Bedrock Knowledge Base ingestion IaC is a stub to build out per corpus (guidance, label, SOPs)." },
    { sev: "RISK", c: TEALDK, t: "No cert · cost · accuracy", d: "No SOC 2 / 3rd-party cert. Bedrock model cost & clinical accuracy must be validated against your data." },
    { sev: "RISK", c: TEALDK, t: "Change control is process", d: "Prompt / model promotion change-control is framework-supported but operated by you under your quality system." },
  ];
  let i = 0; const cw = 5.92, ch = 1.12, gx = 0.28, gy = 0.18, x0 = 0.6, y0 = 1.92;
  for (const g of gaps) {
    const col = i % 2, row = Math.floor(i / 2);
    const cx = x0 + col * (cw + gx), cyy = y0 + row * (ch + gy);
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: cx, y: cyy, w: cw, h: ch, rectRadius: 0.07, fill: { color: CARD }, line: { color: LINE, width: 1 }, shadow: softShadow() });
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: cx + 0.18, y: cyy + 0.2, w: 0.78, h: 0.34, rectRadius: 0.05, fill: { color: g.c }, line: { type: "none" } });
    s.addText(g.sev, { x: cx + 0.18, y: cyy + 0.2, w: 0.78, h: 0.34, align: "center", valign: "middle", fontFace: "Calibri", fontSize: 9, bold: true, color: WHITE, margin: 0 });
    s.addText(g.t, { x: cx + 1.06, y: cyy + 0.14, w: cw - 1.2, h: 0.34, fontFace: "Cambria", fontSize: 13, bold: true, color: NAVY, margin: 0, valign: "middle" });
    s.addText(g.d, { x: cx + 1.06, y: cyy + 0.47, w: cw - 1.22, h: 0.58, fontFace: "Calibri", fontSize: 9.8, color: SLATE, margin: 0, lineSpacingMultiple: 0.96 });
    i++;
  }
  footer(s);
  s.addNotes("Do not soften this slide. Putting the shortfalls on screen yourself is what makes the rest credible. Three buckets: (1) integration — live connectors, reviewer UI — the bulk of the engagement, gated on your systems; (2) infrastructure-as-code to finish — AgentCore registration, observability, KB ingestion; (3) the things only YOU can finish — CSV/CSA validation, no cert, cost/accuracy validation, change-control under your quality system. 'Isn't this a lot?' Yes — and it's the same list for ANY governed AI build; the difference is here it's written down and scoped.");
}

// SLIDE 6 — QUESTIONS
async function slideQuestions() {
  const s = pres.addSlide();
  lightHeader(s, "Due diligence", "The questions to answer before you adopt", 6);
  const qs = [
    { ic: Fa.FaMapMarkedAlt, h: "Data residency & GxP terms", b: "Which Region? Does it meet data-localization and GxP data-integrity requirements? Are the controls Part 11-aligned in the vendor agreement?" },
    { ic: Fa.FaFileSignature, h: "DPA / BAA in place", b: "Data-processing / business-associate agreement executed; vendor TPRM questionnaire signed off before any live patient or safety record is touched." },
    { ic: Fa.FaIdBadge, h: "IdP federation", b: "Can your IdP (Okta / Entra / Ping) express the reviewer roles (writer / safety physician / CRA / MLR)? Cognito ↔ IdP claim mapping is the most common readiness gap." },
    { ic: Fa.FaClipboardCheck, h: "CSV / validation plan", b: "Who owns the computer-system validation (IQ/OQ/PQ) and the validation lifecycle? Plan it before any GxP go-live." },
    { ic: Fa.FaUserShield, h: "Penetration test", b: "Independent pen test of the deployed surface is a production-readiness gate — budget and schedule it before go-live." },
    { ic: Fa.FaDollarSign, h: "Total cost of ownership", b: "Bedrock inference + infra + SI delivery. Model the run-rate, not just the build; set Budgets + Cost Anomaly Detection on Bedrock." },
    { ic: Fa.FaHeadset, h: "Support & maintenance model", b: "Who owns prompt/model change control, patching, and the managed-service SLA after the SI hands off?" },
    { ic: Fa.FaChartLine, h: "Model-drift monitoring", b: "Who watches grounding-failure rate, Guardrail block rate, and eval regression once it is live, and on what cadence?" },
  ];
  let i = 0; const cw = 5.92, ch = 1.13, gx = 0.28, gy = 0.16, x0 = 0.6, y0 = 1.5;
  for (const q of qs) {
    const col = i % 2, row = Math.floor(i / 2);
    const cx = x0 + col * (cw + gx), cyy = y0 + row * (ch + gy);
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: cx, y: cyy, w: cw, h: ch, rectRadius: 0.07, fill: { color: CARD }, line: { color: LINE, width: 1 }, shadow: softShadow() });
    await iconCircle(s, q.ic, cx + 0.2, cyy + 0.26, 0.6, TEAL, WHITE);
    s.addText(q.h, { x: cx + 0.95, y: cyy + 0.13, w: cw - 1.1, h: 0.36, fontFace: "Cambria", fontSize: 12.5, bold: true, color: NAVY, margin: 0, valign: "middle" });
    s.addText(q.b, { x: cx + 0.95, y: cyy + 0.47, w: cw - 1.12, h: 0.6, fontFace: "Calibri", fontSize: 9.5, color: SLATE, margin: 0, lineSpacingMultiple: 0.95 });
    i++;
  }
  footer(s);
  s.addNotes("These are the eight questions a diligent board should make you answer before signing. Present them as YOUR checklist — it signals you are driving the evaluation. The two highest-friction items: IdP claim mapping (reviewer-role expression) and the CSV/CSA validation plan, which is the regulated production gate. Cost: model the Bedrock run-rate, not just the build.");
}

// MATRIX HELPERS
function ownerCell(owner) {
  const map = { U: { c: OWN_USER, l: "User" }, C: { c: OWN_CUST, l: "Customer" }, D: { c: OWN_DEV, l: "Dev / SI" } };
  return map[owner];
}
function matrixSlide(num, partLabel, title, rows) {
  const s = pres.addSlide();
  lightHeader(s, "Responsibility matrix  ·  " + partLabel, title, num);
  s.addText("R/A = Responsible / Accountable   ·   C/I = Consulted / Informed", { x: 6.6, y: 0.4, w: 5.4, h: 0.3, fontFace: "Calibri", fontSize: 9, italic: true, color: SLATE2, align: "right", margin: 0, valign: "middle" });
  const leg = [
    { col: OWN_DEV, t: "Developer / SI — deploys & maintains", w: 3.05 },
    { col: OWN_CUST, t: "Customer — sponsor IT / security / QA / regulatory", w: 3.65 },
    { col: OWN_USER, t: "User — staff operating the agents", w: 2.9 },
  ];
  let lx = 0.6;
  for (const l of leg) {
    s.addShape(pres.shapes.OVAL, { x: lx, y: 1.36, w: 0.2, h: 0.2, fill: { color: l.col }, line: { type: "none" } });
    s.addText(l.t, { x: lx + 0.26, y: 1.28, w: l.w, h: 0.34, fontFace: "Calibri", fontSize: 9.5, color: SLATE, margin: 0, valign: "middle" });
    lx += l.w + 0.35;
  }
  const hdr = [
    { text: "Responsibility domain", options: { fill: { color: NAVY }, color: WHITE, bold: true, align: "left", fontSize: 11, valign: "middle" } },
    { text: "User", options: { fill: { color: OWN_USER }, color: WHITE, bold: true, align: "center", fontSize: 11, valign: "middle" } },
    { text: "Customer (sponsor)", options: { fill: { color: OWN_CUST }, color: WHITE, bold: true, align: "center", fontSize: 11, valign: "middle" } },
    { text: "Developer / SI", options: { fill: { color: OWN_DEV }, color: WHITE, bold: true, align: "center", fontSize: 11, valign: "middle" } },
  ];
  const body = rows.map((r, idx) => {
    const zebra = idx % 2 === 0 ? CARD : CARDTINT;
    function cell(spec) {
      const owner = spec.who ? ownerCell(spec.who) : null;
      const isRA = spec.r === "R/A";
      return { text: spec.r, options: { fill: { color: isRA && owner ? owner.c : zebra }, color: isRA && owner ? WHITE : SLATE2, bold: isRA, align: "center", fontSize: 10.5, valign: "middle" } };
    }
    return [
      { text: r.d, options: { fill: { color: zebra }, color: NAVY, bold: true, align: "left", fontSize: 10, valign: "middle" } },
      cell(r.u), cell(r.c), cell(r.dev),
    ];
  });
  s.addTable([hdr, ...body], { x: 0.6, y: 1.74, w: 12.13, colW: [4.93, 2.0, 3.2, 2.0], border: { type: "solid", pt: 0.5, color: "FFFFFF" }, rowH: 0.3, valign: "middle", fontFace: "Calibri", margin: [3, 4, 3, 4], autoPage: false });
  footer(s);
  return s;
}
function matrixNoteCards(s, notes, circleColor) {
  let x = 0.6; const cw = 3.92, gx = 0.18, cy = 4.18, ch = 2.55;
  for (const n of notes) {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: cy, w: cw, h: ch, rectRadius: 0.08, fill: { color: CARD }, line: { color: LINE, width: 1 }, shadow: softShadow() });
    iconCircleSync(s, n.ic, x + 0.24, cy + 0.24, 0.6, circleColor, WHITE);
    s.addText(n.h, { x: x + 0.96, y: cy + 0.26, w: cw - 1.1, h: 0.55, fontFace: "Cambria", fontSize: 13.5, bold: true, color: NAVY, valign: "middle", margin: 0 });
    s.addText(n.b, { x: x + 0.26, y: cy + 0.92, w: cw - 0.5, h: ch - 1.1, fontFace: "Calibri", fontSize: n.fs || 9.6, color: SLATE, margin: 0, lineSpacingMultiple: 1.0 });
    x += cw + gx;
  }
}
function slideMatrixA() {
  const rows = [
    { d: "Platform & infrastructure — accounts, network, KMS, edge", u: { r: "—" }, c: { r: "C/I", who: "C" }, dev: { r: "R/A", who: "D" } },
    { d: "Identity & access — IdP, Cognito federation, IAM roles", u: { r: "—" }, c: { r: "R/A", who: "C" }, dev: { r: "C/I", who: "D" } },
    { d: "Security & compliance — GxP / Part 11 program, audits, pen test", u: { r: "C/I", who: "U" }, c: { r: "R/A", who: "C" }, dev: { r: "C/I", who: "D" } },
    { d: "Connectors & data — Veeva/Argus/Medidata integration, data quality, KB content", u: { r: "—" }, c: { r: "R/A", who: "C" }, dev: { r: "R/A", who: "D" } },
  ];
  const s = matrixSlide(7, "Part 1 of 3", "Who owns what — platform, identity, security, data", rows);
  s.addText("Where two parties show R/A, the control only holds if both act — e.g. the SI builds the connector; the sponsor provides credentials, approves scopes, and validates against the live, validated system.", { x: 0.6, y: 3.62, w: 12.13, h: 0.5, fontFace: "Calibri", fontSize: 10.5, italic: true, color: SLATE2, margin: 0 });
  matrixNoteCards(s, [
    { ic: Fa.FaServer, h: "Platform & infra", b: "SI designs & deploys the VPC, KMS, and data plane per the templates; your cloud team approves network & key policy and owns the CMK. Edge hardening is finalized for production." },
    { ic: Fa.FaIdBadge, h: "Identity & access", b: "The IdP is yours — reviewer-role definitions (writer / safety physician / CRA / MLR) are sponsor policy. The SI implements the Cognito claim mapping; you own its accuracy." },
    { ic: Fa.FaDatabase, h: "Connectors & data", b: "No connector points at a live system without your scope approval and a signed pilot SOW. Stale or wrong KB content is a sponsor risk; the SI implements change control." },
  ], NAVY);
  s.addNotes("The centerpiece — walk it slowly. Three owners: User (staff operating the agents), Customer (sponsor IT/security/QA/regulatory), Developer/SI. A filled cell = Responsible/Accountable. Dwell on: Identity & access is sponsor-owned (your IdP, your role policy); Connectors & data is shared R/A — both must act. Every 'Customer R/A' cell is an accountability you cannot delegate to the SI.");
  return s;
}
function slideMatrixB() {
  const rows = [
    { d: "Model & guardrails — Bedrock access, Guardrails tuning, eval & change-control", u: { r: "—" }, c: { r: "R/A", who: "C" }, dev: { r: "R/A", who: "D" } },
    { d: "Validation — CSV/CSA (IQ/OQ/PQ) testing & sign-off", u: { r: "—" }, c: { r: "R/A", who: "C" }, dev: { r: "R/A", who: "D" } },
    { d: "HITL operations — approving consequential actions, reviewer roster", u: { r: "R/A", who: "U" }, c: { r: "R/A", who: "C" }, dev: { r: "C/I", who: "D" } },
    { d: "Reviewer UI / HITL handoff surface — build & operate", u: { r: "—" }, c: { r: "C/I", who: "C" }, dev: { r: "R/A", who: "D" } },
  ];
  const s = matrixSlide(8, "Part 2 of 3", "Who owns what — model, validation, human-in-the-loop", rows);
  s.addText("The human gate is the bright line. The SI builds it; the sponsor staffs it with qualified, correctly-roled reviewers (e.g. a safety physician for causality) — this cannot be delegated to the SI.", { x: 0.6, y: 3.62, w: 12.13, h: 0.5, fontFace: "Calibri", fontSize: 10.5, italic: true, color: SLATE2, margin: 0 });
  matrixNoteCards(s, [
    { ic: Fa.FaSlidersH, h: "Model & guardrails", fs: 9.3, b: "The SI recommends & implements per-agent Guardrail policy, prompt pinning, and the eval harness; your quality, safety & regulatory leadership approve it, and a named reviewer signs off promotions under change control." },
    { ic: Fa.FaClipboardCheck, h: "Validation (CSV/CSA)", b: "Computer-system validation is a production-readiness gate, not optional. The SI supports IQ/OQ/PQ during the engagement; you own the validation lifecycle and final sign-off in your quality system." },
    { ic: Fa.FaUserCheck, h: "HITL operations", b: "Consequential actions are approved by your named, correctly-roled reviewers (regulatory writer / safety physician / CRA / MLR). The SI runs the technical gate; you define what counts as “consequential.”" },
  ], TEAL);
  s.addNotes("Part 2 is where sponsor accountability is heaviest — model governance, validation, and the HITL gate. HITL operations is the row where User lights up R/A: the staff who approve consequential actions are accountable for those approvals. Validation: stress the CSV/CSA gate and that final sign-off is yours. If asked 'can't the SI own all of this?' — no. GxP accountability, what counts as consequential, and reviewer staffing are sponsor responsibilities by regulation and by design.");
  return s;
}
function slideMatrixC() {
  const rows = [
    { d: "Support & monitoring — alarms, dashboards, run-rate ops", u: { r: "—" }, c: { r: "C/I", who: "C" }, dev: { r: "R/A", who: "D" } },
    { d: "Incident & deviation response — detection, containment, reporting", u: { r: "—" }, c: { r: "R/A", who: "C" }, dev: { r: "R/A", who: "D" } },
    { d: "Change management — prompt / model upgrades, production promotion", u: { r: "C/I", who: "U" }, c: { r: "R/A", who: "C" }, dev: { r: "R/A", who: "D" } },
    { d: "Training & SOPs — staff enablement, the bright line, acceptable use", u: { r: "R/A", who: "U" }, c: { r: "R/A", who: "C" }, dev: { r: "C/I", who: "D" } },
  ];
  const s = matrixSlide(9, "Part 3 of 3", "Who owns what — operations, change, training", rows);
  s.addText("Operationally: the SI builds and runs the technical controls; the sponsor makes every regulated determination — deviation/CAPA, production sign-off, and SOP enforcement under its quality system.", { x: 0.6, y: 3.62, w: 12.13, h: 0.5, fontFace: "Calibri", fontSize: 10.5, italic: true, color: SLATE2, margin: 0 });
  matrixNoteCards(s, [
    { ic: Fa.FaBell, h: "Support & monitoring", b: "Alarm thresholds, pager routing, and retention windows are sponsor-owned; the SI builds the dashboards and runs managed-service operations against your SLAs." },
    { ic: Fa.FaExclamationTriangle, h: "Incident & deviation", fs: 9.3, b: "The SI executes the runbook, produces audit evidence, and notifies you fast; you make the regulated determination — deviation, CAPA, and any reportability to authorities — under your quality system." },
    { ic: Fa.FaChalkboardTeacher, h: "Change & training", b: "No prompt, model, or tool-grant change reaches production without your sign-off under change control. You own the SOPs and train staff on what the agent does and does not decide; the SI supplies capability docs." },
  ], AMBER);
  s.addNotes("Part 3 closes on day-to-day operations, change, and people. Throughline of all three matrix slides: the SI builds and operates the technical controls; the sponsor makes every regulated determination and owns the quality system. Incident & deviation: the SI contains and produces evidence; the reportability decision is yours. Change management: nothing reaches production without your sign-off — exactly the control a CISO/QA head wants.");
  return s;
}

// SLIDE 10 — BACKLOG
async function slideBacklog() {
  const s = pres.addSlide();
  lightHeader(s, "The honest backlog", "What is still to be done", 10);
  const items = [
    { ic: Fa.FaPlug, h: "Live connectors", b: "Validated adapters for live Veeva (RIM/Vault/CRM), Argus/Veeva Safety, Medidata, and QMS (TrackWise)." },
    { ic: Fa.FaClipboardCheck, h: "CSV / CSA package", b: "Executed IQ/OQ/PQ validation and the traceability matrix under the sponsor's quality system." },
    { ic: Fa.FaDatabase, h: "KB ingestion pipeline", b: "Bedrock Knowledge Base ingestion IaC built out from the stub per corpus (guidance, label, SOPs), grounding wired in." },
    { ic: Fa.FaNetworkWired, h: "Edge + observability IaC", b: "CloudFront / WAF hardening and CloudWatch alarms + dashboards authored per environment." },
    { ic: Fa.FaFileContract, h: "Cedar / OPA policy export", b: "Export the gateway authorization model to a standard policy engine for external review & reuse." },
    { ic: Fa.FaUserShield, h: "Penetration test", b: "Independent pen test of the deployed surface — a production-readiness gate." },
    { ic: Fa.FaDesktop, h: "Reviewer UI", b: "The HITL approve/reject surface that authenticates the reviewer and binds the e-signature into the record." },
    { ic: Fa.FaClipboardList, h: "Production-readiness review", b: "Full security & quality review, IdP integration tested, and sponsor acceptance sign-off." },
  ];
  let i = 0; const cw = 5.92, ch = 1.13, gx = 0.28, gy = 0.16, x0 = 0.6, y0 = 1.5;
  for (const it of items) {
    const col = i % 2, row = Math.floor(i / 2);
    const cx = x0 + col * (cw + gx), cyy = y0 + row * (ch + gy);
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: cx, y: cyy, w: cw, h: ch, rectRadius: 0.07, fill: { color: CARD }, line: { color: LINE, width: 1 }, shadow: softShadow() });
    await iconCircle(s, it.ic, cx + 0.2, cyy + 0.26, 0.6, NAVY, WHITE);
    s.addText(it.h, { x: cx + 0.95, y: cyy + 0.13, w: cw - 1.1, h: 0.36, fontFace: "Cambria", fontSize: 12.5, bold: true, color: NAVY, margin: 0, valign: "middle" });
    s.addText(it.b, { x: cx + 0.95, y: cyy + 0.47, w: cw - 1.12, h: 0.6, fontFace: "Calibri", fontSize: 9.5, color: SLATE, margin: 0, lineSpacingMultiple: 0.95 });
    i++;
  }
  footer(s);
  s.addNotes("The shortfalls slide turned into a plan — same items, now with an owner and a place in the sequence. Three streams: integration (live connectors, reviewer UI) is the bulk of the engagement, gated on your systems; infrastructure-as-code (edge, observability, KB ingestion); and assurance (CSV/CSA validation, pen test, production-readiness review) which converts 'Deployable' to 'Production-ready.' Cedar/OPA export lets your own security team review the authorization model in a standard policy language.");
}

// SLIDE 11 — PATH
async function slidePath() {
  const s = pres.addSlide();
  lightHeader(s, "Recommended adoption path", "Land low-risk, prove the controls, then expand", 11);
  const phases = [
    { n: "1", col: TEAL, t: "Pilot — land here", sub: "Lowest decision-risk, highest visibility", agents: "01 Regulatory Writing · 02 Pharmacovigilance (live path) · 03 Trial Ops/TMF · 08 Medical Affairs", goal: "Prove the gateway, PHI masking, audit trail, and HITL gate in production. Measure cycle-time and reviewer throughput." },
    { n: "2", col: NAVY, t: "Expand — on evidence", sub: "Higher-value, higher-governance", agents: "05 Quality / CAPA · 06 Protocol Design", goal: "Add agents that touch reportability and study design — only after eval, grounding, and audit are proven in production." },
    { n: "3", col: AMBER, t: "Operate — at scale", sub: "Managed service & continuous assurance", agents: "Full suite under change control · de-identified-RWD agents 04 / 07 · model-drift monitoring · annual pen test", goal: "Steady-state operations with named reviewers, alarms, and a production-readiness review behind each promotion." },
  ];
  let x = 0.6; const cw = 3.93, gx = 0.18, cy = 1.6, ch = 3.55;
  for (let i = 0; i < phases.length; i++) {
    const p = phases[i];
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: cy, w: cw, h: ch, rectRadius: 0.1, fill: { color: CARD }, line: { color: p.col, width: 1.5 }, shadow: softShadow() });
    s.addShape(pres.shapes.OVAL, { x: x + 0.3, y: cy + 0.3, w: 0.78, h: 0.78, fill: { color: p.col }, line: { type: "none" } });
    s.addText(p.n, { x: x + 0.3, y: cy + 0.3, w: 0.78, h: 0.78, align: "center", valign: "middle", fontFace: "Cambria", fontSize: 30, bold: true, color: WHITE, margin: 0 });
    s.addText(p.t, { x: x + 1.22, y: cy + 0.33, w: cw - 1.4, h: 0.4, fontFace: "Cambria", fontSize: 16.5, bold: true, color: NAVY, margin: 0 });
    s.addText(p.sub, { x: x + 1.22, y: cy + 0.72, w: cw - 1.4, h: 0.36, fontFace: "Calibri", fontSize: 10.5, italic: true, color: p.col, margin: 0 });
    s.addText("AGENTS", { x: x + 0.3, y: cy + 1.32, w: cw - 0.6, h: 0.24, fontFace: "Calibri", fontSize: 8.5, bold: true, color: SLATE2, charSpacing: 1.5, margin: 0 });
    s.addText(p.agents, { x: x + 0.3, y: cy + 1.56, w: cw - 0.6, h: 0.95, fontFace: "Calibri", fontSize: 10.5, bold: true, color: NAVY, margin: 0, lineSpacingMultiple: 1.0 });
    s.addText("GOAL / PHASE GATE", { x: x + 0.3, y: cy + 2.5, w: cw - 0.6, h: 0.24, fontFace: "Calibri", fontSize: 8.5, bold: true, color: SLATE2, charSpacing: 1.5, margin: 0 });
    s.addText(p.goal, { x: x + 0.3, y: cy + 2.74, w: cw - 0.6, h: 0.75, fontFace: "Calibri", fontSize: 9.5, color: SLATE, margin: 0, lineSpacingMultiple: 1.0 });
    if (i < phases.length - 1) s.addShape(pres.shapes.RIGHT_TRIANGLE, { x: x + cw + 0.005, y: cy + ch / 2 - 0.16, w: 0.17, h: 0.32, fill: { color: SLATE2 }, line: { type: "none" }, rotate: 90 });
    x += cw + gx;
  }
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 5.42, w: 12.13, h: 1.32, rectRadius: 0.08, fill: { color: NAVY }, line: { type: "none" } });
  await iconCircle(s, Fa.FaFlagCheckered, 0.82, 5.66, 0.84, TEAL, WHITE);
  s.addText([
    { text: "Phase gates:  ", options: { bold: true, color: TEALLT, fontSize: 13 } },
    { text: "Each phase advances only when the prior clears its gate — clean audit trail, HITL gate exercised on real approvals, measured cycle-time, and a security/quality sign-off. Best demo entry point: Agent 02 (Pharmacovigilance) — the only agent with a live Bedrock + real-connector path you can run end-to-end. Safest document start: Agent 01.", options: { color: WHITE, fontSize: 12 } },
  ], { x: 1.82, y: 5.56, w: 10.75, h: 1.05, fontFace: "Calibri", valign: "middle", margin: 0, lineSpacingMultiple: 1.0 });
  footer(s);
  s.addNotes("The adoption path de-risks the decision: you are not betting on eight agents at once. Land with the four document- and case-centric agents (01/02/03/08) and prove the gateway, PHI masking, audit, and HITL gate. Agent 02 is the best live demo — it ships a real Bedrock + connector path. Only after Phase 1 clears its gate do you add reportability/design agents (05/06), then the de-identified-RWD agents (04/07). Advancement is earned with evidence, not scheduled by date.");
}

// SLIDE 12 — DECISION
async function slideDecision() {
  const s = pres.addSlide();
  s.background = { color: NAVYDK };
  s.addShape(pres.shapes.OVAL, { x: 11.0, y: -1.2, w: 4.0, h: 4.0, fill: { color: NAVY2 }, line: { type: "none" } });
  s.addText("DECISION SUMMARY", { x: 0.7, y: 0.5, w: 10, h: 0.4, fontFace: "Calibri", fontSize: 13, bold: true, color: TEAL, charSpacing: 2, margin: 0 });
  s.addText("Go / no-go criteria", { x: 0.7, y: 0.86, w: 12, h: 0.7, fontFace: "Cambria", fontSize: 29, bold: true, color: WHITE, margin: 0 });
  const gx = 0.7, gw = 5.85, gy = 1.85, gh = 3.5;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: gx, y: gy, w: gw, h: gh, rectRadius: 0.1, fill: { color: NAVY2 }, line: { color: GREEN, width: 1.5 }, shadow: shadow() });
  await iconCircle(s, Fa.FaCheckCircle, gx + 0.28, gy + 0.28, 0.66, GREEN, WHITE);
  s.addText("GO if you can commit to…", { x: gx + 1.06, y: gy + 0.32, w: gw - 1.2, h: 0.58, fontFace: "Cambria", fontSize: 17, bold: true, color: WHITE, valign: "middle", margin: 0 });
  s.addText([
    { text: "A funded SI-led engagement, not a product purchase", options: { bullet: true, breakLine: true } },
    { text: "Owning the GxP / Part 11 quality program, IdP, and reviewer roster", options: { bullet: true, breakLine: true } },
    { text: "A pilot scoped to Agents 01 / 02 / 03 / 08 with phase gates", options: { bullet: true, breakLine: true } },
    { text: "Budget for CSV/CSA validation + a pen test before go-live", options: { bullet: true, breakLine: true } },
    { text: "Validating Bedrock cost & clinical accuracy against your own data", options: { bullet: true } },
  ], { x: gx + 0.32, y: gy + 1.12, w: gw - 0.6, h: gh - 1.3, fontFace: "Calibri", fontSize: 12, color: ICE, margin: 0, paraSpaceAfter: 7, lineSpacingMultiple: 1.0 });
  const nx = 6.88, nw = 5.85;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: nx, y: gy, w: nw, h: gh, rectRadius: 0.1, fill: { color: NAVY2 }, line: { color: RED, width: 1.5 }, shadow: shadow() });
  await iconCircle(s, Fa.FaTimesCircle, nx + 0.28, gy + 0.28, 0.66, RED, WHITE);
  s.addText("NO-GO / wait if…", { x: nx + 1.06, y: gy + 0.32, w: nw - 1.2, h: 0.58, fontFace: "Cambria", fontSize: 17, bold: true, color: WHITE, valign: "middle", margin: 0 });
  s.addText([
    { text: "You need a certified, turnkey product to switch on now", options: { bullet: true, breakLine: true } },
    { text: "There is no budget or partner for SI delivery & maintenance", options: { bullet: true, breakLine: true } },
    { text: "Your IdP cannot express the reviewer roles and there is no plan to fix it", options: { bullet: true, breakLine: true } },
    { text: "You expect the vendor to assume GxP / Part 11 accountability", options: { bullet: true, breakLine: true } },
    { text: "You cannot staff qualified HITL reviewers (e.g. a safety physician)", options: { bullet: true } },
  ], { x: nx + 0.32, y: gy + 1.12, w: nw - 0.6, h: gh - 1.3, fontFace: "Calibri", fontSize: 12, color: ICE, margin: 0, paraSpaceAfter: 7, lineSpacingMultiple: 1.0 });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.7, y: 5.62, w: 12.03, h: 1.28, rectRadius: 0.08, fill: { color: TEAL }, line: { type: "none" } });
  s.addText([
    { text: "Recommendation:  ", options: { bold: true, color: NAVYDK, fontSize: 15 } },
    { text: "Approve a funded Phase-1 pilot on Agents 01 / 02 / 03 / 08. It compresses an SI-led build with a governance spine your CISO and QA/regulatory leadership can stand behind — while you keep GxP / Part 11 accountability and prove the controls in production before expanding.", options: { color: NAVYDK, fontSize: 13 } },
  ], { x: 1.05, y: 5.72, w: 11.3, h: 1.06, fontFace: "Calibri", valign: "middle", margin: 0, lineSpacingMultiple: 1.0 });
  s.addNotes("Close decisively. Two columns so the board sees a conditional yes with clear criteria. GO if leadership can commit to: a funded SI engagement, owning the quality program/IdP/reviewers, a phased pilot, budget for CSV/CSA + pen test, and validating Bedrock cost/accuracy. NO-GO if any disqualifier holds — especially expecting a turnkey product or expecting the vendor to take GxP accountability. Then ask for the specific decision: approval to fund a Phase-1 pilot on 01/02/03/08. Smallest viable yes: a single-agent pilot on Agent 02 (live path).");
}

async function main() {
  const warm = [
    [Fa.FaServer, "FFFFFF"], [Fa.FaIdBadge, "FFFFFF"], [Fa.FaDatabase, "FFFFFF"],
    [Fa.FaSlidersH, "FFFFFF"], [Fa.FaClipboardCheck, "FFFFFF"], [Fa.FaUserCheck, "FFFFFF"],
    [Fa.FaBell, "FFFFFF"], [Fa.FaExclamationTriangle, "FFFFFF"], [Fa.FaChalkboardTeacher, "FFFFFF"],
  ];
  for (const [c, col] of warm) await icon(c, col);
  await slideTitle();
  await slideBLUF();
  await slideMaturity();
  await slideWhyYes();
  await slideShortfalls();
  await slideQuestions();
  slideMatrixA();
  slideMatrixB();
  slideMatrixC();
  await slideBacklog();
  await slidePath();
  await slideDecision();
  await pres.writeFile({ fileName: process.argv[2] || (__dirname + "/HCLS-CIO-Adoption-Review.pptx") });
  console.log("WROTE CIO deck");
}
main().catch((e) => { console.error(e); process.exit(1); });
