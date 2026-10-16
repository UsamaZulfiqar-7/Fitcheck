"""Import and query O*NET occupational reference data.

O*NET is used only to show advisory occupation context. It does not alter FitCheck's
CV/job match score or treat occupational survey data as a live job advertisement.
"""
from __future__ import annotations

import csv
import io
import zipfile
from collections import defaultdict
from functools import lru_cache
from typing import Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

import config
from core.db import OnetOccupation, session_scope

ONET_VERSION = "31.0"
ONET_ARCHIVE_OBJECT = "onet/31.0/db_31_0_text.zip"
_ARCHIVE_PREFIX = "db_31_0_text/"


def _read_tsv(archive: zipfile.ZipFile, filename: str, required: set[str]) -> list[dict[str, str]]:
    member = _ARCHIVE_PREFIX + filename
    try:
        raw = archive.read(member)
    except KeyError as exc:
        raise ValueError(f"O*NET archive is missing {filename}.") from exc
    rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig")), delimiter="\t"))
    if not rows or not required.issubset(rows[0]):
        raise ValueError(f"O*NET file {filename} has an unexpected or empty header.")
    return rows


def _rated_skills(
    rows: list[dict[str, str]], occupation_codes: set[str]
) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row["O*NET-SOC Code"] not in occupation_codes or row["Scale ID"] != "IM":
            continue
        if row.get("Recommend Suppress") == "Y" or row.get("Not Relevant") == "Y":
            continue
        try:
            importance = float(row["Data Value"])
        except (KeyError, ValueError):
            continue
        result[row["O*NET-SOC Code"]].append({
            "name": row["Element Name"],
            "importance": importance,
        })
    for skills in result.values():
        skills.sort(key=lambda skill: (-skill["importance"], skill["name"].casefold()))
    return result


def _software_skills(
    rows: list[dict[str, str]], occupation_codes: set[str]
) -> dict[str, list[dict[str, str | bool]]]:
    result: dict[str, list[dict[str, str | bool]]] = defaultdict(list)
    for row in rows:
        code = row["O*NET-SOC Code"]
        example = row.get("Workplace Example", "").strip()
        if code not in occupation_codes or not example:
            continue
        result[code].append({
            "name": example,
            "category": row.get("Element Name", "").strip(),
            "hot": row.get("Hot Technology") == "Y",
            "in_demand": row.get("In Demand") == "Y",
        })
    for skills in result.values():
        skills.sort(key=lambda skill: (
            not (skill["hot"] or skill["in_demand"]),
            str(skill["name"]).casefold(),
        ))
    return result


def parse_onet_archive(archive_bytes: bytes) -> list[dict[str, Any]]:
    """Parse relevant occupation, skill, technology, and task data from O*NET's text ZIP."""
    if not archive_bytes:
        raise ValueError("The O*NET archive is empty.")
    try:
        archive = zipfile.ZipFile(io.BytesIO(archive_bytes))
    except zipfile.BadZipFile as exc:
        raise ValueError("The O*NET archive is not a valid ZIP file.") from exc

    with archive:
        occupations = _read_tsv(
            archive, "Occupation Data.txt",
            {"O*NET-SOC Code", "Title", "Description"},
        )
        occupation_codes = {row["O*NET-SOC Code"] for row in occupations}
        essential = _rated_skills(
            _read_tsv(archive, "Essential Skills.txt", {
                "O*NET-SOC Code", "Element Name", "Scale ID", "Data Value",
                "Recommend Suppress", "Not Relevant",
            }),
            occupation_codes,
        )
        transferable = _rated_skills(
            _read_tsv(archive, "Transferable Skills.txt", {
                "O*NET-SOC Code", "Element Name", "Scale ID", "Data Value",
                "Recommend Suppress", "Not Relevant",
            }),
            occupation_codes,
        )
        software = _software_skills(
            _read_tsv(archive, "Software Skills.txt", {
                "O*NET-SOC Code", "Workplace Example", "Element Name",
                "Hot Technology", "In Demand",
            }),
            occupation_codes,
        )
        tasks: dict[str, list[str]] = defaultdict(list)
        for row in _read_tsv(archive, "Task Statements.txt", {
            "O*NET-SOC Code", "Task", "Task Type",
        }):
            task = row.get("Task", "").strip()
            if row["O*NET-SOC Code"] in occupation_codes and task:
                tasks[row["O*NET-SOC Code"]].append(task)

    records = []
    for occupation in occupations:
        code = occupation["O*NET-SOC Code"]
        records.append({
            "onet_code": code,
            "title": occupation["Title"].strip(),
            "description": occupation["Description"].strip(),
            "task_statements": tasks.get(code, []),
            "essential_skills": essential.get(code, []),
            "transferable_skills": transferable.get(code, []),
            "software_skills": software.get(code, []),
            "source_version": ONET_VERSION,
        })
    if not records:
        raise ValueError("No O*NET occupation profiles were found in the archive.")
    return records


def import_onet_archive(archive_bytes: bytes) -> int:
    """Validate, then transactionally replace the imported O*NET reference profiles."""
    records = parse_onet_archive(archive_bytes)
    with session_scope() as session:
        session.query(OnetOccupation).delete()
        session.add_all(OnetOccupation(**record) for record in records)
    _cached_occupation_index.cache_clear()
    return len(records)


def download_reference_archive() -> bytes:
    """Fetch the versioned O*NET archive from the configured private MinIO bucket."""
    if not config.MINIO_ENDPOINT or not config.MINIO_ACCESS_KEY or not config.MINIO_SECRET_KEY:
        raise RuntimeError(
            "MinIO is not configured. Set MINIO_ENDPOINT, MINIO_ACCESS_KEY, and "
            "MINIO_SECRET_KEY in the local .env file."
        )
    from minio import Minio

    client = Minio(
        config.MINIO_ENDPOINT,
        access_key=config.MINIO_ACCESS_KEY,
        secret_key=config.MINIO_SECRET_KEY,
        secure=config.MINIO_SECURE,
    )
    response = client.get_object(config.MINIO_REFERENCE_BUCKET, ONET_ARCHIVE_OBJECT)
    try:
        archive = response.read()
    finally:
        response.close()
        response.release_conn()
    if not archive:
        raise RuntimeError(f"O*NET reference object {ONET_ARCHIVE_OBJECT} is empty.")
    return archive


def import_from_minio() -> int:
    """Download O*NET from MinIO and import it into the configured app database."""
    return import_onet_archive(download_reference_archive())


def _occupation_index() -> tuple[list[dict[str, Any]], TfidfVectorizer, Any]:
    with session_scope() as session:
        profiles = [
            {
                "onet_code": row.onet_code,
                "title": row.title,
                "description": row.description,
                "tasks": row.task_statements,
                "essential_skills": row.essential_skills,
                "transferable_skills": row.transferable_skills,
                "software_skills": row.software_skills,
                "source_version": row.source_version,
            }
            for row in session.query(OnetOccupation).order_by(OnetOccupation.onet_code).all()
        ]
    if not profiles:
        return [], TfidfVectorizer(), None

    documents = [
        " ".join([p["title"], p["description"], *p["tasks"]])
        for p in profiles
    ]
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True)
    return profiles, vectorizer, vectorizer.fit_transform(documents)


@lru_cache(maxsize=1)
def _cached_occupation_index() -> tuple[list[dict[str, Any]], TfidfVectorizer, Any]:
    return _occupation_index()


def recommend_occupations(job_text: str, limit: int = 3) -> list[dict[str, Any]]:
    """Return advisory O*NET occupation profiles closest to a user-supplied job description."""
    if not job_text.strip() or limit <= 0:
        return []
    profiles, vectorizer, matrix = _cached_occupation_index()
    if not profiles or matrix is None:
        return []
    query = vectorizer.transform([job_text])
    similarities = cosine_similarity(query, matrix).ravel()
    best = similarities.argsort()[::-1][:min(limit, len(profiles))]
    return [
        {
            "onet_code": profiles[index]["onet_code"],
            "title": profiles[index]["title"],
            "description": profiles[index]["description"],
            "similarity": round(float(similarities[index]) * 100, 1),
            "essential_skills": profiles[index]["essential_skills"][:6],
            "transferable_skills": profiles[index]["transferable_skills"][:5],
            "software_skills": profiles[index]["software_skills"][:8],
            "source_version": profiles[index]["source_version"],
        }
        for index in best
    ]
