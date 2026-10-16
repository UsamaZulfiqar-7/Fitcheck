"""Central configuration.

Every value can be overridden through environment variables or a `.env` file
(copy `.env.example` to `.env`).  Nothing here requires cloud services or an AI key.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def _float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except ValueError:
        return default


# ---- folders -------------------------------------------------------------
SAMPLE_DATA_DIR = BASE_DIR / "data"                       # shipped synthetic CSVs
DATA_DIR = Path(os.getenv("FITCHECK_DATA_DIR", SAMPLE_DATA_DIR))
UPLOAD_DIR = DATA_DIR / "uploads"                          # raw file storage (local)
for _d in (DATA_DIR, UPLOAD_DIR):
    _d.mkdir(parents=True, exist_ok=True)

SAMPLE_JOBS_CSV = SAMPLE_DATA_DIR / "synthetic_jobs.csv"
SKILL_MAPPINGS_CSV = SAMPLE_DATA_DIR / "skill_mappings.csv"

# ---- database ------------------------------------------------------------
# PostgreSQL example: postgresql+psycopg2://user:password@localhost:5432/fitcheck
# If empty (or PostgreSQL is unreachable) FitCheck falls back to a local SQLite file.
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
SQLITE_URL = f"sqlite:///{(DATA_DIR / 'fitcheck.db').as_posix()}"
if not DATABASE_URL:
    DATABASE_URL = SQLITE_URL

# ---- uploads / OCR ---------------------------------------------------------
MAX_UPLOAD_MB = int(_float("MAX_UPLOAD_MB", 10))
TESSERACT_CMD = os.getenv("TESSERACT_CMD", "").strip()
OCR_MAX_PAGES = int(_float("OCR_MAX_PAGES", 5))

# ---- scoring defaults (can be changed at runtime in Settings) -------------------
SKILL_WEIGHT = min(max(_float("SKILL_WEIGHT", 0.70), 0.0), 1.0)
PREFERRED_WEIGHT = min(max(_float("PREFERRED_WEIGHT", 0.50), 0.0), 1.0)
USE_SEMANTIC = _bool("USE_SEMANTIC", False)

# ---- optional AI -------------------------------------------------------------
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
AI_MODEL = os.getenv("AI_MODEL", "claude-sonnet-4-6")

# ---- optional S3 compatible storage (MinIO) -----------------------------------
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "").strip()      # e.g. localhost:9000
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "").strip()
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "").strip()
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "fitcheck")
MINIO_REFERENCE_BUCKET = os.getenv("MINIO_REFERENCE_BUCKET", "fitcheck-reference-data")
MINIO_SECURE = _bool("MINIO_SECURE", False)

APP_NAME = "FitCheck"
