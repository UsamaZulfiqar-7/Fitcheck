"""Resume Ingestion API Routes.

Implements the flow:
Resumes -> [PDF / DOCX] -> Storage -> Processing -> Analyzing -> Serving
"""
from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from api.schemas import ResumeResponse
from core import extraction, repository as repo, skills, storage

router = APIRouter(prefix="/api/v1/resumes", tags=["Resumes Ingestion & Processing"])


@router.post("/upload", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED,
             summary="Ingest Resume (PDF / DOCX -> Storage -> Processing -> Analyzing -> Serving)")
async def upload_resume(
    file: UploadFile = File(..., description="Resume file (PDF, DOCX, TXT)"),
    candidate_name: Optional[str] = Form("API User", description="Candidate / Profile name"),
) -> ResumeResponse:
    """
    Ingest a candidate CV/Resume into the system:
    1. **Upload & Ingestion**: Receives candidate resume document (PDF or DOCX).
    2. **Storage**: Saves raw bytes into object/disk storage (`storage.save_raw`).
    3. **Processing**: Extracts CV text using `pdfplumber` (PDF) or `python-docx` (DOCX).
    4. **Analyzing**: Extracts candidate skills and normalizes them against the skill taxonomy.
    5. **Serving**: Returns stored resume record with storage path and detected candidate skills.
    """
    filename = file.filename or "resume.pdf"
    ext = extraction.file_extension(filename)
    if ext not in extraction.RESUME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported resume file type '.{ext}'. Allowed types: {', '.join(extraction.RESUME_TYPES).upper()}.",
        )

    data = await file.read()
    try:
        extraction.validate_upload(filename, data, extraction.RESUME_TYPES)
    except extraction.ExtractionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    # 1. Storage: save raw original bytes
    raw_storage_path = storage.save_raw(data, filename, "resume")

    # 2. Processing: extract text
    try:
        result = extraction.extract_text(data, filename, extraction.RESUME_TYPES)
    except extraction.ExtractionError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    extracted_text = result.text.strip()
    if len(extracted_text) < 30:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The resume document did not contain enough readable text (at least 30 characters required).",
        )

    # 3. Database persistence
    cand = repo.get_or_create_candidate(candidate_name or "API User")
    resume_id = repo.save_resume(
        candidate_id=cand.id,
        filename=filename,
        file_type=ext,
        size=len(data),
        raw_path=raw_storage_path,
        method=result.method,
        original_text=extracted_text,
        reviewed_text=extracted_text,
    )

    # 4. Analyzing: extract candidate skills and persist mapping
    cand_skills = skills.extract_skills(extracted_text)
    repo.set_resume_skills(resume_id, cand_skills)

    resume_row = repo.get_resume(resume_id)

    # 5. Serving
    return ResumeResponse(
        resume_id=resume_id,
        candidate_id=cand.id,
        candidate_name=cand.display_name,
        filename=filename,
        file_type=ext,
        file_size_bytes=len(data),
        raw_storage_path=raw_storage_path,
        storage_kind="Local File + MinIO" if storage.minio_enabled() else "Local Disk Storage",
        extraction_method=result.method,
        warnings=result.warnings,
        skills=cand_skills,
        total_skills=len(cand_skills),
        preview_text=extracted_text[:300] + ("..." if len(extracted_text) > 300 else ""),
        created_at=str(resume_row.created_at) if resume_row else "",
    )


@router.get("", response_model=List[ResumeResponse], summary="List All Stored Resumes (Serving)")
def list_stored_resumes(limit: int = 50) -> List[ResumeResponse]:
    """Retrieve all resumes currently stored in the system."""
    resumes = repo.list_resumes(limit=limit)
    out: List[ResumeResponse] = []
    for r in resumes:
        cand_skills = repo.get_resume_skills(r.id)
        cand_row = repo.get_or_create_candidate("User")
        out.append(ResumeResponse(
            resume_id=r.id,
            candidate_id=r.candidate_id,
            candidate_name=f"Profile {r.candidate_id}",
            filename=r.filename,
            file_type=r.file_type,
            file_size_bytes=r.file_size_bytes,
            raw_storage_path=r.raw_path,
            storage_kind="Local File + MinIO" if storage.minio_enabled() else "Local Disk Storage",
            extraction_method=r.extraction_method,
            warnings=[],
            skills=cand_skills,
            total_skills=len(cand_skills),
            preview_text=r.reviewed_text[:200] + ("..." if len(r.reviewed_text) > 200 else ""),
            created_at=str(r.created_at),
        ))
    return out


@router.get("/{resume_id}", response_model=ResumeResponse, summary="Get Stored Resume Details (Serving)")
def get_stored_resume(resume_id: int) -> ResumeResponse:
    """Retrieve details for a single stored resume by ID."""
    r = repo.get_resume(resume_id)
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Resume {resume_id} not found.")

    cand_skills = repo.get_resume_skills(r.id)
    return ResumeResponse(
        resume_id=r.id,
        candidate_id=r.candidate_id,
        candidate_name=f"Profile {r.candidate_id}",
        filename=r.filename,
        file_type=r.file_type,
        file_size_bytes=r.file_size_bytes,
        raw_storage_path=r.raw_path,
        storage_kind="Local File + MinIO" if storage.minio_enabled() else "Local Disk Storage",
        extraction_method=r.extraction_method,
        warnings=[],
        skills=cand_skills,
        total_skills=len(cand_skills),
        preview_text=r.reviewed_text[:300] + ("..." if len(r.reviewed_text) > 300 else ""),
        created_at=str(r.created_at),
    )
