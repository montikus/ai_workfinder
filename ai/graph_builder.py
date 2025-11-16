from langchain_core.language_models.chat_models import BaseChatModel
from langgraph.graph import StateGraph, START, END

from .state import JobSearchState
from .agents import (
    create_supervisor_node,
    create_job_search_agent,
    create_contacts_extractor_agent,
    create_applicator_agent,
    JobSearchTool,
    ContactsTool,
    ApplyTool,
)


def build_job_search_graph(
    model: BaseChatModel,
    job_search_tool: JobSearchTool,
    contacts_tool: ContactsTool,
    apply_tool: ApplyTool,
):
    """
    Build the multi-agent job search graph:

    supervisor <-> (job_search, contacts_extractor, applicator) -> END
    """

    builder = StateGraph(JobSearchState)

    # Nodes
    builder.add_node("supervisor", create_supervisor_node(model))
    builder.add_node("job_search", create_job_search_agent(model, job_search_tool))
    builder.add_node(
        "contacts_extractor", create_contacts_extractor_agent(model, contacts_tool)
    )
    builder.add_node("applicator", create_applicator_agent(model, apply_tool))

    # Start from supervisor
    builder.add_edge(START, "supervisor")

    def route_from_supervisor(state: JobSearchState):
        return state.get("current_agent", "done")

    builder.add_conditional_edges(
        "supervisor",
        route_from_supervisor,
        {
            "job_search": "job_search",
            "contacts_extractor": "contacts_extractor",
            "applicator": "applicator",
            "done": END,
        },
    )

    # After every worker agent, go back to supervisor
    builder.add_edge("job_search", "supervisor")
    builder.add_edge("contacts_extractor", "supervisor")
    builder.add_edge("applicator", "supervisor")

    graph = builder.compile()
    return graph
