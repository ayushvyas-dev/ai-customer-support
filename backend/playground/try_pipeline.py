import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.ai.decide import decide

# Test 1: Order lookup & tracking
email_thread = "Hi, can you tell me the tracking status for my order NX-1001?"

# Test 2: Accessory warranty replacement (Tier 1 autonomous)
# email_thread = "Hi, my USB cable for order NX-1002 broke. Can you send a replacement?"

# Test 3: High-value refund request (Tier 2 HITL approval)
# email_thread = "I demand an immediate $899 refund for order NX-1001!"

decision = decide(email_thread)
print(decision.model_dump_json(indent=2))
