
from __future__ import annotations

from typing import List, Optional, Dict, Any
import logging
import re
import argparse
import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
)

USER_AGENT = "JobAgentBot/0.1 (contact: your-email@example.com)"

session = requests.Session()
session.headers.update({'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7',
    'cache-control': 'max-age=0',
    'dnt': '1',
    'priority': 'u=0, i',
    'sec-ch-ua': '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36'})


# -----------------------------
# Pydantic model
# -----------------------------


class JobPosting(BaseModel):
    """
    Structured representation of a single job posting from justjoin.it.

    Fields
    ------
    source:
        Identifier of the job board. For now it is always `"justjoin"`,
        but this field allows you to extend the tool to more sources later.
    url:
        Absolute URL pointing to the job offer page on justjoin.it.
    title:
        Parsed job title as it appears on the listing (e.g. "Junior Python Developer").
    company:
        Optional company name (not populated at listing level in this basic version).
    location:
        Optional location string (not populated at listing level in this basic version).
    salary:
        Optional salary string (not populated at listing level in this basic version).
    experience_level:
        Normalized experience level passed into the search, e.g. "junior", "mid",
        "senior", or "c-level". This is echoed back so the agent can keep context.
    raw_snippet:
        Raw textual snippet extracted from the listing tile. It may contain company,
        salary, tags and other noisy but sometimes useful information.
    """

    source: str
    url: str
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    salary: Optional[str] = None
    experience_level: Optional[str] = None
    raw_snippet: Optional[str] = None


# -----------------------------
# Low-level helpers
# -----------------------------


def _fetch_html(url: str, params: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """
    Fetch raw HTML from a URL with basic error handling.

    Parameters
    ----------
    url:
        Base URL to call.
    params:
        Optional query parameters to be passed to `requests.get`.

    Returns
    -------
    Optional[str]
        HTML content as a string, or `None` if the request fails.
    """
    try:
        resp = session.get(url, params=params, timeout=10)
        resp.raise_for_status()
        return resp.text
    except requests.RequestException as exc:
        logger.warning("Failed to fetch %s: %s", url, exc)
        return None


def _normalize_specialization(raw: str) -> str:
    """
    Normalize a human-readable specialization into a justjoin.it category slug.

    The mapping is based on how justjoin.it structures its job-offers URLs.
    For example:
        "python"      -> "python"
        "javascript"  -> "javascript"
        "devops"      -> "devops"
        "ai/ml"       -> "ai"
        ".net"        -> "net"

    If a value is not found in the mapping, the function falls back to using
    the first lower-cased word, which often already matches a slug.
    """
    if not raw:
        return "python"

    val = raw.strip().lower()

    mapping = {
        # AI/ML
        "ai": "ai",
        "ml": "ai",
        "ai/ml": "ai",
        "machine learning": "ai",

        # javascript
        "javascript": "javascript",
        "js": "javascript",
        "java script": "javascript",

        # html
        "html": "html",

        # php
        "php": "php",

        # ruby
        "ruby": "ruby",

        # python
        "python": "python",
        "backend python": "python",

        # java
        "java": "java",

        # .net
        ".net": "net",
        "net": "net",

        # scala
        "scala": "scala",

        # c
        "c": "c",

        # mobile
        "mobile": "mobile",
        "android": "mobile",
        "ios": "mobile",

        # testing
        "testing": "testing",
        "qa": "testing",

        # devops
        "devops": "devops",
        "sre": "devops",

        # admin
        "admin": "admin",
        "sysadmin": "admin",
        "system administrator": "admin",

        # ux/ui
        "ux": "ux",
        "ui": "ux",
        "ux/ui": "ux",
        "ui/ux": "ux",

        # pm
        "pm": "pm",
        "project manager": "pm",
        "product manager": "pm",

        # game
        "game": "game",
        "gamedev": "game",
        "game dev": "game",

        # analytics
        "analytics": "analytics",
        "analyst": "analytics",

        # security
        "security": "security",
        "infosec": "security",
        "cybersecurity": "security",

        # data
        "data": "data",
        "data engineer": "data",
        "data science": "data",

        # go
        "go": "go",
        "golang": "go",

        # support
        "support": "support",
        "helpdesk": "support",

        # erp
        "erp": "erp",

        # architecture
        "architecture": "architecture",
        "architect": "architecture",

        # other
        "other": "other",
        "others": "other",
    }

    if val in mapping:
        return mapping[val]

    return val.split()[0]


def _normalize_location(raw: Optional[str]) -> str:
    """
    Normalize a free-form location string to a justjoin.it location slug.

    Examples
    --------
    - None          -> "all-locations"
    - "Warszawa"    -> "warszawa"
    - "KRAKOW"      -> "krakow"
    """
    if not raw:
        return "all-locations"
    return raw.strip().lower()


def _normalize_experience(raw: Optional[str]) -> Optional[str]:
    """
    Normalize an experience level label into the value expected by justjoin.it.

    The tool supports both English and some informal labels (e.g. in Polish
    or Russian) and maps them to one of:

    - "junior"
    - "mid"
    - "senior"
    - "c-level"

    If the value is unknown, it is returned as-is.
    """
    if not raw:
        return None

    val = raw.strip().lower()

    mapping = {
        # junior
        "jun": "junior",
        "jr": "junior",
        "junior": "junior",
        "джун": "junior",

        # mid
        "mid": "mid",
        "regular": "mid",
        "middle": "mid",
        "мид": "mid",

        # senior
        "sen": "senior",
        "sr": "senior",
        "senior": "senior",
        "сеньор": "senior",

        # manager / c-level
        "manager": "c-level",
        "menedżer": "c-level",
        "менеджер": "c-level",
        "lead": "c-level",
        "c-level": "c-level",
    }

    return mapping.get(val, val)


# -----------------------------
# Public API for agents
# -----------------------------


def search_jobs(
    specialization: str,
    experience_level: Optional[str] = None,
    location: Optional[str] = None,
    limit_per_source: int = 20,
) -> List[JobPosting]:
    """
    Search justjoin.it for job offers matching the given filters.

    This is a convenience wrapper around `crawl_justjoin` that:
    - normalizes the specialization, experience and location,
    - encapsulates error handling,
    - and returns a list of `JobPosting` models.

    Parameters
    ----------
    specialization:
        Candidate specialization such as "python", "javascript", "devops", "ai".
        This is mapped to a justjoin.it category slug.
    experience_level:
        Desired experience level, for example "junior", "mid", "senior", "c-level".
        The value is normalized and then used as `experience-level` query parameter.
    location:
        Optional preferred location (e.g. "warszawa", "krakow", "all-locations").
        If omitted, "all-locations" is used.
    limit_per_source:
        Maximum number of job postings to return. For this module there is only
        one source, justjoin.it, so it acts as a simple overall limit.

    Returns
    -------
    List[JobPosting]
        A list of Pydantic models, one per job offer.
    """
    specialization_slug = _normalize_specialization(specialization)
    location_slug = _normalize_location(location)
    experience_norm = _normalize_experience(experience_level)

    jobs: List[JobPosting] = []

    try:
        jj_jobs = crawl_justjoin(
            specialization_slug=specialization_slug,
            location_slug=location_slug,
            experience_level=experience_norm,
            limit=limit_per_source,
        )
        jobs.extend(jj_jobs)
    except Exception as exc:
        logger.exception("Error while crawling justjoin.it: %s", exc)

    return jobs


def search_jobs_tool(
    specialization: str,
    experience_level: Optional[str] = None,
    location: Optional[str] = None,
    limit: int = 20,
) -> List[JobPosting]:
    """
    Tool: Search job offers on justjoin.it based on candidate profile.

    This function is intended to be exposed directly as a LangChain / LangGraph
    tool for an AI agent that assists users with job hunting and auto-applying.

    Overview
    --------
    The tool takes high-level candidate preferences (specialization,
    experience level, location), translates them into justjoin.it URL slugs
    and query parameters, fetches the corresponding listing page, parses
    job tiles, and returns a structured list of job postings.

    Inputs
    ------
    specialization:
        Candidate's primary specialization or tech stack.
        Examples: `"python"`, `"javascript"`, `"devops"`, `"ai"`, `".net"`.
        The value is mapped internally to a justjoin.it category segment.

    experience_level:
        Desired seniority level.
        Supported values (case-insensitive, some aliases supported):
        - `"junior"`   (or `jun`, `jr`, `джун`)
        - `"mid"`      (or `regular`, `middle`, `мид`)
        - `"senior"`   (or `sen`, `sr`, `сеньор`)
        - `"c-level"`  (or `manager`, `менеджер`, `lead`)
        If omitted, all levels are returned.

    location:
        Preferred location slug, for example:
        - `"warszawa"`, `"krakow"`, `"gdansk"`
        - `"all-locations"` for the entire country
        If omitted, `"all-locations"` is used.

    limit:
        Maximum number of job postings to return from justjoin.it.
        This is a simple cap on the size of the result list to keep tool
        responses reasonably small for the agent.

    Output
    ------
    List[JobPosting]
        A list of `JobPosting` Pydantic models. For each job the agent receives:
        - `source`: `"justjoin"`
        - `url`: direct link to the offer
        - `title`: parsed job title
        - `experience_level`: normalized level passed into the tool
        - `raw_snippet`: raw text extracted from the listing tile

    Typical agent usage
    -------------------
    1. The agent builds a candidate profile from the conversation
       (e.g. specialization = "python", experience = "junior", location = "warszawa").
    2. It calls this tool with those parameters.
    3. It inspects the returned `JobPosting` list to:
       - rank or filter offers,
       - explain options to the user,
       - or trigger follow-up tools that open the offer and prepare an application.

    Notes
    -----
    - This tool only works with justjoin.it.
    - Parsing is done at the listing-tile level; deeper parsing of the offer
      details page can be added later if needed.
    """
    return search_jobs(
        specialization=specialization,
        experience_level=experience_level,
        location=location,
        limit_per_source=limit,
    )


# -----------------------------
# JustJoin IT crawler
# -----------------------------


def crawl_justjoin(
    specialization_slug: str,
    location_slug: str = "all-locations",
    experience_level: Optional[str] = None,
    limit: int = 20,
) -> List[JobPosting]:
    """
    Low-level crawler for justjoin.it listing pages.

    This function operates on already-normalized slugs and is not meant to be
    exposed directly as a tool. Prefer `search_jobs` / `search_jobs_tool`
    when integrating with agents.
    """
    base_url = f"https://justjoin.it/job-offers/{location_slug}/{specialization_slug}"

    params: Dict[str, Any] = {
        "orderBy": "DESC",
        "sortBy": "published",
    }
    if experience_level:
        params["experience-level"] = experience_level

    logger.info("Crawling JustJoin: %s params=%s", base_url, params)

    html = _fetch_html(base_url, params=params)
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    jobs: List[JobPosting] = []

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if not href.startswith("/job-offer/"):
            continue

        job_url = "https://justjoin.it" + href

        text = " ".join(a.stripped_strings)
        title = _extract_job_title_from_list_text(text)

        job = JobPosting(
            source="justjoin",
            url=job_url,
            title=title,
            raw_snippet=text or None,
            experience_level=experience_level,
        )
        jobs.append(job)

        if len(jobs) >= limit:
            break

    return jobs


def _extract_job_title_from_list_text(text: str) -> Optional[str]:
    """
    Extract a best-effort job title from a raw listing tile text.

    Heuristic:
    - JustJoin tiles often look like:
        "Machine Learning Engineer 280 000 - 320 000 PLN/year Company ..."
    - This helper cuts the string at the first salary/currency marker and
      treats the left-hand side as the title.
    """
    if not text:
        return None

    cut_patterns = [" PLN", " EUR", " USD", " zł", " pln"]
    idx = len(text)
    for p in cut_patterns:
        pos = text.find(p)
        if pos != -1 and pos < idx:
            idx = pos

    trimmed = text[:idx].strip()
    trimmed = re.sub(r"\s+", " ", trimmed)
    return trimmed or None


# -----------------------------
# CLI for manual testing
# -----------------------------


def _main_cli() -> None:
    """
    Minimal command-line interface for manual testing and debugging.

    This is not intended for agents. It allows a human developer to quickly
    verify that crawling and parsing still work after code changes, for example:

        poetry run python -m backend.tools.parser_crawler \\
            --spec python \\
            --exp junior \\
            --location warszawa \\
            --limit 5
    """
    parser = argparse.ArgumentParser(
        description="Test job crawler for justjoin.it",
    )
    parser.add_argument(
        "--spec",
        "--specialization",
        dest="specialization",
        required=True,
        help="Specialization, e.g. python, java, ai, javascript, devops, ...",
    )
    parser.add_argument(
        "--location",
        dest="location",
        default=None,
        help="Location for JustJoin, e.g. warszawa, krakow, all-locations",
    )
    parser.add_argument(
        "--exp",
        "--experience",
        dest="experience",
        default=None,
        help="Experience level: junior / mid / senior / c-level",
    )
    parser.add_argument(
        "--limit",
        dest="limit",
        type=int,
        default=10,
        help="Max offers to return",
    )

    args = parser.parse_args()

    jobs = search_jobs(
        specialization=args.specialization,
        experience_level=args.experience,
        location=args.location,
        limit_per_source=args.limit,
    )
    print(jobs)



if __name__ == "__main__":
    _main_cli()
