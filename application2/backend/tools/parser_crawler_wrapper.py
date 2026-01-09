



from typing import List, Optional
import logging

from pydantic import BaseModel, Field, ValidationError

from backend.app.tools import search_jobs_tool, JobPosting

logger = logging.getLogger(__name__)


class JustJoinSearchInput(BaseModel):
    """
    Input schema for the JustJoin job search tool.

    Fields
    ------
    specialization:
        Candidate's primary specialization or tech stack. This is mapped to
        a category on justjoin.it (e.g. "python", "javascript", "devops", "ai").
    experience_level:
        Desired seniority level. Typical values:
        - "junior"
        - "mid"
        - "senior"
        - "c-level"
        The agent may also use some aliases (e.g. "jr", "джун"); they will be
        normalized by the underlying tool.
    location:
        Preferred location slug such as "warszawa", "krakow", "gdansk" or
        "all-locations" for the entire country. If omitted, all locations are used.
    limit:
        Maximum number of job postings to return. This is a hard cap on the size
        of the result list to keep tool responses compact.
    """

    specialization: str = Field(
        ...,
        description=(
            "Primary specialization or tech stack to search for "
            "(e.g. 'python', 'javascript', 'devops', 'ai')."
        ),
        min_length=1,
    )
    experience_level: Optional[str] = Field(
        default=None,
        description=(
            "Desired experience level (e.g. 'junior', 'mid', 'senior', 'c-level'). "
            "Can be omitted to search across all levels."
        ),
    )
    location: Optional[str] = Field(
        default=None,
        description=(
            "Preferred location slug (e.g. 'warszawa', 'krakow', 'all-locations'). "
            "If omitted, 'all-locations' is used."
        ),
    )
    limit: int = Field(
        default=20,
        ge=1,
        le=100,
        description=(
            "Maximum number of job postings to return from justjoin.it. "
            "Must be between 1 and 100."
        ),
    )


def justjoin_search_tool(
    specialization: str,
    experience_level: Optional[str] = None,
    location: Optional[str] = None,
    limit: int = 20,
) -> List[dict]:
    """
    Production-ready wrapper around `search_jobs_tool` for use as an agent tool.

    This function is designed to be registered as a tool in LangChain / LangGraph.
    It validates and normalizes the input using a Pydantic schema, calls the
    underlying `search_jobs_tool` from `parser_crawler`, and returns a list of
    JSON-serializable dictionaries representing job postings.

    Parameters
    ----------
    specialization:
        Candidate specialization or tech stack, such as "python", "javascript",
        "devops", "ai", ".net". This value is mapped to a justjoin.it category
        slug by the underlying crawler.
    experience_level:
        Desired seniority level, e.g. "junior", "mid", "senior", "c-level".
        If omitted, the tool will not restrict by seniority.
    location:
        Preferred location slug (e.g. "warszawa", "krakow", "all-locations").
        If omitted, all locations are searched.
    limit:
        Maximum number of job postings to return. Values outside the allowed
        range (1–100) will be rejected by validation.

    Returns
    -------
    List[dict]
        A list of dictionaries, each compatible with JSON serialization and
        derived from the `JobPosting` Pydantic model. Typical keys include:
        - "source"
        - "url"
        - "title"
        - "experience_level"
        - "raw_snippet"

    Error handling
    --------------
    - If validation fails, the function logs the error and returns an empty list.
    - If the underlying crawler raises an exception, it is logged and an empty
      list is returned. This keeps the tool safe and predictable for agents.
    """
    try:
        validated = JustJoinSearchInput(
            specialization=specialization,
            experience_level=experience_level,
            location=location,
            limit=limit,
        )
    except ValidationError as exc:
        logger.warning("JustJoinSearchInput validation failed: %s", exc)
        # In a production setting you might want to propagate a structured
        # error instead. For agent tools, returning an empty list is often
        # safer than raising.
        return []

    try:
        jobs: list[JobPosting] = search_jobs_tool(
            specialization=validated.specialization,
            experience_level=validated.experience_level,
            location=validated.location,
            limit=validated.limit,
        )
    except Exception as exc:
        logger.exception("Error while executing search_jobs_tool: %s", exc)
        return []

    return [job.model_dump() for job in jobs]
