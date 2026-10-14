"""Raw file storage.  Local disk by default; MinIO / S3-compatible storage is optional."""
from __future__ import annotations

import datetime as dt
import logging
import re
from pathlib import Path

import config

log = logging.getLogger("fitcheck.storage")


def _safe_name(filename: str) -> str:
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", Path(filename or "file").name).strip("._") or "file"
    return stem[:100]


def minio_enabled() -> bool:
    return bool(config.MINIO_ENDPOINT and config.MINIO_ACCESS_KEY and config.MINIO_SECRET_KEY)


def save_raw(data: bytes, filename: str, kind: str) -> str:
    """Store the original uploaded bytes; returns the local path. Mirrors to MinIO when configured."""
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    path = config.UPLOAD_DIR / f"{kind}_{stamp}_{_safe_name(filename)}"
    path.write_bytes(data)
    if minio_enabled():
        try:
            from io import BytesIO

            from minio import Minio

            client = Minio(config.MINIO_ENDPOINT, access_key=config.MINIO_ACCESS_KEY,
                           secret_key=config.MINIO_SECRET_KEY, secure=config.MINIO_SECURE)
            if not client.bucket_exists(config.MINIO_BUCKET):
                client.make_bucket(config.MINIO_BUCKET)
            client.put_object(config.MINIO_BUCKET, path.name, BytesIO(data), len(data))
        except Exception as exc:                      # optional feature must never break the app
            log.warning("MinIO upload skipped: %s", exc)
    return str(path)


def read_raw(path: str | None) -> bytes | None:
    if not path:
        return None
    try:
        return Path(path).read_bytes()
    except OSError:
        return None
