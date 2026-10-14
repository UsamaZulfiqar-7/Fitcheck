"""Plotly charts. Every chart is drawn from real analysis data passed in by the pages."""
from __future__ import annotations

import plotly.graph_objects as go

INDIGO, BLUE, SOFT, GOOD, WARN = "#4F46E5", "#2563EB", "#E0E7FF", "#059669", "#D97706"
_LAYOUT = dict(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
               font=dict(family="Plus Jakarta Sans, Inter, sans-serif", color="#0F172A"), margin=dict(l=10, r=10, t=40, b=10))


def gauge(score: float, title: str = "Overall match") -> go.Figure:
    color = GOOD if score >= 80 else WARN if score >= 50 else "#DC2626"
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=score, number={"suffix": " / 100", "font": {"size": 34}},
        title={"text": title, "font": {"size": 15}},
        gauge={"axis": {"range": [0, 100]}, "bar": {"color": color, "thickness": 0.3}, "bgcolor": SOFT,
               "steps": [{"range": [0, 50], "color": "#EEF2FF"}, {"range": [50, 80], "color": "#E0E7FF"},
                         {"range": [80, 100], "color": "#C7D2FE"}]}))
    fig.update_layout(height=250, **_LAYOUT)
    return fig


def breakdown(skill_score: float, text_score: float, sw: float, tw: float, final: float) -> go.Figure:
    labels = ["Skill match", "Text similarity", "Final score"]
    values = [skill_score, text_score, final]
    fig = go.Figure(go.Bar(x=values, y=labels, orientation="h", marker_color=[BLUE, "#818CF8", INDIGO],
                           text=[f"{v:.1f}" for v in values], textposition="outside"))
    fig.update_xaxes(range=[0, 110], showgrid=False, visible=False)
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(height=250, title=dict(text=f"Score breakdown (weights: skills {sw:.0%}, text {tw:.0%})",
                                              font=dict(size=14)), **_LAYOUT)
    return fig


def required_vs_matched(counts: dict[str, dict[str, int]]) -> go.Figure:
    cats = list(counts)
    fig = go.Figure()
    fig.add_bar(name="Skills in job posting", x=cats, y=[counts[c]["job"] for c in cats], marker_color="#C7D2FE")
    fig.add_bar(name="Matched in CV", x=cats, y=[counts[c]["matched"] for c in cats], marker_color=INDIGO)
    fig.update_layout(barmode="group", height=330, title=dict(text="Job skills vs matched skills by category",
                                                              font=dict(size=14)),
                      legend=dict(orientation="h", y=-0.25), **_LAYOUT)
    fig.update_yaxes(dtick=1, gridcolor="#E2E8F0")
    return fig


def score_history(labels: list[str], scores: list[float]) -> go.Figure:
    fig = go.Figure(go.Scatter(x=labels, y=scores, mode="lines+markers+text", text=[f"{s:.1f}" for s in scores],
                               textposition="top center", line=dict(color=INDIGO, width=3), marker=dict(size=9)))
    fig.update_yaxes(range=[0, 105], gridcolor="#E2E8F0")
    fig.update_layout(height=280, title=dict(text="Match score after each CV update", font=dict(size=14)), **_LAYOUT)
    return fig


def progress_bars(skills: list[str], percents: list[float]) -> go.Figure:
    fig = go.Figure(go.Bar(x=percents, y=skills, orientation="h", marker_color=INDIGO,
                           text=[f"{p:.0f}%" for p in percents], textposition="outside"))
    fig.update_xaxes(range=[0, 115], showgrid=False, visible=False)
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(height=max(180, 60 * len(skills) + 60),
                      title=dict(text="Learning progress per skill", font=dict(size=14)), **_LAYOUT)
    return fig
