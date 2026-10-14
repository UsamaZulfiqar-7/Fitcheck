"""Transparent resume <-> job match score.

    skill_match   = weighted matched job skills / weighted total job skills * 100
                    (required skill weight = 1.0, preferred skill weight = PREFERRED_WEIGHT)
    text_similarity = TF-IDF cosine similarity * 100   (optionally averaged with a semantic model)
    final_score   = SKILL_WEIGHT * skill_match + (1 - SKILL_WEIGHT) * text_similarity

The score is an ESTIMATE of how well the CV text covers the job text.  It is not an ATS score
and not a hiring decision.
"""
from __future__ import annotations

import csv
from dataclasses import asdict, dataclass, field
from functools import lru_cache

import config
from core.skills import skill_category

DISCLAIMER = ("This score is an estimate based on skill keywords and text similarity. It is not a guaranteed "
              "ATS score and not a hiring decision.")


@dataclass
class MatchResult:
    final_score: float
    skill_score: float
    text_similarity: float
    skill_weight: float
    text_weight: float
    preferred_weight: float
    matched: list[str] = field(default_factory=list)
    missing_required: list[str] = field(default_factory=list)
    missing_preferred: list[str] = field(default_factory=list)
    additional: list[str] = field(default_factory=list)
    job_skills: dict = field(default_factory=dict)          # skill -> importance
    resume_skills: list[str] = field(default_factory=list)
    matched_weight: float = 0.0
    total_weight: float = 0.0
    tfidf_similarity: float = 0.0
    semantic_similarity: float | None = None
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def band(self) -> str:
        return score_band(self.final_score)


def score_band(score: float) -> str:
    if score >= 80:
        return "Strong match"
    if score >= 60:
        return "Moderate match"
    if score >= 40:
        return "Partial match"
    return "Low match"


@lru_cache(maxsize=1)
def _corpus() -> tuple[str, ...]:
    """Synthetic job descriptions give the TF-IDF model a realistic vocabulary (idf weights)."""
    try:
        with open(config.SAMPLE_JOBS_CSV, newline="", encoding="utf-8") as fh:
            return tuple(row["description"] for row in csv.DictReader(fh) if row.get("description"))
    except OSError:
        return tuple()


def tfidf_similarity(resume_text: str, job_text: str) -> float:
    if not resume_text.strip() or not job_text.strip():
        return 0.0
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    docs = list(_corpus()) + [resume_text, job_text]
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True)
    matrix = vectorizer.fit_transform(docs)
    return float(cosine_similarity(matrix[-2], matrix[-1])[0][0])


@lru_cache(maxsize=1)
def semantic_available() -> bool:
    try:
        import sentence_transformers  # noqa: F401
        return True
    except Exception:
        return False


@lru_cache(maxsize=1)
def _semantic_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer("all-MiniLM-L6-v2")


def semantic_similarity(resume_text: str, job_text: str) -> float | None:
    if not semantic_available():
        return None
    try:
        from sentence_transformers import util
        emb = _semantic_model().encode([resume_text[:6000], job_text[:6000]], convert_to_tensor=True)
        return max(0.0, float(util.cos_sim(emb[0], emb[1])))
    except Exception:
        return None


def compute_match(resume_text: str, job_text: str, resume_skills: list[str], job_skills: dict[str, str], *,
                  skill_weight: float | None = None, preferred_weight: float | None = None,
                  use_semantic: bool | None = None) -> MatchResult:
    sw = config.SKILL_WEIGHT if skill_weight is None else min(max(skill_weight, 0.0), 1.0)
    pw = config.PREFERRED_WEIGHT if preferred_weight is None else min(max(preferred_weight, 0.0), 1.0)
    semantic_on = config.USE_SEMANTIC if use_semantic is None else use_semantic
    notes: list[str] = []

    resume_set = {s.lower(): s for s in resume_skills}
    matched, missing_req, missing_pref = [], [], []
    matched_w = total_w = 0.0
    for skill, importance in job_skills.items():
        weight = 1.0 if importance == "required" else pw
        total_w += weight
        if skill.lower() in resume_set:
            matched.append(skill)
            matched_w += weight
        elif importance == "required":
            missing_req.append(skill)
        else:
            missing_pref.append(skill)
    additional = [s for s in resume_skills if s.lower() not in {k.lower() for k in job_skills}]

    skill_score = round(matched_w / total_w * 100, 1) if total_w > 0 else 0.0
    if not job_skills:
        notes.append("No known skills were detected in the job description, so the skill score is 0. "
                     "Check the job text or add more detail.")

    tfidf = tfidf_similarity(resume_text, job_text)
    semantic = semantic_similarity(resume_text, job_text) if semantic_on else None
    if semantic_on and semantic is None:
        notes.append("Semantic matching was requested but sentence-transformers is not installed; TF-IDF only.")
    similarity = tfidf if semantic is None else (tfidf + semantic) / 2
    text_score = round(similarity * 100, 1)

    final = round(sw * skill_score + (1 - sw) * text_score, 1)
    return MatchResult(final_score=final, skill_score=skill_score, text_similarity=text_score, skill_weight=sw,
                       text_weight=round(1 - sw, 4), preferred_weight=pw, matched=matched,
                       missing_required=missing_req, missing_preferred=missing_pref, additional=additional,
                       job_skills=dict(job_skills), resume_skills=list(resume_skills), matched_weight=matched_w,
                       total_weight=total_w, tfidf_similarity=round(tfidf * 100, 1),
                       semantic_similarity=None if semantic is None else round(semantic * 100, 1), notes=notes)


def formula_text(r) -> str:
    """Human readable substitution of the formula with real numbers (r: MatchResult or dict-like)."""
    g = (lambda k: r[k]) if isinstance(r, dict) else (lambda k: getattr(r, k))
    return (f"Final = {g('skill_weight'):.2f} x Skill match ({g('skill_score')}) + "
            f"{g('text_weight'):.2f} x Text similarity ({g('text_similarity')}) = {g('final_score')}")


def explain_score_change(old: dict, new: dict, skill: str | None = None) -> list[str]:
    """Explain why the score changed between two stored match `details`/score dicts."""
    lines = []
    d_final = round(new["final_score"] - old["final_score"], 1)
    d_skill = round(new["skill_score"] - old["skill_score"], 1)
    d_text = round(new["text_similarity"] - old["text_similarity"], 1)
    lines.append(f"Final score changed by {d_final:+.1f} points ({old['final_score']} -> {new['final_score']}).")
    if skill:
        importance = new.get("job_skills", {}).get(skill)
        if importance:
            weight = 1.0 if importance == "required" else new["preferred_weight"]
            lines.append(f"'{skill}' is a {importance} skill in this job (weight {weight:g}), so counting it as matched "
                         f"moved the skill match from {old['skill_score']} to {new['skill_score']} ({d_skill:+.1f}).")
        else:
            lines.append(f"'{skill}' is not listed in this job posting, so it does not change the skill match "
                         f"({d_skill:+.1f}); it appears under additional skills.")
    elif d_skill:
        lines.append(f"Skill match changed by {d_skill:+.1f}.")
    lines.append(f"Text similarity changed by {d_text:+.1f} because the CV wording changed slightly "
                 f"(TF-IDF compares all words, not only skills).")
    return lines


def category_counts(job_skills: dict, matched: list[str]) -> dict[str, dict[str, int]]:
    """{category: {'required': n, 'matched': m}} for the 'required vs matched' chart."""
    out: dict[str, dict[str, int]] = {}
    matched_l = {m.lower() for m in matched}
    for skill in job_skills:
        cat = skill_category(skill)
        row = out.setdefault(cat, {"job": 0, "matched": 0})
        row["job"] += 1
        if skill.lower() in matched_l:
            row["matched"] += 1
    return out
