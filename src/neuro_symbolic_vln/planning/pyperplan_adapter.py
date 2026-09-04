"""Adapter for running pyperplan with bounded execution time and strict typing."""

from __future__ import annotations

import hashlib
import multiprocessing as mp
import os
import queue
import tempfile
import time
from dataclasses import dataclass
from typing import Any

from pyperplan.planner import HEURISTICS, SEARCHES, search_plan

from neuro_symbolic_vln.contracts import (
    CommittedPlanningState,
    PlanResult,
    PlanStatus,
    SymbolicAction,
)


@dataclass(frozen=True)
class PlannerConfig:
    timeout_seconds: float = 2.0
    search: str = "bfs"
    heuristic: str | None = None


def planner_error_result(state_hash: str, reason: str) -> PlanResult:
    """Helper to produce a typed error result."""
    return PlanResult(
        status=PlanStatus.PLANNER_ERROR,
        actions=(),
        planning_time_ms=0.0,
        state_hash=state_hash,
        problem_hash=None,
        reason=reason,
    )


def parse_symbolic_action(raw_action: str) -> SymbolicAction:
    """
    Parse a single raw pyperplan action string like
    '(move-forward robot north loc-1 loc-2)' into a typed SymbolicAction.
    """
    cleaned = raw_action.strip().strip("()")
    parts = cleaned.split()

    if not parts:
        raise ValueError(f"Cannot parse empty action string: '{raw_action}'")

    name = parts[0]
    arguments = tuple(parts[1:])

    return SymbolicAction(name=name, arguments=arguments)


def parse_symbolic_actions(raw_plan: list[str]) -> tuple[SymbolicAction, ...]:
    """Parse list of pyperplan action strings into a tuple of SymbolicAction."""
    return tuple(parse_symbolic_action(raw) for raw in raw_plan)


def _worker_search(
    domain_path: str,
    problem_path: str,
    search_name: str,
    heuristic_name: str | None,
    result_queue: mp.Queue[dict[str, Any]],
) -> None:
    """Worker process target: runs pyperplan.search_plan and puts result into queue."""
    try:
        if search_name not in SEARCHES:
            result_queue.put(
                {
                    "error": (
                        f"Unsupported search algorithm: {search_name}. "
                        f"Available: {list(SEARCHES.keys())}"
                    )
                }
            )
            return

        search_fn = SEARCHES[search_name]
        heuristic_cls = HEURISTICS.get(heuristic_name) if heuristic_name else None

        plan = search_plan(
            domain_file=domain_path,
            problem_file=problem_path,
            search=search_fn,
            heuristic_class=heuristic_cls,
        )

        if plan is None:
            # Planner proved or concluded no plan exists
            result_queue.put({"success": True, "raw_actions": None})
        else:
            # Extract operator names: each action.name is e.g. "(move-forward ...)"
            raw_actions = [action.name for action in plan]
            result_queue.put({"success": True, "raw_actions": raw_actions})

    except Exception as e:
        result_queue.put({"error": str(e)})


def plan_with_timeout(
    state: CommittedPlanningState,
    domain_path: str,
    problem_string: str,
    config: PlannerConfig | None = None,
) -> PlanResult:
    """
    Solves a planning problem using pyperplan inside an isolated worker process
    with bounded execution time.
    """
    cfg = config or PlannerConfig()
    problem_hash = hashlib.sha256(problem_string.encode("utf-8")).hexdigest()

    # 1. Write out PDDL PROBLEM into tempfile
    temp_fd, temp_problem_path = tempfile.mkstemp(suffix=".pddl", prefix="problem_")
    try:
        with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
            f.write(problem_string)

        # 2. Initialize Process and Queue
        ctx = mp.get_context("spawn")
        result_queue: mp.Queue[dict[str, Any]] = ctx.Queue()
        process = ctx.Process(
            target=_worker_search,
            args=(
                domain_path,
                temp_problem_path,
                cfg.search,
                cfg.heuristic,
                result_queue,
            ),
        )

        start_time = time.perf_counter()
        process.start()
        process.join(timeout=cfg.timeout_seconds)
        planning_time_ms = (time.perf_counter() - start_time) * 1000.0

        # 3. TIMEOUT Scenario: Process still alive after timeout_seconds
        if process.is_alive():
            process.terminate()
            process.join()
            return PlanResult(
                status=PlanStatus.TIMEOUT,
                actions=(),
                planning_time_ms=planning_time_ms,
                state_hash=state.state_hash,
                problem_hash=problem_hash,
                reason=f"Planner exceeded timeout of {cfg.timeout_seconds}s.",
            )

        # 4. Receive the result from Queue
        try:
            worker_output = result_queue.get_nowait()
        except queue.Empty:
            return PlanResult(
                status=PlanStatus.PLANNER_ERROR,
                actions=(),
                planning_time_ms=planning_time_ms,
                state_hash=state.state_hash,
                problem_hash=problem_hash,
                reason="Worker process terminated without returning output.",
            )

        if "error" in worker_output:
            return PlanResult(
                status=PlanStatus.PLANNER_ERROR,
                actions=(),
                planning_time_ms=planning_time_ms,
                state_hash=state.state_hash,
                problem_hash=problem_hash,
                reason=worker_output["error"],
            )

        raw_actions = worker_output.get("raw_actions")
        if raw_actions is None:
            return PlanResult(
                status=PlanStatus.NO_PLAN_KNOWN_SPACE,
                actions=(),
                planning_time_ms=planning_time_ms,
                state_hash=state.state_hash,
                problem_hash=problem_hash,
                reason="No valid plan found within known space.",
            )

        if len(raw_actions) == 0:
            return PlanResult(
                status=PlanStatus.ALREADY_SATISFIED,
                actions=(),
                planning_time_ms=planning_time_ms,
                state_hash=state.state_hash,
                problem_hash=problem_hash,
                reason="Initial state already satisfies the goal.",
            )

        # 5. Parse raw actions into SymbolicAction
        try:
            symbolic_actions = parse_symbolic_actions(raw_actions)
        except Exception as parse_err:
            return PlanResult(
                status=PlanStatus.PLANNER_ERROR,
                actions=(),
                planning_time_ms=planning_time_ms,
                state_hash=state.state_hash,
                problem_hash=problem_hash,
                reason=f"Failed to parse symbolic actions: {parse_err}.",
            )

        return PlanResult(
            status=PlanStatus.FOUND,
            actions=symbolic_actions,
            planning_time_ms=planning_time_ms,
            state_hash=state.state_hash,
            problem_hash=problem_hash,
            reason=None,
        )

    finally:
        if os.path.exists(temp_problem_path):
            try:
                os.unlink(temp_problem_path)
            except OSError:
                pass
