import os
import sqlite3
from pathlib import Path

from serpapi import Client

from shared.types import InternalDoc, SearchResult

DEFAULT_DB_PATH = Path("research.db")
MAX_RESULTS = 5


def _serpapi_search(query: str) -> dict:
    client = Client(api_key=os.environ["SERPAPI_API_KEY"])
    results = client.search(q=query, engine="google", num=MAX_RESULTS)
    return dict(results)


def search_web(query: str) -> list[SearchResult]:
    payload = _serpapi_search(query)
    organic = payload.get("organic_results", [])[:MAX_RESULTS]
    return [
        SearchResult(
            title=item.get("title", ""),
            url=item.get("link", ""),
            snippet=item.get("snippet", ""),
        )
        for item in organic
    ]


def query_internal_db(topic: str, db_path: Path = DEFAULT_DB_PATH) -> list[InternalDoc]:
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT id, title, topic, body, created_at FROM documents WHERE topic = ? ORDER BY created_at DESC",
            (topic,),
        ).fetchall()
    return [InternalDoc(**dict(row)) for row in rows]
