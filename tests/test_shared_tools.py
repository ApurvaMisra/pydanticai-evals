from pathlib import Path
from unittest.mock import patch

import pytest

from data.seed_db import seed
from shared.tools import query_internal_db, search_web


@pytest.fixture
def seeded_db(tmp_path: Path) -> Path:
    db = tmp_path / "research.db"
    seed(db, Path("data/fixtures/internal_docs.json"))
    return db


def test_query_internal_db_returns_matching_docs(seeded_db: Path):
    docs = query_internal_db(topic="product", db_path=seeded_db)
    assert len(docs) == 5
    assert all(d.topic == "product" for d in docs)


def test_query_internal_db_unknown_topic_returns_empty(seeded_db: Path):
    docs = query_internal_db(topic="quantum-unicorns", db_path=seeded_db)
    assert docs == []


def test_search_web_returns_parsed_results():
    fake_payload = {
        "organic_results": [
            {"title": "Hello", "link": "https://example.com/a", "snippet": "First result"},
            {"title": "World", "link": "https://example.com/b", "snippet": "Second result"},
        ]
    }
    with patch("shared.tools._serpapi_search", return_value=fake_payload):
        results = search_web("any query")

    assert len(results) == 2
    assert results[0].title == "Hello"
    assert results[0].url == "https://example.com/a"
    assert results[1].snippet == "Second result"
