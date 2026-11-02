import sys
from pathlib import Path

import nest_asyncio

sys.path.append(str(Path(__file__).resolve().parents[1]))

nest_asyncio.apply()
from app.ai.decide import decide

question = "My Nexa One phone is charging very slowly with the original cable. Order 112-4839201-5528341"
decision = decide(question)
print(decision.model_dump_json(indent=2))