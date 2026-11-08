import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.ai.decide import decide

question = "My Nexa One phone is charging very slowly with the original cable. Order 112-4839201-5528341"
decision = decide(question)
print(decision.model_dump_json(indent=2))
