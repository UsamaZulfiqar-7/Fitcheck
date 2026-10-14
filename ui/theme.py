"""Look and feel: blue / indigo / white SaaS style, reusable HTML components."""
from __future__ import annotations

from html import escape

import streamlit as st

CSS = """
<style>
:root { --ink:#0F172A; --muted:#64748B; --line:#E2E8F0; --indigo:#4F46E5; --blue:#2563EB; --soft:#EEF2FF;
        --good:#059669; --warn:#D97706; --bad:#DC2626; }
html, body, [class*="css"] { font-family: "Inter","Segoe UI",system-ui,-apple-system,sans-serif; }
.block-container { padding-top: 1.4rem; padding-bottom: 3rem; max-width: 1180px; }
h1,h2,h3 { color: var(--ink); letter-spacing:-0.01em; }
[data-testid="stSidebar"] { background: linear-gradient(180deg,#1E1B4B 0%,#312E81 100%); }
[data-testid="stSidebar"] * { color:#E0E7FF !important; }
[data-testid="stSidebar"] input { color:#0F172A !important; }
[data-testid="stSidebar"] [role="radiogroup"] label { padding:.35rem .6rem; border-radius:10px; }
[data-testid="stSidebar"] [role="radiogroup"] label:hover { background:rgba(255,255,255,.10); }
.brand { font-size:1.55rem; font-weight:800; letter-spacing:-.02em; margin-bottom:.1rem; }
.brand span { color:#A5B4FC; }
.hero { background:linear-gradient(120deg,#1E3A8A 0%,#4F46E5 60%,#6366F1 100%); color:#fff; padding:1.6rem 1.8rem;
        border-radius:18px; margin-bottom:1.1rem; box-shadow:0 10px 30px rgba(79,70,229,.25); }
.hero h1 { color:#fff; margin:0 0 .3rem 0; font-size:1.9rem; }
.hero p { color:#E0E7FF; margin:0; font-size:1.02rem; max-width:760px; }
.kpi { background:#fff; border:1px solid var(--line); border-radius:16px; padding:1rem 1.1rem; height:100%;
       box-shadow:0 1px 2px rgba(15,23,42,.04); }
.kpi .label { color:var(--muted); font-size:.78rem; text-transform:uppercase; letter-spacing:.06em; font-weight:600; }
.kpi .value { color:var(--ink); font-size:1.9rem; font-weight:800; line-height:1.15; margin-top:.15rem; }
.kpi .sub { color:var(--muted); font-size:.82rem; margin-top:.15rem; }
.kpi.good .value { color:var(--good); } .kpi.warn .value { color:var(--warn); } .kpi.bad .value { color:var(--bad); }
.kpi.indigo .value { color:var(--indigo); }
.card { background:#fff; border:1px solid var(--line); border-radius:16px; padding:1.1rem 1.25rem; margin-bottom:.9rem; }
.card h4 { margin:.0rem 0 .4rem 0; color:var(--ink); }
.step { display:flex; gap:.8rem; align-items:flex-start; margin:.55rem 0; }
.step .num { background:var(--soft); color:var(--indigo); font-weight:800; width:2rem; height:2rem; border-radius:50%;
             display:flex; align-items:center; justify-content:center; flex:0 0 2rem; }
.step.done .num { background:var(--good); color:#fff; }
.step .t { font-weight:700; color:var(--ink); } .step .d { color:var(--muted); font-size:.9rem; }
.chip { display:inline-block; padding:.22rem .65rem; margin:.15rem .25rem .15rem 0; border-radius:999px; font-size:.82rem; font-weight:600; }
.chip.good { background:#D1FAE5; color:#065F46; } .chip.bad { background:#FEE2E2; color:#991B1B; }
.chip.warn { background:#FEF3C7; color:#92400E; } .chip.info { background:#DBEAFE; color:#1E40AF; }
.chip.muted { background:#F1F5F9; color:#475569; }
.badge { display:inline-block; padding:.18rem .6rem; border-radius:8px; font-size:.75rem; font-weight:700; background:var(--soft); color:var(--indigo); margin-right:.3rem; }
.empty { text-align:center; padding:2.2rem 1rem; border:2px dashed #C7D2FE; border-radius:18px; background:#fff; color:var(--muted); }
.empty h3 { color:var(--ink); margin-bottom:.3rem; }
.notice { background:#EFF6FF; border-left:4px solid var(--blue); padding:.7rem 1rem; border-radius:8px; color:#1E3A8A; font-size:.9rem; }
.stButton > button, .stDownloadButton > button { border-radius:10px; font-weight:600; }
.stButton > button[kind="primary"] { background:var(--indigo); border:0; }
@media (max-width: 900px) {
  .hero { padding:1.1rem 1.1rem; } .hero h1 { font-size:1.45rem; } .kpi .value { font-size:1.5rem; }
  .block-container { padding-left:1rem; padding-right:1rem; }
}
</style>
"""


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def hero(title: str, subtitle: str) -> None:
    st.markdown(f'<div class="hero"><h1>{escape(title)}</h1><p>{escape(subtitle)}</p></div>', unsafe_allow_html=True)


def kpi_html(label: str, value, sub: str = "", tone: str = "indigo") -> str:
    return (f'<div class="kpi {tone}"><div class="label">{escape(str(label))}</div>'
            f'<div class="value">{escape(str(value))}</div><div class="sub">{escape(sub)}</div></div>')


def kpi_row(items: list[tuple]) -> None:
    """items: (label, value, sub, tone)"""
    cols = st.columns(len(items))
    for col, item in zip(cols, items):
        label, value, *rest = item
        col.markdown(kpi_html(label, value, rest[0] if rest else "", rest[1] if len(rest) > 1 else "indigo"),
                     unsafe_allow_html=True)


def chips(items, tone: str = "info") -> str:
    if not items:
        return '<span class="chip muted">none</span>'
    return "".join(f'<span class="chip {tone}">{escape(str(i))}</span>' for i in items)


def badge(text: str) -> str:
    return f'<span class="badge">{escape(text)}</span>'


def card(html: str) -> None:
    st.markdown(f'<div class="card">{html}</div>', unsafe_allow_html=True)


def go(page: str) -> None:
    """on_click callback: jump to another page."""
    st.session_state["nav_target"] = page


def empty_state(title: str, text: str, button: str | None = None, target: str | None = None, key: str = "empty") -> None:
    st.markdown(f'<div class="empty"><h3>{escape(title)}</h3><p>{escape(text)}</p></div>', unsafe_allow_html=True)
    if button and target:
        _, mid, _ = st.columns([1, 1, 1])
        mid.button(button, key=key, on_click=go, args=(target,), type="primary", width="stretch")


def tone_for_score(score: float) -> str:
    return "good" if score >= 80 else "warn" if score >= 50 else "bad"
