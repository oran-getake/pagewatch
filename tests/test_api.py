from __future__ import annotations

import os
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

TEST_DB = Path(tempfile.gettempdir()) / f"pagewatch-api-test-{os.getpid()}.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB}"

from fastapi.testclient import TestClient

from app.db import Base, SessionLocal, engine
from app.main import app
from app.models import Change, CheckJob, Snapshot, WatchTarget
from app.services.checker import check_watch
from app.services.fetcher import FetchResponse
from app.services.jobs import recover_stale_jobs


class APITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        Base.metadata.create_all(bind=engine)
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls) -> None:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
        TEST_DB.unlink(missing_ok=True)

    def setUp(self) -> None:
        response = self.client.post("/api/devices/anonymous")
        self.assertEqual(response.status_code, 201)
        token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {token}"}

    def test_requires_authentication(self) -> None:
        response = self.client.get("/api/watches")
        self.assertEqual(response.status_code, 401)

    def test_register_list_duplicate_pause_resume_and_delete(self) -> None:
        payload = {
            "title": "求人情報",
            "url": "https://example.com/jobs",
            "category": "job",
            "frequency": "daily",
        }
        resolved = SimpleNamespace(normalized_url=payload["url"])
        with patch("app.main.resolve_public_target", return_value=resolved):
            created = self.client.post(
                "/api/watches", json=payload, headers=self.headers
            )
            duplicate = self.client.post(
                "/api/watches", json=payload, headers=self.headers
            )

        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.json()["last_check_status"], "pending")
        self.assertEqual(duplicate.status_code, 409)
        watch_id = created.json()["id"]

        listed = self.client.get("/api/watches", headers=self.headers)
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(len(listed.json()), 1)

        paused = self.client.patch(
            f"/api/watches/{watch_id}",
            json={"is_active": False},
            headers=self.headers,
        )
        self.assertEqual(paused.status_code, 200)
        self.assertEqual(paused.json()["last_check_status"], "paused")

        resumed = self.client.patch(
            f"/api/watches/{watch_id}",
            json={"is_active": True},
            headers=self.headers,
        )
        self.assertEqual(resumed.status_code, 200)
        self.assertEqual(resumed.json()["last_check_status"], "pending")

        deleted = self.client.delete(f"/api/watches/{watch_id}", headers=self.headers)
        self.assertEqual(deleted.status_code, 204)
        self.assertEqual(
            self.client.get("/api/watches", headers=self.headers).json(), []
        )

    def test_other_device_cannot_read_watch(self) -> None:
        payload = {
            "title": "商品",
            "url": "https://example.com/item",
            "category": "product",
            "frequency": "daily",
        }
        with patch(
            "app.main.resolve_public_target",
            return_value=SimpleNamespace(normalized_url=payload["url"]),
        ):
            created = self.client.post(
                "/api/watches", json=payload, headers=self.headers
            )
        watch_id = created.json()["id"]

        other_token = self.client.post("/api/devices/anonymous").json()["access_token"]
        other_headers = {"Authorization": f"Bearer {other_token}"}
        response = self.client.get(f"/api/watches/{watch_id}", headers=other_headers)
        self.assertEqual(response.status_code, 404)

        self.client.delete(f"/api/watches/{watch_id}", headers=self.headers)

    def test_checker_stores_only_initial_and_changed_snapshots(self) -> None:
        payload = {
            "title": "在庫",
            "url": "https://example.com/stock",
            "category": "product",
            "frequency": "daily",
        }
        with patch(
            "app.main.resolve_public_target",
            return_value=SimpleNamespace(normalized_url=payload["url"]),
        ):
            created = self.client.post(
                "/api/watches", json=payload, headers=self.headers
            )
        watch_id = created.json()["id"]

        first = FetchResponse(
            final_url=payload["url"],
            status_code=200,
            content_type="text/html; charset=utf-8",
            body="<main><h1>商品</h1><p>価格 1,000円</p><p>在庫なし</p></main>",
        )
        changed = FetchResponse(
            final_url=payload["url"],
            status_code=200,
            content_type="text/html; charset=utf-8",
            body="<main><h1>商品</h1><p>価格 900円</p><p>在庫あり</p></main>",
        )

        with SessionLocal() as session:
            watch = session.get(WatchTarget, watch_id)
            with (
                patch("app.services.checker.is_allowed", return_value=True),
                patch(
                    "app.services.checker.safe_fetch",
                    side_effect=[first, first, changed],
                ),
            ):
                self.assertEqual(check_watch(session, watch, "initial"), "unchanged")
                session.commit()
                self.assertEqual(check_watch(session, watch, "manual"), "unchanged")
                session.commit()
                self.assertEqual(check_watch(session, watch, "manual"), "changed")
                session.commit()

            snapshots = (
                session.query(Snapshot).filter_by(watch_target_id=watch_id).count()
            )
            changes = session.query(Change).filter_by(watch_target_id=watch_id).all()
            self.assertEqual(snapshots, 2)
            self.assertEqual(len(changes), 1)
            self.assertIn("価格 900円", changes[0].added_text)
            self.assertIn("価格 1,000円", changes[0].removed_text)

        self.client.delete(f"/api/watches/{watch_id}", headers=self.headers)

    def test_recovers_stale_running_job(self) -> None:
        payload = {
            "title": "お知らせ",
            "url": "https://example.com/news",
            "category": "notice",
            "frequency": "daily",
        }
        with patch(
            "app.main.resolve_public_target",
            return_value=SimpleNamespace(normalized_url=payload["url"]),
        ):
            created = self.client.post(
                "/api/watches", json=payload, headers=self.headers
            )
        watch_id = created.json()["id"]

        with SessionLocal() as session:
            job = session.query(CheckJob).filter_by(watch_target_id=watch_id).one()
            job.status = "running"
            job.attempts = 1
            job.started_at = datetime.now(UTC) - timedelta(hours=1)
            session.commit()

            self.assertEqual(recover_stale_jobs(session), 1)
            session.refresh(job)
            self.assertEqual(job.status, "queued")
            self.assertIsNone(job.started_at)

        self.client.delete(f"/api/watches/{watch_id}", headers=self.headers)

    def test_delete_account_invalidates_token_and_cascades(self) -> None:
        response = self.client.delete("/api/account", headers=self.headers)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(
            self.client.get("/api/watches", headers=self.headers).status_code,
            401,
        )


if __name__ == "__main__":
    unittest.main()
