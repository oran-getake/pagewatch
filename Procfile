web: sh -c "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"
worker: python -m app.worker
cron: python -m app.jobs.enqueue_due

