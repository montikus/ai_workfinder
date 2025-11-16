import json
from typing import Callable, List

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from .state import (
    JobSearchState,
    UserProfile,
    JobLead,
    JobContact,
    ApplicationResult,
    AgentName,
)


def create_supervisor_node(model: BaseChatModel):
    """
    Create a supervisor node for the multi-agent job search system.

    The supervisor decides which agent should run next based on the current state.
    """

    system_prompt = """
    You are the supervisor of a multi-agent job search system.
    You have three agents:

    - job_search: searches for job postings based on the candidate profile and fills the `leads` list.
    - contacts_extractor: visits URLs from `leads`, extracts emails/links and fills the `contacts` list.
    - applicator: uses `contacts` and the candidate profile to apply for jobs and writes statuses into `applications`.

    ALWAYS respond ONLY with JSON in the format:
    {"next_agent": "<one of: job_search | contacts_extractor | applicator | done>"}
    No additional text around JSON.
    """.strip()

    def supervisor_node(state: JobSearchState) -> dict:
        profile: UserProfile = state["user_profile"]
        leads_count = len(state["leads"])
        contacts_count = len(state["contacts"])
        apps_count = len(state["applications"])

        context_str = (
            "Candidate profile:\n"
            f"{profile.model_dump_json(indent=2, ensure_ascii=False)}\n\n"
            f"Current state: leads={leads_count}, contacts={contacts_count}, "
            f"applications={apps_count}.\n"
            "Decide which agent should be executed next."
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=context_str),
        ]

        ai_msg = model.invoke(messages)
        if not isinstance(ai_msg, AIMessage):
            # Fallback in case the model returns a different message type
            ai_msg = AIMessage(content=str(ai_msg))

        try:
            data = json.loads(ai_msg.content)
            next_agent: AgentName = data.get("next_agent", "done")
        except Exception:
            next_agent = "done"

        return {
            "messages": [ai_msg],
            "current_agent": next_agent,
        }

    return supervisor_node


JobSearchTool = Callable[[UserProfile], List[JobLead]]


def create_job_search_agent(
    model: BaseChatModel,
    search_tool: JobSearchTool,
):
    """
    Agent that calls the job search tool (scraper / API) to find job leads.
    """

    def node(state: JobSearchState) -> dict:
        profile = state["user_profile"]

        # TODO: if you want, you can first use the model to generate a text query
        # and then pass it into the tool. For now, we pass the profile directly.
        new_leads = search_tool(profile)

        all_leads = list(state["leads"]) + new_leads

        return {
            "leads": all_leads,
            "current_agent": "contacts_extractor",
        }

    return node


ContactsTool = Callable[[List[JobLead]], List[JobContact]]


def create_contacts_extractor_agent(
    model: BaseChatModel,
    contacts_tool: ContactsTool,
):
    """
    Agent that takes job leads and extracts contact information
    (emails / application URLs) using a crawling/parsing tool.
    """

    def node(state: JobSearchState) -> dict:
        leads = state["leads"]
        if not leads:
            # Nothing to process
            return {"current_agent": "done"}

        new_contacts = contacts_tool(leads)
        all_contacts = list(state["contacts"]) + new_contacts

        return {
            "contacts": all_contacts,
            "current_agent": "applicator",
        }

    return node


ApplyTool = Callable[[UserProfile, List[JobContact]], List[ApplicationResult]]


def create_applicator_agent(
    model: BaseChatModel,
    apply_tool: ApplyTool,
):
    """
    Agent that sends applications (emails / fills forms) for each contact
    and writes the result into the `applications` list.
    """

    def node(state: JobSearchState) -> dict:
        profile = state["user_profile"]
        contacts = state["contacts"]

        if not contacts:
            return {"current_agent": "done"}

        results = apply_tool(profile, contacts)
        all_apps = list(state["applications"]) + results

        return {
            "applications": all_apps,
            "current_agent": "done",
        }

    return node
