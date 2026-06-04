"""Agent context — pulled from LangSmith Context Hub at runtime.

The concierge's system prompt (``AGENTS.md``) lives in the LangSmith Context
Hub, NOT in this repo. Engine should look here to find where the agent's
context comes from — but the actual prompt content is edited in the Context
Hub UI, not in the codebase. The hallucination failure mode (the
"answer rate questions from memory" instruction) is fixed by editing
``AGENTS.md`` in the hub, with no code redeploy. (The PII leak, by contrast,
lives in ``tools.py`` and is fixed via an Engine GitHub PR.)

``concierge.prompts.SYSTEM_PROMPT`` is only the seed pushed to the hub by
``scripts/setup_context_hub.py`` and the offline fallback used when the hub
is unreachable — it is not the runtime source of truth.
"""

from __future__ import annotations

from langsmith import Client

CONTEXT_HUB_REPO = "banking-concierge-agent"


def get_prompt() -> str:
    """Return the concierge system prompt, pulled from LangSmith Context Hub.

    Falls back to the seed in ``concierge.prompts.SYSTEM_PROMPT`` when the hub
    is unreachable or the repo hasn't been seeded yet — run
    ``python -m scripts.setup_context_hub`` to initialize it.
    """
    try:
        agent = Client().pull_agent(CONTEXT_HUB_REPO)
        content = getattr(agent.files["AGENTS.md"], "content", "")
        if content:
            return content
    except Exception:
        pass

    from concierge.prompts import SYSTEM_PROMPT

    return SYSTEM_PROMPT
