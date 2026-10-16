"""Upload the downloaded official O*NET reference archive to a private MinIO bucket."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import config  # noqa: E402

DEFAULT_ARCHIVE = ROOT / "data" / "reference" / "onet" / "31.0" / "db_31_0_text.zip"
DATASET = {
    "name": "O*NET Database",
    "version": "31.0",
    "kind": "occupational reference data",
    "source_url": "https://www.onetcenter.org/dl_files/database/db_31_0_text.zip",
    "license_url": "https://www.onetcenter.org/license_db.html",
    "license": "CC BY 4.0, subject to the official license exceptions",
    "attribution": (
        "This page includes information from the O*NET 31.0 Database by the U.S. "
        "Department of Labor, Employment and Training Administration (USDOL/ETA). "
        "Used under the CC BY 4.0 license. O*NET is a trademark of USDOL/ETA."
    ),
    "contents": [
        "occupation titles and descriptions",
        "essential and transferable skills",
        "software skills",
        "task statements",
    ],
    "limitations": (
        "This is not a dataset of current job advertisements, resumes, or labelled "
        "resume-to-job matches. Uploading it does not train or update a FitCheck model."
    ),
}


def upload_archive(archive: Path) -> tuple[str, str]:
    """Upload the archive and its provenance sidecar; return their object names."""
    if not archive.is_file():
        raise FileNotFoundError(
            f"O*NET archive not found at {archive}. Download it from "
            f"{DATASET['source_url']} first."
        )
    if not config.MINIO_ENDPOINT or not config.MINIO_ACCESS_KEY or not config.MINIO_SECRET_KEY:
        raise RuntimeError(
            "MinIO is not configured. Set MINIO_ENDPOINT, MINIO_ACCESS_KEY, "
            "MINIO_SECRET_KEY, and MINIO_REFERENCE_BUCKET in your local .env file."
        )

    try:
        from minio import Minio
    except ImportError as exc:
        raise RuntimeError(
            "MinIO Python client is missing. Install the optional dependencies "
            "with `pip install -r requirements-optional.txt`."
        ) from exc

    client = Minio(
        config.MINIO_ENDPOINT,
        access_key=config.MINIO_ACCESS_KEY,
        secret_key=config.MINIO_SECRET_KEY,
        secure=config.MINIO_SECURE,
    )
    bucket = config.MINIO_REFERENCE_BUCKET
    for bucket_name in {config.MINIO_BUCKET, bucket}:
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)

    version_prefix = "onet/31.0"
    archive_object = f"{version_prefix}/db_31_0_text.zip"
    metadata_object = f"{version_prefix}/metadata.json"
    with archive.open("rb") as data:
        client.put_object(
            bucket,
            archive_object,
            data,
            archive.stat().st_size,
            content_type="application/zip",
        )
    from io import BytesIO

    metadata = json.dumps(DATASET, indent=2).encode("utf-8")
    client.put_object(
        bucket,
        metadata_object,
        BytesIO(metadata),
        len(metadata),
        content_type="application/json",
    )
    return archive_object, metadata_object


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    args = parser.parse_args()

    archive_object, metadata_object = upload_archive(args.archive)
    print(f"Uploaded O*NET 31.0 archive to bucket {config.MINIO_REFERENCE_BUCKET!r}: {archive_object}")
    print(f"Uploaded provenance metadata: {metadata_object}")


if __name__ == "__main__":
    main()
