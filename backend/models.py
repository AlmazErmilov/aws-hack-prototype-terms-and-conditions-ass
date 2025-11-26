from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class Risk(BaseModel):
    title: str
    description: str
    severity: str  # "low", "medium", "high"


class Company(BaseModel):
    id: str
    name: str
    icon_url: Optional[str] = None
    category: str  # "social", "dating", "streaming", etc.
    terms_risks: List[Risk] = []
    summary: Optional[str] = None
    last_updated: Optional[str] = None
    terms_text: Optional[str] = None
    # Cookie policy fields
    cookie_text: Optional[str] = None
    cookie_summary: Optional[str] = None
    cookie_risks: List[Risk] = []


class CompanyCreate(BaseModel):
    name: str
    category: str
    terms_text: str


class CompanyResponse(BaseModel):
    id: str
    name: str
    icon_url: Optional[str] = None
    category: str
    terms_risks: List[Risk] = []
    summary: Optional[str] = None
    last_updated: Optional[str] = None
    terms_text: Optional[str] = None
    # Cookie policy fields
    cookie_text: Optional[str] = None
    cookie_summary: Optional[str] = None
    cookie_risks: List[Risk] = []


class RiskAnalysisRequest(BaseModel):
    company_id: str


class UploadTermsRequest(BaseModel):
    company_name: str
    category: str
    terms_text: Optional[str] = None
    terms_url: Optional[str] = None


class UploadCookieRequest(BaseModel):
    cookie_text: Optional[str] = None
    cookie_url: Optional[str] = None
