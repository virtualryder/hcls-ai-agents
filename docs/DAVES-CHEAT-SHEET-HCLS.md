# 🧾 Dave's Cheat Sheet for HCLS
### Everything a brand-new Life Sciences SA needs: how to pitch each agent, talk through the architecture, and deploy it — explained like you've never touched a command line.

> **How to use this sheet.** Read Part 0 once (the basics). Skim Part 1 so the repo stops looking scary. Parts 2–3 are what you *say* in the room. Part 4 is a card per agent. **Part 5 is the deploy — literally click-this, open-this, type-this.** Part 6 is "when it breaks." Part 7 is the one-page card to keep open during a demo.
>
> Anything in a `grey box` is something you **type or click exactly as written**. When you see `<like-this>`, replace the whole thing (including the `< >`) with your own value.

---

## Part 0 — Total beginner basics (read once)

**What is the "Terminal"?** A plain text window where you type commands instead of clicking buttons. You'll use it for 4 commands total. To open it:
- **Mac:** press `Cmd + Space`, type `Terminal`, press Enter.
- **Windows:** click Start, type `PowerShell`, press Enter.

**What is the "AWS Console"?** The Amazon Web Services website where you click around: <https://console.aws.amazon.com>. You log in with the account the customer (or your team) gives you.

**Copy/paste a command:** highlight it, `Cmd+C` (Mac) / `Ctrl+C` (Windows), click in the Terminal, then `Cmd+V` / `Ctrl+V`, and press **Enter** to run it. Enter = "go."

**"Run this" / "type this"** both mean: paste it into the Terminal and press Enter.

**The 5 free tools you install once** (think of them like apps). Don't worry about what they do yet:

| Tool | What it's for | Get it from |
|---|---|---|
| **Git** | downloads the code | <https://git-scm.com/downloads> |
| **Python 3.11+** | runs the agents | <https://www.python.org/downloads/> (tick "Add to PATH" on Windows) |
| **Node.js** | rebuilds the slide decks (optional) | <https://nodejs.org> (the "LTS" button) |
| **AWS CLI v2** | talks to Amazon from your Terminal | <https://aws.amazon.com/cli/> |
| **Docker Desktop** | only if you choose "container" mode (you won't, at first) | <https://www.docker.com/products/docker-desktop/> |

**Check a tool installed correctly** — type these one at a time; each should print a version number, not an error:
```
git --version
python3 --version
aws --version
```

That's it. You now know everything Part 5 assumes.

---

## Part 1 — The repo, in plain English (it's not as complex as it looks)

A "repo" is just a **folder of folders**. Here's the whole thing, what each part is, and — the important column — **whether you ever touch it.**

| Folder / file | What it is (plain English) | Do you touch it? |
|---|---|---|
| `README.md` | The front page. Start here. | **Read it** |
| `01-…-agent/` … `09-…-agent/` | The **nine agents** — each is one workflow (one folder per agent). | Only to **demo one** (Part 5A) |
| `platform_core/` | The shared "engine" all agents use (the security gateway, audit trail, PHI masking). Built once, reused by all. | **No** — it just works |
| `aws-native-reference/` | The same agents rebuilt the "AWS-native" way (Step Functions). This is what actually **deploys** to AWS. | No (the deploy script uses it) |
| `infra/cloudformation/` | The **deploy recipe** — files that tell AWS what to build. | No (the script points at them) |
| `scripts/` | The **two buttons**: `build_lambdas.sh` and `deploy.sh`. | **Yes — you run these** |
| `decks/` | The **sales slide decks** (PowerPoint + PDF), one per agent + an overview + a CIO deck. | **Yes — you present these** |
| `gtm/` | "Go-to-market": the **cited sources** for every stat, a **demo script**, and an **ROI calculator** (Excel). | **Yes — your proof + numbers** |
| `docs/` | All the guides — including **this one**, the deploy quickstart, the FAQ, and the architecture. | **Yes — your reference** |
| `offerings/` | Sales paperwork: battlecard, pricing/TCO, SOW template, objection handling. | **Yes — when scoping a deal** |
| `governance/` | The tests + safety checks (grounding, red-team, human-gate tests). Proof it behaves. | No (just cite "503 tests pass") |
| `runbooks/` | What ops does *after* go-live (incident, disaster recovery). | Later |
| `Makefile` | Shortcuts. `make decks`, `make roi`, `make build-lambdas`. | Optional |

**The mental model:** the **agents** are the apps, the **platform_core** is the engine they share, **scripts/** are the two buttons that put it on AWS, and **decks/ + gtm/ + offerings/** are your selling kit.

> **The only places you'll ever go:** `decks/` (present), `gtm/` (proof + numbers), `docs/` (this sheet + the quickstart), and `scripts/` (the two buttons). Everything else runs itself.

---

## Part 2 — The 60-second pitch (say this first, every time)

> **"The agents aren't the product — the governed platform that makes them deployable, auditable, and compliant is."**

Then: *"We give a systems integrator a compliant, auditable head start across nine high-value life-sciences workflows. Every agent **drafts, checks, and recommends** — but a **named human signs every consequential decision**, every action is logged to a tamper-evident, 21 CFR Part 11 audit trail, and patient data never leaves the customer's AWS account. It runs on Amazon Bedrock, in their VPC, behind one governed gateway."*

**The one idea to land:** ungoverned AI is a demo; **governed** AI is deployable in a regulated company. The governance is the value.

**The "bright line" (your safety promise):** the AI never decides the regulated thing — what gets *submitted*, the *reportable case*, the *batch release*, what *reaches a doctor*. A qualified human does, and the system *forces* that pause.

**Three buyers, three one-liners:**
- **CIO:** *"One control plane carries all nine workloads — the platform is the asset; agents are interchangeable workloads on top."*
- **CISO / CSO:** *"The controls live in the gateway, **outside** the model — a prompt can't turn them off."*
- **Director of Architecture:** *"It's real and deployable — CloudFormation, in-VPC Bedrock, a Step Functions human gate — and the gaps are written down, not hidden."*

---

## Part 3 — The architecture, explained ONCE (every agent shares it)

Every agent uses the **same picture**. Learn it once and you can talk through any agent's architecture slide. Here it is in plain English, left to right:

```
   THE CUSTOMER / OUTSIDE                 INSIDE THE CUSTOMER'S OWN AWS ACCOUNT (their private cloud)
 ┌───────────────────────┐    ┌──────────────────────────────────────────────────────────────────┐
 │  People (writers,     │    │  EDGE          PRIVATE WORKER         BRAIN (model)     MEMORY     │
 │  safety, QA, MSLs)    │ ─▶ │  CloudFront ─▶ The Agent ─▶ MCP   ─▶  Amazon Bedrock  ─▶ Audit log │
 │  Login (Okta/Entra)   │    │  + WAF + login  worker      GATEWAY   (Claude) +        (DynamoDB) │
 │  Their systems        │ ◀─ │                 (does the   (the       Guardrails       + S3 WORM  │
 │  (Veeva, Argus, MES…) │    │                  work)      bouncer)   PHI masked       (locked)   │
 └───────────────────────┘    └──────────────────────────────────────────────────────────────────┘
```

**The 8-step "traffic flow" (the numbered circles on the slide) — say it like this:**

1. **A person signs in** (a medical writer, a safety physician, a QA reviewer…).
2. **Their identity is verified** by the customer's own login system (Okta / Microsoft Entra). No passwords are stored in AWS.
3. **They reach the agent** through a secure front door (CloudFront + a web firewall).
4. **The agent reads the customer's systems** (Veeva, Argus, Medidata, MES…) over a **private** connection — data never crosses the public internet.
5. **The work scales automatically** — more cases, more workers, no one re-architects.
6. **The AI runs *inside* the customer's account** (Amazon Bedrock + Guardrails). **Patient data is masked before it ever reaches the model**, and it never leaves their VPC.
7. **Every action is written to a locked, append-only audit trail** — who, when, what data, which model version. This is the 21 CFR Part 11 evidence.
8. **Nothing reaches a customer system except through the "MCP gateway"** — the bouncer that checks "is this agent allowed to do this, on behalf of *this* person?" and **pauses for a human signature** on anything risky.

**The two things to point at on the slide:**
- The **MCP gateway box** (the bouncer): *"deny-by-default. An agent can never do more than the human it's acting for. Writes pause for a human."*
- The **red HUMAN GATE box** in the workflow: *"this is enforced by the software, not a policy PDF — it literally won't continue without a signature."*

**Per-agent differences are tiny** — same picture, different systems plugged into the left and one specialty block. Those are in Part 4.

---

## Part 4 — One card per agent (your pocket reference)

Each card: who you're selling to, the cited pain, the cost of inaction, your one-liner, the bright line (what the AI never decides), and the systems it plugs in. **Every stat traces to `gtm/HCLS-DECK-SOURCES.md`.** Open the matching deck `decks/HCLS-0X-*.pptx` while you talk.

### 01 · Regulatory Writing & Intelligence
- **Talk to:** Head of Regulatory, Medical Writing leads, R&D CIO.
- **Pain (cited):** $2.6B per approved drug `[gov]`; writers spend their time hunting evidence, and a hallucinated number is a data-integrity defect.
- **Cost of doing nothing:** ~$60M lost **per month** of submission delay (a $1B asset) `[industry]`.
- **Your line:** *"It drafts and assembles submission sections with every figure traceable to source — a qualified writer signs off on what gets submitted."*
- **Bright line:** the AI never decides **what gets submitted**.
- **Plugs into:** Veeva Vault RIM/DMS; FDA/EMA/PMDA guidance.

### 02 · Pharmacovigilance — ICSR Case Intake  *(best live demo)*
- **Talk to:** Head of Drug Safety / PV, CISO.
- **Pain (cited):** ~28M FAERS reports and climbing `[gov]`; case intake eats 40–85% of PV budgets.
- **Cost of doing nothing:** ~$2.0M/yr modeled case-intake cost `[modeled]`.
- **Your line:** *"It triages, de-duplicates, MedDRA-codes, and drafts the E2B narrative — a safety physician validates the reportable case."*
- **Bright line:** the AI never decides **the reportable case / causality**.
- **Plugs into:** Argus / Veeva Safety, MedDRA, WHO Drug. **This one ships a real Bedrock + connector path — demo it live.**

### 03 · Clinical Trial Ops & TMF
- **Talk to:** Head of Clinical Operations, CRAs.
- **Pain (cited):** ~$800K/day in lost sales **per day of trial delay** (+~$40K/day direct) `[gov]`; 57% of TMFs still on paper/simple e-files.
- **Cost of doing nothing:** ~$25.7M per 30-day database-lock slip `[modeled]`.
- **Your line:** *"It watches TMF completeness and EDC query backlog continuously and drafts the work — a CRA approves every disposition."*
- **Bright line:** the AI never decides **the TMF/query disposition**.
- **Plugs into:** Veeva eTMF, CTMS, Medidata EDC.

### 04 · Site Selection & Patient Matching
- **Talk to:** Feasibility / Clinical Operations, Architecture (data privacy).
- **Pain (cited):** ~80% of trials miss their enrollment timeline `[estimate]`; ~1 in 5 sites enroll no one.
- **Cost of doing nothing:** ~$24M/launch modeled from a 30-day pull-in `[modeled]`.
- **Your line:** *"It ranks sites on real performance and sizes cohorts on de-identified real-world data — humans pick sites and clinicians confirm eligibility."*
- **Bright line:** the AI never decides **site selection or patient eligibility**.
- **Plugs into:** CTMS history, de-identified RWD (de-identification enforced at the gateway).

### 05 · Quality / CAPA & Complaints
- **Talk to:** VP Quality, QA leadership.
- **Pain (cited):** CAPA is the **#1-cited FDA device 483 clause** `[gov]`.
- **Cost of doing nothing:** $10M–$100M per recall `[industry]`.
- **Your line:** *"It triages complaints, drafts root-cause and CAPA, and flags reportability — a quality owner approves classification and closure."*
- **Bright line:** the AI never decides **the CAPA disposition / reportability**.
- **Plugs into:** TrackWise / Veeva Quality, complaint databases.

### 06 · Clinical Protocol Design & Feasibility
- **Talk to:** Clinical Development, Medical leads.
- **Pain (cited):** ~57% of protocols amended, ~45% avoidable `[industry]`.
- **Cost of doing nothing:** ~$535K per avoidable Phase III amendment `[industry]`.
- **Your line:** *"It drafts protocol sections grounded in current guidance and links feasibility to real-world data — clinical leads own the design."*
- **Bright line:** the AI never decides **the protocol design**.
- **Plugs into:** RIM guidance, CTMS history, RWD.

### 07 · Real-World Evidence / HEOR
- **Talk to:** HEOR / Epidemiology, Market Access, Architecture.
- **Pain (cited):** ~45% of analyst time goes to data prep, not analysis `[estimate]`.
- **Cost of doing nothing:** ~$1.3M/yr of non-analytic labor per 20-person team `[modeled]`.
- **Your line:** *"It builds cohorts, translates code systems, and tracks lineage so analysts analyze — an epidemiologist approves the study."*
- **Bright line:** the AI never decides **the analysis or conclusions**.
- **Plugs into:** claims / registry / RWD; ICD/SNOMED/RxNorm.

### 08 · Medical Affairs / MSL Copilot
- **Talk to:** Medical Affairs, Compliance, Commercial.
- **Pain (cited):** MLR review drags weeks→months `[estimate]`; off-label promotion = billions in FCA settlements (GSK $3B, Pfizer $2.3B) `[gov]`.
- **Cost of doing nothing:** missed launch windows + off-label liability.
- **Your line:** *"It drafts on-label, evidence-grounded responses with off-label blocked *technically* — MLR approves before anything reaches a doctor."*
- **Bright line:** the AI never decides **what reaches an HCP**.
- **Plugs into:** Veeva CRM/DMS, approved-label Knowledge Base.

### 09 · Manufacturing Batch-Review  *(CMC / GxP)*
- **Talk to:** VP Manufacturing/Quality, QA release, Site Quality.
- **Pain (cited):** **62% of US drug shortages trace to manufacturing/quality** `[gov]`; batch review runs ~48 hrs each.
- **Cost of doing nothing:** ~$420K/yr modeled investigation labor `[modeled]`, before scrapped-batch cost ($1–2M+ each).
- **Your line:** *"It reviews the electronic batch record by exception — flags only what deviated — and a QA reviewer signs the release/reject."*
- **Bright line:** the AI never decides **batch release**.
- **Plugs into:** MES / electronic batch records, LIMS.

### 10 · Scientific Intelligence & Target Discovery  *(ROADMAP — not built yet)*
- **Status:** a **cited deck + design spec only** (Documented maturity). Use it to show vision and the R&D end of the lifecycle; **don't promise code**.
- **Pain (cited):** ~86% of programs entering the clinic fail `[gov]`; only ~11% of landmark preclinical studies reproduced.
- **Note:** different buyer (research informatics), and it's the one agent not yet built.

---

## Part 5 — DEPLOY: click this, open this, run this

There are **two ways** to show this working. Do **5A first** (5 minutes, no AWS, impossible to break). Do **5B** when a customer gives you an AWS account.

> **First, get the code onto your computer (do this once, used by both paths):**
> 1. Open your **Terminal** (Part 0).
> 2. Type this and press Enter (downloads the repo into a folder called `hcls-ai-agents`):
>    ```
>    git clone https://github.com/virtualryder/hcls-ai-agents.git
>    ```
>    *No Git? Instead go to the repo web page → green **Code** button → **Download ZIP** → unzip it.*
> 3. Go into the folder:
>    ```
>    cd hcls-ai-agents
>    ```
>    (`cd` = "change directory" = "go into this folder." You are now "inside" the repo.)

---

### 5A — The 5-minute laptop demo (no AWS account, nothing to break)

This runs one agent on **your own laptop** with fake (but realistic) data. Perfect for "show me it works" before any cloud setup.

1. **Go into one agent's folder.** (Pharmacovigilance is the best demo.)
   ```
   cd 02-pharmacovigilance-agent
   ```
2. **Install what it needs** (one time, ~2 min — it downloads helper libraries):
   ```
   pip install -r requirements.txt
   ```
   *If `pip` says "not found," try `pip3` instead. If it complains about "externally managed," add ` --break-system-packages` to the end.*
3. **Start it.**
   - **Mac / Linux:**
     ```
     EXTRACT_MODE=demo streamlit run app.py
     ```
   - **Windows (PowerShell):**
     ```
     $env:EXTRACT_MODE="demo"; streamlit run app.py
     ```
4. **What you'll see:** your web browser pops open to a page like `http://localhost:8501` with the agent's dashboard. Click a sample case → watch it triage, code, and draft → it **stops at the human gate** → you approve → it finalizes and shows the audit trail. **That pause is the whole story** — point at it.
5. **To stop it:** click back in the Terminal and press `Ctrl + C`.

> `EXTRACT_MODE=demo` means "use fake data, no AI key needed." This is exactly how the **503 automated tests** run. You can demo the suite with zero cloud setup.

---

### 5B — The real AWS deploy (into a customer's account)

> **Windows users:** the deploy uses shell scripts (`.sh`). Run them from **"Git Bash"** (it installed automatically with Git — search your Start menu for *Git Bash*), **not** PowerShell. Mac users: the normal Terminal is fine.
>
> **Time:** ~30–60 min once Bedrock is switched on. **Cost:** a few dollars/day in a dev account.

#### Step 1 — Install the 5 tools (Part 0) and confirm they work
```
aws --version
python3 --version
git --version
```
Each should print a version. If `aws` errors, reinstall the AWS CLI from Part 0.

#### Step 2 — Log your computer into the customer's AWS account
You need an **Access Key** and **Secret Key** — ask the customer's cloud admin for an IAM user with deploy permissions (the exact permission list is in `docs/AWS-ACCOUNT-PREREQUISITES.md` §1). Then type:
```
aws configure
```
It will ask four things — paste each and press Enter:
- **AWS Access Key ID:** `<the key they gave you>`
- **AWS Secret Access Key:** `<the secret they gave you>`
- **Default region name:** `us-east-1`  *(unless they told you another)*
- **Default output format:** `json`

**Confirm you're in the right account:**
```
aws sts get-caller-identity
```
**What you'll see:** a block with an `Account` number. Check it's the **customer's** account before going further.

#### Step 3 — Turn on the AI model (Amazon Bedrock) — this is clicks, not typing
1. Open <https://console.aws.amazon.com> and log in.
2. In the top search bar type **Bedrock**, click **Amazon Bedrock**.
3. Top-right: make sure the **Region** says **N. Virginia (us-east-1)** (match Step 2).
4. Left menu → **Model access** → **Modify model access** (or **Enable specific models**).
5. Tick the **Anthropic Claude** models (Sonnet + Haiku) → **Next** → **Submit**.
6. Wait until they show **Access granted** (usually instant, occasionally up to a few hours).

> Skip this and every AI call fails with "AccessDenied." It's the #1 missed step.

#### Step 4 — Build the deployable code bundles (one command)
From inside the `hcls-ai-agents` folder, build the agent you want (here, Pharmacovigilance — swap in any agent id like `09-manufacturing-batch-review`):
```
bash scripts/build_lambdas.sh 02-pharmacovigilance
```
**What you'll see:** lines ending in `-> …/connector.zip` and `-> …/lambdas.zip`. That's it packaging the code **with its dependencies** so AWS can run it.

#### Step 5 — Deploy (one command)
Pick two **storage bucket names** — they must be **all-lowercase, no spaces, and globally unique** (add your company + some numbers). The script creates them for you. Then:
```
CFN_BUCKET=acme-hcls-cfn-2026 CODE_BUCKET=acme-hcls-code-2026 \
  bash scripts/deploy.sh 02-pharmacovigilance dev portable native
```
**Read the last line like this:**

| Word | Means | Beginner default |
|---|---|---|
| `02-pharmacovigilance` | which agent | any agent id (`09-manufacturing-batch-review`, etc.) |
| `dev` | which environment | `dev` |
| `portable` | which gateway style | **`portable`** (works in every Region — always start here) |
| `native` | how the agent runs | **`native`** (serverless, no Docker needed) |

**What you'll see:** lots of `==>` progress lines, then a **table of Outputs** (`GatewayEndpoint`, `AuditTable`, `GuardrailId`, a State Machine ARN). Outputs = **success.** This took ~5–15 minutes and built the whole isolated environment (network, security, audit store, gateway, and the agent).

#### Step 6 — Watch it build (optional, reassuring — clicks)
1. AWS Console → search **CloudFormation** → click it.
2. You'll see a stack named `hcls-dev-02-pharmacovigilance`. Green **CREATE_COMPLETE** = done. (Click it → **Events** to watch live.)

#### Step 7 — Prove the human gate works (the money moment)
Grab the agent's workflow and start a sample run:
```
SM_ARN=$(aws cloudformation describe-stacks --stack-name hcls-dev-02-pharmacovigilance \
  --query "Stacks[0].Outputs[?contains(OutputKey,'StateMachine')].OutputValue" --output text)

aws stepfunctions start-execution --state-machine-arn "$SM_ARN" \
  --input file://aws-native-reference/02-pharmacovigilance/sample_input.json
```
**What you'll see:** it runs and then **PAUSES** at the human gate — *that is correct and is the point.* It will not finish until a qualified reviewer approves. (The exact approve command — sending the reviewer's signature — is in `docs/DEPLOY-QUICKSTART.md` §6; it's a 1-line `send-task-success` call. Treat that section as the "advanced" finish.)

#### Step 8 — Show the audit trail (your 21 CFR Part 11 proof)
```
aws dynamodb scan --table-name hcls-dev-audit --max-items 5
```
**What you'll see:** locked, append-only entries — who, when, what data, which model — with patient data masked. *"This is the inspector's evidence."*

#### Step 9 — Clean up a dev account when done
```
aws cloudformation delete-stack --stack-name hcls-dev-02-pharmacovigilance
```
> The **audit table** and **locked S3 records** are kept on purpose (regulated records must survive). Delete those by hand, deliberately, only in dev.

> **Want the deep version with screenshots?** `docs/DEPLOY-QUICKSTART.md` (short + opinionated) and `docs/DEPLOYMENT-HANDBOOK.md` (full click-through). This cheat sheet is the friendly on-ramp to those.

---

## Part 6 — When it breaks (don't panic — it's almost always one of these)

| What you see | What it means | What to do |
|---|---|---|
| `AccessDenied` mentioning Bedrock | You didn't switch on the AI model | Do **Step 3** (turn on Bedrock model access) and re-run |
| `command not found: aws` (or git/python) | The tool isn't installed or not on PATH | Reinstall from Part 0; on Windows re-run the installer and tick "Add to PATH" |
| `pip` says "externally managed environment" | Your Python is protected | Add ` --break-system-packages` to the end of the pip command |
| On Windows, the deploy script errors weirdly | You ran a `.sh` script in PowerShell | Re-run it in **Git Bash** (Part 5B intro) |
| `BucketAlreadyExists` | Your bucket name isn't unique | Pick new `CFN_BUCKET`/`CODE_BUCKET` names (add more numbers) |
| Stack fails on `AWS::BedrockAgentCore::*` | This Region doesn't have AgentCore | You're already using `portable` — if not, switch to it (it works everywhere) |
| `ImportError` in a Lambda | The code zip missed its dependencies | Re-run **Step 4** (`build_lambdas.sh`) — it bundles the deps |
| The run is "stuck" at the human gate | **Working as designed** | That pause is the human-approval gate; approve it (DEPLOY-QUICKSTART §6) |
| A tool call says `DENY` | The user's role isn't allowed that tool | Correct behavior — it's the least-privilege gateway doing its job |

**Golden rule:** if you're unsure, you broke nothing. Re-running the build (Step 4) and deploy (Step 5) is safe — they just update.

---

## Part 7 — The one-page card (keep this open during a customer session)

**THE PITCH (say first):** *"The agents aren't the product — the governed platform that makes them deployable, auditable, and 21 CFR Part 11-compliant is. Nine workflows, one control plane, every consequential decision signed by a human, all inside the customer's AWS account."*

**THE ARCHITECTURE (point at the slide):** person → login (their IdP) → secure edge → the agent → **MCP gateway (the bouncer)** → **Bedrock AI in-VPC (PHI masked)** → **locked audit trail**. The red box = the **human gate** the software enforces.

**WHICH AGENT FOR WHICH ROOM:**
- Safety/PV → **02** (and it's your best **live** demo)
- Regulatory → **01** · Clinical Ops → **03** · Quality → **05** · Manufacturing → **09** · Medical Affairs → **08**

**DEMO WITH NO CLOUD (5 min):**
```
cd hcls-ai-agents/02-pharmacovigilance-agent
pip install -r requirements.txt
EXTRACT_MODE=demo streamlit run app.py      # Windows: $env:EXTRACT_MODE="demo"; streamlit run app.py
```

**DEPLOY TO AWS (the 6 commands):**
```
git clone https://github.com/virtualryder/hcls-ai-agents.git
cd hcls-ai-agents
aws configure                                  # paste keys; region us-east-1
# (then: Console → Bedrock → Model access → enable Claude)
bash scripts/build_lambdas.sh 02-pharmacovigilance
CFN_BUCKET=acme-hcls-cfn-2026 CODE_BUCKET=acme-hcls-code-2026 \
  bash scripts/deploy.sh 02-pharmacovigilance dev portable native
```
**Success = a table of Outputs.** Then `aws dynamodb scan --table-name hcls-dev-audit --max-items 5` shows the audit proof.

**YOUR SELLING KIT:** decks in `decks/` · cited proof in `gtm/HCLS-DECK-SOURCES.md` · numbers in `gtm/roi-calculator/` · 25-min demo script in `gtm/DEMO-STORYBOARD.md` · objections in `offerings/OBJECTION-HANDLING.md`.

**THREE THINGS THE CUSTOMER MUST OWN (say it honestly):** a funded SI engagement (not a product), their GxP/Part 11 quality program + login + reviewers, and budget for validation + a pen test before go-live.

---

*Dave's Cheat Sheet — HCLS AI Agent Suite. Companion to `docs/SA-SE-ENABLEMENT-GUIDE.md` (selling) and `docs/DEPLOY-QUICKSTART.md` (deploying). If a command here ever disagrees with the quickstart, the quickstart wins — tell Dave to update this sheet.*
