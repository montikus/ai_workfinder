from langchain_core.language_models.chat_models import BaseChatModel

from .state import UserProfile, make_initial_state, JobSearchState
from .graph_builder import build_job_search_graph


def build_model() -> BaseChatModel:
    """
    TODO: plug in ChatOllama / ChatOpenAI / Groq / etc. here.

    Example:

    from langchain_ollama import ChatOllama
    return ChatOllama(model="llama3.1", temperature=0)
    """
    raise NotImplementedError("Implement build_model() for your environment")

#test build model invoke
from backend.tools.job_search import search_jobs
from backend.tools.contacts_extraction import extract_contacts
from backend.tools.apply_jobs import apply_for_jobs


def run_example() -> JobSearchState:
    model = build_model()

    graph = build_job_search_graph(
        model=model,
        job_search_tool=search_jobs,
        contacts_tool=extract_contacts,
        apply_tool=apply_for_jobs,
    )

    profile = UserProfile(
        stack=["python", "fastapi", "postgresql"],
        years_experience=2,
        location="Poland",
        remote_only=True,
        languages=["English", "Polish"],
        cv_url="https://example.com/cv.pdf",
    )

    initial_state = make_initial_state(
        user_profile=profile,
        user_request=(
            "Find junior/mid backend Python positions (remote / Poland / EU) "
            "and automatically apply for them."
        ),
    )

    final_state: JobSearchState = graph.invoke(
        initial_state,
        config={"recursion_limit": 25},
    )

    return final_state


if __name__ == "__main__":
    state = run_example()
    print(f"Total applications: {len(state['applications'])}")
