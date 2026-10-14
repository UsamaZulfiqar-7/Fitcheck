"""Settings."""
import streamlit as st

import config
from core import ai, extraction, repository as repo, storage
from core.db import DB_INFO, get_engine
from core.matching import semantic_available
from ui import theme


def render() -> None:
    theme.hero("Settings", "Scoring weights, system status and optional features.")
    get_engine()
    st.subheader("Scoring")
    c1, c2 = st.columns(2)
    sw = c1.slider("Skill match weight (%)", 0, 100, int(round(st.session_state["skill_weight"] * 100)), 5, key="sw_slider")
    st.session_state["skill_weight"] = sw / 100
    pw = c2.slider("Weight of preferred (nice-to-have) skills", 0.0, 1.0, float(st.session_state["preferred_weight"]), 0.1,
                   key="pw_slider")
    st.session_state["preferred_weight"] = pw
    c1.caption(f"Final = {sw/100:.2f} x skill match + {1 - sw/100:.2f} x text similarity. Applies to the next analysis. "
               "Change the defaults permanently in .env (SKILL_WEIGHT, PREFERRED_WEIGHT).")
    sem_ok = semantic_available()
    st.session_state["use_semantic"] = st.checkbox("Also use semantic similarity (sentence-transformers)",
                                                   value=st.session_state["use_semantic"] and sem_ok, disabled=not sem_ok,
                                                   key="sem_box")
    if not sem_ok:
        st.caption("Optional: pip install sentence-transformers (downloads a model on first use). TF-IDF is used otherwise.")

    st.subheader("System status")
    rows = [
        ("Database", f"{DB_INFO.get('backend', '?')}  -  {DB_INFO.get('url', '')}"),
        ("OCR (Tesseract)", "available" if extraction.ocr_available() else "not found - needed only for scanned PDFs and images"),
        ("AI helper", "configured" if ai.available() else "not configured (optional)"),
        ("Object storage", "MinIO enabled" if storage.minio_enabled() else "local folder (default)"),
        ("Upload limit", f"{config.MAX_UPLOAD_MB} MB"),
        ("Synthetic sample jobs", "found" if config.SAMPLE_JOBS_CSV.exists() else "missing - run scripts/generate_synthetic_data.py"),
    ]
    for name, value in rows:
        st.markdown(f"**{name}:** {value}")
    if DB_INFO.get("fallback"):
        st.warning("PostgreSQL could not be reached, so FitCheck is using a local SQLite database instead. "
                   f"Reason: {DB_INFO.get('error')}")
    if not extraction.ocr_available():
        with st.expander("How to install OCR on Windows"):
            st.code(extraction.OCR_HELP, language=None)

    st.subheader("About")
    st.markdown("FitCheck estimates how well a CV covers a job posting and helps you close the gap. The score is an estimate, "
                "not an ATS score and not a hiring decision. Sample jobs are fictional (synthetic).")
