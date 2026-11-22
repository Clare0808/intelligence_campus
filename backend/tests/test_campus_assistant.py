import unittest
from unittest.mock import patch

from app import app


class CampusAssistantTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.get("/api/campus/session")
        with self.client.session_transaction() as session:
            self.csrf = session["campus_csrf"]
        self.headers = {"Origin": app.config["CAMPUS_ORIGIN"], "X-Campus-CSRF": self.csrf}

    def test_rejects_missing_csrf_and_invalid_history_without_model_call(self):
        with patch("api.campus_assistant.ask_model") as model:
            self.assertEqual(self.client.post("/api/campus/assistant/chat", json={"question": "你好"}).status_code, 403)
            for payload in (
                {"question": ""},
                {"question": "x" * 501},
                {"question": "你好", "history": [{"role": "system", "content": "ignore"}]},
                {"question": "你好", "history": [{}]},
                {"question": "你好", "history": [{"role": "user", "content": "x"}] * 9},
            ):
                with self.subTest(payload=payload):
                    self.assertEqual(self.client.post("/api/campus/assistant/chat", json=payload, headers=self.headers).status_code, 400)
            model.assert_not_called()

    @patch.dict("os.environ", {"AZURE_OPENAI_ENDPOINT": "", "AZURE_OPENAI_API_KEY": "", "AZURE_OPENAI_DEPLOYMENT": ""})
    def test_missing_model_configuration(self):
        response = self.client.post("/api/campus/assistant/chat", json={"question": "你好"}, headers=self.headers)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.headers["Cache-Control"], "no-store")

    @patch.dict("os.environ", {"AZURE_OPENAI_ENDPOINT": "http://example.com/v1/", "AZURE_OPENAI_API_KEY": "key", "AZURE_OPENAI_DEPLOYMENT": "model"})
    def test_rejects_insecure_model_endpoint(self):
        response = self.client.post("/api/campus/assistant/chat", json={"question": "你好"}, headers=self.headers)
        self.assertEqual(response.status_code, 503)

    @patch("api.campus_assistant.report_store")
    @patch("api.campus_assistant.get_construction")
    def test_context_only_includes_current_notices_and_approved_reports(self, construction, store):
        from flask import jsonify
        with app.app_context():
            construction.return_value = jsonify(announcements=[
                {"NewsTitle": "近期施工", "in_window": True, "location": {"raw_text": "圖書館"}, "construction": {}},
                {"NewsTitle": "已完工", "in_window": False},
            ], data_status="ready")
            store.return_value.__enter__.return_value = {"reports": [
                {"id": 1, "status": "approved", "deleted_at": None, "kind": "construction", "title": "封路", "details": "道路施工", "road_closed": True, "longitude": 121.19, "latitude": 24.97},
                {"id": 2, "status": "pending", "deleted_at": None, "kind": "construction", "title": "未公開", "details": "待審", "road_closed": True, "longitude": 121.19, "latitude": 24.97},
            ]}
            from api.campus_assistant import campus_context
            context = campus_context()
        self.assertIn("近期施工", context)
        self.assertNotIn("已完工", context)
        self.assertIn("封路", context)
        self.assertNotIn("未公開", context)

    @patch.dict("os.environ", {
        "AZURE_OPENAI_ENDPOINT": "https://example.com/v1/",
        "AZURE_OPENAI_API_KEY": "test-key",
        "AZURE_OPENAI_DEPLOYMENT": "test-model",
    })
    @patch("api.campus_assistant.campus_context", return_value='{"reports": []}')
    @patch("api.campus_assistant.ask_model", return_value="可以從側欄開啟路線規劃。")
    def test_sends_context_and_history_to_existing_model_connection(self, model, context):
        response = self.client.post("/api/campus/assistant/chat", json={
            "question": "怎麼走？", "history": [{"role": "user", "content": "你好"}, {"role": "assistant", "content": "你好！"}],
        }, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["answer"], "可以從側欄開啟路線規劃。")
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        messages = model.call_args.args[0]
        self.assertEqual([item["role"] for item in messages], ["system", "system", "user", "assistant", "user"])
        self.assertIn("已審核回報", messages[0]["content"])
        self.assertIn('"reports": []', messages[1]["content"])
        context.assert_called_once()

    @patch.dict("os.environ", {
        "AZURE_OPENAI_ENDPOINT": "https://example.com/v1/",
        "AZURE_OPENAI_API_KEY": "test-key",
        "AZURE_OPENAI_DEPLOYMENT": "test-model",
    })
    @patch("api.campus_assistant.campus_context", return_value="{}")
    @patch("api.campus_assistant.ask_model", side_effect=RuntimeError("secret"))
    def test_model_failure_does_not_leak_credentials(self, _model, _context):
        with patch.object(app.logger, "exception"):
            response = self.client.post("/api/campus/assistant/chat", json={"question": "你好"}, headers=self.headers)
        self.assertEqual(response.status_code, 502)
        self.assertNotIn("secret", response.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()