from __future__ import annotations

import argparse
from dataclasses import dataclass
import time

from sqlmodel import Session

from app.core.config import Settings, get_settings
from app.core.db import engine
from worker.coordination import build_worker_coordinator
from worker.runtime import run_worker_cycle


@dataclass
class WorkerServiceIterationResult:
    executed: bool
    coordination_backend: str
    skip_reason: str | None
    summary: object | None


def run_worker_service_once(
    *,
    settings: Settings | None = None,
    coordinator=None,
    session_factory=None,
    limit: int | None = None,
    stale_follow_up_days: int | None = None,
) -> WorkerServiceIterationResult:
    runtime_settings = settings or get_settings()
    runtime_coordinator = coordinator or build_worker_coordinator(runtime_settings)
    runtime_session_factory = session_factory or (lambda: Session(engine))

    with runtime_coordinator.execution_lease() as lease:
        if not lease.acquired:
            return WorkerServiceIterationResult(
                executed=False,
                coordination_backend=lease.backend,
                skip_reason="worker lease is currently held by another worker instance",
                summary=None,
            )
        with runtime_session_factory() as session:
            summary = run_worker_cycle(
                session=session,
                settings=runtime_settings,
                limit=limit or runtime_settings.worker_default_limit,
                stale_follow_up_days=stale_follow_up_days
                or runtime_settings.worker_stale_follow_up_days,
            )
        return WorkerServiceIterationResult(
            executed=True,
            coordination_backend=lease.backend,
            skip_reason=None,
            summary=summary,
        )


def run_worker_service(
    *,
    settings: Settings | None = None,
    coordinator=None,
    session_factory=None,
    mode: str | None = None,
    max_cycles: int | None = None,
    sleep_seconds: int | None = None,
    limit: int | None = None,
    stale_follow_up_days: int | None = None,
) -> list[WorkerServiceIterationResult]:
    runtime_settings = settings or get_settings()
    execution_mode = mode or runtime_settings.worker_run_mode
    results: list[WorkerServiceIterationResult] = []
    cycle_count = 0

    while True:
        result = run_worker_service_once(
            settings=runtime_settings,
            coordinator=coordinator,
            session_factory=session_factory,
            limit=limit,
            stale_follow_up_days=stale_follow_up_days,
        )
        results.append(result)
        cycle_count += 1
        if execution_mode == "once":
            break
        if max_cycles is not None and cycle_count >= max_cycles:
            break
        time.sleep(
            sleep_seconds
            if sleep_seconds is not None
            else (
                runtime_settings.worker_poll_interval_seconds
                if result.executed
                else runtime_settings.worker_locked_poll_interval_seconds
            )
        )

    return results


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Trust Ledger worker service.")
    parser.add_argument(
        "--mode",
        choices=["once", "loop"],
        default=None,
        help="Override the configured worker run mode.",
    )
    parser.add_argument(
        "--cycles",
        type=int,
        default=None,
        help="Maximum number of cycles to execute in loop mode.",
    )
    parser.add_argument(
        "--sleep-seconds",
        type=int,
        default=None,
        help="Override the pause between loop cycles.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Override the maximum number of queued items claimed per cycle.",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    results = run_worker_service(
        mode=args.mode,
        max_cycles=args.cycles,
        sleep_seconds=args.sleep_seconds,
        limit=args.limit,
    )
    latest_result = results[-1]
    if not latest_result.executed:
        print(
            "Worker cycle skipped: "
            f"coordination_backend={latest_result.coordination_backend}, "
            f"reason={latest_result.skip_reason}"
        )
        return
    summary = latest_result.summary
    print(
        "Worker cycle complete: "
        f"coordination_backend={latest_result.coordination_backend}, "
        f"worker_run_id={summary.worker_run_id}, "
        f"claimed_automation_tasks={summary.claimed_automation_task_count}, "
        f"sent_notifications={summary.sent_notification_count}, "
        f"processed_score_requests={summary.processed_score_request_count}, "
        f"failed_automation_tasks={summary.failed_automation_task_count}, "
        f"failed_notifications={summary.failed_notification_count}, "
        f"failed_score_requests={summary.failed_score_request_count}"
    )


if __name__ == "__main__":
    main()
