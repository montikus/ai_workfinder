from __future__ import annotations

import logging
from typing import Any, Dict, List, Callable

from langchain_core.messages import SystemMessage, HumanMessage

from backend.tools.parser_crawler_wrapper import justjoin_search_tool
from backend.tools.one_click_apply_wrapper import one_click_apply_wrapper_tool
from backend.tools.apply_tool import apply_to_job_tool

from .state import WorkflowState

logger = logging.getLogger(__name__)


def _trace_append(state: WorkflowState, item: Dict[str, Any]) -> Dict[str, Any]:
    cur = list(state.get("llm_trace", []) or [])
    cur.append(item)
    return {"llm_trace": cur}


def make_supervisor_node(llm) -> Callable[[WorkflowState], Dict[str, Any]]:
    def supervisor_node(state: WorkflowState) -> Dict[str, Any]:
        """
        Supervisor orchestrates phases and routes to the next agent.
        It does NOT rewrite/transform other agents' outputs, only routes.
        LLM is used here just to validate connection + produce a tiny routing note.
        """
        phase = state.get("phase", "init")
        err = state.get("error")

        if err:
            logger.error("Supervisor sees error, stopping. error=%s", err)
            return {"phase": "done", "status": "error"}

        # LLM ping (real call) - very small + cheap
        try:
            msg = llm.invoke(
                [
                    SystemMessage(content="You are the supervisor of a job-application pipeline. Reply in 1 short line."),
                    HumanMessage(content=f"Current phase={phase}. What is the next phase label? (init/search/filter/apply/done)"),
                ]
            )
            note = getattr(msg, "content", "") if msg else ""
        except Exception as e:
            # if LLM fails, we still can run deterministic pipeline
            note = f"llm_error:{e}"

        base_trace = _trace_append(state, {"agent": "supervisor", "phase": phase, "note": note})

        if phase == "init":
            return {**base_trace, "phase": "search", "status": "running"}

        if phase == "after_search":
            return {**base_trace, "phase": "filter", "status": "running"}

        if phase == "after_filter":
            if not state.get("one_click_jobs"):
                return {**base_trace, "phase": "done", "status": "done"}
            return {**base_trace, "phase": "apply", "status": "running"}

        if phase == "after_apply":
            results = state.get("apply_results", []) or []
            ok_any = any(isinstance(r, dict) and r.get("ok") and r.get("applied") for r in results)
            return {**base_trace, "phase": "done", "status": "partial_done" if ok_any else "done"}

        return {**base_trace, "phase": "done", "status": state.get("status", "done")}

    return supervisor_node


def supervisor_router(state: WorkflowState) -> str:
    phase = state.get("phase", "init")
    if phase == "search":
        return "search"
    if phase == "filter":
        return "filter"
    if phase == "apply":
        return "apply"
    return "done"


def make_search_agent_node(llm) -> Callable[[WorkflowState], Dict[str, Any]]:
    def search_agent_node(state: WorkflowState) -> Dict[str, Any]:
        """
        Agent1: uses specialization + experience_level (+ optional location),
        calls justjoin_search_tool, returns jobs list.
        LLM is used only as a small preflight (doesn't alter tool output).
        """
        try:
            specialization = state["specialization"]
            experience_level = state.get("experience_level")
            location = state.get("location")
            limit = int(state.get("limit", 20))

            # LLM preflight (real call)
            try:
                msg = llm.invoke(
                    [
                        SystemMessage(content="You are Agent1. Reply in 1 line. No JSON."),
                        HumanMessage(content=f"Search plan: spec={specialization}, exp={experience_level}, loc={location}, limit={limit}."),
                    ]
                )
                note = getattr(msg, "content", "") if msg else ""
            except Exception as e:
                note = f"llm_error:{e}"

            logger.info("Agent1(search) -> justjoin_search_tool spec=%s exp=%s loc=%s limit=%s",
                        specialization, experience_level, location, limit)

            jobs: List[Dict[str, Any]] = justjoin_search_tool(
                specialization=specialization,
                experience_level=experience_level,
                location=location,
                limit=limit,
            )

            logger.info("Agent1(search) got %d jobs", len(jobs))
            trace = _trace_append(state, {"agent": "agent1_search", "note": note, "jobs_count": len(jobs)})
            return {**trace, "jobs": jobs, "phase": "after_search"}

        except Exception as exc:
            logger.exception("Agent1(search) failed: %s", exc)
            return {"error": f"search_agent_failed: {exc}", "phase": "error", "status": "error"}

    return search_agent_node


def make_one_click_filter_agent_node(llm) -> Callable[[WorkflowState], Dict[str, Any]]:
    def one_click_filter_agent_node(state: WorkflowState) -> Dict[str, Any]:
        """
        Agent2: takes jobs from Agent1 and calls one_click_apply_wrapper_tool.
        LLM is used only as a small preflight (doesn't alter tool output).
        """
        try:
            jobs = state.get("jobs", []) or []

            try:
                msg = llm.invoke(
                    [
                        SystemMessage(content="You are Agent2. Reply in 1 line."),
                        HumanMessage(content=f"Filter 1-click apply from {len(jobs)} jobs."),
                    ]
                )
                note = getattr(msg, "content", "") if msg else ""
            except Exception as e:
                note = f"llm_error:{e}"

            logger.info("Agent2(filter) -> one_click_apply_wrapper_tool input=%d jobs", len(jobs))

            filtered: List[Dict[str, Any]] = one_click_apply_wrapper_tool(jobs)

            logger.info("Agent2(filter) got %d one-click jobs", len(filtered))
            trace = _trace_append(state, {"agent": "agent2_filter", "note": note, "one_click_count": len(filtered)})
            return {**trace, "one_click_jobs": filtered, "phase": "after_filter"}

        except Exception as exc:
            logger.exception("Agent2(filter) failed: %s", exc)
            return {"error": f"one_click_filter_failed: {exc}", "phase": "error", "status": "error"}

    return one_click_filter_agent_node


def make_apply_agent_node(llm) -> Callable[[WorkflowState], Dict[str, Any]]:
    def apply_agent_node(state: WorkflowState) -> Dict[str, Any]:
        """
        Agent3: applies using Playwright tool.
        CV/resume_path is used ONLY here.
        LLM is used only as a small preflight (doesn't alter tool output).
        """
        try:
            jobs = state.get("one_click_jobs", []) or []
            max_apply = int(state.get("max_apply", 10))
            jobs = jobs[:max_apply]

            full_name = state["full_name"]
            email = state["email"]
            resume_path = state["resume_path"]

            headless = bool(state.get("headless", True))
            timeout_sec = int(state.get("timeout_sec", 45))
            captcha_wait_sec = int(state.get("captcha_wait_sec", 180))
            slow_mo_ms = int(state.get("slow_mo_ms", 0))

            try:
                msg = llm.invoke(
                    [
                        SystemMessage(content="You are Agent3. Reply in 1 line."),
                        HumanMessage(content=f"Apply to {len(jobs)} jobs. Candidate={full_name}, email={email}."),
                    ]
                )
                note = getattr(msg, "content", "") if msg else ""
            except Exception as e:
                note = f"llm_error:{e}"

            logger.info("Agent3(apply) starting: jobs=%d headless=%s timeout=%s captcha_wait=%s slow_mo=%s",
                        len(jobs), headless, timeout_sec, captcha_wait_sec, slow_mo_ms)

            results: List[Dict[str, Any]] = []
            for idx, job in enumerate(jobs, start=1):
                url = (job or {}).get("url")
                if not url:
                    results.append({"ok": False, "applied": False, "job_url": None, "step": "validation", "error": "missing_url"})
                    continue

                logger.info("Agent3(apply) [%d/%d] applying to %s", idx, len(jobs), url)

                res = apply_to_job_tool(
                    job_url=url,
                    full_name=full_name,
                    email=email,
                    resume_path=resume_path,
                    attach_message=None,
                    headless=headless,
                    timeout_sec=timeout_sec,
                    captcha_wait_sec=captcha_wait_sec,
                    slow_mo_ms=slow_mo_ms,
                )
                if not isinstance(res, dict):
                    res = {"ok": False, "applied": False, "job_url": url, "step": "runtime", "error": "non_dict_result"}

                results.append(res)

            trace = _trace_append(state, {"agent": "agent3_apply", "note": note, "attempted": len(results)})
            return {**trace, "apply_results": results, "phase": "after_apply"}

        except Exception as exc:
            logger.exception("Agent3(apply) failed: %s", exc)
            return {"error": f"apply_agent_failed: {exc}", "phase": "error", "status": "error"}

    return apply_agent_node
