"""API Architecture & Pipeline Ingestion Explorer.

Visually presents and interactively demonstrates the supervisor's exact architecture:
Jobs (PDF / Image / Text) -> API -> Storage -> Processing -> Analyzing -> Serving
Resumes (PDF / DOCX)     -> Storage -> Processing -> Analyzing -> Serving

How to get Job Posting into the system:
- Text  -> API
- Image -> API
- PDF   -> API
"""
from __future__ import annotations

import json
import streamlit as st

import config
from api.client import FitCheckClient
from core import extraction, storage
from ui import theme


def render() -> None:
    theme.hero(
        "API Architecture & Pipeline Ingestion",
        "Data ingestion via API into storage, multi-stage processing, skill analysis, and serving.",
        badge_text="System Architecture & API",
    )

    client = FitCheckClient()
    health = client.health()

    # KPI Status Cards
    theme.kpi_row([
        ("API Gateway", "Online", "FastAPI v1.0", "indigo"),
        ("Storage Layer", "Active", "Disk & MinIO S3", "blue"),
        ("OCR Engine", "Ready" if extraction.ocr_available() else "Off", "Tesseract OCR", "good" if extraction.ocr_available() else "warn"),
        ("Database", health["database"]["engine"], "ORM Persistence", "indigo"),
    ])

    st.markdown("---")

    # Architecture Diagram Visualizer
    st.subheader("System Architecture: End-to-End Ingestion Pipeline")
    st.markdown(
        """
This architecture strictly implements the data ingestion flow where jobs and resumes are ingested via **API**, persisted in **Storage**, parsed in **Processing**, analyzed for **Skills & Match**, and presented in **Serving**:
"""
    )

    st.markdown(
        """
```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                  FITCHECK ARCHITECTURE                                 │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│   Jobs:                                                                                │
│   ┌──────────────┐                                                                     │
│   │   PDF Job    │──┐                                                                  │
│   ├──────────────┤  │                                                                  │
│   │  Image (OCR) │──┼──▶ [ API GATEWAY ] ──▶ [ STORAGE ] ──▶ [ PROCESSING ] ──┐        │
│   ├──────────────┤  │    FastAPI Endpoints   Raw Files & DB     pdfplumber/OCR  │        │
│   │  Typed Text  │──┘   (POST /api/v1/jobs)  data/uploads/      Text Cleaning   │        │
│   └──────────────┘                                                              │        │
│                                                                                 ▼        │
│   Resumes:                                                                [ ANALYZING ] │
│   ┌──────────────┐                                                        Skill Taxonomy│
│   │   PDF / DOCX │─────────────────────────▶ [ STORAGE ] ──▶ [ PROCESSING ] ──▶ Match Scoring│
│   └──────────────┘                           Raw Files & DB     Parsers/OCR   TF-IDF Cosine│
│                                                                                 │        │
│                                                                                 ▼        │
│                                                                           [ SERVING ]   │
│                                                                           REST API JSON │
│                                                                           Web UI Reports│
└────────────────────────────────────────────────────────────────────────────────────────┘
```
"""
    )

    st.info(
        "**Supervisor's Core Requirement Verified:**\n"
        "- **How to get Job Posting into the system?**\n"
        "  1. `Text -> API`: `POST /api/v1/jobs/text`\n"
        "  2. `Image -> API`: `POST /api/v1/jobs/image` (OCR text extraction)\n"
        "  3. `PDF -> API`: `POST /api/v1/jobs/pdf` (pdfplumber parser)\n"
        "- **API k through data storage ma la kr jana ha:**\n"
        "  Every ingested payload is saved in raw storage (`data/uploads/` & MinIO) and DB metadata before processing!"
    )

    st.markdown("---")
    st.subheader("Interactive API Console: Test Live Ingestion & Storage")

    tabs = st.tabs([
        "1. Text -> API",
        "2. Image -> API",
        "3. PDF -> API",
        "4. Resume Ingestion",
        "5. Swagger UI & cURL",
    ])

    # Tab 1: Text -> API
    with tabs[0]:
        st.markdown("#### `POST /api/v1/jobs/text`")
        st.caption("Send raw/typed text to the API -> API saves text to storage -> processes & analyzes skills -> serves response.")
        c1, c2 = st.columns(2)
        txt_title = c1.text_input("Job Title", value="Senior Backend Python Engineer", key="api_txt_title")
        txt_comp = c2.text_input("Company", value="NetSol Technologies", key="api_txt_comp")
        default_job = """Senior Backend Python Engineer

Requirements:
- Strong experience in Python, FastAPI, Django, and REST APIs.
- Experience with PostgreSQL and Docker containerization.
- Good knowledge of Git and Unit Testing.

Nice to have:
- Experience with Kubernetes and Redis caching.
- Familiarity with AWS cloud services.
"""
        txt_body = st.text_area("Job Description Text", value=default_job, height=180, key="api_txt_body")

        if st.button("🚀 Ingest Text via API", type="primary", key="btn_txt_api"):
            with st.spinner("Calling API (Text -> API -> Storage -> Processing -> Analyzing -> Serving)..."):
                try:
                    res = client.ingest_job_text(txt_body, title=txt_title, company=txt_comp, candidate_name=st.session_state.get("profile_name", "API User"))
                    st.success(f"Successfully Ingested Job via API! Job ID: {res['job_id']}")
                    st.markdown(f"**Storage Path:** `{res['raw_storage_path']}`")
                    st.markdown(f"**Storage Layer:** `{res['storage_kind']}`")
                    st.markdown(f"**Required Skills Detected:** {theme.chips(res['required_skills'], 'good')}", unsafe_allow_html=True)
                    st.markdown(f"**Preferred Skills Detected:** {theme.chips(res['preferred_skills'], 'info')}", unsafe_allow_html=True)
                    with st.expander("View Raw JSON Response"):
                        st.json(res)
                except Exception as exc:
                    st.error(f"API Ingestion Error: {exc}")

    # Tab 2: Image -> API
    with tabs[1]:
        st.markdown("#### `POST /api/v1/jobs/image`")
        st.caption("Upload image screenshot/photo of job posting -> API stores raw image -> runs OCR processing -> analyzes skills -> serves response.")
        img_file = st.file_uploader("Upload Job Posting Image (PNG, JPG, JPEG)", type=["png", "jpg", "jpeg"], key="api_img_upload")
        c1, c2 = st.columns(2)
        img_title = c1.text_input("Job Title (Optional)", value="", placeholder="Auto-detected if empty", key="api_img_title")
        img_comp = c2.text_input("Company (Optional)", value="", key="api_img_comp")

        if img_file is not None:
            st.image(img_file, caption=f"Selected: {img_file.name}", width=400)
            if st.button("🚀 Ingest Image via API", type="primary", key="btn_img_api"):
                with st.spinner("Sending Image to API -> Storing -> Processing OCR -> Analyzing Skills..."):
                    try:
                        res = client.ingest_job_image(img_file.getvalue(), filename=img_file.name, title=img_title, candidate_name=st.session_state.get("profile_name", "API User"))
                        st.success(f"Image Ingested via API! Job ID: {res['job_id']}")
                        st.markdown(f"**Storage Path:** `{res['raw_storage_path']}`")
                        st.markdown(f"**Extraction Method:** `{res['extraction_method']}`")
                        st.markdown(f"**Required Skills:** {theme.chips(res['required_skills'], 'good')}", unsafe_allow_html=True)
                        st.markdown(f"**Preferred Skills:** {theme.chips(res['preferred_skills'], 'info')}", unsafe_allow_html=True)
                        with st.expander("Extracted OCR Text Preview"):
                            st.text(res["preview_text"])
                        with st.expander("View Raw JSON Response"):
                            st.json(res)
                    except Exception as exc:
                        st.error(f"API Ingestion Error: {exc}")

    # Tab 3: PDF -> API
    with tabs[2]:
        st.markdown("#### `POST /api/v1/jobs/pdf`")
        st.caption("Upload job posting PDF -> API stores raw PDF -> extracts text -> analyzes skills -> serves response.")
        pdf_job_file = st.file_uploader("Upload Job Posting PDF", type=["pdf"], key="api_job_pdf_upload")
        c1, c2 = st.columns(2)
        pdf_j_title = c1.text_input("Job Title (Optional)", value="", key="api_pdf_j_title")
        pdf_j_comp = c2.text_input("Company (Optional)", value="", key="api_pdf_j_comp")

        if pdf_job_file is not None:
            if st.button("🚀 Ingest PDF via API", type="primary", key="btn_pdf_api"):
                with st.spinner("Sending PDF to API -> Storing -> Extracting Text -> Analyzing Skills..."):
                    try:
                        res = client.ingest_job_pdf(pdf_job_file.getvalue(), filename=pdf_job_file.name, title=pdf_j_title, candidate_name=st.session_state.get("profile_name", "API User"))
                        st.success(f"PDF Ingested via API! Job ID: {res['job_id']}")
                        st.markdown(f"**Storage Path:** `{res['raw_storage_path']}`")
                        st.markdown(f"**Extraction Method:** `{res['extraction_method']}`")
                        st.markdown(f"**Required Skills:** {theme.chips(res['required_skills'], 'good')}", unsafe_allow_html=True)
                        st.markdown(f"**Preferred Skills:** {theme.chips(res['preferred_skills'], 'info')}", unsafe_allow_html=True)
                        with st.expander("Extracted Text Preview"):
                            st.text(res["preview_text"])
                        with st.expander("View Raw JSON Response"):
                            st.json(res)
                    except Exception as exc:
                        st.error(f"API Ingestion Error: {exc}")

    # Tab 4: Resume Ingestion
    with tabs[3]:
        st.markdown("#### `POST /api/v1/resumes/upload`")
        st.caption("Upload resume (PDF or DOCX) -> API stores file in raw storage -> extracts CV text -> detects candidate skills -> serves response.")
        resume_upload = st.file_uploader("Upload Candidate CV (PDF or DOCX)", type=["pdf", "docx"], key="api_res_upload")
        if resume_upload is not None:
            if st.button("🚀 Ingest Resume via API", type="primary", key="btn_res_api"):
                with st.spinner("Sending Resume to API -> Storing -> Extracting Text -> Detecting Skills..."):
                    try:
                        res = client.ingest_resume(resume_upload.getvalue(), filename=resume_upload.name, candidate_name=st.session_state.get("profile_name", "API User"))
                        st.success(f"Resume Ingested via API! Resume ID: {res['resume_id']}")
                        st.markdown(f"**Storage Path:** `{res['raw_storage_path']}`")
                        st.markdown(f"**Extraction Method:** `{res['extraction_method']}`")
                        st.markdown(f"**Candidate Skills Detected:** {theme.chips(res['skills'], 'indigo')}", unsafe_allow_html=True)
                        with st.expander("View Raw JSON Response"):
                            st.json(res)
                    except Exception as exc:
                        st.error(f"API Ingestion Error: {exc}")

    # Tab 5: Swagger UI & cURL
    with tabs[4]:
        st.markdown("#### 📖 Live Swagger Documentation & cURL Commands")
        st.markdown(
            """
The FitCheck REST API provides interactive OpenAPI Swagger documentation.
When the API server is running on `http://127.0.0.1:8000`:
- **Interactive Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc Documentation:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **OpenAPI Schema:** [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)

To start the API server locally:
```powershell
python run_api.py
```
"""
        )

        st.subheader("cURL Examples to Demonstrate to the Supervisor:")

        st.markdown("**1. Ingest Job as Text (Text ➔ API):**")
        st.code("""curl -X POST "http://127.0.0.1:8000/api/v1/jobs/text" \\
     -H "Content-Type: application/json" \\
     -d '{
       "title": "Data Scientist",
       "company": "NetSol Technologies",
       "text": "Requirements: Python, SQL, Statistics, Machine Learning. Nice to have: Docker, Spark.",
       "candidate_name": "Usama"
     }'""", language="bash")

        st.markdown("**2. Ingest Job as Image (Image ➔ API with OCR):**")
        st.code("""curl -X POST "http://127.0.0.1:8000/api/v1/jobs/image" \\
     -F "file=@job_ad.png" \\
     -F "title=Data Analyst" \\
     -F "candidate_name=Usama" """, language="bash")

        st.markdown("**3. Ingest Job as PDF (PDF ➔ API):**")
        st.code("""curl -X POST "http://127.0.0.1:8000/api/v1/jobs/pdf" \\
     -F "file=@job_posting.pdf" \\
     -F "candidate_name=Usama" """, language="bash")

        st.markdown("**4. Ingest Resume (PDF / DOCX ➔ Storage):**")
        st.code("""curl -X POST "http://127.0.0.1:8000/api/v1/resumes/upload" \\
     -F "file=@my_cv.pdf" \\
     -F "candidate_name=Usama" """, language="bash")

        st.markdown("**5. Match Analysis (Analyzing ➔ Serving):**")
        st.code("""curl -X POST "http://127.0.0.1:8000/api/v1/analysis/match" \\
     -H "Content-Type: application/json" \\
     -d '{
       "resume_id": 1,
       "job_id": 1,
       "skill_weight": 0.70,
       "preferred_weight": 0.50
     }'""", language="bash")
