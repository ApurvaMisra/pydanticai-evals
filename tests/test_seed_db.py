import sqlite3
from pathlib import Path

from data.seed_db import seed


def test_seed_creates_table_and_loads_all_docs(tmp_path: Path):
    db = tmp_path / "research.db"
    fixture = Path("data/fixtures/internal_docs.json")

    seed(db_path=db, fixture_path=fixture)

    conn = sqlite3.connect(db)
    count = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
    topics = {row[0] for row in conn.execute("SELECT DISTINCT topic FROM documents")}
    conn.close()

    assert count == 20
    assert topics == {"product", "competitors", "customers", "infra"}


def test_seed_is_idempotent(tmp_path: Path):
    db = tmp_path / "research.db"
    fixture = Path("data/fixtures/internal_docs.json")

    seed(db_path=db, fixture_path=fixture)
    seed(db_path=db, fixture_path=fixture)  # re-run

    conn = sqlite3.connect(db)
    count = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
    conn.close()

    assert count == 20
