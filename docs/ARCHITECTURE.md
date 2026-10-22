# FitCheck - Architecture

![architecture](architecture.png)

## Layers

| Layer | Modules | Responsibility |
|---|---|---|
| REST API Gateway | `api/main.py`, `api/routes/*.py`, `api/schemas.py`, `api/client.py` | FastAPI endpoints for Jobs (Text/Image/PDF), Resumes, Analysis, and Health |
| Presentation | `app.py`, `ui/pages/*.py`, `ui/theme.py`, `ui/charts.py`, `ui/state.py` | Streamlit pages, interactive API explorer, charts, session state |
| Pipeline | `core/pipeline.py` | Orchestrates the stages: analyse, add a skill to the CV, save an edited CV |
| Storage & Ingestion | `core/storage.py`, `core/extraction.py` | Persists original bytes to `data/uploads/` & MinIO S3; extracts text (OCR fallback) |
| Skill intelligence | `core/taxonomy.py`, `core/skills.py`, `core/onet.py` | Rule-based extraction, normalisation, required/preferred detection, optional O*NET occupation context |
| Scoring | `core/matching.py` | Skill match, TF-IDF cosine similarity, optional semantic similarity, weighted final score, score explanation |
| Learning | `core/learning_content.py`, `core/content/*.py`, `core/ai.py` | Curated lessons, starter paths, practice questions, resources, optional AI notes |
| CV | `core/cv_builder.py` | Parse CV sections, safely add a skill, export DOCX/PDF |
| Persistence | `core/db.py`, `core/repository.py` | SQLAlchemy models, PostgreSQL primary / SQLite fallback, all reads and writes |
| Reporting | `core/report.py` | Downloadable PDF match report |

## End-to-End Data Pipeline Architecture

```text
Jobs    ---> [PDF / Image / Text] ---API---> Storage ---> Processing ---> Analyzing ---> Serving
Resumes ---> [PDF / DOCX] -----------------> Storage ---> Processing ---> Analyzing ---> Serving

How to get Job Posting into the system:
- Text  -> API  (POST /api/v1/jobs/text)
- Image -> API  (POST /api/v1/jobs/image)
- PDF   -> API  (POST /api/v1/jobs/pdf)
```

1. **API Ingestion Layer**:
   - `POST /api/v1/jobs/text` - Ingests typed / pasted raw job text.
   - `POST /api/v1/jobs/image` - Ingests image job ads (JPG, PNG, JPEG).
   - `POST /api/v1/jobs/pdf` - Ingests PDF job descriptions.
   - `POST /api/v1/resumes/upload` - Ingests candidate CVs (PDF, DOCX, TXT).
2. **Storage Layer**:
   - Unmodified original bytes are saved to local filesystem (`data/uploads/`) and optionally mirrored to MinIO/S3 object storage.
   - Relational records are created in PostgreSQL / SQLite linking `raw_path`, metadata, and timestamps.
3. **Processing Layer**:
   - Embedded text extraction via `pdfplumber` (PDF) and `python-docx` (DOCX).
   - Optical Character Recognition (OCR) via Tesseract for scanned documents and images.
   - Text cleaning, line break standardization, and title extraction.
4. **Analyzing Layer**:
   - Skill taxonomy matching and alias normalization.
   - Job requirements classification: **Required** vs. **Preferred (Nice to have)**.
   - Candidate skill extraction from CV.
   - TF-IDF vectorization and Cosine Similarity calculation.
   - Weighted match score computation: `0.7 * skill_match + 0.3 * text_similarity`.
5. **Serving Layer**:
   - REST API serving structured JSON (`/docs`, `/redoc`).
   - Streamlit Web Dashboard serving rich charts, gap analysis, and personalized learning centers.

No distributed processing (Spark, Hadoop, Kafka) is used in the application itself. These technologies are the *subject of the
learning content* the application teaches.

## Database schema

| Table | Purpose | Key constraints |
|---|---|---|
| `candidates` | profile / session owner | PK, unique `display_name` |
| `resumes` | original resume metadata, original text, reviewed text | PK, FK -> candidates |
| `job_postings` | job text, source, synthetic flag | PK, FK -> candidates (nullable) |
| `skills` | canonical skill catalogue with category | PK, unique `name` |
| `resume_skills` | resume <-> skill mapping | composite PK, FKs |
| `job_skills` | job <-> skill mapping with importance | composite PK, FKs, CHECK importance in (required, preferred) |
| `match_results` | every analysis with weights and full details (JSON) | PK, FKs, CHECK 0 <= score <= 100 |
| `learning_modules` | one row per lesson topic | PK, FK -> skills, unique (skill, topic_key) |
| `learning_paths` | status per candidate and skill | PK, unique (candidate, skill), CHECK status |
| `learning_progress` | completed topics per candidate | PK, unique (candidate, module) |
| `cv_versions` | updated CV content (JSON + text) per resume | PK, FKs, unique (resume, version_no) |

All timestamps are stored in UTC. Writes run in short transactions through `session_scope()`, which rolls back on error.
Ready-made DDL: `db/schema_postgres.sql` and `db/schema_sqlite.sql`.

## Important design decisions

* **Original CV is immutable.** Every change creates a `cv_versions` row. The baseline score is always the first analysis of the
  original text, so the old and new scores can be compared.
* **Nothing is learned automatically.** Opening or completing lessons never changes the CV. Adding a skill needs a checkbox
  confirmation, a preview, and a button press.
* **Duplicate protection.** The skill is refused if it is already present (canonical name or exact wording).
* **Offline by default.** Taxonomy, lessons and TF-IDF need no internet or API key. AI, MinIO and sentence-transformers are optional.
* **Graceful degradation.** PostgreSQL unreachable -> SQLite; no Tesseract -> clear install message; AI missing -> built-in content.
* **Transparent score.** The formula is shown with the real numbers on the Results page.
* **O*NET is reference context only.** Its occupation tasks and skill examples are not job advertisements and are never counted as requirements for the user's actual posting.

## Testing

* `tests/test_skills_matching.py` - extraction, aliases, required/preferred detection, scoring arithmetic, synthetic dataset recovery.
* `tests/test_extraction_cv.py` - TXT/DOCX/PDF/image/scanned-PDF extraction, validation errors, CV parsing and safe skill insertion, exports.
* `tests/test_learning_content.py` - every curated path is complete; Python snippets compile.
* `tests/test_lesson_examples.py` - SQL, pandas, statistics and ML examples from the lessons are executed and their stated outputs checked.
* `tests/test_workflow_e2e.py` - the full workflow, database persistence, PostgreSQL/SQLite fallback.
* `tests/test_app_ui.py` - the real Streamlit app driven by `streamlit.testing.AppTest`: pages render, learning -> confirm -> add-to-CV works by clicking, uploads work.
