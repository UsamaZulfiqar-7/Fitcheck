"""Draw docs/architecture.png (data pipeline + components).   python scripts/make_architecture_diagram.py"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "docs" / "architecture.png"
INDIGO, SOFT, TEAL, GRAY = "#4F46E5", "#E0E7FF", "#0F766E", "#475569"


def box(ax, x, y, w, h, text, fc=SOFT, ec=INDIGO, size=9, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.12", fc=fc, ec=ec, lw=1.4))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=size, color="#0F172A",
            fontweight="bold" if bold else "normal", wrap=True)


def arrow(ax, x1, y1, x2, y2, color=INDIGO):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=14, lw=1.5, color=color))


def main() -> None:
    fig, ax = plt.subplots(figsize=(14, 8.2))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 8.2)
    ax.axis("off")
    ax.text(7, 7.85, "FitCheck - architecture and data pipeline", ha="center", fontsize=16, fontweight="bold", color="#1E1B4B")

    # UI layer
    box(ax, 0.4, 6.55, 13.2, 0.85, "Streamlit UI (app.py + ui/pages)\nHome - Resume & Job Analysis - Match Results - Skill Gap Analysis - "
        "Learning Center - Learning Progress - Updated CV & Downloads - Settings", fc="#EEF2FF", bold=True, size=9)

    steps = ["1. Ingestion\nCV + job posting\n(PDF/DOCX/TXT/\nimage/typed)", "2. Raw file\nstorage\n(data/uploads,\noptional MinIO)",
             "3. Text\nextraction\n(pdfplumber,\npython-docx, OCR)", "4. Skill extraction\n& normalisation\n(taxonomy rules)",
             "5. Match score\n(skills 70% +\nTF-IDF 30%)", "6. Skill gap\nanalysis\n(matched/missing/\nadditional)"]
    for i, text in enumerate(steps):
        x = 0.4 + i * 2.2
        box(ax, x, 4.45, 1.95, 1.45, text, size=8.5)
        if i < len(steps) - 1:
            arrow(ax, x + 1.97, 5.17, x + 2.2, 5.17)
    steps2 = ["7. Personalised\nlearning\n(curated lessons,\nexamples, practice)", "8. Learning progress\nstorage\n(topics, paths)",
              "9. Add skill to CV\n(explicit confirm,\npreview, new version)", "10. Updated CV\nDOCX / PDF +\nnew match score", "11. Report\n(PDF)"]
    for i, text in enumerate(steps2):
        x = 0.4 + i * 2.2
        box(ax, x, 2.55, 1.95, 1.45, text, fc="#CCFBF1", ec=TEAL, size=8.5)
        if i < len(steps2) - 1:
            arrow(ax, x + 1.97, 3.27, x + 2.2, 3.27, TEAL)
    arrow(ax, 12.0, 4.45, 1.4, 4.02, GRAY)          # step 6 -> step 7 (wraps to next row)

    box(ax, 0.4, 0.35, 9.0, 1.4, "Database (SQLAlchemy):  PostgreSQL (primary)  or  SQLite (fallback)\n"
        "candidates - resumes - job_postings - skills - resume_skills - job_skills - match_results\n"
        "learning_modules - learning_paths - learning_progress - cv_versions", fc="#F1F5F9", ec=GRAY, size=9)
    box(ax, 9.8, 0.35, 3.8, 1.4, "Optional extras\nAI notes (API key)\nSemantic similarity\nMinIO / S3 storage", fc="#FEF3C7", ec="#B45309", size=9)
    arrow(ax, 7.0, 2.5, 5.5, 1.78, GRAY)
    arrow(ax, 7.0, 6.5, 7.0, 6.0, INDIGO)
    ax.text(0.45, 6.2, "pages call the modular pipeline in core/ (pipeline.py)", fontsize=8, color=GRAY)
    ax.text(13.6, 0.08, "Single-machine pipeline; no distributed processing is claimed.", ha="right", fontsize=8, color=GRAY)
    OUT.parent.mkdir(exist_ok=True)
    fig.savefig(OUT, dpi=140, bbox_inches="tight", facecolor="white")
    print("Wrote", OUT)


if __name__ == "__main__":
    main()
