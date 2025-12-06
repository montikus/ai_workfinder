from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from ai.state import RunInput, state_from_input, summary_from_state
from ai.graph_builder import build_graph


def main() -> int:
    # load .env into environment
    load_dotenv()

    base_url = os.getenv("OPENAI_BASE_URL", "").strip()
    api_key = os.getenv("OPENAI_API_KEY", "").strip()

    if not base_url or not api_key:
        raise SystemExit(
            "Missing OPENAI_BASE_URL / OPENAI_API_KEY in .env (or env vars)."
        )

    cfg_path = Path("config.json")
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))

    model = (cfg.get("llm_model") or os.getenv("OPENAI_MODEL", "")).strip()
    if not model:
        raise SystemExit("Missing llm_model in config.json (or OPENAI_MODEL env var).")

    llm = ChatOpenAI(
        base_url=base_url,
        api_key=api_key,
        model=model,
        temperature=0.0,
        timeout=60,
        max_retries=2,
    )

    run_input = RunInput(
        specialization=cfg["specialization"],
        experience_level=cfg.get("experience_level"),
        location=cfg.get("location"),
        limit=cfg.get("limit", 20),

        full_name=cfg["full_name"],
        email=cfg["email"],
        resume_path=cfg["resume_path"],

        headless=cfg.get("headless", True),
        timeout_sec=cfg.get("timeout_sec", 45),
        captcha_wait_sec=cfg.get("captcha_wait_sec", 180),
        slow_mo_ms=cfg.get("slow_mo_ms", 0),
        max_apply=cfg.get("max_apply", 10),
    )

    graph = build_graph(llm)
    state = state_from_input(run_input)

    final_state = graph.invoke(state)
    summary = summary_from_state(final_state)

    print(summary.model_dump_json(indent=2))
    return 0 if summary.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
