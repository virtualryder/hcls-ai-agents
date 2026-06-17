import os, html, datetime, markdown, cairosvg
from pathlib import Path
from weasyprint import HTML

ROOT=Path(__file__).resolve().parents[2]
CONSOLE=ROOT/"docs/assets/console"
OUTDIR=ROOT/"deliverables/agent-handbooks"; OUTDIR.mkdir(parents=True, exist_ok=True)

# ---------- console mockup primitives (shared chrome) ----------
W,H=1320,760; UIW=980
INK="#232F3E"; INK2="#1B2531"; PAGE="#F2F3F3"; PANEL="#FFFFFF"; BORD="#D5DBDB"
TXT="#16191F"; MUT="#5F6B7A"; LINK="#0073BB"; ORANGE="#EC7211"; AMBER="#FF9900"
SELBG="#F1FAFF"; SELBD="#0073BB"; GREEN="#1D8102"; REDP="#D13212"
def esc(s): return html.escape(str(s))
def rect(x,y,w,h,fill,rx=0,stroke=None,sw=1):
    s=f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" rx="{rx}"'
    if stroke: s+=f' stroke="{stroke}" stroke-width="{sw}"'
    return s+'/>'
def text(x,y,t,size=14,fill=TXT,bold=False,anchor="start"):
    w='font-weight="700"' if bold else ''
    return f'<text x="{x}" y="{y}" font-family="Helvetica, Arial, sans-serif" font-size="{size}" fill="{fill}" {w} text-anchor="{anchor}">{esc(t)}</text>'
def badge(x,y,n):
    return (f'<circle cx="{x}" cy="{y}" r="15" fill="{AMBER}" stroke="#FFFFFF" stroke-width="2"/>'
            f'<text x="{x}" y="{y+5}" font-family="Helvetica, Arial" font-size="15" font-weight="700" fill="#232F3E" text-anchor="middle">{n}</text>')
def button(x,y,w,label,primary=True,h=34):
    fill=ORANGE if primary else "#FFFFFF"; tc="#FFFFFF" if primary else "#16191F"
    st=f' stroke="{BORD}" stroke-width="1"' if not primary else ''
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="{fill}"{st}/>'+text(x+w/2,y+h/2+5,label,14,tc,True,"middle")
def field(x,y,w,label,value,h=34):
    return text(x,y-8,label,12,MUT,True)+rect(x,y,w,h,"#FFFFFF",4,BORD,1)+text(x+10,y+h/2+5,value,13,TXT)
def check(x,y,on=True):
    s=rect(x,y,18,18,(ORANGE if on else "#FFFFFF"),3,(ORANGE if on else "#879596"),1.5)
    if on: s+=f'<path d="M {x+4} {y+9} l 3 4 l 7 -8" stroke="#FFFFFF" stroke-width="2.5" fill="none"/>'
    return s
def topbar():
    s=rect(0,0,W,48,INK)+rect(14,11,26,26,"#FF9900",4)+text(20,29,"a",16,"#232F3E",True)
    s+=text(50,30,"Services",14,"#FFFFFF",True)
    s+=rect(150,10,360,28,"#FFFFFF",4)+text(165,29,"Search [ Alt+S ]",13,"#879596")
    s+=rect(W-300,10,150,28,INK2,4,"#3A4654",1)+text(W-292,29,"N. Virginia  us-east-1",12,"#D5DBDB")
    s+=rect(W-140,10,120,28,INK2,4,"#3A4654",1)+text(W-132,29,"acme-pharma / dev",12,"#D5DBDB")
    return s
def header(svc,crumb):
    return rect(0,48,UIW,46,"#FFFFFF",0,BORD,1)+text(24,78,svc,20,TXT,True)+text(UIW-20,76,crumb,12,MUT,anchor="end")
def leftnav(items,sel):
    x,y,w=0,94,210; s=rect(x,y,w,H-94,"#FAFAFA",0,BORD,1); cy=y+28
    for it in items:
        if it==sel: s+=rect(x,cy-18,w,30,SELBG)+rect(x,cy-18,3,30,SELBD)+text(x+16,cy+2,it,13,SELBD,True)
        else: s+=text(x+16,cy+2,it,13,TXT)
        cy+=34
    return s
def legend(title,steps):
    x=UIW+1; w=W-UIW-1; s=rect(x,48,w,H-48,"#FBFBFC",0,BORD,1)+text(x+18,80,"STEPS",12,ORANGE,True)+text(x+18,104,title,15,TXT,True)
    cy=140
    for i,st in enumerate(steps,1):
        s+=badge(x+30,cy,i); words=st.split(); line=""; ly=cy-4
        for wd in words:
            if len(line)+len(wd)+1>34: s+=text(x+52,ly,line,12.5,TXT); line=wd; ly+=16
            else: line=(line+" "+wd).strip()
        s+=text(x+52,ly,line,12.5,TXT); cy=ly+40
    s+=text(x+18,H-20,"Illustrative mockup — not an actual AWS screenshot",10,MUT)
    return s
def frame(svc,crumb,nav,sel,title,steps,body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
            +rect(0,0,W,H,PAGE)+topbar()+header(svc,crumb)+leftnav(nav,sel)+body+legend(title,steps)+'</svg>')
CX=230; CW=UIW-CX-24
def panel(y,h,title=None):
    s=rect(CX,y,CW,h,"#FFFFFF",6,BORD,1)
    if title: s+=text(CX+18,y+28,title,15,TXT,True)
    return s
def save(path,svg):
    path=str(path); open(path+".svg","w").write(svg)
    cairosvg.svg2png(bytestring=svg.encode(),write_to=path+".png",output_width=W,output_height=H,background_color="white")

# ---------- agent-specific figures ----------
def fig_cognito(p,out):
    b=panel(110,300,"Add identity provider")
    b+=text(CX+18,150,f"User pool: hcls-dev-users  >  Sign-in experience  >  Federated identity provider",12.5,MUT)
    b+=rect(CX+18,168,150,30,SELBG,4,SELBD,1)+text(CX+40,188,"SAML",13,SELBD,True)
    b+=rect(CX+178,168,150,30,"#FFFFFF",4,BORD,1)+text(CX+205,188,"OIDC",13,TXT)
    b+=field(CX+18,230,CW-300,"Metadata document URL","https://customer.okta.com/app/xxx/sso/saml/metadata")
    b+=text(CX+18,300,"Attribute mapping",13,TXT,True)
    b+=rect(CX+18,312,CW-36,30,"#F2F3F3",4)+text(CX+30,331,"IdP claim / group",12,MUT,True)+text(CX+360,331,"User pool attribute",12,MUT,True)
    b+=rect(CX+18,342,CW-36,32,"#FFFFFF",4,BORD,1)
    b+=text(CX+30,362,p["group"],12.5,TXT)+text(CX+360,362,f"custom:hcls_role  =  {p['approver']}",12.5,LINK,True)
    b+=button(CX+CW-150,392,150,"Add provider")
    b+=badge(CX+18,183,1)+badge(CX+18,230,2)+badge(CX+18,358,3)+badge(CX+CW-150,409,4)
    save(out, frame("Amazon Cognito","Cognito > User pools > hcls-dev-users",
        ["User pools","App integration","Sign-in experience","Attribute mapping","Domain"],"Sign-in experience",
        "Phase 3.3 — Federate the IdP",
        ["Choose SAML (or OIDC) as the federated identity provider.","Paste the customer IdP metadata document URL.",
         f"Map {p['group']} to custom:hcls_role = {p['approver']}.","Add provider; provisioning a user = adding them to the IdP group."],b))

def fig_cfn(p,out):
    GUT=CX+16; CXX=CX+46; FW=CW-52
    b=panel(106,400,"Create stack")
    b+=field(CXX,168,FW,"Amazon S3 template URL","https://my-cfn-bucket.s3.amazonaws.com/hcls/quickstart.yaml")
    b+=field(CXX,228,340,"Stack name",f"hcls-dev-{p['id']}")
    b+=text(CXX,296,"Parameters",13,TXT,True)
    params=[("Environment","dev"),("AgentId",p["id"]),("DeployMode","native"),
            ("LambdaCodeBucket","my-code-bucket"),("IdpMetadataUrl","https://customer.okta.com/.../metadata")]
    py=306
    for k,v in params:
        b+=rect(CXX,py,FW,26,"#FFFFFF",3,BORD,1)+text(CXX+12,py+17,k,11.5,MUT,True)+text(CXX+230,py+17,v,11.5,TXT); py+=29
    b+=rect(CXX,py+8,FW,34,"#FFF8F0",4,"#F0C36D",1)+check(CXX+12,py+15,True)+text(CXX+38,py+29,"I acknowledge that AWS CloudFormation might create IAM resources with custom names.",11.5,TXT)
    b+=button(CXX+FW-130,py+58,130,"Submit")
    b+=badge(GUT,178,1)+badge(GUT,296,2)+badge(GUT,py+25,3)+badge(CXX+FW-150,py+75,4)
    save(out, frame("AWS CloudFormation","CloudFormation > Create stack",
        ["Stacks","Create stack","StackSets","Exports","Designer"],"Create stack",
        "Phase 5 — Deploy with CloudFormation",
        ["Specify template: the quickstart.yaml S3 URL.",f"Set AgentId = {p['id']} (plus Environment, DeployMode, code bucket, IdP URL).",
         "Check the IAM capability acknowledgement.","Submit; watch Events to CREATE_COMPLETE; read Outputs."],b))

def fig_secrets(p,out):
    b=panel(110,290,"Store a new secret")
    b+=text(CX+18,150,"Secret type",13,TXT,True)+rect(CX+18,162,200,30,SELBG,4,SELBD,1)+text(CX+34,182,"Other type of secret",12.5,SELBD,True)
    b+=text(CX+18,228,"Key / value",13,TXT,True)
    b+=rect(CX+18,240,260,32,"#FFFFFF",4,BORD,1)+text(CX+30,260,p["secret_key"],12.5,TXT)
    b+=rect(CX+286,240,CW-322,32,"#FFFFFF",4,BORD,1)+text(CX+298,260,f"••••••••••  ({p['system']} API token)",12.5,MUT)
    b+=field(CX+18,308,CW-36,"Secret name",p["secret"])
    b+=text(CX+18,372,"The hcls/ prefix is what get_secret() resolves; the agent IAM role has GetSecretValue on hcls/*.",11.5,MUT)
    b+=button(CX+CW-120,372,120,"Store")
    b+=badge(CX+18,177,1)+badge(CX+18,256,2)+badge(CX+18,308,3)+badge(CX+CW-120,389,4)
    save(out, frame("AWS Secrets Manager","Secrets Manager > Store a new secret",
        ["Secrets","Store a new secret","Rotation","Replication"],"Store a new secret",
        "Phase 7 — Store the system credential",
        ["Choose Other type of secret.",f"Add key {p['secret_key']} = the {p['system']} API token.",
         f"Name the secret {p['secret']} (the hcls/ prefix matters).","Store. The agent role has GetSecretValue on hcls/*."],b))

def fig_stepfunctions(p,out):
    b=panel(110,430,f"Execution  ·  hcls-dev-{p['id']}")
    b+=rect(CX+18,150,150,26,"#FFF3CD",4,"#F0C36D",1)+text(CX+30,168,"Status: RUNNING",12,"#8A6D00",True)
    b+=button(CX+CW-150,148,150,"Start execution")
    nodes=p["nodes"]; gx=CX+60; gy=198
    gate_idx=nodes.index("HumanReviewGate")
    for i,nm in enumerate(nodes):
        done = i < gate_idx
        is_gate = (nm=="HumanReviewGate"); after=i>gate_idx
        col=GREEN if done else (AMBER if is_gate else "#AAB7B8")
        fill="#EAF6E9" if done else ("#FFF3CD" if is_gate else "#F2F3F3")
        b+=rect(gx,gy,260,38,fill,6,col,2)+rect(gx,gy,6,38,col,0)+text(gx+20,gy+24,nm,13,TXT,True)
        if done: b+=text(gx+260-52,gy+24,"done",11.5,GREEN,True)
        if is_gate: b+=text(gx+260-88,gy+24,"WAITING",11.5,"#8A6D00",True)
        if i<len(nodes)-1:
            b+=f'<line x1="{gx+130}" y1="{gy+38}" x2="{gx+130}" y2="{gy+50}" stroke="#879596" stroke-width="2"/>'
        gy+=50
    gyy=198+gate_idx*50
    b+=text(gx+300,gyy+18,"waitForTaskToken — paused for the",12.5,TXT)
    b+=text(gx+300,gyy+36,p["approver"]+" (HITL gate)",12.5,REDP,True)
    b+=text(gx+300,gyy+62,"On approval, Finalize runs:",11.5,MUT)
    b+=text(gx+300,gyy+79,p["finalize_action"],11.5,TXT,True)
    b+=badge(CX+CW-150,165,1)+badge(gx,gyy,2)+badge(gx,198+(len(nodes)-1)*50,3)
    save(out, frame("AWS Step Functions","Step Functions > State machines > Execution",
        ["State machines","Executions","Activities"],"Executions",
        "Phase 8 — Smoke test + human gate",
        ["Start execution with the agent's sample_input.json.",
         f"The graph pauses at HumanReviewGate (waitForTaskToken) for the {p['approver']} — by design.",
         "Approve via send-task-success with a verified reviewer; the machine resumes to Finalize."],b))

def fig_dynamodb(p,out):
    b=panel(110,420,"Explore items  ·  hcls-dev-audit")
    cols=["ts","decision","tool","user","args (PHI-masked)"]; widths=[120,150,180,110,200]
    b+=rect(CX+18,150,CW-36,30,"#232F3E",4); cx=CX+30
    for c,w in zip(cols,widths): b+=text(cx,170,c,12,"#FFFFFF",True); cx+=w
    ry=180
    for row in p["audit"]:
        b+=rect(CX+18,ry,CW-36,30,"#FFFFFF",0,"#EAECEC",1); cx=CX+30
        for v,w in zip(row,widths):
            col=TXT
            if v=="ALLOW": col=GREEN
            if v=="PENDING_APPROVAL": col="#8A6D00"
            b+=text(cx,ry+20,v,11.5,col,(v in("ALLOW","PENDING_APPROVAL"))); cx+=w
        ry+=30
    b+=text(CX+18,ry+28,"Append-only by IAM policy (UpdateItem/DeleteItem denied) — tamper-evident, 21 CFR Part 11.",11.5,MUT)
    b+=badge(CX+18+150+6,165,1)+badge(CX+18,180+(len(p['audit'])-2)*30,2)+badge(CX+18,180+(len(p['audit'])-1)*30,3)
    save(out, frame("Amazon DynamoDB","DynamoDB > Tables > hcls-dev-audit > Explore items",
        ["Tables","Explore items","PartiQL editor","Backups"],"Explore items",
        "Phase 8.3 — Confirm the audit trail",
        ["Each workflow step writes an append-only, PHI-masked audit item.",
         "Note the high-risk action gated as PENDING_APPROVAL before the human approves." if p["high_risk"] else "Reads and reversible actions are logged with full lineage.",
         "After approval the action is ALLOW with approved_by bound to the reviewer." if p["high_risk"] else "The human-approved finalize is ALLOW with the reviewer bound."],b))

print("primitives loaded")

# ---------- agent profiles ----------
RC="RouteChoice"; RD="RouteDecision"
def nd(route,second="Draft"): return ["Assemble",second,"Check",route,"HumanReviewGate","Finalize"]
PROFILES=[
 dict(id="01-regulatory-writing", name="Regulatory Writing & Intelligence", system="RIM",
   systems=[("rim","Veeva Vault RIM","RIM_BASE_URL"),("dms","Veeva Vault / OpenText DMS","DMS_BASE_URL")],
   approver="REGULATORY_APPROVER", group="GRP-REG-APPROVERS", secret="hcls/rim_api_token", secret_key="rim_api_token",
   base_var="RIM_BASE_URL", high_risk=["rim.create_submission_draft","dms.put_draft"], nodes=nd(RC),
   finalize_action="create the submission draft in RIM",
   audit=[("16:31:02","ALLOW","rim.get_obligations","u-auth-1","product=Demo-Drug"),
          ("16:31:06","ALLOW","dms.get_document","u-auth-1","doc_id=CSR-301"),
          ("16:31:10","PENDING_APPROVAL","rim.create_submission_draft","u-auth-1","awaiting approver"),
          ("16:36:14","ALLOW","rim.create_submission_draft","u-appr-3","approved_by=u-appr-3")]),
 dict(id="02-pharmacovigilance", name="Pharmacovigilance — ICSR Case Intake", system="Safety DB",
   systems=[("safety","Argus / Veeva Safety","SAFETY_BASE_URL"),("meddra","MedDRA dictionary","(licensed API)"),("whodrug","WHODrug dictionary","(licensed API)")],
   approver="PV_MEDICAL_REVIEWER", group="GRP-PV-PHYSICIANS", secret="hcls/safety_api_token", secret_key="safety_api_token",
   base_var="SAFETY_BASE_URL", high_risk=["safety.submit_report","safety.write_case_draft"], nodes=nd(RC),
   finalize_action="submit the ICSR to the safety gateway",
   audit=[("16:31:02","ALLOW","safety.get_case","u-pv-1","case_id=ICSR-2026-0002"),
          ("16:31:05","ALLOW","meddra.code_term","u-pv-1","term=[REDACTED]"),
          ("16:31:09","PENDING_APPROVAL","safety.submit_report","u-pv-1","awaiting reviewer"),
          ("16:34:20","ALLOW","safety.submit_report","u-md-7","approved_by=u-md-7")]),
 dict(id="03-clinical-trial-ops", name="Clinical Trial Ops & TMF", system="EDC",
   systems=[("ctms","Veeva/Medidata CTMS","CTMS_BASE_URL"),("etmf","Veeva Vault eTMF","ETMF_BASE_URL"),("edc","Medidata Rave / Veeva CDMS","EDC_BASE_URL")],
   approver="CLINOPS_LEAD", group="GRP-CLINOPS-LEAD", secret="hcls/edc_api_token", secret_key="edc_api_token",
   base_var="EDC_BASE_URL", high_risk=["edc.create_query"], nodes=nd(RD),
   finalize_action="create the EDC data query",
   audit=[("09:12:01","ALLOW","ctms.get_study_status","u-cra-2","study=STUDY-001"),
          ("09:12:04","ALLOW","etmf.get_completeness","u-cra-2","study=STUDY-001"),
          ("09:12:08","PENDING_APPROVAL","edc.create_query","u-cra-2","awaiting ClinOps Lead"),
          ("09:20:31","ALLOW","edc.create_query","u-lead-1","approved_by=u-lead-1")]),
 dict(id="04-site-patient-matching", name="Site Selection & Patient Matching", system="RWD",
   systems=[("rwd","Claims / EHR / registry RWD","RWD_BASE_URL"),("ctms","CTMS site master","CTMS_BASE_URL")],
   approver="SITE_SELECTION_LEAD", group="GRP-SITE-SELECTION", secret="hcls/rwd_api_token", secret_key="rwd_api_token",
   base_var="RWD_BASE_URL", high_risk=[], nodes=nd(RD),
   finalize_action="record the site ranking & cohort summary (no irreversible write)",
   audit=[("11:02:10","ALLOW","rwd.run_cohort_query","u-feas-1","cohort=T2DM (de-identified)"),
          ("11:02:18","ALLOW","ctms.get_study_status","u-feas-1","sites=42"),
          ("11:09:40","ALLOW","finalize.record_ranking","u-site-3","approved_by=u-site-3")]),
 dict(id="05-quality-capa", name="Quality / CAPA & Complaints", system="QMS",
   systems=[("qms","Veeva QMS / TrackWise / MasterControl","QMS_BASE_URL")],
   approver="QUALIFIED_PERSON", group="GRP-QP", secret="hcls/qms_api_token", secret_key="qms_api_token",
   base_var="QMS_BASE_URL", high_risk=["qms.create_capa_draft","qms.close_capa"], nodes=nd(RC),
   finalize_action="create the CAPA draft (and, separately, close the CAPA)",
   audit=[("14:05:11","ALLOW","qms.get_complaint","u-qa-2","complaint=CMP-2026-001"),
          ("14:05:15","ALLOW","qms.search_similar","u-qa-2","matches=3"),
          ("14:05:22","PENDING_APPROVAL","qms.create_capa_draft","u-qa-2","awaiting Qualified Person"),
          ("14:18:03","ALLOW","qms.create_capa_draft","u-qp-1","approved_by=u-qp-1")]),
 dict(id="06-protocol-design", name="Clinical Protocol Design & Feasibility", system="RIM",
   systems=[("rim","RIM guidance corpus","RIM_BASE_URL"),("rwd","RWD feasibility","RWD_BASE_URL"),("ctms","CTMS historical","CTMS_BASE_URL")],
   approver="CLINICAL_SCIENTIST", group="GRP-CLIN-SCI", secret="hcls/rim_api_token", secret_key="rim_api_token",
   base_var="RIM_BASE_URL", high_risk=[], nodes=nd(RC),
   finalize_action="register the protocol draft for review",
   audit=[("10:40:02","ALLOW","rim.search_guidance","u-sci-1","q=endpoints T2DM"),
          ("10:40:09","ALLOW","rwd.run_cohort_query","u-sci-1","eligible≈12,840 (de-identified)"),
          ("10:55:18","ALLOW","finalize.register_protocol","u-med-2","approved_by=u-med-2")]),
 dict(id="07-rwe-heor", name="Real-World Evidence / HEOR", system="RWD",
   systems=[("rwd","Claims / registry / RWD platform","RWD_BASE_URL")],
   approver="EPIDEMIOLOGIST", group="GRP-RWE-EPIDEMIOLOGISTS", secret="hcls/rwd_api_token", secret_key="rwd_api_token",
   base_var="RWD_BASE_URL", high_risk=[], nodes=nd(RC,"Synthesize"),
   finalize_action="release the evidence synthesis for review",
   audit=[("13:20:05","ALLOW","rwd.run_cohort_query","u-heor-1","cohort defn (de-identified)"),
          ("13:20:40","ALLOW","rwd.run_cohort_query","u-heor-1","data-quality pass"),
          ("13:41:12","ALLOW","finalize.release_synthesis","u-epi-2","approved_by=u-epi-2")]),
 dict(id="08-medical-affairs-msl", name="Medical Affairs / MSL Copilot", system="CRM",
   systems=[("crm","Veeva / Salesforce CRM","CRM_BASE_URL"),("dms","Approved content (DMS)","DMS_BASE_URL")],
   approver="MEDICAL_AFFAIRS_APPROVER", group="GRP-MEDICAL-AFFAIRS", secret="hcls/crm_api_token", secret_key="crm_api_token",
   base_var="CRM_BASE_URL", high_risk=["mlr.submit_for_review"], nodes=nd(RC),
   finalize_action="submit the brief to MLR review",
   audit=[("08:05:01","ALLOW","crm.get_hcp","u-msl-1","hcp=HCP-0001"),
          ("08:05:06","ALLOW","dms.get_document","u-msl-1","approved content"),
          ("08:05:12","PENDING_APPROVAL","mlr.submit_for_review","u-msl-1","awaiting Medical Affairs"),
          ("08:22:44","ALLOW","mlr.submit_for_review","u-ma-3","approved_by=u-ma-3")]),
]

TEMPLATE = (Path(__file__).resolve().parent / "handbook_template.md").read_text()

CSS = (Path(__file__).resolve().parent / "handbook.css").read_text()

def render_pdf(p):
    fid=p["id"]; figdir=f"assets/console/{fid}"
    sys_rows="\n".join(f"| `{k}` | {disp} | `{var}` |" for k,disp,var in p["systems"])
    hr = ", ".join(f"`{t}`" for t in p["high_risk"]) if p["high_risk"] else "none (reads / reversible actions; the finalize step is still human-approved)"
    nodes_arrow=" → ".join(p["nodes"])
    repl={
      "{{NAME}}":p["name"], "{{ID}}":fid, "{{SYSTEM}}":p["system"], "{{SYSTEMS_TABLE}}":sys_rows,
      "{{APPROVER}}":p["approver"], "{{GROUP}}":p["group"], "{{SECRET}}":p["secret"], "{{SECRET_KEY}}":p["secret_key"],
      "{{BASEVAR}}":p["base_var"], "{{HIGHRISK}}":hr, "{{FINALIZE_ACTION}}":p["finalize_action"],
      "{{NODES}}":nodes_arrow, "{{FIGDIR}}":figdir, "{{DATE}}":datetime.date.today().strftime("%B %Y"),
    }
    md=TEMPLATE
    for k,v in repl.items(): md=md.replace(k,v)
    html_body=markdown.markdown(md, extensions=["tables","fenced_code","attr_list","sane_lists"])
    cover=f'''<div class="cover"><div class="bar"></div><div class="barb"></div>
      <div class="eyebrow">DEPLOYMENT HANDBOOK</div>
      <h1>{esc(p["name"])}<br/>Deploying on AWS</h1>
      <div class="sub">Step-by-step, console and CLI — from an empty AWS account to a running, governed, human-gated agent.
      Tailored edition: AgentId <b>{esc(fid)}</b>; approval gate <b>{esc(p["approver"])}</b>.</div>
      <div class="rule"></div>
      <div class="meta">Systems-Integrator field &amp; delivery reference &nbsp;·&nbsp; {repl["{{DATE}}"]}</div>
      <div class="tag">Illustrative reference — figures are mockups, not actual AWS screenshots. Validate for your environment.</div></div>'''
    doc=f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{cover}{html_body}</body></html>"
    out=OUTDIR/f"HCLS-Deployment-Handbook-{fid}.pdf"
    HTML(string=doc, base_url=str(ROOT/'docs')).write_pdf(str(out))
    return out

for p in PROFILES:
    d=CONSOLE/p["id"]; d.mkdir(parents=True, exist_ok=True)
    fig_cognito(p, d/"03-cognito")
    fig_cfn(p, d/"04-cfn")
    fig_secrets(p, d/"05-secrets")
    fig_stepfunctions(p, d/"06-sfn")
    fig_dynamodb(p, d/"07-dynamodb")
    out=render_pdf(p)
    print("PDF", out.name, out.stat().st_size//1024, "KB")
print("ALL AGENT HANDBOOKS DONE")
