"""FitCheck REST API Application.

Implements the complete pipeline:
Jobs    ---> [PDF / Image / Text] ---API---> Storage ---> Processing ---> Analyzing ---> Serving
Resumes ---> [PDF / DOCX] -----------------> Storage ---> Processing ---> Analyzing ---> Serving

How to get Job Posting into the system:
- text  -> API  (POST /api/v1/jobs/text)
- Image -> API  (POST /api/v1/jobs/image)
- PDF   -> API  (POST /api/v1/jobs/pdf)
"""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure config runs and guards against AppLocker issues
import config
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routes import analysis, health, jobs, resumes

TAGS_METADATA = [
    {
        "name": "Jobs Ingestion & Processing",
        "description": "Endpoints to ingest jobs into storage via API (Text -> API, Image -> API, PDF -> API), extract text, and analyze skills.",
    },
    {
        "name": "Resumes Ingestion & Processing",
        "description": "Endpoints to upload resumes (PDF, DOCX) into storage, run text extraction, and analyze candidate skills.",
    },
    {
        "name": "Analysis, Scoring & Serving",
        "description": "Endpoints to run match analysis, calculate gap, TF-IDF cosine similarity, weighted scores, and serve reports.",
    },
    {
        "name": "Health & Status",
        "description": "Health checks, storage status (disk/MinIO), OCR status, and database diagnostics.",
    },
]

DESCRIPTION = """
### 🎯 FitCheck Pipeline & Ingestion API

This REST API implements the multi-stage ingestion and analysis pipeline:

```text
┌──────────────┐     ┌─────┐     ┌─────────┐     ┌────────────┐     ┌───────────┐     ┌─────────┐
│     Jobs     │────▶│ API │────▶│ Storage │────▶│ Processing │────▶│ Analyzing │────▶│ Serving │
│(PDF/Img/Txt) │     └─────┘     └─────────┘     └────────────┘     └───────────┘     └─────────┘
└──────────────┘                                                                           │
                                                                                           ▼
┌──────────────┐                 ┌─────────┐     ┌────────────┐     ┌───────────┐      REST API /
│   Resumes    │────────────────▶│ Storage │────▶│ Processing │────▶│ Analyzing │────▶ UI Report
│  (PDF/DOCX)  │                 └─────────┘     └────────────┘     └───────────┘
└──────────────┘
```

#### How to get Job Postings into the system:
* **Text ➔ API**: `POST /api/v1/jobs/text`
* **Image ➔ API**: `POST /api/v1/jobs/image` (OCR via Tesseract)
* **PDF ➔ API**: `POST /api/v1/jobs/pdf` (Extraction via pdfplumber)
"""

app = FastAPI(
    title="FitCheck Pipeline API",
    description=DESCRIPTION,
    version="1.0.0",
    openapi_tags=TAGS_METADATA,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware to allow web applications and frontend clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Route Modules
app.include_router(jobs.router)
app.include_router(resumes.router)
app.include_router(analysis.router)
app.include_router(health.router)


@app.get("/", tags=["Health & Status"], summary="API Root & Overview")
def root_overview():
    return {
        "message": "FitCheck Pipeline API is running",
        "version": "1.0.0",
        "architecture": {
            "jobs_pipeline": "Jobs (PDF/Image/Text) -> API -> Storage -> Processing -> Analyzing -> Serving",
            "resumes_pipeline": "Resumes (PDF/DOCX) -> Storage -> Processing -> Analyzing -> Serving",
            "job_ingestion_options": [
                "POST /api/v1/jobs/text (Text -> API)",
                "POST /api/v1/jobs/image (Image -> API)",
                "POST /api/v1/jobs/pdf (PDF -> API)",
                "POST /api/v1/jobs/upload (Generic Upload)",
            ],
            "resume_ingestion": "POST /api/v1/resumes/upload (PDF/DOCX -> Storage)",
            "analysis_pipeline": "POST /api/v1/analysis/match (Analyzing -> Serving)",
            "end_to_end_pipeline": "POST /api/v1/analysis/end-to-end",
        },
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_spec": "/openapi.json",
        },
    }
