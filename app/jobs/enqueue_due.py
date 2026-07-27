from __future__ import annotations

from app.db import SessionLocal
from app.services.jobs import enqueue_due_jobs


def main() -> None:
    with SessionLocal() as session:
        count = enqueue_due_jobs(session)
    print(f"enqueued={count}")


if __name__ == "__main__":
    main()
