"""Job Ingestion API Routes.

Implements the flow:
Jobs -> [PDF / Image / text] --API--> storage -> processing -> analyzing -> serving

Question: How to get Job Posting into the system?
- text  -> API  (POST /api/v1/jobs/text)
- Image -> API  (POST /api/v1/jobs/image)
- PDF   -> API  (POST /api/v1/jobs/pdf)
"""
from __future__ import annotations

import os
from typing import List, Optional
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

import config
from api.schemas import JobResponse, JobTextInput
from core import extraction, repository as repo, skills, storage

router = APIRouter(prefix="/api/v1/jobs", tags=["Jobs Ingestion & Processing"])


def _extract_title_if_missing(text: str, fallback: str = "Untitled Job") -> str:
    """Guess a title from the first non-empty short line of text."""
    for line in text.splitlines():
        line = line.strip()
        if 3 <= len(line) <= 80:
            return line
    return fallback


def _resolve_candidate_id(cand_id: Optional[int], cand_name: Optional[str]) -> Optional[int]:
    """Helper to ensure a valid candidate profile is attached if specified."""
    if cand_id:
        return cand_id
    if cand_name and cand_name.strip():
        cand = repo.get_or_create_candidate(cand_name.strip())
        return cand.id
    return None


@router.post("/text", response_model=JobResponse, status_code=status.HTTP_201_CREATED,
             summary="Ingest Job Posting from Text (Text -> API -> Storage -> Processing -> Analyzing -> Serving)")
def ingest_job_from_text(payload: JobTextInput) -> JobResponse:
    """
    Ingest a job description via raw typed/pasted text:
    1. **API**: Receives JSON payload with job text and metadata.
    2. **Storage**: Persists the raw text bytes to storage (local disk & MinIO if configured).
    3. **Processing**: Cleans, standardizes line breaks, and validates text.
    4. **Analyzing**: Automatically detects required vs. preferred skills via taxonomy rules.
    5. **Serving**: Returns structured JSON with job ID, storage path, and detected skills.
    """
    cleaned_text = extraction.clean_text(payload.text)
    if len(cleaned_text) < 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job text is too short. Please provide at least 20 characters.",
        )

    # 1. API -> Storage (Raw byte storage)
    raw_filename = f"job_{payload.title.replace(' ', '_')[:30]}.txt"
    raw_storage_path = storage.save_raw(cleaned_text.encode("utf-8"), raw_filename, "job")

    # 2. Database Record
    candidate_id = _resolve_candidate_id(payload.candidate_id, payload.candidate_name)
    title = payload.title or _extract_title_if_missing(cleaned_text)
    job_id = repo.save_job(
        candidate_id=candidate_id,
        title=title,
        company=payload.company,
        source="text",
        raw_path=raw_storage_path,
        text=cleaned_text,
        is_synthetic=False,
    )

    # 3. Processing & Analyzing: Extract job skills with required / preferred importance
    job_skills_dict = skills.extract_job_skills(cleaned_text)
    repo.set_job_skills(job_id, job_skills_dict)

    job_row = repo.get_job(job_id)
    required = [sk for sk, imp in job_skills_dict.items() if imp == "required"]
    preferred = [sk for sk, imp in job_skills_dict.items() if imp == "preferred"]

    # 4. Serving
    return JobResponse(
        job_id=job_id,
        candidate_id=candidate_id,
        title=title,
        company=payload.company,
        source="text",
        raw_storage_path=raw_storage_path,
        storage_kind="Local File + MinIO" if storage.minio_enabled() else "Local Disk Storage",
        character_count=len(cleaned_text),
        extraction_method="direct_clean_text",
        required_skills=required,
        preferred_skills=preferred,
        total_skills_detected=len(job_skills_dict),
        preview_text=cleaned_text[:300] + ("..." if len(cleaned_text) > 300 else ""),
        created_at=str(job_row.created_at) if job_row else "",
    )


@router.post("/pdf", response_model=JobResponse, status_code=status.HTTP_201_CREATED,
             summary="Ingest Job Posting from PDF (PDF -> API -> Storage -> Processing -> Analyzing -> Serving)")
async def ingest_job_from_pdf(
    file: UploadFile = File(..., description="Job posting PDF file"),
    title: Optional[str] = Form(None, description="Optional job title"),
    company: Optional[str] = Form(None, description="Optional hiring company"),
    candidate_name: Optional[str] = Form("API User", description="Profile/Candidate name"),
) -> JobResponse:
    """
    Ingest a job posting from a PDF document:
    1. **API**: Accepts multipart PDF file upload.
    2. **Storage**: Saves original unmodified PDF bytes into storage.
    3. **Processing**: Extracts embedded PDF text using `pdfplumber` (with OCR fallback for scanned PDFs).
    4. **Analyzing**: Extracts skills (required and preferred).
    5. **Serving**: Returns stored job ID, raw path, extracted text preview, and analyzed skills.
    """
    filename = file.filename or "job.pdf"
    ext = extraction.file_extension(filename)
    if ext != "pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Expected a PDF file, but received '.{ext}'.",
        )

    data = await file.read()
    try:
        extraction.validate_upload(filename, data, ["pdf"])
    except extraction.ExtractionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    # Storage
    raw_storage_path = storage.save_raw(data, filename, "job")

    # Processing (Text Extraction)
    try:
        result = extraction.extract_text(data, filename, ["pdf"])
    except extraction.ExtractionError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    extracted_text = result.text.strip()
    if len(extracted_text) < 20:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The PDF did not yield enough readable text. Scanned PDFs require Tesseract OCR.",
        )

    final_title = title or _extract_title_if_missing(extracted_text, filename)
    cand = repo.get_or_create_candidate(candidate_name or "API User")
    job_id = repo.save_job(
        candidate_id=cand.id,
        title=final_title,
        company=company,
        source="pdf",
        raw_path=raw_storage_path,
        text=extracted_text,
        is_synthetic=False,
    )

    # Analyzing
    job_skills_dict = skills.extract_job_skills(extracted_text)
    repo.set_job_skills(job_id, job_skills_dict)

    required = [sk for sk, imp in job_skills_dict.items() if imp == "required"]
    preferred = [sk for sk, imp in job_skills_dict.items() if imp == "preferred"]
    job_row = repo.get_job(job_id)

    # Serving
    return JobResponse(
        job_id=job_id,
        candidate_id=cand.id,
        title=final_title,
        company=company,
        source="pdf",
        raw_storage_path=raw_storage_path,
        storage_kind="Local File + MinIO" if storage.minio_enabled() else "Local Disk Storage",
        character_count=len(extracted_text),
        extraction_method=result.method,
        required_skills=required,
        preferred_skills=preferred,
        total_skills_detected=len(job_skills_dict),
        preview_text=extracted_text[:300] + ("..." if len(extracted_text) > 300 else ""),
        created_at=str(job_row.created_at) if job_row else "",
    )


@router.post("/image", response_model=JobResponse, status_code=status.HTTP_201_CREATED,
             summary="Ingest Job Posting from Image (Image -> API -> Storage -> Processing -> Analyzing -> Serving)")
async def ingest_job_from_image(
    file: UploadFile = File(..., description="Job posting image (JPG, PNG, JPEG)"),
    title: Optional[str] = Form(None, description="Optional job title"),
    company: Optional[str] = Form(None, description="Optional hiring company"),
    candidate_name: Optional[str] = Form("API User", description="Profile/Candidate name"),
) -> JobResponse:
    """
    Ingest a job posting from an Image (screenshot, photo):
    1. **API**: Accepts image file upload.
    2. **Storage**: Saves original image bytes into raw storage.
    3. **Processing**: Runs Optical Character Recognition (OCR) via Tesseract to read text.
    4. **Analyzing**: Extracts required and preferred skills from the OCR text.
    5. **Serving**: Serves structured response with storage details and extracted skills.
    """
    filename = file.filename or "job.png"
    ext = extraction.file_extension(filename)
    if ext not in extraction.IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Expected an image file ({', '.join(extraction.IMAGE_TYPES)}), but received '.{ext}'.",
        )

    data = await file.read()
    try:
        extraction.validate_upload(filename, data, list(extraction.IMAGE_TYPES))
    except extraction.ExtractionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    # Storage
    raw_storage_path = storage.save_raw(data, filename, "job")

    # Processing via OCR
    try:
        result = extraction.extract_text(data, filename, list(extraction.IMAGE_TYPES))
    except extraction.ExtractionError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    extracted_text = result.text.strip()
    if len(extracted_text) < 15:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="OCR could not detect readable text from this image. Please ensure the image is clear and sharp.",
        )

    final_title = title or _extract_title_if_missing(extracted_text, filename)
    cand = repo.get_or_create_candidate(candidate_name or "API User")
    job_id = repo.save_job(
        candidate_id=cand.id,
        title=final_title,
        company=company,
        source="image",
        raw_path=raw_storage_path,
        text=extracted_text,
        is_synthetic=False,
    )

    # Analyzing
    job_skills_dict = skills.extract_job_skills(extracted_text)
    repo.set_job_skills(job_id, job_skills_dict)

    required = [sk for sk, imp in job_skills_dict.items() if imp == "required"]
    preferred = [sk for sk, imp in job_skills_dict.items() if imp == "preferred"]
    job_row = repo.get_job(job_id)

    # Serving
    return JobResponse(
        job_id=job_id,
        candidate_id=cand.id,
        title=final_title,
        company=company,
        source="image",
        raw_storage_path=raw_storage_path,
        storage_kind="Local File + MinIO" if storage.minio_enabled() else "Local Disk Storage",
        character_count=len(extracted_text),
        extraction_method=result.method,
        required_skills=required,
        preferred_skills=preferred,
        total_skills_detected=len(job_skills_dict),
        preview_text=extracted_text[:300] + ("..." if len(extracted_text) > 300 else ""),
        created_at=str(job_row.created_at) if job_row else "",
    )


@router.post("/upload", response_model=JobResponse, status_code=status.HTTP_201_CREATED,
             summary="Ingest Job Posting from Any Supported File (PDF / Image / TXT)")
async def ingest_job_file(
    file: UploadFile = File(..., description="Job file (PDF, PNG, JPG, JPEG, TXT)"),
    title: Optional[str] = Form(None),
    company: Optional[str] = Form(None),
    candidate_name: Optional[str] = Form("API User"),
) -> JobResponse:
    """Unified file ingestion router that detects file extension and runs the appropriate pipeline."""
    filename = file.filename or "job_upload"
    ext = extraction.file_extension(filename)
    if ext == "pdf":
        return await ingest_job_from_pdf(file, title, company, candidate_name)
    elif ext in extraction.IMAGE_TYPES:
        return await ingest_job_from_image(file, title, company, candidate_name)
    elif ext == "txt":
        data = await file.read()
        text = data.decode("utf-8", errors="replace")
        payload = JobTextInput(
            title=title or _extract_title_if_missing(text, filename),
            company=company,
            text=text,
            candidate_name=candidate_name,
        )
        return ingest_job_from_text(payload)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported format '.{ext}'. Supported formats: PDF, PNG, JPG, JPEG, TXT.",
        )


@router.get("", response_model=List[JobResponse], summary="List All Stored Job Postings (Serving)")
def list_stored_jobs(limit: int = 50) -> List[JobResponse]:
    """Retrieve all jobs stored in the system with their analyzed skills."""
    jobs = repo.list_jobs(limit=limit)
    out: List[JobResponse] = []
    for j in jobs:
        sk_dict = repo.get_job_skills(j.id)
        req = [k for k, v in sk_dict.items() if v == "required"]
        pref = [k for k, v in sk_dict.items() if v == "preferred"]
        out.append(JobResponse(
            job_id=j.id,
            candidate_id=j.candidate_id,
            title=j.title,
            company=j.company,
            source=j.source,
            raw_storage_path=j.raw_path,
            storage_kind="Local File + MinIO" if storage.minio_enabled() else "Local Disk Storage",
            character_count=len(j.text),
            extraction_method="database_storage",
            required_skills=req,
            preferred_skills=pref,
            total_skills_detected=len(sk_dict),
            preview_text=j.text[:200] + ("..." if len(j.text) > 200 else ""),
            created_at=str(j.created_at),
        ))
    return out


@router.get("/{job_id}", response_model=JobResponse, summary="Get Stored Job Posting Details (Serving)")
def get_stored_job(job_id: int) -> JobResponse:
    """Retrieve a single stored job by its ID, with its raw storage path and analyzed skills."""
    j = repo.get_job(job_id)
    if not j:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job {job_id} not found.")

    sk_dict = repo.get_job_skills(j.id)
    req = [k for k, v in sk_dict.items() if v == "required"]
    pref = [k for k, v in sk_dict.items() if v == "preferred"]

    return JobResponse(
        job_id=j.id,
        candidate_id=j.candidate_id,
        title=j.title,
        company=j.company,
        source=j.source,
        raw_storage_path=j.raw_path,
        storage_kind="Local File + MinIO" if storage.minio_enabled() else "Local Disk Storage",
        character_count=len(j.text),
        extraction_method="database_storage",
        required_skills=req,
        preferred_skills=pref,
        total_skills_detected=len(sk_dict),
        preview_text=j.text[:300] + ("..." if len(j.text) > 300 else ""),
        created_at=str(j.created_at),
    )
