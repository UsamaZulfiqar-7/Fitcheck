"""Analysis and Matching Pipeline API Routes.

Implements the Analyzing -> Serving phase of the pipeline:
Computes skill gaps, weighted matching scores, TF-IDF semantic similarities,
and serves comprehensive fit reports.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from api.schemas import MatchRequest, MatchResponse
from core import extraction, matching, pipeline, repository as repo, skills, storage

router = APIRouter(prefix="/api/v1/analysis", tags=["Analysis, Scoring & Serving"])


@router.post("/match", response_model=MatchResponse, status_code=status.HTTP_200_OK,
             summary="Run Match Analysis between Stored Resume and Job (Analyzing -> Serving)")
def run_match_analysis(payload: MatchRequest) -> MatchResponse:
    """
    Run the skill gap and score calculation pipeline on an already stored Resume and Job:
    1. **Analyzing**: Extracts and aligns skills between CV and Job description.
    2. Computes weighted Skill Match score (Required skills = 1.0, Preferred = preferred_weight).
    3. Computes TF-IDF Cosine Text Similarity.
    4. Computes Final Score = (skill_weight * skill_score) + ((1 - skill_weight) * text_similarity).
    5. **Serving**: Serves score breakdown, matched skills, and missing skills.
    """
    resume = repo.get_resume(payload.resume_id)
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume {payload.resume_id} not found in database storage.",
        )

    job = repo.get_job(payload.job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {payload.job_id} not found in database storage.",
        )

    cand_id = payload.candidate_id or resume.candidate_id
    settings = {
        "skill_weight": payload.skill_weight if payload.skill_weight is not None else 0.70,
        "preferred_weight": payload.preferred_weight if payload.preferred_weight is not None else 0.50,
        "use_semantic": payload.use_semantic if payload.use_semantic is not None else False,
    }

    try:
        match_id, result = pipeline.analyze(cand_id, payload.resume_id, payload.job_id, settings)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis pipeline failed: {type(exc).__name__}: {exc}",
        )

    return MatchResponse(
        match_id=match_id,
        candidate_id=cand_id,
        resume_id=payload.resume_id,
        job_id=payload.job_id,
        final_score=result.final_score,
        skill_score=result.skill_score,
        text_similarity=result.text_similarity,
        skill_weight=result.skill_weight,
        text_weight=result.text_weight,
        matched_skills=result.matched,
        missing_required_skills=result.missing_required,
        missing_preferred_skills=result.missing_preferred,
        additional_skills=result.additional,
        score_breakdown=result.to_dict(),
        disclaimer=matching.DISCLAIMER,
    )


@router.get("/{match_id}", response_model=MatchResponse, summary="Get Stored Match Analysis Report (Serving)")
def get_match_report(match_id: int) -> MatchResponse:
    """Retrieve an existing match report from storage."""
    m = repo.get_match(match_id)
    if not m:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Match record {match_id} not found.")

    details = m.details or {}
    return MatchResponse(
        match_id=m.id,
        candidate_id=m.candidate_id,
        resume_id=m.resume_id,
        job_id=m.job_id,
        final_score=m.final_score,
        skill_score=m.skill_score,
        text_similarity=m.text_similarity,
        skill_weight=m.skill_weight,
        text_weight=m.text_weight,
        matched_skills=details.get("matched", []),
        missing_required_skills=details.get("missing_required", []),
        missing_preferred_skills=details.get("missing_preferred", []),
        additional_skills=details.get("additional", []),
        score_breakdown=details,
        disclaimer=matching.DISCLAIMER,
    )


@router.post("/end-to-end", status_code=status.HTTP_201_CREATED,
             summary="End-to-End Pipeline: Ingest Job & Resume -> Storage -> Processing -> Analyzing -> Serving")
async def run_end_to_end_pipeline(
    resume_file: UploadFile = File(..., description="Resume file (PDF, DOCX)"),
    job_file: Optional[UploadFile] = File(None, description="Job posting file (PDF, Image, TXT)"),
    job_text: Optional[str] = Form(None, description="Job posting text if no job file uploaded"),
    job_title: Optional[str] = Form("Job Position", description="Job title"),
    candidate_name: Optional[str] = Form("API User", description="Candidate profile name"),
) -> Dict[str, Any]:
    """
    Executes the complete system architecture end-to-end in a single API call:
    1. Ingests Job (from PDF, Image, or Text) via API.
    2. Ingests Resume (PDF/DOCX) via API.
    3. Persists raw bytes for both to Storage (Local / MinIO).
    4. Runs Processing (Text Extraction / OCR).
    5. Runs Analyzing (Skill extraction, gap detection, matching score).
    6. Serves complete comprehensive JSON result.
    """
    cand = repo.get_or_create_candidate(candidate_name or "API User")

    # 1. Process Resume
    resume_data = await resume_file.read()
    r_ext = extraction.file_extension(resume_file.filename or "resume.pdf")
    try:
        extraction.validate_upload(resume_file.filename, resume_data, extraction.RESUME_TYPES)
        r_result = extraction.extract_text(resume_data, resume_file.filename, extraction.RESUME_TYPES)
    except extraction.ExtractionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Resume error: {exc}")

    r_storage = storage.save_raw(resume_data, resume_file.filename, "resume")
    resume_id = repo.save_resume(
        cand.id, resume_file.filename, r_ext, len(resume_data), r_storage,
        r_result.method, r_result.text, r_result.text
    )
    cand_skills = skills.extract_skills(r_result.text)
    repo.set_resume_skills(resume_id, cand_skills)

    # 2. Process Job (either from file or from text)
    j_extracted_text = ""
    j_storage = None
    j_source = "text"

    if job_file and job_file.filename:
        job_data = await job_file.read()
        j_ext = extraction.file_extension(job_file.filename)
        if j_ext not in extraction.JOB_TYPES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"Unsupported job file format .{j_ext}")
        extraction.validate_upload(job_file.filename, job_data, extraction.JOB_TYPES)
        j_result = extraction.extract_text(job_data, job_file.filename, extraction.JOB_TYPES)
        j_extracted_text = j_result.text.strip()
        j_storage = storage.save_raw(job_data, job_file.filename, "job")
        j_source = "image" if j_ext in extraction.IMAGE_TYPES else j_ext
    elif job_text and job_text.strip():
        j_extracted_text = extraction.clean_text(job_text)
        j_storage = storage.save_raw(j_extracted_text.encode("utf-8"), "job_description.txt", "job")
        j_source = "text"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either a job_file (PDF/Image/TXT) or job_text must be provided.",
        )

    job_id = repo.save_job(cand.id, job_title or "Job Position", None, j_source, j_storage, j_extracted_text)
    j_skills = skills.extract_job_skills(j_extracted_text)
    repo.set_job_skills(job_id, j_skills)

    # 3. Match Analysis
    match_id, match_result = pipeline.analyze(cand.id, resume_id, job_id)

    # 4. Serving complete report
    return {
        "pipeline_status": "SUCCESS",
        "pipeline_architecture": {
            "ingestion": f"API (Job format: {j_source}, Resume format: {r_ext})",
            "storage": {
                "resume_raw_path": r_storage,
                "job_raw_path": j_storage,
                "database_record_ids": {"resume_id": resume_id, "job_id": job_id, "match_id": match_id},
            },
            "processing": {
                "resume_extraction_method": r_result.method,
                "job_extraction_method": "tesseract_ocr" if j_source == "image" else j_source,
            },
            "analyzing": {
                "candidate_skills_count": len(cand_skills),
                "job_skills_count": len(j_skills),
                "final_match_score": match_result.final_score,
            },
            "serving": "Served via FitCheck REST API",
        },
        "match_analysis": {
            "match_id": match_id,
            "final_score": match_result.final_score,
            "skill_score": match_result.skill_score,
            "text_similarity": match_result.text_similarity,
            "matched_skills": match_result.matched,
            "missing_required_skills": match_result.missing_required,
            "missing_preferred_skills": match_result.missing_preferred,
            "additional_skills": match_result.additional,
        },
    }
