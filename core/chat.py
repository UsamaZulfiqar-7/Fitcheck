"""Intelligent Skill Gap & Career AI Assistant.

Provides expert, context-aware coaching for candidates closing skill gaps,
preparing for technical interviews, and tailoring their CV for enterprise roles (e.g. NetSol).
Works with Anthropic Claude when an API key is available, or via a rich built-in
domain knowledge engine offline.
"""
from __future__ import annotations

import re
from typing import Any

import config
from core import ai, learning_content as lc
from core.skills import skill_category


def ask_skill_assistant(
    question: str,
    context: dict[str, Any],
) -> str:
    """Generate an actionable, senior-level response to the candidate's question.

    `context` contains:
      - candidate_name: str
      - job_title: str
      - job_company: str | None
      - final_score: float
      - skill_score: float
      - text_similarity: float
      - matched: list[str]
      - missing_required: list[str]
      - missing_preferred: list[str]
      - job_text: str
      - resume_text: str
    """
    q_clean = question.strip()
    if not q_clean:
        return "Please ask a question regarding your skill gaps, interview preparation, or career roadmap!"

    # 1. If Anthropic Claude is configured, leverage it
    if ai.available():
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
            cand_name = context.get("candidate_name") or "Candidate"
            job_title = context.get("job_title") or "Target Role"
            company = context.get("job_company") or "Enterprise Software Company (e.g. NetSol Technologies)"
            missing_req = ", ".join(context.get("missing_required", [])) or "None"
            missing_pref = ", ".join(context.get("missing_preferred", [])) or "None"
            matched = ", ".join(context.get("matched", [])) or "None"
            score = context.get("final_score", 0.0)

            system_prompt = (
                f"You are FitCheck's Chief Technical Career Coach and AI Mentor, assisting candidate {cand_name} "
                f"targeting the role '{job_title}' at '{company}'.\n"
                f"The candidate has a current FitCheck match score of {score}/100.\n"
                f"- Matched Skills (already on CV): {matched}\n"
                f"- Missing Required Skills (High Priority Gaps): {missing_req}\n"
                f"- Missing Preferred Skills (Nice-to-Have): {missing_pref}\n\n"
                "Your objective is to provide executive, technically deep, encouraging, and high-impact advice. "
                "Structure your responses cleanly with markdown headers, bold keywords, code snippets, or bullet points. "
                "Offer practical interview strategies, enterprise-grade architecture patterns, and portfolio project guidance."
            )

            job_snippet = context.get("job_text", "")[:2500]
            user_msg = f"Candidate Question: {q_clean}\n\nContext:\nJob Description snippet:\n{job_snippet}"

            reply = client.messages.create(
                model=config.AI_MODEL,
                max_tokens=1500,
                system=system_prompt,
                messages=[{"role": "user", "content": user_msg}],
            )
            return "".join(b.text for b in reply.content if getattr(b, "type", "") == "text")
        except Exception:
            # Gracefully fall back to local domain engine if network/API fails
            pass

    # 2. Intelligent Built-in Expert Domain Engine (100% Offline & Instant)
    return _generate_offline_expert_response(q_clean, context)


def _generate_offline_expert_response(question: str, ctx: dict[str, Any]) -> str:
    """Rich rule-based AI reasoning engine providing deep, domain-specific guidance."""
    q_lower = question.lower()
    cand_name = ctx.get("candidate_name") or "Professional"
    job_title = ctx.get("job_title") or "Target Position"
    company = ctx.get("job_company") or "NetSol Technologies"
    missing_req = ctx.get("missing_required", [])
    missing_pref = ctx.get("missing_preferred", [])
    all_missing = missing_req + missing_pref
    matched = ctx.get("matched", [])
    score = ctx.get("final_score", 0.0)

    # Detect if user asks about a specific skill
    mentioned_skill = None
    for s in all_missing + matched + ["SQL", "Python", "Docker", "React", "Kafka", "Spark", "Pandas", "Power BI", "AWS", "Git"]:
        if re.search(r"\b" + re.escape(s.lower()) + r"\b", q_lower):
            mentioned_skill = s
            break

    # Intent 1: Priority / What should I learn first?
    if any(k in q_lower for k in ["priority", "first", "start", "order", "where to begin", "what should i learn"]):
        if not all_missing:
            return (
                f"### 🎯 Strategic Roadmap for **{cand_name}**\n\n"
                f"Great news! Your CV already covers all critical skills detected for **{job_title}**! "
                f"Your match score is **{score}/100**.\n\n"
                f"**Next Steps for Peak Interview Performance:**\n"
                f"1. **Deepen System Architecture:** Focus on scalability and optimization for `{', '.join(matched[:4])}`.\n"
                f"2. **Mock Technical Interviews:** Rehearse explaining your real-world architectural decisions.\n"
                f"3. **Domain Alignment:** Study {company}'s enterprise solutions, high-throughput financial transactions, and leasing workflows."
            )

        req_str = ", ".join(f"`{s}`" for s in missing_req) if missing_req else "None (All mandatory skills matched!)"
        pref_str = ", ".join(f"`{s}`" for s in missing_pref) if missing_pref else "None"
        top_focus = missing_req[0] if missing_req else missing_pref[0]

        return (
            f"### 📋 Strategic Skill Prioritization Matrix for **{cand_name}**\n\n"
            f"To maximize your hireability for **{job_title}** at **{company}**, follow this prioritized roadmap:\n\n"
            f"#### 🔴 Tier 1: Mandatory Core Gaps (Must Learn Immediately)\n"
            f"- **Skills:** {req_str}\n"
            f"- **Why:** In FitCheck's scoring formula, required skills carry a full weight of **1.0**. Missing these directly impacts technical shortlisting.\n"
            f"- **Immediate Action:** Start with **{top_focus}** in the *Personalized Learning Center*.\n\n"
            f"#### 🟡 Tier 2: Preferred Differentiators (Competitive Advantage)\n"
            f"- **Skills:** {pref_str}\n"
            f"- **Why:** These carrying **0.50 weight** and elevate your candidate profile from 'qualified' to 'top contender'.\n\n"
            f"#### ⏱️ Suggested 14-Day Sprint Schedule:\n"
            f"- **Days 1–5:** Complete the 5-stage roadmap for **{top_focus}** & build a proof-of-concept module.\n"
            f"- **Days 6–10:** Address the secondary missing skill with targeted code exercises.\n"
            f"- **Days 11–14:** Add the confirmed skills to your CV in FitCheck, review score lift, and export your polished resume."
        )

    # Intent 2: Interview Questions / Interview Prep
    if any(k in q_lower for k in ["interview", "questions", "ask me", "test me", "hr", "technical round"]):
        target_skill = mentioned_skill or (missing_req[0] if missing_req else (all_missing[0] if all_missing else "System Design"))
        return _build_interview_pack(target_skill, job_title, company)

    # Intent 3: Hands-on Enterprise Projects / Portfolio Ideas
    if any(k in q_lower for k in ["project", "portfolio", "build", "hands-on", "proof", "github"]):
        target_skill = mentioned_skill or (missing_req[0] if missing_req else (all_missing[0] if all_missing else "Fullstack/Data"))
        return _build_project_suggestions(target_skill, job_title, company)

    # Intent 4: How to Phrase on CV / Bullet Points
    if any(k in q_lower for k in ["cv", "resume", "bullet", "phrase", "wording", "add to cv", "write"]):
        target_skill = mentioned_skill or (all_missing[0] if all_missing else "Technical Skills")
        return (
            f"### ✍️ High-Impact CV Bullet Formulation: **{target_skill}**\n\n"
            f"When presenting your updated CV to enterprise recruiters at **{company}**, avoid vague phrases like *'Knowledge of {target_skill}'*. "
            f"Instead, use the **Google XYZ Formula**: *'Accomplished [X], as measured by [Y], by doing [Z]'*.\n\n"
            f"#### Executive Bullet Point Examples:\n"
            f"1. *“Architected and automated {target_skill} pipelines processing 50K+ daily records, reducing execution latency by 35%.”*\n"
            f"2. *“Integrated {target_skill} within existing microservices, enforcing structured logging, error boundaries, and ACID transaction compliance.”*\n"
            f"3. *“Implemented automated validation and indexing with {target_skill}, eliminating data reconciliation discrepancies across financial tables.”*\n\n"
            f"💡 **FitCheck Workflow Tip:** Once you finish the learning modules in the Learning Center, use the **'Add to My CV'** button. "
            f"FitCheck will safely insert this into your chosen section and dynamically recalculate your match score!"
        )

    # Intent 5: Specific Skill deep-dive
    if mentioned_skill:
        return _build_skill_deep_dive(mentioned_skill, job_title, company)

    # Intent 6: NetSol / Enterprise Presentation & Culture
    if any(k in q_lower for k in ["netsol", "enterprise", "fintech", "leasing", "presentation"]):
        return (
            f"### 🏢 NetSol Enterprise Alignment & Presentation Strategy\n\n"
            f"**NetSol Technologies** is a premier global provider of enterprise IT and asset finance/leasing solutions (e.g., NFS Ascent, Otoz). "
            f"When interviewing or presenting your technical profile to NetSol leadership:\n\n"
            f"#### 1. Core Engineering Values NetSol Looks For:\n"
            f"- **High Reliability & Zero Data Loss:** Enterprise leasing systems process millions in capital. Emphasize transaction integrity and robust error handling.\n"
            f"- **Clean Architecture & Scalability:** Show mastery of modular design, microservices/REST APIs, dependency injection, and maintainable unit test suites.\n"
            f"- **Database Mastery (SQL & Performance):** Relational schema design, complex joins, indexing, and query optimization are staple requirements.\n\n"
            f"#### 2. How FitCheck Proves Your Value:\n"
            f"- Demonstrate how you analyzed the **{job_title}** job requirements.\n"
            f"- Show your structured gap closure: how you identified `{', '.join(missing_req or ['key skills'])}` and systematically completed the roadmap.\n"
            f"- Present your updated, beautifully formatted CV and the audit-ready PDF match report!"
        )

    # Default Comprehensive Coaching Response
    req_list = ", ".join(missing_req) if missing_req else "None"
    return (
        f"### 💡 Technical Career Advice for **{cand_name}**\n\n"
        f"You are targeting **{job_title}** at **{company}**. Current FitCheck score: **{score}/100**.\n\n"
        f"- **Matched Strengths:** {', '.join(matched) if matched else 'Profile in progress'}\n"
        f"- **High-Priority Gaps:** {req_list}\n\n"
        f"**How can I assist you right now? You can ask me to:**\n"
        f"- 🎯 *“Provide 5 technical interview questions for {missing_req[0] if missing_req else 'my role'}”*\n"
        f"- 🛠️ *“Suggest an enterprise portfolio project using my missing skills”*\n"
        f"- ⏱️ *“Create a 2-week learning sprint plan”*\n"
        f"- 📝 *“How should I phrase my skills on my CV for NetSol?”*\n"
        f"- 📊 *“Explain how my match score was calculated”*"
    )


def _build_interview_pack(skill: str, job_title: str, company: str) -> str:
    """Generate high-yield technical interview questions for a skill."""
    packs: dict[str, list[tuple[str, str]]] = {
        "SQL": [
            ("Explain the difference between `WHERE` and `HAVING`, and when window functions like `ROW_NUMBER()` or `DENSE_RANK()` are preferred.",
             "**Answer Key:** `WHERE` filters rows before aggregation; `HAVING` filters aggregated groups. Window functions compute running calculations over row partitions without collapsing individual rows."),
            ("How do database indexes (B-Tree) improve query performance, and what is the trade-off during `INSERT`/`UPDATE` operations?",
             "**Answer Key:** B-Tree indexes provide O(log n) lookups by sorting key values. The trade-off is write overhead: every insert or update requires the database engine to maintain index balance."),
            ("How do you detect and resolve SQL deadlocks in concurrent enterprise transactions?",
             "**Answer Key:** Enforce consistent lock acquisition orders across transactions, keep transactions short, utilize appropriate isolation levels (e.g. Read Committed), and handle transient deadlock retries."),
        ],
        "Python": [
            ("How does Python handle memory management and garbage collection?",
             "**Answer Key:** Python uses reference counting as its primary mechanism alongside a cyclic generational garbage collector (gc module) that detects circular references."),
            ("Explain the difference between threading, multiprocessing, and `asyncio` for scalable applications.",
             "**Answer Key:** Threading is subject to the GIL (best for I/O bound tasks). Multiprocessing spawns separate processes with independent memory (CPU-bound). `asyncio` is single-threaded cooperative multitasking using an event loop."),
            ("What are Python decorators, and how would you build one for API request rate limiting or performance telemetry?",
             "**Answer Key:** Decorators wrap functions using closures to modify behavior without altering the source function. A telemetry decorator uses `functools.wraps` to time `func(*args, **kwargs)` and log execution durations."),
        ],
        "Docker": [
            ("What is the difference between an image layer and a running container, and how do you achieve multi-stage builds?",
             "**Answer Key:** Layers are immutable read-only snapshots. Containers add a thin read-write layer on top. Multi-stage builds use separate `FROM` statements to compile assets and copy only minimal binaries into final production images."),
            ("How do you manage persistent data and secrets securely in Docker?",
             "**Answer Key:** Use named Docker Volumes for stateful data persistence. Pass secrets via environment files or Docker Secrets, avoiding hardcoding in Dockerfiles."),
        ],
        "React": [
            ("Explain the React Fiber reconciliation algorithm and how the Virtual DOM minimizes reflows.",
             "**Answer Key:** Fiber splits rendering work into incremental chunks that can be paused or prioritized. The diffing algorithm compares virtual trees in O(n) time and batches updates to the real DOM."),
            ("When would you use `useMemo` and `useCallback` versus normal declarations?",
             "**Answer Key:** `useMemo` caches computationally intensive return values; `useCallback` caches function references across rerenders to prevent unnecessary child component rerendering."),
        ],
    }

    questions = packs.get(skill)
    if not questions:
        questions = [
            (f"What are the core design patterns and best practices associated with {skill} in modern software architectures?",
             f"**Answer Key:** Focus on modularity, clear separation of concerns, defensive error handling, and test-driven validation when working with {skill}."),
            (f"How do you profile, debug, and monitor performance bottlenecks when utilizing {skill} in production?",
             f"**Answer Key:** Utilize structured telemetry, APM tools, logging libraries, and proactive load testing to identify bottlenecks before production releases."),
        ]

    output = [
        f"### 🎯 Top Technical Interview Questions: **{skill}**\n",
        f"*Curated for {job_title} candidates at {company}*\n",
    ]
    for idx, (q, a) in enumerate(questions, 1):
        output.append(f"#### Q{idx}: {q}")
        output.append(f"> 💡 {a}\n")

    output.append(
        "**Recruiter Advice:** In interviews, always explain your reasoning out loud: define the trade-offs, mention scalability, and relate back to business impact!"
    )
    return "\n".join(output)


def _build_project_suggestions(skill: str, job_title: str, company: str) -> str:
    """Generate enterprise-ready portfolio project ideas."""
    return (
        f"### 🛠️ Production-Ready Portfolio Projects: **{skill}**\n\n"
        f"To prove your mastery of **{skill}** for **{job_title}** at **{company}**, build and document one of these enterprise projects:\n\n"
        f"#### Project Option 1: Automated Financial Analytics & Reconciliation Pipeline\n"
        f"- **Concept:** Build a high-throughput processing pipeline that ingests raw transactional CSV/JSON feeds, cleanses anomalies, and outputs structured analytical metrics.\n"
        f"- **Tech Stack:** `{skill}`, Python/SQL, Automated Unit Tests (pytest), Dockerized container.\n"
        f"- **What to Showcase:** ACID compliance, parameterized configuration, exception logging, and 99%+ test coverage.\n\n"
        f"#### Project Option 2: Real-time Metric Monitoring & Audit Dashboard\n"
        f"- **Concept:** An enterprise monitoring service that tracks customer leasing applications, status progressions, and KPI thresholds.\n"
        f"- **Tech Stack:** `{skill}`, RESTful API, Streamlit or React frontend, Relational DB.\n"
        f"- **What to Showcase:** Role-based access logic, clean data visualization, responsive layout, and clean documentation with architectural diagrams.\n\n"
        f"⭐ **GitHub Best Practice:** Include a polished `README.md` with an architecture diagram, setup instructions, and an explanation of technical trade-offs!"
    )


def _build_skill_deep_dive(skill: str, job_title: str, company: str) -> str:
    """Detailed domain brief for a specific skill."""
    cat = skill_category(skill)
    curated = lc.has_curated(skill)
    badge = "Full Curated Roadmap Available" if curated else "Starter Path Available"

    return (
        f"### 📘 Technical Briefing: **{skill}** (`{cat}`)\n\n"
        f"- **FitCheck Status:** {badge}\n"
        f"- **Role Relevance:** Essential for high-standard execution in **{job_title}** at **{company}**.\n\n"
        f"#### Core Competency Checklist:\n"
        f"1. **Fundamentals:** Syntax, core abstractions, and environment configuration.\n"
        f"2. **Real-world Application:** Querying, data transformation, or component lifecycle handling.\n"
        f"3. **Optimization & Defensive Coding:** Indexing, exception handling, and edge-case mitigation.\n"
        f"4. **Enterprise Integration:** Packaging, CI/CD pipeline deployment, and automated testing.\n\n"
        f"👉 **Next Action:** Jump to the **Personalized Learning Center** from the sidebar to review the full 5-stage lessons and interactive practice questions for **{skill}**!"
    )
