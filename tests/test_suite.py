import unittest
import json
from app import app
from db.session import get_db
from db.models import OptimizationRun, Finding

class TestDevOpsAutopilot(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True

    def test_01_health(self):
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("guardrails", data)

    def test_02_get_savings(self):
        res = self.client.get("/api/savings")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("total_estimated_savings_inr_month", data)
        self.assertIn("total_actions_count", data)

    def test_03_get_waste_map(self):
        res = self.client.get("/api/waste-map")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIsInstance(data, list)

    def test_04_get_runs(self):
        res = self.client.get("/api/runs")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIsInstance(data, list)

    def test_05_optimize_dry_run(self):
        res = self.client.post("/api/optimize", json={"mode": "dry_run", "scope": "all"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["mode"], "dry_run")
        self.assertIn("run_id", data)
        self.assertIn("savings_inr_month", data)

    def test_06_optimize_live_run(self):
        res = self.client.post("/api/optimize", json={"mode": "live", "scope": "staging"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["mode"], "live")

    def test_07_slack_commands(self):
        # /autopilot status
        res1 = self.client.post("/slack/commands", data={"text": "status"})
        self.assertEqual(res1.status_code, 200)

        # /autopilot explain
        res2 = self.client.post("/slack/commands", data={"text": "explain"})
        self.assertEqual(res2.status_code, 200)

        # /autopilot help
        res3 = self.client.post("/slack/commands", data={"text": "help"})
        self.assertEqual(res3.status_code, 200)

    def test_08_web_dashboard(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.data.decode("utf-8")
        self.assertIn("DevOps Autopilot", html)
        self.assertNotIn("Report (PDF)", html)
        self.assertNotIn("Pitch Deck (PPT)", html)

    def test_09_download_pdf(self):
        res = self.client.get("/report/pdf")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.content_type, "application/pdf")

    def test_10_download_ppt(self):
        res = self.client.get("/report/ppt")
        self.assertEqual(res.status_code, 200)
        self.assertIn("presentationml", res.content_type)

if __name__ == "__main__":
    unittest.main()
