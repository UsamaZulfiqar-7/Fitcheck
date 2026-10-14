# FitCheck - Resume & Job Skill Gap Analyzer

FitCheck compares your CV with a job posting, shows which skills you already have and which are missing, **teaches you the
missing skills inside the app**, and lets you add a skill to your CV (after you confirm that you really learned it) with a
recalculated match score and a downloadable updated CV.

Built with Python + Streamlit. Runs fully offline: **no AI key and no cloud service are required.**

![architecture](docs/architecture.png)

## Features

| Area | What you get |
|---|---|
| Upload | CV: PDF, DOCX, TXT. Job: typed text, PDF, JPG/JPEG/PNG (OCR), TXT, or a synthetic sample job |
| Review | Extracted text is shown and editable before analysis (the original extraction is kept unchanged in the database) |
| Score | Final score /100 = 70% skill match + 30% text similarity (TF-IDF cosine). Weights are configurable. Labelled as an **estimate** |
| Gap analysis | Matched, missing required, missing preferred, additional skills + charts + "why this skill matters" taken from the job text |
| Learning Center | Per missing skill: overview, 5-stage roadmap, written lessons with examples/outputs, practice questions with hints and revealable solutions, free resources, progress saved in the database |
| Add to CV | "I've Learned This Skill — Add to My CV": explicit confirmation, section choice, editable wording, before/after preview, duplicate check, new CV version, old vs new score with explanation |
| Downloads | Updated CV (DOCX / PDF), match report (PDF), original uploaded file |
| Database | PostgreSQL (primary) with automatic SQLite fallback |

Pages: Home Dashboard, Resume & Job Analysis, Match Results, Skill Gap Analysis, Personalized Learning Center,
My Learning Progress, Updated CV & Downloads, Settings.

## 1. Quick start (Windows 10/11, PowerShell, VS Code)

1. Install **Python 3.10 or newer** from https://www.python.org/downloads/ (tick *Add python.exe to PATH*).
2. Open the project folder in VS Code and open a terminal (PowerShell):

```powershell
cd path\to\fitcheck
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell says *running scripts is disabled*, run this once and activate again:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

3. Install the packages and start the app:

```powershell
pip install -r requirements.txt
streamlit run app.py
```

The browser opens at http://localhost:8501. Without any configuration FitCheck uses a local SQLite file
(`data/fitcheck.db`), so you can start immediately.

> In VS Code choose the interpreter: `Ctrl+Shift+P` -> *Python: Select Interpreter* -> `.venv`.

## 2. OCR for scanned PDFs and images (optional but recommended)

Embedded PDF text, DOCX and TXT files need nothing extra. **Photos/screenshots of job postings and scanned PDFs need OCR.**

1. Download the Windows installer of **Tesseract OCR** from https://github.com/UB-Mannheim/tesseract/wiki and install it
   (default folder: `C:\Program Files\Tesseract-OCR`).
2. Either add that folder to your `PATH`, or create `.env` (copy `.env.example`) and set:

```
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
```

3. Restart the app. **Settings -> System status** shows whether OCR is found.

FitCheck also auto-detects the default Windows install path.

## 3. Database

### SQLite (default, zero setup)
Leave `DATABASE_URL` empty. The file `data/fitcheck.db` is created automatically.

### PostgreSQL (primary database)
1. Install PostgreSQL (https://www.postgresql.org/download/windows/) and remember the password of the `postgres` user.
2. Create a database and user (SQL Shell / psql):

```sql
CREATE USER fitcheck WITH PASSWORD 'choose_a_password';
CREATE DATABASE fitcheck OWNER fitcheck;
```

3. Copy `.env.example` to `.env` and set:

```
DATABASE_URL=postgresql+psycopg2://fitcheck:choose_a_password@localhost:5432/fitcheck
```

4. Create the tables (also happens automatically on first start):

```powershell
python scripts\init_db.py
```

It prints which database is used. If PostgreSQL cannot be reached, FitCheck falls back to SQLite and Settings shows the reason.
The SQL schema files are in `db/schema_postgres.sql` and `db/schema_sqlite.sql` (generated from `core/db.py`, run
`python scripts\export_schema.py` to refresh them).

Tables: `candidates`, `resumes`, `job_postings`, `skills`, `resume_skills`, `job_skills`, `match_results`,
`learning_modules`, `learning_paths`, `learning_progress`, `cv_versions` (primary/foreign keys, check constraints, timestamps).

## 4. How to use it

1. **Resume & Job Analysis**: type a profile name in the sidebar (your progress is saved under it), upload your CV, add the job
   (paste text, upload PDF/image/TXT, or load a synthetic sample job), review/correct the text, click **Run analysis**.
2. **Match Results** and **Skill Gap Analysis**: see the score, the formula with real numbers, and the missing skills.
3. **Personalized Learning Center**: pick a missing skill -> *Start learning* -> read lessons, tick topics as completed, try the
   practice questions (hint -> your answer -> reveal solution), open free resources.
4. When all topics are done click **Mark learning path as completed**. Then **I've Learned This Skill — Add to My CV**:
   confirm honestly, choose the CV section, edit the wording, check the preview, and save.
5. **Updated CV & Downloads**: compare original vs updated, edit the text, download DOCX/PDF and the match report.

After restarting the app, enter the same profile name and your latest analysis and learning progress are restored.

## 5. Scoring

```
skill match      = weighted matched job skills / weighted total job skills x 100
                   (required skill = 1.0, preferred skill = PREFERRED_WEIGHT, default 0.5)
text similarity  = TF-IDF cosine similarity(CV text, job text) x 100
                   (optionally averaged with a sentence-transformers similarity)
final score      = SKILL_WEIGHT x skill match + (1 - SKILL_WEIGHT) x text similarity     (default 0.7 / 0.3)
```

Skills are found with a rule-based taxonomy (about 100 skills with aliases, e.g. "ReactJS" = React). A skill is *preferred* when it is
under a heading such as "Nice to have" or on a line such as "... is a plus"; otherwise it is *required*. The TF-IDF model uses the
fictional sample jobs as background vocabulary. **The score is an estimate, not an ATS score and not a hiring decision.**

## 6. Learning content

* **Full written lessons** (5 stages each, examples with expected outputs, 4-6 practice questions with hints and solutions, resources):
  SQL, Python, Excel, Power BI, Pandas, Statistics, Machine Learning, Hadoop, Spark, Kafka, Git, Docker.
  The SQL, pandas, statistics and Python examples are executed in `tests/test_lesson_examples.py` to check the stated outputs.
* **Other skills** (e.g. Tableau, Airflow, React) get a category-specific **starter path** and are clearly labelled as such.
* **Optional AI notes**: set `ANTHROPIC_API_KEY` in `.env` and `pip install anthropic` to generate extra personalised notes. Everything else works without it.
* **Free resources** point to official documentation or well-known free sites. They were *not* checked automatically when this package was
  built (no internet in the build environment), so run `python scripts\check_links.py` once and fix any link that changed.

Practice questions are for learning only: there is no quiz score, certificate or automatic skill verification.

## 7. Synthetic data

You do not need a resume dataset: you upload your own CV. For development/demo FitCheck ships **fictional** sample jobs:

```powershell
python scripts\generate_synthetic_data.py      # regenerates data/synthetic_jobs.csv and data/skill_mappings.csv (seed 42)
```

All companies and postings are invented and labelled *(synthetic)*; do not present them as real market data.

## 8. Tests

```powershell
pip install -r requirements-dev.txt
pytest
```

63 tests cover skill extraction, scoring, file extraction (including OCR), CV editing/export, lesson content, the complete workflow
(upload -> analyse -> learn -> confirm -> add skill -> new score -> downloads) and the Streamlit pages (`streamlit.testing`).
To run them against PostgreSQL: `$env:FITCHECK_TEST_DATABASE_URL="postgresql+psycopg2://user:pass@localhost:5432/testdb"; pytest`.

## 9. Project structure

```
app.py                  Streamlit entry point (sidebar navigation)
config.py               settings from .env
core/                   extraction.py, skills.py, taxonomy.py, matching.py, learning_content.py, cv_builder.py,
                        pipeline.py, repository.py, db.py, storage.py, report.py, ai.py, content/*.py (lessons)
ui/                     theme.py, charts.py, state.py, pages/*.py
scripts/                generate_synthetic_data.py, init_db.py, export_schema.py, check_links.py, make_architecture_diagram.py
data/                   synthetic_jobs.csv, skill_mappings.csv, README_DATA.md (uploads/ and fitcheck.db are created at run time)
db/                     schema_postgres.sql, schema_sqlite.sql
docs/                   ARCHITECTURE.md, PROJECT_EXPLANATION.md, architecture.png
tests/                  pytest suite
```

## 10. Troubleshooting

| Problem | Fix |
|---|---|
| `streamlit` is not recognised | Activate the venv (`.\.venv\Scripts\Activate.ps1`) or run `python -m streamlit run app.py` |
| PowerShell blocks `Activate.ps1` | `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned` |
| "Tesseract was not found" | See section 2; set `TESSERACT_CMD` in `.env` and restart |
| Image text is wrong / empty | Use a sharper, larger image (at least ~1200 px wide) or correct the text in the editor |
| PDF text is empty | The PDF is probably scanned -> OCR is needed. Password-protected PDFs cannot be read |
| Settings says SQLite fallback | PostgreSQL is not running, or the `DATABASE_URL` user/password/database is wrong; read the reason shown |
| `psycopg2` install error | `pip install psycopg2-binary`, or leave `DATABASE_URL` empty to use SQLite |
| Port 8501 already in use | `streamlit run app.py --server.port 8502` |
| Score looks low | Text similarity is strict (it compares all words). Look at the skill match and the missing skills first |
| A skill is not detected | The taxonomy has about 100 skills; add yours to `core/taxonomy.py` (name, category, aliases) |
| Reset everything | Stop the app and delete `data/fitcheck.db` (SQLite) |

## 11. Limitations (please read)

* The score is a keyword/text-similarity estimate; it does not understand years of experience or seniority.
* Skill detection is rule-based and limited to the taxonomy.
* If the original CV is a PDF, the updated CV is **rebuilt from extracted text** with a clean layout; the original PDF design is not preserved.
* Scanned documents depend on OCR quality; always review the extracted text.
* The pipeline runs on a single machine; no distributed processing is implemented.
* Tests were run on Linux (SQLite and PostgreSQL 16). The Windows steps above follow the standard installers but were not executed on Windows in the build environment.
