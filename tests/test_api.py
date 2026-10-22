"""Integration tests for the FitCheck REST API.

Tests the pipeline:
Jobs [PDF / Image / Text] -> API -> Storage -> Processing -> Analyzing -> Serving
Resumes [PDF / DOCX]     -> Storage -> Processing -> Analyzing -> Serving
"""
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from api.main import app
from tests.sample_files import CV_TEXT, JOB_TEXT, cv_docx_bytes, text_pdf_bytes

client = TestClient(app)


def test_api_root_and_health():
    """Verify API root endpoint and health diagnostics."""
    r_root = client.get("/")
    assert r_root.status_code == 200
    data_root = r_root.json()
    assert "architecture" in data_root
    assert "Jobs" in data_root["architecture"]["jobs_pipeline"]

    r_health = client.get("/api/v1/health")
    assert r_health.status_code == 200
    data_health = r_health.json()
    assert data_health["status"] == "healthy"
    assert "storage" in data_health
    assert "database" in data_health
    assert "ocr_engine" in data_health


def test_job_text_ingestion():
    """Test: Text -> API -> Storage -> Processing -> Analyzing -> Serving."""
    payload = {
        "title": "Senior Data Analyst",
        "company": "Netsol Technologies",
        "text": """Senior Data Analyst
Requirements:
- Strong Python, SQL, and Pandas experience.
- Machine Learning and Statistics knowledge.
Nice to have:
- Docker and Git.
""",
        "candidate_name": "Test User",
    }
    r = client.post("/api/v1/jobs/text", json=payload)
    assert r.status_code == 201
    res = r.json()

    assert res["job_id"] > 0
    assert res["title"] == "Senior Data Analyst"
    assert res["company"] == "Netsol Technologies"
    assert res["source"] == "text"
    assert res["raw_storage_path"] is not None
    # Check that storage file physically exists
    assert Path(res["raw_storage_path"]).exists()

    # Verify Analyzing stage: Required vs Preferred skill extraction
    req = res["required_skills"]
    pref = res["preferred_skills"]
    assert "Python" in req
    assert "SQL" in req
    assert "Pandas" in req
    assert "Docker" in pref or "Git" in pref


def test_job_pdf_ingestion():
    """Test: PDF -> API -> Storage -> Processing -> Analyzing -> Serving."""
    pdf_data = text_pdf_bytes(JOB_TEXT)
    files = {"file": ("data_engineer_job.pdf", pdf_data, "application/pdf")}
    data = {"title": "Data Analyst (PDF Upload)", "candidate_name": "Test User"}

    r = client.post("/api/v1/jobs/pdf", files=files, data=data)
    assert r.status_code == 201
    res = r.json()

    assert res["job_id"] > 0
    assert res["source"] == "pdf"
    assert res["raw_storage_path"].endswith(".pdf")
    assert Path(res["raw_storage_path"]).exists()
    assert res["character_count"] > 30
    assert len(res["required_skills"]) > 0


def test_resume_pdf_ingestion():
    """Test: Resume PDF -> Storage -> Processing -> Analyzing -> Serving."""
    pdf_data = text_pdf_bytes(CV_TEXT)
    files = {"file": ("ayesha_khan_cv.pdf", pdf_data, "application/pdf")}
    data = {"candidate_name": "Ayesha Khan"}

    r = client.post("/api/v1/resumes/upload", files=files, data=data)
    assert r.status_code == 201
    res = r.json()

    assert res["resume_id"] > 0
    assert res["file_type"] == "pdf"
    assert res["raw_storage_path"].endswith(".pdf")
    assert Path(res["raw_storage_path"]).exists()

    # Verify Analyzing: Candidate skills
    skills = res["skills"]
    assert "Python" in skills
    assert "Excel" in skills
    assert "Pandas" in skills


def test_resume_docx_ingestion():
    """Test: Resume DOCX -> Storage -> Processing -> Analyzing -> Serving."""
    docx_data = cv_docx_bytes(CV_TEXT)
    files = {"file": ("ayesha_cv.docx", docx_data, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    data = {"candidate_name": "Ayesha Khan DOCX"}

    r = client.post("/api/v1/resumes/upload", files=files, data=data)
    assert r.status_code == 201
    res = r.json()

    assert res["resume_id"] > 0
    assert res["file_type"] == "docx"
    assert res["raw_storage_path"].endswith(".docx")
    assert Path(res["raw_storage_path"]).exists()
    assert "Python" in res["skills"]


def test_match_analysis_and_serving():
    """Test: Analyzing -> Serving (Match score and skill gaps)."""
    # 1. Ingest Job via API
    job_resp = client.post("/api/v1/jobs/text", json={
        "title": "Python Developer",
        "text": JOB_TEXT,
        "candidate_name": "Match Candidate",
    }).json()

    # 2. Ingest Resume via API
    resume_resp = client.post(
        "/api/v1/resumes/upload",
        files={"file": ("cv.pdf", text_pdf_bytes(CV_TEXT), "application/pdf")},
        data={"candidate_name": "Match Candidate"},
    ).json()

    # 3. Request Match Analysis
    match_payload = {
        "resume_id": resume_resp["resume_id"],
        "job_id": job_resp["job_id"],
        "skill_weight": 0.70,
        "preferred_weight": 0.50,
    }
    r = client.post("/api/v1/analysis/match", json=match_payload)
    assert r.status_code == 200
    res = r.json()

    assert res["final_score"] > 0
    assert res["skill_score"] > 0
    assert res["text_similarity"] >= 0
    assert "Python" in res["matched_skills"]
    assert "SQL" in res["missing_required_skills"]
    assert res["disclaimer"] != ""


def test_end_to_end_pipeline_api():
    """Test full single-call pipeline with Job PDF and Resume PDF."""
    r = client.post(
        "/api/v1/analysis/end-to-end",
        files={
            "resume_file": ("resume.pdf", text_pdf_bytes(CV_TEXT), "application/pdf"),
            "job_file": ("job.pdf", text_pdf_bytes(JOB_TEXT), "application/pdf"),
        },
        data={"job_title": "Full Stack Data Scientist", "candidate_name": "EndToEnd User"},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["pipeline_status"] == "SUCCESS"
    assert "pipeline_architecture" in data
    assert "match_analysis" in data
    assert data["match_analysis"]["final_score"] > 0
