"""Create all FitCheck tables in the configured database (PostgreSQL if reachable, otherwise SQLite).

    python scripts/init_db.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import inspect  # noqa: E402

from core.db import DB_INFO, get_engine  # noqa: E402


def main() -> None:
    engine = get_engine()                       # also creates the tables
    tables = sorted(inspect(engine).get_table_names())
    print(f"Database : {DB_INFO['backend']}  ({DB_INFO['url']})")
    if DB_INFO.get("fallback"):
        print(f"WARNING  : the configured database could not be reached, SQLite is used instead.\n           Reason: {DB_INFO['error']}")
    print(f"Tables   : {', '.join(tables)}")


if __name__ == "__main__":
    main()
