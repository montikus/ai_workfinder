from __future__ import annotations

from dotenv import load_dotenv
load_dotenv()
import argparse
import logging
import os

from langchain_openai import ChatOpenAI

from .state import RunInput, state_from_input, summary_from_state
from .graph_builder import build_graph


def _setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="[%(levelname)s] %(name)s: %(message)s",
    )


def _build_llm(base_url: str, api_key: str, model: str):
    """
    OpenAI-compatible endpoint (Azure AI Foundry exports OpenAI-compatible base_url).
    You pass:
      - base_url: e.g. https://.../openai/v1/
      - api_key: your key
      - model: deployment_name (e.g. Llama-4-Maverick-... FP8)
    """
    return ChatOpenAI(
        base_url=base_url,
        api_key=api_key,
        model=model,
        temperature=0.0,
        timeout=60,
        max_retries=2,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="AI_WORKFINDER - JustJoin 1-click auto-apply pipeline (LLM enabled)")

    # pipeline args
    parser.add_argument("--spec", "--specialization", dest="specialization", required=True)
    parser.add_argument("--exp", "--experience", dest="experience_level", default=None)
    parser.add_argument("--location", dest="location", default=None)
    parser.add_argument("--limit", dest="limit", type=int, default=20)

    parser.add_argument("--name", dest="full_name", required=True)
    parser.add_argument("--email", dest="email", required=True)
    parser.add_argument("--resume", dest="resume_path", required=True)

    parser.add_argument("--max-apply", dest="max_apply", type=int, default=10)

    parser.add_argument("--headed", dest="headed", action="store_true")
    parser.add_argument("--timeout", dest="timeout_sec", type=int, default=45)
    parser.add_argument("--captcha-wait", dest="captcha_wait_sec", type=int, default=180)
    parser.add_argument("--slow", dest="slow_mo_ms", type=int, default=0)

    # LLM args (also can be provided via env)
    parser.add_argument("--llm-base-url", dest="llm_base_url", default=os.getenv("OPENAI_BASE_URL", ""))
    parser.add_argument("--llm-api-key", dest="llm_api_key", default=os.getenv("OPENAI_API_KEY", ""))
    parser.add_argument("--llm-model", dest="llm_model", default=os.getenv("OPENAI_MODEL", ""))

    parser.add_argument("--log", dest="log_level", default="INFO")

    args = parser.parse_args()
    _setup_logging(args.log_level)

    if not args.llm_base_url or not args.llm_api_key or not args.llm_model:
        raise SystemExit(
            "Missing LLM config. Provide --llm-base-url, --llm-api-key, --llm-model "
            "or set env OPENAI_BASE_URL, OPENAI_API_KEY, OPENAI_MODEL."
        )

    llm = _build_llm(args.llm_base_url, args.llm_api_key, args.llm_model)

    run_input = RunInput(
        specialization=args.specialization,
        experience_level=args.experience_level,
        location=args.location,
        limit=args.limit,
        full_name=args.full_name,
        email=args.email,
        resume_path=args.resume_path,
        headless=not args.headed,
        timeout_sec=args.timeout_sec,
        captcha_wait_sec=args.captcha_wait_sec,
        slow_mo_ms=args.slow_mo_ms,
        max_apply=args.max_apply,
    )

    graph = build_graph(llm)
    state = state_from_input(run_input)

    final_state = graph.invoke(state)
    summary = summary_from_state(final_state)
    logging.info('answer %r',summary)

    print(summary.model_dump_json(indent=2))
    return 0 if summary.ok else 1


main()