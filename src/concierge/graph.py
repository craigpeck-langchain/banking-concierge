"""The Meridian National Customer Service Concierge graph.

A custom LangGraph StateGraph implementing the classic agent loop:

    START -> agent -> (tools? -> agent)* -> END

Exported as `graph` for LangSmith / LangGraph CLI deployment.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from concierge.context import get_prompt
from concierge.state import ConciergeState
from concierge.tools import TOOLS

load_dotenv(override=True)

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
        client = ChatOpenAI(
            model=model_name,
            temperature=0.2,
            base_url=base_url,
            api_key=os.environ["LANGSMITH_API_KEY"],
        )
    else:
        client = ChatOpenAI(model=model_name, temperature=0.2)
    return client.bind_tools(TOOLS)


ACCOUNT_LOOKUP_CAP = 3
ACCOUNT_LOOKUP_CAP_MESSAGE = (
    "I wasn't able to find a matching account holder with the identifier provided. "
    "The `account_lookup` tool only accepts `CUST-####` identifiers (for example "
    "`CUST-0001`). Could you share the `CUST-####` identifier on file for this caller?"
)


def agent_node(state: ConciergeState) -> dict:
    """Call the LLM with the message history plus the system prompt."""
    lookup_calls = state.get("account_lookup_calls", 0)
    retrieval_calls = state.get("retrieval_calls", 0)

    if lookup_calls >= ACCOUNT_LOOKUP_CAP:
        return {"messages": [AIMessage(content=ACCOUNT_LOOKUP_CAP_MESSAGE)]}

    model = _make_model()
    messages = [SystemMessage(content=SYSTEM_PROMPT), *state["messages"]]
    response = model.invoke(messages)

    tool_calls = getattr(response, "tool_calls", None) or []
    new_retrievals = sum(
        1 for call in tool_calls if call.get("name") == "search_banking_docs"
    )
    new_lookups = sum(
        1 for call in tool_calls if call.get("name") == "account_lookup"
    )

    return {
        "messages": [response],
        "retrieval_calls": retrieval_calls + new_retrievals,
        "account_lookup_calls": lookup_calls + new_lookups,
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
