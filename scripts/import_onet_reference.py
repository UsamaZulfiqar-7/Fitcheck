"""Import O*NET reference profiles from MinIO or a local archive into FitCheck's database."""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.onet import import_from_minio, import_onet_archive  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--archive",
        type=Path,
        help="Use a local O*NET ZIP instead of downloading it from the private MinIO bucket.",
    )
    args = parser.parse_args()

    if args.archive:
        archive = args.archive.read_bytes()
        imported = import_onet_archive(archive)
        fingerprint = hashlib.sha256(archive).hexdigest()
    else:
        from core.onet import download_reference_archive

        archive = download_reference_archive()
        imported = import_onet_archive(archive)
        fingerprint = hashlib.sha256(archive).hexdigest()

    print(f"Imported {imported} O*NET occupation profiles (version 31.0).")
    print(f"Archive SHA-256: {fingerprint}")
    print("O*NET data provides advisory occupation context; it does not change the match score.")


if __name__ == "__main__":
    main()
