from __future__ import annotations

import signal
import time

from app.config import settings
from app.db import SessionLocal
from app.services.jobs import claim_next_job, process_job, recover_stale_jobs

running = True


def _stop(_signum: int, _frame: object) -> None:
    global running
    running = False


def main() -> None:
    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)
    print("PageWatch worker started", flush=True)

    with SessionLocal() as session:
        recovered = recover_stale_jobs(session)
        if recovered:
            print(f"recovered_stale_jobs={recovered}", flush=True)

    while running:
        with SessionLocal() as session:
            job = claim_next_job(session)
            if job is not None:
                process_job(session, job)
                continue
        time.sleep(settings.worker_poll_seconds)

    print("PageWatch worker stopped", flush=True)


if __name__ == "__main__":
    main()
