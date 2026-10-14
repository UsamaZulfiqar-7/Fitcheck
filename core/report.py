"""Downloadable PDF match report."""
from __future__ import annotations

import io
from html import escape

from core.matching import DISCLAIMER, formula_text, score_band


def build_report_pdf(candidate: str, job_title: str, company: str | None, current: dict, baseline: dict | None,
                     learned: list[str], progress: list[dict]) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    ss = getSampleStyleSheet()
    indigo = colors.HexColor("#1E3A8A")
    h1 = ParagraphStyle("h1", parent=ss["Title"], textColor=indigo, fontSize=22)
    h2 = ParagraphStyle("h2", parent=ss["Heading2"], textColor=indigo, spaceBefore=12)
    body = ParagraphStyle("b", parent=ss["BodyText"], fontSize=10, leading=14)
    small = ParagraphStyle("s", parent=body, fontSize=8.5, textColor=colors.HexColor("#475569"))

    def table(rows, widths):
        t = Table(rows, colWidths=widths)
        t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
                               ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EEF2FF")),
                               ("PADDING", (0, 0), (-1, -1), 6), ("FONTSIZE", (0, 0), (-1, -1), 9.5)]))
        return t

    def join(items):
        return escape(", ".join(items)) if items else "None"

    story = [Paragraph("FitCheck - Match Report", h1),
             Paragraph(f"Candidate: <b>{escape(candidate)}</b><br/>Job: <b>{escape(job_title)}</b>"
                       f"{' at ' + escape(company) if company else ''}", body), Spacer(1, 8)]
    rows = [["Final match score", f"{current['final_score']} / 100  ({score_band(current['final_score'])})"],
            ["Skill match", f"{current['skill_score']} / 100"],
            ["Text similarity", f"{current['text_similarity']} / 100"],
            ["Weights", f"skills {current['skill_weight']:.2f} | text {current['text_weight']:.2f} | "
                        f"preferred-skill weight {current['preferred_weight']:.2f}"]]
    if baseline and baseline["final_score"] != current["final_score"]:
        rows.insert(1, ["Original CV score", f"{baseline['final_score']} / 100"])
    story += [table(rows, [140, 360]), Spacer(1, 6), Paragraph(escape(formula_text(current)), small)]

    story += [Paragraph("Skill gap analysis", h2),
              Paragraph(f"<b>Matched skills:</b> {join(current['matched'])}", body),
              Paragraph(f"<b>Missing required skills:</b> {join(current['missing_required'])}", body),
              Paragraph(f"<b>Missing preferred skills:</b> {join(current['missing_preferred'])}", body),
              Paragraph(f"<b>Additional skills in the CV:</b> {join(current['additional'])}", body)]

    story.append(Paragraph("Learning progress", h2))
    if progress:
        data = [["Skill", "Status", "Topics done"]] + [
            [p["skill"], p["status"].replace("_", " "), f"{p['done']}/{p['total']}"] for p in progress]
        t = Table(data, colWidths=[200, 120, 100])
        t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
                               ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEF2FF")),
                               ("PADDING", (0, 0), (-1, -1), 5)]))
        story.append(t)
    else:
        story.append(Paragraph("No learning started yet.", body))
    story.append(Paragraph(f"<b>Skills added to the CV after confirmation:</b> {join(learned)}", body))
    story += [Spacer(1, 14), Paragraph(escape(DISCLAIMER), small)]

    buffer = io.BytesIO()
    SimpleDocTemplate(buffer, pagesize=A4, leftMargin=44, rightMargin=44, topMargin=40, bottomMargin=40).build(story)
    return buffer.getvalue()
