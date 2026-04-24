import json
import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE documents (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    topic TEXT NOT NULL,
    body TEXT NOT NULL,
    created_at TEXT NOT NULL
)
"""


def seed(db_path: Path, fixture_path: Path) -> None:
    if db_path.exists():
        db_path.unlink()

    with sqlite3.connect(db_path) as conn:
        conn.execute(SCHEMA)
        docs = json.loads(fixture_path.read_text())
        conn.executemany(
            "INSERT INTO documents (id, title, topic, body, created_at) VALUES (?, ?, ?, ?, ?)",
            [(d["id"], d["title"], d["topic"], d["body"], d["created_at"]) for d in docs],
        )


if __name__ == "__main__":
    seed(Path("research.db"), Path("data/fixtures/internal_docs.json"))
    print("Seeded research.db with 20 documents.")
