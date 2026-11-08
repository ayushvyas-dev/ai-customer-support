import sys
from pathlib import Path

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR))

from app import db
from app.vectorstore import reindex_all



def parse(path: Path) -> list[tuple[str, str, str]]:
    """Split a section file into (section, title, content) rows, one per ## heading."""
    entries = []
    for block in path.read_text(encoding="utf-8").split("\n## ")[1:]:
        title, _, content = block.partition("\n")
        entries.append((path.stem, title.strip(), content.strip()))
    return entries


print("Seeding knowledge base SQL rows...")
with db.connect() as conn:
    for path in sorted((BASE_DIR / "knowledge_base").glob("*.md")):
        rows = parse(path)
        for section, title, content in rows:
            conn.execute(
                """
                insert into knowledge_base (section, title, content) values (%s, %s, %s)
                on conflict (section, title) do update
                  set content = excluded.content, updated_at = now()
                """,
                (section, title, content),
            )
        print(f"{path.stem}: {len(rows)} entries")

print("\nGenerating and updating vector embeddings in Supabase pgvector...")
chunks = reindex_all()
print(f"Knowledge base successfully seeded and vectorized ({chunks} embedding chunks).")
