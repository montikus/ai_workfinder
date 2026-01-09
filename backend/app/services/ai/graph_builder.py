from __future__ import annotations

from langgraph.graph import StateGraph, START, END

from .state import WorkflowState
from .agents import (
    make_supervisor_node,
    supervisor_router,
    make_search_agent_node,
    make_one_click_filter_agent_node,
    make_apply_agent_node,
)


def build_graph(llm):
    """
    One shared LLM instance is injected into every node via closures.
    """
    g = StateGraph(WorkflowState)

    g.add_node("supervisor", make_supervisor_node(llm))
    g.add_node("search_agent", make_search_agent_node(llm))
    g.add_node("filter_agent", make_one_click_filter_agent_node(llm))
    g.add_node("apply_agent", make_apply_agent_node(llm))

    g.add_edge(START, "supervisor")

    g.add_edge("search_agent", "supervisor")
    g.add_edge("filter_agent", "supervisor")
    g.add_edge("apply_agent", "supervisor")

    g.add_conditional_edges(
        "supervisor",
        supervisor_router,
        {
            "search": "search_agent",
            "filter": "filter_agent",
            "apply": "apply_agent",
            "done": END,
        },
    )

    return g.compile()
