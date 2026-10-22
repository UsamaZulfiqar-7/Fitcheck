"""Pydantic schemas for the FitCheck REST API.

These schemas map directly to the pipeline stages:
Jobs (PDF/Image/Text) -> API -> Storage -> Processing -> Analyzing -> Serving
Resumes (PDF/DOCX)   -> Storage -> Processing -> Analyzing -> Serving
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ============================================================================
# Job Posting Schemas
# ============================================================================

class JobTextInput(BaseModel):
    """Payload for submitting job postings via Text -> API."""
    title: str = Field(default="Untitled Job", description="Job title, e.g. 'Senior Python Developer'")
    company: Optional[str] = Field(default=None, description="Hiring company name")
    text: str = Field(..., min_length=10, description="Full job posting / description text")
    candidate_id: Optional[int] = Field(default=None, description="Optional profile/candidate ID")
    candidate_name: Optional[str] = Field(default="API User", description="Profile name if candidate_id is omitted")


class JobResponse(BaseModel):
    """Response serving stored, processed, and analyzed job postings."""
    job_id: int = Field(..., description="Unique database identifier for the job posting")
    candidate_id: Optional[int] = Field(None, description="Associated candidate profile ID")
    title: str = Field(..., description="Job title")
    company: Optional[str] = Field(None, description="Company name")
    source: str = Field(..., description="Source format: 'text', 'pdf', 'image', 'docx', 'sample'")
    raw_storage_path: Optional[str] = Field(None, description="Path where original bytes are stored")
    storage_kind: str = Field("local+minio", description="Storage layer used")
    character_count: int = Field(..., description="Extracted text length in characters")
    extraction_method: str = Field(..., description="Method used to extract text (e.g. 'direct_text', 'pdfplumber', 'tesseract_ocr')")
    required_skills: List[str] = Field(default_factory=list, description="Skills detected as required")
    preferred_skills: List[str] = Field(default_factory=list, description="Skills detected as nice-to-have / preferred")
    total_skills_detected: int = Field(0, description="Total number of canonical skills identified")
    preview_text: str = Field(..., description="Snippet of the extracted text")
    created_at: str = Field(..., description="Ingestion and storage timestamp (UTC)")


# ============================================================================
# Resume Schemas
# ============================================================================

class ResumeResponse(BaseModel):
    """Response serving stored, processed, and analyzed resumes."""
    resume_id: int = Field(..., description="Unique database identifier for the resume")
    candidate_id: int = Field(..., description="Associated candidate ID")
    candidate_name: str = Field(..., description="Candidate display name")
    filename: str = Field(..., description="Original uploaded filename")
    file_type: str = Field(..., description="Format: 'pdf', 'docx', 'txt'")
    file_size_bytes: int = Field(..., description="Original file size in bytes")
    raw_storage_path: Optional[str] = Field(None, description="Path where original file is stored")
    storage_kind: str = Field("local+minio", description="Storage layer used")
    extraction_method: str = Field(..., description="Method used (e.g. 'pdfplumber', 'docx_xml', 'ocr')")
    warnings: List[str] = Field(default_factory=list, description="Any extraction warnings")
    skills: List[str] = Field(default_factory=list, description="Extracted candidate skills")
    total_skills: int = Field(..., description="Number of skills detected on candidate CV")
    preview_text: str = Field(..., description="First lines of extracted CV text")
    created_at: str = Field(..., description="Ingestion timestamp")


# ============================================================================
# Analysis & Matching Schemas
# ============================================================================

class MatchRequest(BaseModel):
    """Request payload to analyze a stored resume against a stored job."""
    resume_id: int = Field(..., description="ID of previously stored resume")
    job_id: int = Field(..., description="ID of previously stored job posting")
    candidate_id: Optional[int] = Field(None, description="Candidate ID (defaults to resume's candidate)")
    skill_weight: Optional[float] = Field(0.70, ge=0.0, le=1.0, description="Weight of skill match (default 0.70)")
    preferred_weight: Optional[float] = Field(0.50, ge=0.0, le=1.0, description="Weight of preferred skills (default 0.50)")
    use_semantic: Optional[bool] = Field(False, description="Enable sentence-transformers semantic similarity")


class MatchResponse(BaseModel):
    """Response serving the analysis, score, and skill gap report."""
    match_id: int = Field(..., description="Unique match analysis ID")
    candidate_id: int
    resume_id: int
    job_id: int
    final_score: float = Field(..., description="Overall match score out of 100")
    skill_score: float = Field(..., description="Skill coverage score out of 100")
    text_similarity: float = Field(..., description="Text/TF-IDF similarity score out of 100")
    skill_weight: float
    text_weight: float
    matched_skills: List[str] = Field(default_factory=list, description="Skills present in both CV and Job")
    missing_required_skills: List[str] = Field(default_factory=list, description="Must-have skills missing from CV")
    missing_preferred_skills: List[str] = Field(default_factory=list, description="Nice-to-have skills missing from CV")
    additional_skills: List[str] = Field(default_factory=list, description="Extra skills on CV not requested by Job")
    score_breakdown: Dict[str, Any] = Field(default_factory=dict, description="Detailed arithmetic breakdown")
    disclaimer: str = Field(..., description="Legal and ATS advisory notice")


# ============================================================================
# System Health & Architecture Schemas
# ============================================================================

class HealthResponse(BaseModel):
    """System and pipeline status report."""
    status: str = "healthy"
    app_name: str
    architecture_pipeline: str = "Jobs (PDF/Image/Text) -> API -> Storage -> Processing -> Analyzing -> Serving"
    storage: Dict[str, Any]
    database: Dict[str, Any]
    ocr_engine: Dict[str, Any]
    records_count: Dict[str, int]
