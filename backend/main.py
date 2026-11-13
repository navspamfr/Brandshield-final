import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

from backend.database.db import (
    init_db,
    get_organizations,
    get_organization_by_id,
    create_organization,
    get_brand_rules,
    add_brand_rule,
    get_analyses,
    get_dashboard_metrics,
    save_analysis,
    get_recent_activity
)
from backend.models.schemas import OrganizationCreate, RuleCreate, AnalysisRequest
from processing.ai_engine.analyzer import run_compliance_audit

app = FastAPI(
    title="BrandShield API",
    description="Enterprise AI Brand Protection & Compliance Engine",
    version="1.0.0"
)

# Enable CORS for web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    init_db()

@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "BrandShield AI Engine"}

@app.get("/api/organizations")
def list_organizations():
    return get_organizations()

@app.get("/api/organizations/{org_id}")
def get_organization(org_id: int):
    org = get_organization_by_id(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org

@app.post("/api/organizations")
def create_org(payload: OrganizationCreate):
    org_id = create_organization(
        user_id=1,
        name=payload.name,
        industry=payload.industry,
        tagline=payload.tagline,
        description=payload.description,
        website=payload.website,
        tone_of_voice=payload.tone_of_voice,
        target_audience=payload.target_audience,
        primary_color=payload.primary_color,
        secondary_color=payload.secondary_color,
        accent_color=payload.accent_color
    )
    return {"id": org_id, "message": "Brand profile created successfully"}

@app.get("/api/organizations/{org_id}/rules")
def list_rules(org_id: int):
    return get_brand_rules(org_id)

@app.post("/api/organizations/{org_id}/rules")
def add_rule(org_id: int, payload: RuleCreate):
    rule_id = add_brand_rule(
        org_id=org_id,
        category=payload.category,
        rule_title=payload.rule_title,
        rule_description=payload.rule_description,
        severity=payload.severity
    )
    return {"id": rule_id, "message": "Rule added successfully"}

@app.post("/api/analyze")
def analyze_content(payload: AnalysisRequest):
    report = run_compliance_audit(
        org_id=payload.org_id,
        content_text=payload.content_text,
        target_channel=payload.target_channel
    )
    # Save analysis in history
    analysis_id = save_analysis(
        org_id=payload.org_id,
        user_id=payload.user_id or 1,
        title=payload.title,
        asset_type="text",
        target_channel=payload.target_channel,
        input_content=payload.content_text,
        image_path=None,
        compliance_score=report["overall_score"],
        status=report["status"],
        corrected_content=report.get("corrected_content", ""),
        summary=report.get("summary", ""),
        full_report_json=import_json_dumps(report)
    )
    report["analysis_id"] = analysis_id
    return report

@app.get("/api/dashboard/metrics")
def dashboard_metrics(org_id: Optional[int] = None):
    return get_dashboard_metrics(org_id)

@app.get("/api/activity")
def recent_activity(org_id: Optional[int] = None, limit: int = 10):
    return get_recent_activity(org_id, limit)

def import_json_dumps(data):
    import json
    return json.dumps(data)
