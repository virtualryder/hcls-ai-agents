/* HCLS AI Agent Suite — Go-to-Market deck generator
 * ONE generator drives all 9 decks (8 agents + suite overview) from per-agent
 * content objects, using a consistent professional layout (navy title /
 * navy stat hook / light issue+cost / light governed pipeline / light AWS
 * architecture+traffic flow / navy proof+payback).
 *
 * Audience: CIO / CISO (CSO) / Director of Architecture. Board-defensible
 * metrics, source-class tags on-slide, explicit cost-of-doing-nothing.
 * Every figure traces to gtm/HCLS-DECK-SOURCES.md.
 *
 * Run:  node decks/build-agent-decks.js
 */
const pptxgen = require("pptxgenjs");

// ============================================================ PALETTE / FONTS
const SQUID   = "232F3E"; // deep navy — dark slide bg, titles
const SQUID2  = "2E3B4E"; // lighter navy (stat cards on dark)
const SQUID3  = "1B2530"; // deeper navy for takeaway bars
const ORANGE  = "FF9900"; // amber — accents, edge bar, stat numbers
const ORANGED = "E88A00"; // darker orange
const TEAL    = "16A085"; // secondary cards / positive flow
const RED     = "C0392B"; // HUMAN-GATE only
const GRAYBG  = "F2F3F4"; // light content background
const CARD    = "FFFFFF";
const WHITE   = "FFFFFF";
const INK     = "232F3E"; // body text on light
const MUTED   = "6B7785"; // muted gray labels / taglines
const MUTEDLT = "9AA7B4"; // muted on dark
const LINE    = "D5DBE1";
// AWS architecture category colors
const C_COMPUTE = "FF9900"; // compute orange
const C_INTEG   = "E7157B"; // integration magenta
const C_STORAGE = "7AA116"; // storage olive/green
const C_MODEL   = "16A085"; // model/db teal
const C_NET     = "8C4FFF"; // networking purple

const F_BOLD = "Arial";
const F_REG  = "Calibri";
const F_TAG  = "Cambria"; // italic taglines

const EDGE = 0.14; // orange left-edge bar width (inches) — AWS-brand styling
const PW = 13.333, PH = 7.5;

const sh   = () => ({ type: "outer", color: "000000", blur: 7, offset: 3, angle: 90, opacity: 0.16 });
const shsm = () => ({ type: "outer", color: "000000", blur: 5, offset: 2, angle: 90, opacity: 0.10 });

// ------------------------------------------------------------ primitives
function edgeBar(P, s) {
  s.addShape(P.shapes.RECTANGLE, { x: 0, y: 0, w: EDGE, h: PH, fill: { color: ORANGE }, line: { type: "none" } });
}
function footer(P, s, text, onDark) {
  s.addText(text || "HCLS AI Agent Suite · Governed Agentic AI on AWS", {
    x: 0.55, y: PH - 0.42, w: PW - 1.1, h: 0.3, fontFace: F_REG, fontSize: 9.5,
    color: onDark ? MUTEDLT : MUTED, align: "left", valign: "middle", margin: 0,
  });
}
function tag(P, s, x, y, txt, onDark) {
  if (!txt) return;
  const w = Math.min(4.4, 0.10 + txt.length * 0.062);
  s.addText(txt, {
    x, y, w, h: 0.22, fontFace: F_REG, fontSize: 7.5, italic: true,
    color: onDark ? MUTEDLT : MUTED, align: "left", valign: "middle", margin: 0,
  });
}

// ============================================================ SLIDE 1 — TITLE
function slideTitle(P, d) {
  const s = P.addSlide();
  s.background = { color: SQUID };
  edgeBar(P, s);
  s.addText(d.name, { x: 0.85, y: 1.7, w: 11.6, h: 1.9, fontFace: F_BOLD, fontSize: 40, bold: true, color: WHITE, align: "left", valign: "middle", lineSpacingMultiple: 1.02, margin: 0 });
  s.addText("A Governed Agentic AI Reference Architecture for Life Sciences", { x: 0.87, y: 3.75, w: 11.4, h: 0.6, fontFace: F_BOLD, fontSize: 20, bold: true, color: ORANGE, align: "left", valign: "middle", margin: 0 });
  s.addText(`Agent ${d.num} of 8  ·  ${d.tagline}`, { x: 0.88, y: 4.55, w: 11.4, h: 0.5, fontFace: F_TAG, fontSize: 15, italic: true, color: MUTEDLT, align: "left", valign: "middle", margin: 0 });
  s.addText("HCLS AI Agent Suite", { x: 0.88, y: 5.7, w: 11.4, h: 0.35, fontFace: F_BOLD, fontSize: 14, bold: true, color: WHITE, align: "left", valign: "middle", margin: 0 });
  s.addText("HCLS AI Agent Suite  ·  Built on AWS  ·  June 2026", { x: 0.88, y: 6.05, w: 11.4, h: 0.3, fontFace: F_REG, fontSize: 11, color: MUTEDLT, align: "left", valign: "middle", margin: 0 });
  s.addNotes(d.notes.s1);
}

// ============================================================ SLIDE 2 — HOOK
function slideHook(P, d) {
  const s = P.addSlide();
  s.background = { color: SQUID };
  edgeBar(P, s);
  s.addText(d.hero, { x: 0.85, y: 0.85, w: 11.7, h: 1.15, fontFace: F_BOLD, fontSize: 40, bold: true, color: WHITE, align: "left", valign: "middle", charSpacing: 1, margin: 0, lineSpacingMultiple: 1.0 });
  s.addText(d.name, { x: 0.87, y: 2.0, w: 11.6, h: 0.55, fontFace: F_BOLD, fontSize: 22, bold: true, color: ORANGE, align: "left", valign: "middle", margin: 0 });
  s.addText(d.valueProp, { x: 0.88, y: 2.65, w: 11.3, h: 0.85, fontFace: F_TAG, fontSize: 15, italic: true, color: MUTEDLT, align: "left", valign: "top", lineSpacingMultiple: 1.05, margin: 0 });
  const cw = 3.62, gap = 0.32, x0 = 0.85, cy = 3.9, ch = 2.05;
  d.hookStats.forEach((st, i) => {
    const x = x0 + i * (cw + gap);
    const wraps = st.big.length > 9;
    s.addShape(P.shapes.RECTANGLE, { x, y: cy, w: cw, h: ch, fill: { color: SQUID2 }, line: { color: "3A485A", width: 1 } });
    s.addText(st.big, { x: x + 0.28, y: cy + 0.18, w: cw - 0.5, h: wraps ? 0.98 : 0.8, fontFace: F_BOLD, fontSize: wraps ? 26 : 33, bold: true, color: ORANGE, align: "left", valign: "top", lineSpacingMultiple: 0.95, margin: 0 });
    s.addText(st.label, { x: x + 0.3, y: cy + 1.12, w: cw - 0.55, h: 0.6, fontFace: F_REG, fontSize: 12, color: "C9D2DC", align: "left", valign: "top", lineSpacingMultiple: 1.0, margin: 0 });
    tag(P, s, x + 0.3, cy + ch - 0.26, st.tag, true);
  });
  footer(P, s, "HCLS AI Agent Suite  ·  Built on AWS  ·  June 2026", true);
  s.addNotes(d.notes.s2);
}

// ============================================================ SLIDE 3 — ISSUE + COST
function slideIssueCost(P, d) {
  const s = P.addSlide();
  s.background = { color: GRAYBG };
  edgeBar(P, s);
  s.addText("The Issue & The Cost of Doing Nothing", { x: 0.78, y: 0.4, w: 12, h: 0.8, fontFace: F_BOLD, fontSize: 33, bold: true, color: INK, align: "left", valign: "middle", margin: 0 });
  const cw = 5.78, x0 = 0.78, cy = 1.45, ch = 3.7, gap = 0.45;
  s.addShape(P.shapes.RECTANGLE, { x: x0, y: cy, w: cw, h: ch, fill: { color: CARD }, line: { type: "none" }, shadow: sh() });
  s.addShape(P.shapes.RECTANGLE, { x: x0, y: cy, w: 0.08, h: ch, fill: { color: SQUID }, line: { type: "none" } });
  s.addText("THE ISSUE", { x: x0 + 0.35, y: cy + 0.22, w: cw - 0.7, h: 0.45, fontFace: F_BOLD, fontSize: 16, bold: true, color: SQUID, charSpacing: 1, align: "left", valign: "middle", margin: 0 });
  s.addText(d.issueBullets.map((b) => ({ text: b, options: { bullet: { code: "2022" }, breakLine: true, paraSpaceAfter: 9, color: INK } })), { x: x0 + 0.4, y: cy + 0.78, w: cw - 0.75, h: ch - 1.0, fontFace: F_REG, fontSize: 13, color: INK, align: "left", valign: "top", lineSpacingMultiple: 1.02, margin: 0 });
  const x1 = x0 + cw + gap;
  s.addShape(P.shapes.RECTANGLE, { x: x1, y: cy, w: cw, h: ch, fill: { color: CARD }, line: { type: "none" }, shadow: sh() });
  s.addShape(P.shapes.RECTANGLE, { x: x1, y: cy, w: 0.08, h: ch, fill: { color: ORANGE }, line: { type: "none" } });
  s.addText("THE COST OF DOING NOTHING", { x: x1 + 0.35, y: cy + 0.22, w: cw - 0.7, h: 0.45, fontFace: F_BOLD, fontSize: 16, bold: true, color: ORANGED, charSpacing: 1, align: "left", valign: "middle", margin: 0 });
  s.addText(d.costBig, { x: x1 + 0.34, y: cy + 0.66, w: cw - 0.7, h: 0.78, fontFace: F_BOLD, fontSize: 34, bold: true, color: ORANGE, align: "left", valign: "middle", margin: 0 });
  s.addText(d.costMath, { x: x1 + 0.38, y: cy + 1.5, w: cw - 0.78, h: 0.95, fontFace: F_REG, fontSize: 11, italic: true, color: MUTED, align: "left", valign: "top", lineSpacingMultiple: 1.02, margin: 0 });
  s.addText(d.costRisks.map((b) => ({ text: b, options: { bullet: { code: "2022" }, breakLine: true, paraSpaceAfter: 7, color: INK } })), { x: x1 + 0.4, y: cy + 2.5, w: cw - 0.78, h: ch - 2.7, fontFace: F_REG, fontSize: 12, color: INK, align: "left", valign: "top", lineSpacingMultiple: 1.0, margin: 0 });
  tag(P, s, x1 + 0.36, cy + ch - 0.3, d.costTag, false);
  const by = cy + ch + 0.35, bh = 1.0;
  s.addShape(P.shapes.RECTANGLE, { x: x0, y: by, w: 11.78, h: bh, fill: { color: SQUID }, line: { type: "none" } });
  s.addText([
    { text: "The design line:  ", options: { bold: true, color: ORANGE } },
    { text: d.brightLine, options: { color: WHITE } },
  ], { x: x0 + 0.4, y: by, w: 11.0, h: bh, fontFace: F_REG, fontSize: 14.5, align: "left", valign: "middle", lineSpacingMultiple: 1.04, margin: 0 });
  footer(P, s, null, false);
  s.addNotes(d.notes.s3);
}

// ============================================================ SLIDE 4 — GOVERNED PIPELINE
function slidePipeline(P, d) {
  const s = P.addSlide();
  s.background = { color: GRAYBG };
  edgeBar(P, s);
  s.addText("How We Solve It — A Governed Pipeline", { x: 0.78, y: 0.38, w: 12, h: 0.7, fontFace: F_BOLD, fontSize: 31, bold: true, color: INK, align: "left", valign: "middle", margin: 0 });
  s.addText(d.pipelineTagline, { x: 0.8, y: 1.06, w: 12.0, h: 0.6, fontFace: F_TAG, fontSize: 14, italic: true, color: MUTED, align: "left", valign: "top", lineSpacingMultiple: 1.02, margin: 0 });
  const steps = d.pipeline;
  const n = steps.length, x0 = 0.78, top = 2.0, gap = 0.22, totalW = 11.78;
  const bw = (totalW - gap * (n - 1)) / n, bh = 1.7;
  steps.forEach((st, i) => {
    const x = x0 + i * (bw + gap);
    const fill = st.kind === "gate" ? RED : (st.kind === "audit" ? SQUID : TEAL);
    s.addShape(P.shapes.RECTANGLE, { x, y: top, w: bw, h: bh, fill: { color: fill }, line: { type: "none" }, shadow: shsm() });
    s.addText(String(st.n), { x: x + 0.18, y: top + 0.12, w: 0.6, h: 0.5, fontFace: F_BOLD, fontSize: 22, bold: true, color: ORANGE, align: "left", valign: "middle", margin: 0 });
    s.addText(st.title, { x: x + 0.18, y: top + 0.58, w: bw - 0.36, h: 0.6, fontFace: F_BOLD, fontSize: 12.5, bold: true, color: WHITE, align: "left", valign: "top", lineSpacingMultiple: 0.98, margin: 0 });
    s.addText(st.sub, { x: x + 0.18, y: top + 1.16, w: bw - 0.34, h: 0.5, fontFace: F_REG, fontSize: 9, color: "EAF0F3", align: "left", valign: "top", lineSpacingMultiple: 0.96, margin: 0 });
    if (i < n - 1) s.addText("→", { x: x + bw - 0.05, y: top + bh / 2 - 0.22, w: gap + 0.1, h: 0.44, fontFace: F_BOLD, fontSize: 15, bold: true, color: MUTED, align: "center", valign: "middle", margin: 0 });
  });
  const fy = top + bh + 0.5, fh = 1.6, fw = 3.78, fgap = 0.22;
  d.pipelineCards.forEach((c, i) => {
    const x = x0 + i * (fw + fgap);
    s.addShape(P.shapes.RECTANGLE, { x, y: fy, w: fw, h: fh, fill: { color: CARD }, line: { type: "none" }, shadow: sh() });
    s.addShape(P.shapes.RECTANGLE, { x, y: fy, w: 0.07, h: fh, fill: { color: ORANGE }, line: { type: "none" } });
    s.addText(c.title, { x: x + 0.3, y: fy + 0.2, w: fw - 0.55, h: 0.55, fontFace: F_BOLD, fontSize: 14, bold: true, color: INK, align: "left", valign: "middle", margin: 0 });
    s.addText(c.body, { x: x + 0.32, y: fy + 0.74, w: fw - 0.6, h: fh - 0.9, fontFace: F_REG, fontSize: 11, color: MUTED, align: "left", valign: "top", lineSpacingMultiple: 1.0, margin: 0 });
  });
  footer(P, s, null, false);
  s.addNotes(d.notes.s4);
}

// ============================================================ SLIDE 5 — AWS ARCHITECTURE & TRAFFIC FLOW
function archBox(P, s, x, y, w, h, title, sub, color, opts = {}) {
  s.addShape(P.shapes.RECTANGLE, { x, y, w, h, fill: { color }, line: { type: "none" } });
  s.addText([
    { text: title, options: { bold: true, breakLine: !!sub, fontSize: opts.tf || 9.5, color: WHITE } },
    ...(sub ? [{ text: sub, options: { fontSize: opts.sf || 8, color: "F0F4F6" } }] : []),
  ], { x: x + 0.1, y: y + 0.03, w: w - 0.18, h: h - 0.06, fontFace: F_REG, align: "left", valign: "middle", lineSpacingMultiple: 0.94, margin: 0 });
}
function flowNum(P, s, x, y, num) {
  const d = 0.32;
  s.addShape(P.shapes.OVAL, { x, y, w: d, h: d, fill: { color: ORANGE }, line: { color: WHITE, width: 1.5 } });
  s.addText(String(num), { x, y, w: d, h: d, fontFace: F_BOLD, fontSize: 11, bold: true, color: SQUID, align: "center", valign: "middle", margin: 0 });
}
function dashedGroup(P, s, x, y, w, h, label, labelColor) {
  s.addShape(P.shapes.RECTANGLE, { x, y, w, h, fill: { type: "none" }, line: { color: "9AA7B4", width: 1, dashType: "dash" } });
  s.addText(label, { x: x + 0.12, y: y + 0.06, w: w - 0.24, h: 0.28, fontFace: F_BOLD, fontSize: 9, bold: true, color: labelColor || MUTED, charSpacing: 0.5, align: "left", valign: "middle", margin: 0 });
}
function slideArch(P, d) {
  const s = P.addSlide();
  s.background = { color: WHITE };
  edgeBar(P, s);
  s.addText(d.archTitle || "AWS Architecture & Traffic Flow", { x: 0.7, y: 0.2, w: 12.2, h: 0.55, fontFace: F_BOLD, fontSize: 29, bold: true, color: INK, align: "left", valign: "middle", margin: 0 });

  const lgX = 0.6, lgY = 0.95, lgW = 2.55, lgH = 4.55;
  dashedGroup(P, s, lgX, lgY, lgW, lgH, "ORG / EXTERNAL", MUTED);
  const lbx = lgX + 0.13, lbw = lgW - 0.26;
  archBox(P, s, lbx, lgY + 0.42, lbw, 0.6, d.arch.users, "", SQUID, { tf: 9 });
  archBox(P, s, lbx, lgY + 1.18, lbw, 0.6, "IdP — Okta / Azure AD / PingID", "SAML/OIDC + MFA", SQUID, { tf: 8.5, sf: 7.5 });
  archBox(P, s, lbx, lgY + 1.94, lbw, 0.7, d.arch.sor, "validated systems · PrivateLink / Direct Connect", SQUID, { tf: 8.5, sf: 7 });
  archBox(P, s, lbx, lgY + 2.8, lbw, 0.6, d.arch.ext, "", SQUID, { tf: 8.5 });
  s.addText("PrivateLink / Direct Connect", { x: lbx, y: lgY + 3.5, w: lbw, h: 0.25, fontFace: F_REG, fontSize: 7.5, italic: true, color: MUTED, align: "left", valign: "middle", margin: 0 });

  const cX = 3.35, cY = 0.95, cW = 9.35, cH = 5.1;
  dashedGroup(P, s, cX, cY, cW, cH, "AWS CLOUD — PER-CUSTOMER VPC (dedicated, validated account per customer)", SQUID);

  const e1x = cX + 0.18, e1y = cY + 0.48, e1w = 2.7, e1h = 1.95;
  dashedGroup(P, s, e1x, e1y, e1w, e1h, "EDGE / PUBLIC SUBNET", C_NET);
  archBox(P, s, e1x + 0.12, e1y + 0.4, e1w - 0.24, 0.44, "CloudFront + WAF", "", C_NET, { tf: 9 });
  archBox(P, s, e1x + 0.12, e1y + 0.92, e1w - 0.24, 0.44, "ALB — TLS 1.3 + Cognito auth", "", C_NET, { tf: 8 });
  archBox(P, s, e1x + 0.12, e1y + 1.44, e1w - 0.24, 0.44, "Amazon Cognito — SAML→JWT", "", C_NET, { tf: 8 });

  const e2x = e1x + e1w + 0.22, e2y = cY + 0.48, e2w = 3.05, e2h = 1.95;
  dashedGroup(P, s, e2x, e2y, e2w, e2h, "PRIVATE SUBNET — AGENTCORE / FARGATE", C_COMPUTE);
  const rb = d.arch.runtime;
  const rbh = (e2h - 0.42) / rb.length;
  rb.forEach((b, i) => archBox(P, s, e2x + 0.12, e2y + 0.4 + i * rbh, e2w - 0.24, rbh - 0.07, b.t, b.s || "", b.color || C_COMPUTE, { tf: 8, sf: 6.8 }));

  const e3x = e2x + e2w + 0.22, e3y = cY + 0.48, e3w = 2.55, e3h = 1.95;
  dashedGroup(P, s, e3x, e3y, e3w, e3h, "MODEL LAYER — VPC ENDPOINT", C_MODEL);
  archBox(P, s, e3x + 0.12, e3y + 0.42, e3w - 0.24, 0.62, "Amazon Bedrock", "Claude (analysis + draft)", C_MODEL, { tf: 9, sf: 7.5 });
  archBox(P, s, e3x + 0.12, e3y + 1.14, e3w - 0.24, 0.62, "Bedrock Guardrails", "PHI + content filters (mandatory)", C_MODEL, { tf: 9, sf: 7 });

  const dtx = cX + 0.18, dty = cY + 2.6, dtw = cW - 0.36, dth = 1.25;
  dashedGroup(P, s, dtx, dty, dtw, dth, "DATA TIER — KMS CMK-ENCRYPTED", C_STORAGE);
  const dtiles = d.arch.data, dtn = dtiles.length, dtgap = 0.18;
  const dtbw = (dtw - 0.24 - dtgap * (dtn - 1)) / dtn;
  dtiles.forEach((b, i) => archBox(P, s, dtx + 0.12 + i * (dtbw + dtgap), dty + 0.42, dtbw, 0.68, b.t, b.s || "", b.color || C_STORAGE, { tf: 8.5, sf: 7 }));

  const sox = cX + 0.18, soy = cY + 4.02, sow = cW - 0.36, soh = 0.78;
  s.addShape(P.shapes.RECTANGLE, { x: sox, y: soy, w: sow, h: soh, fill: { color: SQUID3 }, line: { type: "none" } });
  s.addText([
    { text: "SECURITY & OPS:  ", options: { bold: true, color: ORANGE } },
    { text: "KMS CMK per data class  ·  IAM least privilege  ·  CloudWatch  ·  X-Ray  ·  CloudTrail  ·  Security Hub + Config (21 CFR Part 11 audit)", options: { color: "E6ECF1" } },
  ], { x: sox + 0.22, y: soy, w: sow - 0.4, h: soh, fontFace: F_REG, fontSize: 10, align: "left", valign: "middle", margin: 0 });

  flowNum(P, s, lgX + lgW - 0.04, lgY + 0.5, 1);
  flowNum(P, s, lgX + lgW - 0.04, lgY + 1.28, 2);
  flowNum(P, s, e1x + e1w - 0.02, e1y + 0.95, 3);
  flowNum(P, s, lgX + lgW - 0.04, lgY + 2.1, 4);
  flowNum(P, s, e2x + e2w / 2 - 0.16, e2y + e2h - 0.04, 5);
  flowNum(P, s, e3x - 0.2, e3y + 0.6, 6);
  flowNum(P, s, dtx + dtw - 0.4, dty - 0.16, 7);
  flowNum(P, s, e2x + e2w - 0.4, e2y + e2h - 0.04, 8);

  s.addText(d.arch.legend, { x: 0.6, y: 6.25, w: 12.2, h: 0.95, fontFace: F_REG, fontSize: 9, color: INK, align: "left", valign: "top", lineSpacingMultiple: 1.03, margin: 0 });
  s.addNotes(d.notes.s5);
}

// ============================================================ SLIDE 6 — PROOF / PAYBACK / DEPLOY
function slideProof(P, d) {
  const s = P.addSlide();
  s.background = { color: SQUID };
  edgeBar(P, s);
  s.addText("Proof, Payback & How to Deploy", { x: 0.78, y: 0.38, w: 12, h: 0.7, fontFace: F_BOLD, fontSize: 32, bold: true, color: WHITE, align: "left", valign: "middle", margin: 0 });
  const cy = 1.35, ch = 4.05, cw = 5.78, x0 = 0.78, gap = 0.45;
  s.addShape(P.shapes.RECTANGLE, { x: x0, y: cy, w: cw, h: ch, fill: { color: SQUID2 }, line: { color: "3A485A", width: 1 } });
  s.addText("MEASURED OUTCOMES", { x: x0 + 0.32, y: cy + 0.22, w: cw - 0.6, h: 0.4, fontFace: F_BOLD, fontSize: 15, bold: true, color: ORANGE, charSpacing: 1, align: "left", valign: "middle", margin: 0 });
  const gx = [x0 + 0.32, x0 + cw / 2 + 0.12], gy = [cy + 0.78, cy + 2.1];
  d.proofStats.forEach((st, i) => {
    const x = gx[i % 2], y = gy[Math.floor(i / 2)];
    s.addText(st.big, { x, y, w: cw / 2 - 0.4, h: 0.6, fontFace: F_BOLD, fontSize: 26, bold: true, color: ORANGE, align: "left", valign: "middle", margin: 0 });
    s.addText(st.label, { x, y: y + 0.58, w: cw / 2 - 0.42, h: 0.6, fontFace: F_REG, fontSize: 10.5, color: "C9D2DC", align: "left", valign: "top", lineSpacingMultiple: 0.98, margin: 0 });
    tag(P, s, x, y + 1.16, st.tag, true);
  });
  const x1 = x0 + cw + gap;
  s.addShape(P.shapes.RECTANGLE, { x: x1, y: cy, w: cw, h: ch, fill: { color: SQUID2 }, line: { color: "3A485A", width: 1 } });
  s.addText("WHAT IT TAKES TO DEPLOY", { x: x1 + 0.32, y: cy + 0.22, w: cw - 0.6, h: 0.4, fontFace: F_BOLD, fontSize: 15, bold: true, color: TEAL, charSpacing: 1, align: "left", valign: "middle", margin: 0 });
  s.addText(d.deploySteps.map((b) => ({ text: b, options: { bullet: { type: "number" }, breakLine: true, paraSpaceAfter: 4, color: "E6ECF1" } })), { x: x1 + 0.45, y: cy + 0.72, w: cw - 0.8, h: 2.4, fontFace: F_REG, fontSize: 10.5, color: "E6ECF1", align: "left", valign: "top", lineSpacingMultiple: 1.0, margin: 0 });
  s.addText([
    { text: "Deploy:  ", options: { bold: true, color: ORANGE } },
    { text: d.deployOneLiner, options: { color: "DCE3EA", italic: true } },
  ], { x: x1 + 0.32, y: cy + 3.12, w: cw - 0.62, h: 0.6, fontFace: F_REG, fontSize: 9.5, align: "left", valign: "top", lineSpacingMultiple: 1.0, margin: 0 });
  s.addText(d.deployRef || `aws-native-reference/${d.runbook}  ·  docs/DEPLOY-QUICKSTART.md`, { x: x1 + 0.32, y: cy + ch - 0.4, w: cw - 0.6, h: 0.3, fontFace: F_REG, fontSize: 8.5, italic: true, color: MUTEDLT, align: "left", valign: "middle", margin: 0 });
  const by = cy + ch + 0.32, bh = 0.92;
  s.addShape(P.shapes.RECTANGLE, { x: x0, y: by, w: 11.78, h: bh, fill: { color: SQUID3 }, line: { color: "3A485A", width: 1 } });
  s.addText([
    { text: "The takeaway:  ", options: { bold: true, color: ORANGE } },
    { text: "the agent isn't the product — the governed platform that makes it 21 CFR Part 11 / GxP-defensible and deployable on AWS is.", options: { color: WHITE } },
  ], { x: x0 + 0.4, y: by, w: 11.0, h: bh, fontFace: F_REG, fontSize: 14, align: "left", valign: "middle", lineSpacingMultiple: 1.03, margin: 0 });
  s.addNotes(d.notes.s6);
}

function buildAgentDeck(P, d) {
  slideTitle(P, d); slideHook(P, d); slideIssueCost(P, d); slidePipeline(P, d); slideArch(P, d); slideProof(P, d);
}

// ============================================================ shared pipeline assurance cards
const stdCards = (consequential) => ([
  { title: "Every action audited", body: "node, timestamp, actor, data sources, model + prompt version — append-only and inspection-ready (21 CFR Part 11)." },
  { title: "Grounded & explainable", body: "every regulated claim traces to the source corpus; Bedrock Guardrails mask PHI before any model call and bound the output." },
  { title: `AI never decides ${consequential}`, body: "the consequential action is a human-only step, enforced in the orchestration framework — not a policy SOP." },
]);

// ============================================================ AGENT CONTENT
const AGENTS = [
{
  num: "01", name: "Regulatory Writing & Intelligence",
  tagline: "draft and assemble submission content from grounded evidence — a qualified human signs off",
  runbook: "01-regulatory-writing/DEPLOY.md",
  hero: "FROM SEARCHING TO SUBMITTING",
  valueProp: "A governed medical-writing copilot that retrieves approved evidence, drafts and assembles CTD/eCTD sections with every figure traceable to source — while a qualified regulatory writer reviews and signs off on what is submitted.",
  hookStats: [
    { big: "$2.6B", label: "average capitalized cost per approved drug — the value behind every submission", tag: "[gov/peer-reviewed — DiMasi/Tufts]" },
    { big: "~$60M / mo", label: "NPV lost per month of submission delay for a $1B-peak asset", tag: "[industry-research — McKinsey 2025]" },
    { big: "~55%", label: "first-draft CSR hours cut (180→80) with 50% fewer errors (Merck)", tag: "[vendor — Merck-reported]" },
  ],
  issueBullets: [
    "Medical writers spend disproportionate time retrieving and reconciling evidence rather than reasoning.",
    "A hallucinated number in a submission is a data-integrity defect — FDA's own gen-AI tool was reported to fabricate studies.",
    "Only ~13% of top pharma automate table/listing/figure assembly at scale; the rest is manual.",
    "Every regulated artifact carries 21 CFR Part 11 e-signature and ALCOA+ obligations before the first line of agent code.",
  ],
  costBig: "~$60M / month",
  costMath: "Industry: ~$60M NPV lost per month of submission delay for a $1B-peak asset (~$180M for a 12-week slip). The FY2026 PDUFA filing fee alone is $4.68M.",
  costRisks: [
    "Data-integrity findings and refuse-to-file risk from inconsistent or unsourced figures.",
    "Reviewer time lost reconciling drafts assembled by hand across documents.",
  ],
  costTag: "[industry-research — McKinsey 2025; FDA PDUFA FY2026]",
  brightLine: "the agent retrieves, drafts, and checks consistency; a qualified regulatory/medical writer reviews and signs off — nothing is submitted unedited.",
  pipelineTagline: "Retrieve approved evidence through a scoped gateway, draft and assemble grounded sections, verify every figure — then stop at a human gate before anything is filed.",
  pipeline: [
    { n: 1, title: "Retrieve evidence", sub: "RIM/DMS + guidance via gateway-scoped connectors", kind: "auto" },
    { n: 2, title: "Draft & assemble", sub: "CTD/eCTD sections grounded in source", kind: "auto" },
    { n: 3, title: "Consistency check", sub: "every figure traceable; grounding fails fast", kind: "auto" },
    { n: 4, title: "HUMAN GATE", sub: "qualified writer reviews & signs off", kind: "gate" },
    { n: 5, title: "Append-only audit", sub: "lineage + e-signature to immutable store", kind: "audit" },
  ],
  pipelineCards: stdCards("what gets submitted"),
  arch: {
    users: "Regulatory & medical writers",
    sor: "Veeva Vault RIM + DMS",
    ext: "FDA / EMA / PMDA guidance portals",
    runtime: [
      { t: "UI task (authoring console)", color: C_COMPUTE },
      { t: "Writer agent + grounding checker", color: C_COMPUTE },
      { t: "MCP auth gateway", s: "all outbound tool calls", color: C_INTEG },
    ],
    data: [
      { t: "Bedrock Knowledge Base", s: "approved evidence (RAG)", color: C_MODEL },
      { t: "DynamoDB audit", s: "append-only", color: C_INTEG },
      { t: "S3 Object Lock", s: "WORM submissions", color: C_STORAGE },
      { t: "Secrets Manager", s: "scoped tokens", color: C_STORAGE },
    ],
    legend: "1 writer sign-in   2 SAML federation (MFA at IdP; Cognito issues JWT — no credentials in AWS)   3 authenticated session to authoring console   4 RIM/DMS + guidance read over private connectivity   5 demand scales the agent workers   6 model calls reach Bedrock + Guardrails only over the private VPC endpoint (PrivateLink)   7 every draft, source, and e-signature persisted to append-only audit   8 connectors reachable only through the governed MCP gateway",
  },
  proofStats: [
    { big: "~55%", label: "first-draft CSR hours cut, 50% fewer errors (Merck)", tag: "[vendor — Merck]" },
    { big: "~40%", label: "CSR cycle-time reduction in early gen-AI pilots", tag: "[industry-research — McKinsey]" },
    { big: "$4.68M", label: "FY2026 PDUFA filing fee at stake per submission", tag: "[gov/peer-reviewed — FDA]" },
    { big: "100%", label: "of figures traceable to source by design (grounding gate)", tag: "[design property]" },
  ],
  deploySteps: [
    "Provision KMS CMK per data class + per-customer validated VPC / network.",
    "Stand up Cognito SAML→JWT federation with role scoping (writer / reviewer / QP).",
    "Front with CloudFront + WAF, ALB TLS 1.3.",
    "Deploy the agent + grant tools via the MCP gateway (deny-by-default).",
    "Connect Veeva Vault RIM/DMS; index approved guidance into a Knowledge Base.",
    "Enable S3 Object Lock + append-only audit; run smoke + HITL sign-off test.",
  ],
  deployOneLiner: "CloudFormation quick-deploy provisions the isolated environment + dual MCP gateway + native/container agent; point connectors at Veeva Vault; index approved guidance.",
  notes: {
    s1: "[00:20] Title. Agent 01 is a high-credibility land motion for R&D/regulatory. Position to the CIO as the safest way to prove the shared control plane on a document-centric workflow; to the CISO as a 21 CFR Part 11 story from commit one; to the Director of Architecture as grounded RAG with a hard human gate.",
    s2: "[00:45] Hook. Lead with DiMasi's $2.6B/drug as the value at stake, then McKinsey's ~$60M/month delay cost. The Merck 55% figure is vendor-reported and shown as such — it's the proof that the workflow is real, not the lead claim.",
    s3: "[01:10] Issue + cost. The pain is retrieval-vs-reasoning and hallucination risk; the cost is delay NPV plus the $4.68M PDUFA fee. The bright line: the agent drafts and checks, a qualified human signs off — this is what makes it submittable, not just impressive.",
    s4: "[01:35] Pipeline. Five steps, human gate in red. The grounding checker is the differentiator: a figure with no source fails fast rather than being asserted. The three assurance cards answer the regulated-buyer questions.",
    s5: "[02:15] Architecture — the most important slide. Trace the eight numbered flow steps. To deploy, the customer provides: an IdP, private connectivity to Veeva Vault, approved guidance content, and named reviewer/QP roles. Bedrock + Guardrails are reached over AWS PrivateLink; PHI/PII never egresses to an external AI API after masking.",
    s6: "[02:45] Proof + deploy. Outcomes are documented-at-company or modeled-at-baseline, never guaranteed. Six deploy steps map to the native DEPLOY.md. Close on the takeaway: the governed platform is the product.",
  },
},
{
  num: "02", name: "Pharmacovigilance — ICSR Case Intake",
  tagline: "triage, de-duplicate, MedDRA-code, and draft E2B narratives — a safety physician validates the case",
  runbook: "02-pharmacovigilance/DEPLOY.md",
  hero: "FROM CASE BACKLOG TO SAME-DAY TRIAGE",
  valueProp: "A governed ICSR copilot that triages intake, detects duplicates, proposes MedDRA coding, and drafts the E2B(R3) narrative — while a safety physician validates causality and the reportable case before it leaves the building.",
  hookStats: [
    { big: "~28M", label: "cumulative FAERS reports by end-2023; quarterly volume ~3× since 2007", tag: "[gov/peer-reviewed — FDA FAERS]" },
    { big: "40–85%", label: "of PV budgets consumed by case intake & processing", tag: "[sector-press/estimate]" },
    { big: "40–70%", label: "manual data-entry time cut in a Pfizer AI/RPA pilot", tag: "[gov/peer-reviewed — Schmider 2019]" },
  ],
  issueBullets: [
    "Adverse-event volumes scale with portfolio breadth; intake is high-volume and time-critical.",
    "Triage, duplicate detection, MedDRA coding, and E2B narrative drafting are repetitive and regulated.",
    "Case processing consumes up to two-thirds of internal PV resources; median ~69 min per report.",
    "ICSR volumes are growing ~8–15%/year — the backlog compounds without automation.",
  ],
  costBig: "~$2.0M / yr",
  costMath: "Modeled: 100,000 cases/yr × ~$20 outsourced intake/case = ~$2.0M/yr before internal labor. Intake/processing is 40–85% of PV budget; ~8–15% annual volume growth.",
  costRisks: [
    "Late or missed expedited reporting — regulatory and patient-safety exposure.",
    "Coding inconsistency that undermines signal detection across the portfolio.",
  ],
  costTag: "[modeled + sector-press/estimate]",
  brightLine: "the agent triages, de-duplicates, codes, and drafts; a qualified safety physician validates causality and the reportable case before submission.",
  pipelineTagline: "Ingest case data through a scoped gateway, propose triage / dedupe / MedDRA coding and draft the narrative — then stop at a safety-physician gate before reporting.",
  pipeline: [
    { n: 1, title: "Ingest & mask", sub: "case sources via gateway; PHI masked first", kind: "auto" },
    { n: 2, title: "Triage & dedupe", sub: "seriousness, expectedness, duplicate detection", kind: "auto" },
    { n: 3, title: "Code & draft E2B", sub: "MedDRA coding + E2B(R3) narrative draft", kind: "auto" },
    { n: 4, title: "HUMAN GATE", sub: "safety physician validates causality & case", kind: "gate" },
    { n: 5, title: "Append-only audit", sub: "every decision logged to immutable store", kind: "audit" },
  ],
  pipelineCards: stdCards("the reportable case"),
  arch: {
    users: "Safety operations & physicians",
    sor: "Argus / Veeva Safety",
    ext: "MedDRA · WHO Drug dictionaries",
    runtime: [
      { t: "UI task (case console)", color: C_COMPUTE },
      { t: "Triage/code agent + PHI masker", color: C_COMPUTE },
      { t: "MCP auth gateway", s: "all outbound tool calls", color: C_INTEG },
    ],
    data: [
      { t: "Safety DB connector", s: "Argus / Veeva", color: C_MODEL },
      { t: "DynamoDB audit", s: "append-only", color: C_INTEG },
      { t: "S3 Object Lock", s: "WORM case records", color: C_STORAGE },
      { t: "Secrets Manager", s: "scoped tokens", color: C_STORAGE },
    ],
    legend: "1 safety-ops sign-in   2 SAML federation (MFA at IdP; Cognito issues JWT)   3 authenticated session to case console   4 safety DB + dictionary reads over private connectivity   5 case volume scales the agent workers   6 model calls reach Bedrock + Guardrails only over the private VPC endpoint (PrivateLink) (PHI masked first)   7 every triage/coding/causality decision persisted to append-only audit   8 connectors reachable only through the governed MCP gateway",
  },
  proofStats: [
    { big: "40–70%", label: "manual data-entry time cut (Pfizer pilot)", tag: "[gov/peer-reviewed — Schmider]" },
    { big: "10–30%", label: "PV cost savings with GenAI/automation deployed", tag: "[industry-research]" },
    { big: "up to 2/3", label: "of internal PV resources today go to case processing", tag: "[gov/peer-reviewed]" },
    { big: "~69 min", label: "median processing per report today — the target", tag: "[gov/peer-reviewed]" },
  ],
  deploySteps: [
    "Provision KMS CMK + per-customer validated VPC / network.",
    "Stand up Cognito SAML→JWT federation (safety-ops / physician roles).",
    "Front with CloudFront + WAF, ALB TLS 1.3.",
    "Deploy the agent + grant tools via the MCP gateway (deny-by-default).",
    "Connect Argus/Veeva Safety + MedDRA/WHO Drug; enable PHI masker.",
    "Enable S3 Object Lock + append-only audit; run the live end-to-end demo path.",
  ],
  deployOneLiner: "CloudFormation quick-deploy provisions the isolated environment + dual MCP gateway; Agent 02 ships a live Bedrock + real-connector reference path you can run end-to-end.",
  notes: {
    s1: "[00:20] Title. Agent 02 is the flagship live path — real Bedrock inference and a real HTTP connector run end-to-end. Position to the CISO around PHI masking before any model call, and to the CIO around a high-volume workflow with a hard physician gate.",
    s2: "[00:45] Hook. FAERS volume (gov) is the pain proxy; 40–85% of PV budget (sector, flag it) is the spend; Schmider's 40–70% (peer-reviewed) is the credible ROI anchor.",
    s3: "[01:10] Issue + cost. Lead the modeled ~$2.0M/yr intake cost with arithmetic visible. The bright line: the agent drafts the case, a safety physician owns causality and reportability.",
    s4: "[01:35] Pipeline. PHI is masked at step 1, before anything reaches a model. Human gate in red. The audit card matters most to PV — every coding and causality call is logged.",
    s5: "[02:15] Architecture. Trace the eight steps; emphasize masking happens before the model boundary. Customer provides Argus/Veeva access, MedDRA/WHO Drug licenses, and named physician approvers.",
    s6: "[02:45] Proof + deploy. This is the agent to demo live. Six deploy steps map to the native DEPLOY.md and the demo/ path. Close on the takeaway.",
  },
},
{
  num: "03", name: "Clinical Trial Ops & TMF",
  tagline: "surface TMF gaps and EDC query backlog continuously — a CRA approves every disposition",
  runbook: "03-clinical-trial-ops/DEPLOY.md",
  hero: "FROM LATE SURPRISES TO CONTINUOUS READINESS",
  valueProp: "A governed trial-ops copilot that monitors TMF completeness and EDC query backlog continuously and drafts the work — while a CRA or TMF owner approves every filing, query, and closure, keeping the trial inspection-ready by design.",
  hookStats: [
    { big: "~$800K / day", label: "lost/delayed sales per day of trial delay (+ ~$40K/day direct cost)", tag: "[gov/peer-reviewed — Tufts 2024]" },
    { big: "57%", label: "of TMF owners still rely on paper / simple e-file systems", tag: "[industry-research — Veeva]" },
    { big: "$19.0M", label: "median pivotal-trial cost (IQR $12.2M–$33.1M)", tag: "[gov/peer-reviewed — JAMA IM]" },
  ],
  issueBullets: [
    "TMF gaps surface late — often after database lock, when they are most expensive to fix.",
    "EDC query backlogs slow enrollment and data cleaning; completeness is continuous, not periodic.",
    "“Failure to maintain adequate/accurate case histories” is among the most common FDA BIMO 483 findings.",
    "Advanced-eTMF users report inspection readiness of 56% vs. 25% — tooling gap is measurable.",
  ],
  costBig: "~$25.7M / slip",
  costMath: "Modeled: a 30-day database-lock / TMF slip on one Phase III ≈ 30 × ($800K lost sales + $55,716 direct/day) ≈ ~$25.7M. Tufts 2024 supersedes the old “$4–8M/day” figure.",
  costRisks: [
    "Inspection findings and refuse-to-file risk from an incomplete TMF.",
    "Enrollment and lock delays compounding the per-day cost of delay.",
  ],
  costTag: "[modeled — Tufts 2024 day-of-delay × Phase III direct cost]",
  brightLine: "the agent detects gaps and drafts queries; a CRA or TMF owner approves every filing, query, and closure — the disposition is human-owned.",
  pipelineTagline: "Continuously read eTMF/EDC/CTMS through a scoped gateway, detect gaps and draft queries — then route every disposition to a human gate.",
  pipeline: [
    { n: 1, title: "Continuous read", sub: "eTMF / EDC / CTMS via gateway connectors", kind: "auto" },
    { n: 2, title: "Detect gaps", sub: "completeness model vs. TMF reference model", kind: "auto" },
    { n: 3, title: "Draft queries/actions", sub: "propose filings, queries, follow-ups", kind: "auto" },
    { n: 4, title: "HUMAN GATE", sub: "CRA / TMF owner approves disposition", kind: "gate" },
    { n: 5, title: "Append-only audit", sub: "every action logged to immutable store", kind: "audit" },
  ],
  pipelineCards: stdCards("the TMF/query disposition"),
  arch: {
    users: "CRAs, CTAs & TMF owners",
    sor: "Veeva eTMF + CTMS + EDC",
    ext: "TMF Reference Model",
    runtime: [
      { t: "Event-driven worker + EventBridge", s: "continuous monitoring", color: C_COMPUTE },
      { t: "Completeness/query agent", color: C_COMPUTE },
      { t: "MCP auth gateway", s: "all outbound tool calls", color: C_INTEG },
    ],
    data: [
      { t: "Aurora / DynamoDB", s: "trial + TMF state", color: C_MODEL },
      { t: "DynamoDB audit", s: "append-only", color: C_INTEG },
      { t: "S3 Object Lock", s: "WORM TMF records", color: C_STORAGE },
      { t: "Secrets Manager", s: "scoped tokens", color: C_STORAGE },
    ],
    legend: "1 user sign-in   2 SAML federation (MFA at IdP; Cognito issues JWT)   3 authenticated session to trial-ops console   4 eTMF/EDC/CTMS reads over private connectivity   5 EventBridge schedules continuous completeness checks   6 model calls reach Bedrock + Guardrails only over the private VPC endpoint (PrivateLink)   7 every gap, query, and disposition persisted to append-only audit   8 connectors reachable only through the governed MCP gateway",
  },
  proofStats: [
    { big: "~$800K/day", label: "delay cost the agent works to compress", tag: "[gov/peer-reviewed — Tufts]" },
    { big: "56% vs 25%", label: "inspection readiness, advanced-eTMF vs. manual", tag: "[industry-research — Veeva]" },
    { big: "1M+ docs", label: "auto-classified by a TMF bot, “tens of thousands of hours”", tag: "[vendor — Veeva]" },
    { big: "continuous", label: "completeness vs. periodic spot-checks today", tag: "[design property]" },
  ],
  deploySteps: [
    "Provision KMS CMK + per-customer validated VPC / network.",
    "Stand up Cognito SAML→JWT federation (CRA / CTA / TMF-owner roles).",
    "Front with CloudFront + WAF, ALB TLS 1.3.",
    "Deploy the agent + grant tools via the MCP gateway (deny-by-default).",
    "Connect Veeva eTMF + CTMS + EDC; load the TMF Reference Model.",
    "Wire EventBridge for continuous checks; enable audit; run smoke + HITL test.",
  ],
  deployOneLiner: "CloudFormation quick-deploy provisions the isolated environment + dual MCP gateway + event-driven worker; point connectors at eTMF/EDC/CTMS.",
  notes: {
    s1: "[00:20] Title. Agent 03 turns periodic TMF QC into continuous readiness. Position to the CIO as event-driven automation on the shared control plane; to clinical ops as fewer post-lock surprises.",
    s2: "[00:45] Hook. Tufts $800K/day is the strongest number in the suite — lead with it. Veeva 57% paper and JAMA $19.0M median set the operational reality.",
    s3: "[01:10] Issue + cost. The modeled ~$25.7M 30-day-slip figure shows arithmetic. Note explicitly that we use Tufts 2024, not the discredited $4–8M/day myth. Bright line: the CRA owns the disposition.",
    s4: "[01:35] Pipeline. The key word is continuous — EventBridge drives ongoing checks rather than a pre-lock scramble. Human gate in red.",
    s5: "[02:15] Architecture. Note the EventBridge-driven worker for continuous monitoring. Customer provides eTMF/EDC/CTMS access and named approvers.",
    s6: "[02:45] Proof + deploy. Veeva's 1M-doc bot is vendor-reported and flagged. Close on continuous readiness and the platform-is-the-product takeaway.",
  },
},
{
  num: "04", name: "Site Selection & Patient Matching",
  tagline: "rank sites on real performance and size cohorts on RWD — humans select sites and confirm eligibility",
  runbook: "04-site-patient-matching/DEPLOY.md",
  hero: "FROM SITE GUESSWORK TO EVIDENCE",
  valueProp: "A governed feasibility copilot that ranks sites on historical performance and sizes cohorts against real-world data — while humans select the sites and clinicians confirm every patient's eligibility, with diversity surfaced as a first-class metric.",
  hookStats: [
    { big: "~80%", label: "of trials miss their original enrollment timeline", tag: "[sector-press/estimate — flag on slide]" },
    { big: "~20% / ~30%", label: "of sites enroll zero / under-enroll patients", tag: "[sector-press/estimate]" },
    { big: "~36%", label: "average screen-failure rate (70–85% in CNS/rare disease)", tag: "[sector-press/estimate]" },
  ],
  issueBullets: [
    "Feasibility still leans on site-opinion surveys rather than historical performance data.",
    "Real-world cohort sizing is rarely integrated at scale, so enrollment assumptions are optimistic.",
    "~1 in 5 sites enroll no one and ~30% under-enroll — wasted activation cost and lost time.",
    "FDA Diversity Action Plan expectations make representativeness a design requirement, not an afterthought.",
  ],
  costBig: "~$24M / launch",
  costMath: "Modeled: compressing enrollment by 30 days ≈ 30 × $800K/day lost sales ≈ ~$24M recovered per launch. Cost per patient recruited commonly $1,500–$10,000; recruitment is 20–30% of trial budget.",
  costRisks: [
    "Site activation spend on non-enrolling sites.",
    "Diversity-plan and ICH E17 gaps that jeopardize acceptability of the evidence.",
  ],
  costTag: "[modeled — Tufts 2024 day-of-delay; recruitment benchmarks]",
  brightLine: "the agent ranks sites and sizes cohorts; humans select the sites and a clinician confirms each patient's eligibility — no autonomous enrollment.",
  pipelineTagline: "Read historical site performance and de-identified RWD through a scoped gateway, rank and size — then route selection and eligibility to humans.",
  pipeline: [
    { n: 1, title: "Read performance + RWD", sub: "CTMS history + de-identified RWD via gateway", kind: "auto" },
    { n: 2, title: "Rank & size cohorts", sub: "performance model + feasibility + diversity", kind: "auto" },
    { n: 3, title: "Draft feasibility pack", sub: "ranked sites, cohort sizing, diversity view", kind: "auto" },
    { n: 4, title: "HUMAN GATE", sub: "humans select sites; clinician confirms eligibility", kind: "gate" },
    { n: 5, title: "Append-only audit", sub: "rationale + data lineage logged", kind: "audit" },
  ],
  pipelineCards: stdCards("site selection & patient eligibility"),
  arch: {
    users: "Feasibility & clinical-ops teams",
    sor: "CTMS (historical performance)",
    ext: "RWD / claims / registry (de-identified)",
    runtime: [
      { t: "UI task (feasibility console)", color: C_COMPUTE },
      { t: "Ranking/cohort agent + de-id check", color: C_COMPUTE },
      { t: "MCP auth gateway", s: "all outbound tool calls", color: C_INTEG },
    ],
    data: [
      { t: "Aurora / DynamoDB", s: "feasibility state", color: C_MODEL },
      { t: "DynamoDB audit", s: "append-only", color: C_INTEG },
      { t: "S3 Object Lock", s: "WORM rationale", color: C_STORAGE },
      { t: "Secrets Manager", s: "scoped tokens", color: C_STORAGE },
    ],
    legend: "1 user sign-in   2 SAML federation (MFA at IdP; Cognito issues JWT)   3 authenticated session to feasibility console   4 CTMS + de-identified RWD reads over private connectivity   5 demand scales the agent workers   6 model calls reach Bedrock + Guardrails only over the private VPC endpoint (PrivateLink)   7 ranking rationale + data lineage persisted to append-only audit   8 connectors reachable only through the governed MCP gateway (de-identification enforced)",
  },
  proofStats: [
    { big: "~$24M", label: "modeled recovery per launch from a 30-day pull-in", tag: "[modeled]" },
    { big: "evidence", label: "historical performance vs. opinion surveys", tag: "[design property]" },
    { big: "diversity", label: "representativeness surfaced as a first-class metric", tag: "[FDA Diversity Action Plan posture]" },
    { big: "de-identified", label: "RWD via Safe Harbor / Expert Determination", tag: "[HIPAA]" },
  ],
  deploySteps: [
    "Provision KMS CMK + per-customer validated VPC / network.",
    "Stand up Cognito SAML→JWT federation (feasibility / clinician roles).",
    "Front with CloudFront + WAF, ALB TLS 1.3.",
    "Deploy the agent + grant tools via the MCP gateway (deny-by-default).",
    "Connect CTMS history + de-identified RWD; enforce de-identification at the gateway.",
    "Enable S3 Object Lock + append-only audit; run smoke + HITL test.",
  ],
  deployOneLiner: "CloudFormation quick-deploy provisions the isolated environment + dual MCP gateway; point connectors at CTMS history and a de-identified RWD source.",
  notes: {
    s1: "[00:20] Title. Agent 04 replaces opinion-based feasibility with evidence. Position to the Director of Architecture around enforced de-identification at the gateway; to clinical ops around fewer non-enrolling sites.",
    s2: "[00:45] Hook. All three hook stats are sector estimates — say so on the slide. They establish the enrollment-failure reality without overclaiming.",
    s3: "[01:10] Issue + cost. The ~$24M modeled recovery uses Tufts day-of-delay; show the math. Diversity Action Plan is a live-but-moving driver — frame it as design posture. Bright line: humans select sites, clinicians confirm eligibility.",
    s4: "[01:35] Pipeline. De-identification is enforced at the gateway, not assumed. Human gate in red. No autonomous enrollment.",
    s5: "[02:15] Architecture. Emphasize de-identification enforcement on RWD connectors. Customer provides CTMS history and a de-identified RWD source.",
    s6: "[02:45] Proof + deploy. Be candid: an independent AI patient-matching ROI benchmark is not established — the value case is the modeled delay-recovery plus governance. Close on the takeaway.",
  },
},
{
  num: "05", name: "Quality / CAPA & Complaints",
  tagline: "draft root-cause and CAPA, score complaints — a quality owner approves classification and closure",
  runbook: "05-quality-capa/DEPLOY.md",
  hero: "FROM REPEAT FINDINGS TO ROOT CAUSE",
  valueProp: "A governed quality copilot that triages complaints, drafts root-cause analysis and CAPA records, and flags MDR reportability — while a quality owner approves every classification, reportability call, and closure.",
  hookStats: [
    { big: "#1 cited", label: "CAPA (21 CFR 820.100) is consistently the most-cited FDA device 483 clause", tag: "[gov/peer-reviewed — FDA]" },
    { big: "561", label: "drug-program 483s issued in FY2024 (211.192 cites up ~171% YoY)", tag: "[gov/peer-reviewed + sector-press]" },
    { big: "$10M–$100M", label: "typical pharma recall cost depending on scope", tag: "[industry-research]" },
  ],
  issueBullets: [
    "Product-complaint volumes are large; CAPA root-cause consistency is a recurring inspection finding.",
    "On-time CAPA closure rates are a perennial 483/warning-letter theme.",
    "Complaint handling (820.198) is among the most error-prone QSR areas for device makers.",
    "FDA's QMSR (effective Feb 2026) raises the bar on quality-record integrity and traceability.",
  ],
  costBig: "$10M–$100M / recall",
  costMath: "Industry: a pharma recall runs $10M–$100M by scope; non-routine device quality events are estimated at $2.5B–$5B/yr industry-wide. CAPA and complaint handling are the perennial top inspection findings.",
  costRisks: [
    "Warning letters and consent decrees from repeat root-cause and closure findings.",
    "Recall and MDR exposure from late or mis-classified complaints.",
  ],
  costTag: "[industry-research — recall-cost analysis; FDA inspection data]",
  brightLine: "the agent drafts root-cause, CAPA, and reportability recommendations; a quality owner approves classification, MDR reportability, and closure.",
  pipelineTagline: "Read complaints and quality events through a scoped gateway, draft root-cause and CAPA and flag reportability — then route every disposition to a quality owner.",
  pipeline: [
    { n: 1, title: "Ingest complaints/events", sub: "QMS + complaint DB via gateway connectors", kind: "auto" },
    { n: 2, title: "Triage & cluster", sub: "severity, similar-event clustering, trends", kind: "auto" },
    { n: 3, title: "Draft RCA + CAPA", sub: "root-cause draft, CAPA, MDR reportability flag", kind: "auto" },
    { n: 4, title: "HUMAN GATE", sub: "quality owner approves classification & closure", kind: "gate" },
    { n: 5, title: "Append-only audit", sub: "every decision logged to immutable store", kind: "audit" },
  ],
  pipelineCards: stdCards("the CAPA disposition or reportability"),
  arch: {
    users: "Quality & complaint-handling teams",
    sor: "QMS (TrackWise / Veeva Quality)",
    ext: "Complaint databases",
    runtime: [
      { t: "UI task (quality console)", color: C_COMPUTE },
      { t: "RCA/CAPA agent + clustering", color: C_COMPUTE },
      { t: "MCP auth gateway", s: "all outbound tool calls", color: C_INTEG },
    ],
    data: [
      { t: "Aurora / DynamoDB", s: "case + CAPA state", color: C_MODEL },
      { t: "DynamoDB audit", s: "append-only", color: C_INTEG },
      { t: "S3 Object Lock", s: "WORM quality records", color: C_STORAGE },
      { t: "Secrets Manager", s: "scoped tokens", color: C_STORAGE },
    ],
    legend: "1 user sign-in   2 SAML federation (MFA at IdP; Cognito issues JWT)   3 authenticated session to quality console   4 QMS + complaint-DB reads over private connectivity   5 demand scales the agent workers   6 model calls reach Bedrock + Guardrails only over the private VPC endpoint (PrivateLink)   7 every classification, RCA, and closure persisted to append-only audit   8 connectors reachable only through the governed MCP gateway",
  },
  proofStats: [
    { big: "consistency", label: "structured RCA vs. variable manual root-cause", tag: "[design property]" },
    { big: "reportability", label: "MDR flag drafted; quality owner decides", tag: "[design property]" },
    { big: "#1 finding", label: "CAPA is the clause this directly addresses", tag: "[gov/peer-reviewed — FDA]" },
    { big: "QMSR-ready", label: "audit + traceability posture for Feb 2026", tag: "[gov/peer-reviewed]" },
  ],
  deploySteps: [
    "Provision KMS CMK + per-customer validated VPC / network.",
    "Stand up Cognito SAML→JWT federation (analyst / quality-owner roles).",
    "Front with CloudFront + WAF, ALB TLS 1.3.",
    "Deploy the agent + grant tools via the MCP gateway (deny-by-default).",
    "Connect TrackWise/Veeva Quality + complaint DB.",
    "Enable S3 Object Lock + append-only audit; run smoke + HITL test.",
  ],
  deployOneLiner: "CloudFormation quick-deploy provisions the isolated environment + dual MCP gateway; point connectors at the QMS and complaint database.",
  notes: {
    s1: "[00:20] Title. Agent 05 targets the single most-cited FDA finding area. Position to the CISO/quality leadership around traceable, consistent root-cause; to the CIO around QMSR-readiness for Feb 2026.",
    s2: "[00:45] Hook. CAPA-is-#1-cited and 561 483s are government-grade. Recall cost is industry-research. Strong, defensible openers.",
    s3: "[01:10] Issue + cost. Recall cost is the headline dollar risk; CAPA/complaint findings are the recurring operational risk. Bright line: the quality owner decides classification and closure.",
    s4: "[01:35] Pipeline. The MDR reportability flag is drafted, never decided by the agent. Human gate in red.",
    s5: "[02:15] Architecture. Standard shared spine. Customer provides QMS + complaint-DB access and named quality approvers.",
    s6: "[02:45] Proof + deploy. Be candid: independent AI CAPA-automation ROI is not established — the value case is finding-area fit, consistency, and QMSR-readiness. Close on the takeaway.",
  },
},
{
  num: "06", name: "Clinical Protocol Design & Feasibility",
  tagline: "draft protocol sections grounded in guidance and RWD — clinical leads own the design",
  runbook: "06-protocol-design/DEPLOY.md",
  hero: "FROM REWRITES TO RIGHT-FIRST-TIME",
  valueProp: "A governed protocol copilot that drafts sections grounded in current guidance and links feasibility assumptions to real-world data — while clinical and medical leads own the design, reducing the avoidable amendments that delay every trial.",
  hookStats: [
    { big: "~57%", label: "of protocols incur ≥1 substantial amendment; ~45% avoidable", tag: "[industry-research — Tufts]" },
    { big: "$535K", label: "median direct cost of a substantial Phase III amendment", tag: "[industry-research — Tufts]" },
    { big: "~44%", label: "rise in distinct Phase II/III procedures since 2009 (complexity)", tag: "[industry-research — Tufts]" },
  ],
  issueBullets: [
    "First-draft protocols incorporate historical guidance and study data late, driving rework.",
    "Feasibility assumptions are often not linked to real-world data, so they prove optimistic.",
    "Phase III protocols with ≥1 substantial amendment have risen toward ~82% in recent benchmarking.",
    "Each substantial amendment adds direct cost and a 60–80-day cycle delay valued at ~$800K/day.",
  ],
  costBig: "~$535K / amendment",
  costMath: "Modeled: preventing one avoidable Phase III amendment ≈ $535K direct (Tufts) + a ~60–80-day delay valued at ~$800K/day lost sales. ~45% of substantial amendments are avoidable.",
  costRisks: [
    "Compounding delay cost from each amendment cycle.",
    "Enrollment and site disruption when protocols change mid-study.",
  ],
  costTag: "[modeled — Tufts 2016 amendment cost + Tufts 2024 delay-day]",
  brightLine: "the agent drafts sections and surfaces feasibility evidence; clinical and medical leads own the protocol design — nothing is finalized unedited.",
  pipelineTagline: "Retrieve current guidance and historical/RWD evidence through a scoped gateway, draft grounded sections and feasibility — then route the design to clinical leads.",
  pipeline: [
    { n: 1, title: "Retrieve guidance + data", sub: "RIM guidance + historical/RWD via gateway", kind: "auto" },
    { n: 2, title: "Draft sections", sub: "objectives, endpoints, eligibility — grounded", kind: "auto" },
    { n: 3, title: "Link feasibility", sub: "eligibility vs. RWD cohort feasibility", kind: "auto" },
    { n: 4, title: "HUMAN GATE", sub: "clinical / medical leads own the design", kind: "gate" },
    { n: 5, title: "Append-only audit", sub: "draft + source lineage logged", kind: "audit" },
  ],
  pipelineCards: stdCards("the protocol design"),
  arch: {
    users: "Clinical & medical study leads",
    sor: "RIM (guidance) + CTMS history",
    ext: "RWD (feasibility)",
    runtime: [
      { t: "UI task (protocol console)", color: C_COMPUTE },
      { t: "Drafting agent + feasibility linker", color: C_COMPUTE },
      { t: "MCP auth gateway", s: "all outbound tool calls", color: C_INTEG },
    ],
    data: [
      { t: "Bedrock Knowledge Base", s: "guidance corpus (RAG)", color: C_MODEL },
      { t: "DynamoDB audit", s: "append-only", color: C_INTEG },
      { t: "S3 Object Lock", s: "WORM drafts", color: C_STORAGE },
      { t: "Secrets Manager", s: "scoped tokens", color: C_STORAGE },
    ],
    legend: "1 user sign-in   2 SAML federation (MFA at IdP; Cognito issues JWT)   3 authenticated session to protocol console   4 guidance + historical/RWD reads over private connectivity   5 demand scales the agent workers   6 model calls reach Bedrock + Guardrails only over the private VPC endpoint (PrivateLink)   7 every draft and source persisted to append-only audit   8 connectors reachable only through the governed MCP gateway",
  },
  proofStats: [
    { big: "~45%", label: "of substantial amendments are avoidable — the target", tag: "[industry-research — Tufts]" },
    { big: "$535K", label: "direct cost avoided per prevented Phase III amendment", tag: "[industry-research — Tufts]" },
    { big: "grounded", label: "current guidance incorporated at first draft", tag: "[design property]" },
    { big: "RWD-linked", label: "feasibility tied to real cohort sizing", tag: "[design property]" },
  ],
  deploySteps: [
    "Provision KMS CMK + per-customer validated VPC / network.",
    "Stand up Cognito SAML→JWT federation (clinical / medical-lead roles).",
    "Front with CloudFront + WAF, ALB TLS 1.3.",
    "Deploy the agent + grant tools via the MCP gateway (deny-by-default).",
    "Connect RIM guidance + CTMS history; connect an RWD source for feasibility.",
    "Enable S3 Object Lock + append-only audit; run smoke + HITL test.",
  ],
  deployOneLiner: "CloudFormation quick-deploy provisions the isolated environment + dual MCP gateway; index guidance into a Knowledge Base; connect historical + RWD sources.",
  notes: {
    s1: "[00:20] Title. Agent 06 attacks avoidable amendments at the design stage. Position to clinical development around right-first-time protocols; to the CIO around reuse of the same grounded-RAG control plane as Agent 01.",
    s2: "[00:45] Hook. All three are Tufts industry-research — strong and defensible. 57% amend / 45% avoidable / $535K / 44% complexity tell a tight story.",
    s3: "[01:10] Issue + cost. The value case is avoided-amendment cost plus avoided delay days — both Tufts, labeled modeled. Bright line: clinical leads own the design.",
    s4: "[01:35] Pipeline. Feasibility is linked to RWD so eligibility criteria are realistic. Human gate in red.",
    s5: "[02:15] Architecture. Same grounded-RAG spine as 01, plus an RWD feasibility link. Customer provides guidance content, historical data, and an RWD source.",
    s6: "[02:45] Proof + deploy. Be candid: independent AI protocol-design ROI is not established — the value case is Tufts amendment economics. Close on the takeaway.",
  },
},
{
  num: "07", name: "Real-World Evidence / HEOR",
  tagline: "build cohorts and translate code so analysts analyze — an epidemiologist approves the study",
  runbook: "07-rwe-heor/DEPLOY.md",
  hero: "FROM WRANGLING TO EVIDENCE",
  valueProp: "A governed RWE/HEOR copilot that defines cohorts, translates between code systems, and assembles auditable data lineage — so analysts spend time on analysis, while an epidemiologist or biostatistician approves the study and its conclusions.",
  hookStats: [
    { big: "~45%", label: "of analyst time goes to data prep, not analysis (measured)", tag: "[sector-press/estimate — Anaconda]" },
    { big: "~6 months", label: "to manually build a retrospective RWE database study", tag: "[sector-press/estimate]" },
    { big: "~$1.3M / yr", label: "non-analytic labor for a 20-person RWE team (modeled)", tag: "[modeled]" },
  ],
  issueBullets: [
    "RWE/HEOR requires cohort definition, confounding control, and structured code translation.",
    "Analyst time is disproportionately spent on data wrangling rather than evidence generation.",
    "FDA's RWE Framework hinges on data fitness-for-purpose and auditable lineage — hard to do by hand.",
    "Follow-on FDA RWD/RWE guidances (2023–24) keep raising the bar on traceability.",
  ],
  costBig: "~$1.3M / yr / team",
  costMath: "Modeled: analyst ~$150K fully loaded × ~45% on wrangling = ~$67K/yr each; a 20-person RWE team ≈ ~$1.3M/yr of non-analytic labor. A single study can take ~6 months to build before analysis.",
  costRisks: [
    "Slow evidence generation that delays HEOR dossiers and market-access decisions.",
    "Lineage gaps that weaken the fitness-for-purpose case to FDA.",
  ],
  costTag: "[modeled — loaded analyst cost × Anaconda data-prep share]",
  brightLine: "the agent builds cohorts, translates code, and documents lineage; an epidemiologist or biostatistician approves the study design and conclusions.",
  pipelineTagline: "Read de-identified RWD through a scoped gateway, define cohorts and translate code with full lineage — then route the study to a qualified human.",
  pipeline: [
    { n: 1, title: "Read de-identified RWD", sub: "claims / registry / RWD via gateway", kind: "auto" },
    { n: 2, title: "Define cohort + translate", sub: "phenotype, code-system mapping, lineage", kind: "auto" },
    { n: 3, title: "Draft analysis plan", sub: "confounding controls, feasibility counts", kind: "auto" },
    { n: 4, title: "HUMAN GATE", sub: "epidemiologist / biostatistician approves", kind: "gate" },
    { n: 5, title: "Append-only audit", sub: "data lineage + decisions logged", kind: "audit" },
  ],
  pipelineCards: stdCards("the analysis & conclusions"),
  arch: {
    users: "RWE / HEOR analysts & epidemiologists",
    sor: "Claims / registry / RWD platforms",
    ext: "Code systems (ICD / SNOMED / RxNorm)",
    runtime: [
      { t: "UI task (analysis console)", color: C_COMPUTE },
      { t: "Cohort/code agent + lineage tracker", color: C_COMPUTE },
      { t: "MCP auth gateway", s: "all outbound tool calls", color: C_INTEG },
    ],
    data: [
      { t: "Aurora / Redshift", s: "cohort + lineage", color: C_MODEL },
      { t: "DynamoDB audit", s: "append-only", color: C_INTEG },
      { t: "S3 Object Lock", s: "WORM study records", color: C_STORAGE },
      { t: "Secrets Manager", s: "scoped tokens", color: C_STORAGE },
    ],
    legend: "1 analyst sign-in   2 SAML federation (MFA at IdP; Cognito issues JWT)   3 authenticated session to analysis console   4 de-identified RWD reads over private connectivity   5 demand scales the agent workers   6 model calls reach Bedrock + Guardrails only over the private VPC endpoint (PrivateLink)   7 full data lineage + decisions persisted to append-only audit   8 connectors reachable only through the governed MCP gateway (de-identification enforced)",
  },
  proofStats: [
    { big: "~45%→90%", label: "analyst time shifted from prep toward analysis", tag: "[design target vs. Anaconda baseline]" },
    { big: "lineage", label: "auditable data provenance for FDA fitness-for-purpose", tag: "[gov/peer-reviewed — FDA RWE]" },
    { big: "code xlat", label: "ICD/SNOMED/RxNorm mapping with provenance", tag: "[design property]" },
    { big: "hours→min", label: "vendor proxy: AstraZeneca analyst acceleration", tag: "[vendor — AWS]" },
  ],
  deploySteps: [
    "Provision KMS CMK + per-customer validated VPC / network.",
    "Stand up Cognito SAML→JWT federation (analyst / epidemiologist roles).",
    "Front with CloudFront + WAF, ALB TLS 1.3.",
    "Deploy the agent + grant tools via the MCP gateway (deny-by-default).",
    "Connect de-identified claims/registry/RWD; enforce de-identification at the gateway.",
    "Enable S3 Object Lock + append-only audit; run smoke + HITL test.",
  ],
  deployOneLiner: "CloudFormation quick-deploy provisions the isolated environment + dual MCP gateway; point connectors at de-identified RWD; wire code-system references.",
  notes: {
    s1: "[00:20] Title. Agent 07 moves analyst time from wrangling to evidence. Position to the Director of Architecture around enforced de-identification and auditable lineage; to HEOR leadership around faster dossiers.",
    s2: "[00:45] Hook. We use Anaconda's measured ~45% data-prep share rather than the bare “80%” myth — more defensible. The ~$1.3M/yr is modeled; show it.",
    s3: "[01:10] Issue + cost. Lineage is the regulatory hook — FDA fitness-for-purpose demands it. Bright line: a qualified scientist approves the study.",
    s4: "[01:35] Pipeline. Lineage is captured continuously, not reconstructed later. Human gate in red.",
    s5: "[02:15] Architecture. Note de-identification enforcement and the lineage tracker. Customer provides de-identified RWD and code-system references.",
    s6: "[02:45] Proof + deploy. The AstraZeneca acceleration is a vendor proxy, flagged. The defensible value is the prep-to-analysis shift plus lineage. Close on the takeaway.",
  },
},
{
  num: "08", name: "Medical Affairs / MSL Copilot",
  tagline: "draft on-label, evidence-grounded HCP responses — MLR review approves before anything ships",
  runbook: "08-medical-affairs-msl/DEPLOY.md",
  hero: "FROM WEEKS IN MLR TO DAYS",
  valueProp: "A governed Medical Affairs copilot that drafts on-label, evidence-grounded responses for HCP interactions with off-label guardrails enforced technically — while MLR review approves everything before it reaches a healthcare professional.",
  hookStats: [
    { big: "weeks→months", label: "MLR review is the single biggest content-release bottleneck", tag: "[sector-press/estimate]" },
    { big: "50–70%", label: "potential reduction in time-to-deliver for medical-legal reviews", tag: "[industry-research — McKinsey]" },
    { big: "$3B / $2.3B", label: "record off-label promotion settlements (GSK / Pfizer)", tag: "[gov/peer-reviewed — DOJ]" },
  ],
  issueBullets: [
    "Field medical teams need rapid, on-label, evidence-grounded responses for HCP interactions.",
    "Off-label guardrails must be technical, not procedural — a policy SOP is not a control.",
    "MLR cycles routinely stretch from weeks into months, causing missed launch windows.",
    "Off-label promotion is among the highest-dollar compliance risks in pharma.",
  ],
  costBig: "Billions in FCA risk",
  costMath: "DOJ recovered $6.8B in total FY2025 False Claims Act recoveries (healthcare a leading category). Record off-label settlements: GSK $3B, Pfizer $2.3B, J&J $2.2B, AstraZeneca $520M.",
  costRisks: [
    "Off-label promotion liability and corporate-integrity-agreement exposure.",
    "Missed launch windows when MLR is the bottleneck.",
  ],
  costTag: "[gov/peer-reviewed — DOJ; industry-research — McKinsey]",
  brightLine: "the agent drafts on-label, grounded responses within Guardrails; MLR review approves before anything reaches an HCP — off-label is blocked technically.",
  pipelineTagline: "Retrieve approved label and evidence through a scoped gateway, draft on-label responses within Guardrails — then route every response through MLR before delivery.",
  pipeline: [
    { n: 1, title: "Retrieve label + evidence", sub: "approved label/DMS via Knowledge Base", kind: "auto" },
    { n: 2, title: "Draft on-label response", sub: "grounded; off-label blocked by Guardrails", kind: "auto" },
    { n: 3, title: "Annotate references", sub: "claims linked to approved sources", kind: "auto" },
    { n: 4, title: "HUMAN GATE", sub: "MLR review approves before HCP delivery", kind: "gate" },
    { n: 5, title: "Append-only audit", sub: "every response + approval logged", kind: "audit" },
  ],
  pipelineCards: stdCards("what reaches an HCP"),
  arch: {
    users: "MSLs & Medical Information teams",
    sor: "Veeva CRM + DMS / MSL portal",
    ext: "Approved label & evidence library",
    runtime: [
      { t: "UI task (MSL console)", color: C_COMPUTE },
      { t: "Response agent + off-label Guardrails", color: C_COMPUTE },
      { t: "MCP auth gateway", s: "all outbound tool calls", color: C_INTEG },
    ],
    data: [
      { t: "Bedrock Knowledge Base", s: "label + evidence (RAG)", color: C_MODEL },
      { t: "DynamoDB audit", s: "append-only", color: C_INTEG },
      { t: "S3 Object Lock", s: "WORM responses", color: C_STORAGE },
      { t: "Secrets Manager", s: "scoped tokens", color: C_STORAGE },
    ],
    legend: "1 MSL sign-in   2 SAML federation (MFA at IdP; Cognito issues JWT)   3 authenticated session to MSL console   4 CRM/DMS + label reads over private connectivity   5 demand scales the agent workers   6 model calls reach Bedrock + Guardrails only over the private VPC endpoint (PrivateLink) (off-label filters mandatory)   7 every response and MLR approval persisted to append-only audit   8 connectors reachable only through the governed MCP gateway",
  },
  proofStats: [
    { big: "50–70%", label: "potential MLR time-to-deliver reduction", tag: "[industry-research — McKinsey]" },
    { big: "20–30%", label: "medical-writing cost savings (rising as it matures)", tag: "[industry-research — McKinsey]" },
    { big: "technical", label: "off-label guardrail enforced, not procedural", tag: "[design property]" },
    { big: "~$3–5B/yr", label: "potential Medical Affairs efficiency industry-wide", tag: "[industry-research — McKinsey]" },
  ],
  deploySteps: [
    "Provision KMS CMK + per-customer validated VPC / network.",
    "Stand up Cognito SAML→JWT federation (MSL / MLR-reviewer roles).",
    "Front with CloudFront + WAF, ALB TLS 1.3.",
    "Deploy the agent + grant tools via the MCP gateway (deny-by-default).",
    "Connect Veeva CRM/DMS; index approved label + evidence; set off-label Guardrails.",
    "Enable S3 Object Lock + append-only audit; run smoke + HITL (MLR) test.",
  ],
  deployOneLiner: "CloudFormation quick-deploy provisions the isolated environment + dual MCP gateway; connect Veeva CRM/DMS, index the approved label, and set off-label Guardrails.",
  notes: {
    s1: "[00:20] Title. Agent 08 compresses MLR while making off-label a technical control. Position to the CISO/compliance around enforced off-label Guardrails and full auditability; to commercial around faster content release.",
    s2: "[00:45] Hook. MLR-is-the-bottleneck (sector, flag it), McKinsey 50–70% (industry), and the DOJ settlement figures (gov) frame both upside and risk.",
    s3: "[01:10] Issue + cost. The cost slide is risk-led: billions in FCA exposure. Bright line: MLR approves before anything reaches an HCP; off-label is blocked technically.",
    s4: "[01:35] Pipeline. Off-label is blocked by Guardrails at draft time, not caught later. Reference annotation makes MLR faster. Human gate in red.",
    s5: "[02:15] Architecture. Off-label content filters are mandatory at the model boundary. Customer provides CRM/DMS access, the approved label, and named MLR reviewers.",
    s6: "[02:45] Proof + deploy. McKinsey figures are industry-research; the off-label control is a design property, not a benchmark. Close on the takeaway.",
  },
},
];

// ============================================================ EXPANSION (roadmap) AGENTS
// Agents that extend the lifecycle beyond the core-8 land/expand narrative.
//   09 Manufacturing Batch-Review — BUILT to flagship depth (LangGraph app + 36 tests +
//      AWS-native rebuild + 4-doc set); see 09-manufacturing-batch-review-agent/.
//   10 Scientific Intelligence & Target Discovery — ROADMAP (Documented; cited deck + spec).
// Per-agent decks only — the executive overview stays at the 8 core-lifecycle agents by design.
const EXPANSION = [
{
  num: "09", name: "Manufacturing Batch-Review",
  tagline: "review electronic batch records by exception — QA owns every release/reject",
  runbook: "09-manufacturing-batch-review",
  deployRef: "aws-native-reference/09-manufacturing-batch-review/DEPLOY.md  ·  docs/DEPLOY-QUICKSTART.md",
  hero: "FROM 48-HOUR REVIEWS TO REVIEW BY EXCEPTION",
  valueProp: "A governed batch-review copilot that reads the electronic batch record and process data, flags deviations and out-of-spec results by exception, and drafts the disposition — while a QA reviewer makes and signs every release/reject decision.",
  hookStats: [
    { big: "62%", label: "of US drug shortages trace to manufacturing/quality problems — the #1 root cause", tag: "[gov/peer-reviewed — FDA]" },
    { big: "~48 hrs", label: "average review per batch report today (up to ~500 hrs for complex paper-based)", tag: "[sector-press/estimate]" },
    { big: "~$14K", label: "average cost per deviation investigation (mostly senior labor)", tag: "[sector-press/estimate]" },
  ],
  issueBullets: [
    "Batch-record review and OOS/deviation investigation are slow, manual, and senior-labor-heavy.",
    "21 CFR 211.192 (production-record review / discrepancy investigation) is among the most-cited FDA warning-letter findings.",
    "Right-first-time for complex biologics often sits ~80%; every non-RFT batch triggers rework and release delay.",
    "A single biologics batch failure can cost tens of millions; raw materials alone often exceed $1–2M.",
  ],
  costBig: "~$420K / yr",
  costMath: "Modeled: 200 batches/yr × ~15% deviating (85% RFT) ≈ 30 investigations × ~$14K labor ≈ ~$420K/yr — before any scrapped batch ($1–2M+ each) or delayed-release carrying cost.",
  costRisks: [
    "Release delays and drug-shortage risk from review backlogs.",
    "Data-integrity / 211.192 findings from inconsistent record review.",
  ],
  costTag: "[modeled — deviation-investigation cost × batch volume]",
  brightLine: "the agent reviews records and flags exceptions; a QA reviewer makes and signs the final release/reject decision — the agent never releases a batch.",
  pipelineTagline: "Read the electronic batch record + MES/LIMS data through a scoped gateway, check by exception and draft the disposition — then stop at a QA gate before release.",
  pipeline: [
    { n: 1, title: "Read EBR + MES/LIMS", sub: "batch record + process/QC data via gateway", kind: "auto" },
    { n: 2, title: "Check by exception", sub: "limits, OOS, missing steps, e-sig completeness", kind: "auto" },
    { n: 3, title: "Draft disposition", sub: "exception report + recommended release/hold", kind: "auto" },
    { n: 4, title: "HUMAN GATE (QA)", sub: "QA reviewer approves release / reject", kind: "gate" },
    { n: 5, title: "Append-only audit", sub: "every check + decision logged", kind: "audit" },
  ],
  pipelineCards: stdCards("batch release"),
  arch: {
    users: "QA review & release",
    sor: "MES / electronic batch records",
    ext: "LIMS (QC results)",
    runtime: [
      { t: "Event worker + EventBridge", s: "on batch completion", color: C_COMPUTE },
      { t: "Review/exception agent + limit checker", color: C_COMPUTE },
      { t: "MCP auth gateway", s: "all outbound tool calls", color: C_INTEG },
    ],
    data: [
      { t: "Aurora / DynamoDB", s: "batch + review state", color: C_MODEL },
      { t: "DynamoDB audit", s: "append-only", color: C_INTEG },
      { t: "S3 Object Lock", s: "WORM disposition", color: C_STORAGE },
      { t: "Secrets Manager", s: "scoped tokens", color: C_STORAGE },
    ],
    legend: "1 QA sign-in   2 SAML federation (MFA at IdP; Cognito issues JWT)   3 authenticated session to review console   4 MES/EBR + LIMS reads over private connectivity   5 EventBridge triggers review on batch completion   6 model calls reach Bedrock + Guardrails only over the private VPC endpoint (PrivateLink)   7 every flag, exception, and release decision persisted to append-only audit (21 CFR Part 11)   8 connectors reachable only through the governed MCP gateway",
  },
  proofStats: [
    { big: "~80%", label: "batch-release time cut with review by exception", tag: "[sector-press/estimate]" },
    { big: ">50%", label: "deviation reduction at a benchmarked biopharma site", tag: "[industry-research — McKinsey]" },
    { big: "#2 cited", label: "211.192 record-review is a top FDA warning-letter finding", tag: "[gov/peer-reviewed]" },
    { big: "36 tests", label: "passing with no API key (built to flagship depth)", tag: "[built]" },
  ],
  deploySteps: [
    "Provision KMS CMK + per-customer validated VPC / network.",
    "Stand up Cognito SAML→JWT federation (operator / QA-reviewer roles).",
    "Front with CloudFront + WAF, ALB TLS 1.3.",
    "Deploy the agent + grant tools via the MCP gateway (deny-by-default).",
    "Connect MES / electronic batch records + LIMS; wire EventBridge on batch completion.",
    "Enable S3 Object Lock + append-only audit; run smoke + QA-gate test.",
  ],
  deployOneLiner: "CloudFormation quick-deploy provisions the isolated environment + dual MCP gateway + connector Lambdas (mes/lims); connect MES/EBR + LIMS. AWS-native Strands + Step Functions rebuild included.",
  notes: {
    s1: "[00:20] Title. Agent 09 is BUILT to flagship depth — a LangGraph app (review-by-exception scan + QA gate), 36 passing tests, an AWS-native Strands + Step Functions rebuild, and a four-document doc set. It extends the suite to CMC/manufacturing with the same governed review-and-approve pattern and a QA release gate.",
    s2: "[00:45] Hook. Lead with FDA's 62% (gov). The 48-hr review and $14K deviation figures are sector estimates — flag them. The story: the most regulated, highest-cost manual review in the plant.",
    s3: "[01:10] Issue + cost. Modeled ~$420K/yr investigation labor with arithmetic visible — before scrapped-batch cost. Bright line: QA owns and signs the release; the agent never releases a batch.",
    s4: "[01:35] Pipeline. Review by exception — the agent surfaces only what deviates. Human gate (QA) in red. Every flag traces to a record value.",
    s5: "[02:15] Architecture. EventBridge triggers review on batch completion. New connectors: MES/EBR + LIMS. Same governed spine + 21 CFR Part 11 audit. Customer provides MES/LIMS access and named QA approvers.",
    s6: "[02:45] Proof + deploy. RBE ~80% is trade-press (illustrative); the >50% deviation reduction is McKinsey. This is a roadmap deck — deployment follows the build (docs/specs/09). Close on the takeaway.",
  },
},
{
  num: "10", name: "Scientific Intelligence & Target Discovery",
  tagline: "synthesize literature, omics & patents into ranked, evidence-linked targets — a scientist owns the hypothesis  [roadmap]",
  runbook: "10-scientific-intelligence",
  deployRef: "docs/specs/10-scientific-intelligence.md (design spec — roadmap agent, Documented maturity)",
  hero: "FROM A MILLION PAPERS A YEAR TO RANKED TARGETS",
  valueProp: "A governed discovery copilot that synthesizes literature, omics, patents, and internal data into ranked, evidence-linked targets with full provenance — while a scientist owns the target hypothesis and every go/no-go decision.",
  hookStats: [
    { big: "~86%", label: "of drugs entering clinical testing fail; wrong target / lack of efficacy leads", tag: "[gov/peer-reviewed — Wong 2019]" },
    { big: "11%", label: "of landmark preclinical cancer studies were reproducible (Amgen)", tag: "[gov/peer-reviewed — Begley 2012]" },
    { big: ">1M / yr", label: "new papers added to PubMed (>35M total) — no team can read it all", tag: "[gov/peer-reviewed — NLM]" },
  ],
  issueBullets: [
    "Target evidence is spread across >35M papers, omics, patents, and internal data — no team can synthesize it manually.",
    "Poor target validation is a leading cause of the ~86% clinical failure rate.",
    "The preclinical evidence base is shaky — only ~11% of landmark cancer studies reproduced.",
    "Discovery-to-candidate runs ~3–6 years and hundreds of millions before a single patient.",
  ],
  costBig: "~$2.6B / drug",
  costMath: "Industry: ~$2.6B capitalized cost per approved drug (incl. failures); a typical preclinical program is ~$430M out-of-pocket over 3–6 years. Failed targets are the dominant driver.",
  costRisks: [
    "Years and hundreds of millions sunk into targets that fail in the clinic.",
    "Missed prior art / evidence that a competitor already acted on.",
  ],
  costTag: "[industry-research — DiMasi/Tufts; PhRMA]",
  brightLine: "the agent synthesizes and ranks evidence with full provenance; a scientist owns the target hypothesis and the go/no-go decision.",
  pipelineTagline: "Retrieve literature, omics, patents and internal data through a scoped gateway, synthesize and rank targets with provenance — then route the hypothesis to a scientist.",
  pipeline: [
    { n: 1, title: "Retrieve evidence", sub: "literature/omics/patents/internal via gateway + KB", kind: "auto" },
    { n: 2, title: "Synthesize & link", sub: "extract claims, link to source, de-duplicate", kind: "auto" },
    { n: 3, title: "Rank targets", sub: "score on evidence strength + tractability", kind: "auto" },
    { n: 4, title: "HUMAN GATE", sub: "scientist owns the hypothesis & go/no-go", kind: "gate" },
    { n: 5, title: "Append-only audit", sub: "full provenance + decisions logged", kind: "audit" },
  ],
  pipelineCards: stdCards("the target hypothesis"),
  arch: {
    users: "Discovery scientists & computational biology",
    sor: "ELN + internal data lake",
    ext: "Literature · omics · patents",
    runtime: [
      { t: "UI task (discovery console)", color: C_COMPUTE },
      { t: "Synthesis/ranking agent + provenance linker", color: C_COMPUTE },
      { t: "MCP auth gateway", s: "all outbound tool calls", color: C_INTEG },
    ],
    data: [
      { t: "Bedrock Knowledge Base", s: "approved corpus (RAG)", color: C_MODEL },
      { t: "DynamoDB audit", s: "append-only", color: C_INTEG },
      { t: "S3 Object Lock", s: "WORM rationale", color: C_STORAGE },
      { t: "Secrets Manager", s: "scoped tokens", color: C_STORAGE },
    ],
    legend: "1 scientist sign-in   2 SAML federation (MFA at IdP; Cognito issues JWT)   3 authenticated session to discovery console   4 ELN + internal data reads over private connectivity (least-privilege)   5 demand scales the agent workers   6 model calls reach Bedrock + Guardrails only over AWS PrivateLink; internal evidence never egresses to an external AI API after masking   7 full provenance + decisions persisted to append-only audit   8 connectors reachable only through the governed MCP gateway",
  },
  proofStats: [
    { big: "~18 mo", label: "AI novel-target → preclinical candidate (Insilico, company-reported)", tag: "[vendor — company-reported]" },
    { big: "~50%", label: "tissue-analysis time cut on AWS (AstraZeneca)", tag: "[vendor — AWS]" },
    { big: "provenance", label: "every claim linked to source — reproducibility by design", tag: "[design property]" },
    { big: "~$430M", label: "typical preclinical spend the workflow de-risks", tag: "[industry-research]" },
  ],
  deploySteps: [
    "Provision KMS CMK + per-customer validated VPC / network.",
    "Stand up Cognito SAML→JWT federation (scientist / comp-bio roles).",
    "Front with CloudFront + WAF, ALB TLS 1.3.",
    "Deploy the agent + grant tools via the MCP gateway (deny-by-default).",
    "Connect ELN + internal data; index literature/omics/patents into a Knowledge Base.",
    "Enable S3 Object Lock + append-only audit; run smoke + provenance/gate test.",
  ],
  deployOneLiner: "Roadmap agent (Documented): build per docs/CREATE-A-NEW-AGENT.md, then CloudFormation quick-deploy provisions the isolated environment + dual MCP gateway; connect ELN + index the corpus.",
  notes: {
    s1: "[00:20] Title. Agent 10 is a ROADMAP/expansion agent (Documented maturity) — cited design, not a built reference. It extends the suite to the FRONT of the lifecycle (R&D). Position to a different buyer: research informatics / computational biology, not the clinical/safety/quality buyer of the built eight.",
    s2: "[00:45] Hook. Lead with the peer-reviewed ~86% failure (Wong 2019) and the 11% reproducibility (Begley). PubMed scale is the overload pain. All three are gov/peer-reviewed.",
    s3: "[01:10] Issue + cost. The cost is the $2.6B/drug and ~$430M preclinical — failed targets are the dominant driver. Bright line: the scientist owns the hypothesis; provenance answers the reproducibility pain.",
    s4: "[01:35] Pipeline. The differentiator is provenance — every claim links to its source. Human gate (scientist) in red. This is evidence synthesis, not an autonomous decision.",
    s5: "[02:15] Architecture. New connectors: ELN + literature/omics/patents into a Knowledge Base. Internal evidence reaches Bedrock only over AWS PrivateLink and never egresses to an external AI API after masking. Customer provides ELN access and the corpus.",
    s6: "[02:45] Proof + deploy. Insilico/AstraZeneca figures are company-/vendor-reported — never lead with them. Roadmap deck — deployment follows the build (docs/specs/10). Close on the takeaway.",
  },
},
];

// ============================================================ SUITE OVERVIEW
function buildOverview(P) {
  // 1 TITLE
  {
    const s = P.addSlide(); s.background = { color: SQUID }; edgeBar(P, s);
    s.addText("HCLS AI Agent Suite", { x: 0.85, y: 1.7, w: 11.6, h: 1.3, fontFace: F_BOLD, fontSize: 48, bold: true, color: WHITE, align: "left", valign: "middle", margin: 0 });
    s.addText("Governed Agentic AI for Life Sciences — Built on AWS", { x: 0.87, y: 3.15, w: 11.4, h: 0.6, fontFace: F_BOLD, fontSize: 22, bold: true, color: ORANGE, align: "left", valign: "middle", margin: 0 });
    s.addText("Eight reference agents on one 21 CFR Part 11 / GxP-defensible platform — the agent isn't the product, the governance is.", { x: 0.88, y: 3.9, w: 11.4, h: 0.6, fontFace: F_TAG, fontSize: 16, italic: true, color: MUTEDLT, align: "left", valign: "middle", margin: 0 });
    s.addText("Executive Overview  ·  Built on AWS  ·  June 2026", { x: 0.88, y: 6.0, w: 11.4, h: 0.3, fontFace: F_REG, fontSize: 12, color: MUTEDLT, align: "left", valign: "middle", margin: 0 });
    s.addNotes("[00:30] Open with the thesis: everyone in life sciences is moving on AI, almost no one is governed. This suite is eight reference agents sharing ONE governed AWS control plane. For a CIO/CISO, the platform is the asset — the agents are interchangeable, regulated workloads on top of it.");
  }
  // 2 THESIS
  {
    const s = P.addSlide(); s.background = { color: SQUID }; edgeBar(P, s);
    s.addText("EVERYONE'S MOVING. FEW ARE GOVERNED.", { x: 0.85, y: 0.85, w: 11.8, h: 1.0, fontFace: F_BOLD, fontSize: 34, bold: true, color: WHITE, align: "left", valign: "middle", charSpacing: 0.5, margin: 0 });
    s.addText("In a workflow where a hallucinated number is a data-integrity defect, governance is the gap this platform closes.", { x: 0.88, y: 1.95, w: 11.3, h: 0.5, fontFace: F_TAG, fontSize: 15, italic: true, color: MUTEDLT, align: "left", valign: "middle", margin: 0 });
    const stats = [
      { big: "$60–110B", label: "/yr potential gen-AI value for pharma & medical products", tag: "[industry-research — McKinsey 2023]" },
      { big: "~5%", label: "of commercial life-sci firms have turned gen AI into real value", tag: "[industry-research — McKinsey 2024]" },
      { big: "Jan 2025", label: "FDA draft guidance on AI in regulatory decision-making (7-step credibility)", tag: "[gov/peer-reviewed — FDA]" },
    ];
    const cw = 3.62, gap = 0.32, x0 = 0.85, cy = 3.0, ch = 2.1;
    stats.forEach((st, i) => {
      const x = x0 + i * (cw + gap);
      s.addShape(P.shapes.RECTANGLE, { x, y: cy, w: cw, h: ch, fill: { color: SQUID2 }, line: { color: "3A485A", width: 1 } });
      s.addText(st.big, { x: x + 0.28, y: cy + 0.22, w: cw - 0.5, h: 0.85, fontFace: F_BOLD, fontSize: 34, bold: true, color: ORANGE, align: "left", valign: "middle", margin: 0 });
      s.addText(st.label, { x: x + 0.3, y: cy + 1.12, w: cw - 0.55, h: 0.65, fontFace: F_REG, fontSize: 12, color: "C9D2DC", align: "left", valign: "top", margin: 0 });
      tag(P, s, x + 0.3, cy + ch - 0.3, st.tag, true);
    });
    s.addText("The takeaway: this platform is the governance layer that lets a sponsor adopt AI as fast as the market — and defend it to an FDA/EMA inspector.", { x: 0.85, y: 5.5, w: 11.8, h: 0.7, fontFace: F_REG, fontSize: 14, italic: true, color: "C9D2DC", align: "left", valign: "middle", margin: 0 });
    footer(P, s, "HCLS AI Agent Suite  ·  Built on AWS  ·  June 2026", true);
    s.addNotes("[00:55] The frame the whole suite answers. McKinsey: $60–110B/yr of value but only ~5% have realized it. FDA's Jan 2025 draft guidance signals the regulator now expects a credibility framework. The gap between adoption and governance IS the opportunity.");
  }
  // 3 SHARED ARCHITECTURE
  slideArch(P, {
    archTitle: "Shared AWS Architecture & Traffic Flow",
    arch: {
      users: "Writers · safety · clinical · quality · MSL",
      sor: "Veeva · Argus · Medidata · QMS",
      ext: "Approved corpus · RWD · dictionaries",
      runtime: [
        { t: "UI task (per-agent console)", color: C_COMPUTE },
        { t: "Agent worker + EventBridge/SQS", s: "event-driven agents", color: C_COMPUTE },
        { t: "MCP auth gateway", s: "all outbound tool calls", color: C_INTEG },
      ],
      data: [
        { t: "Aurora / DynamoDB", s: "state", color: C_MODEL },
        { t: "DynamoDB audit", s: "append-only", color: C_INTEG },
        { t: "S3 Object Lock", s: "WORM", color: C_STORAGE },
        { t: "Secrets Manager", s: "scoped tokens", color: C_STORAGE },
      ],
      legend: "1 sign-in   2 SAML federation (MFA at IdP; Cognito issues JWT — no credentials in AWS)   3 authenticated session   4 systems-of-record read over private connectivity   5 queue/scale for event-driven agents   6 model calls reach Bedrock + Guardrails over a PrivateLink VPC endpoint (PHI masked first)   7 every action persisted to append-only audit (21 CFR Part 11)   8 tools reachable only through the governed MCP gateway",
    },
    notes: { s5: "[02:00] The shared platform — every agent inherits this. One control plane: CloudFront/WAF edge, Cognito federation, MCP authorization gateway (deny-by-default, short-lived scoped tokens), Bedrock + Guardrails over PrivateLink, HITL gate, S3 Object Lock + DynamoDB append-only audit, per-customer VPC + dedicated validated account. To the CISO: no PHI egress to external AI APIs after masking; least-privilege IAM throughout." },
  });
  // 4 & 5 PORTFOLIO
  function portfolioSlide(idxs, partLabel) {
    const s = P.addSlide(); s.background = { color: GRAYBG }; edgeBar(P, s);
    s.addText("The 8-Agent Portfolio" + (partLabel ? `  —  ${partLabel}` : ""), { x: 0.78, y: 0.35, w: 12, h: 0.6, fontFace: F_BOLD, fontSize: 28, bold: true, color: INK, align: "left", valign: "middle", margin: 0 });
    const cols = 2, cw = 5.78, ch = 2.55, gx = 0.78, gy = 1.25, gapx = 0.45, gapy = 0.4;
    idxs.forEach((ai, k) => {
      const a = AGENTS[ai];
      const col = k % cols, row = Math.floor(k / cols);
      const x = gx + col * (cw + gapx), y = gy + row * (ch + gapy);
      s.addShape(P.shapes.RECTANGLE, { x, y, w: cw, h: ch, fill: { color: CARD }, line: { type: "none" }, shadow: sh() });
      s.addShape(P.shapes.RECTANGLE, { x, y, w: 0.07, h: ch, fill: { color: ORANGE }, line: { type: "none" } });
      s.addText(`${a.num}`, { x: x + 0.28, y: y + 0.2, w: 1.0, h: 0.5, fontFace: F_BOLD, fontSize: 22, bold: true, color: ORANGE, align: "left", valign: "middle", margin: 0 });
      s.addText(a.name, { x: x + 0.95, y: y + 0.18, w: cw - 1.2, h: 0.6, fontFace: F_BOLD, fontSize: 14, bold: true, color: INK, align: "left", valign: "middle", lineSpacingMultiple: 0.95, margin: 0 });
      s.addText(a.tagline, { x: x + 0.3, y: y + 0.85, w: cw - 0.6, h: 0.62, fontFace: F_REG, fontSize: 10.5, italic: true, color: MUTED, align: "left", valign: "top", lineSpacingMultiple: 1.0, margin: 0 });
      s.addText([
        { text: "Headline:  ", options: { bold: true, color: INK } },
        { text: a.hookStats[0].big + " — " + a.hookStats[0].label, options: { color: INK } },
      ], { x: x + 0.3, y: y + 1.5, w: cw - 0.6, h: 0.55, fontFace: F_REG, fontSize: 10.5, align: "left", valign: "top", lineSpacingMultiple: 0.98, margin: 0 });
      s.addText([
        { text: "Cost of doing nothing:  ", options: { bold: true, color: ORANGED } },
        { text: a.costBig, options: { bold: true, color: ORANGED } },
      ], { x: x + 0.3, y: y + ch - 0.5, w: cw - 0.6, h: 0.4, fontFace: F_REG, fontSize: 11, align: "left", valign: "middle", margin: 0 });
    });
    footer(P, s, null, false);
    return s;
  }
  portfolioSlide([0, 1, 2, 7], "Land-first (document- & case-centric)").addNotes("[02:30] Portfolio part 1 — land-first agents: Regulatory Writing (01), Pharmacovigilance (02), Clinical Trial Ops/TMF (03), Medical Affairs MSL (08). These are document- and case-centric, measurable, and prove the control plane. 02 ships a live path. Walk the cost-of-nothing column for the CFO.");
  portfolioSlide([3, 4, 5, 6], "Higher-governance (sequence after)").addNotes("[03:00] Portfolio part 2 — higher-governance agents: Site/Patient Matching (04), Quality/CAPA (05), Protocol Design (06), RWE/HEOR (07). These touch enrollment, reportability, study design, and evidence, so they carry mandatory human gates and de-identification. Sequence after the platform is proven.");
  // 6 GOVERNANCE SPINE
  {
    const s = P.addSlide(); s.background = { color: GRAYBG }; edgeBar(P, s);
    s.addText("The Governance & Compliance Spine", { x: 0.78, y: 0.35, w: 12, h: 0.6, fontFace: F_BOLD, fontSize: 28, bold: true, color: INK, align: "left", valign: "middle", margin: 0 });
    s.addText("Every agent inherits the same controls — mapped to the regulations life-sciences buyers are inspected against.", { x: 0.8, y: 1.0, w: 12, h: 0.45, fontFace: F_TAG, fontSize: 13, italic: true, color: MUTED, align: "left", valign: "top", margin: 0 });
    const body = [
      ["21 CFR Part 11 (records / e-sig)", "Append-only audit; bound reviewer identity on every gate; system validation posture; KMS CMK encryption"],
      ["GxP / ALCOA+ (data integrity)", "Grounding verification; every figure traceable to source; prompt version pinning; tamper-evident lineage"],
      ["GVP / ICH E2B(R3) (safety)", "PHI masked before model calls; safety-physician gate on causality & reportability (Agent 02)"],
      ["ICH E6(R3) GCP (trials)", "Continuous TMF completeness; CRA gate on dispositions; inspection-ready audit (Agent 03)"],
      ["HIPAA / de-identification", "Safe Harbor / Expert Determination enforced at the gateway for any RWD use (Agents 04/07)"],
      ["FDA AI guidance (Jan 2025) + NIST AI RMF", "Risk-based credibility framing; Guardrails, explainable grounded output, framework-enforced HITL"],
    ];
    const ty = 1.6, rowH = 0.72, tw = 11.78, c0 = 3.95, x0 = 0.78;
    s.addShape(P.shapes.RECTANGLE, { x: x0, y: ty, w: tw, h: 0.45, fill: { color: SQUID }, line: { type: "none" } });
    s.addText("Regulation / framework", { x: x0 + 0.15, y: ty, w: c0 - 0.3, h: 0.45, fontFace: F_BOLD, fontSize: 12, bold: true, color: WHITE, valign: "middle", margin: 0 });
    s.addText("Mapped control on the platform", { x: x0 + c0 + 0.15, y: ty, w: tw - c0 - 0.3, h: 0.45, fontFace: F_BOLD, fontSize: 12, bold: true, color: WHITE, valign: "middle", margin: 0 });
    body.forEach((r, i) => {
      const y = ty + 0.45 + i * rowH;
      s.addShape(P.shapes.RECTANGLE, { x: x0, y, w: tw, h: rowH, fill: { color: i % 2 ? "E9ECEF" : CARD }, line: { color: LINE, width: 0.5 } });
      s.addShape(P.shapes.RECTANGLE, { x: x0 + c0, y, w: 0.012, h: rowH, fill: { color: LINE }, line: { type: "none" } });
      s.addText(r[0], { x: x0 + 0.15, y, w: c0 - 0.3, h: rowH, fontFace: F_BOLD, fontSize: 11, bold: true, color: SQUID, valign: "middle", align: "left", margin: 0 });
      s.addText(r[1], { x: x0 + c0 + 0.18, y, w: tw - c0 - 0.36, h: rowH, fontFace: F_REG, fontSize: 10.5, color: INK, valign: "middle", align: "left", lineSpacingMultiple: 0.98, margin: 0 });
    });
    footer(P, s, null, false);
    s.addNotes("[03:30] The compliance spine is the reason a CISO, QA head, or general counsel signs off. Each regulation life-sciences buyers are inspected against maps to a concrete control already in the platform — not a policy promise. 21 CFR Part 11, GxP/ALCOA+, GVP/E2B, ICH E6(R3), HIPAA de-identification, and the FDA Jan-2025 AI guidance + NIST AI RMF.");
  }
  // 7 MATURITY LADDER
  {
    const s = P.addSlide(); s.background = { color: GRAYBG }; edgeBar(P, s);
    s.addText("The Maturity Ladder", { x: 0.78, y: 0.35, w: 12, h: 0.6, fontFace: F_BOLD, fontSize: 28, bold: true, color: INK, align: "left", valign: "middle", margin: 0 });
    s.addText("Climb at the sponsor's own pace — each rung reuses the same governed control plane.", { x: 0.8, y: 1.0, w: 12, h: 0.45, fontFace: F_TAG, fontSize: 13, italic: true, color: MUTED, align: "left", valign: "top", margin: 0 });
    const rungs = [
      { t: "1 · Documented", b: "Architecture, workflow, and compliance design written and reviewed. Useful for discovery and architecture review." },
      { t: "2 · Demonstrated", b: "Runs end-to-end in demo mode (no API key, deterministic fixtures). Internal demos and customer workshops." },
      { t: "3 · Deployable", b: "CloudFormation + container contracts + CI pass; customer AWS account + Bedrock. Suitable for a pilot." },
      { t: "4 · Production-ready", b: "CSV/CSA complete, IdP integrated, connectors live, pen-test passed. The engagement milestone." },
    ];
    const bw = 2.82, gap = 0.18, x0 = 0.78, y = 1.7, bh = 3.6;
    rungs.forEach((r, i) => {
      const x = x0 + i * (bw + gap);
      const fill = [TEAL, C_COMPUTE, C_INTEG, SQUID][i];
      s.addShape(P.shapes.RECTANGLE, { x, y, w: bw, h: bh, fill: { color: fill }, line: { type: "none" }, shadow: shsm() });
      s.addText(r.t, { x: x + 0.22, y: y + 0.25, w: bw - 0.4, h: 0.7, fontFace: F_BOLD, fontSize: 17, bold: true, color: WHITE, align: "left", valign: "top", lineSpacingMultiple: 0.98, margin: 0 });
      s.addText(r.b, { x: x + 0.24, y: y + 1.1, w: bw - 0.45, h: bh - 1.3, fontFace: F_REG, fontSize: 12, color: "F2F6F8", align: "left", valign: "top", lineSpacingMultiple: 1.05, margin: 0 });
    });
    s.addText("The suite sits at Demonstrated + Deployable-by-design — 536 tests pass with no API key; production-readiness is the engagement.", { x: 0.78, y: 5.6, w: 11.8, h: 0.5, fontFace: F_REG, fontSize: 14, italic: true, color: INK, align: "left", valign: "middle", margin: 0 });
    footer(P, s, null, false);
    s.addNotes("[04:00] The maturity ladder is the honesty slide. We position every agent against four levels: Documented, Demonstrated, Deployable, Production-ready. The suite is Demonstrated + Deployable-by-design today — 536 automated tests pass with no API key. Production-readiness (CSV/CSA, live integration, pen-test) is the engagement, not a day-one claim.");
  }
  // 8 DEPLOYMENT
  {
    const s = P.addSlide(); s.background = { color: GRAYBG }; edgeBar(P, s);
    s.addText("Deployment — One Platform, Per-Customer Isolation", { x: 0.78, y: 0.35, w: 12, h: 0.6, fontFace: F_BOLD, fontSize: 26, bold: true, color: INK, align: "left", valign: "middle", margin: 0 });
    const steps = [
      ["Foundation", "Per-customer VPC + dedicated, validated AWS account; KMS CMK per data class; network to systems-of-record (PrivateLink / Direct Connect)."],
      ["Identity", "Cognito SAML→JWT federation with role scoping (writer / safety / CRA / quality / MSL / reviewer). No credentials stored in AWS."],
      ["Edge", "CloudFront + WAF; ALB TLS 1.3; Cognito auth at the edge."],
      ["Agent + tools", "Deploy the AgentCore/Fargate agent; grant tools via the deny-by-default MCP gateway with short-lived scoped tokens."],
      ["Connectors + data", "Wire Veeva / Argus / Medidata / QMS connectors and Secrets Manager; index approved corpus; add per-agent blocks (EventBridge, Step Functions HITL)."],
      ["Governance + go-live", "Bedrock Guardrails (mandatory); S3 Object Lock + DynamoDB append-only audit; CloudTrail / Security Hub / Config; smoke + HITL test."],
    ];
    const cw = 5.78, ch = 1.35, gx = 0.78, gy = 1.2, gapx = 0.45, gapy = 0.25;
    steps.forEach((st, k) => {
      const col = k % 2, row = Math.floor(k / 2);
      const x = gx + col * (cw + gapx), y = gy + row * (ch + gapy);
      s.addShape(P.shapes.RECTANGLE, { x, y, w: cw, h: ch, fill: { color: CARD }, line: { type: "none" }, shadow: shsm() });
      s.addText(`${k + 1}`, { x: x + 0.22, y: y + 0.18, w: 0.55, h: 0.5, fontFace: F_BOLD, fontSize: 20, bold: true, color: ORANGE, align: "left", valign: "top", margin: 0 });
      s.addText(st[0], { x: x + 0.78, y: y + 0.16, w: cw - 1.0, h: 0.4, fontFace: F_BOLD, fontSize: 13.5, bold: true, color: INK, align: "left", valign: "middle", margin: 0 });
      s.addText(st[1], { x: x + 0.78, y: y + 0.52, w: cw - 1.0, h: ch - 0.6, fontFace: F_REG, fontSize: 10, color: MUTED, align: "left", valign: "top", lineSpacingMultiple: 1.0, margin: 0 });
    });
    s.addText("Reference: docs/DEPLOY-QUICKSTART.md  ·  docs/DEPLOYMENT-HANDBOOK.md  ·  aws-native-reference/<agent>/DEPLOY.md", { x: 0.78, y: 6.0, w: 11.8, h: 0.35, fontFace: F_REG, fontSize: 10.5, italic: true, color: MUTED, align: "left", valign: "middle", margin: 0 });
    footer(P, s, null, false);
    s.addNotes("[04:30] Deployment is a repeatable six-stage path. The customer provides identity, network reachability, connectors, and approved content; the reference templates provide everything else. One CloudFormation master stack provisions connectors + dual MCP gateway + native/container agent in a new account in any Region. Per-customer isolation (dedicated validated account + VPC) is what regulated buyers require.");
  }
  // 9 LAND-AND-EXPAND
  {
    const s = P.addSlide(); s.background = { color: GRAYBG }; edgeBar(P, s);
    s.addText("Land-and-Expand", { x: 0.78, y: 0.35, w: 12, h: 0.6, fontFace: F_BOLD, fontSize: 28, bold: true, color: INK, align: "left", valign: "middle", margin: 0 });
    s.addText("Prove the governed control plane with document- and case-centric agents, then expand to higher-governance workloads on the same foundation.", { x: 0.8, y: 1.0, w: 12, h: 0.45, fontFace: F_TAG, fontSize: 13, italic: true, color: MUTED, align: "left", valign: "top", margin: 0 });
    const phases = [
      { t: "LAND", c: TEAL, agents: "01 Regulatory Writing · 02 Pharmacovigilance (live path) · 03 Trial Ops/TMF · 08 Medical Affairs", why: "Document- and case-centric, measurable. Proves identity, gateway, PHI masking, audit, and Guardrails in production." },
      { t: "EXPAND", c: C_COMPUTE, agents: "05 Quality/CAPA · 06 Protocol Design", why: "Add reportability and design-ownership gates on the now-proven control plane." },
      { t: "SCALE", c: SQUID, agents: "04 Site/Patient Matching · 07 RWE/HEOR", why: "Highest-governance: de-identified RWD, enforced at the gateway, with auditable lineage." },
    ];
    const y0 = 1.7, bh = 1.25, gap = 0.3;
    phases.forEach((p, i) => {
      const y = y0 + i * (bh + gap);
      s.addShape(P.shapes.RECTANGLE, { x: 0.78, y, w: 11.78, h: bh, fill: { color: CARD }, line: { type: "none" }, shadow: shsm() });
      s.addShape(P.shapes.RECTANGLE, { x: 0.78, y, w: 2.1, h: bh, fill: { color: p.c }, line: { type: "none" } });
      s.addText(p.t, { x: 0.78, y, w: 2.1, h: bh, fontFace: F_BOLD, fontSize: 22, bold: true, color: WHITE, align: "center", valign: "middle", margin: 0 });
      s.addText(p.agents, { x: 3.1, y: y + 0.18, w: 9.2, h: 0.5, fontFace: F_BOLD, fontSize: 13.5, bold: true, color: INK, align: "left", valign: "middle", margin: 0 });
      s.addText(p.why, { x: 3.1, y: y + 0.66, w: 9.2, h: 0.5, fontFace: F_REG, fontSize: 12, color: MUTED, align: "left", valign: "top", lineSpacingMultiple: 1.0, margin: 0 });
    });
    footer(P, s, null, false);
    s.addNotes("[05:00] Land-and-expand de-risks the buy. Land with the document- and case-centric agents (01/02/03/08) — they prove identity, the gateway, PHI masking, audit, and Guardrails. 02 ships a live path you can demo. Expand to reportability and design (05/06). Scale to the de-identified-RWD agents (04/07). Every phase reuses the same control plane — no re-architecting.");
  }
  // 10 COST OF INACTION SUMMARY
  {
    const s = P.addSlide(); s.background = { color: SQUID }; edgeBar(P, s);
    s.addText("The Suite-Level Cost of Inaction", { x: 0.85, y: 0.45, w: 11.8, h: 0.7, fontFace: F_BOLD, fontSize: 30, bold: true, color: WHITE, align: "left", valign: "middle", margin: 0 });
    s.addText("Per-agent cost of doing nothing, at a reference sponsor — substitute your own volumes.", { x: 0.88, y: 1.15, w: 11.4, h: 0.4, fontFace: F_TAG, fontSize: 14, italic: true, color: MUTEDLT, align: "left", valign: "top", margin: 0 });
    const shortNames = {
      "01": "Reg Writing", "02": "Pharmacovigilance", "03": "Trial Ops / TMF", "04": "Site / Patient",
      "05": "Quality / CAPA", "06": "Protocol Design", "07": "RWE / HEOR", "08": "Medical Affairs",
    };
    const cw = 3.62, ch = 1.18, gx = 0.85, gy = 1.7, gapx = 0.32, gapy = 0.28;
    AGENTS.forEach((a, k) => {
      const col = k % 3, row = Math.floor(k / 3);
      const x = gx + col * (cw + gapx), y = gy + row * (ch + gapy);
      s.addShape(P.shapes.RECTANGLE, { x, y, w: cw, h: ch, fill: { color: SQUID2 }, line: { color: "3A485A", width: 1 } });
      s.addText(`${a.num}  ${shortNames[a.num]}`, { x: x + 0.2, y: y + 0.14, w: cw - 0.4, h: 0.4, fontFace: F_BOLD, fontSize: 12, bold: true, color: "C9D2DC", align: "left", valign: "top", margin: 0 });
      s.addText(a.costBig, { x: x + 0.2, y: y + 0.55, w: cw - 0.4, h: 0.5, fontFace: F_BOLD, fontSize: 17, bold: true, color: ORANGE, align: "left", valign: "middle", margin: 0 });
    });
    s.addText("Several are modeled at a reference baseline (shown as such); 01/03/05/06 lean on direct published figures. None are guaranteed — they substitute the customer's actuals.", { x: 0.85, y: 6.35, w: 11.8, h: 0.5, fontFace: F_REG, fontSize: 10.5, italic: true, color: MUTEDLT, align: "left", valign: "middle", margin: 0 });
    s.addNotes("[05:30] The CFO summary slide. Eight cost-of-doing-nothing figures on one view. Be disciplined: several are modeled at a reference baseline (show the label), while 01 (delay NPV), 03 (Tufts day-of-delay), 05 (recall cost), and 06 (amendment cost) use direct published figures. None are guaranteed — they substitute the customer's own volumes.");
  }
  // 11 TAKEAWAY
  {
    const s = P.addSlide(); s.background = { color: SQUID }; edgeBar(P, s);
    s.addText("The Takeaway", { x: 0.85, y: 1.5, w: 11.6, h: 0.8, fontFace: F_BOLD, fontSize: 40, bold: true, color: WHITE, align: "left", valign: "middle", margin: 0 });
    s.addText([
      { text: "The agent isn't the product.  ", options: { bold: true, color: ORANGE } },
      { text: "The governed platform that makes it 21 CFR Part 11 / GxP-defensible and deployable on AWS is.", options: { color: WHITE } },
    ], { x: 0.87, y: 2.6, w: 11.4, h: 1.4, fontFace: F_BOLD, fontSize: 24, align: "left", valign: "top", lineSpacingMultiple: 1.1, margin: 0 });
    s.addText("Eight reference agents · one control plane · land-first with 01 / 02 / 03 / 08 · expand at your own pace.", { x: 0.88, y: 4.4, w: 11.4, h: 0.6, fontFace: F_TAG, fontSize: 16, italic: true, color: MUTEDLT, align: "left", valign: "middle", margin: 0 });
    s.addText("docs/DEPLOY-QUICKSTART.md  ·  docs/SUITE-ARCHITECTURE.md  ·  June 2026", { x: 0.88, y: 6.0, w: 11.4, h: 0.3, fontFace: F_REG, fontSize: 12, color: MUTEDLT, align: "left", valign: "middle", margin: 0 });
    s.addNotes("[06:00] Close on the thesis restated: the agent isn't the product — the governed platform is. That's what a sponsor actually buys, and what its FDA/EMA inspector actually evaluates. Recommend landing with 01/02/03/08 to prove the control plane, then expanding at their own pace. Hand off to the quickstart and architecture references. Invite the architecture deep-dive next.");
  }
}

// ============================================================ BUILD
const OUT = process.env.DECK_OUT || __dirname;
const fileNames = {
  "01": "HCLS-01-Regulatory-Writing.pptx",
  "02": "HCLS-02-Pharmacovigilance.pptx",
  "03": "HCLS-03-Clinical-Trial-Ops-TMF.pptx",
  "04": "HCLS-04-Site-Patient-Matching.pptx",
  "05": "HCLS-05-Quality-CAPA.pptx",
  "06": "HCLS-06-Protocol-Design.pptx",
  "07": "HCLS-07-RWE-HEOR.pptx",
  "08": "HCLS-08-Medical-Affairs-MSL.pptx",
  "09": "HCLS-09-Manufacturing-Batch-Review.pptx",
  "10": "HCLS-10-Scientific-Intelligence.pptx",
};

async function main() {
  for (const d of [...AGENTS, ...EXPANSION]) {
    const P = new pptxgen();
    P.layout = "LAYOUT_WIDE"; P.author = "HCLS AI Agent Suite"; P.title = `HCLS Agent ${d.num} — ${d.name}`;
    buildAgentDeck(P, d);
    await P.writeFile({ fileName: `${OUT}/${fileNames[d.num]}` });
    console.log("wrote", fileNames[d.num]);
  }
  const PO = new pptxgen();
  PO.layout = "LAYOUT_WIDE"; PO.author = "HCLS AI Agent Suite"; PO.title = "HCLS AI Agent Suite — Executive Overview";
  buildOverview(PO);
  await PO.writeFile({ fileName: `${OUT}/HCLS-Agentic-AI-Suite-Executive-Overview.pptx` });
  console.log("wrote HCLS-Agentic-AI-Suite-Executive-Overview.pptx");
}

main().catch((e) => { console.error(e); process.exit(1); });
