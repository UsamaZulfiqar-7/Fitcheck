import os
import pathlib
import sys
import tempfile
import uuid

ROOT = pathlib.Path(__file__).resolve().parents[1]
UNIQ = uuid.uuid4().hex[:6]      # keeps profile names unique when a persistent PostgreSQL test DB is reused
TMP = tempfile.mkdtemp(prefix="fitcheck_test_")
os.environ["FITCHECK_DATA_DIR"] = TMP
os.environ["DATABASE_URL"] = os.environ.get("FITCHECK_TEST_DATABASE_URL", "")   # empty -> SQLite inside TMP
os.environ.pop("ANTHROPIC_API_KEY", None)
sys.path.insert(0, str(ROOT))
