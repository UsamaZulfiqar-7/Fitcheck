"""Health & Diagnostics API Route.

Reports the operational state of:
- API Service
- Raw Storage (Local Disk & MinIO S3)
- Processing Engines (Tesseract OCR, pdfplumber, python-docx)
- Database (PostgreSQL / SQLite)
"""
from __future__ import annotations

import os
from fastapi import APIRouter
from sqlalchemy import func, select

import config
from api.schemas import HealthResponse
from core import db, extraction, repository as repo, storage

router = APIRouter(prefix="/api/v1/health", tags=["Health & Status"])


@router.get("", response_model=HealthResponse, summary="Get Pipeline & Storage Health Status")
def get_health_status() -> HealthResponse:
    is_sqlite = "sqlite" in config.DATABASE_URL.lower()
    tesseract_ok = extraction.ocr_available()
    tesseract_path = config.TESSERACT_CMD or (
        extraction._WINDOWS_TESSERACT if os.path.exists(extraction._WINDOWS_TESSERACT) else "Not configured"
    )

    with db.session_scope() as s:
        cand_count = s.scalar(select(func.count()).select_from(db.Candidate)) or 0
        job_count = s.scalar(select(func.count()).select_from(db.JobPosting)) or 0
        resume_count = s.scalar(select(func.count()).select_from(db.Resume)) or 0
        match_count = s.scalar(select(func.count()).select_from(db.MatchResult)) or 0

    return HealthResponse(
        status="healthy",
        app_name=config.APP_NAME,
        architecture_pipeline="Jobs (PDF/Image/Text) -> API -> Storage -> Processing -> Analyzing -> Serving",
        storage={
            "local_upload_dir": str(config.UPLOAD_DIR),
            "minio_enabled": storage.minio_enabled(),
            "minio_endpoint": config.MINIO_ENDPOINT or None,
            "minio_bucket": config.MINIO_BUCKET if storage.minio_enabled() else None,
        },
        database={
            "engine": "SQLite" if is_sqlite else "PostgreSQL",
            "url_masked": config.DATABASE_URL.split("@")[-1] if "@" in config.DATABASE_URL else "local_sqlite",
        },
        ocr_engine={
            "available": tesseract_ok,
            "executable": tesseract_path if tesseract_ok else "Tesseract not detected",
        },
        records_count={
            "candidates": cand_count,
            "job_postings": job_count,
            "resumes": resume_count,
            "match_analyses": match_count,
        },
    )
