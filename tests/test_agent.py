import pytest
from pydantic_ai.models.function import AgentInfo, FunctionModel
from pydantic_ai.messages import ModelMessage, ModelResponse, ToolCallPart

from agent import build_agent


def _replier(answer_text: str):
    async def fn(messages: list[ModelMessage], info: AgentInfo):
        return ModelResponse(
            parts=[ToolCallPart(
                tool_name="final_result",
                args={
                    "answer": answer_text,
                    "citations": [],
                    "confidence": "high",
                },
                tool_call_id="1",
            )]
        )
    return fn


@pytest.mark.asyncio
async def test_agent_returns_final_answer_with_function_model(monkeypatch):
    # build_agent() constructs an OpenAI provider at import time; a dummy key
    # satisfies the env-var check so we can override the model in the test.
    monkeypatch.setenv("OPENAI_API_KEY", "sk-dummy-key-for-testing")
    agent = build_agent()
    with agent.override(model=FunctionModel(_replier("42"))):
        result = await agent.run("What is the answer?")
    assert result.output.answer == "42"
    assert result.output.confidence == "high"
