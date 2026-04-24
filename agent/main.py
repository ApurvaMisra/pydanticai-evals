import time

from pydantic_ai import Agent, DeferredToolRequests, DeferredToolResults
from pydantic_ai.usage import UsageLimits

from agent.models import FinalAnswer
from shared.tools import query_internal_db as _query_db
from shared.tools import search_web as _search_web
from shared.trace import banner, separator, trace


SYSTEM_PROMPT = """
You are a research assistant. Answer the user's question using the provided tools.

Available tools:
- search_web(query): Search the public web (general knowledge, current events).
- query_internal_db(topic): Query the internal company research database.
  Valid topics: "product", "competitors", "customers", "infra".
  This tool REQUIRES HUMAN APPROVAL.

Strict rules — follow every one:
1. Use query_internal_db ONLY when the user asks about internal/company matters.
2. Call each (tool, args) combination AT MOST ONCE. If you have already called
   query_internal_db with topic="product", DO NOT call it again with topic="product";
   use the result you already received.
3. After receiving a tool result, read it carefully. The result already contains
   the information you need — use it to form your answer.
4. Return a FinalAnswer as soon as you have enough information. Cite the sources
   you used (doc IDs for internal_db, URLs for web). Do not over-research.
5. If a tool returned "No results" or "No internal documents found", do not retry
   the same call — either try a different topic/query or answer with what you have.
"""

TOOL_CALL_BUDGET = 6


def build_agent() -> Agent:
    agent = Agent(
        "openai:gpt-5.2",
        name="deep-research",
        instructions=SYSTEM_PROMPT,
        output_type=[FinalAnswer, DeferredToolRequests],
        instrument=True,
    )

    @agent.tool_plain
    def search_web(query: str) -> str:
        """Search the public web for general knowledge or current events."""
        trace("tool", f"search_web(query={query!r})")
        t0 = time.perf_counter()
        hits = _search_web(query)
        dt = time.perf_counter() - t0
        if not hits:
            trace("tool", f"  -> no results ({dt:.2f}s)")
            return "No results."
        trace("tool", f"  -> {len(hits)} results ({dt:.2f}s)")
        return "\n".join(f"- {h.title} ({h.url}): {h.snippet}" for h in hits)

    @agent.tool_plain(requires_approval=True)
    def query_internal_db(topic: str) -> str:
        """Query the internal company research database by topic.

        Valid topics: "product", "competitors", "customers", "infra".
        """
        trace("tool", f"query_internal_db(topic={topic!r})  [human-approved]")
        t0 = time.perf_counter()
        docs = _query_db(topic=topic)
        dt = time.perf_counter() - t0
        if not docs:
            trace("tool", f"  -> no documents ({dt:.2f}s)")
            return f"No internal documents found for topic {topic!r}."
        trace("tool", f"  -> {len(docs)} documents ({dt:.2f}s)")
        return "\n".join(f"- {d.id} [{d.title}] ({d.created_at}): {d.body}" for d in docs)

    return agent


async def run_agent(question: str, approver=None) -> FinalAnswer:
    approver = approver or _console_approver
    limits = UsageLimits(tool_calls_limit=TOOL_CALL_BUDGET)

    banner("PydanticAI agent — run")
    trace("agent", f"question: {question!r}")
    trace("agent", f"tool_calls_limit={TOOL_CALL_BUDGET}")
    separator(f"turn 1")
    trace("model", f"calling gpt-5.2 ...")

    agent = build_agent()
    run_start = time.perf_counter()
    result = await agent.run(question, usage_limits=limits)
    turn = 1

    while isinstance(result.output, DeferredToolRequests):
        deferred: DeferredToolRequests = result.output
        trace("model", f"deferred for human approval ({len(deferred.approvals)} call(s))")

        decisions = DeferredToolResults()
        for call in deferred.approvals:
            decision = approver(f"{call.tool_name}({call.args})")
            decisions.approvals[call.tool_call_id] = decision
            verdict = "APPROVED" if decision else "DENIED"
            trace("hitl", f"{verdict}: {call.tool_name}({call.args})")

        turn += 1
        separator(f"turn {turn}")
        trace("model", f"resuming ...")
        result = await agent.run(
            message_history=result.all_messages(),
            deferred_tool_results=decisions,
            usage_limits=limits,
        )

    elapsed = time.perf_counter() - run_start
    answer = result.output
    trace("agent", f"done in {elapsed:.2f}s across {turn} turn(s)")
    trace("agent", f"final: confidence={answer.confidence}, {len(answer.citations)} citation(s)")
    banner("PydanticAI agent — done")
    return answer


def _console_approver(proposal: str) -> bool:
    print(f"\n[HITL] Agent wants to call: {proposal}")
    return input("Approve? [y/N]: ").strip().lower() == "y"
