import json
import unittest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage

from app.ai.agent import execute_tools_node
from app.main import app, create_token
from app.pipeline import resume_approval_flow


class TestHITLApproval(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.token = create_token("supervisor_user")
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_list_pending_approvals_endpoint(self):
        with patch("app.db.get_pending_approvals", return_value=[]):
            res = self.client.get("/api/approvals/pending", headers=self.headers)
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.json(), [])

    def test_approve_endpoint(self):
        with patch("app.db.resolve_approval", return_value=True):
            res = self.client.post(
                "/api/approvals/appr-test-123/approve",
                json={"reviewer": "supervisor_admin", "notes": "Approved courtesy credit"},
                headers=self.headers,
            )
            self.assertEqual(res.status_code, 200)
            body = res.json()
            self.assertEqual(body["status"], "approved")
            self.assertEqual(body["approval_id"], "appr-test-123")

    def test_reject_endpoint(self):
        with patch("app.db.resolve_approval", return_value=True):
            res = self.client.post(
                "/api/approvals/appr-test-456/reject",
                json={"reviewer": "supervisor_admin", "notes": "Customer outside warranty period"},
                headers=self.headers,
            )
            self.assertEqual(res.status_code, 200)
            body = res.json()
            self.assertEqual(body["status"], "rejected")
            self.assertEqual(body["approval_id"], "appr-test-456")

    def test_tier2_refund_triggers_interrupt_in_tool_execution(self):
        ai_msg = AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "tool_request_refund",
                    "args": {"order_id": "NX-1001", "amount_usd": 50.0, "reason": "Customer complaint"},
                    "id": "refund_call_1",
                }
            ],
        )
        state = {
            "messages": [ai_msg],
            "thread_id": "thread-refund-test",
            "executed_tools": [],
        }

        # Patch interrupt to simulate supervisor approving
        with patch(
            "app.ai.agent.interrupt",
            return_value={"approved": True, "notes": "Approved by supervisor"},
        ):
            res = execute_tools_node(state)
            self.assertEqual(len(res["messages"]), 1)
            parsed = json.loads(res["messages"][0].content)
            self.assertEqual(parsed["status"], "processed")
            self.assertEqual(parsed["amount_usd"], 50.0)

    def test_tier2_refund_rejected_by_supervisor_stops_execution(self):
        ai_msg = AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "tool_request_refund",
                    "args": {"order_id": "NX-1001", "amount_usd": 50.0, "reason": "Customer complaint"},
                    "id": "refund_call_2",
                }
            ],
        )
        state = {
            "messages": [ai_msg],
            "thread_id": "thread-refund-test-2",
            "executed_tools": [],
        }

        # Patch interrupt to simulate supervisor rejecting
        with patch(
            "app.ai.agent.interrupt",
            return_value={"approved": False, "notes": "Policy violation"},
        ):
            res = execute_tools_node(state)
            self.assertEqual(len(res["messages"]), 1)
            parsed = json.loads(res["messages"][0].content)
            self.assertTrue(parsed.get("error"))
            self.assertIn("Action declined by supervisor", parsed.get("message"))


if __name__ == "__main__":
    unittest.main()

