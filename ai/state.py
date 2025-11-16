from typing import Literal, List
from pydantic import BaseModel, Field

from langgraph.graph import MessagesState
from langchain_core.messages import HumanMessage, AnyMessage


class UserProfile(BaseModel):
    stack: List[str] = Field(..., description="Main technology stack")
    years_experience: int = Field(
        ..., ge=0, description="Number of years of commercial experience"
    )
    location: str | None = Field(
        None, description="Preferred location (city/country)"
    )
    remote_only: bool = Field(
        True, description="Whether to search only for remote positions"
    )
    salary_min_eur: int | None = Field(
        None,
        description="Minimum desired salary in EUR (brutto/netto — as you decide)",
    )
    languages: List[str] = Field(
        default_factory=list, description="Languages (e.g. EN, PL, etc.)"
    )
    cv_url: str | None = Field(
        None, description="URL to the CV (PDF) if it is already hosted somewhere"
    )


class JobLead(BaseModel):
    """Raw job posting returned by the job search tool."""

    title: str | None = None
    company: str | None = None
    source: str | None = None  # which job board / site
    url: str | None = None
    raw_data: dict | None = None


class JobContact(BaseModel):
    """Contact data extracted for a specific job lead."""

    job_url: str
    emails: List[str] = Field(default_factory=list)
    apply_urls: List[str] = Field(
        default_factory=list,
        description="Direct URLs to application forms / 'Apply' pages",
    )


class ApplicationResult(BaseModel):
    """Result of applying for a specific job."""

    job_url: str
    status: Literal["applied", "skipped", "failed"]
    reason: str | None = None


AgentName = Literal[
    "supervisor",
    "job_search",
    "contacts_extractor",
    "applicator",
    "done",
]


class JobSearchState(MessagesState):
    """
    Graph state for the job search flow.

    Inherits from MessagesState, so it also contains the `messages` field
    used by LangGraph for conversation history.
    """

    user_profile: UserProfile
    leads: List[JobLead]
    contacts: List[JobContact]
    applications: List[ApplicationResult]
    current_agent: AgentName


def make_initial_state(
    user_profile: UserProfile,
    user_request: str,
) -> JobSearchState:
    """
    Helper to build the initial state from the user profile and request text.
    """
    initial_message = HumanMessage(content=user_request, name="user")

    state: JobSearchState = {
        "messages": [initial_message],
        "user_profile": user_profile,
        "leads": [],
        "contacts": [],
        "applications": [],
        "current_agent": "supervisor",
    }
    return state
