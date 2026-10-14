"""Optional AI enhancement. FitCheck works completely without it."""
from __future__ import annotations

import config


def available() -> bool:
    if not config.ANTHROPIC_API_KEY:
        return False
    try:
        import anthropic  # noqa: F401
        return True
    except Exception:
        return False


def personalised_notes(skill: str, job_title: str, job_text: str, resume_text: str) -> str:
    """Extra explanation + examples tailored to this candidate and job (markdown)."""
    if not available():
        raise RuntimeError("AI is not configured. Add ANTHROPIC_API_KEY to your .env file and install 'anthropic'.")
    import anthropic

    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    prompt = (
        f"A candidate wants to learn '{skill}' for the job '{job_title}'.\n"
        f"JOB TEXT:\n{job_text[:3500]}\n\nCANDIDATE CV:\n{resume_text[:3500]}\n\n"
        "Write beginner-friendly study notes in markdown: (1) how this job will actually use the skill, "
        "(2) how the candidate's existing skills help, (3) three short worked examples, (4) a 2-week study plan. "
        "Be technically accurate. Do not invent links, courses or claims about the candidate's experience."
    )
    reply = client.messages.create(model=config.AI_MODEL, max_tokens=1400,
                                   messages=[{"role": "user", "content": prompt}])
    return "".join(block.text for block in reply.content if getattr(block, "type", "") == "text")
