import json
import unittest
from unittest.mock import MagicMock, patch

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from app.ai.agent import (
    agent_reason_node,
    build_support_graph,
    execute_tools_node,
    route_after_agent_reason,
    route_after_classify,
    support_graph,
)
from app.ai.schemas import SupportState


class TestAgenticGraph(unittest.TestCase):
    def test_route_after_classify_agentic(self):
        state_normal: SupportState = {
            "thread_text": "Hi, where is my order NX-1001?",
            "needs_human": False,
            "has_attachments": False,
        }
        self.assertEqual(route_after_classify(state_normal), "agent_reason")

        state_escalate: SupportState = {
            "thread_text": "Help, my battery is smoking!",
            "needs_human": True,
            "has_attachments": False,
        }
        self.assertEqual(route_after_classify(state_escalate), "escalate")

    def test_route_after_agent_reason_with_tool_calls(self):
        ai_msg = AIMessage(
            content="",
            tool_calls=[{"name": "tool_lookup_order", "args": {"order_id": "NX-1001"}, "id": "call_1"}],
        )
        state: SupportState = {
            "messages": [ai_msg],
            "tool_call_count": 0,
        }
        self.assertEqual(route_after_agent_reason(state), "execute_tools")

    def test_route_after_agent_reason_without_tool_calls(self):
        ai_msg = AIMessage(content="Your order NX-1001 was delivered on Nov 10 via FedEx.")
        state: SupportState = {
            "messages": [ai_msg],
            "tool_call_count": 1,
        }
        self.assertEqual(route_after_agent_reason(state), "validate_reply")

    def test_route_after_agent_reason_hits_max_iterations(self):
        ai_msg = AIMessage(
            content="",
            tool_calls=[{"name": "tool_lookup_order", "args": {"order_id": "NX-1001"}, "id": "call_4"}],
        )
        state: SupportState = {
            "messages": [ai_msg],
            "tool_call_count": 4,  # Max cap reached
        }
        self.assertEqual(route_after_agent_reason(state), "validate_reply")

    def test_execute_tools_node_executes_tool_and_updates_state(self):
        ai_msg = AIMessage(
            content="",
            tool_calls=[{"name": "tool_lookup_order", "args": {"order_id": "NX-1001"}, "id": "call_123"}],
        )
        state: SupportState = {
            "messages": [ai_msg],
            "tool_call_count": 0,
            "executed_tools": [],
        }

        res = execute_tools_node(state)
        self.assertEqual(res["tool_call_count"], 1)
        self.assertEqual(len(res["messages"]), 1)
        self.assertIsInstance(res["messages"][0], ToolMessage)
        self.assertEqual(res["messages"][0].tool_call_id, "call_123")

        parsed_output = json.loads(res["messages"][0].content)
        self.assertEqual(parsed_output["order_id"], "NX-1001")
        self.assertEqual(res["order_id"], "NX-1001")
        self.assertEqual(len(res["executed_tools"]), 1)
        self.assertEqual(res["executed_tools"][0]["tool"], "tool_lookup_order")

    def test_graph_structure_has_agentic_nodes(self):
        graph = build_support_graph()
        node_keys = graph.nodes.keys()
        self.assertIn("classify", node_keys)
        self.assertIn("agent_reason", node_keys)
        self.assertIn("execute_tools", node_keys)
        self.assertIn("validate_reply", node_keys)
        self.assertIn("apply_rules", node_keys)
        self.assertIn("send_reply", node_keys)
        self.assertIn("escalate", node_keys)


if __name__ == "__main__":
    unittest.main()

