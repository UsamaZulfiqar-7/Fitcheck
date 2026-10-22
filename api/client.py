"""FitCheck API Client.

Allows calling the FitCheck REST API over HTTP or in-process via FastAPI TestClient.
Used by Streamlit UI, scripts, and tests.
"""
from __future__ import annotations

import io
from typing import Any, Dict, List, Optional
import requests

from api.main import app


class FitCheckClient:
    """Client for FitCheck REST API with automatic HTTP / In-Process fallback."""

    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url.rstrip("/")
        self._test_client = None

    def _is_server_alive(self) -> bool:
        try:
            r = requests.get(f"{self.base_url}/api/v1/health", timeout=0.8)
            return r.status_code == 200
        except Exception:
            return False

    @property
    def test_client(self):
        if self._test_client is None:
            from fastapi.testclient import TestClient
            self._test_client = TestClient(app)
        return self._test_client

    def ingest_job_text(self, text: str, title: str = "Untitled Job",
                         company: Optional[str] = None, candidate_name: str = "API User") -> Dict[str, Any]:
        """Post job as text (Text -> API -> Storage -> Processing -> Analyzing -> Serving)."""
        payload = {
            "title": title,
            "company": company,
            "text": text,
            "candidate_name": candidate_name,
        }
        if self._is_server_alive():
            r = requests.post(f"{self.base_url}/api/v1/jobs/text", json=payload, timeout=30)
            r.raise_for_status()
            return r.json()
        resp = self.test_client.post("/api/v1/jobs/text", json=payload)
        if resp.status_code >= 400:
            raise RuntimeError(f"API Error {resp.status_code}: {resp.text}")
        return resp.json()

    def ingest_job_pdf(self, pdf_bytes: bytes, filename: str = "job.pdf",
                        title: Optional[str] = None, candidate_name: str = "API User") -> Dict[str, Any]:
        """Upload job as PDF (PDF -> API -> Storage -> Processing -> Analyzing -> Serving)."""
        files = {"file": (filename, pdf_bytes, "application/pdf")}
        data = {"title": title or "", "candidate_name": candidate_name}
        if self._is_server_alive():
            r = requests.post(f"{self.base_url}/api/v1/jobs/pdf", files=files, data=data, timeout=30)
            r.raise_for_status()
            return r.json()
        resp = self.test_client.post("/api/v1/jobs/pdf", files=files, data=data)
        if resp.status_code >= 400:
            raise RuntimeError(f"API Error {resp.status_code}: {resp.text}")
        return resp.json()

    def ingest_job_image(self, image_bytes: bytes, filename: str = "job.png",
                          title: Optional[str] = None, candidate_name: str = "API User") -> Dict[str, Any]:
        """Upload job as Image (Image -> API -> Storage -> Processing -> Analyzing -> Serving)."""
        files = {"file": (filename, image_bytes, "image/png")}
        data = {"title": title or "", "candidate_name": candidate_name}
        if self._is_server_alive():
            r = requests.post(f"{self.base_url}/api/v1/jobs/image", files=files, data=data, timeout=30)
            r.raise_for_status()
            return r.json()
        resp = self.test_client.post("/api/v1/jobs/image", files=files, data=data)
        if resp.status_code >= 400:
            raise RuntimeError(f"API Error {resp.status_code}: {resp.text}")
        return resp.json()

    def ingest_resume(self, file_bytes: bytes, filename: str = "resume.pdf",
                       candidate_name: str = "API User") -> Dict[str, Any]:
        """Upload resume (PDF/DOCX -> Storage -> Processing -> Analyzing -> Serving)."""
        content_type = "application/pdf" if filename.endswith(".pdf") else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        files = {"file": (filename, file_bytes, content_type)}
        data = {"candidate_name": candidate_name}
        if self._is_server_alive():
            r = requests.post(f"{self.base_url}/api/v1/resumes/upload", files=files, data=data, timeout=30)
            r.raise_for_status()
            return r.json()
        resp = self.test_client.post("/api/v1/resumes/upload", files=files, data=data)
        if resp.status_code >= 400:
            raise RuntimeError(f"API Error {resp.status_code}: {resp.text}")
        return resp.json()

    def match_analysis(self, resume_id: int, job_id: int,
                       skill_weight: float = 0.70, preferred_weight: float = 0.50) -> Dict[str, Any]:
        """Analyze match between stored resume and job (Analyzing -> Serving)."""
        payload = {
            "resume_id": resume_id,
            "job_id": job_id,
            "skill_weight": skill_weight,
            "preferred_weight": preferred_weight,
        }
        if self._is_server_alive():
            r = requests.post(f"{self.base_url}/api/v1/analysis/match", json=payload, timeout=30)
            r.raise_for_status()
            return r.json()
        resp = self.test_client.post("/api/v1/analysis/match", json=payload)
        if resp.status_code >= 400:
            raise RuntimeError(f"API Error {resp.status_code}: {resp.text}")
        return resp.json()

    def health(self) -> Dict[str, Any]:
        """Check system status."""
        if self._is_server_alive():
            return requests.get(f"{self.base_url}/api/v1/health", timeout=5).json()
        return self.test_client.get("/api/v1/health").json()
