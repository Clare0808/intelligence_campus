import os
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from flask import Flask

from api.campus_account import configure_accounts
from api.campus_assistant import assistant_bp
from api.campus_assistant_log import configure_assistant_log
from api.campus_users import configure_users


class CampusAssistantLogTests(unittest.TestCase):
    origin = "http://127.0.0.1:5173"
    chat_url = "/api/campus/assistant/chat"
    log_url = "/api/campus/admin/assistant/questions"

    def setUp(self):
        folder = self.enterContext(tempfile.TemporaryDirectory())
        self.db_path = Path(folder) / "assistant.sqlite3"
        app = Flask(__name__)
        configure_accounts(app)
        configure_users(app)
        configure_assistant_log(app)
        app.register_blueprint(assistant_bp)
        app.config.update(
            TESTING=True, CAMPUS_PREVIEW=True, CAMPUS_ORIGIN=self.origin,
            CAMPUS_USERS_DB=str(Path(folder) / "users.sqlite3"),
            CAMPUS_ASSISTANT_DB=str(self.db_path),
        )
        self.app = app
        self.guest = app.test_client()
        self.user = app.test_client()
        self.admin = app.test_client()

    def headers(self, client):
        csrf = client.get("/api/campus/session").json["csrf"]
        return {"Origin": self.origin, "X-Campus-CSRF": csrf}

    def login(self, client, role):
        headers = self.headers(client)
        response = client.post(
            "/api/campus/session/preview", json={"role": role}, headers=headers
        )
        self.assertEqual(response.status_code, 200)
        return {**headers, "X-Campus-CSRF": response.json["csrf"]}

    def test_records_valid_questions_and_restricts_admin_read(self):
        guest_headers = self.headers(self.guest)
        user_headers = self.login(self.user, "reporter")
        self.login(self.admin, "reviewer")
        self.assertEqual(self.guest.get(self.log_url).status_code, 401)
        self.assertEqual(self.user.get(self.log_url).status_code, 403)
        self.assertEqual(self.admin.get(self.log_url + "?before=bad").status_code, 400)
        self.assertEqual(self.admin.get(self.log_url).json["questions"], [])

        with patch.dict(os.environ, {
            "AZURE_OPENAI_ENDPOINT": "https://example.com/v1/",
            "AZURE_OPENAI_API_KEY": "secret-key", "AZURE_OPENAI_DEPLOYMENT": "test-model",
        }), patch("api.campus_assistant.campus_context", return_value="{}"), patch(
            "api.campus_assistant.ask_model", return_value="回答"
        ):
            self.assertEqual(self.guest.post(self.chat_url, json={"question": "invalid"}).status_code, 403)
            self.assertEqual(self.guest.post(self.chat_url, headers=guest_headers,
                                             json={"question": "  "}).status_code, 400)
            self.assertEqual(self.guest.post(self.chat_url, headers=guest_headers,
                                             json={"question": "  訪客問題？  "}).status_code, 200)
            self.assertEqual(self.user.post(self.chat_url, headers=user_headers,
                                            json={"question": "登入問題？"}).status_code, 200)

        response = self.admin.get(self.log_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        self.assertIsNone(response.json["next_before"])
        rows = response.json["questions"]
        self.assertEqual([row["question"] for row in rows], ["登入問題？", "訪客問題？"])
        self.assertEqual([row["account"] for row in rows], ["preview:reporter", None])
        self.assertTrue(rows[0]["created_at"].endswith("+00:00"))
        self.assertEqual(self.admin.get(self.log_url + f"?before={rows[0]['id']}").json["questions"], [rows[1]])
        with closing(sqlite3.connect(self.db_path)) as db:
            self.assertEqual(db.execute("SELECT count(*) FROM assistant_questions").fetchone()[0], 2)

    def test_model_failure_still_records_once_and_db_failure_prevents_model_call(self):
        headers = self.headers(self.guest)
        with patch.dict(os.environ, {
            "AZURE_OPENAI_ENDPOINT": "https://example.com/v1/",
            "AZURE_OPENAI_API_KEY": "secret-key", "AZURE_OPENAI_DEPLOYMENT": "test-model",
        }), patch("api.campus_assistant.campus_context", return_value="{}"), patch(
            "api.campus_assistant.ask_model", side_effect=RuntimeError("model failed")
        ):
            with patch.object(self.app.logger, "exception"):
                self.assertEqual(self.guest.post(self.chat_url, headers=headers,
                                                 json={"question": "失敗問題"}).status_code, 502)
        with closing(sqlite3.connect(self.db_path)) as db:
            self.assertEqual(db.execute("SELECT question FROM assistant_questions").fetchone()[0], "失敗問題")

        with patch("api.campus_assistant.record_question", side_effect=sqlite3.OperationalError("private path")), patch(
            "api.campus_assistant.ask_model"
        ) as model:
            response = self.guest.post(self.chat_url, headers=headers, json={"question": "未記錄"})
            self.assertEqual(response.status_code, 503)
            self.assertNotIn("private path", response.get_data(as_text=True))
            model.assert_not_called()

    def test_logged_in_identity_uses_existing_session_account(self):
        headers = self.headers(self.user)
        with self.user.session_transaction() as session:
            session["campus_account"] = {"provider": "google", "subject": "member-1", "name": "使用者"}
        with patch("api.campus_assistant.ask_model", return_value="回答"), patch(
            "api.campus_assistant.campus_context", return_value="{}"
        ), patch.dict(os.environ, {
            "AZURE_OPENAI_ENDPOINT": "https://example.com/v1/",
            "AZURE_OPENAI_API_KEY": "secret-key", "AZURE_OPENAI_DEPLOYMENT": "test-model",
        }):
            self.assertEqual(self.user.post(self.chat_url, headers=headers, json={"question": "問題"}).status_code, 200)
        with closing(sqlite3.connect(self.db_path)) as db:
            self.assertEqual(db.execute("SELECT account FROM assistant_questions").fetchone()[0], "google:member-1")

    def test_paginates_without_repeating_rows(self):
        self.login(self.admin, "reviewer")
        from api.campus_assistant_log import assistant_database

        with self.app.app_context(), assistant_database() as db:
            db.executemany(
                "INSERT INTO assistant_questions (question, account, created_at) VALUES (?, NULL, ?)",
                [(str(i), "2026-11-22T00:00:00+00:00") for i in range(51)],
            )
        first = self.admin.get(self.log_url).json
        self.assertEqual(len(first["questions"]), 50)
        second = self.admin.get(self.log_url + f"?before={first['next_before']}").json
        self.assertEqual(len(second["questions"]), 1)
        self.assertIsNone(second["next_before"])
        self.assertLess(second["questions"][0]["id"], first["questions"][-1]["id"])


if __name__ == "__main__":
    unittest.main()