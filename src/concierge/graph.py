"""The Meridian National Customer Service Concierge graph.

A custom LangGraph StateGraph implementing the classic agent loop:

    START -> agent -> (tools? -> agent)* -> END

Exported as `graph` for LangSmith / LangGraph CLI deployment.
"""

from __future__ import annotations

import logging
import os

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from openai import AuthenticationError

from concierge.context import get_prompt
from concierge.state import ConciergeState
from concierge.tools import TOOLS

load_dotenv(override=True)

logger = logging.getLogger(__name__)

# The system prompt (AGENTS.md) is pulled from LangSmith Context Hub at module
# import; a hub edit is picked up on the next process start. Falls back to the
# seed in concierge.prompts.SYSTEM_PROMPT when the hub is unreachable.
SYSTEM_PROMPT = get_prompt()


def _make_model() -> ChatOpenAI:
    model_name = os.getenv("CONCIERGE_MODEL", "gpt-4o-mini")
    base_url = os.getenv("BASE_URL")
    if base_url:
        # Route through the LangSmith LLM Gateway: callers authenticate with
        # their LangSmith API key; provider keys live in Provider Secrets.
        # LANGSMITH_API_KEY is a reserved name on LangSmith Cloud deployments
        # (the control plane injects it under the legacy LANGCHAIN_API_KEY
        # alias instead), so check both.
        gateway_key = os.getenv("LANGSMITH_API_KEY") or os.environ["LANGCHAIN_API_KEY"]
        client = ChatOpenAI(
            model=model_name,
            temperature=0.2,
            base_url=base_url,
            api_key=gateway_key,
        )
    else:
        client = ChatOpenAI(model=model_name, temperature=0.2)
    return client.bind_tools(TOOLS)


def healthcheck() -> bool:
    """Validate the gateway credential with a minimal call; log on auth failure."""
    try:
        _make_model().invoke([HumanMessage(content="ping")])
        return True
    except AuthenticationError as exc:
        logger.error("LLM gateway authentication failed at startup (401): %s", exc)
        return False


def agent_node(state: ConciergeState) -> dict:
    """Call the LLM with the message history plus the system prompt."""
    model = _make_model()
    messages = [SystemMessage(content=SYSTEM_PROMPT), *state["messages"]]
    try:
        response = model.invoke(messages)
    except AuthenticationError as exc:
        # The LangSmith LLM Gateway rejected our credential (401 invalid_api_key);
        # degrade gracefully with a user-facing message instead of an empty output.
        logger.error("LLM gateway authentication failed (401): %s", exc)
        degraded = AIMessage(
            content=(
                "The assistant is temporarily unavailable due to an LLM service "
                "authentication issue. Please try again shortly or escalate to support."
            )
        )
        return {
            "messages": [degraded],
            "retrieval_calls": state.get("retrieval_calls", 0),
        }

    retrieval_calls = state.get("retrieval_calls", 0)
    tool_calls = getattr(response, "tool_calls", None) or []
    new_retrievals = sum(
        1 for call in tool_calls if call.get("name") == "search_banking_docs"
    )

    return {
        "messages": [response],
        "retrieval_calls": retrieval_calls + new_retrievals,
    }


def _build_graph():
    builder = StateGraph(ConciergeState)
    builder.add_node("agent", agent_node)
    builder.add_node("tools", ToolNode(TOOLS, handle_tool_errors=True))

    builder.add_edge(START, "agent")
    builder.add_conditional_edges(
        "agent",
        tools_condition,
        {"tools": "tools", END: END},
    )
    builder.add_edge("tools", "agent")
    return builder.compile()


graph = _build_graph()

# Surface a bad/expired gateway credential at deploy time rather than on the
# first user request; failure is logged (not raised) so import still succeeds.
healthcheck()
