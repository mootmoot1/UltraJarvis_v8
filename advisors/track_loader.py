from pathlib import Path
TRACKS = {
 "content":{"title":"Track: Content/Media Automation","items":[
  "Content pipeline design (ideas→scripts→assets→publish)","Research 5 niches low competition",
  "30-day content calendar","Short-form generator (script→voice→b-roll→caption)",
  "Auto-thumbnail templates","Subtitle pipeline (SRT)","Multi-platform posting bot",
  "Hook library (100)","Script template variants","Title generator + CTR proxy",
  "Hashtag/topic chooser","Engagement responder (guarded)","Analytics CSV export",
  "Weekly report","Repurpose long→short","Rights/licensing checklist",
  "Collab outreach template","Monetization map","Experiment backlog (10)","Reliability checklist"
 ]},
 "saas":{"title":"Track: Automation SaaS (SMB/Freelancers)","items":[
  "Pick 3 pain points","Spec MVP #1","Prototype CLI→Web","Auth/billing (test keys)",
  "Usage logging","Landing page v1","Prospect list (50)","Cold email templates",
  "Demo flow","Feedback capture","Pricing hypotheses","Churn risks",
  "Support bot stub","Onboarding checklist","Audit logging","Uptime/health monitor",
  "Weekly growth report","Referral program v1","Partner integrations","Scale plan"
 ]},
 "leadgen":{"title":"Track: Lead Gen / Outreach","items":[
  "Define ICP + signals","Lead scraper stub (public)","Enrichment step","Lead scoring v1",
  "Domain warmup checklist","Cold sequence (3) + safety","Mailbox rotation config",
  "Auto-personalization","Booking link integration","CSV CRM stub",
  "Daily send limits","Unsubscribe handling","Reply classifier",
  "Follow-up rules","Weekly pipeline report","A/B subject lines",
  "Anti-spam hygiene","Offer library","Case studies template","Scale plan"
 ]},
 "ecommerce":{"title":"Track: E-commerce / Digital","items":[
  "10 product ideas","Competitor review mining","Supplier checklist","Product page template",
  "Pricing tiers","Simple checkout stub","Email capture + welcome","Abandoned cart stub",
  "UGC/review capture","Creative assets generator","Ad angles (20 hooks)","ROAS sheet",
  "Affiliate outline","Seasonal calendar","Fulfillment checklist","Support macros",
  "Refund policy template","Weekly sales dashboard","Scaling ops checklist","Localization shortlist"
 ]},
 "consulting":{"title":"Track: Consulting/Services (AI)","items":[
  "Pick 3 niches","Packaged offers","Discovery script","Proposal template",
  "Case study template","Portfolio stub","Lead list (50/company)","Cold DM/email scripts",
  "SOW template","Reporting template","Delivery pipeline","Privacy checklist",
  "Contract checklist","Testimonial capture","Upsell paths","Ops checklist",
  "KB structure","Support SLAs","Quarterly repositioning","Scale plan"
 ]},
 "finance":{"title":"Track: Finance/Research (No advice)","items":[
  "Data sources list (public)","News aggregator stub","Watchlist CSV","Signals dashboard",
  "Event calendar stub","Sentiment proxy","Alert thresholds","Risk disclaimer template",
  "Backtest sandbox (dummy)","Weekly digest","Macro calendar links","Glossary",
  "Paper-trade journal","CSV export","Permissioning model","Quota checklist",
  "Data quality notes","Ops runbook","Next integrations","Compliance checklist"
 ]}
}

def list_tracks()->dict: return {"ok":True,"tracks":sorted(TRACKS.keys())}

def add_track(name:str)->dict:
    key=name.strip().lower()
    if key not in TRACKS: 
        return {"ok":False,"error":f"unknown track '{name}'","available":sorted(TRACKS.keys())}
    data=TRACKS[key]
    p=Path("project/roadmap.md")
    p.parent.mkdir(parents=True, exist_ok=True)
    md=p.read_text(encoding="utf-8") if p.exists() else "# Roadmap\n\n"
    sec=f"## {data['title']}"
    if sec not in md: 
        md += f"\n{sec}\n"
    for it in data["items"]: 
        md += f"- {it}\n"
    p.write_text(md, encoding="utf-8")
    return {"ok":True,"added":data["title"],"count":len(data["items"]), "file":str(p)}
