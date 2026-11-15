import json
import unittest
from unittest.mock import MagicMock, patch

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

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

    def test_agent_reason_node_preserves_conversation_turn_history(self):
        """Turn 1 must build system and user message and return them with assistant tool call."""
        mock_tool_ai_msg = AIMessage(
            content="",
            tool_calls=[{"name": "tool_lookup_order", "args": {"order_id": "NX-1001"}, "id": "call_1"}],
        )
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = mock_tool_ai_msg

        state: SupportState = {
            "thread_text": "Hi, can you tell me the tracking status for my order NX-1001?",
            "section": "shipping",
            "messages": [],
            "tool_call_count": 0,
        }

        with patch("app.ai.agent.get_agent_model_with_tools", return_value=mock_llm):
            res_turn1 = agent_reason_node(state)

        # Must return initial prompt + AI message to preserve history for Gemini API
        self.assertEqual(len(res_turn1["messages"]), 3)
        self.assertIn("Nexa Mobile", res_turn1["messages"][0].content)
        self.assertIn("NX-1001", res_turn1["messages"][1].content)
        self.assertEqual(res_turn1["messages"][2], mock_tool_ai_msg)

        # Now simulate LangGraph message accumulation:
        tool_msg = ToolMessage(
            content='{"order_id": "NX-1001", "status": "delivered"}',
            tool_call_id="call_1",
            name="tool_lookup_order",
        )
        accumulated_messages = list(res_turn1["messages"]) + [tool_msg]

        # Turn 2: Agent reasoner receives accumulated history
        mock_final_ai_msg = AIMessage(content="Your order NX-1001 was delivered via FedEx.")
        mock_llm.invoke.return_value = mock_final_ai_msg

        state_turn2: SupportState = {
            "thread_text": "Hi, can you tell me the tracking status for my order NX-1001?",
            "section": "shipping",
            "messages": accumulated_messages,
            "tool_call_count": 1,
        }

        with patch("app.ai.agent.get_agent_model_with_tools", return_value=mock_llm):
            res_turn2 = agent_reason_node(state_turn2)

        # Model must be invoked with full 4-turn history: System -> User -> Assistant (tool call) -> Tool (result)
        invoked_msgs = mock_llm.invoke.call_args[0][0]
        self.assertEqual(len(invoked_msgs), 4)
        self.assertIsInstance(invoked_msgs[0], SystemMessage)
        self.assertIsInstance(invoked_msgs[1], HumanMessage)
        self.assertEqual(invoked_msgs[2], mock_tool_ai_msg)
        self.assertEqual(invoked_msgs[3], tool_msg)

        # Result of Turn 2 returns the finalized assistant response
        self.assertEqual(len(res_turn2["messages"]), 1)
        self.assertEqual(res_turn2["messages"][0], mock_final_ai_msg)
        self.assertEqual(res_turn2["reply"], "Your order NX-1001 was delivered via FedEx.")

    def test_classify_falls_back_to_heuristic_on_network_failure(self):
        from app.ai.classifier import classify

        with patch("app.ai.classifier.ChatGroq.invoke", side_effect=Exception("Connection error")), \
             patch("app.ai.classifier.ChatGoogleGenerativeAI.invoke", side_effect=Exception("DNS resolution failed")):
            res = classify("Hi, can you tell me the tracking status for my order NX-1001?")

        self.assertEqual(res.section, "shipping")
        self.assertFalse(res.needs_human)
        self.assertIn("shipping", res.reason)

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

