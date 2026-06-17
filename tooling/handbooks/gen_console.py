import html, os, cairosvg
from pathlib import Path as _P
import os as _os
OUT=str(_P(__file__).resolve().parents[2]/"docs"/"assets"/"console")
_os.makedirs(OUT, exist_ok=True)
W,H=1320,760
UIW=980                      # UI area width; legend to the right
INK="#232F3E"; INK2="#1B2531"; PAGE="#F2F3F3"; PANEL="#FFFFFF"; BORD="#D5DBDB"
TXT="#16191F"; MUT="#5F6B7A"; LINK="#0073BB"; ORANGE="#EC7211"; AMBER="#FF9900"
SELBG="#F1FAFF"; SELBD="#0073BB"; GREEN="#1D8102"; REDP="#D13212"
def esc(s): return html.escape(str(s))
def rect(x,y,w,h,fill,rx=0,stroke=None,sw=1,dash=None):
    s=f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" rx="{rx}"'
    if stroke: s+=f' stroke="{stroke}" stroke-width="{sw}"'
    if dash: s+=f' stroke-dasharray="{dash}"'
    return s+'/>'
def text(x,y,t,size=14,fill=TXT,bold=False,anchor="start",font="Helvetica, Arial, sans-serif"):
    w='font-weight="700"' if bold else ''
    return f'<text x="{x}" y="{y}" font-family="{font}" font-size="{size}" fill="{fill}" {w} text-anchor="{anchor}">{esc(t)}</text>'
def badge(x,y,n):
    return (f'<circle cx="{x}" cy="{y}" r="15" fill="{AMBER}" stroke="#FFFFFF" stroke-width="2"/>'
            f'<text x="{x}" y="{y+5}" font-family="Helvetica, Arial" font-size="15" font-weight="700" fill="#232F3E" text-anchor="middle">{n}</text>')
def button(x,y,w,label,primary=True,h=34):
    fill=ORANGE if primary else "#FFFFFF"; tc="#FFFFFF" if primary else "#16191F"
    st=f' stroke="{BORD}" stroke-width="1"' if not primary else ''
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="{fill}"{st}/>'+text(x+w/2,y+h/2+5,label,14,tc,True,"middle")
def field(x,y,w,label,value,h=34):
    s=text(x,y-8,label,12,MUT,True)
    s+=rect(x,y,w,h,"#FFFFFF",4,BORD,1)
    s+=text(x+10,y+h/2+5,value,13,TXT)
    return s
def check(x,y,on=True,label="",lc=TXT):
    s=rect(x,y,18,18,("#EC7211" if on else "#FFFFFF"),3,(ORANGE if on else "#879596"),1.5)
    if on: s+=f'<path d="M {x+4} {y+9} l 3 4 l 7 -8" stroke="#FFFFFF" stroke-width="2.5" fill="none"/>'
    if label: s+=text(x+26,y+13,label,13,lc)
    return s

def topbar():
    s=rect(0,0,W,48,INK)
    s+=rect(14,11,26,26,"#FF9900",4)+text(20,29,"a",16,"#232F3E",True)  # cube-ish glyph
    s+=text(50,30,"Services",14,"#FFFFFF",True)
    s+=rect(150,10,360,28,"#FFFFFF",4)+text(165,29,"Search [ Alt+S ]",13,"#879596")
    s+=rect(W-300,10,150,28,INK2,4,"#3A4654",1)+text(W-292,29,"N. Virginia  us-east-1",12,"#D5DBDB")
    s+=rect(W-140,10,120,28,INK2,4,"#3A4654",1)+text(W-132,29,"acme-pharma / dev",12,"#D5DBDB")
    return s
def header(svc,crumb):
    s=rect(0,48,UIW,46,"#FFFFFF",0,BORD,1)
    s+=text(24,78,svc,20,TXT,True)
    s+=text(UIW-20,76,crumb,12,MUT,anchor="end")
    return s
def leftnav(items,sel):
    x,y,w=0,94,210; s=rect(x,y,w,H-94,"#FAFAFA",0,BORD,1)
    cy=y+28
    for it in items:
        if it==sel:
            s+=rect(x,cy-18,w,30,SELBG)+rect(x,cy-18,3,30,SELBD)
            s+=text(x+16,cy+2,it,13,SELBD,True)
        else:
            s+=text(x+16,cy+2,it,13,TXT)
        cy+=34
    return s
def legend(title,steps):
    x=UIW+1; w=W-UIW-1; s=rect(x,48,w,H-48,"#FBFBFC",0,BORD,1)
    s+=text(x+18,80,"STEPS",12,ORANGE,True)
    s+=text(x+18,104,title,15,TXT,True)
    cy=140
    for i,st in enumerate(steps,1):
        s+=badge(x+30,cy,i)
        # wrap text ~ 30 chars
        words=st.split(); line=""; ly=cy-4
        for wd in words:
            if len(line)+len(wd)+1>34:
                s+=text(x+52,ly,line,12.5,TXT); line=wd; ly+=16
            else: line=(line+" "+wd).strip()
        s+=text(x+52,ly,line,12.5,TXT)
        cy=ly+40
    s+=text(x+18,H-20,"Illustrative mockup — not an actual AWS screenshot",10,MUT,italic:=False)
    return s
def frame(svc,crumb,nav,sel,title,steps,body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Helvetica, Arial, sans-serif">'
            +rect(0,0,W,H,PAGE)+topbar()+header(svc,crumb)+leftnav(nav,sel)+body+legend(title,steps)+'</svg>')

def save(name,svg):
    open(f"{OUT}/{name}.svg","w").write(svg)
    cairosvg.svg2png(bytestring=svg.encode(),write_to=f"{OUT}/{name}.png",output_width=W,output_height=H,background_color="white")
    print("wrote",name)

# panel helper inside UI content area
CX=230; CW=UIW-CX-24
def panel(y,h,title=None):
    s=rect(CX,y,CW,h,"#FFFFFF",6,BORD,1)
    if title: s+=text(CX+18,y+28,title,15,TXT,True)
    return s

# ---------- 1. Bedrock model access ----------
b=panel(110,250,"Model access")
b+=text(CX+18,158,"Anthropic models — enable the tiers the agents use, then Save.",12.5,MUT)
rows=[("Claude Sonnet (narrative tier)",True),("Claude Haiku (fast tier)",True),("Titan Text",False)]
ry=185
b+=rect(CX+18,ry,CW-36,28,"#F2F3F3",4)+text(CX+28,ry+18,"Model",12,MUT,True)+text(CX+CW-120,ry+18,"Access status",12,MUT,True)
ry+=34
for nm,on in rows:
    b+=check(CX+28,ry,on)+text(CX+58,ry+13,nm,13,TXT)
    b+=text(CX+CW-120,ry+13,"Access granted" if on else "Available to request",12,(GREEN if on else MUT))
    ry+=34
b+=button(CX+CW-150,330,150,"Save changes")
b+=badge(W-300-0,0+0,0) if False else ""
# badges on UI
b+=badge(1140,30,1)         # region (top-right area)
b+=badge(120,140,2)         # left nav Model access
b+=badge(CX+28,219,3)       # checkboxes
b+=badge(CX+CW-150,347,4)   # save
save("01-bedrock-model-access",
 frame("Amazon Bedrock","Bedrock > Model access",
   ["Overview","Base models","Model access","Guardrails","Playgrounds"],"Model access",
   "Phase 3.1 — Enable model access",
   ["Set the Region (top-right) to an AgentCore-enabled Region, e.g. us-east-1.",
    "Left nav: open Model access, then Manage model access.",
    "Check the Anthropic Claude narrative + fast tiers.",
    "Save changes; wait for status to read Access granted."],b))

# ---------- 2. Bedrock guardrail ----------
b=panel(110,300,"Create guardrail")
b+=field(CX+18,150,330,"Guardrail name","hcls-dev-guardrail")
b+=text(CX+18,215,"Sensitive information filter (PII)",13,TXT,True)
pii=[("US Social Security Number","Block"),("Email / Name / Phone","Anonymize")]
ry=228
for nm,act in pii:
    b+=rect(CX+18,ry,CW-36,28,"#F7FAFC",4,BORD,1)+text(CX+30,ry+18,nm,12.5,TXT)
    b+=text(CX+CW-120,ry+18,act,12.5,(REDP if act=="Block" else LINK),True)
    ry+=34
b+=text(CX+18,ry+24,"Denied topic",13,TXT,True)
b+=rect(CX+18,ry+34,CW-36,40,"#FFF8F0",4,"#F0C36D",1)
b+=text(CX+30,ry+52,"OffLabelPromotion — promotion for an unapproved indication or absolute",12,TXT)
b+=text(CX+30,ry+68,"efficacy/safety claims (cure, guarantee, completely safe).",12,TXT)
b+=button(CX+CW-260,395,120,"Create version",False)
b+=button(CX+CW-130,395,130,"Create guardrail")
b+=badge(CX+18,150,1); b+=badge(CX+18,222,2); b+=badge(CX+18,ry+34,3); b+=badge(CX+CW-130,412,4)
save("02-bedrock-guardrail",
 frame("Amazon Bedrock","Bedrock > Guardrails > Create",
   ["Overview","Base models","Model access","Guardrails","Playgrounds"],"Guardrails",
   "Phase 3.2 — Create the Guardrail",
   ["Name the guardrail hcls-dev-guardrail.",
    "Add PII filters: SSN -> Block; Email/Name/Phone -> Anonymize.",
    "Add a denied topic OffLabelPromotion to block off-label/absolute claims.",
    "Create, then Create version. Record the Guardrail ID + version."],b))

# ---------- 3. Cognito IdP ----------
b=panel(110,300,"Add identity provider")
b+=text(CX+18,150,"User pool: hcls-dev-users  >  Sign-in experience  >  Federated identity provider",12.5,MUT)
b+=rect(CX+18,168,150,30,SELBG,4,SELBD,1)+text(CX+40,188,"SAML",13,SELBD,True)
b+=rect(CX+178,168,150,30,"#FFFFFF",4,BORD,1)+text(CX+205,188,"OIDC",13,TXT)
b+=field(CX+18,230,CW-300,"Metadata document URL","https://customer.okta.com/app/xxx/sso/saml/metadata")
b+=text(CX+18,300,"Attribute mapping",13,TXT,True)
b+=rect(CX+18,312,CW-36,30,"#F2F3F3",4)+text(CX+30,331,"IdP claim / group",12,MUT,True)+text(CX+360,331,"User pool attribute",12,MUT,True)
b+=rect(CX+18,342,CW-36,32,"#FFFFFF",4,BORD,1)
b+=text(CX+30,362,"GRP-PV-PHYSICIANS",12.5,TXT)+text(CX+360,362,"custom:hcls_role  =  PV_MEDICAL_REVIEWER",12.5,LINK,True)
b+=button(CX+CW-150,392,150,"Add provider")
b+=badge(CX+18,183,1); b+=badge(CX+18,230,2); b+=badge(CX+18,358,3); b+=badge(CX+CW-150,409,4)
save("03-cognito-idp",
 frame("Amazon Cognito","Cognito > User pools > hcls-dev-users",
   ["User pools","App integration","Sign-in experience","Attribute mapping","Domain"],"Sign-in experience",
   "Phase 3.3 — Federate the customer IdP",
   ["Choose SAML (or OIDC) as the federated identity provider.",
    "Paste the customer IdP metadata document URL.",
    "Map the approver group to custom:hcls_role (e.g. PV_MEDICAL_REVIEWER).",
    "Add provider. Provisioning a user = adding them to the IdP group."],b))

# ---------- 4. CloudFormation create stack ----------
GUT=CX+16; CXX=CX+46; FW=CW-52     # badge gutter + content x + field width
b=panel(106,400,"Create stack")
b+=field(CXX,168,FW,"Amazon S3 template URL","https://my-cfn-bucket.s3.amazonaws.com/hcls/quickstart.yaml")
b+=field(CXX,228,340,"Stack name","hcls-dev-02-pharmacovigilance")
b+=text(CXX,296,"Parameters",13,TXT,True)
params=[("Environment","dev"),("AgentId","02-pharmacovigilance"),("DeployMode","native"),
        ("LambdaCodeBucket","my-code-bucket"),("IdpMetadataUrl","https://customer.okta.com/.../metadata")]
py=306
for k,v in params:
    b+=rect(CXX,py,FW,26,"#FFFFFF",3,BORD,1)+text(CXX+12,py+17,k,11.5,MUT,True)+text(CXX+230,py+17,v,11.5,TXT)
    py+=29
b+=rect(CXX,py+8,FW,34,"#FFF8F0",4,"#F0C36D",1)
b+=check(CXX+12,py+15,True)+text(CXX+38,py+29,"I acknowledge that AWS CloudFormation might create IAM resources with custom names.",11.5,TXT)
b+=button(CXX+FW-130,py+58,130,"Submit")
# badges live in the left gutter (never over text)
b+=badge(GUT,178,1)            # S3 template field
b+=badge(GUT,296,2)            # Parameters heading
b+=badge(GUT,py+25,3)          # acknowledgement
b+=badge(CXX+FW-150,py+75,4)   # submit
save("04-cloudformation-create-stack",
 frame("AWS CloudFormation","CloudFormation > Create stack",
   ["Stacks","Create stack","StackSets","Exports","Designer"],"Create stack",
   "Phase 3 - Deploy with CloudFormation",
   ["Specify template: the quickstart.yaml S3 URL.",
    "Set parameters: Environment, AgentId, DeployMode, code bucket, IdP URL.",
    "Check the IAM capability acknowledgement.",
    "Submit; watch Events to CREATE_COMPLETE; read Outputs (GatewayId, GuardrailId, AuditTable)."],b))

# ---------- 5. Secrets Manager ----------
b=panel(110,290,"Store a new secret")
b+=text(CX+18,150,"Secret type",13,TXT,True)
b+=rect(CX+18,162,200,30,SELBG,4,SELBD,1)+text(CX+34,182,"Other type of secret",12.5,SELBD,True)
b+=text(CX+18,228,"Key / value",13,TXT,True)
b+=rect(CX+18,240,260,32,"#FFFFFF",4,BORD,1)+text(CX+30,260,"safety_api_token",12.5,TXT)
b+=rect(CX+286,240,CW-322,32,"#FFFFFF",4,BORD,1)+text(CX+298,260,"••••••••••••••••  (customer Safety API token)",12.5,MUT)
b+=field(CX+18,308,CW-36,"Secret name","hcls/safety_api_token")
b+=text(CX+18,372,"The hcls/ prefix is what platform get_secret() resolves; the agent IAM role has GetSecretValue on hcls/*.",11.5,MUT)
b+=button(CX+CW-120,372,120,"Store")
b+=badge(CX+18,177,1); b+=badge(CX+18,256,2); b+=badge(CX+18,308,3); b+=badge(CX+CW-120,389,4)
save("05-secrets-manager",
 frame("AWS Secrets Manager","Secrets Manager > Store a new secret",
   ["Secrets","Store a new secret","Rotation","Replication"],"Store a new secret",
   "Phase 5 — Store the system credential",
   ["Choose Other type of secret.",
    "Add key safety_api_token = the customer Safety API token.",
    "Name the secret hcls/safety_api_token (the hcls/ prefix matters).",
    "Store. The agent role already has GetSecretValue on hcls/*."],b))

# ---------- 6. Step Functions execution (HITL) ----------
b=panel(110,420,"Execution  ·  hcls-dev-02-pharmacovigilance")
b+=rect(CX+18,150,150,26,"#FFF3CD",4,"#F0C36D",1)+text(CX+30,168,"Status: RUNNING",12,"#8A6D00",True)
b+=button(CX+CW-150,148,150,"Start execution")
# vertical graph
nodes=[("Assemble",GREEN),("Draft",GREEN),("Check",GREEN),("RouteChoice",GREEN),
       ("HumanReviewGate",AMBER),("Finalize","#AAB7B8")]
gx=CX+60; gy=200
for i,(nm,col) in enumerate(nodes):
    fill="#EAF6E9" if col==GREEN else ("#FFF3CD" if col==AMBER else "#F2F3F3")
    bd=col
    b+=rect(gx,gy,260,40,fill,6,bd,2)
    b+=rect(gx,gy,6,40,bd,0)
    b+=text(gx+22,gy+25,nm,13.5,TXT,True)
    if col==GREEN: b+=text(gx+260-58,gy+25,"done",11.5,GREEN,True)
    if col==AMBER: b+=text(gx+260-90,gy+25,"WAITING",11.5,"#8A6D00",True)
    if i<len(nodes)-1:
        b+=f'<line x1="{gx+130}" y1="{gy+40}" x2="{gx+130}" y2="{gy+54}" stroke="#879596" stroke-width="2"/>'
        b+=f'<path d="M {gx+125} {gy+50} l 5 6 l 5 -6" fill="#879596"/>'
    gy+=54
b+=text(gx+300,200+4*54+25,"waitForTaskToken — paused for the",12.5,TXT)
b+=text(gx+300,200+4*54+43,"PV Medical Reviewer (HITL gate)",12.5,REDP,True)
b+=badge(CX+CW-150,165,1); b+=badge(gx,200+4*54,2); b+=badge(gx,200+5*54,3)
save("06-stepfunctions-execution",
 frame("AWS Step Functions","Step Functions > State machines > Execution",
   ["State machines","Executions","Activities"],"Executions",
   "Phase 6 — Smoke test + the human gate",
   ["Start execution with the agent's sample_input.json.",
    "The graph pauses at HumanReviewGate (waitForTaskToken). This is by design — nothing finalizes without a human.",
    "Approve via send-task-success with a verified reviewer; the machine resumes to Finalize (gateway-authorized submit)."],b))

# ---------- 7. DynamoDB audit ----------
b=panel(110,420,"Explore items  ·  hcls-dev-audit")
cols=["ts","decision","tool","user","args (PHI-masked)"]
b+=rect(CX+18,150,CW-36,30,"#232F3E",4)
cx=CX+30
widths=[120,140,170,120,200]
for c,w in zip(cols,widths):
    b+=text(cx,170,c,12,"#FFFFFF",True); cx+=w
data=[("16:31:02","ALLOW","safety.get_case","u-pv-1","case_id=ICSR-2026-0002"),
      ("16:31:05","ALLOW","meddra.code_term","u-pv-1","term=[REDACTED]"),
      ("16:31:09","PENDING_APPROVAL","safety.submit_report","u-pv-1","awaiting reviewer"),
      ("16:34:20","ALLOW","safety.submit_report","u-md-7","approved_by=u-md-7"),]
ry=180
for row in data:
    b+=rect(CX+18,ry,CW-36,30,"#FFFFFF",0,"#EAECEC",1)
    cx=CX+30
    for v,w in zip(row,widths):
        col=TXT
        if v=="ALLOW": col=GREEN
        if v=="PENDING_APPROVAL": col="#8A6D00"
        b+=text(cx,ry+20,v,11.5,col,(v in("ALLOW","PENDING_APPROVAL"))); cx+=w
    ry+=30
b+=text(CX+18,ry+28,"Append-only by IAM policy (UpdateItem/DeleteItem denied) — tamper-evident, 21 CFR Part 11.",11.5,MUT)
b+=badge(CX+18+140+6,165,1); b+=badge(CX+18,180+2*30,2); b+=badge(CX+18,180+3*30,3)
save("07-dynamodb-audit",
 frame("Amazon DynamoDB","DynamoDB > Tables > hcls-dev-audit > Explore items",
   ["Tables","Explore items","PartiQL editor","Backups"],"Explore items",
   "Phase 6.3 — Confirm the audit trail",
   ["Each workflow step writes an append-only audit item with PHI masked.",
    "Note PENDING_APPROVAL on the high-risk submit before the human approves.",
    "After approval the submit is ALLOW with approved_by bound to the reviewer."],b))

print("ALL DONE")
