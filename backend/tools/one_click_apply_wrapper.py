
from typing import List
import logging

from pydantic import BaseModel, Field, ValidationError

from backend.tools.parser_crawler import JobPosting
from backend.tools.one_click_apply_tool import one_click_apply_filter_tool

logger = logging.getLogger(__name__)


class OneClickWrapperInput(BaseModel):
    """
    Input schema for the 1-click-apply wrapper tool.

    Fields
    ------
    jobs:
        A list of job postings produced by the first tool in the pipeline
        (for example, the output of `justjoin_search_tool`). Each item must
        be compatible with the `JobPosting` Pydantic model defined in
        `backend.tools.parser_crawler`.
    """

    jobs: List[JobPosting] = Field(
        ...,
        description=(
            "List of job postings to filter. "
            "Each item should conform to the `JobPosting` schema."
        ),
        min_length=1,
    )


def one_click_apply_wrapper_tool(jobs: List[dict]) -> List[dict]:
    """
    Production-ready tool: filter job postings to those with '1-click Apply'.

    This function is designed to be registered directly as a tool for an
    LLM-based agent (LangChain / LangGraph). It performs:

    1. Input validation via `OneClickWrapperInput` to ensure that the provided
       jobs match the `JobPosting` schema expected by the underlying logic.
    2. Delegation to `one_click_apply_filter_tool`, which performs the actual
       filtering based on the presence of the "1-click Apply" badge in the
       `raw_snippet` field of each job posting.
    3. Conversion of the filtered `JobPosting` models back into dictionaries
       that are fully JSON-serializable and easy for agents to consume.

    Parameters
    ----------
    jobs:
        List of dictionaries representing job postings, typically the direct
        output from a discovery tool such as `justjoin_search_tool`. Each dict
        must be compatible with the `JobPosting` Pydantic model.

    Returns
    -------
    List[dict]
        A filtered list of job postings where each offer can be applied to
        directly via the "1-click Apply" button on justjoin.it, without
        redirecting to an external company website.

    Error handling
    --------------
    - If validation fails (e.g. wrong structure of `jobs`), the function logs
      the problem and returns an empty list.
    - If the underlying filter tool raises an exception, it is logged and an
      empty list is returned. This keeps the tool safe and predictable for
      LLM agents.
    """
    try:
        validated = OneClickWrapperInput(
            jobs=[JobPosting.model_validate(j) for j in jobs]
        )
    except ValidationError as exc:
        logger.warning("OneClickWrapperInput validation failed: %s", exc)
        return []

    try:
        filtered = one_click_apply_filter_tool(
            [job.model_dump() for job in validated.jobs]
        )
    except Exception as exc:
        logger.exception("Error while executing one_click_apply_filter_tool: %s", exc)
        return []

    return filtered
