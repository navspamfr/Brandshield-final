from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class OrganizationCreate(BaseModel):
    name: str
    industry: Optional[str] = None
    tagline: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    tone_of_voice: Optional[str] = None
    target_audience: Optional[str] = None
    primary_color: str = "#8955D9"
    secondary_color: str = "#D0B7FF"
    accent_color: str = "#100C18"

class RuleCreate(BaseModel):
    category: str
    rule_title: str
    rule_description: str
    severity: str = "medium"

class AnalysisRequest(BaseModel):
    org_id: int
    user_id: Optional[int] = 1
    title: str = "Ad-hoc Compliance Check"
    content_text: Optional[str] = None
    target_channel: str = "Social Media"
