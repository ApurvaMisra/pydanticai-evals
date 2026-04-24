# PydanticAI Deep-Research Agent

A minimal [PydanticAI](https://ai.pydantic.dev) research agent that combines
web search (SerpAPI) with a human-in-the-loop-gated internal SQLite document
store. Structured output with citations, tool calling, HITL approval via
`requires_approval=True`.

This repo is scaffolding for an evals demo — the agent is deliberately simple
so the eval harness (added in a separate session) is the main event.

## Features

- PydanticAI agent with a `FinalAnswer` structured output (answer + citations + confidence)
- Two tools:
  - `search_web(query)` — SerpAPI
  - `query_internal_db(topic)` — SQLite; requires human approval
- `tool_calls_limit` safety net to prevent runaway loops
- Color-coded trace logging so you can see every model call and tool call
- OpenTelemetry → Arize Phoenix tracing (AGENT / TOOL / LLM spans, inputs, outputs, token counts)

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- OpenAI API key
- SerpAPI key (free tier works)

## Setup

```bash
# 1. Install dependencies
uv venv
uv pip install -e ".[dev,observability]"

# 2. Configure keys
cp .env.example .env
# edit .env — set OPENAI_API_KEY and SERPAPI_API_KEY

# 3. Seed the internal documents database
uv run python -m data.seed_db
# → Seeded research.db with 20 documents.
```

## Running the agent

Start Phoenix in a separate terminal (leave it running) to receive traces:

```bash
uv run phoenix serve
# UI at http://localhost:6006
```

Then run the agent:

```bash
uv run python -m agent.run "Summarize our Q1 product launch results"
```

When the agent proposes to query the internal database, you'll be prompted to
approve. Try both approving and denying to observe the fallback behavior.

Good demo questions:

- `"Summarize our Q1 product launch results"` — triggers `query_internal_db(product)`
- `"What are our main customer churn drivers?"` — triggers `query_internal_db(customers)`
- `"What are the latest announcements from Anthropic?"` — pure web search, no HITL
- `"Compare our product launch performance with our competitor landscape"` — multiple DB queries

## Running tests

```bash
uv run pytest
```

Tests use `FunctionModel` to mock the LLM — no API calls needed.

## Observability

`Agent(..., instrument=True)` in `build_agent()` makes PydanticAI emit OpenTelemetry
spans for every turn, tool call, and HITL gate. `shared/observability.py::setup_phoenix()`
installs a `TracerProvider` with two processors:

1. `OpenInferenceSpanProcessor` — rewrites PydanticAI's GenAI-convention spans
   with OpenInference attributes (`openinference.span.kind`, `input.value`,
   `output.value`, `llm.token_count.*`) so Phoenix classifies them as
   AGENT / LLM / TOOL and renders prompts, responses, and token counts.
2. `BatchSpanProcessor(OTLPSpanExporter)` — ships them to Phoenix via OTLP/HTTP
   (default `http://localhost:6006`, override with `PHOENIX_COLLECTOR_ENDPOINT`).

Tests and library imports stay trace-free — Phoenix setup only happens in the
CLI entry point (`agent/run.py`).

## Repo map

```
agent/                # the PydanticAI agent
  __init__.py         # re-exports run_agent, build_agent, FinalAnswer
  main.py             # build_agent(), run_agent(), tool definitions
  models.py           # FinalAnswer, Citation Pydantic models
  run.py              # CLI entry point
shared/               # tools & utilities used by the agent
  tools.py            # search_web (SerpAPI), query_internal_db (SQLite)
  types.py            # SearchResult, InternalDoc
  trace.py            # color-aware tagged trace helper
  observability.py    # OpenTelemetry → Phoenix setup
data/                 # SQLite seeder and fixture data
tests/                # pytest suite
```

## Next step: evals

An evals harness will be added in a follow-up session. The agent's structured
`FinalAnswer` output (with citation list and confidence) is designed to make
eval metrics straightforward — citation accuracy, confidence calibration,
tool-selection correctness, etc.
