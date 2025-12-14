

from typing import List, Optional
import logging

from pydantic import BaseModel, Field, ValidationError

from backend.tools.parser_crawler import JobPosting

logger = logging.getLogger(__name__)


class OneClickFilterInput(BaseModel):
    """
    Input schema for the one-click-apply filter tool.

    Fields
    ------
    jobs:
        A list of job postings produced by the first agent's tool.
        Each element must be compatible with the `JobPosting` Pydantic model,
        for example the result of `job.model_dump()` from `parser_crawler`.
    """

    jobs: List[JobPosting] = Field(
        ...,
        description=(
            "List of job postings to filter. Each item should match the "
            "`JobPosting` schema produced by the justjoin.it crawler."
        ),
        min_length=1,
    )


def _has_one_click_apply(job: JobPosting, label: str = "1-click Apply") -> bool:
    """
    Check if a job posting supports 1-click apply on justjoin.it.

    The detection is based on the `raw_snippet` field, which stores the visible
    text extracted from the listing tile. If this text contains the configured
    label (by default '1-click Apply'), we assume the offer can be applied to
    directly on justjoin.it.
    """
    if not job.raw_snippet:
        return False
    return label.lower() in job.raw_snippet.lower()


def filter_one_click_apply(jobs: List[JobPosting]) -> List[JobPosting]:
    """
    Filter a list of `JobPosting` objects to keep only 1-click apply offers.

    Parameters
    ----------
    jobs:
        List of `JobPosting` instances returned by the justjoin.it crawler.

    Returns
    -------
    List[JobPosting]
        Subset of the input list where each job has the '1-click Apply'
        badge on justjoin.it.
    """
    return [job for job in jobs if _has_one_click_apply(job)]


def one_click_apply_filter_tool(jobs: List[dict]) -> List[dict]:
    """
    Tool: Filter job offers to only those with '1-click Apply' on justjoin.it.

    This function is designed to be exposed as a tool in LangGraph / LangChain.
    It accepts a JSON-serializable list of job objects (as dictionaries),
    validates them against the `JobPosting` schema, applies the one-click-apply
    filter, and returns a filtered list of dictionaries.

    Expected input
    --------------
    jobs:
        A list of job representations produced by the first agent's search tool.
        Typically this is the direct output of a tool like:

            justjoin_search_tool(...) -> List[dict]

        where each dict matches the `JobPosting` schema from
        `backend.tools.parser_crawler`.

    Output
    ------
    List[dict]
        A filtered list of job postings, containing only those offers that can
        be applied to via the "1-click Apply" button on justjoin.it, i.e.
        without leaving the platform for an external company site.

    Typical usage in a multi-agent pipeline
    ---------------------------------------
    1. The discovery agent calls a search tool to obtain a broad list of offers.
       Example fields: title, url, experience_level, raw_snippet, etc.
    2. The filtering agent calls this tool with that list to keep only offers
       that support quick in-platform application.
    3. The filtered list is then used by downstream agents to:
       - prepare personalized applications,
       - decide where to auto-apply,
       - or present "instant apply" options to the user.

    Error handling
    --------------
    - If validation fails (the input list cannot be converted to `JobPosting`),
      the function logs the error and returns an empty list.
    - Any unexpected runtime errors are logged and also result in an empty list,
      so the tool remains safe and predictable for LLM agents.
    """
    try:
        input_model = OneClickFilterInput(
            jobs=[JobPosting.model_validate(j) for j in jobs]
        )
    except ValidationError as exc:
        logger.warning("OneClickFilterInput validation failed: %s", exc)
        return []

    try:
        filtered_jobs: List[JobPosting] = filter_one_click_apply(input_model.jobs)
    except Exception as exc:
        logger.exception("Error while filtering one-click-apply jobs: %s", exc)
        return []

    return [job.model_dump() for job in filtered_jobs]


if __name__ == "__main__":
    jobs = [
    JobPosting(
        source='justjoin',
        url='https://justjoin.it/job-offer/shimi-sp-z-o-o--python-developer-warszawa-python',
        title='Python Developer 75 - 120',
        company=None,
        location=None,
        salary=None,
        experience_level='junior',
        raw_snippet='Python Developer 75 - 120 PLN/h 75 - 120 PLN/h Shimi Sp. z o.o. Warszawa 7d left AWS Terraform Python AWS Terraform Python 7d left',
    ),
    JobPosting(
        source='justjoin',
        url='https://justjoin.it/job-offer/kodland-korepetytor-online---python-i-scratch-warszawa-python',
        title='Korepetytor online - Python i Scratch 2 967 - 3 391',
        company=None,
        location=None,
        salary=None,
        experience_level='junior',
        raw_snippet='Korepetytor online - Python i Scratch 2 967 - 3 391 PLN/month 2 967 - 3 391 PLN/month KODLAND Warszawa , + 4 Locations 8d left Roblox Unity Scartch Roblox Unity Scartch 8d left',
    ),
    JobPosting(
        source='justjoin',
        url='https://justjoin.it/job-offer/kodland-korepetytor-online---python-pro-warszawa-python-037e63ca',
        title='Korepetytor online - Python Pro 2 967 - 3 391',
        company=None,
        location=None,
        salary=None,
        experience_level='junior',
        raw_snippet='Korepetytor online - Python Pro 2 967 - 3 391 PLN/month 2 967 - 3 391 PLN/month KODLAND Warszawa , + 3 Locations 8d left Tutoring Python Python PRO Tutoring Python Python PRO 8d left',
    ),
    JobPosting(
        source='justjoin',
        url='https://justjoin.it/job-offer/kodland-korepetytor-online---python-pro-warszawa-python',
        title='Korepetytor online - Python Pro 2 967 - 3 391',
        company=None,
        location=None,
        salary=None,
        experience_level='junior',
        raw_snippet='Korepetytor online - Python Pro 2 967 - 3 391 PLN/month 2 967 - 3 391 PLN/month KODLAND Warszawa , + 3 Locations 8d left Tutoring Python Python PRO Tutoring Python Python PRO 8d left',
    ),
    JobPosting(
        source='justjoin',
        url='https://justjoin.it/job-offer/szkola-w-chmurze-junior-backend-developer-warszawa-python',
        title='Junior Backend Developer Undisclosed Salary Undisclosed Salary Szkoła w Chmurze Warszawa 13d left Git SQL Docker Git SQL Docker 13d left',
        company=None,
        location=None,
        salary=None,
        experience_level='junior',
        raw_snippet='Junior Backend Developer Undisclosed Salary Undisclosed Salary Szkoła w Chmurze Warszawa 13d left Git SQL Docker Git SQL Docker 13d left',
    ),
    JobPosting(
        source='justjoin',
        url='https://justjoin.it/job-offer/7n-junior-fullstack-developer-python-react-django--warszawa-python',
        title='Super offer Junior Fullstack Developer (Python, React, Django) 8 400 - 12 600',
        company=None,
        location=None,
        salary=None,
        experience_level='junior',
        raw_snippet='Super offer Junior Fullstack Developer (Python, React, Django) 8 400 - 12 600 PLN/month 8 400 - 12 600 PLN/month 7N Warszawa 13d left 1-click Apply Python Scrum Software Development Python Scrum Software Development 1-click Apply 13d left',
    ),
    JobPosting(
        source='justjoin',
        url='https://justjoin.it/job-offer/codility-content-services-delivery-engineer-warszawa-python',
        title='Content Services & Delivery Engineer Undisclosed Salary Undisclosed Salary Codility Warszawa , + 2 Locations 3d left Analytical Thinking Python Data Analytical Thinking Python Data 3d left',
        company=None,
        location=None,
        salary=None,
        experience_level='junior',
        raw_snippet='Content Services & Delivery Engineer Undisclosed Salary Undisclosed Salary Codility Warszawa , + 2 Locations 3d left Analytical Thinking Python Data Analytical Thinking Python Data 3d left',
    ),
    JobPosting(
        source='justjoin',
        url='https://justjoin.it/job-offer/ness-solution-implementation-support---payment-systems-warszawa-python',
        title='Implementation Support – Payment Systems 60 - 75',
        company=None,
        location=None,
        salary=None,
        experience_level='junior',
        raw_snippet='Implementation Support – Payment Systems 60 - 75 PLN/h 60 - 75 PLN/h Ness Solution Warszawa 3d left Oracle Oracle 3d left',
    ),
    JobPosting(
        source='justjoin',
        url='https://justjoin.it/job-offer/blockwise-junior-data-engineer-python--warszawa-python',
        title='Junior Data Engineer (Python) 7 000 - 12 000',
        company=None,
        location=None,
        salary=None,
        experience_level='junior',
        raw_snippet='Junior Data Engineer (Python) 7 000 - 12 000 PLN/month 7 000 - 12 000 PLN/month BlockWise Warszawa 19d left Python SQL Linux Python SQL Linux 19d left',
    ),
    JobPosting(
        source='justjoin',
        url='https://justjoin.it/job-offer/epam-systems-python-mentee-warszawa-python',
        title='Python Mentee Undisclosed Salary Undisclosed Salary EPAM Systems Warszawa , + 4 Locations 6d left Analytical Thinking Databases Algorithms Analytical Thinking Databases Algorithms 6d left',
        company=None,
        location=None,
        salary=None,
        experience_level='junior',
        raw_snippet='Python Mentee Undisclosed Salary Undisclosed Salary EPAM Systems Warszawa , + 4 Locations 6d left Analytical Thinking Databases Algorithms Analytical Thinking Databases Algorithms 6d left',
    ),
    JobPosting(
        source='justjoin',
        url='https://justjoin.it/job-offer/datafuze-junior-python-engineer-warszawa-python',
        title='Junior Python Engineer 7 000 - 10 000',
        company=None,
        location=None,
        salary=None,
        experience_level='junior',
        raw_snippet='Junior Python Engineer 7 000 - 10 000 PLN/month 7 000 - 10 000 PLN/month DataFuze Warszawa 2d left 1-click Apply Python Docker SQL Python Docker SQL 1-click Apply 2d left',
    ),
    JobPosting(
        source='justjoin',
        url='https://justjoin.it/job-offer/cloudfide-junior-data-engineer-warszawa-python',
        title='Junior Data Engineer Undisclosed Salary Undisclosed Salary Cloudfide Warszawa 22d left Python Databricks Microsoft SQL Python Databricks Microsoft SQL 22d left',
        company=None,
        location=None,
        salary=None,
        experience_level='junior',
        raw_snippet='Junior Data Engineer Undisclosed Salary Undisclosed Salary Cloudfide Warszawa 22d left Python Databricks Microsoft SQL Python Databricks Microsoft SQL 22d left',
    ),
    JobPosting(
        source='justjoin',
        url='https://justjoin.it/job-offer/square-one-junior-python-developer-z-ai-warszawa-python',
        title='Junior Python Developer Z AI 65 - 75',
        company=None,
        location=None,
        salary=None,
        experience_level='junior',
        raw_snippet='Junior Python Developer Z AI 65 - 75 PLN/h 65 - 75 PLN/h Square One Warszawa 5d left 1-click Apply AI Python ORM AI Python ORM 1-click Apply 5d left',
    ),
    JobPosting(
        source='justjoin',
        url='https://justjoin.it/job-offer/senovo-it-hunior-python-developer---b2b-remote-warszawa-python',
        title='Junior Python Developer 14 000 - 15 000',
        company=None,
        location=None,
        salary=None,
        experience_level='junior',
        raw_snippet='Junior Python Developer 14 000 - 15 000 PLN/month 14 000 - 15 000 PLN/month Senovo-It Warszawa 8d left 1-click Apply Flask API Django Flask API Django 1-click Apply 8d left',
    ),
    JobPosting(
        source='justjoin',
        url='https://justjoin.it/job-offer/cloudfide-junior-engineer-opportunity-warszawa-python',
        title='Junior Engineer Opportunity Undisclosed Salary Undisclosed Salary Cloudfide Warszawa , + 2 Locations 21d left MS SQL Microsoft SQL Spring Boot MS SQL Microsoft SQL Spring Boot 21d left',
        company=None,
        location=None,
        salary=None,
        experience_level='junior',
        raw_snippet='Junior Engineer Opportunity Undisclosed Salary Undisclosed Salary Cloudfide Warszawa , + 2 Locations 21d left MS SQL Microsoft SQL Spring Boot MS SQL Microsoft SQL Spring Boot 21d left',
    ),
]

    filtered = filter_one_click_apply(jobs)
    print(filtered)
